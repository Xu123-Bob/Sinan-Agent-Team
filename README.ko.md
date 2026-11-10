<div align="center">

<img src="image/logopage02.png" alt="백택 Baize 로고" width="320" />

# 사남 (Sinan-Agent-Team)

**멀티 에이전트 전략 수립 시스템**

듀얼 게임 · 컨텍스트 격리 · 지식베이스 공유 · JSON Schema 강검증 · 멀티 Provider 멀티 Key 로테이션

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
## 개요
**본 프로젝트는 멀티 에이전트 전략 수립 및 전략 효과 평가 프레임워크입니다**
- 제품은 **Rule\Rubric\LLM-to-judge** 를 통해 전략 수립과 전략 평가 체계를 공동으로 구축합니다
- 본 프로젝트에는 총 **6개의 에이전트** 가 있습니다. 2개의 출제 에이전트, 2개의 판정 에이전트, 1개의 정찰 에이전트, 1개의 판단 에이전트입니다
- Rule 계층은 비즈니스 내용의 제약과 **에이전트 출력 구조** 의 제약(에이전트가 정상적으로 출력하도록 보장)을 포함합니다
- Rubric은 **2개의 출제 에이전트 게임** 을 통해 각자가 관점을 설명하고, 최종적으로 **판정 에이전트가 최종 확인** 을 완료합니다
- 전략 수립과 평가는 **2개의 전략 수립 에이전트가 토론** 하고, 최종적으로도 **판정 에이전트가 최종 확인** 을 완료합니다
- 데이터와 전문 지식의 스캔 및 획득은 **1개의 정찰 에이전트** 가 수행하며, 주로 `knowledge/`, `data/`, `output/` 을 스캔합니다
- 생성 산출물에는 **전략안, Rubric 문제표, 토론 원고** 가 포함되며, 최종적으로 `knowledge/` 에 저장됩니다. 새로운 전략을 반복할 때 **정찰 에이전트가 자동으로 스캔** 합니다
- 본 프로젝트는 제가 2026년 베이징 AI 청년 해커톤에 참가한 작품으로, Alipay 평가 4위를 획득하고 Alipay·지능형 에이전트 용동 대회에 추천되었습니다

### 멀티 에이전트 구조도

<div align="center">
멀티 에이전트 구조도
</div>

<p align="center">
  <img src="image/infra.png" alt="멀티 에이전트 구조도" width="800" />
</p>

### 제품 소개  
정적 웹사이트: https://sinan-website.pages.dev/

---

## 핵심 기능

- **6-Agent 아키텍처**：정찰 / 출제 그룹(A+B) / 전략 그룹(A+B) / 판단, 각자 역할 수행 |
- **컨텍스트 엄격 격리**：출제 그룹 ↔ 전략 그룹 완전 격리; Judge 프라이빗 메모리는 절대 외부 유출 불가 |
- **지식베이스 읽기 전용 공유**：`knowledge/` 는 모든 Agent가 읽을 수 있지만, 어떤 Agent도 쓸 수 없음 |
- **듀얼 게임 3라운드**：Rubric 그룹 A ⇄ B, 전략 그룹 A ⇄ B, 각각 3라운드 게임 |
- **Judge 독립 결정**：모든 컨텍스트를 볼 수 있는 유일한 에이전트이며, 결정 산출물만 출력 |
- **JSON Schema 강검증**：각 Agent 출력은 반드시 Pydantic 통과; 실패 시 자동으로 2회 재시도 |
- **하드 룰 전후 이중 검증**：생성 전 Prompt에 주입, 생성 후 독립 재검증; 사용자가 최저선 커스터마이즈 가능 |
- **멀티 Provider 멀티 Key**：동일 Provider에서 여러 Key 로테이션 지원; 각 Agent가 독립적으로 모델 지정 가능 |
- **임의 경로 입력**：상대 / 절대 / Windows / Linux / 단일 파일 / 폴더; Enter로 자동 스캔 |
- **임의 비즈니스 영역**：이커머스 / GitHub / AtomGit / 도우인 / TikTok 내장; 커스터마이즈 확장 가능 |
- **전체 중국어 CLI**：Typer + Rich 렌더링, 컬러 패널, 토론 과정 실시간 출력 |

