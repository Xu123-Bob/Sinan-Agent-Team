# === 友好依赖检查：把 ugly traceback 变成可读提示 ===
try:
    from agent.main import (
        generate_agent,
        evolve_agent,
        compare_strategies,
        scout_folder,
        _validate_configs,
        _validate_knowledge_dir,
    )
except ImportError as e:
    import sys
    from rich.console import Console
    _err = Console()
    _err.print(
        f"\n[bold red]❌ 司南启动失败：[/bold red]{e}\n\n"
        "[bold yellow]可能原因与修复：[/bold yellow]\n"
        "  1. [cyan]安装不完整[/cyan] → 执行：\n"
        "     [green]pip install --force-reinstall .[/green]\n\n"
        "  2. [cyan]editable 模式失效（Python 3.13+ 常见）[/cyan] → 改用普通安装：\n"
        "     [green]pip uninstall -y sinan-agent && pip install .[/green]\n\n"
        "  3. [cyan]Python 版本过新[/cyan] → 推荐使用 Python 3.10~3.12\n\n"
        "  4. [cyan]在错误目录下运行[/cyan] → 确保当前目录是项目根目录，"
        "或直接运行：[green]python -m agent[/green]\n\n"
        "运行 [bold]python -m agent.doctor[/bold] 可自动诊断。\n"
    )
    sys.exit(1)

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.align import Align
from rich.table import Table
from rich.text import Text
from rich import box

from agent.main import (
    generate_agent,
    evolve_agent,
    compare_strategies,
    scout_folder,
    _validate_configs,
    _validate_knowledge_dir,
)
from agent.core.intent_parser import IntentParser
from agent.core.scenario_detector import ScenarioDetector
from agent.core.agent_config import get_all_agent_configs
from agent.core.knowledge_base import load_knowledge_text, KnowledgeBase
from agent.core.path_discovery import (
    discover_data_folders,
    discover_strategy_files,
)


# ==========================================
# 全局
# ==========================================
app = typer.Typer(
    help="司南 (Sinan) - 多智能体策略制定系统",
    no_args_is_help=False,
)
console = Console()

DOMAIN_CHOICES = ["ecommerce", "github", "atomgit", "douyin", "tiktok"]
MAX_PREVIEW_CHARS = 1200

EXPLICIT_ACTIONS = {
    "模型博弈": "generate",
    "双模型博弈": "generate",
    "开始博弈": "generate",
    "博弈": "generate",
    "博弈生成": "generate",
    "制定策略": "generate",
    "开始制定": "generate",
    "迭代策略": "evolve",
    "策略迭代": "evolve",
    "迭代": "evolve",
    "进化策略": "evolve",
    "进化": "evolve",
}

EXIT_WORDS = {"/exit", "/quit", "exit", "quit", "退出", "再见"}

GROUP_COLOR = {
    "rubric": "magenta",
    "strategy": "blue",
    "judge": "yellow",
}
GROUP_ICON = {
    "rubric": "🧩",
    "strategy": "🎯",
    "judge": "⚖️",
}


# ==========================================
# 展示工具
# ==========================================
def _truncate(text: str, limit: int = MAX_PREVIEW_CHARS) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n... [内容过长已截断，完整内容见输出文件] ..."


def _fmt_list(items, empty: str = "无", indent: str = "  - ") -> str:
    if not items:
        return f"{indent}{empty}"
    return "\n".join(f"{indent}{x}" for x in items)


def _speaker_label(speaker: str) -> str:
    return {"A": "一", "B": "二"}.get(speaker, speaker)


def _render_rubric(content: dict) -> str:
    # 方案 2-A1：去掉 ≡
    lines = ["[bold]Rubric 评分量规[/bold]"]
    total = 0.0
    for d in content.get("dimensions", []):
        try:
            total += float(d.get("max_score", 0))
        except (ValueError, TypeError):
            pass
        lines.append(
            f"  • [cyan]{d.get('name', '?')}[/cyan] "
            f"({d.get('max_score', '?')} 分)"
        )
        if d.get("description"):
            lines.append(f"    [dim]考察: {d['description']}[/dim]")
        if d.get("measurement"):
            lines.append(f"    [dim]衡量: {d['measurement']}[/dim]")
        if d.get("weight_reason"):
            lines.append(f"    [dim]权重理由: {d['weight_reason']}[/dim]")
        if d.get("must_include"):
            lines.append(f"    [dim]必含: {', '.join(d['must_include'])}[/dim]")
    lines.append(f"\n[bold yellow]合计：{total} 分[/bold yellow]")
    if content.get("rationale"):
        lines.append(f"\n[italic dim]设计思路: {content['rationale']}[/italic dim]")
    return "\n".join(lines)


def _render_strategy(content: dict) -> str:
    lines = [
        f"[bold]{content.get('title', '策略')}[/bold]",
        f"[dim]{content.get('objective', '')}[/dim]",
        "",
    ]
    for sec in content.get("sections", []):
        lines.append(f"[bold cyan]▸ {sec.get('name', '')}[/bold cyan]")
        if sec.get("content"):
            lines.append(_truncate(sec["content"], 400))
        for a in sec.get("actions", []) or []:
            meta = []
            if a.get("timeline"):
                meta.append(f"时间: {a['timeline']}")
            if a.get("owner"):
                meta.append(f"负责人: {a['owner']}")
            if a.get("kpi"):
                meta.append(f"KPI: {a['kpi']}")
            meta_str = f" [dim]({' | '.join(meta)})[/dim]" if meta else ""
            lines.append(
                f"  - [green]{a.get('name', '')}[/green] "
                f"{a.get('description', '')}{meta_str}"
            )
        if sec.get("rubric_refs"):
            # 方案 2-B1：↳ → →
            lines.append(
                f"  [dim]→ 对应 Rubric: {', '.join(sec['rubric_refs'])}[/dim]"
            )
        lines.append("")
    if content.get("summary"):
        lines.append(f"[italic dim]总结: {content['summary']}[/italic dim]")
    if content.get("key_risks"):
        lines.append("\n[bold red]⚠ 潜在风险：[/bold red]")
        for r in content["key_risks"]:
            lines.append(f"  - {r}")
    return "\n".join(lines)


def _render_strategy_decision(content: dict) -> str:
    # 方案 2-A2：去掉 ◎
    lines = [
        f"[bold yellow]Judge 总分：{content.get('total_score', 0)}/100[/bold yellow]",
    ]
    if content.get("reasoning"):
        lines.append(f"[italic dim]裁定说明: {content['reasoning']}[/italic dim]")
    lines.append("")

    dims = content.get("dimension_scores", []) or []
    if dims:
        lines.append("[bold]各维度得分：[/bold]")
        for d in dims:
            lines.append(
                f"  • [cyan]{d.get('name', '?')}[/cyan]: "
                f"{d.get('score', 0)}/{d.get('max_score', 0)} — "
                f"[dim]{d.get('comment', '')}[/dim]"
            )
        lines.append("")

    if content.get("defects"):
        lines.append("[bold red]⚠ 缺陷：[/bold red]")
        for x in content["defects"]:
            lines.append(f"  - {x}")
        lines.append("")

    if content.get("improvement_directions"):
        # 方案 2-B2：↗ → →
        lines.append("[bold green]→ 改进方向：[/bold green]")
        for x in content["improvement_directions"]:
            lines.append(f"  - {x}")
        lines.append("")

    final_strategy = content.get("final_strategy")
    if isinstance(final_strategy, dict) and "title" in final_strategy:
        # 方案 2-A3：去掉 ━━━
        lines.append("[bold]最终策略[/bold]")
        lines.append(_render_strategy(final_strategy))

    return "\n".join(lines)


