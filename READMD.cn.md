<div align="center">

<img src="image/logopage02.png" alt="白泽 Baize Logo" width="320" />

# 司南 (Sinan-Agent-Team)

**多智能体策略制定系统**

双博弈 · 上下文隔离 · 知识库共享 · JSON Schema 强校验 · 多 Provider 多 Key 轮询

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
## 概述
**本项目为多智能体策略制定与策略效果评价框架**
- 产品通过**Rule\Rubric\LLM-to-judge**，共同构建策略制定和策略评价的体系
- 本项目共有**6个agent**，2个出题agent，2个判定agent，1个侦察agent，1个判断agent
- Rule层，包括业务内容的约束，也包括对**agent输出结构**的约束（确保agent输出正常）
- Rubric通过2个**出题agent博弈**，各自阐述观点，最终由**判定agent完成最终确认**
- 策略制定与评价，由2个**策略制定agent讨论**，最终也由**判定agent完成最终确认**
- 扫描和获取数据与专业知识，由**1个侦察agent**来完成，主要扫描`knowledge/`、`data/`、`output/`
- 生成产物包括：**策略方案、Rubric题表和讨论文稿**，最终保存在`knowledge/`，**迭代新策略时侦察agent会自动扫描**
- 本项目是本人参与2026年北京AI青年黑客松的参赛作品，获得支付宝评分第4名，推荐至支付宝·智能体涌动大赛

### 多智能体结构图

<div align="center">
多智能体结构图
</div>

<p align="center">
  <img src="image/infra.png" alt="多智能体结构图" width="800" />
</p>

### 产品介绍
静态网址：https://sinan-website.pages.dev/

---

## 核心特性

- **6-Agent 架构**：侦察 / 出题组（A+B） / 策略组（A+B） / 判断，各司其职 |
- **上下文严格隔离**：出题组 ↔ 策略组完全隔离；Judge 私有记忆永不外泄 |
- **知识库只读共享**：`knowledge/` 对所有 Agent 可读，但任何 Agent 不可写 |
- **双博弈三轮**：Rubric 组 A ⇄ B、策略组 A ⇄ B，各自三轮博弈 |
- **Judge 独立裁定**：唯一能看到全部上下文的智能体，只输出决策产物 |
- **JSON Schema 强校验**：每个 Agent 输出必过 Pydantic；失败自动重试 2 次 |
- **硬规则前后双校验**：生成前注入 Prompt，生成后独立复核；用户可自定义底线 |
- **多 Provider 多 Key**：同 Provider 支持多 Key 轮询；每个 Agent 可独立指定模型 |
- **任意路径输入**：相对 / 绝对 / Windows / Linux / 单文件 / 文件夹；回车自动扫描 |
- **任意业务领域**：内置电商 / GitHub / AtomGit / 抖音 / TikTok；可自定义扩展 |
- **全中文 CLI**：Typer + Rich 渲染，分色面板、实时打印辩论过程 |

---
## 登录界面
<div align="center">
登录界面
</div>

<p align="center">
  <img src="image/sinancli-01.jpg" alt="登录界面" width="800" />
</p>

## 环境要求（先读这里）
```
| 项 | 推荐 | 说明 |
|---|---|---|
| **Python** | **3.10 / 3.11 / 3.12** | ⭐ 强烈推荐 |
| Python 3.13 | 可用 | 部分依赖可能有小问题 |
| Python 3.14+ | ❌ **不推荐** | editable install 有已知兼容问题 |
| 操作系统 | Windows / macOS / Linux | 全平台支持 |
| 网络 | 需要访问 LLM API | DeepSeek / Kimi / Qwen 等 |
```
> **遇到任何安装或启动问题，先运行诊断**：
> ```bash
> python -m agent.doctor
> ```
> 会一次性检查 Python 版本、依赖、agent 包完整性、安装方式、启动测试，并给出修复建议。

---

## 安装（3 种方式任选）

### 方式 1：一键脚本（推荐新手）

```bash
# Windows
scripts\install.bat

# Linux / macOS
bash scripts/install.sh
```

脚本会自动检查 Python、创建 venv、安装依赖、跑一遍 doctor 验证。

### 方式 2：手动安装（熟悉 Python 的开发者）