---
## 로그인 화면
<div align="center">
로그인 화면
</div>

<p align="center">
  <img src="image/sinancli-01.jpg" alt="로그인 화면" width="800" />
</p>


## 환경 요구사항 (먼저 읽기)
```
| 항목 | 권장 | 설명 |
|---|---|---|
| **Python** | **3.10 / 3.11 / 3.12** | ⭐ 강력 권장 |
| Python 3.13 | 사용 가능 | 일부 의존성에 작은 문제 있을 수 있음 |
| Python 3.14+ | ❌ **권장하지 않음** | editable install에 알려진 호환성 문제 있음 |
| 운영체제 | Windows / macOS / Linux | 전체 플랫폼 지원 |
| 네트워크 | LLM API 접근 필요 | DeepSeek / Kimi / Qwen 등 |
```
> **설치 또는 시작 문제가 발생하면 먼저 진단 실행**：
> ```bash
> python -m agent.doctor
> ```
> Python 버전, 의존성, agent 패키지 완전성, 설치 방식, 시작 테스트를 한 번에 확인하고 수정 제안을 제공합니다.

---

## 설치 (3가지 방법 중 선택)

### 방법 1: 원클릭 스크립트 (초보자 권장)

```bash
# Windows
scripts\install.bat

# Linux / macOS
bash scripts/install.sh
```

스크립트가 Python 확인, venv 생성, 의존성 설치, doctor 검증을 자동으로 수행합니다.

### 방법 2: 수동 설치 (Python에 익숙한 개발자)

```bash
# 가상 환경 사용 강력 권장
python -m venv .venv

# 활성화 (3가지 중 1가지 선택)
source .venv/bin/activate         # Linux / macOS
.venv\Scripts\activate            # Windows CMD
.venv\Scripts\Activate.ps1        # Windows PowerShell

# 설치
pip install -e .
```

> **Python 3.13+ 사용자 주의**：`pip install -e .` 후 `sinan` 명령이 `ModuleNotFoundError: agent.core.xxx` 를 보고하면 다음으로 변경하세요：
> ```bash
> pip install .
> ```
> 또는 `python -m agent` 로 직접 시작 (아래 「시작」 섹션 참조).

### 방법 3: Docker (환경 구축을 피하고 싶은 경우)

```bash
docker build -t sinan .

docker run -it --rm \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/knowledge:/app/knowledge \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  sinan
```

Python 버전, 의존성 컴파일, 시스템 차이 문제를 완전히 우회합니다.

---

## 시작 (3가지 동등한 방법)

```bash
sinan                  # pip 설치 명령 (가장 편리)
python -m agent        # 대안 (sinan 명령이 무효일 때 사용)
python -m agent.cli    # 추가 대안
```

**세 명령은 완전히 동등** 하며, 어느 하나만 작동하면 됩니다.

`sinan` 이 오류를 보고하면 `python -m agent` 로 직접 전환하세요. **문제를 조사할 필요가 없습니다**.

---

## 빠른 시작

### 1. 백엔드 구성

```bash
cp .env.example .env
```

`.env` 를 편집하여 **최소 하나** 의 API Key 입력 (최소 구성):

```env
SINAN_DEEPSEEK_API_KEY=sk-당신의키
SINAN_DEFAULT_PROVIDER=deepseek
```

다른 필드는 모두 삭제하고 이 두 줄만 있으면 됩니다.

> 다중 모델, 다중 Key 풀, Agent별 할당 등의 고급 구성은 [`USAGE.md`](USAGE.md) 를 참조하세요.

### 2. 지식베이스 준비 (선택)

```bash
mkdir -p knowledge
echo "# 회사 용어 규범\n절대적 표현 회피..." > knowledge/company_style.md
```

시작 시 자동으로 로드되어 모든 Agent가 참고할 수 있지만, 어떤 Agent도 **쓸 수 없습니다**.

### 3. 구성 검증

```bash
python -c "from agent.core.agent_config import summarize_configs; print(summarize_configs())"
```

6개 Agent의 Provider와 Key 상태가 모두 ✅ 인지 확인하세요.

### 4. 실행

```bash
sinan
# 또는
python -m agent
```

또는 명령줄에서 직접 생성:

