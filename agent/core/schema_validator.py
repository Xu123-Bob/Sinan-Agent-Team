"""
Schema 强校验器
确保 Agent 输出的 JSON 结构稳定，防止下游崩溃。
"""
import json
from typing import Tuple, Any, Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def parse_json_safely(text: str) -> Tuple[bool, str, Any]:
    """从 LLM 输出中稳健提取 JSON（容忍 ```json 包裹）"""
    if not text:
        return False, "空输出", None
    t = text.strip()
    # 去掉 markdown 代码围栏
    if t.startswith("```"):
        lines = t.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        t = "\n".join(lines)
    try:
        return True, "", json.loads(t)
    except json.JSONDecodeError as e:
        # 尝试找第一个 { 到最后一个 }
        start, end = t.find("{"), t.rfind("}")
        if start != -1 and end > start:
            try:
                return True, "", json.loads(t[start:end + 1])
            except Exception:
                pass
        return False, f"JSON 解析失败: {e}", None


def validate_with_schema(data: Any, schema_cls: Type[T]) -> Tuple[bool, str, T | None]:
    """用 Pydantic Schema 校验"""
    if not isinstance(data, dict):
        return False, f"期望 dict，实际 {type(data).__name__}", None
    try:
        obj = schema_cls(**data)
        return True, "", obj
    except ValidationError as e:
        return False, f"Schema 校验失败:\n{e}", None


def validate_agent_output(
    raw_text: str, schema_cls: Type[T]
) -> Tuple[bool, str, T | None]:
    """一站式：解析 + 校验"""
    ok, err, data = parse_json_safely(raw_text)
    if not ok:
        return False, err, None
    return validate_with_schema(data, schema_cls)