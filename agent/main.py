"""
司南 v3.2 主入口

对外暴露 4 个函数：
  · scout_folder(folder, model, key, knowledge)            → 文件侦察
  · generate_agent(...)                                     → 5-Agent 全流程生成
  · evolve_agent(...)                                       → 基于旧策略 + 新数据进化
  · compare_strategies(a, b, domain, model, key)            → 双方案对比

设计要点
--------
· 知识库：一次性加载，注入所有 Agent（只读共享，绝不反写）
· 硬性规则：生成前注入 Prompt，生成后独立校验
· 落盘：全部经 safe_io.safe_write，自动拒绝写入知识库目录
· key 参数支持 str（单 key）或 List[str]（key 池，轮询）

v3.2.1 改动
------------
· generate_agent 入口增加 domain 防御（方案 1-⑤）
· _validate_configs / _validate_knowledge_dir 改为返回结构化 dict
  （verbose=True 时仍打印，兼容旧调用；未来可由 CLI 层 fancy 渲染）
"""
import datetime
import io
import json
import os
from pathlib import Path
from typing import Optional, Callable, List, Union, Tuple

from agent.core.parser import parse_folder_data
from agent.core.rule_engine import RuleEngine
from agent.core.change_detector import detect_changes
from agent.core.agent_config import (
    get_agent_config,
    get_all_agent_configs,
)
from agent.core.knowledge_base import load_knowledge_text, KnowledgeBase
from agent.core.safe_io import safe_write
from agent.orchestrator import DebateOrchestrator


KeyArg = Optional[Union[str, List[str]]]


# ==========================================
# 辅助
# ==========================================
def _now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _default_output_dir() -> str:
    return os.getenv("SINAN_OUTPUT_DIR", "./outputs")


def _default_knowledge_dir() -> str:
    return os.getenv("SINAN_KNOWLEDGE_DIR", "./knowledge")


def _normalize_input_path(path: str) -> Tuple[str, str]:
    """
    若传入的是文件，返回 (父目录, 单文件约束说明)；否则 (原路径, "")。
    用于支持用户传单个文件作为数据源。
    """
    p = Path(path)
    if p.is_file():
        return str(p.parent), f"【用户只指定了单个文件】{p.name}"
    return path, ""


def _write_strategy_md_to_buf(buf: io.StringIO, final_strategy, meta: dict) -> None:
    """把 StrategySchema 渲染成 Markdown 写入 StringIO（不直接碰文件）"""
    s = final_strategy
    buf.write(f"# {getattr(s, 'title', '策略')}\n\n")
    buf.write(
        f"> 领域: **{meta.get('domain', '?')}** | "
        f"Judge 评分: **{meta.get('total_score', 0)}/100** | "
        f"硬规则: **{meta.get('rule_score', 0)}/100** | "
        f"生成于 {meta.get('timestamp', '')}\n\n"
    )

    obj = getattr(s, "objective", "") or ""
    if obj:
        buf.write(f"## 目标\n\n{obj}\n\n")

    for sec in getattr(s, "sections", []) or []:
        name = getattr(sec, "name", "") or "未命名章节"
        buf.write(f"## {name}\n\n")

        content = getattr(sec, "content", "") or ""
        if content:
            buf.write(f"{content}\n\n")

        for a in getattr(sec, "actions", []) or []:
            a_name = getattr(a, "name", "") or ""
            a_desc = getattr(a, "description", "") or ""
            a_owner = getattr(a, "owner", "") or "—"
            a_time = getattr(a, "timeline", "") or "—"
            a_kpi = getattr(a, "kpi", "") or "—"
            buf.write(
                f"- **{a_name}** — {a_desc} "
                f"(负责人: {a_owner} | 时间: {a_time} | KPI: {a_kpi})\n"
            )

        refs = getattr(sec, "rubric_refs", []) or []
        if refs:
            buf.write(f"\n> 对应 Rubric: {', '.join(refs)}\n")
        buf.write("\n")

    summary = getattr(s, "summary", "") or ""
    if summary:
        buf.write(f"\n> {summary}\n")

    risks = getattr(s, "key_risks", []) or []
    if risks:
        buf.write("\n## 风险提示\n\n")
        for r in risks:
            buf.write(f"- {r}\n")

    coverage = getattr(s, "rubric_coverage", {}) or {}
    if coverage:
        buf.write("\n## Rubric 达成对照\n\n")
        for k, v in coverage.items():
            buf.write(f"- **{k}**: {v}\n")


