"""
司南 v3.2 多智能体编排器

职责
----
· 加载 5 个 Agent 的模型配置（从 .env 按 Agent 粒度读取，显式参数可覆盖）
· 支持单 key（str）与 key 池（List[str]），池模式由 llm_factory 全局轮询
· 知识库注入：将只读知识库文本传给所有 Agent（Scout 由 main.py 单独处理）
· 编排 Rubric 组三轮博弈 → Judge 定题 → Strategy 组三轮博弈 → Judge 定稿
· 落实上下文隔离规则：
    - Rubric 组 history ✗→ Strategy 组
    - Strategy 组 history ✗→ Rubric 组
    - Judge 的 _memory ✗→ 任何 Agent
    - Judge 只向外部输出「决策产物」（final_rubric / final_strategy）
· 通过 event_callback 实时推送每轮事件（供 CLI 渲染）
"""
from typing import Optional, Callable, List, Dict, Any, Union

from agent.agents.rubric_agents import RubricAgentA, RubricAgentB
from agent.agents.strategy_agents import StrategyAgentA, StrategyAgentB
from agent.agents.judge import JudgeAgent
from agent.core.agent_config import get_agent_config
from agent.schemas import (
    RubricSchema,
    RubricDecision,
    StrategySchema,
    StrategyDecision,
)


# ==========================================
# 常量
# ==========================================
DEFAULT_ROUNDS = 3

# key 参数类型：单 key（str）或 key 池（List[str]）
KeyArg = Optional[Union[str, List[str]]]


