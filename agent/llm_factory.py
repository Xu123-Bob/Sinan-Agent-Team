"""
LLM 工厂 v3.1
· 支持单 key（str）与 key 池（List[str]）
· 池模式自动 round-robin 轮询（跨 Agent 全局共享同一 pool 的循环）
· 线程安全（关键路径加锁）
"""
import os
import threading
from itertools import cycle
from typing import Optional, Union, List, Dict, Any, Tuple

import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=False)


SINAN_DEFAULT_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
        "model": "deepseek-flash",
    },
    "kimi": {
        "name": "Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "env_key": "MOONSHOT_API_KEY",
        "model": "moonshot-v1-8k",
    },
    "qwen": {
        "name": "Qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "env_key": "DASHSCOPE_API_KEY",
        "model": "qwen-plus",
    },
    "glm": {
        "name": "GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "env_key": "ZHIPUAI_API_KEY",
        "model": "glm-4-flash",
    },
    "ollama": {
        "name": "Ollama (本地)",
        "base_url": "http://localhost:11434/v1",
        "env_key": "",
        "model": "qwen2.5:7b",
    },
}


class LLMFactory:
    def __init__(self, custom_providers: Optional[Dict[str, dict]] = None):
        self.providers = SINAN_DEFAULT_PROVIDERS.copy()
        if custom_providers:
            self.providers.update(custom_providers)

        # key 池轮询状态：{ tuple(keys) : itertools.cycle }
        self._key_cycles: Dict[Tuple[str, ...], Any] = {}
        self._lock = threading.Lock()

    # ==========================================
    # key 选择
    # ==========================================
    def _pick_key(self, keys: List[str]) -> str:
        """同池多个 key → 轮询；只有一个直接返回"""
        if len(keys) == 1:
            return keys[0]
        key_tuple = tuple(keys)
        with self._lock:
            if key_tuple not in self._key_cycles:
                self._key_cycles[key_tuple] = cycle(keys)
            return next(self._key_cycles[key_tuple])

    def _normalize_keys(
        self,
        api_key_override: Optional[Union[str, List[str]]],
    ) -> List[str]:
        if isinstance(api_key_override, str):
            return [api_key_override.strip()] if api_key_override.strip() else []
        if isinstance(api_key_override, list):
            return [k.strip() for k in api_key_override if k and k.strip()]
        return []

    # ==========================================
    # 兼容旧接口（无 agent_config 时走 env 兜底）
    # ==========================================
    def auto_detect_provider(self) -> str:
        for name, prov in self.providers.items():
            env_key_name = prov.get("env_key", "")
            if not env_key_name:
                continue
            candidates = [
                f"SINAN_{env_key_name}",
                f"{env_key_name}",
                f"SINAN_{env_key_name}S",           # 复数
                f"{env_key_name}S",
            ]
            if any(os.getenv(k) for k in candidates):
                return name
            # 编号 KEY_1 ~ KEY_20
            for i in range(1, 21):
                if os.getenv(f"SINAN_{env_key_name}_{i}") or os.getenv(f"{env_key_name}_{i}"):
                    return name
        if "ollama" in self.providers:
            return "ollama"
        raise RuntimeError(...)

    def _load_env_keys(self, provider: str) -> List[str]:
        """当 override 为空时从环境变量读 key 池（兼容旧路径）"""
        if provider == "ollama":
            return ["not-needed"]
        prov = self.providers.get(provider, {})
        env_key_name = prov.get("env_key", "")
        if not env_key_name:
            return []

        keys = []

        # 复数池
        raw_pool = os.getenv(f"SINAN_{env_key_name}S") or os.getenv(f"{env_key_name}S")
        if raw_pool:
            keys.extend(k.strip() for k in raw_pool.split(",") if k.strip())

        # 单数
        single = (
            os.getenv(f"SINAN_{env_key_name}") or os.getenv(env_key_name) or ""
        ).strip()
        if single:
            keys.append(single)

        # 编号
        for i in range(1, 20):
            v = os.getenv(f"SINAN_{env_key_name}_{i}") or os.getenv(f"{env_key_name}_{i}")
            if v and v.strip():
                keys.append(v.strip())

        # 去重保序
        seen = set()
        out = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                out.append(k)
        return out

    # ==========================================
    # 核心：构建客户端
    # ==========================================
    def get_llm_client(
        self,
        provider_name: Optional[str] = None,
        api_key_override: Optional[Union[str, List[str]]] = None,
    ) -> Tuple[OpenAI, str, str]:
        if not provider_name:
            provider_name = self.auto_detect_provider()
        if provider_name not in self.providers:
            raise ValueError(
                f"未知的模型后端: '{provider_name}'。"
                f"可用：{', '.join(self.providers.keys())}"
            )

        prov = self.providers[provider_name]

        # 1) 归一化 override
        keys = self._normalize_keys(api_key_override)

        # 2) override 为空 → env 兜底
        if not keys:
            keys = self._load_env_keys(provider_name)

        if not keys:
            raise RuntimeError(
                f"[{prov['name']}] 缺少 API Key。"
                f"请配置 SINAN_{provider_name.upper()}_API_KEYS 或 "
                f"SINAN_{provider_name.upper()}_API_KEY"
            )

        # 3) 轮询选 key
        api_key = self._pick_key(keys)

        client = OpenAI(
            api_key=api_key,
            base_url=prov["base_url"],
            timeout=httpx.Timeout(300.0, connect=10.0),
        )
        return client, prov["model"], prov["name"]

    # ==========================================
    # 对话接口
    # ==========================================
    def chat(
        self,
        messages: List[Dict[str, str]],
        provider_name: Optional[str] = None,
        api_key_override: Optional[Union[str, List[str]]] = None,
        json_mode: bool = False,
        temperature: float = 0.3,
    ) -> str:
        client, model_name, display_name = self.get_llm_client(
            provider_name, api_key_override
        )

        kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"[{display_name}] API 调用失败: {e}")


# ==========================================
# 全局实例
# ==========================================
llm_factory = LLMFactory()