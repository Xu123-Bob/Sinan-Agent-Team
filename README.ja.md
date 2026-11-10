<div align="center">

<img src="image/logopage02.png" alt="白澤 Baize ロゴ" width="320" />

# 司南 (Sinan-Agent-Team)

**マルチエージェント戦略策定システム**

デュアル・ゲーム · コンテキスト分離 · ナレッジベース共有 · JSON Schema 厳格検証 · マルチプロバイダー・マルチキーローテーション

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
## 概要
**本プロジェクトは、マルチエージェントによる戦略策定と戦略効果評価のフレームワークです**
- 本製品は **Rule\Rubric\LLM-to-judge** を通じて、戦略策定と戦略評価の体系を共同で構築します
- 本プロジェクトには合計 **6つのエージェント** があります。2つの出題エージェント、2つの判定エージェント、1つの偵察エージェント、1つの判断エージェントです
- Rule 層には、業務内容の制約と、**エージェント出力構造** の制約（エージェントが正常に出力することを保証）が含まれます
- Rubric は **2つの出題エージェントのゲーム** を通じて、それぞれが意見を述べ、最終的に **判定エージェントが最終確認** を行います
- 戦略策定と評価は、**2つの戦略策定エージェントが議論** し、最終的にも **判定エージェントが最終確認** を行います
- データと専門知識のスキャンと取得は、**1つの偵察エージェント** が行い、主に `knowledge/`、`data/`、`output/` をスキャンします
- 生成される成果物には、**戦略案、Rubric 問題表、討論記録** が含まれ、最終的に `knowledge/` に保存されます。新しい戦略を反復する際、**偵察エージェントが自動的にスキャン** します
- 本プロジェクトは、私が2026年北京AI青年ハッカソンに参加した作品であり、Alipay 評価で第4位を獲得し、Alipay・インテリジェントエージェント湧動コンテストに推薦されました

### マルチエージェント構造図

<div align="center">
マルチエージェント構造図
</div>

<p align="center">
  <img src="image/infra.png" alt="マルチエージェント構造図" width="800" />
</p>

### 商品紹介
静的ウェブサイト：https://sinan-website.pages.dev/

---

## コア機能

- **6-Agent アーキテクチャ**：偵察 / 出題グループ（A+B） / 戦略グループ（A+B） / 判断、それぞれが役割を担う |
- **コンテキストの厳格な分離**：出題グループ ↔ 戦略グループは完全に分離。Judge のプライベートメモリは決して外部に漏れない |
- **ナレッジベースは読み取り専用共有**：`knowledge/` はすべての Agent が読み取り可能だが、どの Agent も書き込み不可 |
- **デュアル・ゲーム三ラウンド**：Rubric グループ A ⇄ B、戦略グループ A ⇄ B、それぞれ三ラウンドのゲーム |
- **Judge の独立裁定**：すべてのコンテキストを見ることができる唯一のエージェントで、意思決定の成果物のみを出力 |
- **JSON Schema 厳格検証**：各 Agent の出力は必ず Pydantic を通過。失敗時は自動的に2回再試行 |
- **ハードルールの前後二重検証**：生成前に Prompt に注入、生成後に独立して再確認。ユーザーはボトムラインをカスタマイズ可能 |
- **マルチプロバイダー・マルチキー**：同一プロバイダーで複数キーのローテーションをサポート。各 Agent が独立してモデルを指定可能 |
- **任意のパス入力**：相対 / 絶対 / Windows / Linux / 単一ファイル / フォルダ。Enter で自動スキャン |
- **任意の業務領域**：eコマース / GitHub / AtomGit / 抖音 / TikTok を内蔵。カスタマイズ拡張可能 |
- **全中国語 CLI**：Typer + Rich レンダリング、色分けパネル、討論プロセスをリアルタイム表示 |

---
## ログイン画面
<div align="center">
ログイン画面
</div>

<p align="center">
  <img src="image/sinancli-01.jpg" alt="ログイン画面" width="800" />
