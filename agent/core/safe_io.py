"""
统一落盘入口 + 知识库保护

所有需要写文件的地方（策略 / rubric / debate / 日志）都必须调用 safe_write。
它会拒绝写入任何"受保护"路径，当前包括知识库目录。
"""
import os
from pathlib import Path
from typing import Iterable, List, Optional, Union


# 默认受保护目录（相对项目根目录）
DEFAULT_PROTECTED_DIRS = ["knowledge"]


def _resolve_protected_paths(extra: Optional[Iterable[str]] = None) -> List[Path]:
    """
    收集所有受保护目录的绝对路径。
    来源：
      1. .env 中的 SINAN_KNOWLEDGE_DIR（如果设置）
      2. 项目根的 knowledge/（默认）
      3. 调用方额外传入的路径
    """
    protected: List[Path] = []

    env_kb = os.getenv("SINAN_KNOWLEDGE_DIR")
    if env_kb:
        protected.append(Path(env_kb).resolve())

    for p in DEFAULT_PROTECTED_DIRS:
        protected.append(Path(p).resolve())

    if extra:
        for p in extra:
            protected.append(Path(p).resolve())

    # 去重保序
    seen = set()
    out = []
    for p in protected:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _is_inside(target: Path, parent: Path) -> bool:
    """target 是否在 parent 内部（含 parent 本身）"""
    try:
        target.relative_to(parent)
        return True
    except ValueError:
        return False


def assert_not_protected(
    target: Union[str, Path],
    extra_protected: Optional[Iterable[str]] = None,
) -> None:
    """
    若 target 落在任何受保护目录内 → 抛 PermissionError。
    """
    t = Path(target).resolve()
    for protected in _resolve_protected_paths(extra_protected):
        if _is_inside(t, protected):
            raise PermissionError(
                f"⛔ 禁止写入受保护目录：\n"
                f"   目标路径: {t}\n"
                f"   受保护根: {protected}\n"
                f"   （知识库只读，任何 Agent 不得反向输出）"
            )


def safe_write(
    path: Union[str, Path],
    content: str,
    *,
    encoding: str = "utf-8",
    extra_protected: Optional[Iterable[str]] = None,
    create_parents: bool = True,
) -> Path:
    """
    安全写入（唯一推荐入口）。

    行为：
      1. 拒绝写入知识库
      2. 自动创建父目录
      3. 返回写入后的绝对路径
    """
    target = Path(path)
    assert_not_protected(target, extra_protected)
    if create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding=encoding) as f:
        f.write(content)
    return target.resolve()


def safe_write_bytes(
    path: Union[str, Path],
    content: bytes,
    *,
    extra_protected: Optional[Iterable[str]] = None,
    create_parents: bool = True,
) -> Path:
    """二进制版安全写入"""
    target = Path(path)
    assert_not_protected(target, extra_protected)
    if create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as f:
        f.write(content)
    return target.resolve()