def _render_content(content) -> str:
    """通用内容渲染：Rubric / Strategy / JudgeDecision / 纯文本"""
    if content is None:
        return "[dim]（无内容）[/dim]"

    if isinstance(content, dict):
        if "final_strategy" in content:
            return _render_strategy_decision(content)
        if "final_rubric" in content:
            return _render_content(content["final_rubric"])
        if "dimensions" in content:
            return _render_rubric(content)
        if "sections" in content:
            return _render_strategy(content)
        return _truncate(json.dumps(content, ensure_ascii=False, indent=2))

    if isinstance(content, str):
        return _truncate(content)

    return _truncate(str(content))


def _make_debate_renderer():
    """事件回调：start / before / after / decision"""
    def _cb(event: dict):
        phase = event.get("phase")
        group = event.get("group", "")
        speaker = event.get("speaker", "")
        role = event.get("role", "")
        round_n = event.get("round", "")

        color = GROUP_COLOR.get(group, "cyan")
        icon = GROUP_ICON.get(group, "•")

        if phase == "start":
            console.print()
            console.print(Panel.fit(
                f"[bold {color}]{icon} {role}[/bold {color}]",
                border_style=color,
                box=box.ROUNDED,          # 方案 2-C
            ))
            return

        # 方案 2-B4：◈/◇ → [A]/[B]
        if speaker in ("A", "B"):
            tag = "[A]" if speaker == "A" else "[B]"
            spk_name = (
                f"[bold {color}]{tag} 模型{_speaker_label(speaker)}[/bold {color}]"
            )
        elif speaker == "judge":
            spk_name = "[bold yellow]⚖️ 判断智能体[/bold yellow]"
        else:
            spk_name = f"[bold {color}]{speaker or '?'}[/bold {color}]"

        title = f"{spk_name} · {role}" + (f" · 第 {round_n} 轮" if round_n else "")

        if phase == "before":
            console.print(
                f"\n[dim]⏳ {title} 正在生成...  "
                f"[bold yellow](Ctrl+C 可中断)[/bold yellow][/dim]"
            )
            return

        if phase == "after":
            content = event.get("content")
            comment = event.get("comment", "")
            body = _render_content(content)
            if comment:
                body += f"\n\n[italic dim]💬 {comment}[/italic dim]"
            console.print(Panel(
                body, title=title, border_style=color,
                box=box.ROUNDED, padding=(0, 1),   # 方案 2-C
            ))
            return

        if phase == "decision":
            content = event.get("content")
            comment = event.get("comment", "")
            body = _render_content(content)
            if comment:
                body += f"\n\n[italic dim]💬 {comment}[/italic dim]"
            console.print(Panel(
                body,
                title=f"[bold yellow]{icon} {role}（决策）[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,                    # 方案 2-C
                padding=(1, 2),
            ))
            return

    return _cb


def render_final_summary(result: dict):
    """Judge 维度得分 + 缺陷 + 改进方向 + 硬规则校验"""
    console.print()

    dims = result.get("dimension_scores", []) or []
    if dims:
        # 方案 2-A4：去掉 ∑
        table = Table(
            title="Judge 评分明细",
            box=box.ROUNDED, border_style="yellow",
        )
        table.add_column("维度", style="bold cyan", justify="left")
        table.add_column("得分", justify="center", style="bold yellow")
        table.add_column("评价", style="dim", justify="left")
        for d in dims:
            table.add_row(
                d.get("name", "?"),
                f"{d.get('score', 0)}/{d.get('max_score', 0)}",
                (d.get("comment", "") or "")[:80],
            )
        console.print(table)

    if result.get("defects"):
        console.print(Panel(
            "\n".join(f"  • {x}" for x in result["defects"]),
            title="⚠ 缺陷", border_style="red", box=box.ROUNDED,
        ))

    if result.get("improvement_directions"):
        # 方案 2-B3：去掉 ↗
        console.print(Panel(
            "\n".join(f"  • {x}" for x in result["improvement_directions"]),
            title="改进方向", border_style="green", box=box.ROUNDED,
        ))

    rule_result = result.get("rule_result") or {}
    details = rule_result.get("details") or []
    if details:
        lines = []
        for d in details:
            mark = "[green]✓[/green]" if d.get("passed") else "[red]✕[/red]"
            line = (
                f"  {mark} {d.get('name', '?')} "
                f"({d.get('score', 0)}/{d.get('max_score', 0)})"
            )
            if d.get("description"):
                line += f" — [dim]{d['description']}[/dim]"
            lines.append(line)
        score = rule_result.get("rule_score", 0)
        title = f"⚖ 硬性规则校验：{score}/100"
        if rule_result.get("all_passed"):
            title += " [green](全部通过)[/green]"
        console.print(Panel(
            "\n".join(lines),
            title=title,
            border_style="green" if rule_result.get("all_passed") else "yellow",
            box=box.ROUNDED,
        ))


# ==========================================
# 场景探测 / 领域决策
# ==========================================
def _ensure_domain(
    domain: Optional[str],
    folder_for_detect: Optional[str] = None,
    model_a: Optional[str] = None,
    key_a: Optional[str] = None,
) -> str:
    """
    领域确认工具。仅在已明确 folder 时使用：
      · 有 folder：优先 detector 自动推断 → 失败则弹选择（含自定义）
      · 无 folder：直接报错让调用方先取得数据路径（方案 1-③）
    """
    # 场景 A：调用方已经显式给了合法领域 → 直接用
    if domain and domain.lower() not in ("unknown", "", "none"):
        return domain.lower()

    # 场景 B：调用方没给 folder → 拒绝，提示先提供数据路径
    if not folder_for_detect:
        raise ValueError(
            "_ensure_domain 需要 folder_for_detect（数据路径）才能推断领域；"
            "调用方应先取得数据路径再调用。"
        )

    # 场景 C：有 folder → 先 detector 推断
    console.print(
        f"[dim]未指定领域，正在根据 [{folder_for_detect}] 内容自动探测...[/dim]"
    )
    detector = ScenarioDetector(provider_name=model_a, api_key=key_a)
    detected = detector.detect(folder_for_detect)
    if detected and detected != "unknown":
        console.print(f"[green]自动探测到领域: [bold]{detected}[/bold][/green]")
        return detected

    # detector 也推不出来 → 手动选择（含自定义）
    console.print("[yellow]无法自动推断领域，请手动选择。[/yellow]")
    console.print("\n[bold]请选择业务领域：[/bold]")
    for i, p in enumerate(DOMAIN_CHOICES, 1):
        console.print(f"  [cyan]{i}[/cyan]. {p}")
    custom_idx = len(DOMAIN_CHOICES) + 1
    console.print(f"  [cyan]{custom_idx}[/cyan]. 其他（手动输入）")

    while True:
        choice = Prompt.ask(
            "输入编号",
            choices=[str(i) for i in range(1, custom_idx + 1)],
        ).strip()
        if choice == str(custom_idx):
            custom = Prompt.ask("[cyan]请输入自定义领域名[/cyan]").strip().lower()
            if custom:
                return custom
            console.print("[yellow]领域名不能为空，请重试。[/yellow]")
            continue
        return DOMAIN_CHOICES[int(choice) - 1]


