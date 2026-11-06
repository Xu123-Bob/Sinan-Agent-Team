# agent/core/intent_parser.py
import json
from agent.llm_factory import llm_factory

class IntentParser:
    """用 LLM 把用户的自然语言转换为结构化指令"""

    def __init__(self, provider_name: str = None, api_key: str = None):
        # ⭐ 新增：未指定时从 agent_config 读默认
        if not provider_name:
            from agent.core.agent_config import get_agent_config
            cfg = get_agent_config("SCOUT")  # 或 JUDGE，用任意一个即可
            provider_name = cfg.provider
            if not api_key and cfg.api_keys:
                api_key = cfg.api_keys
        self.provider_name = provider_name
        self.api_key = api_key

    def parse(self, user_input: str, context: str = "") -> dict:
        prompt = f"""
你是司南 Agent 的意图解析器。用户会用自然语言告诉你他想做什么。
请从用户的输入中解析出以下 JSON 结构：
{{
    "action": "generate | compare | evolve | help | unknown",
    "platform": "ecommerce | github | atomgit | douyin | tiktok | unknown",
    "folder_a": "策略A的文件夹路径 (用于 generate 或 compare)",
    "folder_b": "策略B的文件夹路径 (仅用于 compare)",
    "history_folder": "旧策略文件夹 (用于 evolve)",
    "new_data_folder": "新数据文件夹 (用于 evolve)",
    "confidence": 0.0-1.0,
    "clarify": "如果信息缺失，用一句话说明缺什么（否则留空）"
}}

【平台映射规则】：
- 电商/网店/淘宝/天猫/京东/拼多多 → platform="ecommerce"
- GitHub/Github/开源项目/代码仓库/PR → platform="github"
- AtomGit → platform="atomgit"
- 抖音/短视频/直播 → platform="douyin"
- TikTok/海外短视频/跨境电商 → platform="tiktok"

【动作映射规则】：
- 制定/生成/评估/打分/怎么做/出个方案/帮我写 → action="generate"
- 对比/比较/vs/A和B哪个好/选哪个 → action="compare"
- 进化/更新/复盘/迭代/根据新数据优化/版本升级 → action="evolve"
- 帮助/怎么用/说明/使用手册 → action="help"

【路径提取规则】：
- 如果用户提到了具体的文件夹路径（例如 ./data/xxx 或 D:\\xxx），请填入相应字段。
- 如果用户只说了动作和平台，但没给路径，相应字段留空，并在 clarify 里说明"请提供xxx路径"。

【Few-shot 示例】：
示例1: "帮我制定 ./data/ecommerce_v1 的电商策略"
输出: {{"action":"generate","platform":"ecommerce","folder_a":"./data/ecommerce_v1","folder_b":"","history_folder":"","new_data_folder":"","confidence":0.95,"clarify":""}}

示例2: "对比 ./outputs/v1.md 和 ./outputs/v2.md 两个方案"
输出: {{"action":"compare","platform":"ecommerce","folder_a":"./outputs/v1.md","folder_b":"./outputs/v2.md","history_folder":"","new_data_folder":"","confidence":0.95,"clarify":""}}

示例3: "我抖音策略要更新，老的在 ./outputs/old.md，新数据在 ./data/new"
输出: {{"action":"evolve","platform":"douyin","folder_a":"","folder_b":"","history_folder":"./outputs/old.md","new_data_folder":"./data/new","confidence":0.9,"clarify":""}}

{("【上文对话】: " + context) if context else ""}
【用户本次输入】: {user_input}
"""
        response = llm_factory.chat(
            messages=[{"role": "user", "content": prompt}],
            provider_name=self.provider_name,
            api_key_override=self.api_key,
            json_mode=True,
            temperature=0.1
        )
        return json.loads(response)