</p>


## 環境要件（まずここを読む）
```
| 項目 | 推奨 | 説明 |
|---|---|---|
| **Python** | **3.10 / 3.11 / 3.12** | ⭐ 強く推奨 |
| Python 3.13 | 利用可能 | 一部の依存関係に小さな問題がある可能性 |
| Python 3.14+ | ❌ **非推奨** | editable install に既知の互換性問題あり |
| OS | Windows / macOS / Linux | 全プラットフォーム対応 |
| ネットワーク | LLM API へのアクセスが必要 | DeepSeek / Kimi / Qwen など |
```
> **インストールや起動で問題が発生した場合は、まず診断を実行**：
> ```bash
> python -m agent.doctor
> ```
> Python バージョン、依存関係、agent パッケージの完全性、インストール方法、起動テストを一括チェックし、修復提案を提示します。

---

## インストール（3つの方法から選択）

### 方法 1：ワンクリックスクリプト（初心者に推奨）

```bash
# Windows
scripts\install.bat

# Linux / macOS
bash scripts/install.sh
```

スクリプトは Python のチェック、venv の作成、依存関係のインストール、doctor の実行による検証を自動で行います。

### 方法 2：手動インストール（Python に慣れた開発者向け）

```bash
# 仮想環境の使用を強く推奨
python -m venv .venv

# アクティベート（3つから1つ選択）
source .venv/bin/activate         # Linux / macOS
.venv\Scripts\activate            # Windows CMD
.venv\Scripts\Activate.ps1        # Windows PowerShell

# インストール
pip install -e .
```

> **Python 3.13+ ユーザーへの注意**：`pip install -e .` の後で `sinan` コマンドが `ModuleNotFoundError: agent.core.xxx` を報告する場合は、以下に変更してください：
> ```bash
> pip install .
> ```
> または `python -m agent` で直接起動（下記「起動」セクション参照）。

### 方法 3：Docker（環境構築を避けたい場合）

```bash
docker build -t sinan .

docker run -it --rm \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/knowledge:/app/knowledge \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  sinan
```

Python バージョン、依存関係のコンパイル、システム差異の問題を完全に回避します。

---

## 起動（3つの等価な方法）

```bash
sinan                  # pip でインストールしたコマンド（最も便利）
python -m agent        # 代替（sinan コマンドが無効な場合に使用）
python -m agent.cli    # さらに代替
```

**3つのコマンドは完全に等価** です。いずれか1つが動作すれば問題ありません。

`sinan` がエラーを報告する場合は、`python -m agent` に直接切り替えてください。**問題の調査は不要です**。

---

## クイックスタート

### 1. バックエンドの設定

```bash
cp .env.example .env
```

`.env` を編集し、**少なくとも1つ** の API キーを入力（最小構成）：

```env
SINAN_DEEPSEEK_API_KEY=sk-あなたのキー
SINAN_DEFAULT_PROVIDER=deepseek
```

他のフィールドはすべて削除して、この2行だけで構いません。

> マルチモデル、マルチキープール、Agent ごとの割り当てなどの詳細設定は [`USAGE.md`](USAGE.md) を参照してください。

### 2. ナレッジベースの準備（任意）

```bash
mkdir -p knowledge
echo "# 会社用語規範\n絶対的な表現を避ける..." > knowledge/company_style.md
```

起動時に自動的に読み込まれ、すべての Agent が参照できますが、どの Agent も **書き込みはできません**。

### 3. 設定の検証

```bash
python -c "from agent.core.agent_config import summarize_configs; print(summarize_configs())"
```

6つの Agent の Provider と Key のステータスがすべて ✅ であることを確認してください。

### 4. 実行

```bash
sinan
# または
python -m agent
```

またはコマンドラインで直接生成：

```bash
sinan generate ./data/ecommerce_v1 -d ecommerce
# または
python -m agent generate ./data/ecommerce_v1 -d ecommerce
```

### 5. 成果物の確認

