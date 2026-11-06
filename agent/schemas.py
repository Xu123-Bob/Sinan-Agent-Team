"""
司南 v3.0 数据结构定义
所有 Agent 的输出必须符合下列 Schema，否则将触发重试机制。
"""
from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional, Literal


# ============================================
# Rubric（考核量规）
# ============================================
class RubricDimension(BaseModel):
    name: str = Field(description="维度名称")
    description: str = Field(default="", description="考察内容")
    max_score: float = Field(ge=0, description="满分分值")
    weight_reason: str = Field(default="", description="为何这样分配分值")
    measurement: str = Field(default="", description="如何量化衡量")
    must_include: List[str] = Field(
        default_factory=list,
        description="达成该维度的必含关键词/要素"
    )


class RubricSchema(BaseModel):
    dimensions: List[RubricDimension] = Field(min_length=1)
    rationale: str = Field(default="", description="总体设计思路")

    @model_validator(mode="after")
    def normalize_total(self):
        """强制维度总分归一化到 100（容错：容许 LLM 小偏差）"""
        total = sum(d.max_score for d in self.dimensions)
        if total <= 0:
            raise ValueError("所有维度分值不能为 0")
        if abs(total - 100) > 0.5:
            factor = 100.0 / total
            for d in self.dimensions:
                d.max_score = round(d.max_score * factor, 2)
            diff = round(100 - sum(d.max_score for d in self.dimensions), 2)
            if diff != 0:
                self.dimensions[0].max_score = round(
                    self.dimensions[0].max_score + diff, 2
                )
        return self

    def total(self) -> float:
        return round(sum(d.max_score for d in self.dimensions), 2)


# ============================================
# Strategy（策略正文）
# ============================================
class StrategyAction(BaseModel):
    name: str = Field(description="动作名称")
    description: str = Field(default="", description="动作详情")
    timeline: str = Field(default="", description="时间节点")
    owner: str = Field(default="", description="负责人/角色")
    kpi: str = Field(default="", description="衡量指标")


class StrategySection(BaseModel):
    name: str = Field(description="章节名")
    content: str = Field(default="", description="章节正文")
    actions: List[StrategyAction] = Field(default_factory=list)
    rubric_refs: List[str] = Field(
        default_factory=list,
        description="对应到哪些 Rubric 维度名"
    )


class StrategySchema(BaseModel):
    title: str
    objective: str = Field(description="核心目标")
    sections: List[StrategySection] = Field(min_length=1)
    summary: str = Field(default="", description="一句话总结")
    key_risks: List[str] = Field(default_factory=list, description="潜在风险")
    rubric_coverage: Dict[str, str] = Field(
        default_factory=dict,
        description="{维度名: 本策略如何达成}"
    )


# ============================================
# Judge 决策产物
# ============================================
class DimensionScore(BaseModel):
    name: str
    score: float = Field(ge=0)
    max_score: float = Field(ge=0)
    comment: str = ""


class RubricDecision(BaseModel):
    """Judge 在出题阶段输出的最终题"""
    final_rubric: RubricSchema
    reasoning: str = Field(default="", description="裁定过程摘要")


class StrategyDecision(BaseModel):
    """Judge 在策略阶段输出的最终裁定"""
    final_strategy: StrategySchema
    total_score: float = Field(ge=0, le=100)
    dimension_scores: List[DimensionScore] = Field(default_factory=list)
    defects: List[str] = Field(default_factory=list)
    improvement_directions: List[str] = Field(default_factory=list)
    decision: Literal["approve", "revise", "reject"] = "approve"
    reasoning: str = ""