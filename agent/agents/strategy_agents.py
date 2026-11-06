"""
策略智能体 A / B
· 上下文互通（共享 strategy_history）
· 三轮博弈
· 不与出题组共享任何上下文
· 只接收 Judge 输出的「最终 Rubric」作为输入
"""
from agent.agents.base import BaseAgent
from agent.schemas import RubricSchema, StrategySchema


def _fmt_rubric(rubric: RubricSchema) -> str:
    return "\n".join(
        f"- {d.name}（{d.max_score} 分）：{d.description}"
        for d in rubric.dimensions
    )


class StrategyAgentA(BaseAgent):
    """出策略方"""
    def __init__(self, model=None, api_key=None, knowledge: str = ""):
        super().__init__("StrategyAgentA", "策略-撰写者", model, api_key, knowledge)

    def draft(
        self, goal: str, domain: str, rubric: RubricSchema,
        rule_constraints: str = "",
    ) -> StrategySchema:
        prompt = f"""你是顶级 {domain} 策略专家（策略撰写者）。
请基于业务目标与评分标准，写一份可落地的策略。

【业务目标与数据】
{goal[:9000]}

【评分标准（Rubric）】
{_fmt_rubric(rubric)}

【用户定义的硬性底线】
{rule_constraints or "（无）"}

【要求】
1. 每个 Rubric 维度都必须有对应章节/动作
2. 每个动作包含具体 timeline、owner、kpi
3. 量化目标必须明确
4. 严格输出符合 StrategySchema 的 JSON

Schema 顶层字段：
- title, objective, sections[], summary, key_risks[], rubric_coverage{{}}

每个 section 包含: name, content, actions[]{{name, description, timeline, owner, kpi}}, rubric_refs[]
"""
        return self.chat_with_schema(prompt, StrategySchema, temperature=0.7)

    def revise(
        self, current: StrategySchema, rebuttal: str,
        goal: str, domain: str, rubric: RubricSchema,
    ) -> StrategySchema:
        prompt = f"""你是 {domain} 策略撰写者。对方（反驳者）提出如下问题：

{rebuttal}

【原策略】
{current.model_dump_json(indent=2, ensure_ascii=False)}

【Rubric】
{_fmt_rubric(rubric)}

请针对性修补策略。严格输出 StrategySchema JSON。
"""
        return self.chat_with_schema(prompt, StrategySchema, temperature=0.5)


class StrategyAgentB(BaseAgent):
    """反驳方"""
    def __init__(self, model=None, api_key=None, knowledge: str = ""):
        super().__init__("StrategyAgentB", "策略-反驳者", model, api_key, knowledge)

    def rebut(
        self, strategy: StrategySchema, goal: str, domain: str,
        rubric: RubricSchema, round_no: int,
    ) -> str:
        """返回反驳意见（纯文本，不结构化，方便表达逻辑）"""
        prompt = f"""你是 {domain} 策略风控官（反驳者）。
现在是第 {round_no} 轮反驳。请严格挑出下列策略的问题。

【业务目标】
{goal[:6000]}

【Rubric】
{_fmt_rubric(rubric)}

【待反驳策略】
{strategy.model_dump_json(indent=2, ensure_ascii=False)}

【反驳重点】
1. 未覆盖哪些 Rubric 维度？哪些动作是空话？
2. 是否存在不可执行/资源浪费/合规风险？
3. 量化指标是否可达成？
4. 与其他策略动作是否冲突？

输出格式：直接输出反驳意见正文（纯文本，不超过 800 字）。
"""
        return self._call_llm(prompt, json_mode=False, temperature=0.5)