```bash
ls outputs/
# strategy_<domain>_<folder>_<ts>.md   ← 最終戦略
# rubric_<domain>_<folder>_<ts>.json   ← 最終 Rubric
# debate_<domain>_<folder>_<ts>.json   ← 完全な討論記録
```

### 6. 6つのエージェント
```
| アイコン | Agent | 役割 | 独立したモデル設定 |
|------|-------|------|----------------|
| 🔍 | `SCOUT` | ファイル偵察、データ内容の識別 | ✅ |
| 🧩 | `RUBRIC_A` | 出題メイン（Rubric 初稿） | ✅ |
| 🧩 | `RUBRIC_B` | 出題レビュアー（Rubric 再確認） | ✅ |
| 🎯 | `STRATEGY_A` | 戦略執筆者 | ✅ |
| 🎯 | `STRATEGY_B` | 戦略反論者 | ✅ |
| ⚖️ | `JUDGE` | 判断エージェント（最終裁定 + 評価） | ✅ |
```

---

## CLI コマンド

```bash
# インタラクティブ chat（初心者に推奨）
sinan

# ワンクリック生成
sinan generate <任意のパス> -d <領域> [-o 出力ディレクトリ] [-k ナレッジベースディレクトリ]

# 反復進化（V1 → V2）
sinan evolve <旧戦略.md> <新データパス> -d <領域>

# 2つの戦略を比較
sinan compare <戦略A.md> <戦略B.md> -d <領域>

# 環境診断
python -m agent.doctor
```

> `sinan` コマンドが使用できない場合は、すべて `python -m agent <サブコマンド>` に置き換えてください。

### サポート領域

システムデフォルト領域：`ecommerce` · `github` · `atomgit` · `douyin` · `tiktok` · `finance`

> ユーザーは `data/` フォルダに関連データとタスク目標を追加できます。

> ユーザーは `configs/rules.yaml` で新しい領域ルールをカスタマイズできます。

### サポートパス

- ✅ 相対パス（`./data/foo`）
- ✅ 絶対パス（`/home/user/foo`、`D:\data\foo`）
- ✅ 単一ファイル（`./goal.md`）
- ✅ フォルダ全体（任意の場所）
- ✅ Enter キー → 現在のディレクトリをスマートスキャン

---

## ナレッジベース

`knowledge/` は **読み取り専用の共有ナレッジベース** であり、6つのすべてのインテリジェントエージェントが参照します。

### 特徴
- **共有読み取り**：すべての Agent は生成前にナレッジベースの内容を参照として読み取ります
- **書き込み不可**：コード層の `safe_io.safe_write` が強制的にブロック |
- **物理的強化**：`chmod -R a-w knowledge/` の実行を推奨（Linux/macOS） |
- **分離を破壊しない**：ナレッジベースは静的な公共参照であり、ゲーム history とは完全に無関係 |
- **サイズ制御**：単一ファイル 8k 文字、合計 20k 文字で切り捨て。`.env` で調整可能 |
- **マルチフォーマット**：md / txt / docx / xlsx / csv / pptx / yaml / json |

### 適したコンテンツ

- 会社ブランド / 用語規範
- 業界標準 / ポリシーレッドライン
- 社内 SOP / プロセス文書
- 再利用可能な戦略テンプレート
- 過去の優れた事例（匿名化後）
- 金融知識

### 不適切なコンテンツ

- 平文の秘密鍵 / パスワード
- 顧客のプライバシーデータ
- 大きなバイナリ（画像/動画）

---

## 設定

### 階層設定（推奨）

各 Agent が独立してモデルとキーを指定可能：

```env
SINAN_DEFAULT_PROVIDER=kimi/deepseek/GLM/Qwen

SINAN_RUBRIC_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_RUBRIC_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_JUDGE_PROVIDER=kimi/deepseek/GLM/Qwen
```

### マルチキープール（レート制限 / マルチアカウント）

