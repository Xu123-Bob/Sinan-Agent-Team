"""
司南环境自检脚本
用法：python check_env.py
"""
import importlib
import sys
from pathlib import Path


MODULES = [
    # 顶层
    "agent",
    "agent.cli",
    "agent.main",
    "agent.orchestrator",
    "agent.schemas",
    "agent.llm_factory",
    # agents 包
    "agent.agents",
    "agent.agents.base",
    "agent.agents.scout",
    "agent.agents.rubric_agents",
    "agent.agents.strategy_agents",
    "agent.agents.judge",
    # core 包
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


def main() -> int:
    print("=" * 60)
    print("司南环境自检")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"工作目录: {Path.cwd()}")
    print()

    # 1. 检查目录结构
    print("[目录结构检查]")
    expected_files = [
        "agent/__init__.py",
        "agent/cli.py",
        "agent/main.py",
        "agent/orchestrator.py",
        "agent/schemas.py",
        "agent/llm_factory.py",
        "agent/agents/__init__.py",
        "agent/agents/base.py",
        "agent/agents/scout.py",
        "agent/agents/rubric_agents.py",
        "agent/agents/strategy_agents.py",
        "agent/agents/judge.py",
        "agent/core/__init__.py",
        "agent/core/parser.py",
        "agent/core/agent_config.py",
        "agent/core/knowledge_base.py",
        "agent/core/safe_io.py",
        "agent/core/file_scanner.py",
        "agent/core/path_discovery.py",
        "agent/core/intent_parser.py",
        "agent/core/scenario_detector.py",
        "agent/core/rule_engine.py",
        "agent/core/schema_validator.py",
        "agent/core/change_detector.py",
    ]
    missing_files = []
    for f in expected_files:
        if Path(f).exists():
            print(f"  ✅ {f}")
        else:
            print(f"  ❌ {f}  ← 缺失")
            missing_files.append(f)

    print()

    # 2. 检查模块导入
    print("[模块导入检查]")
    failed_modules = []
    for m in MODULES:
        try:
            importlib.import_module(m)
            print(f"  ✅ {m}")
        except Exception as e:
            print(f"  ❌ {m}  →  {type(e).__name__}: {e}")
            failed_modules.append((m, str(e)))

    print()
    print("=" * 60)
    if missing_files or failed_modules:
        if missing_files:
            print(f"⚠ 缺少文件 {len(missing_files)} 个：")
            for f in missing_files:
                print(f"    - {f}")
        if failed_modules:
            print(f"⚠ 导入失败 {len(failed_modules)} 个：")
            for m, err in failed_modules:
                print(f"    - {m}: {err}")
        print()
        print("请补齐上述文件后再试。")
        return 1
    else:
        print("🎉 全部通过，可以运行 sinan")
        return 0


if __name__ == "__main__":
    sys.exit(main())