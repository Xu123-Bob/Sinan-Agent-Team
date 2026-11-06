# 司南 v3.2 使用手册

> **版本**：v3.2.0  
> **适用**：6-Agent 多智能体策略制定系统  
> **最后更新**：2025-11-04  
> **配套文档**：[README.md](README.md) · [STRUCTURE.md](STRUCTURE.md) · [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📑 目录

- [一、安装与环境](#一安装与环境)
- [二、启动方式](#二启动方式)
- [三、配置后端](#三配置后端)
- [四、配置知识库](#四配置知识库)
- [五、准备测试数据](#五准备测试数据)
- [六、运行范例（10 个场景）](#六运行范例10-个场景)
- [七、查看产物](#七查看产物)
- [八、排错速查](#八排错速查)
- [九、一页速查](#九一页速查)

---

## 一、安装与环境

### 1.1 环境要求

| 项 | 推荐 | 说明 |
|---|---|---|
| **Python** | **3.10 / 3.11 / 3.12** | ⭐ 强烈推荐 |
| Python 3.13 | 可用 | 部分依赖可能小问题 |
| Python 3.14+ | ❌ **不推荐** | editable install 有已知兼容问题 |
| 系统 | Windows / macOS / Linux | 全平台 |
| 网络 | 可访问 LLM API | 需要 |

### 1.2 检查 Python 版本

```bash
python --version
# 或
python3 --version
```

**如果版本 ≥ 3.14，请先装一个 Python 3.12**（见 1.5）。

### 1.3 一键安装（推荐）

```bash
# Windows
scripts\install.bat

# Linux / macOS
bash scripts/install.sh
```

脚本会：
1. 检查 Python 版本
2. 询问是否创建 venv
3. 安装依赖
4. 自动跑一遍 `python -m agent.doctor` 验证

### 1.4 手动安装

```bash
# 1. 创建虚拟环境（强烈建议）
python -m venv .venv

# 2. 激活
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows CMD
.venv\Scripts\Activate.ps1         # Windows PowerShell

# 3. 安装
pip install -e .

# 4. 验证
python -m agent.doctor
```

**如果 `pip install -e .` 在 Python 3.13+ 上有问题**，改用：

```bash
pip install .
```

或直接跳过 pip，用 `python -m agent` 启动。

### 1.5 装 Python 3.12（如果当前版本太新）

**Windows**：
1. 访问 https://www.python.org/downloads/release/python-3120/
2. 下载 Windows installer
3. 安装时勾选 "Add Python 3.12 to PATH"
4. 新开 CMD 验证：`python --version`

**macOS**：

```bash
brew install python@3.12
# 用 python3.12 代替 python
```

**Linux**：

```bash
# Ubuntu
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv

# 或 pyenv
pyenv install 3.12.0
```

### 1.6 Docker 安装（不想折腾环境）

```bash
docker build -t sinan .
docker run -it --rm \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/knowledge:/app/knowledge \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  sinan
```

---

## 二、启动方式

### 2.1 三种等价启动命令

```bash
sinan                  # 首选（pip 装的命令）
python -m agent        # 备选（sinan 报错时用这个）
python -m agent.cli    # 再备选
```

**功能完全一致**，任一条能用即可。

### 2.2 环境诊断

启动前或遇到问题时：

```bash
python -m agent.doctor
```

输出示例：

```
╔══════════════════════════════════════════════════╗
║          司南环境诊断工具 (Sinan Doctor)          ║
╚══════════════════════════════════════════════════╝

============================================================
1. Python 环境
============================================================
  版本: 3.12.0
  可执行: D:\Python312\python.exe
  平台: Windows 10
  ✅ 版本合格

============================================================
2. 第三方依赖
============================================================
  ✅ openai          1.35.0
  ✅ httpx           0.27.0
  ✅ python-dotenv   1.0.1
  ...

============================================================
3. agent 包完整性
============================================================
  ✅ agent
  ✅ agent.cli
  ...（24 个模块）

============================================================
4. 安装方式诊断
============================================================
  安装方式: 普通安装（agent 包在 site-packages 内）
  ✅ 推荐方式，稳定

============================================================
5. 启动方式测试
============================================================
  ✅ 加载 agent.cli:app 成功

============================================================
诊断结论
============================================================
🎉 一切正常，可以启动：
   sinan
   或
   python -m agent
```

### 2.3 进入交互式 chat

```bash
sinan
# 或
python -m agent
```

应看到：

```
███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗
██╔════╝██║████╗  ██║██╔══██╗████╗  ██║
███████╗██║██╔██╗ ██║███████║██╔██╗ ██║
╚════██║██║██║╚██╗██║██╔══██║██║╚██╗██║
███████║██║██║ ╚████║██║  ██║██║ ╚████║
╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝

司 南 · 多 智 能 体 策 略 制 定 系 统
Sinan Agent Engine v3.2.0  |  Status: ONLINE

┌──────────────┬──────────┬─────────────┐
│ 智能体        │ Provider │ API Key     │
├──────────────┼──────────┼─────────────┤
│ 🔍 文件侦察   │ deepseek │ ✅ x1        │
│ 🧩 出题主编   │ deepseek │ ✅ x1        │
│ 🧩 出题审查   │ kimi     │ ✅ x1        │
│ 🎯 策略撰写   │ deepseek │ ✅ x1        │
│ 🎯 策略反驳   │ kimi     │ ✅ x1        │
│ ⚖️ 判断智能体 │ kimi     │ ✅ x1        │
└──────────────┴──────────┴─────────────┘

📚 知识库: ./knowledge · 0 个文件

你 ❯
```

看到 `你 ❯` 就说明**配置成功**。

---

## 三、配置后端

### 3.1 从模板复制

```bash
cp .env.example .env
# Windows
copy .env.example .env
```

### 3.2 三种配置方案（按需选择）

#### 🟢 方案 A：极简（一个 key，全用 deepseek）

**适合**：第一次跑、个人测试、预算敏感

```env
SINAN_DEEPSEEK_API_KEY=sk-你的deepseek密钥
SINAN_DEFAULT_PROVIDER=deepseek
```

> 6 个 Agent 全部走 deepseek，共用一个 key。

#### 🟡 方案 B：双模型（推荐）

**适合**：真正体验"博弈"效果，两个模型互补

```env
SINAN_DEEPSEEK_API_KEY=sk-你的deepseek密钥
SINAN_MOONSHOT_API_KEY=sk-你的kimi密钥

SINAN_DEFAULT_PROVIDER=deepseek

SINAN_SCOUT_PROVIDER=deepseek

SINAN_RUBRIC_A_PROVIDER=deepseek
SINAN_RUBRIC_B_PROVIDER=kimi

SINAN_STRATEGY_A_PROVIDER=deepseek
SINAN_STRATEGY_B_PROVIDER=kimi

SINAN_JUDGE_PROVIDER=kimi
```

#### 🔴 方案 C：多 key 池（企业级）

**适合**：单 key 有 QPS 限制，或多个团队账号

```env
# 每个 provider 3 个 key 轮询
SINAN_DEEPSEEK_API_KEYS=sk-ds-1,sk-ds-2,sk-ds-3
SINAN_MOONSHOT_API_KEYS=sk-kimi-1,sk-kimi-2

SINAN_DEFAULT_PROVIDER=deepseek

SINAN_RUBRIC_A_PROVIDER=deepseek
SINAN_RUBRIC_B_PROVIDER=kimi
SINAN_STRATEGY_A_PROVIDER=deepseek
SINAN_STRATEGY_B_PROVIDER=kimi
SINAN_JUDGE_PROVIDER=kimi
```

> 也可以用 `SINAN_DEEPSEEK_API_KEY_1=...` `_2=...` `_3=...` 分行写。

### 3.3 各 Provider 的 key 变量名

| Provider | `.env` 变量 | 申请地址 |
|---|---|---|
| DeepSeek | `SINAN_DEEPSEEK_API_KEY` | https://platform.deepseek.com |
| Kimi / Moonshot | `SINAN_MOONSHOT_API_KEY` | https://platform.moonshot.cn |
| Qwen / 通义千问 | `SINAN_DASHSCOPE_API_KEY` | https://dashscope.console.aliyun.com |
| GLM / 智谱 | `SINAN_ZHIPUAI_API_KEY` | https://open.bigmodel.cn |
| Ollama 本地 | 无需 key | 本地 `ollama serve` |

### 3.4 可选：输出目录

```env
SINAN_OUTPUT_DIR=./outputs
# 或
SINAN_OUTPUT_DIR=D:/strategy_out
```

### 3.5 验证配置

```bash
python -c "from agent.core.agent_config import summarize_configs; print(summarize_configs())"
```

预期：

```
  SCOUT        → deepseek   ✅ 1 个 key
  RUBRIC_A     → deepseek   ✅ 1 个 key
  RUBRIC_B     → kimi       ✅ 1 个 key
  STRATEGY_A   → deepseek   ✅ 1 个 key
  STRATEGY_B   → kimi       ✅ 1 个 key
  JUDGE        → kimi       ✅ 1 个 key
```

若出现 `⚠ 无 key`，检查：
1. `.env` 是否在项目根目录
2. key 变量名是否拼对（特别是 `MOONSHOT` 不是 `KIMI`）
3. 等号两边**不要有空格**

---

## 四、配置知识库

### 4.1 什么是知识库

`knowledge/` 目录存放**组织公共知识**，供 6 个智能体共享阅读。它是**只读**的——任何 Agent 都无法写入、修改、删除。

### 4.2 快速开始

```bash
mkdir -p knowledge

cat > knowledge/company_style.md <<'EOF'
# 公司品牌用语规范

- 禁止使用"最好"、"第一"、"绝对"等绝对化表述
- 品牌名统一写作"司南"（不带引号）
- 客服称呼统一为"小南"
EOF
```

### 4.3 推荐组织结构

```
knowledge/
├── company/                # 公司级通用
│   ├── 业务分类标准.md
│   └── 品牌用语规范.md
├── domain/                 # 领域知识
│   ├── ecommerce/
│   │   └── 电商行业规范.md
│   └── github/
│       └── 开源治理准则.md
└── templates/              # 策略模板
    └── Q4营销方案模板.md
```

> 结构自由，代码自动递归扫描。

### 4.4 `.env` 配置

```env
SINAN_KNOWLEDGE_DIR=./knowledge
SINAN_KNOWLEDGE_MAX_CHARS=20000
```

### 4.5 物理加固（强烈推荐）

**Linux / macOS**：

```bash
chmod -R a-w knowledge/
```

**Windows**：右键知识库目录 → 属性 → 安全 → 去掉写入权限。

启动时会检测并提示：

```
⚠️  知识库目录当前可写，建议执行：chmod -R a-w knowledge/
```

### 4.6 体量控制

| 项 | 默认上限 | 说明 |
|---|---|---|
| 单文件 | 8000 字符 | 超出自动截断 |
| 总量 | 20000 字符（≈10k token） | 超出按优先级截断 |

可通过 `.env` 的 `SINAN_KNOWLEDGE_MAX_CHARS` 调整。

### 4.7 支持的文件格式

| 类型 | 后缀 | 处理方式 |
|---|---|---|
| 文档 | `.md` `.txt` `.docx` | 直接读取 / 提取文本 |
| 表格 | `.csv` `.xlsx` `.xls` `.tsv` | 解析为 Markdown 表格（前 50 行） |
| 结构化 | `.yaml` `.yml` `.json` `.toml` | 原样读取 |
| 其他 | 图片/视频/压缩包 | 自动忽略 |

### 4.8 验证写入保护

```bash
python -c "
from agent.core.safe_io import safe_write
try:
    safe_write('./knowledge/test.md', 'x')
    print('❌ 应该被拦截！')
except PermissionError:
    print('✅ 写入知识库被拦截')
"
```

---

## 五、准备测试数据

### 5.1 方式一：用内置示例

```bash
ls data/
# ecommerce_v1/  ecommerce_v2/  github_v1/  tiktok_v1/
```

### 5.2 方式二：手动造一个最小数据集

**Linux / macOS**：

```bash
mkdir -p mydata/ecommerce_test

cat > mydata/ecommerce_test/goal.md <<'EOF'
# 2025 Q4 电商运营目标

- GMV 提升 30%
- 新客占比 40%
- 复购率提升到 25%
- 控制广告 ROI ≥ 3.0
EOF

cat > mydata/ecommerce_test/metrics.csv <<'EOF'
sku,price,sales_30d,inventory,return_rate
A001,99,1200,300,2.1%
A002,199,800,500,1.5%
A003,49,3000,800,3.8%
EOF
```

**Windows CMD**：

```cmd
mkdir mydata\ecommerce_test

(
echo # 2025 Q4 电商运营目标
echo.
echo - GMV 提升 30%%
echo - 新客占比 40%%
echo - 复购率提升到 25%%
echo - 控制广告 ROI ≥ 3.0
) > mydata\ecommerce_test\goal.md

(
echo sku,price,sales_30d,inventory,return_rate
echo A001,99,1200,300,2.1%%
echo A002,199,800,500,1.5%%
echo A003,49,3000,800,3.8%%
) > mydata\ecommerce_test\metrics.csv
```

> **注意**：Windows CMD 里 `%` 需要写 `%%` 转义。

> 任何位置都行（`/tmp/`、`~/Downloads/`、`D:\data\`）。

---

## 六、运行范例（10 个场景）

### 场景 1：最简单——chat 里说一句话

```bash
sinan
```

```
你 ❯ 帮我制定 mydata/ecommerce_test 的电商策略
```

内部流程（全程实时打印）：

```
🔍 正在扫描文件夹并侦察内容: mydata/ecommerce_test

╔════════════════════════════════════════╗
║  🔍 文件侦察智能体 · 预审报告            ║
╚════════════════════════════════════════╝
📋 业务概览
  该文件夹是一份电商初始运营数据。goal.md 描述了
  2025 Q4 的 GMV、新客、复购等目标；metrics.csv
  记录了 3 个 SKU 的价格、销量、库存、退货率。
  可用于制定商品促销与库存清理策略。
  置信度: 88% | 文件数: 2 | 总大小: 0.02 MB

🎯 初步判断
  领域: ecommerce
  建议策略: 商品促销与库存清理策略

🗂 关键目标文件
  • goal.md
  • metrics.csv

请选择下一步
  [1] 确认 — 用该文件夹全部内容制定策略（推荐）
  [2] 我只用其中某些文件
  [3] 我手动描述策略目标
  [4] 换一个文件夹重新扫描
输入编号 [1]: 1

🧩 出题组三轮博弈
  ⏳ 模型一 · 初始出题 正在生成...
  ...（实时展示每一轮 Rubric 演进）

⚖️ 判断智能体裁定最终题目
  ...

🎯 策略组三轮博弈
  ...

⚖️ 判断智能体裁定最终策略
  ...

∑ Judge 评分明细
┌──────────────┬───────┬──────────┐
│ 维度          │ 得分   │ 评价      │
├──────────────┼───────┼──────────┤
│ GMV 提升路径  │ 26/30 │ 覆盖完整  │
│ 新客获取      │ 18/25 │ 略欠具体  │
│ 复购率        │ 19/20 │ 好        │
│ ROI 控制      │ 22/25 │ 合理      │
└──────────────┴───────┴──────────┘

⚖ 硬性规则校验：100/100 (全部通过)

★ Judge 最终评分：85/100

策略已保存: outputs/strategy_ecommerce_ecommerce_test_20251104_141500.md
Rubric 已保存: outputs/rubric_ecommerce_ecommerce_test_20251104_141500.json
辩论记录: outputs/debate_ecommerce_ecommerce_test_20251104_141500.json
```

### 场景 2：命令行一键生成（不进 chat）

```bash
sinan generate mydata/ecommerce_test -d ecommerce
# sinan 报错时：
python -m agent generate mydata/ecommerce_test -d ecommerce
```

指定输出目录 + 知识库：

```bash
sinan generate mydata/ecommerce_test \
  -d ecommerce \
  -o /mnt/backup/strategy_out \
  -k ./knowledge
```

### 场景 3：单文件作为输入

只给一个 `goal.md`：

```bash
sinan generate mydata/ecommerce_test/goal.md -d ecommerce
```

> 自动取父目录并只解析该文件，`metrics.csv` 不会被读入。

### 场景 4：回车智能发现（不给路径）

```bash
sinan
你 ❯ 博弈
🤔 请提供数据所在路径（可以是任意位置的文件夹）

请提供包含目标和数据的文件夹路径
（支持任意路径：相对/绝对/Windows/Linux；直接回车可扫描当前目录）
路径 ❯ [直接回车]

正在扫描当前目录下的候选数据文件夹...
  1. mydata/ecommerce_test (2 文件) 含目标 含表格
  2. data/ecommerce_v1     (5 文件) 含目标 含表格
  3. data/douyin_2024      (3 文件) 含表格
输入编号或直接填写路径 [1]: 1
```

### 场景 5：迭代进化（V1 → V2）

```bash
sinan evolve \
  outputs/strategy_ecommerce_ecommerce_test_20251104_141500.md \
  mydata/ecommerce_v2 \
  -d ecommerce
```

`mydata/ecommerce_v2` 里放新一期的 `goal.md` 和 `metrics.csv`。

流程：

- 读旧策略
- 扫描新数据
- Scout 预审新数据
- 全 6-Agent 流程重新博弈
- 输出 `v2_strategy_*.md`

### 场景 6：对比两个方案

```bash
sinan compare \
  outputs/strategy_ecommerce_ecommerce_test_20251104_141500.md \
  outputs/v2_strategy_ecommerce_ecommerce_test_20251105_090000.md \
  -d ecommerce
```

输出：

```
⊗ 司南策略对决启动
领域: ecommerce
方案 A: outputs/strategy_ecommerce_..._141500.md
方案 B: outputs/v2_strategy_ecommerce_..._090000.md

⏳ 判断智能体评估中...

★ 胜出: B

裁判理由:
方案 B 在数据量化、动作可执行性、ROI 控制上都优于方案 A。
方案 A 缺乏明确的库存清理时间节点，B 方案还补充了私域复购机制……
```

### 场景 7：手工描述目标（文件不用看）

```bash
sinan
你 ❯ 博弈
请提供包含目标和数据的文件夹路径
路径 ❯ mydata/ecommerce_test

... Scout 扫描后 ...

请选择下一步
输入编号 [1]: 3

请描述要制定什么策略、基于什么信息。逐行输入，单行 END 结束。
> 我要为这个店铺制定双十一冲量策略
> 重点：主推爆款 + 私域复购 + 库存清理
> 预算：广告 20 万，ROI 要求 4.0
> END

╭──────── 将基于您的口述制定策略 ────────╮
│ 我要为这个店铺制定双十一冲量策略       │
│ 重点：主推爆款 + 私域复购 + 库存清理   │
│ 预算：广告 20 万，ROI 要求 4.0         │
╰────────────────────────────────────────╯
```

> 用户口述的优先级**高于**文件内容，LLM 会严格遵循。

### 场景 8：切换某个 Agent 的模型

不改 `.env`，只让 Judge 用 deepseek：

```bash
sinan chat --judge-model deepseek --judge-key sk-另一把
```

多个 Agent 一起覆盖：

```bash
sinan generate mydata/ecommerce_test \
  -d ecommerce \
  --model-a deepseek \
  --model-b kimi \
  --judge-model kimi
```

### 场景 9：多 key 池轮询验证

`.env`：

```env
SINAN_DEEPSEEK_API_KEYS=sk-ds-1,sk-ds-2,sk-ds-3
SINAN_DEFAULT_PROVIDER=deepseek
```

启动后横幅显示：

```
│ 🔍 文件侦察   │ deepseek │ ✅ x3 轮询 │
│ 🧩 出题主编   │ deepseek │ ✅ x3 轮询 │
│ 🎯 策略撰写   │ deepseek │ ✅ x3 轮询 │
```

一次生成流程会发起 10+ 次 LLM 调用，**自动轮流使用 3 把 key**，单 key 的 QPS 压力降到 1/3。

### 场景 10：在脚本里调用（非交互）

```bash
#!/bin/bash
# batch_run.sh —— 批量给多个数据文件夹生成策略

set -e

DOMAIN="ecommerce"
DATA_ROOT="./data"

for folder in "$DATA_ROOT"/*/; do
    folder_name=$(basename "$folder")
    echo "=========================================="
    echo "处理: $folder_name"
    echo "=========================================="

    python -m agent generate "$folder" \
        -d "$DOMAIN" \
        -o "./batch_outputs" \
        || echo "⚠ $folder_name 失败，继续下一个"

    echo
done

echo "全部完成，产物在 ./batch_outputs"
```

---

## 七、查看产物

### 7.1 输出三件套

每次运行后 `outputs/` 会生成：

```bash
ls outputs/
```

```
strategy_ecommerce_ecommerce_test_20251104_141500.md   ← 最终策略
rubric_ecommerce_ecommerce_test_20251104_141500.json   ← 最终 Rubric
debate_ecommerce_ecommerce_test_20251104_141500.json   ← 完整辩论记录
```

### 7.2 策略文件（Markdown）

```bash
cat outputs/strategy_ecommerce_*.md
```

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

### 7.3 辩论记录（JSON）

```bash
# 想看两个模型到底是怎么博弈的
python -c "
import json
d = json.load(open('outputs/debate_ecommerce_20251104_141500.json'))
print(len(d['rubric_history']), '条出题博弈')
print(len(d['strategy_history']), '条策略博弈')
"
```

### 7.4 文件命名规则

```
{prefix}{type}_{domain}_{folder_name}_{timestamp}.{ext}

prefix:  ""  → 初始版本
         "v2_" → evolve 生成的 V2
type:    strategy / rubric / debate
domain:  ecommerce / github / ...
folder:  数据文件夹名
timestamp: YYYYMMDD_HHMMSS
```

---

## 八、排错速查

### 8.1 先跑诊断

```bash
python -m agent.doctor
```

90% 的问题会被它诊断出来。

### 8.2 常见问题对照表

| 症状 | 原因 | 修复 |
|---|---|---|
| `sinan` 报 `ModuleNotFoundError: agent.core.xxx` | Python 3.13+ editable finder 问题 | `pip install .` 或用 `python -m agent` |
| `sinan` 命令找不到 | `Scripts\` 不在 PATH | 用 `python -m agent`，或手动改 PATH |
| `⚠ 以下 Agent 缺 API Key` | `.env` key 变量名错 | 见 [3.3](#33-各-provider-的-key-变量名) |
| `✕ 意图解析失败` | LLM API 调用失败 | 检查网络 / key / 余额 |
| `Schema 校验失败` | 小模型输出 JSON 不稳 | 关键 Agent 换 deepseek |
| 生成时间过长 | 12+ 次 LLM 调用 | 用更快的模型 / 减轮数 |
| 知识库目录当前可写 | 未设物理只读 | `chmod -R a-w knowledge/` |
| Windows 路径报错 | `\` 未转义 | 用 `D:/data/x` 或 CLI 传参 |

### 8.3 详细排错

见 [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)，按错误信息组织，每个问题给出"现象 → 原因 → 三步内修复"。

---

## 九、一页速查

### 9.1 命令速查

```bash
# ===== 安装 =====
scripts\install.bat                    # Windows
bash scripts/install.sh                # Linux/macOS
pip install -e .                       # 手动

# ===== 诊断 =====
python -m agent.doctor

# ===== 配置 =====
cp .env.example .env
# 编辑 .env，填 1~3 个 key

# ===== 启动 =====
sinan                                  # 首选
python -m agent                        # 备选
python -m agent.cli                    # 再备选

# ===== 生成 =====
sinan generate <路径> -d <领域> [-o 输出] [-k 知识库]

# ===== 进化 =====
sinan evolve <旧策略.md> <新数据> -d <领域>

# ===== 对比 =====
sinan compare <A.md> <B.md> -d <领域>

# ===== 查看 =====
ls outputs/
cat outputs/strategy_*.md
```

### 9.2 参数速查

| 项 | 支持值 |
|---|---|
| **领域** | `ecommerce` / `github` / `atomgit` / `douyin` / `tiktok` |
| **路径** | 相对 / 绝对 / Windows / Linux / 单文件 / 文件夹 |
| **多 key** | `SINAN_<PROVIDER>_API_KEYS=a,b,c` |
| **输出目录** | `-o` / `--output-dir` 或 `.env` 的 `SINAN_OUTPUT_DIR` |
| **知识库** | `-k` / `--knowledge-dir` 或 `.env` 的 `SINAN_KNOWLEDGE_DIR` |

### 9.3 6-Agent 速览

| Agent | 作用 | 可独立配置 |
|---|---|---|
| 🔍 `SCOUT` | 文件侦察，识别数据内容 | ✅ |
| 🧩 `RUBRIC_A` | 出题主编（Rubric 初稿） | ✅ |
| 🧩 `RUBRIC_B` | 出题审查员（Rubric 复核） | ✅ |
| 🎯 `STRATEGY_A` | 策略撰写者 | ✅ |
| 🎯 `STRATEGY_B` | 策略反驳者 | ✅ |
| ⚖️ `JUDGE` | 判断智能体（最终裁定 + 评分） | ✅ |

### 9.4 隔离保证

- **出题组**：A ⇄ B 上下文互通；不回传给策略组
- **策略组**：A ⇄ B 上下文互通；只接收 Judge 给出的 `final_rubric`
- **Judge**：唯一可见全部上下文；只对外输出决策产物
- **知识库**：所有 Agent 可读，任何 Agent 不可写
- **硬规则**：`configs/rules.yaml` 中定义，生成前后双校验

### 9.5 目录结构速查

```
sinan_agent/
├── .env                    # 实际配置（不入 Git）
├── .env.example            # 模板
├── pyproject.toml
├── requirements.txt
├── README.md / USAGE.md / STRUCTURE.md / TROUBLESHOOTING.md
├── configs/rules.yaml      # 硬规则
├── knowledge/              # 知识库（只读）
├── data/                   # 示例数据
├── outputs/                # 输出
├── scripts/
│   ├── install.sh
│   └── install.bat
├── Dockerfile
└── agent/
    ├── __init__.py         # 包初始化 + 版本检测
    ├── __main__.py         # python -m agent 入口
    ├── cli.py
    ├── main.py
    ├── orchestrator.py
    ├── schemas.py
    ├── llm_factory.py
    ├── doctor.py           # 环境诊断
    ├── agents/
    └── core/
```

---

**文档结束** · 有问题请看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 或运行 `python -m agent.doctor`