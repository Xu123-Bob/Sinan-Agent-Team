"""
判断智能体（Judge）
· 唯一掌握「全部上下文」的智能体
· 内部 _memory 永不外泄
· 只输出「决策产物」：final_rubric / final_strategy
· 不向出题组、策略组回传任何上下文
"""
from typing import List, Dict, Any
from agent.agents.base import BaseAgent
from agent.schemas import (
    RubricSchema, RubricDecision,
    StrategySchema, StrategyDecision,
)


def _dump_history(history: List[Dict]) -> str:
    return "\n\n".join(
        f"--- 第 {h.get('round', '?')} 轮 · {h.get('speaker')} · {h.get('role')} ---\n"
        f"内容摘要:\n{_short(h.get('content'))}"
        for h in history
    )


def _short(content: Any, limit: int = 3000) -> str:
    if isinstance(content, str):
        return content[:limit]
    import json
    return json.dumps(content, ensure_ascii=False)[:limit]


class JudgeAgent(BaseAgent):
    def __init__(self, model=None, api_key=None, knowledge: str = ""):
        super().__init__("JudgeAgent", "判断智能体", model, api_key, knowledge)
        self._memory: List[Dict] = []  # 私有，永不外泄

    # ==========================================
    # Phase 1：裁定最终 Rubric
    # ==========================================
    def decide_rubric(
        self,
        rubric_history: List[Dict],
        goal: str,
        domain: str,
        rule_constraints: str = "",
    ) -> RubricDecision:
        # 存档到私有记忆
        self._memory.append({
            "phase": "rubric",
            "history": rubric_history,
        })

        prompt = f"""你是 {domain} 战略委员会主席（判断智能体）。
出题组（两位专家）经过三轮博弈，产生了如下 Rubrics 演进过程。

【完整博弈历史】
{_dump_history(rubric_history)}

【业务目标】
{goal[:6000]}

【用户硬性底线】
{rule_constraints or "（无）"}

【你的任务】
1. 独立审阅博弈过程，识别两位专家是否真正达成了Rubric共识
2. 若双方意见不一，以你的专业判断为准
3. 输出最终的、唯一的 Rubric

严格输出 JSON（符合 RubricSchema）：
{{"dimensions": [{{"name":"...","description":"...","max_score":30,"weight_reason":"...","measurement":"...","must_include":[]}}], "rationale": "..."}}
"""
        final = self.chat_with_schema(prompt, RubricSchema, temperature=0.3)
        return RubricDecision(
            final_rubric=final,
            reasoning="Judge 综合出题组三轮博弈后形成最终题目",
        )

    # ==========================================
    # Phase 2：裁定最终策略
    # ==========================================
    def decide_strategy(
        self,
        strategy_history: List[Dict],
        rubric: RubricSchema,
        goal: str,
        domain: str,
    ) -> StrategyDecision:
        self._memory.append({
            "phase": "strategy",
            "history": strategy_history,
        })

        prompt = f"""你是 {domain} 战略委员会主席（判断智能体）。
策略组（撰写者 ⇄ 反驳者）经过三轮博弈，产生了如下策略演进过程。

【完整博弈历史】
{_dump_history(strategy_history)}

【最终 Rubric】
{rubric.model_dump_json(indent=2, ensure_ascii=False)}

【业务目标】
{goal[:5000]}

【你的任务】
1. 从博弈历史中提炼出最优策略
2. 严格按 Rubric 逐维度打分
3. 最终交付一份稳定的 StrategySchema

严格输出符合 StrategyDecision 的 JSON，其中 final_strategy 必须是完整策略对象。
"""
        decision = self.chat_with_schema(
            prompt, StrategyDecision, temperature=0.3
        )
        return decision

    # 私有方法：判断智能体可访问自身 memory 做事后复盘（不外泄）
    def _recall(self) -> List[Dict]:
        return list(self._memory)