```bash
sinan generate ./data/ecommerce_v1 -d ecommerce
# 또는
python -m agent generate ./data/ecommerce_v1 -d ecommerce
```

### 5. 산출물 확인

```bash
ls outputs/
# strategy_<domain>_<folder>_<ts>.md   ← 최종 전략
# rubric_<domain>_<folder>_<ts>.json   ← 최종 Rubric
# debate_<domain>_<folder>_<ts>.json   ← 전체 토론 기록
```

### 6. 6개 에이전트
```
| 아이콘 | Agent | 역할 | 독립 모델 설정 |
|------|-------|------|----------------|
| 🔍 | `SCOUT` | 파일 정찰, 데이터 내용 식별 | ✅ |
| 🧩 | `RUBRIC_A` | 출제 메인 (Rubric 초안) | ✅ |
| 🧩 | `RUBRIC_B` | 출제 검토자 (Rubric 재검토) | ✅ |
| 🎯 | `STRATEGY_A` | 전략 작성자 | ✅ |
| 🎯 | `STRATEGY_B` | 전략 반론자 | ✅ |
| ⚖️ | `JUDGE` | 판단 에이전트 (최종 결정 + 평가) | ✅ |
```

---

## CLI 명령

```bash
# 대화형 chat (초보자 권장)
sinan

# 원클릭 생성
sinan generate <임의 경로> -d <영역> [-o 출력 디렉토리] [-k 지식베이스 디렉토리]

# 반복 진화 (V1 → V2)
sinan evolve <기존 전략.md> <새 데이터 경로> -d <영역>

# 두 전략 비교
sinan compare <전략A.md> <전략B.md> -d <영역>

# 환경 진단
python -m agent.doctor
```

> `sinan` 명령이 사용 불가능한 경우, 모두 `python -m agent <하위 명령>` 으로 대체하세요.

### 지원 영역

시스템 기본 영역: `ecommerce` · `github` · `atomgit` · `douyin` · `tiktok` · `finance`

> 사용자는 `data/` 폴더에 관련 데이터와 작업 목표를 추가할 수 있습니다.

> 사용자는 `configs/rules.yaml` 에서 새 영역 규칙을 커스터마이즈할 수 있습니다.

### 지원 경로

- ✅ 상대 경로 (`./data/foo`)
- ✅ 절대 경로 (`/home/user/foo`, `D:\data\foo`)
- ✅ 단일 파일 (`./goal.md`)
- ✅ 전체 폴더 (임의 위치)
- ✅ Enter 키 → 현재 디렉토리 스마트 스캔

---

## 지식베이스

`knowledge/` 는 **읽기 전용 공유 지식베이스** 로, 6개 모든 지능형 에이전트가 참고합니다.

### 특징
- **공유 읽기**：모든 Agent는 생성 전에 지식베이스 내용을 참고로 읽음
- **쓰기 불가**：코드 계층 `safe_io.safe_write` 가 강제 차단 |
- **물리적 강화**：`chmod -R a-w knowledge/` 실행 권장 (Linux/macOS) |
- **격리 파괴 없음**：지식베이스는 정적 공공 참조이며, 게임 history와 완전히 무관 |
- **용량 제어**：단일 파일 8k 문자, 총 20k 문자 잘림, `.env` 로 조정 가능 |
- **다중 형식**：md / txt / docx / xlsx / csv / pptx / yaml / json |

### 적합한 콘텐츠

- 회사 브랜드 / 용어 규범
- 업계 표준 / 정책 레드라인
- 내부 SOP / 프로세스 문서
- 재사용 가능한 전략 템플릿
- 과거 우수 사례 (익명화 후)
- 금융 지식

### 부적합한 콘텐츠

- 평문 비밀 키 / 비밀번호
- 고객 개인정보 데이터
- 대형 바이너리 (이미지/동영상)

---

## 구성

### 계층 구성 (권장)

각 Agent가 독립적으로 모델과 key 지정 가능:

```env
SINAN_DEFAULT_PROVIDER=kimi/deepseek/GLM/Qwen

SINAN_RUBRIC_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_RUBRIC_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_A_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_STRATEGY_B_PROVIDER=kimi/deepseek/GLM/Qwen
SINAN_JUDGE_PROVIDER=kimi/deepseek/GLM/Qwen
```