```bash
# 强烈建议使用虚拟环境
python -m venv .venv

# 激活（三选一）
source .venv/bin/activate         # Linux / macOS
.venv\Scripts\activate            # Windows CMD
.venv\Scripts\Activate.ps1        # Windows PowerShell

# 安装
pip install -e .
```

> **Python 3.13+ 用户注意**：如果 `pip install -e .` 后 `sinan` 命令报 `ModuleNotFoundError: agent.core.xxx`，请改用：
> ```bash
> pip install .
> ```
> 或直接用 `python -m agent` 启动（见下文「启动」章节）。

### 方式 3：Docker（不想折腾环境）

```bash
docker build -t sinan .

docker run -it --rm \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/knowledge:/app/knowledge \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  sinan
```

彻底绕过 Python 版本、依赖编译、系统差异的所有问题。

---

## 启动（3 种等价方式）

```bash
sinan                  # pip 装的命令（最方便）
python -m agent        # 备选（sinan 命令失效时用这个）
python -m agent.cli    # 再备选
```

**三条命令功能完全等价**，任一条能用就行。

如果 `sinan` 报错，直接改用 `python -m agent` 即可，**不需要排查问题**。

---

## 快速开始

### 1. 配置后端

```bash
cp .env.example .env
```

编辑 `.env`，填入**至少一个** API Key（最简配置）：

```env
SINAN_DEEPSEEK_API_KEY=sk-你的密钥
SINAN_DEFAULT_PROVIDER=deepseek
```

其他字段全删掉，只要这两行。

> 多模型、多 Key 池、按 Agent 分配的进阶配置见 [`USAGE.md`](USAGE.md)。

### 2. 准备知识库（可选）

```bash
mkdir -p knowledge
echo "# 公司用语规范\n避免绝对化表述..." > knowledge/company_style.md
```

启动时会自动加载，供所有 Agent 参考，但任何 Agent 都**无法写入**。

### 3. 验证配置

```bash
python -c "from agent.core.agent_config import summarize_configs; print(summarize_configs())"
```

应看到 6 个 Agent 的 Provider 和 Key 状态都是 ✅。

### 4. 运行

```bash
sinan
# 或
python -m agent
```

或直接命令行生成：

```bash
sinan generate ./data/ecommerce_v1 -d ecommerce
# 或
python -m agent generate ./data/ecommerce_v1 -d ecommerce
```

### 5. 查看产物

```bash
ls outputs/
# strategy_<domain>_<folder>_<ts>.md   ← 最终策略
# rubric_<domain>_<folder>_<ts>.json   ← 最终 Rubric
# debate_<domain>_<folder>_<ts>.json   ← 完整辩论记录
```

### 6.6 个智能体
```
| 图标 | Agent | 职责 | 可否独立配置模型 |
|------|-------|------|----------------|
| 🔍 | `SCOUT` | 文件侦察，识别数据内容 | ✅ |
| 🧩 | `RUBRIC_A` | 出题主编（Rubric 初稿） | ✅ |
| 🧩 | `RUBRIC_B` | 出题审查员（Rubric 复核） | ✅ |
| 🎯 | `STRATEGY_A` | 策略撰写者 | ✅ |
| 🎯 | `STRATEGY_B` | 策略反驳者 | ✅ |
| ⚖️ | `JUDGE` | 判断智能体（最终裁定 + 评分） | ✅ |
```

---

## CLI 命令

```bash
# 交互式 chat（推荐新手）
sinan

# 一键生成
sinan generate <任意路径> -d <领域> [-o 输出目录] [-k 知识库目录]

# 迭代进化（V1 → V2）
sinan evolve <旧策略.md> <新数据路径> -d <领域>

# 对比两份策略
sinan compare <策略A.md> <策略B.md> -d <领域>

# 环境诊断
python -m agent.doctor
```

> `sinan` 命令不可用时，全部替换为 `python -m agent <子命令>` 即可。

### 支持领域

系统默认领域：`ecommerce` · `github` · `atomgit` · `douyin` · `tiktok` · `finance`

> 用户可在 `data/`文件夹中添加相关数据与任务目标。

> 用户可在 `configs/rules.yaml` 中自定义新领域规则。

### 支持路径

- ✅ 相对路径（`./data/foo`）
- ✅ 绝对路径（`/home/user/foo`、`D:\data\foo`）
- ✅ 单个文件（`./goal.md`）
- ✅ 整个文件夹（任意位置）
- ✅ 直接回车 → 智能扫描当前目录

