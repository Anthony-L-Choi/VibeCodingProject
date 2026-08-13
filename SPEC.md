# SPEC.md — OLED 소자 특성 예측 MCP 개발

`PLAN.md`의 실행 계약을 구현 가능한 수준으로 구체화한 기술 스펙이다.
아래 4가지는 PLAN.md에 없거나 원 요구사항 문서(`OLED_Luminance_Prediction_MCP_Server_Requirements_v1.0.md`)와 부딪혀
사용자에게 확인받은 결정이다.

| 항목 | 결정 |
|---|---|
| Dataset 생성 방식 | 완전 랜덤 (물리 관계 반영 없음) |
| `predict_luminance` 입력 스키마 | EML(Host/Dopant) + 구동조건만 간소화 (7-Layer 전체 아님) |
| 입력 검증·에러 응답 | 포함 (원 문서 10.4절 공통 에러 스키마 사용) |
| 아키텍처 수준 | 최소 구현 (Model Interface 추상화 없음, CatBoost 직접 사용) |
| MCP 서버 등록 범위 | project 범위 — `.mcp.json`을 저장소에 커밋해 팀·코칭 리뷰어와 공유 (아래 6.4절 참고) |
| MCP 서버 개발 방법론 | `mcp-server-dev`(`build-mcp-server`) 스킬의 Phase 1~6 프레임워크 적용 — 최초 결론은 기존 결정과 동일 (0절 참고) |
| MCP 서버 전송 방식 | HTTP, 이 컴퓨터에서만 접근 가능한 로컬 전용(`http://127.0.0.1:8090/mcp`) — 최초 구현은 stdio였으나 사용자 요청으로 변경 (6절 참고) |

`code.claude.com/docs/ko/mcp` 문서를 참고해 Claude Code가 MCP 서버에 연결하는 방식(등록 명령·범위·환경변수)을
6.4절에 반영했다. 이 문서는 Claude Code가 클라이언트로서 서버에 *연결*하는 방법을 설명할 뿐, 서버 코드 자체를
Python으로 작성하는 방법은 다루지 않는다 — 서버 구현은 0절의 스킬 프레임워크로 결정하고 5·6절 스펙으로 구체화했다.

---

## 0. MCP 서버 개발 방법론 — `mcp-server-dev` 스킬 적용

6절(MCP 서버) 설계는 `mcp-server-dev`(`claude-plugins-official` 마켓플레이스) 플러그인의 `build-mcp-server`
스킬이 정의한 Phase 1~6 의사결정 프레임워크를 따라 도출했다. 스킬은 Phase 1에서 사용 사례를 인터뷰 형식으로
확인한 뒤 Phase 2~4에서 배포 모델·Tool 설계 패턴·프레임워크를 추천한다.

### Phase 1 — 사용 사례 인터뷰

| 질문 | 이 프로젝트의 답 |
|---|---|
| 무엇에 연결하는가? | 외부 연동 없음 — CatBoost 모델을 이용한 순수 로컬 연산 |
| 누가 쓰는가? | 본인 1인 (Capstone 과제·코칭 리뷰용, 불특정 다수 배포 대상 아님) |
| Action(Tool) 개수 | 1개 (`predict_luminance`) |
| 중간 입력/풍부한 UI 필요 여부 | 없음 — 구조화된 입력을 한 번에 받아 한 번에 응답 |
| 업스트림 인증 | 없음 |

### Phase 2~4 — 배포 모델 / Tool 패턴 / 프레임워크

| Phase | 스킬의 결정 매트릭스 적용 | 채택 |
|---|---|---|
| Phase 2 — 배포 모델 | "Just me / my team" + "Nothing external — pure logic" → **Local stdio** (개인 프로토타입 한정 권장; 스킬은 항상 "배포용으로는 MCPB가 낫다"는 캐비앗을 붙이는데, 이번 프로젝트는 배포 대상이 아니라 그 업그레이드 경로는 9절에서 명시적 비범위로 둔다) | ~~Local stdio~~ → **HTTP(로컬 전용)로 변경**. 최초엔 스킬 권장대로 stdio를 썼으나, 이후 사용자가 명시적으로 HTTP 전송을 요청해 바꿨다. 외부 공개 배포(Cloudflare Workers 등, 스킬이 말하는 "진짜" 원격 HTTP)는 아니고 `127.0.0.1`에만 바인딩한 로컬 전용 HTTP다 — 9절에 비범위로 명시. |
| Phase 3 — Tool 설계 패턴 | Action 15개 미만 → **One tool per action** | `predict_luminance` 1개만 등록 |
| Phase 4 — 프레임워크 | Python + 기존 Python 라이브러리(CatBoost) 래핑 → **FastMCP 3.x** | FastMCP |