```env
# カンマ区切り
SINAN_DEEPSEEK_API_KEYS=sk-1,sk-2,sk-3

# または行ごとに番号付け
SINAN_DEEPSEEK_API_KEY_1=sk-1
SINAN_DEEPSEEK_API_KEY_2=sk-2
SINAN_DEEPSEEK_API_KEY_3=sk-3
```

起動バナーに `✅ x3 ローテーション` と表示され、すべての呼び出しが自動的にラウンドロビンで分散されます。

### 各プロバイダーのキー変数名
- DeepSeek：`SINAN_DEEPSEEK_API_KEY`
- Kimi / Moonshot：`SINAN_MOONSHOT_API_KEY`
- Qwen / 通義千問：`SINAN_DASHSCOPE_API_KEY`
- GLM / 智譜：`SINAN_ZHIPUAI_API_KEY`
- Ollama ローカル：キー不要

### ハードルールのカスタマイズ

`configs/rules.yaml` を編集：

```yaml
global:
  rules:
    - name: "絶対的表現の禁止"
      type: "forbidden"
      value: "最高|第一|絶対"
      score: 20
      description: "戦略に絶対的な表現を含めてはならない"

healthcare:
  rules:
    - name: "処方薬の商品名を含めない"
      type: "forbidden"
      value: "アスピリン|イブプロフェン"
      score: 20
```

サポートされるルールタイプ：`keyword` / `forbidden` / `regex` / `min_length` / `schema_field`。

---

## アーキテクチャの要点

### コンテキスト分離の保証
```
| Agent | Rubric ゲーム閲覧 | Strategy ゲーム閲覧 | Judge メモリ閲覧 | ナレッジベース閲覧 | ナレッジベース書き込み |
|---|:---:|:---:|:---:|:---:|:---:|
| 🔍 ScoutAgent | ✗ | ✗ | ✗ | ✓ | ✗ |
| 🧩 RubricAgentA / B | ✓（自分のグループのみ） | ✗ | ✗ | ✓ | ✗ |
| 🎯 StrategyAgentA / B | ✗（final_rubric のみ取得） | ✓（自分のグループのみ） | ✗ | ✓ | ✗ |
| ⚖️ JudgeAgent | ✓ | ✓ | ✓（自身のプライベート） | ✓ | ✗ |
```
### 出力 Schema の厳格検証
```
| Agent | 出力 Schema |
|---|---|
| Scout | `ScoutReport` |
| RubricA / B | `RubricSchema` |
| StrategyA / B | `StrategySchema` |
| Judge | `RubricDecision` / `StrategyDecision` |
```
失敗時は自動的にエラーメッセージを LLM に戻して自己修復させ、最大2回再試行します。

### ハードルールの三層防御

```
生成前：rule_constraints を Prompt に注入 → Agent が自主的に遵守
生成後：RuleEngine.evaluate(final_strategy) → 独立して再確認・採点
書き込み時：safe_io.safe_write → ナレッジベースへの書き込みをブロック
```

---

## トラブルシューティング

### ワンクリック診断（まずこれを実行）

```bash
python -m agent.doctor
```

チェック内容：
- Python バージョン
- サードパーティ依存関係
- agent パッケージの完全性（24モジュール）
- インストール方法（editable / 通常 / ソースディレクトリ）
- 起動テスト

問題に対して **具体的な修復コマンド** を提示します。

### よくある問題のクイックリファレンス

#### `sinan` が `ModuleNotFoundError: No module named 'agent.core.xxx'` を報告

**原因**：Python 3.13+ で editable install の finder マッピングが不完全。

**修復（3つから1つ選択）**：

```bash
# 方案 A：通常インストールに変更
pip uninstall -y sinan-agent
pip install .

# 方案 B：代替起動方法を直接使用
python -m agent

# 方案 C：Windows で sinan.cmd ラッパーを作成
# TROUBLESHOOTING.md を参照
```

#### `sinan` コマンドが見つからない

```bash
# 代替起動を使用
python -m agent
```

