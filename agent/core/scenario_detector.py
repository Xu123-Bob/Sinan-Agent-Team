"""
场景探测器
从「平台」升级为「领域」，且支持用户自定义。
"""
import json
from pathlib import Path
from agent.llm_factory import llm_factory


class ScenarioDetector:
    SUPPORTED = ["ecommerce", "github", "atomgit", "douyin", "tiktok"]

    def __init__(self, provider_name: str = None, api_key: str = None):
        self.provider_name = provider_name
        self.api_key = api_key

    def _quick_heuristics(self, folder: str) -> str | None:
        p = Path(folder)
        if not p.exists():
            return None
        names = " ".join(
            f.name.lower() for f in p.rglob("*") if f.is_file()
        )
        if any(k in names for k in ["readme.md", "package.json", "requirements.txt"]):
            return "github"
        if any(k in names for k in ["douyin", "抖音", "短视频"]):
            return "douyin"
        if any(k in names for k in ["tiktok"]):
            return "tiktok"
        if any(k in names for k in ["order", "sku", "gmv", "电商", "销售"]):
            return "ecommerce"
        return None

    def detect(self, folder: str) -> str:
        quick = self._quick_heuristics(folder)
        if quick:
            return quick

        p = Path(folder)
        files = [str(f.relative_to(p)) for f in p.rglob("*") if f.is_file()][:50]
        prompt = f"""根据文件清单判断最可能属于哪个业务领域。
可选：ecommerce / github / atomgit / douyin / tiktok / 其他自定义。
只输出 JSON：{{"domain": "...", "reason": "..."}}

文件清单：
{chr(10).join(files)}
"""
        try:
            raw = llm_factory.chat(
                messages=[{"role": "user", "content": prompt}],
                provider_name=self.provider_name,
                api_key_override=self.api_key,
                json_mode=True, temperature=0.0,
            )
            data = json.loads(raw)
            domain = (data.get("domain") or "").lower()
            return domain if domain in self.SUPPORTED else domain or "unknown"
        except Exception:
            return "unknown"