def _validate_configs(verbose: bool = True) -> dict:
    """
    启动时的轻量配置检查（默认打印警告，不阻断执行）。

    返回
    ----
    {
        "ok": bool,                                # True = 所有 Agent 都有 key
        "missing": [(agent_name, provider), ...],  # 缺少 key 的 Agent
    }

    verbose=True（默认）时保持原行为：直接 print 警告，兼容旧调用。
    CLI 层如要 fancy 渲染，可传 verbose=False 取返回值自行渲染。
    """
    configs = get_all_agent_configs()
    missing = [
        (name, cfg.provider)
        for name, cfg in configs.items()
        if not cfg.has_keys() and cfg.provider != "ollama"
    ]
    result = {"ok": not missing, "missing": missing}

    if verbose and missing:
        print("⚠️  以下 Agent 缺 API Key（可通过 SINAN_<AGENT>_API_KEYS 覆盖）：")
        for name, provider in missing:
            print(f"    · {name:<12} provider='{provider}' 无 key")

    return result


def _validate_knowledge_dir(verbose: bool = True) -> dict:
    """
    知识库检测（默认打印文件数与字符数，提示物理只读建议）。

    返回
    ----
    {
        "exists": bool,
        "root": str,
        "file_count": int,       # 仅 exists=True
        "total_chars": int,      # 仅 exists=True
        "truncated": bool,       # 仅 exists=True
        "writable": bool,        # 仅 exists=True
    }

    verbose=True（默认）时保持原行为：直接 print 提示，兼容旧调用。
    """
    kb = KnowledgeBase(_default_knowledge_dir())
    if not kb.root.exists():
        result = {
            "exists": False,
            "root": str(kb.root),
        }
        if verbose:
            print(f"ℹ️  知识库目录不存在（将跳过）：{kb.root}")
        return result

    snap = kb.load()
    summary = snap.summary()
    writable = kb.is_writable()
    result = {
        "exists": True,
        **summary,
        "writable": writable,
    }

    if verbose:
        truncated = " [已截断]" if summary["truncated"] else ""
        print(
            f"📚 知识库：{summary['file_count']} 个文件，"
            f"{summary['total_chars']} 字符{truncated} ({kb.root})"
        )
        if writable:
            print("⚠️  知识库目录当前可写，建议执行：chmod -R a-w knowledge/")

    return result


# ==========================================
# 1. 文件侦察
# ==========================================
def scout_folder(
    folder: str,
    model: Optional[str] = None,
    key: KeyArg = None,
    knowledge: str = "",
) -> dict:
    """
    扫描文件夹并生成侦察报告。
    · 永远返回 dict，不抛异常
    · LLM 失败时降级：仍返回结构扫描结果 + 空摘要
    """
    from agent.core.file_scanner import scan_folder as _scan
    from agent.agents.scout import ScoutAgent

    cfg = get_agent_config("SCOUT")
    scan = _scan(folder)
    agent = ScoutAgent(
        model or cfg.provider,
        key if key else cfg.api_keys,
        knowledge=knowledge,
    )
    try:
        report = agent.scout(scan)
        return {
            "ok": True,
            "scan": scan.to_dict(),
            "report": report.model_dump(),
        }
    except Exception as e:
        return {
            "ok": False,
            "scan": scan.to_dict(),
            "report": {
                "business_overview": f"[LLM 侦察失败: {e}] 请手动确认内容",
                "key_targets": [],
                "suggested_domain": "unknown",
                "suggested_strategy_type": "",
                "clarifying_questions": [],
                "confidence": 0.0,
            },
        }