### Phase 5~6 — 스캐폴딩 / 테스트

- **Phase 5**: Local stdio 프로토타입은 스킬에 전용 reference 파일이 없어 "인라인으로 직접 스캐폴딩"이 정해진 경로다 — `mcp_server/server.py`를 그대로 작성한다.
- **Phase 6**: 스킬의 "Anthropic Directory 제출" 체크리스트는 원격 배포 서버 대상이라 이번 스코프에 해당하지 않는다. 대신 "Claude Code에 실제로 연결해 Tool을 호출해본다"는 원칙만 적용하며, 6.4절의 등록·연결 확인 절차로 충족한다.

이 결과는 기존 6절 스펙(정상 흐름·입력 검증·에러 응답·등록 방식)과 동일하다 — 스킬의 프레임워크로 설계를
재확인한 것이며 바꾸지 않았다.

---

## 1. 범위 재확인

PLAN.md ③ 기준:

- **반드시**: Synthetic Dataset 생성 + CatBoost 모델 생성(성능 목표 없음) + `predict_luminance` MCP Tool 1개
- **안 하는 것**: `search_oled_devices`, `inverse_design_oled`, SQLite 구축, CatBoost 성능 검증(R² 기준), Feature Importance/설명가능성, Model Interface 추상화(이번 결정으로 추가)

---

## 2. 데이터 스키마

### 2.1 입력 스키마 (간소화)

원 문서의 7-Layer 전체 대신, EML(Host/Dopant)과 구동조건만 사용한다. Anode/HIL/HTL/ETL/EIL/Cathode는 이번 스코프에 없다.

```json
{
  "host_material_id": "HOST_001",
  "host_homo": -5.70,
  "host_lumo": -2.60,
  "host_t1": 2.80,
  "host_s1": 3.10,

  "dopant_material_id": "DOPANT_001",
  "dopant_homo": -5.50,
  "dopant_lumo": -2.80,
  "dopant_t1": 2.50,
  "dopant_s1": 2.90,

  "eml_thickness_nm": 30.0,
  "dopant_concentration_percent": 8.0,

  "voltage_v": 4.2,
  "current_density_ma_cm2": 10.0
}
```

필수 필드: 위 14개 전부. `null` 허용 필드 없음 (원 문서와 달리 전극 Layer가 없어 `null` 케이스가 발생하지 않음).

### 2.2 출력 스키마

```json
{ "luminance_cd_m2": 12543.2 }
```

### 2.3 값 범위 (Dataset 생성용, 검증 기준 아님)

MVP는 범위 기반 입력 검증을 하지 않는다 (원 문서 5.1절과 동일). 아래는 **랜덤 생성 시 사용할 범위**일 뿐이다.

| 필드 | 범위 |
|---|---|
| homo | -6.0 ~ -5.0 |
| lumo | -3.0 ~ -2.0 |
| t1 | 2.0 ~ 3.0 |
| s1 | 2.5 ~ 3.5 |
| eml_thickness_nm | 10 ~ 50 |
| dopant_concentration_percent | 1 ~ 15 |
| voltage_v | 3.0 ~ 6.0 |
| current_density_ma_cm2 | 1 ~ 20 |
| luminance_cd_m2 (target) | 100 ~ 30,000 (원 문서 DATA-006) |

---

## 3. Phase 1 — Synthetic Dataset 생성

**방식**: 완전 랜덤. 위 2.3 범위 내에서 각 필드를 독립적으로 균등분포(uniform)로 뽑는다.
`luminance_cd_m2`도 입력값과 무관하게 100~30,000 범위에서 독립적으로 균등분포로 뽑는다.
Material ID는 `HOST_001`~`HOST_050`, `DOPANT_001`~`DOPANT_050` 중 랜덤 선택 (풀 50개씩, 재사용 가능).

**스크립트**: `data/generate_dataset.py`
**출력**: `data/data.json` — 2.1 입력 스키마 + `device_id` + `target.luminance_cd_m2`를 가진 레코드 10,000건 배열.

```json
[
  {
    "device_id": "OLED_000001",
    "host_material_id": "HOST_012",
    "host_homo": -5.43, "host_lumo": -2.71, "host_t1": 2.65, "host_s1": 3.02,
    "dopant_material_id": "DOPANT_027",
    "dopant_homo": -5.61, "dopant_lumo": -2.44, "dopant_t1": 2.31, "dopant_s1": 2.88,
    "eml_thickness_nm": 27.4,
    "dopant_concentration_percent": 6.8,
    "voltage_v": 4.5,
    "current_density_ma_cm2": 12.3,
    "target": { "luminance_cd_m2": 18321.7 }
  }
]
```