def _ask_domain_override(suggested: str) -> str:
    """在 Scout 面板里让用户更换领域；支持从内置列表选或自定义输入。（方案 1-④）"""
    console.print(f"\n[dim]当前建议领域: [bold]{suggested}[/bold][/dim]")
    for i, d in enumerate(DOMAIN_CHOICES, 1):
        mark = " [green](建议)[/green]" if d == suggested else ""
        console.print(f"  [cyan]{i}[/cyan]. {d}{mark}")
    custom_idx = len(DOMAIN_CHOICES) + 1
    console.print(f"  [cyan]{custom_idx}[/cyan]. 其他（手动输入）")
    console.print("[dim]也可直接输入领域名（如 healthcare / fintech）[/dim]")

    raw = Prompt.ask("选择", default="").strip()
    if not raw:
        return suggested
    if raw.isdigit() and 1 <= int(raw) <= len(DOMAIN_CHOICES):
        return DOMAIN_CHOICES[int(raw) - 1]
    if raw == str(custom_idx):
        custom = Prompt.ask("[cyan]请输入自定义领域名[/cyan]").strip().lower()
        return custom or suggested
    return raw.lower()


def _decide_domain_after_scout(
    intent_domain: Optional[str],
    scout: dict,
    folder: str,
    model_a: Optional[str],
    key_a: Optional[str],
    domain_label: str = "领域",
) -> str:
    """
    Scout 扫描完成后的领域决策（供 _run_generate / _run_evolve 复用）。（方案 1-②⑥）

    优先级（高 → 低）：
      1. 用户在 Scout 面板里主动改过领域（selected != suggested）→ 直接采用
      2. 用户指令中显式指定的领域（intent_domain）→ 与 Scout 建议冲突时确认
      3. Scout.suggested_domain（自动推断）
      4. _ensure_domain 兜底（此时 folder 一定非空）
    """
    intent_domain = (
        intent_domain if intent_domain not in ("unknown", "", None) else None
    )
    scout_suggested = scout.get("suggested_domain") or "unknown"
    scout_selected = scout.get("selected_domain") or scout_suggested

    # 1) 用户在面板里主动改过 → 最高优先
    if scout_selected != scout_suggested and scout_selected not in ("unknown", ""):
        if intent_domain and intent_domain != scout_selected:
            console.print(
                f"[dim]{domain_label}已按面板选择设为 [bold]{scout_selected}[/bold]"
                f"（指令中的 {intent_domain} 已被覆盖）[/dim]"
            )
        return scout_selected

    # 2) 指令说了 A，Scout 建议 B → 冲突确认（默认采用 Scout 建议）
    if intent_domain and intent_domain != scout_suggested and scout_suggested != "unknown":
        console.print()
        console.print(Panel(
            f"您在指令中指定的{domain_label}: [bold cyan]{intent_domain}[/bold cyan]\n"
            f"Scout 扫描建议的{domain_label}: [bold yellow]{scout_suggested}[/bold yellow]\n\n"
            "扫描结果基于实际数据内容，通常更准确。",
            title=f"⚠ {domain_label}不一致",
            border_style="yellow", box=box.ROUNDED,
        ))
        keep = Prompt.ask(
            f"采用 [{scout_suggested}]（回车默认）还是保持 [{intent_domain}]？"
            " 输入 s 采用建议 / k 保持原领域",
            choices=["s", "k"], default="s",
        )
        return scout_suggested if keep == "s" else intent_domain

    # 3) 指令有值且 Scout 没建议
    if intent_domain:
        return intent_domain

    # 4) Scout 推断出来了
    if scout_suggested != "unknown":
        return scout_suggested

    # 5) 兜底：手动选择（此时 folder 一定非空）
    return _ensure_domain(
        None, folder_for_detect=folder,
        model_a=model_a, key_a=key_a,
    )


# ==========================================
# 智能路径发现（任意位置，不固定在 data/ outputs/）
# ==========================================
def _ask_folder_with_discovery(prompt_text: str) -> str:
    """带智能发现的路径输入：输入路径直返，回车扫当前目录候选"""
    console.print(f"\n[yellow]{prompt_text}[/yellow]")
    console.print(
        "[dim]（支持任意路径：相对/绝对/Windows/Linux；直接回车可扫描当前目录）[/dim]"
    )

    user_input = Prompt.ask("[cyan]路径[/cyan]").strip()
    if user_input:
        return user_input

    console.print("[dim]正在扫描当前目录下的候选数据文件夹...[/dim]")
    try:
        candidates = discover_data_folders(".", max_depth=3)
    except Exception as e:
        console.print(f"[yellow]扫描失败: {e}，请手动输入。[/yellow]")
        return Prompt.ask("[cyan]路径[/cyan]").strip()

    if not candidates:
        console.print("[yellow]未发现候选目录，请手动输入路径。[/yellow]")
        return Prompt.ask("[cyan]路径[/cyan]").strip()

    for i, c in enumerate(candidates, 1):
        flags = []
        if c.get("has_goal"):
            flags.append("[green]含目标[/green]")
        if c.get("has_table"):
            flags.append("[green]含表格[/green]")
        flag_str = " ".join(flags)
        console.print(
            f"  [cyan]{i}[/cyan]. {c['path']} "
            f"[dim]({c['file_count']} 文件) {flag_str}[/dim]"
        )

    choice = Prompt.ask("输入编号或直接填写路径", default="1").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(candidates):
        return candidates[int(choice) - 1]["abs_path"]
    return choice


def _ask_strategy_with_discovery(prompt_text: str) -> str:
    """带智能发现的策略文件输入：输入路径直返，回车扫当前目录候选"""
    console.print(f"\n[yellow]{prompt_text}[/yellow]")
    console.print("[dim]（支持任意路径；直接回车扫描当前目录下的策略文件）[/dim]")

    user_input = Prompt.ask("[cyan]路径[/cyan]").strip()
    if user_input:
        return user_input

    console.print("[dim]正在扫描当前目录下的候选策略文件...[/dim]")
    try:
        candidates = discover_strategy_files(".", max_depth=3)
    except Exception as e:
        console.print(f"[yellow]扫描失败: {e}，请手动输入。[/yellow]")
        return Prompt.ask("[cyan]路径[/cyan]").strip()

    if not candidates:
        console.print("[yellow]未发现候选策略文件，请手动输入。[/yellow]")
        return Prompt.ask("[cyan]路径[/cyan]").strip()

    for i, c in enumerate(candidates, 1):
        console.print(
            f"  [cyan]{i}[/cyan]. {c['path']} [dim]({c['size_kb']}KB)[/dim]"
        )

    choice = Prompt.ask("输入编号或直接填写路径", default="1").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(candidates):
        return candidates[int(choice) - 1]["abs_path"]
    return choice