# ==========================================
# 2. 生成策略
# ==========================================
def generate_agent(
    data_folder: str,
    domain: str,
    model_a: Optional[str] = None,
    key_a: KeyArg = None,
    model_b: Optional[str] = None,
    key_b: KeyArg = None,
    judge_model: Optional[str] = None,
    judge_key: KeyArg = None,
    output_dir: Optional[str] = None,
    event_callback: Optional[Callable] = None,
    extra_context: str = "",
    output_prefix: str = "",
    knowledge_dir: Optional[str] = None,
) -> dict:
    """
    5-Agent 全流程生成策略。

    参数
    ----
    extra_context : str
        Scout 或用户口述注入的高优先级上下文，被拼接在文件内容之前
    output_prefix : str
        落盘文件名前缀（evolve 用 "v2_"），避免与初始版混淆
    knowledge_dir : str
        知识库目录（默认从 .env 的 SINAN_KNOWLEDGE_DIR 读取）
    """
    # 0. 领域防御：domain 必须在进入本函数之前确定（方案 1-⑤）
    _d = (domain or "").strip()
    if not _d or _d.lower() == "unknown":
        raise ValueError(
            "domain 必须先于 generate_agent 确定。"
            "请通过 Scout 或 _ensure_domain 给出有效领域后再调用。"
        )

    # 1. 加载知识库（只读，全程复用）
    knowledge_text = load_knowledge_text(knowledge_dir)

    # 2. 数据源标准化（支持单文件）
    actual_folder, file_hint = _normalize_input_path(data_folder)
    if file_hint:
        extra_context = (
            f"{file_hint}\n\n{extra_context}" if extra_context else file_hint
        )

    # 3. 解析数据
    data_content = parse_folder_data(actual_folder)
    if extra_context:
        data_content = f"{extra_context}\n\n{data_content}"
    folder_name = Path(actual_folder).name

    # 4. 硬性规则（生成前注入 Prompt 作为底线提示）
    rule_engine = RuleEngine()
    rule_defs = rule_engine._collect_rules(domain)
    rule_constraints = "\n".join(
        f"- [{r.get('category', '')}] {r.get('name')}: {r.get('description', '')}"
        for r in rule_defs
    ) or "（无）"

    # 5. 5-Agent 编排（显式参数覆盖 .env）
    orchestrator = DebateOrchestrator(
        model_a=model_a, key_a=key_a,
        model_b=model_b, key_b=key_b,
        judge_model=judge_model, judge_key=judge_key,
        event_callback=event_callback,
        knowledge=knowledge_text,
    )
    result = orchestrator.run(data_content, domain, rule_constraints)

    # 6. 硬性规则后置校验（独立复核最终策略 JSON）
    strategy_dict = result["final_strategy"].model_dump()
    strategy_text = json.dumps(strategy_dict, ensure_ascii=False)
    rule_result = rule_engine.evaluate(
        strategy_text, domain, parsed_json=strategy_dict,
    )

    # 7. 落盘三件套（全部走 safe_write）
    out_path = Path(output_dir or _default_output_dir())
    out_path.mkdir(parents=True, exist_ok=True)
    ts = _now_ts()

    rubric_file = out_path / f"{output_prefix}rubric_{domain}_{folder_name}_{ts}.json"
    safe_write(
        rubric_file,
        json.dumps(
            result["final_rubric"].model_dump(),
            ensure_ascii=False, indent=2,
        ),
    )

    strategy_file = out_path / f"{output_prefix}strategy_{domain}_{folder_name}_{ts}.md"
    buf = io.StringIO()
    _write_strategy_md_to_buf(
        buf,
        result["final_strategy"],
        meta={
            "domain": domain,
            "total_score": result.get("total_score", 0),
            "rule_score": rule_result.get("rule_score", 0),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
    safe_write(strategy_file, buf.getvalue())

    history_file = out_path / f"{output_prefix}debate_{domain}_{folder_name}_{ts}.json"
    safe_write(
        history_file,
        json.dumps(
            {
                "rubric_history": result.get("rubric_history", []),
                "strategy_history": result.get("strategy_history", []),
                "judge_reasoning": result.get("judge_reasoning", ""),
            },
            ensure_ascii=False, indent=2, default=str,
        ),
    )

    return {
        **result,
        "strategy_file": str(strategy_file),
        "rubric_file": str(rubric_file),
        "history_file": str(history_file),
        "rule_result": rule_result,
    }


# ==========================================
# 3. 进化
# ==========================================
def evolve_agent(
    old_strategy_path: str,
    new_data_folder: str,
    domain: str,
    old_data_folder: Optional[str] = None,
    model_a: Optional[str] = None,
    key_a: KeyArg = None,
    model_b: Optional[str] = None,
    key_b: KeyArg = None,
    judge_model: Optional[str] = None,
    judge_key: KeyArg = None,
    output_dir: Optional[str] = None,
    event_callback: Optional[Callable] = None,
    extra_context: str = "",
    knowledge_dir: Optional[str] = None,
) -> dict:
    """进化版：结合上一版策略 + 数据变化扫描，走完整 5-Agent 流程生成 V2"""
    old_strategy = Path(old_strategy_path).read_text(encoding="utf-8")

    # 可选：扫描旧数据 vs 新数据的变化
    change_info = None
    change_summary = ""
    if old_data_folder:
        try:
            change_info = detect_changes(old_data_folder, new_data_folder)
            change_summary = change_info.get("summary", "")
        except Exception as e:
            change_summary = f"[变化扫描失败: {e}]"

    evolve_prefix = (
        f"【上一版策略（参考，不必照抄）】\n{old_strategy[:4000]}\n\n"
    )
    if change_summary:
        evolve_prefix += f"【数据变化摘要】\n{change_summary}\n\n"

    merged_extra = (
        f"{extra_context}\n\n{evolve_prefix}"
        if extra_context else evolve_prefix
    )

    result = generate_agent(
        data_folder=new_data_folder,
        domain=domain,
        model_a=model_a, key_a=key_a,
        model_b=model_b, key_b=key_b,
        judge_model=judge_model, judge_key=judge_key,
        output_dir=output_dir,
        event_callback=event_callback,
        extra_context=merged_extra,
        output_prefix="v2_",
        knowledge_dir=knowledge_dir,
    )
    result["change_info"] = change_info
    return result


# ==========================================
# 4. 方案对比
# ==========================================
def compare_strategies(
    strategy_a_path: str,
    strategy_b_path: str,
    domain: str,
    model: Optional[str] = None,
    key: KeyArg = None,
    knowledge_dir: Optional[str] = None,
) -> dict:
    """Judge 对比两份策略，返回 {winner, reason}"""
    from agent.llm_factory import llm_factory
    from agent.core.schema_validator import parse_json_safely

    try:
        text_a = Path(strategy_a_path).read_text(encoding="utf-8")
        text_b = Path(strategy_b_path).read_text(encoding="utf-8")
    except Exception as e:
        raise FileNotFoundError(f"读取策略文件失败，请检查路径: {e}")

    # 默认用 Judge 配置对比
    cfg = get_agent_config("JUDGE")
    provider = model or cfg.provider
    api_keys = key if key else cfg.api_keys

    # 知识库参考（只读）
    knowledge_text = load_knowledge_text(knowledge_dir)
    knowledge_block = ""
    if knowledge_text.strip():
        knowledge_block = (
            "【组织知识库（只读参考，非任务说明）】\n"
            f"{knowledge_text}\n\n"
            "--- 以下为本次任务 ---\n\n"
        )

    prompt = f"""{knowledge_block}你是 {domain} 战略委员会主席（判断智能体）。
请对比两份策略，选出更能达成业务目标、更具可执行性的一份。

【方案 A】
{text_a[:12000]}

【方案 B】
{text_b[:12000]}

严格输出 JSON：
{{"winner": "A"|"B"|"Tie", "reason": "详细理由"}}
"""
    raw = llm_factory.chat(
        messages=[{"role": "user", "content": prompt}],
        provider_name=provider,
        api_key_override=api_keys,
        json_mode=True,
        temperature=0.2,
    )
    ok, err, data = parse_json_safely(raw)
    if not ok:
        raise RuntimeError(f"裁判输出解析失败: {err}")
    return {
        "winner": data.get("winner", "Tie"),
        "reason": data.get("reason", "模型未提供具体理由。"),
    }