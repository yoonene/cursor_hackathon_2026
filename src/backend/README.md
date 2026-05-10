# AI Saju Counselor — Backend (`src/backend`)

백엔드는 해커톤 프로젝트 **AI Saju Counselor**의 일부로, 사용자가 기능 메뉴를 고르는 대신 대화와 상황에 따라 다음 점(reading)을 제안하는 **에이전트형 사주 상담**을 지향합니다. 제품 기획·API 계약은 저장소 루트의 `docs/`를 기준으로 합니다.

- [`docs/hackathon_project_plan.md`](../../docs/hackathon_project_plan.md) — 문제 정의, UX(인테이크 → 전체 리포트 → 상담), 보드 템플릿, 기술 아키텍처 방향
- [`docs/api_contract.md`](../../docs/api_contract.md) — REST 엔드포인트, `saju_report` / `counseling_board` 스키마, `semantic_key` 규칙 등 프론트엔드와의 계약

---

## 이 백엔드가 하는 일 (현재 구현 기준)

### 구현됨

1. **`GET /health`**  
   헬스 체크 (`{"status": "ok"}`).

2. **`POST /reading/start`**  
   고정 인테이크 폼에 대응하는 최초 리딩을 생성합니다.
   - `PersonProfile` 조립 → **`saju_calculator`(lunar_python)** 원국 계산 · **`rule_engine`(YAML 규칙)** 해석 시그널 (**side_projects 로직 차용**, 템플릿 렌더러 미사용)
   - 로컬 시간대 기본값: `Settings.default_timezone` (기본 `Asia/Seoul`)
   - **`counselor_llm.generate_initial_counseling_copy`** 가 CLōD/OpenAI 호환 Chat Completions로 **초기 채팅 메시지 + 리포트 섹션 문구(JSON)** 생성; 키·URL·모델 없으면 **시그널 요약 폴백**
   - **`build_saju_report`** 가 팩트(`SajuData`) + LLM 출력으로 `SajuReport` 생성
   - **`build_initial_counseling_board`**, 세션 저장, `agent_trace`에 `analyze_base_saju` 및 `llm_call` 포함

3. **`POST /chat`**  
   동일 `session_id`로 후속 메시지를 보냅니다. **`chat_service.continue_chat`** + **`generate_followup_counseling_reply`**; 세션이 없으면 **404**.

### 아직 HTTP로 노출되지 않음 (스키마·도메인 로직은 존재)

API 계약과 프로젝트 플랜에 맞춰 **다음은 Pydantic 스키마와 순수 함수 수준으로 준비**되어 있으나, 라우터·LangGraph 노드와 연결되지 않았습니다.

| 계약 / 계획 | 코드 위치 (요약) |
|-------------|------------------|
| `POST /session/reset` | `schemas.requests.ResetSessionRequest`, `session_store.InMemorySessionStore.reset` |
| `POST /demo/load` | `schemas.requests.LoadDemoRequest` |
| `GET /session/{session_id}` | 세션 스토어 `get` — 라우트 미등록 |

**도메인 도구(결정론적):**

- `saju.compute_saju.analyze_base_saju` — 기본 사주 프로필
- `saju.compatibility.analyze_compatibility` — 궁합 점수·라벨·강점·마찰
- `saju.domain_fortune.analyze_domain_fortune` — 연애/직업/금전 등 도메인별 흐름
- `saju.favorable_timing.analyze_favorable_timing` — 행동 유형별 유리한 시기

**LangGraph:** 후속 상담은 `app/agents/` 의 `StateGraph` 기반 **멀티-에이전트 그래프**로 처리됩니다. `router_node`가 의도를 분류한 뒤 `saju_agent_node`(상대 원국 계산) → `compat_agent_node`(궁합 분석) 등으로 위임합니다. NLG는 그래프 실행 후 `services/counselor_llm.py`에서 별도로 처리합니다.

**LLM / CLōD:** `src/backend/` 에 두는 `.env` 파일에 다음 세 값을 **모두 채우면** 초기 리딩 카피가 CLōD/OpenAI 호환 `chat/completions` 으로 생성된다. 하나라도 비어 있으면 자동 폴백이다.

| 변수 | 설명 |
|------|------|
| `CLOD_API_KEY` | 베어럴 토큰 |
| `CLOD_BASE_URL` | 게이트 베이스 URL (**끝이 `/v1`** 이어야 한다. 예: `https://your-host/.../v1`) |
| `CLOD_STRONG_MODEL` | 사용할 채팅 모델 슬러그 |