# ==========================================
# 欢迎横幅（6-Agent 配置表 + 知识库信息）
# ==========================================
def show_welcome_banner(knowledge_dir: Optional[str] = None):
    console.clear()
    console.print("\n")

    logo_str = (
        "███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗\n"
        "██╔════╝██║████╗  ██║██╔══██╗████╗  ██║\n"
        "███████╗██║██╔██╗ ██║███████║██╔██╗ ██║\n"
        "╚════██║██║██║╚██╗██║██╔══██║██║╚██╗██║\n"
        "███████║██║██║ ╚████║██║  ██║██║ ╚████║\n"
        "╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝"
    )
    header = Text(justify="center")
    header.append(f"{logo_str}\n\n", style="bold #00f0ff")
    header.append("司 南 · 多 智 能 体 策 略 制 定 系 统\n", style="bold #cda353")
    header.append("Sinan Agent Engine v3.2.0  |  Status: ", style="dim #00f0ff")
    header.append("ONLINE\n", style="bold green")
    console.print(header)

    # ---- 6-Agent 模型分配表 ----
    configs = get_all_agent_configs()
    # 方案 2-A5：去掉 ◈ ◈
    table = Table(
        title="各智能体模型分配",
        box=box.ROUNDED, border_style="#cda353",
        show_header=True, header_style="bold #00f0ff",
    )
    table.add_column("智能体", justify="left", style="cyan")
    table.add_column("Provider", justify="center", style="yellow")
    table.add_column("API Key", justify="center")

    icon_map = {
        "SCOUT": "🔍", "RUBRIC_A": "🧩", "RUBRIC_B": "🧩",
        "STRATEGY_A": "🎯", "STRATEGY_B": "🎯", "JUDGE": "⚖️",
    }
    label_map = {
        "SCOUT": "文件侦察", "RUBRIC_A": "出题主编",
        "RUBRIC_B": "出题审查", "STRATEGY_A": "策略撰写",
        "STRATEGY_B": "策略反驳", "JUDGE": "判断智能体",
    }
    for name, cfg in configs.items():
        n = cfg.key_count()
        if n == 0:
            key_status = "[yellow]⚠ 默认[/yellow]"
        elif n == 1:
            # 方案 2-B5：✅ → ✓
            key_status = "[green]✓ x1[/green]"
        else:
            key_status = f"[green]✓ x{n} 轮询[/green]"
        table.add_row(
            f"{icon_map[name]} {label_map[name]}",
            cfg.provider,
            key_status,
        )
    console.print(Align.center(table))

    # ---- 知识库信息 ----
    kb = KnowledgeBase(knowledge_dir or "./knowledge")
    if kb.root.exists():
        snap = kb.load()
        summary = snap.summary()
        truncated = " [已截断]" if summary["truncated"] else ""
        console.print(
            f"[dim]📚 知识库: {kb.root} · "
            f"{summary['file_count']} 个文件 · "
            f"{summary['total_chars']} 字符{truncated}[/dim]"
        )
    else:
        console.print(f"[dim]📚 知识库: {kb.root}（不存在，跳过）[/dim]")

    console.print("\n")

    tips = (
        "[bold white]你可以直接输入快捷指令或说人话：[/bold white]\n"
        "  [#00f0ff]▸[/#00f0ff] [bold green]博弈[/bold green] / [bold green]模型博弈[/bold green]"
        "        — 6-Agent 双博弈生成策略\n"
        "  [#00f0ff]▸[/#00f0ff] [bold green]迭代策略[/bold green]        — 结合新数据复盘进化策略\n"
        "  [#00f0ff]▸[/#00f0ff] 帮我制定 ./anywhere/my_data 的电商策略\n"
        "  [#00f0ff]▸[/#00f0ff] 对比 /abs/path/a.md 和 D:\\\\plans\\\\b.md\n\n"
        "[dim]输入 [bold red]/exit[/bold red] 退出 | "
        "[bold cyan]/help[/bold cyan] 查看帮助 | "
        "[bold yellow]Ctrl+C 中断任务[/bold yellow][/dim]"
    )
    # 方案 2-A6：去掉 ◤ ◢；DOUBLE_EDGE → ROUNDED
    console.print(Panel(
        tips,
        title="[bold #00f0ff]SINAN CONTROL CENTER[/bold #00f0ff]",
        subtitle="[dim #cda353]Multi-Agent Debate Mode Ready[/dim #cda353]",
        border_style="#00f0ff", box=box.ROUNDED, padding=(1, 2),
    ))
    console.print("\n")


def _show_help():
    # 方案 2-G：• → ▸，统一符号
    console.print(Panel(
        "  ▸ [bold]快捷指令（精准命中，不经过 LLM）：[/bold]\n"
        "  ▸ [green]模型博弈[/green] / [green]博弈[/green] → 6-Agent 双博弈生成策略\n"
        "  ▸ [green]迭代策略[/green] / [green]进化[/green] → 结合新数据复盘进化\n\n"
        "  ▸ [bold]自然语言同样支持（路径可以是任意位置）：[/bold]\n"
        "  ▸ [cyan]generate[/cyan] 帮我制定 ./anywhere/foo 的电商策略\n"
        "  ▸ [cyan]compare[/cyan]  对比 /abs/a.md 和 D:\\\\b.md\n"
        "  ▸ [cyan]evolve[/cyan]   根据新数据进化抖音策略\n\n"
        "  ▸ [bold]路径说明：[/bold]\n"
        "    · 相对 / 绝对 / Windows / Linux 路径都支持\n"
        "    · 数据目录或单个文件都可以\n"
        "    · 直接回车可扫描当前目录找候选\n\n"
        "  ▸ [bold]支持领域：[/bold] ecommerce / github / atomgit / douyin / tiktok / 自定义\n"
        "  ▸ [bold]6-Agent 架构：[/bold]\n"
        "    🔍 [cyan]文件侦察[/cyan]       → 扫描目录，识别数据内容，与用户确认目标\n"
        "    🧩 [magenta]出题组 A ⇄ B[/magenta]  → 三轮博弈产生 Rubric 演进\n"
        "    ⚖️ [yellow]判断智能体[/yellow]       → 汇总出题博弈，独立裁定最终 Rubric\n"
        "    🎯 [blue]策略组 A ⇄ B[/blue]   → 三轮博弈产生策略演进（上下文与出题组隔离）\n"
        "    ⚖️ [yellow]判断智能体[/yellow]       → 汇总策略博弈，裁定最终策略 + 分数\n"
        "  ▸ [bold]知识库（只读共享）：[/bold] ./knowledge · 通过 --knowledge-dir 或 SINAN_KNOWLEDGE_DIR 指定\n"
        "  ▸ [bold]模型分配：[/bold] .env 中的 SINAN_<AGENT>_PROVIDER / _API_KEY(S)\n"
        "  ▸ [bold]多 key 支持：[/bold] SINAN_<PROVIDER>_API_KEYS=a,b,c 自动轮询\n"
        "  ▸ [bold]输出目录：[/bold] --output-dir / -o 或 .env 中 SINAN_OUTPUT_DIR\n"
        "  ▸ [bold]硬性规则：[/bold] 生成前后双校验，见 configs/rules.yaml\n"
        "  ▸ [bold]打断快捷键：[/bold] 任务运行时按 [bold yellow]Ctrl+C[/bold yellow] 中断当前任务\n"
        "  ▸ [bold]退出程序：[/bold] 输入 /exit 或 [bold yellow]Ctrl+C[/bold yellow]（在提示符处）",
        title="司南帮助",
        style="cyan",
    ))


