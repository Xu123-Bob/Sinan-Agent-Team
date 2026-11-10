<div align="center">

<img src="image/logopage02.png" alt="Baize Logo" width="320" />

# Sinan (Sinan-Agent-Team)

**Multi-Agent Strategy-Making System**

Dual Gameplay · Context Isolation · Shared Knowledge Base · Strict JSON Schema Validation · Multi-Provider Multi-Key Rotation

<p align="center">

  <a href="https://github.com/Xu123-Bob/Sinan-Agent-Team/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Xu123-Bob/Sinan-Agent-Team?style=flat-square" alt="License">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  </a>
</p>

<p align="center">
  <a href="README.cn.md">简体中文</a> |
  <a href="README.en.md">English</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.es.md">Español</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.ru.md">Русский язык</a> |
</p>

</div>

----------
## Overview
**This project is a multi-agent framework for strategy-making and strategy-evaluation**
- The product builds a system for strategy-making and strategy evaluation through **Rule / Rubric / LLM-to-judge**
- There are **6 agents** in total: 2 question-setting agents, 2 judging agents, 1 scouting agent, and 1 decision agent
- The Rule layer includes constraints on business content as well as constraints on **agent output structure** (to ensure agents output correctly)
- Rubrics are produced through **two question-setting agents playing a game**, each stating its views, with the **judging agent making the final confirmation**
- Strategy-making and evaluation are carried out through **discussion between 2 strategy-making agents**, also finalized by the **judging agent**
- Scanning and acquiring data and professional knowledge is done by **1 scouting agent**, which mainly scans `knowledge/`, `data/`, and `output/`
- Generated artifacts include: **strategy plans, Rubric question sheets, and discussion transcripts**, all saved to `knowledge/`; the **scouting agent automatically scans them when iterating on new strategies**
- This project is my entry for the 2026 Beijing AI Youth Hackathon. It received a score of 4th place from Alipay and was recommended for the Alipay - Intelligent Entities Surge Competition.

### Multi-Agent Architecture Diagram

<div align="center">
Multi-Agent Architecture Diagram
</div>

<p align="center">
  <img src="image/infra.png" alt="Multi-Agent Architecture Diagram" width="800" />
</p>

### Product Introduction
Static URL: https://sinan-website.pages.dev/

---

## Core Features

- **6-Agent Architecture**: Scouting / Question-setting team (A+B) / Strategy team (A+B) / Judgment — each with its own role
- **Strict Context Isolation**: Question-setting team ↔ Strategy team fully isolated; Judge's private memory never leaks
- **Read-Only Shared Knowledge Base**: `knowledge/` is readable by all Agents, but no Agent can write to it
- **Dual Gameplay, Three Rounds**: Rubric team A ⇄ B and Strategy team A ⇄ B, each playing three rounds
- **Independent Judge Ruling**: The only agent that can see the full context, and it outputs only the decision artifact
- **Strict JSON Schema Validation**: Every Agent output must pass Pydantic; failures trigger automatic retries (up to 2 times)
- **Hard Rules Validated Both Before and After**: Injected into the Prompt before generation, independently re-checked after generation; users can customize baselines
- **Multi-Provider, Multi-Key**: Multiple keys supported per Provider with rotation; each Agent can specify its own model
- **Arbitrary Path Input**: Relative / absolute / Windows / Linux / single file / folder; press Enter to auto-scan
- **Any Business Domain**: Built-in ecommerce / GitHub / AtomGit / Douyin / TikTok; extensible with custom domains
- **Fully Chinese CLI**: Typer + Rich rendering, color-coded panels, real-time debate printing

---
## Login interface
<div align="center">
Login interface
</div>

<p align="center">
  <img src="image/sinancli-01.jpg" alt="Login interface" width="800" />
</p>

## Environment Requirements (Read This First)
```
| Item | Recommended | Notes |
|---|---|---|
| **Python** | **3.10 / 3.11 / 3.12** | ⭐ Strongly recommended |
| Python 3.13 | Usable | Some dependencies may have minor issues |
| Python 3.14+ | ❌ **Not recommended** | Known compatibility issues with editable install |
| OS | Windows / macOS / Linux | Cross-platform support |
| Network | Requires access to LLM APIs | DeepSeek / Kimi / Qwen, etc. |
```
> **If you hit any installation or startup issue, run diagnostics first**:
> ```bash
> python -m agent.doctor
> ```
> It checks the Python version, dependencies, agent package integrity, install method, and startup test all at once, and provides fix suggestions.