- 템플릿: [.env.example](.env.example) → 같은 디렉터리에 `.env` 로 복사한 뒤 값 입력.
- 변경 후에는 Uvicorn을 재시작한다.

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| 런타임 | Python ≥ 3.11 |
| 웹 | FastAPI, Uvicorn |
| 검증·모델 | Pydantic v2, pydantic-settings |
| 에이전트 그래프 | LangGraph (`app/agents/`) |
| 만세력 | lunar-python (`saju.saju_calculator`) |
| 규칙 해석 | PyYAML 규칙 (`app/saju/rules/*.yaml`, `rule_engine`) |
| LLM 게이트 | httpx → OpenAI 형식 `/v1/chat/completions` (`counselor_llm`) |
| 패키징 | setuptools (`app*` 및 `rules/*.yaml` package-data) |

의존성은 [`pyproject.toml`](./pyproject.toml)을 참고하세요.

---

## 디렉터리 구조 (요약)

```text
app/
  main.py              # FastAPI 앱 팩토리, 라우터 마운트
  core/config.py       # Settings (CLōD 등)
  api/                 # HTTP 라우트 (health, reading/start, chat)
  demo/                # Streamlit 등 로컬 데모 스크립트
  schemas/             # 요청/응답·상태·리포트·보드 뷰 모델 (API 계약 정렬)
  saju/                # lunar 계산 YAML 규칙 · compute 파이프
  builders/            # SajuReport(팩트+LLM)·CounselingBoard 초기 상태
  services/            # reading, counselor_llm, session_store
  agents/              # LangGraph 멀티-에이전트 그래프
    graph_state.py     # AgentGraphState TypedDict
    nodes.py           # router / saju_agent / compat_agent / fortune_agent / timing_agent 노드
    graph.py           # StateGraph 빌드 + run_counselor_graph()
tests/                 # pytest — mock JSON 스키마 검증 + `/reading/start` API
```

---

## 규칙 레이어 + NLG 레이어

- **규칙(결정론)** : `analyze_base_saju` → 같은 생년월일·시·타임존이면 같은 기둥·오행 분포·`interpretation_signals` 를 낸다 (`SajuData.calculation_metrics` 등).
- **서술(생성형)** : `build_saju_report` 텍스트는 LLM 결과에 의존하며, API 키가 없을 때만 시그널명 기반 폴백 카피를 쓴다.
- 인테이크에 시간대 필드가 없으므로 `default_timezone`(기본 서울)을 쓴다; 프로덕션 만세력/절입시 정밀 검수는 필요 시 추가한다.

---

## 로컬 실행

[uv](https://docs.astral.sh/uv/)로 가상환경과 의존성을 관리합니다. 저장소 루트가 아니라 **이 디렉터리**에서 실행합니다.

```bash
cd src/backend
cp .env.example .env   # 처음 한 번: 키·URL·모델 채운 뒤 저장 (커밋하지 않음)
uv sync
uv run uvicorn app.main:app --reload
```

- `uv sync`가 프로젝트 의존성을 받고(필요 시 `.venv` 생성), 이 패키지를 편집 가능 모드로 설치합니다.
- 셸에서 가상환경을 직접 켜두고 싶다면: `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`) 후 `uvicorn app.main:app --reload`.
- 한 번만 수동으로 맞추려면 대안으로 `uv venv` 뒤 `uv pip install -e .`를 써도 됩니다.

uv 미설치 시: 공식 안내대로 설치 후 위 명령을 다시 실행하세요.

---

## Streamlit 데모 (`/reading/start` → `/chat`)

한 터미널에서는 Uvicorn, 다른 터미널에서는 Streamlit을 켭니다.

```bash
cd src/backend
uv sync --extra demo
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# 다른 탭에서
uv run streamlit run demo/streamlit_demo.py
```

- 브라우저에서 데모 UI가 열리면 왼쪽에서 인테이크 입력 후 **전체 리딩 시작**, 오른쪽 채창에서 후속 질문을 이어 가면 됩니다.
- 베이스 URL은 사이드바에서 수정하거나, 환경 변수 `SAJU_BACKEND_URL`(기본 `http://127.0.0.1:8000`)로 지정합니다.

---

## 직접 요청해서 응답 확인하기

테스트 코드가 아니라 **본인이 터미널·브라우저에서 호출**하려면 아래 순서로 하면 됩니다.

### 1) 서버 켜기

```bash
cd src/backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2) 브라우저에서 실행 (Swagger)

1. 브라우저에서 **`http://127.0.0.1:8000/docs`** 를 연다.
2. **`GET /health`** → **Try it out** → **Execute** 하면 바디를 화면에서 볼 수 있다.
3. **`POST /reading/start`** 도 같은 방식으로, 아래 파일 내용을 **Request body**에 붙여 넣거나 복사해서 보내면 된다.
   - 요청 예시 파일: 저장소 기준 [`docs/mocks/00_start_reading_request.json`](../../docs/mocks/00_start_reading_request.json)  
     (`session_id` 는 원하면 매번 다른 문자열로 바꿔도 된다.)