# ==========================================
# 侦察展示 & 交互确认
# ==========================================
def _render_scout_panel(scout_result: dict) -> None:
    scan = scout_result.get("scan", {})
    report = scout_result.get("report", {})

    console.print()
    # 方案 2-C：DOUBLE_EDGE → ROUNDED（保留 🔍）
    console.print(Panel.fit(
        "[bold cyan]🔍 文件侦察智能体 · 预审报告[/bold cyan]",
        border_style="cyan", box=box.ROUNDED,
    ))

    conf = report.get("confidence", 0)
    # 方案 2-F1：去掉 📋
    console.print(Panel(
        f"{report.get('business_overview', '（无）')}\n\n"
        f"[dim]置信度: {conf:.0%}  |  "
        f"文件数: {scan.get('total_files', 0)}  |  "
        f"总大小: {scan.get('total_size_mb', 0)} MB[/dim]",
        title="业务概览", border_style="cyan", box=box.ROUNDED,
    ))

    domain = report.get("suggested_domain", "unknown")
    stype = report.get("suggested_strategy_type", "") or "（未建议）"
    # 方案 2-F2：去掉 🎯
    console.print(Panel(
        f"领域: [bold yellow]{domain}[/bold yellow]\n"
        f"建议策略: [bold green]{stype}[/bold green]",
        title="初步判断", border_style="yellow", box=box.ROUNDED,
    ))

    targets = report.get("key_targets", []) or []
    if targets:
        # 方案 2-F3：去掉 🗂
        console.print(Panel(
            "\n".join(f"  • [cyan]{t}[/cyan]" for t in targets),
            title="关键目标文件", border_style="green", box=box.ROUNDED,
        ))

    groups = scan.get("groups", {})
    label_map = {
        "data": ("📊 数据", "green"),
        "document": ("📄 文档", "cyan"),
        "config": ("⚙️  配置", "yellow"),
        "code": ("💻 代码", "blue"),
        "other": ("📦 其他", "dim"),
    }
    for key in ["data", "document", "config", "code", "other"]:
        items = groups.get(key, []) or []
        if not items:
            continue
        label, color = label_map[key]
        lines = []
        for f in items[:10]:
            lines.append(f"  • {f['path']} [dim]({f['size_kb']}KB)[/dim]")
        if len(items) > 10:
            lines.append(f"  [dim]... 还有 {len(items) - 10} 个[/dim]")
        console.print(Panel(
            "\n".join(lines),
            title=f"{label}（{len(items)}）",
            border_style=color, box=box.ROUNDED,
        ))

    questions = report.get("clarifying_questions", []) or []
    if questions:
        # 方案 2-F4：去掉 🤔
        console.print(Panel(
            "\n".join(f"  ❓ {q}" for q in questions),
            title="需确认的问题", border_style="magenta", box=box.ROUNDED,
        ))


def _run_scout_and_confirm(
    folder: str,
    scout_model: Optional[str],
    scout_key: Optional[str],
    knowledge_text: str = "",
    _depth: int = 0,
) -> dict:
    """
    返回:
      {
        mode: "folder" | "subset" | "manual",
        folder: str,
        extra_instruction: str,
        suggested_domain: str,     # Scout 原始推断
        selected_domain: str,      # 用户最终确认/修改的领域（方案 1-④ 新增）
      }
    """
    if _depth > 3:
        console.print("[yellow]换目录次数过多，直接使用当前目录继续。[/yellow]")
        return {
            "mode": "folder", "folder": folder,
            "extra_instruction": "",
            "suggested_domain": "unknown",
            "selected_domain": "unknown",
        }

    console.print(f"[dim]🔍 正在扫描文件夹并侦察内容: {folder}[/dim]")
    try:
        scout_result = scout_folder(
            folder, scout_model, scout_key, knowledge=knowledge_text,
        )
    except Exception as e:
        console.print(f"[yellow]⚠ 侦察失败({e})，跳过预审直接生成。[/yellow]")
        return {
            "mode": "folder", "folder": folder,
            "extra_instruction": "",
            "suggested_domain": "unknown",
            "selected_domain": "unknown",
        }

    _render_scout_panel(scout_result)
    report = scout_result.get("report", {})
    suggested_domain = report.get("suggested_domain", "unknown") or "unknown"

    # 用户对领域的选择（默认 == suggested，直到用户主动改）
    selected_domain = suggested_domain

    console.print()
    # 方案 1-④：4 选项 → 5 选项
    console.print(Panel(
        f"  [cyan][1][/cyan] 确认 — 使用建议领域 [bold]{suggested_domain}[/bold]，用该文件夹全部内容\n"
        "  [cyan][2][/cyan] 更换领域 — 不用建议领域，手动选择/输入\n"
        "  [cyan][3][/cyan] 只用部分文件 — 手动指定使用哪些文件\n"
        "  [cyan][4][/cyan] 手动口述目标 — 跳过文件内容，直接描述策略目标\n"
        "  [cyan][5][/cyan] 换一个文件夹重新扫描",
        title="请选择下一步", border_style="#cda353", box=box.ROUNDED,
    ))

    while True:
        try:
            choice = Prompt.ask(
                "输入编号", choices=["1", "2", "3", "4", "5"], default="1"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]已取消，使用全部内容继续。[/dim]")
            return {
                "mode": "folder", "folder": folder,
                "extra_instruction": "",
                "suggested_domain": suggested_domain,
                "selected_domain": selected_domain,
            }

        # [1] 确认
        if choice == "1":
            return {
                "mode": "folder", "folder": folder,
                "extra_instruction": "",
                "suggested_domain": suggested_domain,
                "selected_domain": selected_domain,
            }

        # [2] 更换领域（改完后回菜单）
        if choice == "2":
            new_domain = _ask_domain_override(suggested_domain)
            if new_domain == suggested_domain:
                console.print("[dim]保持建议领域，回到菜单。[/dim]")
                continue
            selected_domain = new_domain
            console.print(
                f"[green]领域已切换为: [bold]{selected_domain}[/bold][/green]"
            )
            continue

        # [3] 只用部分文件
        if choice == "3":
            sub = Prompt.ask("请输入要使用的文件/子目录路径（逗号分隔）").strip()
            if not sub:
                console.print("[yellow]未输入，返回菜单[/yellow]")
                continue
            return {
                "mode": "subset", "folder": folder,
                "extra_instruction": sub,
                "suggested_domain": suggested_domain,
                "selected_domain": selected_domain,
            }

        # [4] 手动口述
        if choice == "4":
            console.print(
                "[dim]请描述要制定什么策略、基于什么信息。"
                "逐行输入，单行 END 结束。[/dim]"
            )
            lines = []
            while True:
                try:
                    ln = Prompt.ask(">")
                except (KeyboardInterrupt, EOFError):
                    break
                if ln.strip().upper() == "END":
                    break
                if ln.strip():
                    lines.append(ln)
            manual = "\n".join(lines).strip()
            if not manual:
                console.print("[yellow]未输入，返回菜单[/yellow]")
                continue
            return {
                "mode": "manual", "folder": "",
                "extra_instruction": manual,
                "suggested_domain": suggested_domain,
                "selected_domain": selected_domain,
            }

        # [5] 换文件夹
        if choice == "5":
            new_folder = _ask_folder_with_discovery("请输入新文件夹路径")
            if new_folder and Path(new_folder).exists():
                return _run_scout_and_confirm(
                    new_folder, scout_model, scout_key,
                    knowledge_text, _depth=_depth + 1,
                )
            console.print("[red]路径无效，请重试[/red]")


