"""
规则引擎 v2
· 支持 global 规则（所有场景都适用）
· 支持 per-domain 规则
· 支持用户自定义 domain（配置文件任意扩展）
· 支持 schema_field 类型：断言 JSON 中必含字段
"""
import re
import yaml
from pathlib import Path


class RuleEngine:
    def __init__(self, config_path: str = "configs/rules.yaml"):
        self.config_path = Path(config_path)
        self.rules_data = self._load_rules()

    def _load_rules(self) -> dict:
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _collect_rules(self, domain: str) -> list:
        """合并全局规则 + 领域规则"""
        rules = []
        rules.extend(self.rules_data.get("global", {}).get("rules", []))
        rules.extend(self.rules_data.get(domain, {}).get("rules", []))
        return rules

    def _check_rule(self, rule: dict, content: str, parsed_json: dict | None) -> bool:
        rtype = rule.get("type", "keyword")
        val = rule.get("value")

        if rtype == "keyword":
            return str(val).lower() in content.lower()
        if rtype == "forbidden":
            return not re.search(str(val), content)
        if rtype == "regex":
            return re.search(str(val), content, re.IGNORECASE) is not None
        if rtype == "min_length":
            return len(content) >= int(val)
        if rtype == "schema_field":
            # value 形如 "sections[].actions[].kpi"，简化为检查顶层字段
            if not parsed_json:
                return False
            return val in parsed_json
        return False

    def evaluate(self, content: str, domain: str, parsed_json: dict | None = None) -> dict:
        rules = self._collect_rules(domain)
        if not rules:
            return {"rule_score": 100.0, "details": [], "all_passed": True}

        achieved = 0
        total = sum(r.get("score", 0) for r in rules)
        details = []
        all_passed = True

        for r in rules:
            passed = self._check_rule(r, content, parsed_json)
            if passed:
                achieved += r.get("score", 0)
            else:
                all_passed = False
            details.append({
                "name": r.get("name", "未命名规则"),
                "category": r.get("category", "general"),
                "description": r.get("description", ""),
                "passed": passed,
                "max_score": r.get("score", 0),
                "score": r.get("score", 0) if passed else 0,
            })

        normalized = (achieved / total) * 100 if total else 0
        return {
            "rule_score": round(normalized, 1),
            "details": details,
            "all_passed": all_passed,
        }