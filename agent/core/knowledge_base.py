"""
知识库加载器（严格只读）

设计要点：
  · 不提供任何 write / save / update 接口 —— 从 API 层就没有"写"这个概念
  · 递归扫描子目录，按优先级加载（文档 > 表格 > 其他）
  · 单文件 8000 字符、总量 20000 字符截断，防止 token 爆炸
  · 目录不存在时优雅降级：返回空字符串
  · 启动时可选检测目录是否物理只读
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional


# 目录黑名单（不扫描）
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", ".idea", ".vscode",
    ".mypy_cache", ".ruff_cache",
}

# 二进制 / 图片 / 视频 / 压缩包 → 跳过
IGNORE_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".bmp", ".webp",
    ".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".mp3", ".wav",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".pyc", ".pyo",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
}

# 优先级分组（高 → 低）
_PRIORITY_DOC = {".md", ".txt", ".rst", ".docx", ".pdf"}  # 文档
_PRIORITY_TABLE = {".csv", ".xlsx", ".xls", ".tsv"}       # 表格
_PRIORITY_STRUCT = {".yaml", ".yml", ".json", ".toml"}    # 结构化

# 默认上限
DEFAULT_MAX_FILE_CHARS = 8000
DEFAULT_MAX_TOTAL_CHARS = 20000


@dataclass
class KnowledgeFile:
    path: str          # 相对路径
    size_bytes: int
    content: str
    truncated: bool = False


@dataclass
class KnowledgeSnapshot:
    """一次性加载的全部知识库快照（只读）"""
    root: str
    files: List[KnowledgeFile] = field(default_factory=list)
    total_chars: int = 0
    truncated: bool = False
    exists: bool = False
    skipped_files: int = 0

    def to_prompt_text(self) -> str:
        """合并为一段可注入 Prompt 的文本"""
        if not self.files:
            return ""
        sections = []
        for f in self.files:
            header = f"### 📄 {f.path}"
            if f.truncated:
                header += " [已截断]"
            sections.append(f"{header}\n{f.content.strip()}")
        text = "\n\n".join(sections)
        if self.truncated:
            text += "\n\n... [知识库总内容过长，部分文件已省略] ..."
        return text

    def summary(self) -> Dict:
        return {
            "root": self.root,
            "exists": self.exists,
            "file_count": len(self.files),
            "total_chars": self.total_chars,
            "truncated": self.truncated,
            "skipped_files": self.skipped_files,
        }


# ==========================================
# 文件分类
# ==========================================
def _priority(ext: str) -> int:
    if ext in _PRIORITY_DOC:
        return 0
    if ext in _PRIORITY_TABLE:
        return 1
    if ext in _PRIORITY_STRUCT:
        return 2
    return 3


# ==========================================
# 单个文件读取
# ==========================================
def _read_file(path: Path, max_chars: int) -> Optional[KnowledgeFile]:
    """
    读取单个知识文件。
    返回 None 表示跳过（二进制 / 读失败 / 空）。
    """
    ext = path.suffix.lower()
    if ext in IGNORE_EXTS:
        return None

    try:
        size = path.stat().st_size
    except Exception:
        return None
    if size == 0:
        return None

    text = ""

    # 表格类
    if ext in {".csv", ".xlsx", ".xls", ".tsv"}:
        try:
            import pandas as pd
            if ext == ".csv":
                df = pd.read_csv(path)
            elif ext == ".tsv":
                df = pd.read_csv(path, sep="\t")
            else:
                df = pd.read_excel(path)
            text = df.head(50).to_markdown(index=False)
        except Exception:
            return None

    # Word
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(path)
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paras)
        except Exception:
            return None

    # PPT
    elif ext == ".pptx":
        try:
            from pptx import Presentation
            prs = Presentation(path)
            parts = []
            for i, slide in enumerate(prs.slides):
                parts.append(f"--- 幻灯片 {i+1} ---")
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        parts.append(shape.text)
            text = "\n".join(parts)
        except Exception:
            return None

    # 纯文本
    else:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

    if not text.strip():
        return None

    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True

    return KnowledgeFile(
        path=str(path),
        size_bytes=size,
        content=text,
        truncated=truncated,
    )


# ==========================================
# 主类
# ==========================================
class KnowledgeBase:
    """
    知识库读取器（只读）

    ⚠️ 刻意不提供 write / save / update / delete 方法。
    任何写操作意图都应使用 safe_io.safe_write，它会拒绝写入知识库目录。
    """

    def __init__(
        self,
        root: str = "./knowledge",
        max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
        max_total_chars: int = DEFAULT_MAX_TOTAL_CHARS,
    ):
        self.root = Path(root).resolve()
        self.max_file_chars = max_file_chars
        self.max_total_chars = max_total_chars

    def load(self) -> KnowledgeSnapshot:
        """一次性加载全部知识（返回快照）"""
        snap = KnowledgeSnapshot(root=str(self.root), exists=self.root.exists())
        if not self.root.exists() or not self.root.is_dir():
            return snap

        # 收集所有候选文件
        candidates: List[tuple[int, Path]] = []  # (priority, path)
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for fname in files:
                if fname.startswith("."):
                    continue
                fp = Path(root) / fname
                if fp.suffix.lower() in IGNORE_EXTS:
                    continue
                candidates.append((_priority(fp.suffix.lower()), fp))

        # 按优先级排序（文档 > 表格 > 结构化 > 其他）
        candidates.sort(key=lambda x: x[0])

        # 逐个加载
        for _, fp in candidates:
            # 预算检查
            if snap.total_chars >= self.max_total_chars:
                snap.truncated = True
                break

            remaining = self.max_total_chars - snap.total_chars
            file_max = min(self.max_file_chars, remaining)

            kf = _read_file(fp, file_max)
            if kf is None:
                snap.skipped_files += 1
                continue

            # 转为相对路径（展示更干净）
            try:
                rel = str(fp.relative_to(self.root))
            except ValueError:
                rel = fp.name
            kf.path = rel

            snap.files.append(kf)
            snap.total_chars += len(kf.content)
            if kf.truncated:
                snap.truncated = True

        return snap

    def load_text(self) -> str:
        """加载为单段文本（Prompt 注入用）"""
        return self.load().to_prompt_text()

    def is_writable(self) -> bool:
        """
        检测目录是否物理可写（仅用于启动提示，不阻断）
        """
        if not self.root.exists():
            return False
        try:
            probe = self.root / ".sinan_write_probe"
            probe.write_text("probe", encoding="utf-8")
            probe.unlink()
            return True
        except Exception:
            return False


# ==========================================
# 便捷函数
# ==========================================
def load_knowledge_text(root: Optional[str] = None) -> str:
    """
    一站式加载知识库并返回 Prompt 文本。
    root 优先取参数；否则取 .env 的 SINAN_KNOWLEDGE_DIR；否则 ./knowledge
    """
    if not root:
        root = os.getenv("SINAN_KNOWLEDGE_DIR", "./knowledge")
    max_chars = int(os.getenv("SINAN_KNOWLEDGE_MAX_CHARS", DEFAULT_MAX_TOTAL_CHARS))
    kb = KnowledgeBase(root=root, max_total_chars=max_chars)
    return kb.load_text()