"""
让 `python -m agent` 等价于 `python -m agent.cli`

用户即使 `sinan` 命令失效，也有备用启动方式。
"""
from agent.cli import app

if __name__ == "__main__":
    app()