**완료 조건 (PLAN ④-1과 동일)**: `data/data.json`에 데이터 10,000건이 있다.
**확인 방법**: `python -c "import json; print(len(json.load(open('data/data.json'))))"` → `10000` 출력.

---

## 4. Phase 2 — CatBoost 모델 학습

**입력 Feature**: 2.1의 14개 필드에서 Material ID 2개(host/dopant)를 제외한 12개 수치 Feature 사용.
(Material ID는 랜덤 생성으로 luminance와 무관하므로 CatBoost의 Categorical Feature로 포함하지 않는다 — 포함해도 무방하나 이번 스코프에서는 제외해 단순화한다.)

**Target**: `target.luminance_cd_m2`

**학습**: `models/train_model.py`
1. `data/data.json` 로드
2. 12개 Feature, 1개 Target으로 CatBoostRegressor 학습 (하이퍼파라미터는 기본값 사용, 튜닝 없음)
3. Train/Test 분리는 하되(예: 80/20), **평가 지표를 통과 기준으로 삼지 않는다** — 학습이 에러 없이 끝나고 파일이 저장되면 완료.

**출력**: `models/luminance_model.cbm`

**완료 조건 (PLAN ④-2)**: `models` 폴더에 `.cbm` 파일로 CatBoost 모델이 저장되어 있다.
**확인 방법**: `python -c "import os; assert os.path.exists('models/luminance_model.cbm')"`

---

## 5. Phase 3 — Inference 모듈

**파일**: `inference/predict.py`

**함수 시그니처**:

```python
def predict_luminance(input_data: dict) -> float:
    """input_data는 2.1 입력 스키마(14개 필드)를 따른다.
    models/luminance_model.cbm을 로드해 luminance_cd_m2를 반환한다."""
```

내부 동작: `catboost` import는 모듈 로드 시 최상단에서 즉시 한다. `.cbm` 모델 파일 로드(`model.load_model()`)만
`predict_luminance()` 첫 호출 시점까지 지연한다 → 12개 Feature 벡터로 변환 → `model.predict()` → `float` 반환.

**`catboost` import를 지연시키지 않는 이유(디버깅으로 확인된 실제 버그)**: 처음엔 "catboost import가 무거워서
서버 기동(stdio 핸드셰이크)이 타임아웃날 수 있다"고 추측해 import 자체를 `predict_luminance()` 호출 시점까지
지연시켰다. 그런데 실제로는 catboost import 자체는 1~2초로 가볍고, 문제는 다른 데 있었다 — FastMCP는 동기
Tool 함수를 `anyio.to_thread.run_sync()`로 워커 스레드에서 실행하는데, **그 워커 스레드 안에서 catboost를
처음 import하면 이벤트 루프가 동시에 stdio 비동기 I/O를 처리하는 것과 맞물려 응답 없이 멈춘다**(재현 확인 —
동일 import를 격리 실행하면 1~2초, MCP 서버 안에서 지연 import로 실행하면 응답이 아예 안 옴). import를
모듈 최상단(메인 스레드, 이벤트 루프 시작 전)으로 옮기니 3초 만에 정상 응답했다. `.cbm` 파일 로드(디스크
읽기만 하는 가벼운 작업)는 여전히 첫 호출까지 지연해도 문제가 없어 그대로 둔다.

**모델 파일 경로 해석**: `models/luminance_model.cbm` 경로는 현재 작업 디렉터리(cwd)에 의존하지 않는다.
Claude Code가 이 서버를 stdio로 실행할 때 `CLAUDE_PROJECT_DIR` 환경변수(프로젝트 루트)를 서버 프로세스에
주입해 준다(`code.claude.com/docs/ko/mcp` 참고). `os.environ.get("CLAUDE_PROJECT_DIR", ".")`를 기준으로
`models/luminance_model.cbm` 경로를 만든다 — Claude Code 밖에서(`python inference/predict.py`처럼) 직접
실행할 때는 폴백값 `"."`이 쓰인다.

**완료 조건 (PLAN ④-3)**: input 값을 넣었을 때 Luminance 결과값이 나오는 module이 존재한다.
**확인 방법**: `python -c "from inference.predict import predict_luminance; print(predict_luminance({...샘플...}))"` → 숫자 출력.

---

## 6. Phase 4 — MCP 서버

이 절의 Tool 패턴(1개)·프레임워크(FastMCP)는 0절의 `mcp-server-dev` 스킬 Phase 3~4 결정을 그대로
구체화한 것이다. 전송 방식(HTTP)만 스킬의 Phase 2 최초 권장(Local stdio)에서 사용자 요청으로 바뀌었다.