### 다중 Key 풀 (속도 제한 / 다중 계정)

```env
# 쉼표 구분
SINAN_DEEPSEEK_API_KEYS=sk-1,sk-2,sk-3

# 또는 줄별 번호
SINAN_DEEPSEEK_API_KEY_1=sk-1
SINAN_DEEPSEEK_API_KEY_2=sk-2
SINAN_DEEPSEEK_API_KEY_3=sk-3
```

시작 배너에 `✅ x3 로테이션` 이 표시되며, 모든 호출이 자동으로 라운드 로빈 분산됩니다.

### 각 Provider의 key 변수명
- DeepSeek: `SINAN_DEEPSEEK_API_KEY`
- Kimi / Moonshot: `SINAN_MOONSHOT_API_KEY`
- Qwen / 통의천문: `SINAN_DASHSCOPE_API_KEY`
- GLM / 지보: `SINAN_ZHIPUAI_API_KEY`
- Ollama 로컬: key 불필요

### 하드 룰 커스터마이즈

`configs/rules.yaml` 편집:

```yaml
global:
  rules:
    - name: "절대적 표현 금지"
      type: "forbidden"
      value: "최고|첫째|절대"
      score: 20
      description: "전략에 절대적 표현이 포함되어서는 안 됨"

healthcare:
  rules:
    - name: "처방약 상품명 포함 금지"
      type: "forbidden"
      value: "아스피린|이부프로펜"
      score: 20
```

지원 규칙 유형: `keyword` / `forbidden` / `regex` / `min_length` / `schema_field`.

---

## 아키텍처 요점

### 컨텍스트 격리 보장
```
| Agent | Rubric 게임 열람 | Strategy 게임 열람 | Judge 메모리 열람 | 지식베이스 열람 | 지식베이스 쓰기 |
|---|:---:|:---:|:---:|:---:|:---:|
| 🔍 ScoutAgent | ✗ | ✗ | ✗ | ✓ | ✗ |
| 🧩 RubricAgentA / B | ✓ (자기 그룹만) | ✗ | ✗ | ✓ | ✗ |
| 🎯 StrategyAgentA / B | ✗ (final_rubric만 획득) | ✓ (자기 그룹만) | ✗ | ✓ | ✗ |
| ⚖️ JudgeAgent | ✓ | ✓ | ✓ (자신의 프라이빗) | ✓ | ✗ |
```
### 출력 Schema 강검증
```
| Agent | 출력 Schema |
|---|---|
| Scout | `ScoutReport` |
| RubricA / B | `RubricSchema` |
| StrategyA / B | `StrategySchema` |
| Judge | `RubricDecision` / `StrategyDecision` |
```
실패 시 자동으로 오류 메시지를 LLM에 되돌려 자가 수정하게 하며, 최대 2회 재시도합니다.

### 하드 룰 3계층 방어

```
생성 전: rule_constraints를 Prompt에 주입 → Agent가 자발적으로 준수
생성 후: RuleEngine.evaluate(final_strategy) → 독립 재검증 및 채점
쓰기 시: safe_io.safe_write → 지식베이스 쓰기 차단
```

---

## 문제 해결

### 원클릭 진단 (먼저 실행)

```bash
python -m agent.doctor
```

확인 항목:
- Python 버전
- 서드파티 의존성
- agent 패키지 완전성 (24개 모듈)
- 설치 방식 (editable / 일반 / 소스 디렉토리)
- 시작 테스트

문제에 대해 **구체적인 수정 명령** 을 제시합니다.

### 일반 문제 빠른 참조

#### `sinan` 이 `ModuleNotFoundError: No module named 'agent.core.xxx'` 보고

**원인**: Python 3.13+ 에서 editable install의 finder 매핑이 불완전.

**수정 (3가지 중 1가지 선택)**:

```bash
# 방안 A: 일반 설치로 변경
pip uninstall -y sinan-agent
pip install .

# 방안 B: 대안 시작 방법 직접 사용
python -m agent

# 방안 C: Windows에서 sinan.cmd 래퍼 생성
# TROUBLESHOOTING.md 참조
```

#### `sinan` 명령을 찾을 수 없음