# ==========================================
# 任务执行
# ==========================================
def _run_generate(
    intent: dict,
    domain: Optional[str],
    model_a: Optional[str],
    key_a: Optional[str],
    model_b: Optional[str],
    key_b: Optional[str],
    judge_model: Optional[str],
    judge_key: Optional[str],
    scout_model: Optional[str],
    scout_key: Optional[str],
    output_dir: Optional[str] = None,
    knowledge_dir: Optional[str] = None,
    knowledge_text: str = "",
) -> str:
    folder = intent.get("folder_a") or ""
    if not folder:
        folder = _ask_folder_with_discovery(
            "请提供包含目标和数据的文件夹路径"
        )

    # ★ Scout 预审（知识库一并注入）
    scout = _run_scout_and_confirm(
        folder, scout_model, scout_key, knowledge_text,
    )

    # 方案 1-②：领域决策（面板选择 > 指令显式 > Scout 建议 > 手动兜底）
    domain = _decide_domain_after_scout(
        domain, scout, folder, model_a, key_a,
    )
    console.print(f"[dim]最终领域: [bold]{domain}[/bold][/dim]")

    # 根据 Scout 模式构造 extra_context
    mode = scout.get("mode")
    if mode == "manual":
        extra_context = (
            f"【用户口述策略目标（最高优先级，严格遵循）】\n"
            f"{scout['extra_instruction']}"
        )
        actual_folder = folder
        console.print(Panel(
            f"[bold]将基于您的口述制定策略：[/bold]\n"
            f"{scout['extra_instruction'][:500]}",
            border_style="yellow", box=box.ROUNDED,
        ))
    elif mode == "subset":
        extra_context = (
            f"【用户指定只用以下文件/子目录作为依据】\n"
            f"{scout['extra_instruction']}"
        )
        actual_folder = folder
    else:
        extra_context = ""
        actual_folder = folder

    console.print(
        f"[dim]开始为「[bold]{domain}[/bold]」制定策略，"
        f"数据源: {actual_folder}[/dim]"
    )
    result = generate_agent(
        data_folder=actual_folder,
        domain=domain,
        model_a=model_a, key_a=key_a,
        model_b=model_b, key_b=key_b,
        judge_model=judge_model, judge_key=judge_key,
        output_dir=output_dir,
        event_callback=_make_debate_renderer(),
        extra_context=extra_context,
        knowledge_dir=knowledge_dir,
    )

    render_final_summary(result)
    console.print()
    # 方案 2-E1：去掉 ★，改用 title
    console.print(Panel.fit(
        f"[bold yellow]Judge 最终评分：{result['total_score']}/100[/bold yellow]",
        title="评分", style="bold green",
    ))

    strategy_file = result.get("strategy_file")
    if strategy_file and Path(strategy_file).exists():
        # 方案 2-D1："=" * 60 → console.rule()
        console.rule()
        console.print(Markdown(Path(strategy_file).read_text(encoding="utf-8")))
        console.rule()

    console.print(f"策略已保存: [bold green]{result.get('strategy_file', '?')}[/bold green]")
    console.print(f"Rubric 已保存: [bold green]{result.get('rubric_file', '?')}[/bold green]")
    console.print(f"辩论记录: [bold green]{result.get('history_file', '?')}[/bold green]")

    return (
        f"用户刚才为 {actual_folder}（{domain}）生成了初始策略，"
        f"存于 {result.get('strategy_file', '?')}"
    )


def _run_compare(
    intent: dict,
    domain: str,
    model_a: Optional[str],
    key_a: Optional[str],
    knowledge_dir: Optional[str] = None,
) -> str:
    folder_a = intent.get("folder_a") or ""
    folder_b = intent.get("folder_b") or ""
    if not folder_a:
        folder_a = _ask_strategy_with_discovery(
            "请提供方案 A 的策略文件路径"
        )
    if not folder_b:
        folder_b = _ask_strategy_with_discovery(
            "请提供方案 B 的策略文件路径"
        )

    console.print(f"[dim]对比方案: {folder_a} vs {folder_b}[/dim]")
    console.print("[dim]⏳ 判断智能体评估中...  [bold yellow](Ctrl+C 可中断)[/bold yellow][/dim]")

    result = compare_strategies(
        folder_a, folder_b, domain, model_a, key_a,
        knowledge_dir=knowledge_dir,
    )

    # 方案 2-D3："=" * 60 → console.rule()
    console.print(f"\n胜出: [bold yellow]{result.get('winner', 'Tie')}[/bold yellow]")
    console.rule()
    console.print(Markdown(f"**裁判理由:**\n{result.get('reason', '')}"))
    console.rule()
    return "用户刚才对比了两个策略方案"


