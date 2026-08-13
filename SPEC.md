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

필수 필드: 위 13개 전부. `null` 허용 필드 없음 (원 문서와 달리 전극 Layer가 없어 `null` 케이스가 발생하지 않음).

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

**입력 Feature**: 2.1의 13개 필드에서 Material ID 2개(host/dopant)를 제외한 11개 수치 Feature 사용.
(Material ID는 랜덤 생성으로 luminance와 무관하므로 CatBoost의 Categorical Feature로 포함하지 않는다 — 포함해도 무방하나 이번 스코프에서는 제외해 단순화한다.)

**Target**: `target.luminance_cd_m2`

**학습**: `models/train_model.py`
1. `data/data.json` 로드
2. 11개 Feature, 1개 Target으로 CatBoostRegressor 학습 (하이퍼파라미터는 기본값 사용, 튜닝 없음)
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
    """input_data는 2.1 입력 스키마(13개 필드)를 따른다.
    models/luminance_model.cbm을 로드해 luminance_cd_m2를 반환한다."""
```

내부 동작: 모델 로드(모듈 임포트 시 1회) → 11개 Feature 벡터로 변환 → `model.predict()` → `float` 반환.

**완료 조건 (PLAN ④-3)**: input 값을 넣었을 때 Luminance 결과값이 나오는 module이 존재한다.
**확인 방법**: `python -c "from inference.predict import predict_luminance; print(predict_luminance({...샘플...}))"` → 숫자 출력.

---

## 6. Phase 4 — MCP 서버

**실행 방식**: stdio 기반 (원 문서 16.1절과 동일)
**파일**: `mcp_server/server.py`
**Tool**: `predict_luminance` 1개만 등록.

### 6.1 정상 흐름

1. Client가 `predict_luminance` Tool을 2.1 스키마의 JSON으로 호출
2. 서버가 6.2의 최소 검증 수행
3. 통과하면 `inference.predict.predict_luminance()` 호출
4. `{ "luminance_cd_m2": <float> }` 반환

### 6.2 입력 검증 (포함하기로 결정)

원 문서 5.1절 기준 — 범위 검증은 하지 않고 다음만 확인한다.

- 13개 필수 필드가 모두 존재하는가
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

---

## 7. 디렉터리 구조 (최소 구현)

```text
practice/
├── PLAN.md
├── SPEC.md
├── OLED_Luminance_Prediction_MCP_Server_Requirements_v1.0.md
├── requirements.txt
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
- HTTP/SSE 등 stdio 외 실행 방식