---

## Installation (Choose 1 of 3)

### Option 1: One-Click Script (Recommended for Beginners)

```bash
# Windows
scripts\install.bat

# Linux / macOS
bash scripts/install.sh
```

The script automatically checks Python, creates a venv, installs dependencies, and runs doctor for verification.

### Option 2: Manual Installation (For Developers Familiar with Python)

```bash
# Strongly recommended to use a virtual environment
python -m venv .venv

# Activate (choose one)
source .venv/bin/activate         # Linux / macOS
.venv\Scripts\activate            # Windows CMD
.venv\Scripts\Activate.ps1        # Windows PowerShell

# Install
pip install -e .
```

> **Note for Python 3.13+ users**: If the `sinan` command raises `ModuleNotFoundError: agent.core.xxx` after `pip install -e .`, switch to:
> ```bash
> pip install .
> ```
> Or start directly with `python -m agent` (see the "Startup" section below).

### Option 3: Docker (No Environment Hassle)

```bash
docker build -t sinan .

docker run -it --rm \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/knowledge:/app/knowledge \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  sinan
```

Completely bypasses all Python version, dependency compilation, and system differences.

---

## Startup (3 Equivalent Ways)

```bash
sinan                  # pip-installed command (most convenient)
python -m agent        # Alternative (use this if sinan fails)
python -m agent.cli    # Another alternative
```

**All three commands are fully equivalent** — as long as one works, you're good.

If `sinan` errors out, just use `python -m agent` instead — **no need to troubleshoot**.

---

## Quick Start

### 1. Configure the Backend

```bash
cp .env.example .env
```

Edit `.env` and fill in **at least one** API Key (minimal config):

```env
SINAN_DEEPSEEK_API_KEY=sk-your-key
SINAN_DEFAULT_PROVIDER=deepseek
```

Delete all other fields — just these two lines.

> For advanced configuration with multiple models, multi-key pools, and per-Agent assignment, see [`USAGE.md`](USAGE.md).

### 2. Prepare the Knowledge Base (Optional)

```bash
mkdir -p knowledge
echo "# Company Language Guidelines\nAvoid absolute statements..." > knowledge/company_style.md
```

Auto-loaded at startup for all Agents to reference, but no Agent can **write** to it.

### 3. Verify Configuration

```bash
python -c "from agent.core.agent_config import summarize_configs; print(summarize_configs())"
```

You should see the Provider and Key status for all 6 Agents as ✅.

### 4. Run

```bash
sinan
# or
python -m agent
```

Or generate directly via CLI:

```bash
sinan generate ./data/ecommerce_v1 -d ecommerce
# or
python -m agent generate ./data/ecommerce_v1 -d ecommerce
```

### 5. View Artifacts

```bash
ls outputs/
# strategy_<domain>_<folder>_<ts>.md   ← Final strategy
# rubric_<domain>_<folder>_<ts>.json   ← Final Rubric
# debate_<domain>_<folder>_<ts>.json   ← Full debate record
```

### 6. The 6 Agents
```
| Icon | Agent | Responsibility | Independently Configurable Model |
|------|-------|------|----------------|
| 🔍 | `SCOUT` | File scouting, identifying data content | ✅ |
| 🧩 | `RUBRIC_A` | Rubric lead editor (Rubric draft) | ✅ |
| 🧩 | `RUBRIC_B` | Rubric reviewer (Rubric review) | ✅ |
| 🎯 | `STRATEGY_A` | Strategy writer | ✅ |
| 🎯 | `STRATEGY_B` | Strategy challenger | ✅ |
| ⚖️ | `JUDGE` | Judging agent (final ruling + scoring) | ✅ |
```

---

## CLI Commands

```bash
# Interactive chat (recommended for beginners)
sinan

# One-click generation
sinan generate <any-path> -d <domain> [-o output-dir] [-k knowledge-dir]

# Iterative evolution (V1 → V2)
sinan evolve <old-strategy.md> <new-data-path> -d <domain>

# Compare two strategies
sinan compare <strategyA.md> <strategyB.md> -d <domain>

# Environment diagnostics
python -m agent.doctor
```

> If the `sinan` command is unavailable, replace all of them with `python -m agent <subcommand>`.

### Supported Domains

Default domains: `ecommerce` · `github` · `atomgit` · `douyin` · `tiktok` · `finance`

> Users can add relevant data and task goals in the `data/` folder.

> Users can define new domain rules in `configs/rules.yaml`.

### Supported Paths

