"""
按 Agent 粒度读取模型配置（支持同一 Provider 多 API Key）

优先级（高 → 低）：
  SINAN_<AGENT>_API_KEYS      → 专属池
  SINAN_<AGENT>_API_KEY       → 专属单个
  SINAN_<PROVIDER>_API_KEYS   → Provider 池
  SINAN_<PROVIDER>_API_KEY    → Provider 单个
  SINAN_<PROVIDER>_API_KEY_1..N → Provider 编号
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=False)


AGENT_NAMES = [
    "SCOUT",
    "RUBRIC_A",
    "RUBRIC_B",
    "STRATEGY_A",
    "STRATEGY_B",
    "JUDGE",
]

PROVIDER_ENV_KEYS = {
    "deepseek": "SINAN_DEEPSEEK_API",
    "kimi":     "SINAN_MOONSHOT_API",
    "qwen":     "SINAN_DASHSCOPE_API",
    "glm":      "SINAN_ZHIPUAI_API",
    "ollama":   "",  # 无 key
}

DEFAULT_PROVIDER = os.getenv("SINAN_DEFAULT_PROVIDER", "deepseek").strip().lower()


@dataclass
class AgentModelConfig:
    provider: str
    api_keys: List[str] = field(default_factory=list)

    @property
    def api_key(self) -> Optional[str]:
        """兼容旧调用：若只有一个 key 返回它，多个返回第一个，无则 None"""
        return self.api_keys[0] if self.api_keys else None

    def has_keys(self) -> bool:
        return bool(self.api_keys)

    def key_count(self) -> int:
        return len(self.api_keys)

    def __repr__(self) -> str:
        n = len(self.api_keys)
        hint = f"{n} key(s)" if n > 1 else ("1 key" if n == 1 else "(no key)")
        return f"AgentModelConfig(provider={self.provider}, {hint})"


# ==========================================
# key 读取工具
# ==========================================
def _clean(keys: List[str]) -> List[str]:
    """去空、去重、保序"""
    seen = set()
    out = []
    for k in keys:
        k = (k or "").strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _read_comma_separated(env_name: str) -> List[str]:
    raw = os.getenv(env_name) or ""
    return _clean(raw.split(","))


def _read_numbered(prefix: str, limit: int = 20) -> List[str]:
    """读取 PREFIX_1, PREFIX_2, ... PREFIX_N"""
    out = []
    for i in range(1, limit + 1):
        v = os.getenv(f"{prefix}_{i}")
        if v and v.strip():
            out.append(v.strip())
    return _clean(out)


def _collect_keys(prefix: str) -> List[str]:
    """
    prefix 例如 "SINAN_DEEPSEEK_API"
    支持：
      · SINAN_DEEPSEEK_API_KEYS   （复数，逗号分隔）
      · SINAN_DEEPSEEK_API_KEY    （单数）
      · SINAN_DEEPSEEK_API_KEY_1..N （编号）
    合并后去重
    """
    keys: List[str] = []
    # 1) 复数池
    keys.extend(_read_comma_separated(f"{prefix}_KEYS"))
    # 2) 单数（放进池）
    single = (os.getenv(f"{prefix}_KEY") or "").strip()
    if single:
        keys.append(single)
    # 3) 编号池
    keys.extend(_read_numbered(f"{prefix}_KEY"))
    return _clean(keys)


# ==========================================
# 主接口
# ==========================================
def get_agent_config(agent_name: str) -> AgentModelConfig:
    name = agent_name.upper()
    if name not in AGENT_NAMES:
        raise ValueError(
            f"未知 Agent: '{agent_name}'。可选：{', '.join(AGENT_NAMES)}"
        )

    # 1) provider
    provider = (
        os.getenv(f"SINAN_{name}_PROVIDER") or DEFAULT_PROVIDER
    ).strip().lower()

    # 2) 找 keys —— 优先级从上到下
    # ① Agent 专属池
    agent_prefix = f"SINAN_{name}_API"
    keys = _collect_keys(agent_prefix)

    # ② Provider 池
    if not keys:
        provider_prefix = PROVIDER_ENV_KEYS.get(provider, "")
        if provider_prefix:
            keys = _collect_keys(provider_prefix)

    # ③ Ollama 兜底（无需 key）
    if not keys and provider == "ollama":
        keys = []

    return AgentModelConfig(provider=provider, api_keys=keys)


def get_all_agent_configs() -> dict:
    return {name: get_agent_config(name) for name in AGENT_NAMES}


def summarize_configs() -> str:
    """启动摘要（CLI 用）"""
    lines = []
    for name, cfg in get_all_agent_configs().items():
        n = cfg.key_count()
        if n == 0:
            status = "⚠ 无 key（依赖 provider 兜底或本地）"
        elif n == 1:
            status = "✅ 1 个 key"
        else:
            status = f"✅ {n} 个 key（轮询）"
        lines.append(f"  {name:<12} → {cfg.provider:<10} {status}")
    return "\n".join(lines)