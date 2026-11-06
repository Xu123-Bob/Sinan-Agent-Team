"""
路径发现工具

当用户在 CLI 里没有提供路径时：
  · 扫描指定 base 目录（默认当前工作目录）
  · 识别可能的数据文件夹（含 goal/metrics/表格/文档）
  · 识别可能的策略文件（.md 且含策略特征词）
  · 返回候选列表，供 CLI 展示让用户选
"""
import os
from pathlib import Path
from typing import List, Dict

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", ".idea",
    ".vscode", ".sinan", "dist", "build", ".pytest_cache",
}

# 数据文件夹识别信号
DATA_FILENAME_HINTS = {
    "goal.md", "goals.md", "objective.md", "readme.md",
    "metrics.csv", "data.csv", "kpi.md",
}
DATA_EXT_HINTS = {".csv", ".xlsx", ".xls", ".sav", ".db", ".sqlite", ".parquet"}

# 策略文件识别信号
STRATEGY_TITLE_HINTS = ["策略", "strategy", "运营", "方案", "复盘", "plan"]
STRATEGY_FILENAME_HINTS = ["strategy", "plan", "策略"]


def _iter_files(base: Path, max_depth: int = 3, max_files: int = 3000):
    """安全遍历，限制深度和数量"""
    count = 0
    base_depth = len(base.parts)
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        depth = len(Path(root).parts) - base_depth
        if depth > max_depth:
            dirs[:] = []
            continue
        for f in files:
            count += 1
            if count > max_files:
                return
            yield Path(root) / f


def _looks_like_data_folder(folder: Path) -> bool:
    """判断一个目录是否像"数据文件夹" """
    try:
        items = list(folder.iterdir())
    except Exception:
        return False
    if not items:
        return False

    names = {p.name.lower() for p in items if p.is_file()}
    exts = {p.suffix.lower() for p in items if p.is_file()}

    # 命中任一信号就算
    if names & DATA_FILENAME_HINTS:
        return True
    if exts & DATA_EXT_HINTS:
        return True
    # 至少有一个 md 或 csv 且有 2 个以上文件
    if len(items) >= 2 and (".md" in exts or ".csv" in exts):
        return True
    return False


def _looks_like_strategy_file(path: Path, head_chars: int = 600) -> bool:
    """判断一个 .md 文件是否像"策略文件" """
    if path.suffix.lower() != ".md":
        return False
    name_lower = path.name.lower()
    if any(k in name_lower for k in STRATEGY_FILENAME_HINTS):
        return True
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(head_chars)
        head_lower = head.lower()
        return any(k in head_lower for k in STRATEGY_TITLE_HINTS)
    except Exception:
        return False


def discover_data_folders(
    base: str = ".",
    max_depth: int = 3,
    limit: int = 10,
) -> List[Dict]:
    """
    扫描 base 目录，返回候选数据文件夹。
    [{path, file_count, has_table, has_goal}]
    """
    base_path = Path(base).resolve()
    if not base_path.exists():
        return []

    seen = set()
    candidates = []
    for f in _iter_files(base_path, max_depth=max_depth):
        parent = f.parent
        if parent in seen:
            continue
        if not _looks_like_data_folder(parent):
            continue
        seen.add(parent)

        try:
            items = [p for p in parent.iterdir() if p.is_file()]
        except Exception:
            continue
        exts = {p.suffix.lower() for p in items}
        names = {p.name.lower() for p in items}

        candidates.append({
            "path": str(parent.relative_to(base_path)) or ".",
            "abs_path": str(parent),
            "file_count": len(items),
            "has_table": bool(exts & DATA_EXT_HINTS),
            "has_goal": bool(names & {"goal.md", "goals.md", "objective.md"}),
        })
        if len(candidates) >= limit:
            break

    # 排序：含 goal 的 > 含表格的 > 文件多的
    candidates.sort(
        key=lambda x: (not x["has_goal"], not x["has_table"], -x["file_count"]),
    )
    return candidates


def discover_strategy_files(
    base: str = ".",
    max_depth: int = 3,
    limit: int = 10,
) -> List[Dict]:
    """
    扫描 base 目录，返回候选策略文件。
    [{path, abs_path, size_kb}]
    """
    base_path = Path(base).resolve()
    if not base_path.exists():
        return []

    candidates = []
    for f in _iter_files(base_path, max_depth=max_depth):
        if not _looks_like_strategy_file(f):
            continue
        try:
            size_kb = round(f.stat().st_size / 1024, 1)
        except Exception:
            size_kb = 0
        candidates.append({
            "path": str(f.relative_to(base_path)),
            "abs_path": str(f),
            "size_kb": size_kb,
        })
        if len(candidates) >= limit:
            break

    return candidates