def _run_evolve(
    intent: dict,
    domain: Optional[str],
    model_a: Optional[str],
    key_a: Optional[str],
    model_b: Optional[str],
    key_b: Optional[str],
    judge_model: Optional[str],
    judge_key: Optional[str],
    scout_model: Optional[str],
    scout_key: Optional[str],
    output_dir: Optional[str] = None,
    knowledge_dir: Optional[str] = None,
    knowledge_text: str = "",
) -> str:
    history_path = intent.get("history_folder") or ""
    new_data = intent.get("new_data_folder") or ""
    if not history_path:
        history_path = _ask_strategy_with_discovery(
            "请提供上一版策略的文件路径"
        )
    if not new_data:
        new_data = _ask_folder_with_discovery(
            "请提供新目标和新数据所在的文件夹路径"
        )

    # ★ Scout 预审（针对新数据）
    scout = _run_scout_and_confirm(
        new_data, scout_model, scout_key, knowledge_text,
    )

    # 方案 1-⑥：领域决策（复用 _decide_domain_after_scout）
    domain = _decide_domain_after_scout(
        domain, scout, new_data, model_a, key_a,
        domain_label="新数据领域",
    )
    console.print(f"[dim]最终领域: [bold]{domain}[/bold][/dim]")

    mode = scout.get("mode")
    if mode == "manual":
        extra_context = (
            f"【用户口述策略目标（最高优先级）】\n"
            f"{scout['extra_instruction']}"
        )
    elif mode == "subset":
        extra_context = (
            f"【用户指定只用以下文件/子目录作为依据】\n"
            f"{scout['extra_instruction']}"
        )
    else:
        extra_context = ""

    # 方案 2-A8：去掉 ⟳
    console.print("[dim]启动进化复盘...[/dim]")
    result = evolve_agent(
        old_strategy_path=history_path,
        new_data_folder=new_data,
        domain=domain,
        model_a=model_a, key_a=key_a,
        model_b=model_b, key_b=key_b,
        judge_model=judge_model, judge_key=judge_key,
        output_dir=output_dir,
        event_callback=_make_debate_renderer(),
        extra_context=extra_context,
        knowledge_dir=knowledge_dir,
    )

    render_final_summary(result)
    console.print()
    # 方案 2-E2：去掉 ★
    console.print(Panel.fit(
        f"[bold yellow]Judge 最终 V2 评分：{result['total_score']}/100[/bold yellow]",
        title="评分", style="bold green",
    ))

    strategy_file = result.get("strategy_file")
    if strategy_file and Path(strategy_file).exists():
        # 方案 2-D2："=" * 60 → console.rule()
        console.rule()
        console.print(Markdown(Path(strategy_file).read_text(encoding="utf-8")))
        console.rule()

    console.print(f"V2 策略已保存: [bold green]{result.get('strategy_file', '?')}[/bold green]")
    console.print(f"辩论记录: [bold green]{result.get('history_file', '?')}[/bold green]")
    return f"用户刚才进化了策略，基于 {history_path} 和新数据 {new_data}"


# ==========================================
# 核心 chat 循环
# ==========================================
def _chat_loop(
    model_a: Optional[str],
    key_a: Optional[str],
    model_b: Optional[str],
    key_b: Optional[str],
    judge_model: Optional[str],
    judge_key: Optional[str],
    scout_model: Optional[str],
    scout_key: Optional[str],
    output_dir: Optional[str] = None,
    knowledge_dir: Optional[str] = None,
):
    # 一次性加载知识库（全程复用）
    knowledge_text = load_knowledge_text(knowledge_dir)

    show_welcome_banner(knowledge_dir)
    _validate_configs()
    _validate_knowledge_dir()

    parser = IntentParser(provider_name=model_a, api_key=key_a)
    context = ""

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]你[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim] 再见！[/dim]")
            break

        if not user_input.strip():
            continue

        stripped = user_input.strip()
        lower = stripped.lower()

        if lower in EXIT_WORDS:
            console.print("[dim] 再见！[/dim]")
            break
        if lower in {"/help", "help", "帮助"}:
            _show_help()
            continue

        if stripped in EXPLICIT_ACTIONS:
            action_override = EXPLICIT_ACTIONS[stripped]
            intent = {
                "action": action_override,
                "domain": "unknown",
                "folder_a": "",
                "folder_b": "",
                "history_folder": "",
                "new_data_folder": "",
                "confidence": 1.0,
                "clarify": "",
            }
            # 方案 2-A7：去掉 ↯
            console.print(f"[dim]快捷指令命中：{stripped} → {action_override}[/dim]")
        else:
            console.print("[dim]正在解析指令...[/dim]")
            try:
                intent = parser.parse(user_input, context)
            except Exception as e:
                console.print(f"[bold red] ✕ 意图解析失败: {e}[/bold red]")
                continue

        action = intent.get("action", "unknown")
        domain = (intent.get("domain") or intent.get("platform") or "unknown").lower()
        confidence = intent.get("confidence", 0)

        if action == "unknown" or confidence < 0.5:
            clarify_msg = intent.get("clarify") or "请说清楚你想做什么（生成 / 对比 / 进化）"
            # 方案 2-B6：🤔 → ?
            console.print(f"[yellow]? {clarify_msg}[/yellow]")
            continue
        if action == "help":
            _show_help()
            continue

        # 方案 1-①：不在 chat_loop 决定领域，交给 _run_generate / _run_evolve
        # 在 Scout 之后决定；这里只打印占位
        domain_display = (
            domain if domain not in ("unknown", "", None) else "待 Scout 推断"
        )
        console.print(
            f"[dim]识别到 → 动作: [bold]{action}[/bold] | "
            f"领域: [bold]{domain_display}[/bold][/dim]"
        )

        try:
            if action in ["generate", "run"]:
                context = _run_generate(
                    intent, domain, model_a, key_a,
                    model_b, key_b, judge_model, judge_key,
                    scout_model, scout_key,
                    output_dir, knowledge_dir, knowledge_text,
                )
            elif action == "compare":
                context = _run_compare(
                    intent, domain, model_a, key_a, knowledge_dir,
                )
            elif action == "evolve":
                context = _run_evolve(
                    intent, domain, model_a, key_a,
                    model_b, key_b, judge_model, judge_key,
                    scout_model, scout_key,
                    output_dir, knowledge_dir, knowledge_text,
                )
            else:
                console.print(f"[yellow]暂不支持的动作: {action}[/yellow]")
        except KeyboardInterrupt:
            console.print(
                "\n[bold yellow]⏸ 已中断当前任务（本次进度不保留），返回主菜单[/bold yellow]"
            )
            context = ""
        except Exception as e:
            console.print(f"[bold red] ✕ 执行失败: {e}[/bold red]")
            context = ""


# ==========================================
# 根命令
# ==========================================
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    model_a: str = typer.Option(None, "--model-a",
        help="覆盖出题组A/策略组A 的 provider（默认读 .env）"),
    key_a: str = typer.Option(None, "--key-a",
        help="覆盖出题组A/策略组A 的单个 API Key（池请用 .env）"),
    model_b: str = typer.Option(None, "--model-b",
        help="覆盖出题组B/策略组B 的 provider"),
    key_b: str = typer.Option(None, "--key-b",
        help="覆盖出题组B/策略组B 的单个 API Key"),
    judge_model: str = typer.Option(None, "--judge-model",
        help="覆盖判断智能体的 provider"),
    judge_key: str = typer.Option(None, "--judge-key",
        help="覆盖判断智能体的单个 API Key"),
    scout_model: str = typer.Option(None, "--scout-model",
        help="覆盖文件侦察智能体的 provider"),
    scout_key: str = typer.Option(None, "--scout-key",
        help="覆盖文件侦察智能体的单个 API Key"),
    output_dir: str = typer.Option(None, "--output-dir", "-o",
        help="输出目录（默认 ./outputs 或 .env 中 SINAN_OUTPUT_DIR）"),
    knowledge_dir: str = typer.Option(None, "--knowledge-dir", "-k",
        help="知识库目录（默认 ./knowledge 或 .env 中 SINAN_KNOWLEDGE_DIR）"),
):
    """司南 (Sinan) —— 不带子命令时直接进入交互式 chat 模式"""
    if ctx.invoked_subcommand is None:
        _chat_loop(
            model_a, key_a, model_b, key_b,
            judge_model, judge_key, scout_model, scout_key,
            output_dir, knowledge_dir,
        )


