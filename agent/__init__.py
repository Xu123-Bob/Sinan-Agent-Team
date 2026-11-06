"""
司南 (Sinan) — 6-Agent 多智能体策略制定系统
"""
import sys
import warnings

__version__ = "3.2.0"
__author__ = "Sinan Team"

# 静默检查最低版本（不打印任何警告）
if sys.version_info < (3, 10):
    raise RuntimeError(
        f"司南要求 Python 3.10+，当前 {sys.version_info.major}.{sys.version_info.minor}"
    )