- ✅ Relative paths (`./data/foo`)
- ✅ Absolute paths (`/home/user/foo`, `D:\data\foo`)
- ✅ Single file (`./goal.md`)
- ✅ Entire folder (any location)
- ✅ Just press Enter → intelligently scan the current directory

---

## Knowledge Base

`knowledge/` is a **read-only shared knowledge base**, referenced by all 6 agents.

### Features
- **Shared Reading**: All Agents read the knowledge base as reference before generation
- **No Writing**: `safe_io.safe_write` enforces blocking at the code layer
- **Physical Hardening**: Recommended to run `chmod -R a-w knowledge/` (Linux/macOS)
- **No Isolation Breach**: The knowledge base is static public reference, completely unrelated to gameplay history
- **Controlled Size**: Truncated at 8k chars per file and 20k chars total, adjustable via `.env`
- **Multi-Format**: md / txt / docx / xlsx / csv / pptx / yaml / json

### Good Things to Include

- Company brand / language guidelines
- Industry standards / policy red lines for the domain
- Internal SOPs / process documents
- Reusable strategy templates
- Historical success cases (after de-identification)
- Financial knowledge

### Things to Avoid

- Plaintext keys / passwords
- Customer privacy data
- Large binaries (images/videos)

---

## Configuration

### Layered Configuration (Recommended)

Each Agent can independently specify its model and key:

```env
SINAN_DEFAULT_PROVIDER=kimi/deepseek/GLM/Qwen

SINAN_RUBRIC_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_RUBRIC_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_JUDGE_PROVIDER=kimi/deepseek/GLM/Qwen
```

### Multi-Key Pool (Rate Limiting / Multi-Account)

```env
# Comma-separated
SINAN_DEEPSEEK_API_KEYS=sk-1,sk-2,sk-3

# Or numbered by line
SINAN_DEEPSEEK_API_KEY_1=sk-1
SINAN_DEEPSEEK_API_KEY_2=sk-2
SINAN_DEEPSEEK_API_KEY_3=sk-3
```

The startup banner shows `✅ x3 rotating`, and all calls are automatically round-robin distributed.

### Key Variable Names for Each Provider
- DeepSeek: `SINAN_DEEPSEEK_API_KEY`
- Kimi / Moonshot: `SINAN_MOONSHOT_API_KEY`
- Qwen / Tongyi Qianwen: `SINAN_DASHSCOPE_API_KEY`
- GLM / Zhipu: `SINAN_ZHIPUAI_API_KEY`
- Ollama local: no key required

### Customizing Hard Rules

Edit `configs/rules.yaml`:

```yaml
global:
  rules:
    - name: "No absolute wording"
      type: "forbidden"
      value: "best|first|absolute"
      score: 20
      description: "Strategies must not contain absolute expressions"

healthcare:
  rules:
    - name: "No prescription drug brand names"
      type: "forbidden"
      value: "aspirin|ibuprofen"
      score: 20
```

Supported rule types: `keyword` / `forbidden` / `regex` / `min_length` / `schema_field`.

---

## Architecture Highlights

### Context Isolation Guarantee
```
| Agent | Can See Rubric Gameplay | Can See Strategy Gameplay | Can See Judge Memory | Can Read Knowledge Base | Can Write Knowledge Base |
|---|:---:|:---:|:---:|:---:|:---:|
| 🔍 ScoutAgent | ✗ | ✗ | ✗ | ✓ | ✗ |
| 🧩 RubricAgentA / B | ✓ (own group only) | ✗ | ✗ | ✓ | ✗ |
| 🎯 StrategyAgentA / B | ✗ (only final_rubric) | ✓ (own group only) | ✗ | ✓ | ✗ |
| ⚖️ JudgeAgent | ✓ | ✓ | ✓ (private) | ✓ | ✗ |
```
### Strict Output Schema Validation
```
| Agent | Output Schema |
|---|---|
| Scout | `ScoutReport` |
| RubricA / B | `RubricSchema` |
| StrategyA / B | `StrategySchema` |
| Judge | `RubricDecision` / `StrategyDecision` |
```
On failure, the error message is automatically fed back to the LLM for self-repair, with up to 2 retries.

### Three-Layer Hard Rule Protection

```
Before generation: rule_constraints injected into Prompt → Agent proactively complies
After generation: RuleEngine.evaluate(final_strategy) → independent re-check and scoring
On write: safe_io.safe_write → blocks knowledge base writes
```

---

## Troubleshooting

### One-Click Diagnostics (Run This First)