**실행 방식**: HTTP(streamable-HTTP) 기반, `127.0.0.1:8090`에만 바인딩한 로컬 전용 서버 — 이 컴퓨터
밖에서는 접근할 수 없다. 원 문서 16.1절은 stdio를 예시로 들지만 이 프로젝트에서는 HTTP로 대체했다.
Claude Code처럼 stdio 서버를 자동으로 실행해주는 클라이언트와 달리, HTTP 서버는 Claude Code가 대신
띄워주지 않는다 — **Claude Code에서 이 도구를 쓰려면 먼저 사람이 직접 서버를 실행해둬야 한다**:
```bash
py -3.12 mcp_server/server.py
```
`python`이 아니라 `py -3.12`로 실행하는 이유: 이 컴퓨터의 기본 `python`은 3.9인데 `fastmcp`/`mcp` SDK는
Python 3.10 이상이 필요하다(원 요구사항 문서에는 없던 제약이며, 이번 구현에서 Python 3.12를 새로 설치해
해결했다). `py` 런처로 버전을 고정해 어떤 셸에서 실행해도 같은 인터프리터를 쓰게 한다.

**파일**: `mcp_server/server.py`
**Tool**: `predict_luminance` 1개만 등록.

### 6.1 정상 흐름

1. Client가 `predict_luminance` Tool을 2.1 스키마의 JSON으로 호출
2. 서버가 6.2의 최소 검증 수행
3. 통과하면 `inference.predict.predict_luminance()` 호출
4. `{ "luminance_cd_m2": <float> }` 반환

### 6.2 입력 검증 (포함하기로 결정)

원 문서 5.1절 기준 — 범위 검증은 하지 않고 다음만 확인한다.

- 14개 필수 필드가 모두 존재하는가
- JSON 구조가 올바른가 (object, 배열 아님)
- 각 필드 타입이 맞는가 (`*_material_id`는 string, 나머지는 number)

검증 실패 시 6.3 에러 형식으로 응답하고 모델을 호출하지 않는다.

### 6.3 공통 에러 응답 (원 문서 10.4절 포함하기로 결정)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid predict_luminance input.",
    "details": { "field": "host_homo", "reason": "required field missing" }
  }
}
```

이번 스코프에서 실제로 발생 가능한 에러 코드:

| 코드 | 발생 조건 |
|---|---|
| `VALIDATION_ERROR` | 6.2 검증 실패 |
| `MODEL_NOT_LOADED` | `models/luminance_model.cbm` 파일이 없거나 로드 실패 |
| `INTERNAL_ERROR` | 그 외 서버 내부 예외 |

(`DATABASE_NOT_INITIALIZED`, `DATASET_NOT_FOUND`는 이번 스코프에 DB/검색이 없으므로 발생하지 않는다 — 구현하지 않는다.)

**완료 조건 (PLAN ④-4)**: MCP 서버를 실행한 뒤 `predict_luminance` Tool을 샘플 입력으로 호출하면 `luminance` 필드를 가진 응답이 온다.
**확인 방법**: MCP client(또는 stdio 테스트 스크립트)로 샘플 입력 호출 → 응답 JSON에 `luminance_cd_m2` 존재 확인. 추가로 필수 필드 하나를 빼고 호출 → `VALIDATION_ERROR` 응답 확인.

### 6.4 Claude Code 등록 및 테스트 (`code.claude.com/docs/ko/mcp` 기준)

원 요구사항 문서 11.1절의 "AI Agent" Client는 이번 프로젝트에서는 Claude Code를 가리킨다. Claude Code가
이 HTTP 서버에 연결하려면 등록이 필요하다.

**등록 방식**: project 범위. 저장소 루트에 `.mcp.json`을 커밋해 클론한 사람 누구나 같은 서버를 쓸 수 있게 한다
(local 범위는 이 컴퓨터에서만 비공개로 등록되어 코칭·발표에서 재현이 안 된다).

```json
{
  "mcpServers": {
    "oled-luminance": {
      "type": "http",
      "url": "http://127.0.0.1:8090/mcp"
    }
  }
}
```

stdio 등록과 달리 `command`/`args`/`env`가 없다 — HTTP 서버는 Claude Code가 대신 실행해주지 않으므로,
연결하기 전에 사람이 먼저 `py -3.12 mcp_server/server.py`로 서버를 띄워둬야 한다(위 "실행 방식" 참고).
서버가 안 떠 있으면 `claude mcp list`에서 연결 실패로 뜬다.

CLI로 동일하게 등록할 수도 있다:

```bash
claude mcp add --transport http --scope project oled-luminance http://127.0.0.1:8090/mcp
```

**최초 승인**: project 범위 서버는 처음 쓸 때 신뢰 승인이 필요하다. Claude Code를 대화형으로 한 번 실행해
승인 대화상자를 통과해야 `claude mcp list`에 "⏸ 승인 대기 중"이 아니라 정상 연결로 뜬다.

**연결 확인**:

```bash
claude mcp list        # oled-luminance가 나열되는지
claude mcp get oled-luminance
```

Claude Code 세션 안에서는 `/mcp`로 연결 상태와 노출된 Tool 개수(1개)를 확인한다.

**Tool 설명 작성 규칙**: `predict_luminance`의 `description`은 Tool Search가 언제 이 도구를 찾아 쓸지
판단하는 근거이므로, 무엇을 예측하는지·언제 쓰는지를 앞부분에 명확히 적는다 (2KB 넘으면 잘린다 — 이번
스코프에서는 문제되지 않는 길이).

---

## 7. 디렉터리 구조 (최소 구현)

```text
practice/
├── PLAN.md
├── SPEC.md
├── OLED_Luminance_Prediction_MCP_Server_Requirements_v1.0.md
├── requirements.txt
├── .mcp.json
│
├── data/
│   ├── generate_dataset.py
│   └── data.json
│
├── models/
│   ├── train_model.py
│   └── luminance_model.cbm
│
├── inference/
│   └── predict.py
│
└── mcp_server/
    └── server.py