または Python の `Scripts\` を PATH 環境変数に追加します。

#### 依存関係がインストールできない / 固まる

**原因**：Python バージョンが新しすぎて、一部のパッケージがまだ対応していない。

**修復**：
1. Python 3.12 に切り替える
2. または Docker を使用：`docker build -t sinan . && docker run -it sinan`

#### `⚠ 以下の Agent に API Key がありません`

**原因**：`.env` 内の対応する provider のキー変数名が間違っている。

**よくある間違い**：

| あなたが書いたもの | 正しくは |
|---|---|
| `SINAN_KIMI_API_KEY` | `SINAN_MOONSHOT_API_KEY` |
| `SINAN_QWEN_API_KEY` | `SINAN_DASHSCOPE_API_KEY` |
| `SINAN_GLM_API_KEY` | `SINAN_ZHIPUAI_API_KEY` |

#### `Schema 検証失敗（2回再試行後）`

**原因**：LLM の JSON 出力形式が不安定（小規模モデル / 温度が高い）。

**修復**：重要な Agent に強力なモデルを割り当てる

```env
SINAN_RUBRIC_A_PROVIDER=deepseek
SINAN_JUDGE_PROVIDER=deepseek
```

> その他のトラブルシューティング項目は [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) を参照してください。

---

## 成果物の例

`outputs/strategy_ecommerce_ecommerce_v1_20251104_141500.md`：

```markdown
# eコマース Q4 運営戦略

> 領域: ecommerce | Judge 評価: 85/100 | ハードルール: 100/100 | 生成日時 2025-11-04 14:15:00

## 目標
GMV 30% 向上、新規客占比 40%、リピート率 25%、ROI ≥ 3.0

## 商品プロモーション
...

- **爆款 A001 タイムセール** — 毎週水曜限定2時間、サイト内+プライベートドメインに配信
  (担当: 運営チーム | 時間: 毎週水曜 20:00-22:00 | KPI: 単場 GMV ≥ 8万)
```

`outputs/debate_ecommerce_ecommerce_v1_20251104_141500.json`：

```json
{
  "rubric_history": [...],   // 出題グループ三ラウンドゲームの全過程
  "strategy_history": [...], // 戦略グループ三ラウンドゲームの全過程
  "judge_reasoning": "..."   // Judge 裁定説明
}
```

---

## ドキュメントナビゲーション

| ドキュメント | 内容 |
|---|---|
| [`USAGE.md`](USAGE.md) | 完全使用マニュアル（10シナリオ + トラブルシューティング） |
| [`STRUCTURE.md`](STRUCTURE.md) | プロジェクト構造、ファイルの役割、データフロー |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | トラブルシューティングマニュアル（エラーメッセージから検索） |
| [`knowledge/README.md`](knowledge/README.md) | ナレッジベースの使用説明 |

---

## 開発

```bash
# 開発依存関係のインストール
pip install -e ".[all]"

# テストの実行
pytest

# Lint
ruff check agent/

# フォーマット
ruff format agent/

# 環境診断
python -m agent.doctor
```

---

## License

[Apache-2.0](apach-2.0)

---

## 🙏 謝辞

- [OpenAI Python SDK](https://github.com/openai/openai-python) — 統一 LLM 接続
- [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) — 美しい CLI
- [Pydantic](https://docs.pydantic.dev/) — Schema 厳格検証
- [DeepSeek](https://deepseek.com/) / [Kimi](https://kimi.moonshot.cn/) / [Qwen](https://dashscope.aliyun.com/) / [GLM](https://open.bigmodel.cn/) — バックエンドモデル能力の提供
- [baize](https://github.com/Xu123-Bob/Baize) — 本人自作の agent
- **また、新京報と貝殻財経に感謝します。本作品は、開催された2026年AI青年ハッカソンコンテストで Alipay 評価 4/26、大会 6/26 の成績を収め、Alipay・インテリジェントエージェント湧動コンテストにも推薦されました**