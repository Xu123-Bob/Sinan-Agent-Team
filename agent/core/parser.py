"""
多格式文件解析器

将数据文件夹中的各类文件（Excel/CSV/SPSS/PPT/Word/SQLite/纯文本）
解析为 LLM 可读的文本。支持总量截断与单文件截断。

接口：
  parse_folder_data(folder_path, max_chars=40000) -> str
"""
import os
import sqlite3
from pathlib import Path

import pandas as pd
from docx import Document
from pptx import Presentation


# ==========================================
# 常量
# ==========================================
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", ".idea", ".vscode",
    ".sinan", ".mypy_cache", ".ruff_cache", "dist", "build",
}

IGNORE_EXTS = {
    # 图片
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".bmp", ".webp",
    # 压缩包
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    # 可执行文件
    ".exe", ".dll", ".so", ".dylib", ".pyc", ".pyo",
    # 音视频
    ".mp4", ".mov", ".avi", ".mkv", ".flv", ".mp3", ".wav",
    # 字体
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
}

# 单文件字符上限（超出截断）
MAX_CHARS_PER_FILE = 8000


# ==========================================
# 各类型文件解析
# ==========================================
def parse_excel_or_csv(file_path: Path) -> str:
    """Excel / CSV → Markdown 表格（前 50 行）"""
    try:
        ext = file_path.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext == ".tsv":
            df = pd.read_csv(file_path, sep="\t")
        else:
            df = pd.read_excel(file_path)
        return df.head(50).to_markdown(index=False)
    except Exception as e:
        return f"[解析表格失败: {e}]"


def parse_spss(file_path: Path) -> str:
    """SPSS .sav 文件 → Markdown 表格（可选依赖 pyreadstat）"""
    try:
        import pyreadstat
        df, _meta = pyreadstat.read_sav(str(file_path))
        return df.head(50).to_markdown(index=False)
    except ImportError:
        return "[未安装 pyreadstat，无法解析 .sav；请执行 pip install pyreadstat]"
    except Exception as e:
        return f"[解析 SPSS 失败: {e}]"


def parse_pptx(file_path: Path) -> str:
    """PPT → 提取所有幻灯片文本"""
    try:
        prs = Presentation(file_path)
        parts = []
        for i, slide in enumerate(prs.slides):
            parts.append(f"--- 幻灯片 {i + 1} ---")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    parts.append(shape.text)
        return "\n".join(parts)
    except Exception as e:
        return f"[解析 PPT 失败: {e}]"


def parse_docx(file_path: Path) -> str:
    """Word → 段落 + 表格文本"""
    try:
        doc = Document(file_path)
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    except Exception as e:
        return f"[解析 DOCX 失败: {e}]"


def parse_sqlite(file_path: Path) -> str:
    """SQLite 数据库 → 表结构 + 每表前 20 行"""
    try:
        conn = sqlite3.connect(str(file_path))
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            parts = []
            for (t_name,) in tables:
                parts.append(f"--- 表名: {t_name} ---")
                try:
                    df = pd.read_sql_query(f"SELECT * FROM `{t_name}` LIMIT 20", conn)
                    parts.append(df.to_markdown(index=False))
                except Exception as e:
                    parts.append(f"[表 {t_name} 读取失败: {e}]")
            return "\n".join(parts) if parts else "[数据库中无表]"
        finally:
            conn.close()
    except Exception as e:
        return f"[解析 SQLite 失败: {e}]"


def parse_text(file_path: Path) -> str:
    """纯文本（.md/.txt/.json/.yaml/.sql/代码等）"""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return "[无法读取的二进制文件]"


# ==========================================
# 分发器
# ==========================================
def _parse_single_file(file_path: Path) -> str:
    ext = file_path.suffix.lower()

    if ext in {".csv", ".tsv", ".xlsx", ".xls"}:
        return parse_excel_or_csv(file_path)
    if ext == ".sav":
        return parse_spss(file_path)
    if ext == ".pptx":
        return parse_pptx(file_path)
    if ext == ".docx":
        return parse_docx(file_path)
    if ext in {".db", ".sqlite"}:
        return parse_sqlite(file_path)
    if ext in {".doc", ".ppt"}:
        return "[提示] 旧版 Office 格式解析受限，建议另存为 docx/pptx 后重试。"
    # 其余按纯文本处理
    return parse_text(file_path)


# ==========================================
# 主接口
# ==========================================
def parse_folder_data(folder_path: str, max_chars: int = 40000) -> str:
    """
    递归解析文件夹，把所有文件内容拼成一段文本。

    参数
    ----
    folder_path : str
        数据文件夹路径（任意位置）
    max_chars : int
        总字符上限，超出截断（防止 token 爆炸）

    返回
    ----
    str
        拼装后的完整文本
    """
    path = Path(folder_path)

    # 单文件兼容：若传入的是文件，只解析该文件
    if path.is_file():
        content = _parse_single_file(path)
        if len(content) > MAX_CHARS_PER_FILE:
            content = content[:MAX_CHARS_PER_FILE] + "\n... [内容过长已截断] ..."
        header = f"\n{'=' * 40}\n📄 文件: {path.name}\n{'=' * 40}\n"
        return header + content

    if not path.exists() or not path.is_dir():
        raise ValueError(f"目录不存在: {folder_path}")

    parsed_parts = []
    current_chars = 0

    for root, dirs, files in os.walk(path):
        # 过滤黑名单目录
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)

        for fname in sorted(files):
            file_path = Path(root) / fname
            ext = file_path.suffix.lower()

            if ext in IGNORE_EXTS:
                continue

            # 解析单文件
            content = _parse_single_file(file_path)

            # 单文件截断
            if len(content) > MAX_CHARS_PER_FILE:
                content = content[:MAX_CHARS_PER_FILE] + "\n... [内容过长已截断] ..."

            try:
                rel_path = file_path.relative_to(path)
            except ValueError:
                rel_path = fname

            header = f"\n{'=' * 40}\n📄 文件: {rel_path}\n{'=' * 40}\n"

            # 总量截断检查
            if current_chars + len(header) + len(content) > max_chars:
                parsed_parts.append(
                    "\n... [已达到上下文限制，剩余文件省略] ..."
                )
                return "".join(parsed_parts)

            parsed_parts.append(header)
            parsed_parts.append(content)
            current_chars += len(header) + len(content)

    return "".join(parsed_parts) if parsed_parts else "文件夹为空。"