# ==========================================
# 子命令
# ==========================================
@app.command()
def generate(
    folder_path: str = typer.Argument(..., help="包含目标和数据的文件夹或文件（任意路径）"),
    domain: str = typer.Option(None, "--domain", "-d", help="业务领域（不填自动探测）"),
    output_dir: str = typer.Option(None, "--output-dir", "-o",
        help="输出目录（默认 ./outputs 或 .env 中 SINAN_OUTPUT_DIR）"),
    knowledge_dir: str = typer.Option(None, "--knowledge-dir", "-k",
        help="知识库目录（默认 ./knowledge 或 .env 中 SINAN_KNOWLEDGE_DIR）"),
    model_a: str = typer.Option(None, help="覆盖出题组A/策略组A 的 provider"),
    key_a: str = typer.Option(None, help="覆盖出题组A/策略组A 的单个 API Key"),
    model_b: str = typer.Option(None, help="覆盖出题组B/策略组B 的 provider"),
    key_b: str = typer.Option(None, help="覆盖出题组B/策略组B 的单个 API Key"),
    judge_model: str = typer.Option(None, help="覆盖判断智能体的 provider"),
    judge_key: str = typer.Option(None, help="覆盖判断智能体的单个 API Key"),
    scout_model: str = typer.Option(None, help="覆盖文件侦察智能体的 provider"),
    scout_key: str = typer.Option(None, help="覆盖文件侦察智能体的单个 API Key"),
):
    """🧩 文件侦察 → 出题组博弈 → Judge 定题 → 策略组博弈 → Judge 定稿"""
    _validate_configs()
    _validate_knowledge_dir()

    knowledge_text = load_knowledge_text(knowledge_dir)
    intent = {"folder_a": folder_path}
    try:
        _run_generate(
            intent, domain, model_a, key_a,
            model_b, key_b, judge_model, judge_key,
            scout_model, scout_key,
            output_dir, knowledge_dir, knowledge_text,
        )
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⏸ 任务已中断[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red] ✕ 生成失败: {e}[/bold red]")


@app.command()
def evolve(
    old_strategy_path: str = typer.Argument(..., help="上一版策略路径（任意位置）"),
    new_data_folder: str = typer.Argument(..., help="新目标/新数据文件夹（任意位置）"),
    domain: str = typer.Option(None, "--domain", "-d", help="业务领域"),
    output_dir: str = typer.Option(None, "--output-dir", "-o",
        help="输出目录（默认 ./outputs 或 .env 中 SINAN_OUTPUT_DIR）"),
    knowledge_dir: str = typer.Option(None, "--knowledge-dir", "-k",
        help="知识库目录（默认 ./knowledge 或 .env 中 SINAN_KNOWLEDGE_DIR）"),
    model_a: str = typer.Option(None, help="覆盖出题组A/策略组A 的 provider"),
    key_a: str = typer.Option(None, help="覆盖出题组A/策略组A 的单个 API Key"),
    model_b: str = typer.Option(None, help="覆盖出题组B/策略组B 的 provider"),
    key_b: str = typer.Option(None, help="覆盖出题组B/策略组B 的单个 API Key"),
    judge_model: str = typer.Option(None, help="覆盖判断智能体的 provider"),
    judge_key: str = typer.Option(None, help="覆盖判断智能体的单个 API Key"),
    scout_model: str = typer.Option(None, help="覆盖文件侦察智能体的 provider"),
    scout_key: str = typer.Option(None, help="覆盖文件侦察智能体的单个 API Key"),
):
    """⟳ 结合上一版策略与新数据，走 6-Agent 全流程生成 V2"""
    _validate_configs()
    _validate_knowledge_dir()

    # 方案 2-A9：去掉 ⟳
    console.print(Panel.fit(
        f"启动进化复盘\n"
        f"旧策略: {old_strategy_path}\n"
        f"新数据: {new_data_folder}",
        style="bold magenta",
    ))
    knowledge_text = load_knowledge_text(knowledge_dir)
    intent = {
        "history_folder": old_strategy_path,
        "new_data_folder": new_data_folder,
    }
    try:
        _run_evolve(
            intent, domain, model_a, key_a,
            model_b, key_b, judge_model, judge_key,
            scout_model, scout_key,
            output_dir, knowledge_dir, knowledge_text,
        )
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⏸ 任务已中断[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]✕ 进化失败: {e}[/bold red]")


@app.command()
def compare(
    strategy_a: str = typer.Argument(..., help="策略 A 的文件路径（任意位置）"),
    strategy_b: str = typer.Argument(..., help="策略 B 的文件路径（任意位置）"),
    domain: str = typer.Option("ecommerce", "--domain", "-d", help="业务领域"),
    knowledge_dir: str = typer.Option(None, "--knowledge-dir", "-k",
        help="知识库目录（默认 ./knowledge 或 .env 中 SINAN_KNOWLEDGE_DIR）"),
    model_a: str = typer.Option(None, help="覆盖裁判模型 provider"),
    key_a: str = typer.Option(None, help="覆盖裁判模型单个 API Key"),
):
    """⚖️ Judge 裁定模式：对比两份策略方案的优劣"""
    # 方案 2-A10：去掉 ⊗；"对决" → "对比"
    console.print(Panel.fit(
        f"司南策略对比启动\n"
        f"领域: [bold cyan]{domain}[/bold cyan]\n"
        f"方案 A: [yellow]{strategy_a}[/yellow]\n"
        f"方案 B: [yellow]{strategy_b}[/yellow]",
        style="bold magenta",
    ))
    intent = {"folder_a": strategy_a, "folder_b": strategy_b}
    try:
        _run_compare(intent, domain, model_a, key_a, knowledge_dir)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⏸ 任务已中断[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]✕ 对比失败: {e}[/bold red]")


@app.command()
def chat(
    model_a: str = typer.Option(None, help="覆盖出题组A/策略组A 的 provider"),
    key_a: str = typer.Option(None, help="覆盖出题组A/策略组A 的单个 API Key"),
    model_b: str = typer.Option(None, help="覆盖出题组B/策略组B 的 provider"),
    key_b: str = typer.Option(None, help="覆盖出题组B/策略组B 的单个 API Key"),
    judge_model: str = typer.Option(None, help="覆盖判断智能体的 provider"),
    judge_key: str = typer.Option(None, help="覆盖判断智能体的单个 API Key"),
    scout_model: str = typer.Option(None, help="覆盖文件侦察智能体的 provider"),
    scout_key: str = typer.Option(None, help="覆盖文件侦察智能体的单个 API Key"),
    output_dir: str = typer.Option(None, "--output-dir", "-o",
        help="输出目录（默认 ./outputs 或 .env 中 SINAN_OUTPUT_DIR）"),
    knowledge_dir: str = typer.Option(None, "--knowledge-dir", "-k",
        help="知识库目录（默认 ./knowledge 或 .env 中 SINAN_KNOWLEDGE_DIR）"),
):
    """交互式对话模式（与直接运行 sinan 等价）"""
    _chat_loop(
        model_a, key_a, model_b, key_b,
        judge_model, judge_key, scout_model, scout_key,
        output_dir, knowledge_dir,
    )


if __name__ == "__main__":
    app()