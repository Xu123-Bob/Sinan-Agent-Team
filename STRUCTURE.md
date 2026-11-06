# 司南 v3.2 项目结构

> **版本**：v3.2.0  
> **用途**：项目目录树 / 文件职责 / 数据流 / 依赖关系 / 架构要点  
> **配套文档**：[README.md](README.md) · [USAGE.md](USAGE.md) · [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📑 目录

- [一、完整目录树](#一完整目录树)
- [二、文件职责详解](#二文件职责详解)
- [三、6 个智能体一览](#三6-个智能体一览)
- [四、数据流](#四数据流)
- [五、依赖关系图](#五依赖关系图)
- [六、关键架构特性](#六关键架构特性)
- [七、隔离规则](#七隔离规则)
- [八、产物命名规则](#八产物命名规则)
- [九、已删除文件](#九已删除文件)
- [十、目录设计原则](#十目录设计原则)

---

## 一、完整目录树

```
sinan_agent/
│
├── .env                            # 实际配置（含真实 API Key，不入 Git）
├── .env.example                    # 环境变量模板
├── .gitignore                      # 忽略 .env / outputs / knowledge 私密内容
│
├── pyproject.toml                  # 项目元数据 + 依赖 + sinan 命令注册
├── requirements.txt                # 依赖清单（pip install -r）
│
├── README.md                       # 项目简介（快速上手）
├── USAGE.md                        # 完整使用手册
├── STRUCTURE.md                    # 本文件（项目结构说明）
├── TROUBLESHOOTING.md              # 排错手册
├── LICENSE                         # MIT
│
├── Dockerfile                      # 容器化方案
│
├── configs/                        # 配置目录
│   └── rules.yaml                  # 硬性规则（global + 领域 + 用户自定义）
│
├── knowledge/                      # 知识库（只读共享）
│   ├── README.md                   # 放置规则说明
│   └── ...                         # 用户自由组织
│
├── data/                           # 内置示例数据
│   ├── ecommerce_v1/               # 电商初始数据
│   ├── ecommerce_v2/               # 电商新一期数据（用于 evolve 演示）
│   ├── github_v1/                  # GitHub 开源项目示例
│   └── tiktok_v1/                  # TikTok 示例
│
├── outputs/                        # [自动生成] 默认输出目录
│   ├── strategy_*.md               # 最终策略
│   ├── rubric_*.json               # 最终 Rubric
│   ├── debate_*.json               # 完整辩论记录
│   └── v2_*                        # evolve 生成的 V2 产物
│
├── scripts/                        # 安装/运维脚本
│   ├── install.sh                  # Linux / macOS 一键安装
│   └── install.bat                 # Windows 一键安装
│
├── tests/                          # 单元测试（可选）
│   ├── test_schemas.py
│   ├── test_rule_engine.py
│   └── test_agent_config.py
│
└── agent/                          # 核心代码包
    │
    ├── __init__.py                 # 包初始化 + 版本号 + Python 版本检测
    ├── __main__.py                 # `python -m agent` 入口
    ├── doctor.py                   # 环境诊断工具
    │
    ├── cli.py                      # CLI 入口（Typer）
    ├── main.py                     # 业务编排入口
    ├── orchestrator.py             # 5-Agent 博弈编排器
    ├── schemas.py                  # 全部 Pydantic Schema
    ├── llm_factory.py              # LLM 工厂（多 provider + 多 key 轮询）
    │
    ├── agents/                     # 6 个智能体
    │   ├── __init__.py             # 导出所有 Agent
    │   ├── base.py                 # Agent 基类（含知识库注入 + Schema 强校验）
    │   ├── scout.py                # 🔍 ScoutAgent 文件侦察
    │   ├── rubric_agents.py        # 🧩 RubricAgentA + RubricAgentB
    │   ├── strategy_agents.py      # 🎯 StrategyAgentA + StrategyAgentB
    │   └── judge.py                # ⚖️ JudgeAgent 判断智能体
    │
    └── core/                       # 底层能力
        ├── __init__.py
        ├── agent_config.py         # 按 Agent 读 .env 配置（多 key 池）
        ├── knowledge_base.py       # 知识库加载器（只读，无 write 方法）
        ├── safe_io.py              # 安全写入（拦截知识库写入）
        ├── file_scanner.py         # 文件系统结构扫描（零 LLM）
        ├── path_discovery.py       # 路径智能发现（候选数据/策略文件）
        ├── parser.py               # 多格式文件解析（Excel/Word/PPT/DB）
        ├── intent_parser.py        # 自然语言意图解析
        ├── scenario_detector.py    # 场景探测（domain 推断）
        ├── rule_engine.py          # 规则引擎（global + domain + 自定义）
        ├── schema_validator.py     # JSON 稳健解析 + Pydantic 校验
        └── change_detector.py      # 数据变化扫描（evolve 用）
```

---

## 二、文件职责详解

### 🎯 入口层

| 文件 | 职责 | 关键函数/类 |
|---|---|---|
| `agent/cli.py` | Typer CLI 入口。chat / generate / evolve / compare 四个命令；Scout 交互确认；事件渲染器（分色）；横幅 6-Agent 配置表 + 知识库信息；`--knowledge-dir` / `--output-dir` 参数 | `app` / `_chat_loop` / `_run_generate` / `_run_evolve` / `_run_compare` |
| `agent/main.py` | 业务编排。知识库加载；Scout 调用；5-Agent 编排；硬规则后置校验；`safe_write` 落盘三件套 | `scout_folder` / `generate_agent` / `evolve_agent` / `compare_strategies` |
| `agent/orchestrator.py` | 5-Agent 博弈编排。Rubric 组 → Judge → Strategy 组 → Judge；上下文隔离；`knowledge` 透传；`_emit` 事件推送 | `DebateOrchestrator.run` / `_run_rubric_debate` / `_run_strategy_debate` |
| `agent/__main__.py` | `python -m agent` 等价于 `python -m agent.cli`；提供除 `sinan` 外的备选入口 | — |
| `agent/doctor.py` | 环境诊断：Python 版本 / 依赖 / agent 包完整性 / 安装方式 / 启动测试 | `main` / `check_python` / `check_third_party` / `check_agent_package` |

### 🤖 智能体层（`agent/agents/`）

| 文件 | 职责 | 关键类 |
|---|---|---|
| `base.py` | `BaseAgent` 基类：LLM 调用封装 + 知识库自动注入 + `chat_with_schema` 自动重试；统一 `api_keys: List[str]` | `BaseAgent` |
| `scout.py` | 文件侦察：读 `ScanReport` → 输出 `ScoutReport`（业务概览 / 关键目标 / 建议领域 / 澄清问题） | `ScoutAgent` |
| `rubric_agents.py` | 出题组：A 主编 + B 审查员；三轮出题博弈 | `RubricAgentA` / `RubricAgentB` |
| `strategy_agents.py` | 策略组：A 撰写者 + B 反驳者；三轮策略博弈；只接收 `final_rubric` | `StrategyAgentA` / `StrategyAgentB` |
| `judge.py` | 判断智能体：私有 `_memory`；`decide_rubric` / `decide_strategy` 两阶段裁定 | `JudgeAgent` |

### 🧬 数据结构层

| 文件 | 职责 | 关键类 |
|---|---|---|
| `agent/schemas.py` | 全部 Pydantic Schema 定义 | `RubricSchema` / `StrategySchema` / `ScoutReport` / `RubricDecision` / `StrategyDecision` / `DimensionScore` |

### 🔌 LLM 接入层

| 文件 | 职责 | 关键类 |
|---|---|---|
| `agent/llm_factory.py` | 多 provider 配置（deepseek/kimi/qwen/glm/ollama）+ 多 key 池 round-robin 轮询 + 线程安全 | `LLMFactory` / `llm_factory` |

### 🛠 底层能力（`agent/core/`）

| 文件 | 职责 | 关键函数/类 |
|---|---|---|
| `agent_config.py` | 按 Agent 从 `.env` 读取 provider + api_keys；支持单 key / 逗号池 / 编号池；`AgentModelConfig` 数据类 | `get_agent_config` / `get_all_agent_configs` / `summarize_configs` |
| `knowledge_base.py` | 知识库加载器；**无 write 方法**；单文件 8k / 总量 20k 截断；多格式支持 | `KnowledgeBase` / `load_knowledge_text` / `KnowledgeSnapshot` |
| `safe_io.py` | 落盘唯一入口；`assert_not_protected` 拦截写入知识库目录 | `safe_write` / `safe_write_bytes` / `assert_not_protected` |
| `file_scanner.py` | 递归扫描文件夹；按 data/document/config/code/other 分组；安全读取文本头部 | `scan_folder` / `ScanReport` / `FileEntry` |
| `path_discovery.py` | 智能发现候选数据文件夹 / 策略文件；用于 CLI 路径 Prompt 默认值 | `discover_data_folders` / `discover_strategy_files` |
| `parser.py` | 多格式文件解析：CSV/Excel/SPSS/PPT/Word/SQLite → 文本 | `parse_folder_data` / `parse_excel_or_csv` / `parse_pptx` / ... |
| `intent_parser.py` | 用 LLM 把自然语言 → `{action, domain, folder_a, ...}`；禁止编造路径 | `IntentParser.parse` |
| `scenario_detector.py` | 根据文件清单推断 domain（ecommerce/github/...） | `ScenarioDetector.detect` |
| `rule_engine.py` | 硬性规则引擎：global + 领域 + 用户自定义；支持 5 种检查类型 | `RuleEngine.evaluate` / `_collect_rules` |
| `schema_validator.py` | `parse_json_safely`（容错 JSON 提取）+ `validate_with_schema` | `parse_json_safely` / `validate_agent_output` |
| `change_detector.py` | 扫描新旧文件夹的 MD5 差异（evolve 用） | `detect_changes` / `snapshot_folder` |

### ⚙️ 配置与安装

| 文件 | 职责 |
|---|---|
| `.env.example` | 三层配置模板：Provider key / Agent provider / 知识库 / 运行时开关 |
| `configs/rules.yaml` | 硬性规则库；global 段 + 各领域段 + 用户自定义段 |
| `pyproject.toml` | 项目元数据 + 依赖 + `sinan` 命令注册 + ruff/mypy/pytest 配置 |
| `requirements.txt` | 精简依赖清单（便于一键 pip install） |
| `scripts/install.sh` | Linux/macOS 一键安装（检查 Python → venv → pip → doctor） |
| `scripts/install.bat` | Windows 一键安装（同上） |
| `Dockerfile` | 容器化方案；基于 Python 3.12；内置所有依赖 |

### 📚 知识库目录

| 文件/目录 | 职责 |
|---|---|
| `knowledge/` | 用户自由组织的只读参考知识 |
| `knowledge/README.md` | 说明放置规则、体量控制、格式支持 |

> **重要**：代码中**没有**任何函数会写入 `knowledge/`，且 `safe_io.safe_write` 会拦截。建议用户额外执行 `chmod -R a-w knowledge/`。

---

## 三、6 个智能体一览

| Agent | 图标 | 类型 | 输入 | 输出 Schema | 上下游 |
|---|:---:|---|---|---|---|
| `ScoutAgent` | 🔍 | 侦察 | `ScanReport` + knowledge | `ScoutReport` | 最上游，独立调用 |
| `RubricAgentA` | 🧩 | 出题主编 | goal + domain + rules + knowledge | `RubricSchema` | Rubric 组 |
| `RubricAgentB` | 🧩 | 出题审查 | 当前 Rubric + goal + rules + knowledge | `RubricSchema` | Rubric 组 |
| `StrategyAgentA` | 🎯 | 策略撰写 | goal + domain + `final_rubric` + rules + knowledge | `StrategySchema` | Strategy 组 |
| `StrategyAgentB` | 🎯 | 策略反驳 | 当前策略 + goal + domain + `final_rubric` + knowledge | `str`（纯文本反驳） | Strategy 组 |
| `JudgeAgent` | ⚖️ | 判断 | 完整 history + goal + domain + knowledge | `RubricDecision` / `StrategyDecision` | 两次裁定 |

### 博弈轮次

```
ScoutAgent         → 1 次 LLM 调用

Rubric 组（3 轮）：
  RubricAgentA 出初稿       → 1 次
  RubricAgentB 第 1 轮审核  → 1 次
  RubricAgentA 第 1 轮修改  → 1 次
  RubricAgentB 第 2 轮审核  → 1 次
  RubricAgentA 第 2 轮修改  → 1 次
  RubricAgentB 第 3 轮审核  → 1 次
  ──────────────────────────────
  Judge.decide_rubric       → 1 次

Strategy 组（3 轮）：
  StrategyAgentA 出初稿     → 1 次
  StrategyAgentB 第 1 轮反驳 → 1 次
  StrategyAgentA 第 1 轮修改 → 1 次
  StrategyAgentB 第 2 轮反驳 → 1 次
  StrategyAgentA 第 2 轮修改 → 1 次
  StrategyAgentB 第 3 轮反驳 → 1 次
  ──────────────────────────────
  Judge.decide_strategy     → 1 次

总计：约 12~15 次 LLM 调用
```

---

## 四、数据流

```
启动
 │
 ├─ [.env]           → agent_config       → 6 个 Agent 的 provider + api_keys
 ├─ [knowledge/]     → knowledge_base     → 只读文本
 └─ [configs/rules.yaml] → rule_engine    → 硬规则约束
 │
 ▼
用户输入（CLI / chat）
 │
 ▼
[🔍 ScoutAgent]  ← file_scanner + knowledge + LLM
 │  扫描 → 摘要 → 用户 4 选 1 确认
 ▼
[main.generate_agent]
 │  拼接 extra_context（Scout 结果 + 单文件约束）
 │  硬规则约束注入 Prompt
 ▼
[DebateOrchestrator.run]
 │
 ├─ Phase 1: Rubric 组 A ⇄ B 三轮博弈
 │            history（隔离区 1，✗ 传给策略组）
 │                │
 │                ▼
 ├─ Phase 2: Judge.decide_rubric  →  final_rubric
 │
 ├─ Phase 3: Strategy 组 A ⇄ B 三轮博弈
 │            只接收 final_rubric
 │            history（隔离区 2，✗ 传给策略组）
 │                │
 │                ▼
 └─ Phase 4: Judge.decide_strategy  →  final_strategy + 分数
 │
 ▼
[RuleEngine.evaluate]  硬规则后置校验
 │
 ▼
[safe_io.safe_write] 落盘三件套
 ├─ strategy_*.md   → ✅ 允许
 ├─ rubric_*.json   → ✅ 允许
 ├─ debate_*.json   → ✅ 允许
 └─ knowledge/*     → ⛔ PermissionError
```

---

## 五、依赖关系图

```
agent/cli.py
  ├─ agent/main.py
  │   ├─ agent/core/parser.py
  │   ├─ agent/core/rule_engine.py
  │   ├─ agent/core/change_detector.py
  │   ├─ agent/core/agent_config.py
  │   ├─ agent/core/knowledge_base.py
  │   ├─ agent/core/safe_io.py
  │   └─ agent/orchestrator.py
  │       ├─ agent/agents/rubric_agents.py
  │       │   └─ agent/agents/base.py
  │       │       ├─ agent/llm_factory.py
  │       │       └─ agent/core/schema_validator.py
  │       ├─ agent/agents/strategy_agents.py
  │       │   └─ agent/agents/base.py
  │       ├─ agent/agents/judge.py
  │       │   └─ agent/agents/base.py
  │       ├─ agent/core/agent_config.py
  │       └─ agent/schemas.py
  │
  ├─ agent/core/intent_parser.py
  │   └─ agent/llm_factory.py
  ├─ agent/core/scenario_detector.py
  │   └─ agent/llm_factory.py
  ├─ agent/core/agent_config.py
  ├─ agent/core/knowledge_base.py
  ├─ agent/core/path_discovery.py
  └─ agent/main.py（同上）

agent/agents/scout.py
  └─ agent/agents/base.py

agent/doctor.py
  └─（仅标准库 + agent 内部模块）
```

### 依赖层级（从下到上）

```
第 1 层（最底层，无内部依赖）：
  agent/schemas.py
  agent/llm_factory.py
  agent/core/parser.py
  agent/core/file_scanner.py
  agent/core/path_discovery.py
  agent/core/safe_io.py
  agent/core/knowledge_base.py

第 2 层：
  agent/core/agent_config.py   （依赖 llm_factory 类型）
  agent/core/schema_validator.py（依赖 pydantic）
  agent/core/rule_engine.py    （仅标准库 + yaml）
  agent/core/change_detector.py

第 3 层：
  agent/agents/base.py         （依赖 llm_factory + schema_validator）
  agent/core/intent_parser.py  （依赖 llm_factory）
  agent/core/scenario_detector.py

第 4 层：
  agent/agents/scout.py        （依赖 base）
  agent/agents/rubric_agents.py（依赖 base + schemas）
  agent/agents/strategy_agents.py
  agent/agents/judge.py

第 5 层：
  agent/orchestrator.py        （依赖所有 agents + schemas + agent_config）

第 6 层：
  agent/main.py                （依赖 orchestrator + 所有 core）

第 7 层（最上层）：
  agent/cli.py                 （依赖 main + 部分 core）
```

---

## 六、关键架构特性

| 特性 | 实现位置 | 说明 |
|---|---|---|
| **6-Agent 分层** | `agents/` 下 6 个 Agent 类 | 各司其职，避免单点盲区 |
| **上下文隔离** | `orchestrator._run_strategy_debate` 只传 `final_rubric` | 出题组 history 不会流入策略组 |
| **Judge 私有记忆** | `JudgeAgent._memory` | 永不外泄 |
| **知识库只读共享** | `knowledge_base`（无 write 方法）+ `safe_io`（拦截写入） | 6 Agent 可读，任何 Agent 不可写 |
| **Schema 强校验** | `BaseAgent.chat_with_schema` + `schemas.py` | 输出必过 Pydantic，失败重试 2 次 |
| **硬规则双校验** | `main.generate_agent` 前注入 Prompt，后调 `RuleEngine` | 生成前 + 生成后双层防护 |
| **多 key 池轮询** | `llm_factory._pick_key` + `agent_config._collect_keys` | 同池跨 Agent 全局 round-robin |
| **任意路径支持** | `path_discovery.py` + CLI `_ask_*_with_discovery` | 用户可给任意位置路径 |
| **单文件输入** | `main._normalize_input_path` | 用户传单个文件自动取父目录并限定范围 |
| **Scout 预审闭环** | `scout_folder` → `_run_scout_and_confirm`（4 选 1） | 生成前确认目标 |
| **环境诊断** | `agent/doctor.py` | 一键排查安装问题 |
| **三入口备选** | `sinan` / `python -m agent` / `python -m agent.cli` | 任意一条能用即可 |

---

## 七、隔离规则

### 7.1 上下文隔离矩阵

| Agent | 可看 Rubric 博弈 | 可看 Strategy 博弈 | 可看 Judge 记忆 | 可看知识库 | 可写知识库 |
|---|:---:|:---:|:---:|:---:|:---:|
| 🔍 ScoutAgent | ✗ | ✗ | ✗ | ✓ | ✗ |
| 🧩 RubricAgentA | ✓（自己组） | ✗ | ✗ | ✓ | ✗ |
| 🧩 RubricAgentB | ✓（自己组） | ✗ | ✗ | ✓ | ✗ |
| 🎯 StrategyAgentA | ✗（只拿 final_rubric） | ✓（自己组） | ✗ | ✓ | ✗ |
| 🎯 StrategyAgentB | ✗（只拿 final_rubric） | ✓（自己组） | ✗ | ✓ | ✗ |
| ⚖️ JudgeAgent | ✓ | ✓ | ✓（自身私有） | ✓ | ✗ |

### 7.2 三个隔离区

```
┌─────────────────────────────────────────────────┐
│ 隔离区 1：Rubric 组内部                          │
│   · RubricAgentA ⇄ RubricAgentB                 │
│   · 双方 history 互通                            │
│   · history 只传给 Judge，不传给策略组           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 隔离区 2：Strategy 组内部                        │
│   · StrategyAgentA ⇄ StrategyAgentB             │
│   · 双方 history 互通                            │
│   · 只接收 final_rubric，✗ 看不到 rubric_history│
│   · history 只传给 Judge                         │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 隔离区 3：Judge 私有                             │
│   · JudgeAgent._memory                          │
│   · 唯一能看全部历史的 Agent                     │
│   · 只对外输出决策产物（final_rubric/final_...）│
│   · 永不外泄 _memory                             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 公共层：知识库                                   │
│   · knowledge/ 目录                              │
│   · 所有 Agent 可读                              │
│   · 任何 Agent 不可写（safe_io 拦截）            │
│   · 静态公共参考，与博弈过程无关                 │
└─────────────────────────────────────────────────┘
```

---

## 八、产物命名规则

### 8.1 文件命名

```
{prefix}{type}_{domain}_{folder_name}_{timestamp}.{ext}
```

| 段 | 取值 | 说明 |
|---|---|---|
| `prefix` | `""` 或 `"v2_"` | 空 = 初始版本；`v2_` = evolve 生成 |
| `type` | `strategy` / `rubric` / `debate` | 产物类型 |
| `domain` | `ecommerce` / `github` / ... | 业务领域 |
| `folder_name` | 数据文件夹名 | 便于追溯数据源 |
| `timestamp` | `YYYYMMDD_HHMMSS` | 精确到秒，防覆盖 |
| `ext` | `.md` / `.json` | 格式 |

### 8.2 示例

```
outputs/
├── strategy_ecommerce_ecommerce_v1_20251104_141500.md
├── rubric_ecommerce_ecommerce_v1_20251104_141500.json
├── debate_ecommerce_ecommerce_v1_20251104_141500.json
├── v2_strategy_ecommerce_ecommerce_v2_20251105_090000.md
├── v2_rubric_ecommerce_ecommerce_v2_20251105_090000.json
└── v2_debate_ecommerce_ecommerce_v2_20251105_090000.json
```

### 8.3 三件套职责

| 文件 | 内容 |
|---|---|
| `strategy_*.md` | 最终策略（Markdown，可直接阅读） |
| `rubric_*.json` | 最终 Rubric（结构化，可复用） |
| `debate_*.json` | 完整辩论记录（rubric_history + strategy_history + judge_reasoning） |

---

## 九、已删除文件

### 9.1 v2 → v3 重构时移除

| 旧文件 | 被谁替代 |
|---|---|
| `agent/core/platform_detector.py` | `agent/core/scenario_detector.py` |
| `agent/core/rubric_engine.py` | `agent/agents/rubric_agents.py` + `judge.py` |
| `agent/core/optimizer.py` | `agent/agents/strategy_agents.py` + `judge.py` |
| `agent/core/evaluator.py` | `agent/agents/judge.py` |
| `rubrics/` 目录 | v3 不再写入；Rubric 存 `outputs/rubric_*.json` |

### 9.2 迁移说明

如果你从 v2 升级到 v3：

```bash
# 1. 备份旧文件（保险起见）
cp -r rubrics rubrics_v2_backup

# 2. 删除旧文件
rm agent/core/platform_detector.py
rm agent/core/rubric_engine.py
rm agent/core/optimizer.py
rm agent/core/evaluator.py
rm -rf rubrics/

# 3. 确认没有代码引用旧模块
grep -r "platform_detector\|rubric_engine\|optimizer\|evaluator" agent/
# 应无结果

# 4. 运行诊断验证
python -m agent.doctor
```

---

## 十、目录设计原则

### 10.1 分层清晰

```
agent/
├── agents/    ← 智能体（"谁来做"）
├── core/      ← 底层能力（"用什么做"）
├── *.py       ← 顶层编排（"怎么串起来"）
```

- **agents/** 只关心"这个 Agent 怎么调用 LLM、怎么输出结构化结果"
- **core/** 只关心"文件怎么解析、规则怎么校验、知识库怎么加载"等通用能力
- **顶层 .py** 负责编排（`orchestrator`）、入口（`cli`）、流程（`main`）

### 10.2 输入输出边界

| 边界 | 处理位置 |
|---|---|
| 用户路径输入 | `cli.py` → `main.py` |
| 文件解析 | `core/parser.py` |
| LLM 调用 | `llm_factory.py`（唯一出口） |
| Schema 校验 | `core/schema_validator.py`（唯一入口） |
| 硬规则校验 | `core/rule_engine.py` |
| 文件写入 | `core/safe_io.py`（唯一出口） |
| 知识库读取 | `core/knowledge_base.py`（唯一入口） |
| 知识库写入 | ⛔ 不存在（任何路径都不允许） |

### 10.3 配置外置

- **模型配置**：`.env`（Provider / Agent / 多 key 池）
- **硬规则**：`configs/rules.yaml`
- **知识库**：`knowledge/`（用户自由组织）
- **代码中无硬编码的 provider / key / 规则**

### 10.4 可替换性

- **换模型**：改 `.env` 即可，不改代码
- **加领域**：在 `configs/rules.yaml` 里加新段，不改代码
- **扩知识**：往 `knowledge/` 丢文件即可
- **改 Agent 行为**：改 `agent/agents/*.py` 里的 prompt，不影响其他模块

---

**文档结束** · 相关文档：[README.md](README.md) · [USAGE.md](USAGE.md) · [TROUBLESHOOTING.md](TROUBLESHOOTING.md)