```bash
# 대안 시작 사용
python -m agent
```

또는 Python의 `Scripts\` 를 PATH 환경 변수에 추가하세요.

#### 의존성 설치 불가 / 멈춤

**원인**: Python 버전이 너무 새로워 일부 패키지가 아직 적응하지 못함.

**수정**:
1. Python 3.12로 전환
2. 또는 Docker 사용: `docker build -t sinan . && docker run -it sinan`

#### `⚠ 다음 Agent에 API Key 없음`

**원인**: `.env` 의 해당 provider key 변수명이 잘못됨.

**흔한 실수**:

| 당신이 쓴 것 | 올바른 것 |
|---|---|
| `SINAN_KIMI_API_KEY` | `SINAN_MOONSHOT_API_KEY` |
| `SINAN_QWEN_API_KEY` | `SINAN_DASHSCOPE_API_KEY` |
| `SINAN_GLM_API_KEY` | `SINAN_ZHIPUAI_API_KEY` |

#### `Schema 검증 실패 (2회 재시도 후)`

**원인**: LLM 출력 JSON 형식 불안정 (소형 모델 / 온도 과高).

**수정**: 핵심 Agent에 더 강력한 모델 할당

```env
SINAN_RUBRIC_A_PROVIDER=deepseek
SINAN_JUDGE_PROVIDER=deepseek
```

> 더 많은 문제 해결 항목은 [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) 를 참조하세요.

---

## 산출물 예시

`outputs/strategy_ecommerce_ecommerce_v1_20251104_141500.md`:

```markdown
# 이커머스 Q4 운영 전략

> 영역: ecommerce | Judge 평가: 85/100 | 하드 룰: 100/100 | 생성일 2025-11-04 14:15:00

## 목표
GMV 30% 향상, 신규 고객 비중 40%, 재구매율 25%, ROI ≥ 3.0

## 상품 프로모션
...

- **히트 상품 A001 타임세일** — 매주 수요일 2시간 한정, 사이트 내+프라이빗 도메인 배포
  (담당: 운영팀 | 시간: 매주 수요일 20:00-22:00 | KPI: 단일 세션 GMV ≥ 8만)
```

`outputs/debate_ecommerce_ecommerce_v1_20251104_141500.json`:

```json
{
  "rubric_history": [...],   // 출제 그룹 3라운드 게임 전 과정
  "strategy_history": [...], // 전략 그룹 3라운드 게임 전 과정
  "judge_reasoning": "..."   // Judge 결정 설명
}
```

---

## 문서 내비게이션

| 문서 | 내용 |
|---|---|
| [`USAGE.md`](USAGE.md) | 전체 사용 매뉴얼 (10개 시나리오 + 문제 해결) |
| [`STRUCTURE.md`](STRUCTURE.md) | 프로젝트 구조, 파일 책임, 데이터 흐름 |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | 문제 해결 매뉴얼 (오류 메시지로 검색) |
| [`knowledge/README.md`](knowledge/README.md) | 지식베이스 사용 설명 |

---

## 개발

```bash
# 개발 의존성 설치
pip install -e ".[all]"

# 테스트 실행
pytest

# Lint
ruff check agent/

# 포맷
ruff format agent/

# 환경 진단
python -m agent.doctor
```

---

## License

[Apache-2.0](apach-2.0)

---

## 🙏 감사의 말

- [OpenAI Python SDK](https://github.com/openai/openai-python) — 통합 LLM 연결
- [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) — 아름다운 CLI
- [Pydantic](https://docs.pydantic.dev/) — Schema 강검증
- [DeepSeek](https://deepseek.com/) / [Kimi](https://kimi.moonshot.cn/) / [Qwen](https://dashscope.aliyun.com/) / [GLM](https://open.bigmodel.cn/) — 백엔드 모델 능력 제공
- [baize](https://github.com/Xu123-Bob/Baize) — 본인 자체 개발 agent
- **또한 신징보와 베이커차이징에 감사드립니다. 본 작품은 개최된 2026년 AI 청년 해커톤 대회에서 Alipay 평가 4/26, 대회 6/26의 성적을 거두었으며, Alipay·지능형 에이전트 용동 대회에도 추천되었습니다**