# ==========================================
# 编排器
# ==========================================
class DebateOrchestrator:
    """
    5-Agent 编排：

    Phase 1: Rubric 组（A ⇄ B）三轮博弈
    Phase 2: Judge 裁定最终 Rubric
    Phase 3: Strategy 组（A ⇄ B）三轮博弈（只接收 final_rubric）
    Phase 4: Judge 裁定最终策略（打分 + 缺陷 + 改进）
    """

    def __init__(
        self,
        model_a: Optional[str] = None,
        key_a: KeyArg = None,
        model_b: Optional[str] = None,
        key_b: KeyArg = None,
        judge_model: Optional[str] = None,
        judge_key: KeyArg = None,
        event_callback: Optional[Callable] = None,
        rounds: int = DEFAULT_ROUNDS,
        knowledge: str = "",
    ):
        """
        参数
        ----
        model_a / key_a : 覆盖 RUBRIC_A 和 STRATEGY_A 的配置
                          key_a 可为单 key（str）或 key 池（List[str]）
        model_b / key_b : 覆盖 RUBRIC_B 和 STRATEGY_B 的配置
        judge_model / judge_key : 覆盖 JUDGE 的配置
        event_callback : 实时事件推送回调
        rounds : 每组博弈的轮数，默认 3
        knowledge : 知识库只读文本（由 main.py 加载后传入）

        优先级：显式参数 > .env 中 SINAN_<AGENT>_* > SINAN_DEFAULT_PROVIDER
        """
        # ---------- 从 .env 读取每个 Agent 的默认配置 ----------
        cfg_rub_a = get_agent_config("RUBRIC_A")
        cfg_rub_b = get_agent_config("RUBRIC_B")
        cfg_str_a = get_agent_config("STRATEGY_A")
        cfg_str_b = get_agent_config("STRATEGY_B")
        cfg_judge = get_agent_config("JUDGE")

        # ---------- 显式参数 > .env ----------
        self.rubric_a = RubricAgentA(
            model_a or cfg_rub_a.provider,
            key_a if key_a else cfg_rub_a.api_keys,
            knowledge=knowledge,
        )
        self.rubric_b = RubricAgentB(
            model_b or cfg_rub_b.provider,
            key_b if key_b else cfg_rub_b.api_keys,
            knowledge=knowledge,
        )
        self.strategy_a = StrategyAgentA(
            model_a or cfg_str_a.provider,
            key_a if key_a else cfg_str_a.api_keys,
            knowledge=knowledge,
        )
        self.strategy_b = StrategyAgentB(
            model_b or cfg_str_b.provider,
            key_b if key_b else cfg_str_b.api_keys,
            knowledge=knowledge,
        )
        self.judge = JudgeAgent(
            judge_model or cfg_judge.provider,
            judge_key if judge_key else cfg_judge.api_keys,
            knowledge=knowledge,
        )

        self.event_callback = event_callback
        self.rounds = rounds
        self.knowledge = knowledge

    # ==========================================
    # 事件推送
    # ==========================================
    def _emit(
        self,
        phase: str,          # "start" | "before" | "after" | "decision"
        group: str,          # "rubric" | "strategy" | "judge"
        speaker: str,        # "A" | "B" | "judge" | ""
        role: str,           # 人类可读角色名
        round_n: int,        # 轮次（0 表示非轮次事件）
        content: Any = None, # 输出内容（dict / str）
        comment: str = "",   # 附加说明
    ) -> None:
        if not self.event_callback:
            return
        self.event_callback({
            "phase": phase,
            "group": group,
            "speaker": speaker,
            "role": role,
            "round": round_n,
            "content": content,
            "comment": comment,
        })

    # ==========================================
    # 阶段 1：Rubric 组三轮博弈
    # ==========================================
    def _run_rubric_debate(
        self,
        goal: str,
        domain: str,
        rule_constraints: str,
    ) -> List[Dict]:
        """返回 Rubric 演进 history（供 Judge 决策使用，不外传给策略组）"""
        history: List[Dict] = []
        self._emit("start", "rubric", "", "🧩 出题组三轮博弈", 0)

        # ---------- Round 0：A 出初稿 ----------
        self._emit("before", "rubric", "A", "初始出题", 0)
        rubric = self.rubric_a.draft(goal, domain, rule_constraints)
        self._emit(
            "after", "rubric", "A", "初始出题", 0,
            content=rubric.model_dump(),
            comment=rubric.rationale or "初始 Rubric 已生成",
        )
        history.append({
            "round": 0, "speaker": "A", "role": "初始出题",
            "content": rubric.model_dump(),
            "comment": rubric.rationale or "",
        })

        # ---------- 第 1..N 轮：B 审核 → A 修订 ----------
        for i in range(1, self.rounds + 1):
            # B 审核
            self._emit("before", "rubric", "B", f"第 {i} 轮审核", i)
            rubric, note = self.rubric_b.review(
                rubric, goal, domain, i, rule_constraints,
            )
            self._emit(
                "after", "rubric", "B", f"第 {i} 轮审核", i,
                content=rubric.model_dump(),
                comment=note,
            )
            history.append({
                "round": i, "speaker": "B", "role": f"第 {i} 轮审核",
                "content": rubric.model_dump(), "comment": note,
            })

            if i < self.rounds:
                self._emit("before", "rubric", "A", f"第 {i} 轮修改", i)
                rubric = self.rubric_a.revise(rubric, note, goal, domain)
                self._emit(
                    "after", "rubric", "A", f"第 {i} 轮修改", i,
                    content=rubric.model_dump(),
                    comment="根据审查意见修补",
                )
                history.append({
                    "round": i, "speaker": "A", "role": f"第 {i} 轮修改",
                    "content": rubric.model_dump(),
                    "comment": "根据审查意见修补",
                })

        return history

    # ==========================================
    # 阶段 3：Strategy 组三轮博弈
    # ==========================================
    def _run_strategy_debate(
        self,
        goal: str,
        domain: str,
        rubric: RubricSchema,
        rule_constraints: str,
    ) -> List[Dict]:
        """只接收 final_rubric（Judge 产物），✗ 不接收 rubric_history"""
        history: List[Dict] = []
        self._emit("start", "strategy", "", "🎯 策略组三轮博弈", 0)

        # ---------- Round 0：A 出初稿 ----------
        self._emit("before", "strategy", "A", "初始策略", 0)
        strategy = self.strategy_a.draft(
            goal, domain, rubric, rule_constraints,
        )
        self._emit(
            "after", "strategy", "A", "初始策略", 0,
            content=strategy.model_dump(),
            comment=strategy.summary or "初始策略已生成",
        )
        history.append({
            "round": 0, "speaker": "A", "role": "初始策略",
            "content": strategy.model_dump(),
            "comment": strategy.summary or "",
        })

        # ---------- 第 1..N 轮：B 反驳 → A 修订 ----------
        for i in range(1, self.rounds + 1):
            # B 反驳
            self._emit("before", "strategy", "B", f"第 {i} 轮反驳", i)
            rebuttal = self.strategy_b.rebut(
                strategy, goal, domain, rubric, i,
            )
            self._emit(
                "after", "strategy", "B", f"第 {i} 轮反驳", i,
                content=rebuttal,
                comment="反驳意见",
            )
            history.append({
                "round": i, "speaker": "B", "role": f"第 {i} 轮反驳",
                "content": rebuttal, "comment": "",
            })

            if i < self.rounds:
                self._emit("before", "strategy", "A", f"第 {i} 轮修改", i)
                strategy = self.strategy_a.revise(
                    strategy, rebuttal, goal, domain, rubric,
                )
                self._emit(
                    "after", "strategy", "A", f"第 {i} 轮修改", i,
                    content=strategy.model_dump(),
                    comment="根据反驳意见修补",
                )
                history.append({
                    "round": i, "speaker": "A", "role": f"第 {i} 轮修改",
                    "content": strategy.model_dump(), "comment": "",
                })

        return history

    # ==========================================
    # 主流程
    # ==========================================
    def run(
        self,
        goal: str,
        domain: str,
        rule_constraints: str = "",
    ) -> Dict:
        """
        执行完整编排，返回：
        {
            "final_rubric": RubricSchema,
            "final_strategy": StrategySchema,
            "total_score": float,
            "dimension_scores": List[dict],
            "defects": List[str],
            "improvement_directions": List[str],
            "judge_reasoning": str,
            "rubric_history": List[dict],
            "strategy_history": List[dict],
        }
        """

        # ---------- Phase 1: Rubric 组三轮博弈 ----------
        rubric_history = self._run_rubric_debate(
            goal, domain, rule_constraints,
        )

        # ---------- Phase 2: Judge 裁定最终 Rubric ----------
        self._emit("start", "judge", "judge", "⚖️ 判断智能体裁定最终题目", 0)
        self._emit("before", "judge", "judge", "综合出题博弈", 0)
        rubric_decision: RubricDecision = self.judge.decide_rubric(
            rubric_history, goal, domain, rule_constraints,
        )
        self._emit(
            "decision", "judge", "judge", "最终 Rubric 已定", 0,
            content=rubric_decision.final_rubric.model_dump(),
            comment=rubric_decision.reasoning or "",
        )

        final_rubric: RubricSchema = rubric_decision.final_rubric

        # ---------- Phase 3: Strategy 组三轮博弈 ----------
        # ⚠️ 隔离规则：只传入 final_rubric，不传 rubric_history
        strategy_history = self._run_strategy_debate(
            goal, domain, final_rubric, rule_constraints,
        )

        # ---------- Phase 4: Judge 裁定最终策略 ----------
        self._emit("start", "judge", "judge", "⚖️ 判断智能体裁定最终策略", 0)
        self._emit("before", "judge", "judge", "综合策略博弈", 0)
        strategy_decision: StrategyDecision = self.judge.decide_strategy(
            strategy_history, final_rubric, goal, domain,
        )
        self._emit(
            "decision", "judge", "judge", "最终策略已定", 0,
            content=strategy_decision.model_dump(),
            comment=f"总分 {strategy_decision.total_score}/100",
        )

        return {
            "final_rubric": final_rubric,
            "final_strategy": strategy_decision.final_strategy,
            "total_score": strategy_decision.total_score,
            "dimension_scores": [
                d.model_dump() for d in strategy_decision.dimension_scores
            ],
            "defects": strategy_decision.defects,
            "improvement_directions": strategy_decision.improvement_directions,
            "judge_reasoning": strategy_decision.reasoning,
            # 以下仅供 CLI / 落盘存档，不会回传给任何 Agent
            "rubric_history": rubric_history,
            "strategy_history": strategy_history,
        }

    # ==========================================
    # 调试辅助
    # ==========================================
    def describe_agents(self) -> Dict[str, Dict]:
        """各 Agent 的模型与 key 数量摘要（用于排查）"""
        return {
            "RUBRIC_A": {
                "provider": self.rubric_a.model,
                "key_count": len(self.rubric_a.api_keys),
            },
            "RUBRIC_B": {
                "provider": self.rubric_b.model,
                "key_count": len(self.rubric_b.api_keys),
            },
            "STRATEGY_A": {
                "provider": self.strategy_a.model,
                "key_count": len(self.strategy_a.api_keys),
            },
            "STRATEGY_B": {
                "provider": self.strategy_b.model,
                "key_count": len(self.strategy_b.api_keys),
            },
            "JUDGE": {
                "provider": self.judge.model,
                "key_count": len(self.judge.api_keys),
            },
        }