```bash
python -m agent.doctor
```

Checks:
- Python version
- Third-party dependencies
- agent package integrity (24 modules)
- Install method (editable / regular / source directory)
- Startup test

And provides **specific fix commands** for any issues.

### Quick Reference for Common Issues

#### `sinan` raises `ModuleNotFoundError: No module named 'agent.core.xxx'`

**Cause**: Incomplete finder mapping for editable install on Python 3.13+.

**Fix (choose one)**:

```bash
# Option A: Switch to a regular install
pip uninstall -y sinan-agent
pip install .

# Option B: Use the alternative startup method directly
python -m agent

# Option C: Create a sinan.cmd wrapper on Windows
# See TROUBLESHOOTING.md
```

#### The `sinan` command is not found

```bash
# Use the alternative startup
python -m agent
```

Or add Python's `Scripts\` to the PATH environment variable.

#### Dependencies fail to install / hang

**Cause**: Python version too new; some packages haven't caught up yet.

**Fix**:
1. Switch to Python 3.12
2. Or use Docker: `docker build -t sinan . && docker run -it sinan`

#### `⚠ The following Agents are missing API Keys`

**Cause**: The key variable name for the corresponding provider in `.env` is misspelled.

**Common pitfalls**:

| What You Wrote | What It Should Be |
|---|---|
| `SINAN_KIMI_API_KEY` | `SINAN_MOONSHOT_API_KEY` |
| `SINAN_QWEN_API_KEY` | `SINAN_DASHSCOPE_API_KEY` |
| `SINAN_GLM_API_KEY` | `SINAN_ZHIPUAI_API_KEY` |

#### `Schema validation failed (after 2 retries)`

**Cause**: Unstable JSON output from the LLM (small model / temperature too high).

**Fix**: Switch key Agents to a stronger model

```env
SINAN_RUBRIC_A_PROVIDER=deepseek
SINAN_JUDGE_PROVIDER=deepseek
```

> For more troubleshooting items, see [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

---

## Artifact Examples

`outputs/strategy_ecommerce_ecommerce_v1_20251104_141500.md`:

```markdown
# Ecommerce Q4 Operations Strategy

> Domain: ecommerce | Judge Score: 85/100 | Hard Rules: 100/100 | Generated at 2025-11-04 14:15:00

## Goals
GMV +30%, new-customer share 40%, repurchase rate 25%, ROI ≥ 3.0

## Product Promotion
...

- **Best-seller A001 Flash Sale** — limited 2-hour window every Wednesday, distributed on-site + private domain
  (Owner: Operations team | Time: Every Wednesday 20:00-22:00 | KPI: single-session GMV ≥ 80k)
```

`outputs/debate_ecommerce_ecommerce_v1_20251104_141500.json`:

```json
{
  "rubric_history": [...],   // Full three-round gameplay of the question-setting team
  "strategy_history": [...], // Full three-round gameplay of the strategy team
  "judge_reasoning": "..."   // Judge ruling explanation
}
```

---

## Documentation Navigation

| Document | Content |
|---|---|
| [`USAGE.md`](USAGE.md) | Full usage manual (10 scenarios + troubleshooting) |
| [`STRUCTURE.md`](STRUCTURE.md) | Project structure, file responsibilities, data flow |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | Troubleshooting manual (look up by error message) |
| [`knowledge/README.md`](knowledge/README.md) | Knowledge base usage instructions |

---

## Development

```bash
# Install development dependencies
pip install -e ".[all]"

# Run tests
pytest

# Lint
ruff check agent/

# Format
ruff format agent/

# Environment diagnostics
python -m agent.doctor
```

---

## License

[Apache-2.0](apach-2.0)

---

## 🙏 Acknowledgements

- [OpenAI Python SDK](https://github.com/openai/openai-python) — Unified LLM access
- [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) — Beautiful CLI
- [Pydantic](https://docs.pydantic.dev/) — Strict Schema validation
- [DeepSeek](https://deepseek.com/) / [Kimi](https://kimi.moonshot.cn/) / [Qwen](https://dashscope.aliyun.com/) / [GLM](https://open.bigmodel.cn/) — Backend model capabilities
- [baize](https://github.com/Xu123-Bob/Baize) — Self-developed agent
- **Special thanks to The Beijing News and Shell Finance. This work won an Alipay rating of 4/26 and an overall ranking of 6/26 at the 2026 AI Youth Hackathon, and was also recommended for the Alipay · Intelligent Agent Surge Competition**