---

## 知识库

`knowledge/` 是一个**只读共享知识库**，供所有 6 个智能体参考。

### 特性
- **共享读取**：所有 Agent 在生成前会读取知识库内容作为参考
- **不可写入**：代码层 `safe_io.safe_write` 强制拦截 |
- **物理加固**：建议执行 `chmod -R a-w knowledge/`（Linux/macOS） |
- **不破坏隔离**：知识库是静态公共参考，与博弈 history 完全无关 |
- **体量可控**：单文件 8k 字符、总 20k 字符截断，可通过 `.env` 调节 |
- **多格式**：md / txt / docx / xlsx / csv / pptx / yaml / json |

### 适合放什么

- 公司品牌 / 用语规范
- 领域行业标准 / 政策红线
- 内部 SOP / 流程文档
- 可复用的策略模板
- 历史优秀案例（脱敏后）
- 金融知识

### 不适合放什么

- 明文密钥 / 密码
- 客户隐私数据
- 大型二进制（图片/视频）

---

## 配置

### 分层配置（推荐）

每个 Agent 都能独立指定模型和 key：

```env
SINAN_DEFAULT_PROVIDER=kimi/deepseek/GLM/Qwen

SINAN_RUBRIC_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_RUBRIC_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_JUDGE_PROVIDER=kimi/deepseek/GLM/Qwen
```

### 多 Key 池（限流 / 多账号）

```env
# 逗号分隔
SINAN_DEEPSEEK_API_KEYS=sk-1,sk-2,sk-3

# 或分行编号
SINAN_DEEPSEEK_API_KEY_1=sk-1
SINAN_DEEPSEEK_API_KEY_2=sk-2
SINAN_DEEPSEEK_API_KEY_3=sk-3
```

启动横幅会显示 `✅ x3 轮询`，所有调用自动 round-robin 分摊。

### 各 Provider 的 key 变量名
- DeepSeek：`SINAN_DEEPSEEK_API_KEY`
- Kimi / Moonshot：`SINAN_MOONSHOT_API_KEY`
- Qwen / 通义千问：`SINAN_DASHSCOPE_API_KEY`
- GLM / 智谱：`SINAN_ZHIPUAI_API_KEY`
- Ollama 本地：无需 key

### 硬规则自定义

编辑 `configs/rules.yaml`：

```yaml
global:
  rules:
    - name: "禁止绝对化用语"
      type: "forbidden"
      value: "最好|第一|绝对"
      score: 20
      description: "策略中不得出现绝对化表述"

healthcare:
  rules:
    - name: "不得含处方药商品名"
      type: "forbidden"
      value: "阿司匹林|布洛芬"
      score: 20
```

支持规则类型：`keyword` / `forbidden` / `regex` / `min_length` / `schema_field`。

---

## 架构要点

### 上下文隔离保证
```
| Agent | 可看 Rubric 博弈 | 可看 Strategy 博弈 | 可看 Judge 记忆 | 可看知识库 | 可写知识库 |
|---|:---:|:---:|:---:|:---:|:---:|
| 🔍 ScoutAgent | ✗ | ✗ | ✗ | ✓ | ✗ |
| 🧩 RubricAgentA / B | ✓（仅自己组） | ✗ | ✗ | ✓ | ✗ |
| 🎯 StrategyAgentA / B | ✗（只拿 final_rubric） | ✓（仅自己组） | ✗ | ✓ | ✗ |
| ⚖️ JudgeAgent | ✓ | ✓ | ✓（自身私有） | ✓ | ✗ |
```
### 输出 Schema 强校验
```
| Agent | 输出 Schema |
|---|---|
| Scout | `ScoutReport` |
| RubricA / B | `RubricSchema` |
| StrategyA / B | `StrategySchema` |
| Judge | `RubricDecision` / `StrategyDecision` |
```
失败时自动把错误信息回灌给 LLM 让其自修复，最多重试 2 次。

### 硬规则三层防护

```
生成前：rule_constraints 注入 Prompt → Agent 主动遵守
生成后：RuleEngine.evaluate(final_strategy) → 独立复核打分
写入时：safe_io.safe_write → 拦截知识库写入
```

---

## 排错

### 一键诊断（先跑这个）

```bash
python -m agent.doctor
```

