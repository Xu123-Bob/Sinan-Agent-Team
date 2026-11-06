"""
文件侦察智能体 (Scout)
· 输入：ScanReport
· 输出：ScoutReport（业务概览 / 关键目标 / 建议领域 / 澄清问题）
· 不做 Rubric、不做策略，只做侦察汇报
"""
from typing import List
from pydantic import BaseModel, Field

from agent.agents.base import BaseAgent
from agent.core.file_scanner import ScanReport


class ScoutReport(BaseModel):
    business_overview: str = Field(
        default="", description="3-5 句业务概览"
    )
    key_targets: List[str] = Field(
        default_factory=list, description="关键目标文件相对路径（最多5个）"
    )
    suggested_domain: str = Field(
        default="unknown",
        description="ecommerce/github/atomgit/douyin/tiktok/unknown"
    )
    suggested_strategy_type: str = Field(
        default="", description="建议制定什么策略"
    )
    clarifying_questions: List[str] = Field(
        default_factory=list, description="需向用户确认的关键问题"
    )
    confidence: float = Field(default=0.6, ge=0, le=1)


class ScoutAgent(BaseAgent):
    def __init__(self, model=None, api_key=None, knowledge: str = ""):
        super().__init__("ScoutAgent", "文件侦察智能体", model, api_key, knowledge)

    def scout(self, scan: ScanReport) -> ScoutReport:
        payload = self._build_payload(scan)
        prompt = f"""你是司南策略系统的「文件侦察智能体」。
用户刚给了一个文件夹，你的任务是快速侦察并汇报：

1. 这些文件是什么数据/材料？（业务概览 3-5 句）
2. 哪些是「关键目标文件」？（优先数据文件和目标/README 文档）
3. 建议什么业务领域？
4. 建议制定什么类型的策略？
5. 若有歧义，提出 1-3 个向用户确认的关键问题

【文件夹路径】{scan.folder}
【统计】{scan.total_files} 个文件 / {scan.total_size_mb} MB
{self._truncated_note(scan)}

【文件清单与内容预览】
{payload}

严格输出 JSON（符合 ScoutReport Schema）：
{{
  "business_overview": "3-5句业务概览",
  "key_targets": ["关键文件路径1", "关键文件路径2"],
  "suggested_domain": "ecommerce|github|atomgit|douyin|tiktok|unknown",
  "suggested_strategy_type": "建议策略类型",
  "clarifying_questions": ["问题1"],
  "confidence": 0.0-1.0
}}

【硬性规则】
- business_overview 必须基于真实文件内容，不要空话
- key_targets 最多 5 个
- 若文件与业务数据无关（纯代码/噪音），suggested_domain="unknown" 且 confidence 调低
- clarifying_questions 只在确有歧义时列出；若无需确认，写 []
"""
        return self.chat_with_schema(prompt, ScoutReport, temperature=0.3)

    @staticmethod
    def _truncated_note(scan: ScanReport) -> str:
        return "【注意】文件过多已截取部分扫描" if scan.truncated else ""

    @staticmethod
    def _build_payload(scan: ScanReport, max_chars: int = 12000) -> str:
        lines = []
        priority = ["data", "document", "config", "code", "other"]
        current = 0
        for role in priority:
            entries = scan.groups.get(role, [])
            if not entries:
                continue
            lines.append(f"\n### {role.upper()}（{len(entries)} 个）")
            for e in entries[:15]:
                head = e.head_preview.strip().replace("\n", " ")[:200]
                block = (
                    f"- {e.path} ({e.size_kb()}KB) 预览: {head}"
                    if head
                    else f"- {e.path} ({e.size_kb()}KB)"
                )
                if current + len(block) > max_chars:
                    lines.append("... [更多文件已省略] ...")
                    return "\n".join(lines)
                lines.append(block)
                current += len(block)
        return "\n".join(lines) if lines else "（空文件夹）"