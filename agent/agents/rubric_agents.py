"""
出题智能体 A / B
· 两者上下文互通（共享同一个 rubric_history）
· 三轮博弈
· 全程推给 JudgeAgent 观察
"""
from agent.agents.base import BaseAgent
from agent.schemas import RubricSchema


class RubricAgentA(BaseAgent):
    """主出题方"""
    def __init__(self, model=None, api_key=None, knowledge: str = ""):
        super().__init__("RubricAgentA", "出题-主编", model, api_key, knowledge)

    def draft(
        self, goal: str, domain: str, rule_constraints: str = ""
    ) -> RubricSchema:
        prompt = f"""你是资深 {domain} 领域的策略考核专家（出题主编）。
请基于以下业务目标与数据，设计一套【策略考核 Rubrics】。

【业务目标与数据】
{goal[:10000]}

【用户定义的硬性底线】（设计的维度必须对齐这些约束）
{rule_constraints or "（无）"}

【出题硬性要求】
1. 维度 3-6 个，覆盖业务目标核心方面
2. 每个维度分值相加严格 = 100
3. 分值权重必须差异化（禁止平均分配），并说明 weight_reason
4. description 与 measurement 必须具体可执行
5. 尽量为每个维度给出 must_include 关键词（用于后续硬校验）

严格输出 JSON（符合 RubricSchema）：
{{
  "dimensions": [
    {{
      "name": "维度名",
      "description": "考察内容",
      "max_score": 30,
      "weight_reason": "为什么 30 分",
      "measurement": "如何衡量",
      "must_include": ["关键词1", "关键词2"]
    }}
  ],
  "rationale": "总体设计思路（200 字内）"
}}
"""
        return self.chat_with_schema(prompt, RubricSchema, temperature=0.7)

    def revise(
        self,
        current: RubricSchema,
        feedback: str,
        goal: str,
        domain: str,
    ) -> RubricSchema:
        prompt = f"""你是 {domain} 策略考核专家（出题主编）。
同伴（审查员）提出了如下反馈，请据此修改 Rubric。

【业务目标】
{goal[:6000]}

【当前 Rubric】
{current.model_dump_json(indent=2)}

【同伴反馈】
{feedback}

【要求】
- 严格保持 RubricSchema 结构
- 维度总分仍为 100
- 保留合理部分，重点修补被指出的问题
- 直接输出 JSON
"""
        return self.chat_with_schema(prompt, RubricSchema, temperature=0.4)


class RubricAgentB(BaseAgent):
    """审核方"""
    def __init__(self, model=None, api_key=None, knowledge: str = ""):
        super().__init__("RubricAgentB", "出题-审查员", model, api_key, knowledge)

    def review(
        self,
        current: RubricSchema,
        goal: str,
        domain: str,
        round_no: int,
        rule_constraints: str = "",
    ) -> tuple[RubricSchema, str]:
        """返回 (修改后的 Rubric, 审查意见摘要)"""
        prompt = f"""你是 {domain} 策略运营总监（出题审查员）。
现在是第 {round_no} 轮复核。请审查并修改下面的 Rubric。

【业务目标与数据】
{goal[:6000]}

【用户定义的硬性底线】
{rule_constraints or "（无）"}

【当前 Rubric】
{current.model_dump_json(indent=2)}

【审查重点】
1. 是否完整覆盖业务目标？是否有冗余/缺失维度？
2. 分值权重是否与业务重点匹配？
3. description/measurement 是否可执行？
4. 总分是否 = 100？

严格输出 JSON（符合 RubricSchema，可直接采用为修改后的版本）：
{{
  "dimensions": [
    {{
      "name": "维度名",
      "description": "考察内容",
      "max_score": 30,
      "weight_reason": "为什么这样分配",
      "measurement": "如何衡量",
      "must_include": ["关键词"]
    }}
  ],
  "rationale": "本轮审查意见 + 修改说明（300 字内）"
}}
"""
        temperature = 0.25 if round_no >= 2 else 0.4
        rubric = self.chat_with_schema(prompt, RubricSchema, temperature=temperature)
        review_note = rubric.rationale or f"第 {round_no} 轮审查完成"
        return rubric, review_note