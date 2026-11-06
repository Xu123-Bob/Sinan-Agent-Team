import hashlib
from pathlib import Path


IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".idea", ".vscode", ".sinan"}


def snapshot_folder(folder: str) -> dict:
    """为文件夹内所有文件生成 MD5 hash 快照"""
    result = {}
    base = Path(folder)
    if not base.exists():
        return result
    for f in base.rglob("*"):
        if not f.is_file():
            continue
        rel_parts = f.relative_to(base).parts
        if any(p in IGNORE_DIRS for p in rel_parts):
            continue
        try:
            content = f.read_bytes()
            result[str(f.relative_to(base))] = hashlib.md5(content).hexdigest()
        except Exception:
            pass
    return result


def detect_changes(old_folder: str, new_folder: str) -> dict:
    """对比两个文件夹的差异，返回可读摘要"""
    old_snap = snapshot_folder(old_folder)
    new_snap = snapshot_folder(new_folder)

    added = sorted(k for k in new_snap if k not in old_snap)
    removed = sorted(k for k in old_snap if k not in new_snap)
    modified = sorted(k for k in new_snap if k in old_snap and new_snap[k] != old_snap[k])
    has_changes = bool(added or removed or modified)

    lines = []
    if added:
        lines.append(f"新增文件: {', '.join(added)}")
    if removed:
        lines.append(f"删除文件: {', '.join(removed)}")
    if modified:
        lines.append(f"修改文件: {', '.join(modified)}")
    if not has_changes:
        lines.append("未检测到任何变化。")

    return {
        "has_changes": has_changes,
        "added": added,
        "removed": removed,
        "modified": modified,
        "summary": "\n".join(lines),
    }