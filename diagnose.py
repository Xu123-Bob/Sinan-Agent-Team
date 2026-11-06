"""诊断 sinan.exe 加载了哪个 agent 包"""
import sys
import site
from pathlib import Path


def main():
    print("=" * 70)
    print("诊断 1: Python 版本与 sys.path")
    print("=" * 70)
    print(f"Python: {sys.version}")
    print(f"可执行文件: {sys.executable}")
    print()
    for i, p in enumerate(sys.path):
        print(f"  [{i}] {p or '(空)'}")

    print()
    print("=" * 70)
    print("诊断 2: 当前能 import 到哪个 agent")
    print("=" * 70)
    try:
        import agent
        print(f"  agent       → {agent.__file__}")
    except Exception as e:
        print(f"  agent 导入失败: {e}")
        return
    try:
        import agent.core
        print(f"  agent.core  → {agent.core.__file__}")
    except Exception as e:
        print(f"  agent.core 导入失败: {e}")
    try:
        import agent.core.parser
        print(f"  agent.core.parser → {agent.core.parser.__file__}")
    except Exception as e:
        print(f"  ❌ agent.core.parser 导入失败: {e}")

    print()
    print("=" * 70)
    print("诊断 3: 所有能搜到 agent 包的位置")
    print("=" * 70)
    seen = set()
    for p in sys.path:
        if not p:
            continue
        candidate = Path(p) / "agent"
        if candidate.exists() and candidate.is_dir():
            real = candidate.resolve()
            if real in seen:
                continue
            seen.add(real)
            has_parser = (candidate / "core" / "parser.py").exists()
            has_init = (candidate / "__init__.py").exists()
            mark = "✅" if has_parser else "❌ 缺 parser.py"
            print(f"  {candidate}")
            print(f"      __init__: {has_init}    parser.py: {has_parser}  {mark}")

    print()
    print("=" * 70)
    print("诊断 4: site-packages 里的 sinan / agent 相关痕迹")
    print("=" * 70)
    for sp in site.getsitepackages():
        sp_path = Path(sp)
        if not sp_path.exists():
            continue

        # 找 sinan*.dist-info / egg-info
        for pattern in ["sinan*.dist-info", "sinan*.egg-info", "agent*.dist-info"]:
            for d in sp_path.glob(pattern):
                print(f"  包信息: {d}")

        # 找 agent 目录（非 editable）
        agent_dir = sp_path / "agent"
        if agent_dir.exists() and agent_dir.is_dir():
            has_parser = (agent_dir / "core" / "parser.py").exists()
            print(f"  目录: {agent_dir}  parser.py: {has_parser}")

        # 找 .pth 文件
        for pth in sp_path.glob("*.pth"):
            try:
                content = pth.read_text(errors="ignore")
            except Exception:
                continue
            low = content.lower()
            if "sinan" in low or "agent" in low:
                print(f"  .pth: {pth}")
                for line in content.splitlines():
                    if line.strip():
                        print(f"        → {line.strip()}")

    print()
    print("=" * 70)
    print("诊断 5: sinan.exe 是否存在")
    print("=" * 70)
    scripts_dir = Path(sys.executable).parent / "Scripts"
    for exe in ["sinan.exe", "sinan-script.py", "sinan"]:
        p = scripts_dir / exe
        if p.exists():
            print(f"  找到: {p}")


if __name__ == "__main__":
    main()