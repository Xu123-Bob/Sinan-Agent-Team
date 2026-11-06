"""
文件系统扫描器（纯结构性，不调用 LLM）
· 递归扫描 + 分类分组（data/document/code/config/other）
· 头部采样（文本类读前 1500 字节）
· 二进制安全
"""
import os
import mimetypes
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List


IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", ".idea",
    ".vscode", ".sinan", ".pytest_cache", "dist", "build",
    ".mypy_cache", ".ruff_cache", ".next", "target",
}
IGNORE_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".pyc",
    ".mp4", ".mov", ".avi", ".mp3", ".wav",
    ".woff", ".woff2", ".ttf", ".otf",
}

ROLE_DATA = {".csv", ".xlsx", ".xls", ".sav", ".db", ".sqlite",
             ".parquet", ".json", ".jsonl", ".tsv"}
ROLE_DOC = {".md", ".txt", ".docx", ".doc", ".pptx", ".ppt",
            ".pdf", ".rtf"}
ROLE_CODE = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java",
             ".rs", ".cpp", ".c", ".h", ".rb", ".php", ".sh",
             ".html", ".css", ".scss", ".vue", ".sql"}
ROLE_CONFIG = {".yaml", ".yml", ".toml", ".ini", ".env",
               ".conf", ".cfg", ".properties"}

HEAD_BYTES = 1500
TEXT_PREVIEW_EXTS = {
    ".csv", ".tsv", ".md", ".txt", ".json", ".jsonl",
    ".yaml", ".yml", ".py", ".js", ".ts", ".toml",
    ".ini", ".env", ".sql", ".html",
}


@dataclass
class FileEntry:
    path: str
    abs_path: str
    ext: str
    size_bytes: int
    mime: str
    role: str
    head_preview: str = ""

    def size_kb(self) -> float:
        return round(self.size_bytes / 1024, 1)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "ext": self.ext,
            "size_kb": self.size_kb(),
            "mime": self.mime,
            "role": self.role,
            "head_preview": self.head_preview[:400],
        }


@dataclass
class ScanReport:
    folder: str
    total_files: int
    total_size_mb: float
    groups: Dict[str, List[FileEntry]] = field(default_factory=dict)
    ignored_count: int = 0
    truncated: bool = False

    def to_dict(self) -> dict:
        return {
            "folder": self.folder,
            "total_files": self.total_files,
            "total_size_mb": self.total_size_mb,
            "groups": {k: [f.to_dict() for f in v]
                       for k, v in self.groups.items()},
            "ignored_count": self.ignored_count,
            "truncated": self.truncated,
        }


def _classify(ext: str) -> str:
    ext = ext.lower()
    if ext in ROLE_DATA:   return "data"
    if ext in ROLE_DOC:    return "document"
    if ext in ROLE_CODE:   return "code"
    if ext in ROLE_CONFIG: return "config"
    return "other"


def _read_head(path: str, ext: str) -> str:
    if ext not in TEXT_PREVIEW_EXTS:
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(HEAD_BYTES)
    except Exception:
        return ""


def scan_folder(
    folder: str,
    max_files: int = 500,
    max_total_mb: float = 200.0,
) -> ScanReport:
    base = Path(folder)
    if not base.exists() or not base.is_dir():
        raise ValueError(f"目录不存在或不是文件夹: {folder}")

    groups: Dict[str, List[FileEntry]] = {
        "data": [], "document": [], "code": [], "config": [], "other": [],
    }
    total_files = 0
    total_bytes = 0
    ignored = 0
    truncated = False

    for root, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)
        for fname in sorted(files):
            if total_files >= max_files:
                truncated = True
                break
            fp = Path(root) / fname
            ext = fp.suffix.lower()
            if ext in IGNORE_EXTS:
                ignored += 1
                continue
            try:
                size = fp.stat().st_size
            except Exception:
                ignored += 1
                continue
            if size == 0:
                continue
            total_bytes += size
            if total_bytes > max_total_mb * 1024 * 1024:
                truncated = True
                break

            role = _classify(ext)
            mime, _ = mimetypes.guess_type(str(fp))
            try:
                rel = str(fp.relative_to(base))
            except ValueError:
                rel = fname

            groups[role].append(FileEntry(
                path=rel,
                abs_path=str(fp),
                ext=ext,
                size_bytes=size,
                mime=mime or "application/octet-stream",
                role=role,
                head_preview=_read_head(str(fp), ext),
            ))
            total_files += 1
        if truncated:
            break

    return ScanReport(
        folder=str(base.resolve()),
        total_files=total_files,
        total_size_mb=round(total_bytes / (1024 * 1024), 2),
        groups=groups,
        ignored_count=ignored,
        truncated=truncated,
    )