```

`search_oled_devices`, `inverse_design_oled`용 폴더(예: SQLite, services, tools 하위구조)는 만들지 않는다.
Model Interface 추상화 레이어(원 문서 9.2절)도 만들지 않는다 — `train_model.py`와 `predict.py`가 CatBoost API를 직접 호출한다.

---

## 8. Phase별 검증 요약 (PLAN ⑤ 그대로)

| Phase | 완료 조건 | 확인 명령 |
|---|---|---|
| 1 | `data/data.json` 10,000건 | `python -c "import json;print(len(json.load(open('data/data.json'))))"` |
| 2 | `models/*.cbm` 존재 | `python -c "import os;assert os.path.exists('models/luminance_model.cbm')"` |
| 3 | `predict_luminance()` 호출 시 숫자 반환 | `python -c "from inference.predict import predict_luminance; print(predict_luminance({...}))"` |
| 4 | MCP Tool 호출 시 `luminance_cd_m2` 필드 응답 | MCP client로 샘플 호출 |
| 4-등록 | Claude Code가 서버에 연결됨 | `claude mcp list`에 `oled-luminance` 표시, 세션 내 `/mcp`로 확인 |

사람이 눈으로 보는 것: 없음 (PLAN ⑤와 동일)
승인 지점: Git 커밋/초기화 시점 (이미 완료 — `e51dbbb`)

---

## 9. 명시적 비범위 (원 문서 대비)

- 7-Layer 전체 구조 입력 (Anode/HIL/HTL/ETL/EIL/Cathode) — 이번엔 EML+구동조건만
- SQLite DB, `search_oled_devices`
- `inverse_design_oled`, 역설계 후보 생성
- CatBoost 성능 평가(R² 기준), Train/Validation/Test 3분할 (Train/Test 2분할만 사용)
- Feature Importance, SHAP, 설명가능성
- Model Interface 추상화 (LightGBM/XGBoost/NN 교체 가능 구조)
- 물리 관계를 반영한 Dataset 생성 (완전 랜덤으로 결정)
- 외부에서 접근 가능한 공개 배포 (Cloudflare Workers 등) — HTTP 전송은 쓰지만 `127.0.0.1`에만 바인딩한 로컬 전용이다. 스킬이 말하는 "진짜" 원격 HTTP(누구나 URL로 접속)는 아니다.
- SSE 전송 (streamable-HTTP만 사용)
- OAuth 등 원격 서버 인증 (로컬 전용이라 외부 노출이 없어 해당 없음)
- local/user 범위 등록 (project 범위 `.mcp.json` 하나만 쓴다)
- MCPB 패키징 — `mcp-server-dev` 스킬이 Local stdio 선택 시 항상 권장하는 배포 업그레이드 경로(0절 Phase 2 참고). 이 프로젝트는 배포 대상이 아닌 개인 프로토타입이라 비범위로 둔다.
- Anthropic Directory 제출, 원격 커넥터로서의 리뷰 기준 통과 (스킬 Phase 6은 진짜 원격 배포 서버 대상 — 이 프로젝트는 로컬 전용이라 해당 없음)