会检查：
- Python 版本
- 第三方依赖
- agent 包完整性（24 个模块）
- 安装方式（editable / 普通 / 源码目录）
- 启动测试

并针对问题给出**具体的修复命令**。

### 常见问题速查

#### `sinan` 报 `ModuleNotFoundError: No module named 'agent.core.xxx'`

**原因**：Python 3.13+ 上 editable install 的 finder 映射不完整。

**修复（三选一）**：

```bash
# 方案 A：改用普通安装
pip uninstall -y sinan-agent
pip install .

# 方案 B：直接用备选启动方式
python -m agent

# 方案 C：Windows 上建 sinan.cmd 包装
# 见 TROUBLESHOOTING.md
```

#### `sinan` 命令找不到

```bash
# 用备选启动
python -m agent
```

或把 Python 的 `Scripts\` 加到 PATH 环境变量。

#### 依赖装不上 / 卡住

**原因**：Python 版本太新，某些包还没适配。

**修复**：
1. 切换到 Python 3.12
2. 或用 Docker：`docker build -t sinan . && docker run -it sinan`

#### `⚠ 以下 Agent 缺 API Key`

**原因**：`.env` 中对应 provider 的 key 变量名写错了。

**常见坑**：

| 你写的 | 应该是 |
|---|---|
| `SINAN_KIMI_API_KEY` | `SINAN_MOONSHOT_API_KEY` |
| `SINAN_QWEN_API_KEY` | `SINAN_DASHSCOPE_API_KEY` |
| `SINAN_GLM_API_KEY` | `SINAN_ZHIPUAI_API_KEY` |

#### `Schema 校验失败（重试 2 次后）`

**原因**：LLM 输出 JSON 格式不稳定（小模型 / 温度过高）。

**修复**：给关键 Agent 换更强的模型

```env
SINAN_RUBRIC_A_PROVIDER=deepseek
SINAN_JUDGE_PROVIDER=deepseek
```

> 更多排错项见 [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)。

---

## 产物示例

`outputs/strategy_ecommerce_ecommerce_v1_20251104_141500.md`：

```markdown
# 电商 Q4 运营策略

> 领域: ecommerce | Judge 评分: 85/100 | 硬规则: 100/100 | 生成于 2025-11-04 14:15:00

## 目标
GMV 提升 30%，新客占比 40%，复购率 25%，ROI ≥ 3.0

## 商品促销
...

- **爆款 A001 秒杀** — 每周三限时 2 小时，投放站内+私域
  (负责人: 运营组 | 时间: 每周三 20:00-22:00 | KPI: 单场 GMV ≥ 8 万)
```

`outputs/debate_ecommerce_ecommerce_v1_20251104_141500.json`：

```json
{
  "rubric_history": [...],   // 出题组三轮博弈全过程
  "strategy_history": [...], // 策略组三轮博弈全过程
  "judge_reasoning": "..."   // Judge 裁定说明
}
```

---

## 文档导航

| 文档 | 内容 |
|---|---|
| [`USAGE.md`](USAGE.md) | 完整使用手册（10 个场景 + 排错） |
| [`STRUCTURE.md`](STRUCTURE.md) | 项目结构、文件职责、数据流 |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | 排错手册（按错误信息查找） |
| [`knowledge/README.md`](knowledge/README.md) | 知识库使用说明 |

---

## 开发

```bash
# 安装开发依赖
pip install -e ".[all]"

# 运行测试
pytest

# Lint
ruff check agent/

# 格式化
ruff format agent/

# 环境诊断
python -m agent.doctor
```

---

## License

[Apache-2.0](apach-2.0)

---

## 🙏 致谢

- [OpenAI Python SDK](https://github.com/openai/openai-python) — 统一 LLM 接入
- [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) — 美观的 CLI
- [Pydantic](https://docs.pydantic.dev/) — Schema 强校验
- [DeepSeek](https://deepseek.com/) / [Kimi](https://kimi.moonshot.cn/) / [Qwen](https://dashscope.aliyun.com/) / [GLM](https://open.bigmodel.cn/) — 提供后端模型能力
- [baize](https://github.com/Xu123-Bob/Baize) — 本人自研agent
- **还需要感谢新京报和贝壳财经，本作品在举办的2026年AI青年黑客松比赛中获得支付宝评分4/26，大赛6/26的成绩，也被推荐到支付宝·智能体涌动大赛**