응답 JSON 전체가 화면에 나오므로, mock으로 기대했던 형태(`01_initial_reading_response.json` 등)와 비교해 보면 된다. **실제 수치·문구는** 결정론 엔진과 mock 예시가 다를 수 있다.

### 3) 터미널에서 `curl` (다른 탭에서)

`src/backend` 를 작업 디렉터리로 둔다고 가정한다.

```bash
# 헬스
curl -s http://127.0.0.1:8000/health
```

예쁘게 보려면 로컬에 `jq`가 있으면:

```bash
curl -s http://127.0.0.1:8000/health | jq .
```

인테이크(mock 파일 그대로):

```bash
curl -s -X POST http://127.0.0.1:8000/reading/start \
  -H "Content-Type: application/json" \
  --data-binary @../../docs/mocks/00_start_reading_request.json | jq .
```

응답이 한 줄로만 보이면 `| jq .` 없이 실행해 보면 된다.

---

## 테스트 (`docs/mocks` 연동)

계약용 예시 JSON은 저장소 루트의 [`docs/mocks/`](../../docs/mocks/)에 있습니다. **`backend` 브랜치에는 `main`을 merge 하면** 이 디렉터리가 같이 들어옵니다(로컬에서는 `git merge origin/main`).

- `00_start_reading_request.json` — `POST /reading/start`에 넣을 수 있는 인테이크 본문
- `01` … `07` — API 계약 문서(`docs/api_contract.md` §14)에 대응하는 응답 스냅샷(스키마 검증용)

백엔드 테스트는 이 파일들을 로드해 **Pydantic 모델로 파싱되는지** 확인하고, 실제 FastAPI에는 `00` 본문(세션 ID만 테스트마다 고유하게 바꿈)으로 **`/reading/start`가 계약 타입과 맞는 응답을 내는지** 검증합니다. `_aligns_demo_mock_contract_shape` 테스트는 **`01` 예시와 같은 플래그**(`current_stage`, `recommended_tab`, 초기 `active_reading` 등)를 기대합니다.

```bash
cd src/backend
uv sync --extra dev
uv run pytest
```

- **인메모리(TestClient)** 위주: `tests/test_reading_start_api.py`, `tests/test_chat_api.py`
- **실제 HTTP**: Uvicorn 서브프로세스 + `httpx` — `tests/test_api_live_http.py` (`@pytest.mark.integration`)
  - 전체 실행 시 위 파일도 같이 돌아갑니다.
  - 통합 테스트만: `uv run pytest -m integration`
  - 통합 제외(빠른 CI 등): `uv run pytest -m "not integration"`

수동으로 API를 두드려 응답을 보는 방법은 이 문서의 **「직접 요청해서 응답 확인하기」** 절을 보면 됩니다.

환경 변수는 선택적으로 `.env`에 둘 수 있습니다 (`Settings` 참고).

---

## 프론트엔드와 맞출 때

1. **스냅샷 규칙:** 계약상 매 응답에 `saju_report` + `counseling_board` 전체가 포함됩니다. 현재는 초기 응답만 구현되어 있습니다.
2. **`semantic_key`:** 동일 키의 리딩은 업서트한다는 규칙이 계약에 정의되어 있으며, `ConversationState.readings_by_semantic_key` 등으로 확장할 여지가 있습니다.
3. **`recommended_tab` / `ui_event`:** 프론트는 보드·탭 애니메이션 힌트로 쓰되, 렌더링의 진실은 항상 스냅샷 필드에 두는 것이 계약 의도입니다.

---

## 다음 구현 후보 (우선순위 참고)

1. `POST /chat` 확장 — LangGraph 또는 서비스 레이어에서 의도·도메인 도구 라우팅 (`compatibility` / `domain_fortune` / `favorable_timing`) 후 Active Reading 템플릿 매핑, 보드·인사이트·히스토리 갱신
2. CLōD 연동 — 라우팅용 경량 모델 / 최종 답변용 강한 모델 분리 (플랜 §9.4)
3. `POST /session/reset`, `POST /demo/load`, `GET /session/{session_id}` — 데모·디버깅
4. `tests/` — `POST /chat`, `analyze_base_saju` 변형 케이스 등 추가 단위·통합 테스트

이 README는 `docs`와 코드베이스의 **현재 스냅샷**을 반영합니다. 계약이 바뀌면 `docs/api_contract.md`를 먼저 갱신한 뒤 이 문서와 구현을 맞추는 것을 권장합니다.
