"""
司南环境诊断工具

用法：
  python -m agent.doctor
"""
import importlib
import platform
import site
import sys
from pathlib import Path

# 依赖清单
REQUIRED_MODULES = [
    ("openai", "openai"),
    ("httpx", "httpx"),
    ("dotenv", "python-dotenv"),
    ("typer", "typer"),
    ("rich", "rich"),
    ("pydantic", "pydantic"),
    ("yaml", "pyyaml"),
    ("pandas", "pandas"),
    ("docx", "python-docx"),
    ("pptx", "python-pptx"),
]

AGENT_MODULES = [
    "agent",
    "agent.cli",
    "agent.main",
    "agent.orchestrator",
    "agent.schemas",
    "agent.llm_factory",
    "agent.agents",
    "agent.agents.base",
    "agent.agents.scout",
    "agent.agents.rubric_agents",
    "agent.agents.strategy_agents",
    "agent.agents.judge",
    "agent.core",
    "agent.core.parser",
    "agent.core.agent_config",
    "agent.core.knowledge_base",
    "agent.core.safe_io",
    "agent.core.file_scanner",
    "agent.core.path_discovery",
    "agent.core.intent_parser",
    "agent.core.scenario_detector",
    "agent.core.rule_engine",
    "agent.core.schema_validator",
    "agent.core.change_detector",
]


def _line(msg=""):
    print(msg)


def check_python():
    _line("=" * 60)
    _line("1. Python 环境")
    _line("=" * 60)
    ver = platform.python_version()
    _line(f"  版本: {ver}")
    _line(f"  可执行: {sys.executable}")
    _line(f"  平台: {platform.system()} {platform.release()}")

    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 14):
        _line("  ⚠️  Python 3.14+ 兼容性风险较高，建议 3.10~3.12")
    elif (major, minor) >= (3, 10):
        _line("  ✅ 版本合格")
    else:
        _line("  ❌ 版本过低，需要 3.10+")


def check_third_party():
    _line()
    _line("=" * 60)
    _line("2. 第三方依赖")
    _line("=" * 60)
    missing = []
    for module_name, package_name in REQUIRED_MODULES:
        try:
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "?")
            _line(f"  ✅ {package_name:<15} {version}")
        except ImportError:
            _line(f"  ❌ {package_name:<15} 未安装")
            missing.append(package_name)
    return missing


def check_agent_package():
    _line()
    _line("=" * 60)
    _line("3. agent 包完整性")
    _line("=" * 60)
    failed = []
    for m in AGENT_MODULES:
        try:
            importlib.import_module(m)
            _line(f"  ✅ {m}")
        except Exception as e:
            _line(f"  ❌ {m}  →  {type(e).__name__}: {e}")
            failed.append((m, str(e)))
    return failed


def check_install_mode():
    _line()
    _line("=" * 60)
    _line("4. 安装方式诊断")
    _line("=" * 60)
    try:
        import agent
        agent_path = Path(agent.__file__).resolve()
        _line(f"  agent 包位置: {agent_path}")
    except Exception as e:
        _line(f"  ❌ 无法定位 agent: {e}")
        return

    # 检查是否是 editable
    sp_dirs = site.getsitepackages()
    in_site_packages = any(str(agent_path).startswith(sp) for sp in sp_dirs)

    if in_site_packages:
        _line("  安装方式: 普通安装（agent 包在 site-packages 内）")
        _line("  ✅ 推荐方式，稳定")
    else:
        _line(f"  安装方式: editable / 源码目录")

        # 检查 sinan 入口
        sinan_exe = Path(sys.executable).parent / "Scripts" / "sinan.exe"
        if sys.platform != "win32":
            sinan_exe = Path(sys.executable).parent / "sinan"
        if sinan_exe.exists():
            _line(f"  ✅ sinan 命令存在: {sinan_exe}")
        else:
            _line(f"  ⚠️  sinan 命令不存在，请用 python -m agent 启动")


def check_startup():
    _line()
    _line("=" * 60)
    _line("5. 启动方式测试")
    _line("=" * 60)
    # 模拟 sinan 启动
    try:
        from agent.cli import app
        _line("  ✅ 加载 agent.cli:app 成功")
    except Exception as e:
        _line(f"  ❌ 加载失败: {e}")


def print_advice(python_ok, missing, agent_failed):
    _line()
    _line("=" * 60)
    _line("诊断结论")
    _line("=" * 60)

    has_issue = False

    if not python_ok:
        has_issue = True
        _line("❌ Python 版本不符合要求")

    if missing:
        has_issue = True
        _line(f"❌ 缺少依赖: {', '.join(missing)}")
        _line(f"   修复: pip install -e .")

    if agent_failed:
        has_issue = True
        _line(f"❌ agent 包有 {len(agent_failed)} 个模块加载失败")
        _line("   修复: pip install --force-reinstall .")

    if not has_issue:
        _line("🎉 一切正常，可以启动：")
        _line("   sinan")
        _line("   或")
        _line("   python -m agent")
    else:
        _line()
        _line("如果你已尝试上面的修复仍失败，请切换到 Python 3.12 后重试。")


def main():
    _line()
    _line("╔" + "═" * 58 + "╗")
    _line("║" + " 司南环境诊断工具 (Sinan Doctor)".center(50) + "║")
    _line("╚" + "═" * 58 + "╝")
    _line()

    check_python()
    missing = check_third_party()
    agent_failed = check_agent_package()
    check_install_mode()
    check_startup()

    major, minor = sys.version_info[:2]
    python_ok = (major, minor) >= (3, 10) and (major, minor) < (3, 14)
    print_advice(python_ok, missing, agent_failed)


if __name__ == "__main__":
    main()