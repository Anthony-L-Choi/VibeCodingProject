# OLED Luminance Prediction MCP Server 요구사항 정의서 v1.0

## 1. 프로젝트 개요

### 1.1 목적

OLED 소자의 7-Layer 구조 및 각 Layer의 Material, Material Property, Device Structure 정보와 구동 조건을 입력받아 OLED의 **Luminance (cd/m²)**를 예측하는 MCP 서버를 구축한다.

MCP 서버는 다음 세 가지 핵심 기능을 제공한다.

1. Luminance 예측
2. OLED 데이터 검색
3. Luminance 목표 기반 OLED 역설계

서버는 AI Agent와 일반 Application 모두에서 사용할 수 있도록 MCP 표준 Tool Interface를 제공한다.

---

## 2. 시스템 구성

```text
                         ┌──────────────────────┐
                         │      MCP Client      │
                         │                      │
                         │ ChatGPT / Claude     │
                         │ Custom Application   │
                         └──────────┬───────────┘
                                    │
                                    │ MCP
                                    ▼
                    ┌─────────────────────────────┐
                    │      OLED MCP Server        │
                    │          Python             │
                    │                             │
                    │ ┌─────────────────────────┐ │
                    │ │ Prediction Service      │ │
                    │ └────────────┬────────────┘ │
                    │              │              │
                    │ ┌────────────▼────────────┐ │
                    │ │ Model Interface         │ │
                    │ │                          │ │
                    │ │ CatBoost Model           │ │
                    │ └─────────────────────────┘ │
                    │                             │
                    │ ┌─────────────────────────┐ │
                    │ │ Search Service           │ │
                    │ └────────────┬────────────┘ │
                    │              │              │
                    │ ┌────────────▼────────────┐ │
                    │ │ Inverse Design Service  │ │
                    │ └────────────┬────────────┘ │
                    └──────────────┼──────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
             ┌─────────────┐              ┌─────────────┐
             │ SQLite DB   │              │ JSON Dataset│
             │             │              │             │
             │ Search      │              │ 100,000     │
             │             │              │ OLED devices│
             └─────────────┘              └─────────────┘
```

---

## 3. OLED Device 데이터 모델

### 3.1 고정 Device Structure

모든 데이터는 동일한 7-Layer 구조를 사용한다.

```text
Anode
  ↓
HIL
  ↓
HTL
  ↓
EML
  ↓
ETL
  ↓
EIL
  ↓
Cathode
```

EML은 예외적으로 Host와 Dopant를 별도로 가진다.

```text
EML
├── Host
└── Dopant
```

### 3.2 Layer 데이터 구조

일반 Layer는 다음 세 가지 정보를 가진다.

```text
Layer
├── Material
├── Material Property
└── Device Structure
```

#### Material

```json
{
  "material_id": "HTL_001",
  "material_name": "HTL_Material_001"
}
```

#### Material Property

사용하는 Material Property는 다음 네 가지로 제한한다.

- HOMO
- LUMO
- T1
- S1

예:

```json
{
  "homo": -5.40,
  "lumo": -2.20,
  "t1": null,
  "s1": null
}
```

전극 등 일부 Layer에서 의미가 없는 Property는 `null`로 표현한다.

#### Device Structure

```json
{
  "thickness_nm": 40.0
}
```

---

## 4. EML 데이터 구조

EML은 Host와 Dopant를 별도로 가진다.

```json
{
  "layer_type": "EML",

  "host": {
    "material_id": "HOST_001",
    "material_name": "Host_001",

    "material_properties": {
      "homo": -5.70,
      "lumo": -2.60,
      "t1": 2.80,
      "s1": 3.10
    }
  },

  "dopant": {
    "material_id": "DOPANT_001",
    "material_name": "Dopant_001",

    "material_properties": {
      "homo": -5.50,
      "lumo": -2.80,
      "t1": 2.50,
      "s1": 2.90
    }
  },

  "device_structure": {
    "thickness_nm": 30.0,
    "dopant_concentration_percent": 8.0
  }
}
```

---

## 5. Operating Condition

OLED Device에는 다음 구동 조건을 포함한다.

```json
{
  "operating_condition": {
    "voltage_v": 4.2,
    "current_density_ma_cm2": 10.0
  }
}
```

동일한 OLED 구조라도 Operating Condition에 따라 서로 다른 Luminance를 가질 수 있다.

### 5.1 입력값 허용 범위

MVP에서는 각 입력값에 대해 별도의 허용 범위를 정의하지 않는다.

서버는 다음 항목만 검증한다.

- 필수 필드 존재 여부
- JSON 구조
- 데이터 타입
- `null` 허용 여부

즉, HOMO/LUMO/T1/S1, Layer Thickness, Dopant Concentration, Voltage, Current Density 등에 대해 최소/최대 범위 기반 검증은 수행하지 않는다.

---

## 6. Target

ML의 Prediction Target은 단일 값이다.

```json
{
  "target": {
    "luminance_cd_m2": 12543.2
  }
}
```

Synthetic Dataset의 Target 범위는 다음과 같다.

**100 ~ 30,000 cd/m²**

---

## 7. Synthetic Dataset

현재 실제 실험 데이터가 없기 때문에 **100,000건의 Synthetic OLED Dataset**을 생성한다.

단순 Random Dataset이 아니라 OLED 물성 및 소자 구조 사이의 관계를 반영한 Synthetic Dataset으로 생성한다.

개념적인 관계는 다음과 같다.

```text
HOMO/LUMO
     ↓
Energy Level Alignment
     ↓
Charge Injection / Transport
     ↓
EML Recombination
     ↓
Luminance
```

주요 영향 요소에는 다음이 포함된다.

- Material HOMO/LUMO
- Host/Dopant T1/S1
- Layer Thickness
- Dopant Concentration
- EML 조건
- Voltage
- Current Density
- Layer 간 Energy Level Alignment

### 7.1 Dataset 구성

```text
Total       100,000
Train        70,000
Validation   15,000
Test         15,000
```

---

## 8. JSON Dataset 저장

원본 Dataset은 **JSON 파일 하나**로 저장한다.

```text
data/
└── oled_dataset.json
```

예상 구조:

```json
[
  {
    "device_id": "OLED_000001",
    "layers": [],
    "operating_condition": {
      "voltage_v": 4.2,
      "current_density_ma_cm2": 10.0
    },
    "target": {
      "luminance_cd_m2": 12543.2
    }
  },
  {
    "device_id": "OLED_000002",
    "layers": [],
    "operating_condition": {
      "voltage_v": 4.5,
      "current_density_ma_cm2": 12.0
    },
    "target": {
      "luminance_cd_m2": 18321.7
    }
  }
]
```

JSON은 원본/배포 데이터로 사용하고, 검색 성능을 위해 초기화 과정에서 SQLite DB로 적재한다.

```text
oled_dataset.json
       │
       │ import
       ▼
SQLite DB
       │
       ├── Search
       └── Inverse Design candidate source
```

### 8.1 SQLite DB Schema

SQLite DB는 검색 성능과 구현 단순성을 위해 원본 OLED JSON을 보존하면서 주요 검색 필드를 별도 컬럼으로 저장한다.

#### `devices`

```sql
CREATE TABLE devices (
  device_id TEXT PRIMARY KEY,
  voltage_v REAL NOT NULL,
  current_density_ma_cm2 REAL NOT NULL,
  luminance_cd_m2 REAL NOT NULL,
  host_material_id TEXT NOT NULL,
  host_material_name TEXT NOT NULL,
  dopant_material_id TEXT NOT NULL,
  dopant_material_name TEXT NOT NULL,
  dopant_concentration_percent REAL NOT NULL,
  eml_thickness_nm REAL NOT NULL,
  device_json TEXT NOT NULL
);
```

#### `layers`

```sql
CREATE TABLE layers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT NOT NULL,
  layer_type TEXT NOT NULL,
  material_id TEXT,
  material_name TEXT,
  homo REAL,
  lumo REAL,
  t1 REAL,
  s1 REAL,
  thickness_nm REAL,
  dopant_concentration_percent REAL,
  FOREIGN KEY (device_id) REFERENCES devices(device_id)
);
```

#### Index

```sql
CREATE INDEX idx_devices_luminance ON devices(luminance_cd_m2);
CREATE INDEX idx_devices_host ON devices(host_material_id);
CREATE INDEX idx_devices_dopant ON devices(dopant_material_id);
CREATE INDEX idx_devices_eml_thickness ON devices(eml_thickness_nm);
CREATE INDEX idx_devices_operating_condition
  ON devices(voltage_v, current_density_ma_cm2);
```

---

## 9. ML 모델

### 9.1 Initial Model

첫 번째 모델은 **CatBoost**를 사용한다.

```text
OLED JSON
    ↓
Feature Extraction
    ↓
Feature Vector
    ↓
CatBoost
    ↓
Luminance
```

### 9.2 Model Abstraction

MCP Server가 특정 ML 프레임워크에 직접 종속되지 않도록 Model Interface를 둔다.

```text
Prediction Service
       │
       ▼
Model Interface
       │
       ├── CatBoost
       ├── LightGBM
       ├── XGBoost
       └── Neural Network
```

향후 모델을 교체해도 MCP Tool Interface는 변경하지 않는 것을 목표로 한다.

---

## 10. MCP Tool

초기 버전에서는 다음 3개의 핵심 Tool을 제공한다.

### 10.1 `predict_luminance`

#### 목적

주어진 OLED Device의 Luminance를 예측한다.

#### Input

7-Layer OLED Device JSON

예:

```json
{
  "device_id": "OLED_INPUT_001",
  "layers": [
    {
      "layer_type": "Anode",
      "material": {
        "material_id": "ANODE_001",
        "material_name": "ITO"
      },
      "material_properties": {
        "homo": null,
        "lumo": null,
        "t1": null,
        "s1": null
      },
      "device_structure": {
        "thickness_nm": 120.0
      }
    },
    {
      "layer_type": "HIL",
      "material": {
        "material_id": "HIL_001",
        "material_name": "HIL_Material_001"
      },
      "material_properties": {
        "homo": -5.30,
        "lumo": -2.10,
        "t1": null,
        "s1": null
      },
      "device_structure": {
        "thickness_nm": 20.0
      }
    },
    {
      "layer_type": "HTL",
      "material": {
        "material_id": "HTL_001",
        "material_name": "HTL_Material_001"
      },
      "material_properties": {
        "homo": -5.40,
        "lumo": -2.20,
        "t1": null,
        "s1": null
      },
      "device_structure": {
        "thickness_nm": 40.0
      }
    },
    {
      "layer_type": "EML",
      "host": {
        "material_id": "HOST_001",
        "material_name": "Host_001",
        "material_properties": {
          "homo": -5.70,
          "lumo": -2.60,
          "t1": 2.80,
          "s1": 3.10
        }
      },
      "dopant": {
        "material_id": "DOPANT_001",
        "material_name": "Dopant_001",
        "material_properties": {
          "homo": -5.50,
          "lumo": -2.80,
          "t1": 2.50,
          "s1": 2.90
        }
      },
      "device_structure": {
        "thickness_nm": 30.0,
        "dopant_concentration_percent": 8.0
      }
    },
    {
      "layer_type": "ETL",
      "material": {
        "material_id": "ETL_001",
        "material_name": "ETL_Material_001"
      },
      "material_properties": {
        "homo": -6.10,
        "lumo": -2.90,
        "t1": null,
        "s1": null
      },
      "device_structure": {
        "thickness_nm": 35.0
      }
    },
    {
      "layer_type": "EIL",
      "material": {
        "material_id": "EIL_001",
        "material_name": "EIL_Material_001"
      },
      "material_properties": {
        "homo": null,
        "lumo": -3.00,
        "t1": null,
        "s1": null
      },
      "device_structure": {
        "thickness_nm": 5.0
      }
    },
    {
      "layer_type": "Cathode",
      "material": {
        "material_id": "CATHODE_001",
        "material_name": "Al"
      },
      "material_properties": {
        "homo": null,
        "lumo": null,
        "t1": null,
        "s1": null
      },
      "device_structure": {
        "thickness_nm": 100.0
      }
    }
  ],
  "operating_condition": {
    "voltage_v": 4.2,
    "current_density_ma_cm2": 10.0
  }
}
```

`predict_luminance` 입력에서 `device_id`는 선택값이다. Dataset 저장 레코드에서는 `device_id`를 필수로 사용한다.

#### Output

```json
{
  "luminance_cd_m2": 12543.2
}
```

#### 제외사항

Prediction 결과에는 다음 정보를 포함하지 않는다.

- Feature Importance
- SHAP
- 주요 Feature
- Prediction Explanation
- 상세 모델 분석

즉, 기본 Tool은 **예측값만 반환**한다.

---

### 10.2 `search_oled_devices`

#### 목적

SQLite에 저장된 OLED Device 데이터를 조건으로 검색한다.

예시 질의:

- Luminance가 20,000 이상인 OLED 검색
- 특정 Dopant를 사용한 OLED 검색
- EML Thickness가 30 nm인 OLED 검색
- 특정 조건에서 Luminance가 높은 OLED 검색

#### 주요 검색 조건

```text
Device ID
Host
Dopant
Dopant Concentration
EML Thickness
Voltage
Current Density
Luminance
```

`host`와 `dopant` 검색 조건은 기본적으로 Material ID를 기준으로 한다.

#### Input

검색 연산자는 다음을 지원한다.

```text
eq   Exact match
gte  Greater than or equal
lte  Less than or equal
```

`gte`와 `lte`를 함께 사용하면 구간 검색으로 처리한다.

예:

```json
{
  "filters": {
    "device_id": {
      "eq": "OLED_083421"
    },
    "host": {
      "eq": "HOST_012"
    },
    "dopant": {
      "eq": "DOPANT_015"
    },
    "dopant_concentration_percent": {
      "gte": 5.0,
      "lte": 10.0
    },
    "eml_thickness_nm": {
      "eq": 30.0
    },
    "voltage_v": {
      "gte": 4.0,
      "lte": 5.0
    },
    "current_density_ma_cm2": {
      "gte": 10.0
    },
    "luminance_cd_m2": {
      "gte": 20000.0
    }
  },
  "sort_by": "luminance_cd_m2",
  "sort_order": "desc",
  "limit": 10,
  "offset": 0,
  "include_device_json": false
}
```

`sort_by`는 다음 값만 허용한다.

```text
device_id
luminance_cd_m2
eml_thickness_nm
dopant_concentration_percent
voltage_v
current_density_ma_cm2
```

`sort_order`는 `asc` 또는 `desc`를 사용한다.

#### Output 예시

```json
{
  "total_count": 1,
  "results": [
    {
      "device_id": "OLED_083421",
      "luminance_cd_m2": 28542.1,
      "host": "HOST_012",
      "dopant": "DOPANT_015",
      "dopant_concentration_percent": 8.2,
      "eml_thickness_nm": 30.0,
      "voltage_v": 4.5,
      "current_density_ma_cm2": 12.0
    }
  ]
}
```

검색 결과 개수를 제한할 수 있도록 `limit`을 제공한다. 기본값은 `10`, 최대값은 `100`으로 한다. `offset`은 기본값 `0`을 사용한다.

`total_count`는 `limit`과 `offset`을 적용하기 전 조건에 맞는 전체 결과 개수이다.

`include_device_json`이 `true`인 경우 각 결과에 원본 OLED Device JSON을 `device` 필드로 포함한다. 기본값은 `false`이며, 기본 출력은 요약 정보만 반환한다.

검색 결과가 없는 경우 오류로 처리하지 않고 다음과 같이 빈 배열을 반환한다.

```json
{
  "total_count": 0,
  "results": []
}
```

---

### 10.3 `inverse_design_oled`

#### 목적

사용자가 원하는 Target Luminance를 입력하면 목표를 만족할 가능성이 높은 EML 조건을 탐색한다.

#### 역설계에서 변경 가능한 영역

Anode, HIL, HTL, ETL, EIL, Cathode는 고정한다.

EML의 다음 요소를 변경 대상으로 한다.

```text
EML
├── Host
├── Dopant
├── Host HOMO
├── Host LUMO
├── Host T1
├── Host S1
├── Dopant HOMO
├── Dopant LUMO
├── Dopant T1
├── Dopant S1
├── EML Thickness
└── Dopant Concentration
```

다만 Material ID와 Material Property를 완전히 독립적으로 변경하지 않는다.

권장 방식:

```text
Host ID
   ↓
Host Material Property 자동 결정

Dopant ID
   ↓
Dopant Material Property 자동 결정
```

따라서 실제 역설계 변수는 다음과 같이 정의한다.

```text
Host Material
Dopant Material
EML Thickness
Dopant Concentration
```

HOMO/LUMO/T1/S1은 선택된 Material에서 파생되는 값으로 처리한다.

### 역설계 목표

MVP에서는 **Luminance 하나만 목표로 사용한다.**

예:

```json
{
  "target_luminance_cd_m2": 25000,
  "number_of_candidates": 5
}
```

목표 만족 기준은 다음과 같이 정의한다.

```text
predicted_luminance_cd_m2 >= target_luminance_cd_m2
```

즉, 예측 Luminance가 사용자가 입력한 Target Luminance 이상이면 목표를 만족한 후보로 간주한다.

### 역설계 후보 생성 범위

MVP에서는 역설계 후보 생성 범위를 별도로 정의하지 않는다.

후보 생성 시 Host Material, Dopant Material, EML Thickness, Dopant Concentration에 대해 요구사항 수준의 고정 최소/최대 범위 또는 간격을 두지 않는다.

### 역설계 알고리즘

초기 버전에서는 Candidate Generation + CatBoost Prediction 방식으로 구현한다.

```text
Target Luminance
       │
       ▼
Candidate Generation
       │
       ▼
EML Parameter Combination
       │
       ▼
Feature Extraction
       │
       ▼
CatBoost Prediction
       │
       ▼
Target 만족 여부
       │
       ├── No → 다음 후보
       │
       └── Yes
             ↓
        Candidate Ranking
             ↓
        Top N 반환
```

예:

```text
Target = 25,000 cd/m²

Candidate 1 → 29,421
Candidate 2 → 28,753
Candidate 3 → 27,821
Candidate 4 → 26,932
Candidate 5 → 25,417
```

#### Output

```json
{
  "target_luminance_cd_m2": 25000,
  "candidates": [
    {
      "rank": 1,
      "predicted_luminance_cd_m2": 29421.0,
      "host": "HOST_012",
      "dopant": "DOPANT_015",
      "eml_thickness_nm": 30.0,
      "dopant_concentration_percent": 8.2
    },
    {
      "rank": 2,
      "predicted_luminance_cd_m2": 28753.0,
      "host": "HOST_009",
      "dopant": "DOPANT_021",
      "eml_thickness_nm": 32.0,
      "dopant_concentration_percent": 7.5
    }
  ]
}
```

후보 정렬은 `predicted_luminance_cd_m2` 기준 내림차순으로 한다.

---

### 10.4 Common Error Response

모든 MCP Tool은 오류 발생 시 다음 공통 형식으로 응답한다.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid OLED device input.",
    "details": {
      "field": "layers",
      "reason": "7 layers are required."
    }
  }
}
```

#### Error Code

```text
VALIDATION_ERROR         Input JSON 구조, 필수 필드, 타입 검증 실패
MODEL_NOT_LOADED         CatBoost 모델 파일 로드 실패 또는 미로드 상태
DATABASE_NOT_INITIALIZED SQLite DB 파일 없음 또는 초기화 실패
DATASET_NOT_FOUND        JSON Dataset 파일 없음
INTERNAL_ERROR           기타 서버 내부 오류
```

검색 결과가 없는 경우와 역설계 목표를 만족하는 후보가 없는 경우는 시스템 오류로 처리하지 않는다.

검색 결과가 없으면 `search_oled_devices`는 `results: []`를 반환한다.

역설계 후보가 없으면 `inverse_design_oled`는 다음과 같이 빈 후보 목록을 반환한다.

```json
{
  "target_luminance_cd_m2": 25000,
  "candidates": []
}
```

---

## 11. MCP Client

MCP Server의 최종 사용자는 다음 두 유형을 모두 지원한다.

### 11.1 AI Agent

예:

> HOST_015와 DOPANT_007을 사용한 OLED의 Luminance를 예측해줘.

AI Agent가 `predict_luminance` Tool을 호출한다.

### 11.2 일반 Application

Python, C++, Web Application 등의 프로그램이 MCP Protocol을 통해 동일한 Tool을 호출할 수 있어야 한다.

```text
Application
    ↓
MCP
    ↓
OLED MCP Server
    ↓
MCP Tool
    ↓
Prediction / Search / Inverse Design
```

Natural Language Client와 Programmatic Client 모두 동일한 Tool Interface를 사용한다.

---

## 12. Python 프로젝트 구조

권장 프로젝트 구조:

```text
oled_mcp_server/
│
├── server/
│   ├── mcp_server.py
│   ├── tools/
│   │   ├── predict.py
│   │   ├── search.py
│   │   └── inverse_design.py
│   │
│   ├── services/
│   │   ├── prediction_service.py
│   │   ├── search_service.py
│   │   └── inverse_design_service.py
│   │
│   ├── models/
│   │   ├── base_model.py
│   │   └── catboost_model.py
│   │
│   ├── data/
│   │   ├── json_loader.py
│   │   └── sqlite_repository.py
│   │
│   └── schemas/
│       └── oled_schema.py
│
├── data/
│   └── oled_dataset.json
│
├── database/
│   └── oled.db
│
├── model/
│   └── catboost/
│       └── luminance_model.cbm
│
├── training/
│   ├── feature_engineering.py
│   ├── train.py
│   └── evaluate.py
│
├── scripts/
│   └── import_json_to_sqlite.py
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

## 13. Functional Requirements

| ID | 요구사항 | 상태 |
|---|---|---|
| FR-001 | 7-Layer OLED JSON 입력 | 확정 |
| FR-002 | Layer별 Material 정보 | 확정 |
| FR-003 | Layer별 Material Property | 확정 |
| FR-004 | Layer별 Device Structure 정보 | 확정 |
| FR-005 | EML Host/Dopant 구조 | 확정 |
| FR-006 | Operating Condition 입력 | 확정 |
| FR-007 | Luminance Prediction | 확정 |
| FR-008 | OLED 데이터 Search | 확정 |
| FR-009 | 조건 기반 Search | 확정 |
| FR-010 | Luminance 기반 Inverse Design | 확정 |
| FR-011 | EML 조건 변경 기반 Inverse Design | 확정 |
| FR-012 | AI Agent MCP Client 지원 | 확정 |
| FR-013 | Application MCP Client 지원 | 확정 |
| FR-014 | `predict_luminance` 전체 7-Layer 입력 예시 제공 | 확정 |
| FR-015 | Search 연산자, 정렬, limit, offset 제공 | 확정 |
| FR-016 | Search 결과 원본 Device JSON 선택 반환 | 확정 |

---

## 14. ML Requirements

| ID | 요구사항 | 상태 |
|---|---|---|
| ML-001 | Synthetic Dataset 100,000건 | 확정 |
| ML-002 | CatBoost 사용 | 확정 |
| ML-003 | Model Abstraction 적용 | 확정 |
| ML-004 | 향후 다른 ML Model로 교체 가능 | 확정 |
| ML-005 | Train/Validation/Test 분리 | 확정 |
| ML-006 | CatBoost 모델 평가 기준 R² 0.90 이상 | 확정 |

Dataset Split:

```text
Train       70,000
Validation  15,000
Test        15,000
```

### 14.1 Model Evaluation Criteria

CatBoost 모델의 MVP 통과 기준은 Test Dataset 기준 **R² 0.90 이상**으로 한다.

```text
R² >= 0.90
```

---

## 15. Data Requirements

| ID | 요구사항 | 상태 |
|---|---|---|
| DATA-001 | JSON 단일 파일 | 확정 |
| DATA-002 | SQLite 검색 DB | 확정 |
| DATA-003 | 7-Layer 고정 구조 | 확정 |
| DATA-004 | EML Host + Dopant | 확정 |
| DATA-005 | Material Property는 HOMO/LUMO/T1/S1 | 확정 |
| DATA-006 | Luminance 100~30,000 cd/m² | 확정 |
| DATA-007 | Operating Condition 포함 | 확정 |
| DATA-008 | Synthetic Dataset | 확정 |
| DATA-009 | SQLite `devices`, `layers` Schema 정의 | 확정 |

---

## 16. MCP Requirements

| ID | 요구사항 | 상태 |
|---|---|---|
| MCP-001 | `predict_luminance` 제공 | 확정 |
| MCP-002 | `search_oled_devices` 제공 | 확정 |
| MCP-003 | `inverse_design_oled` 제공 | 확정 |
| MCP-004 | AI Agent 사용 지원 | 확정 |
| MCP-005 | 일반 Application 사용 지원 | 확정 |
| MCP-006 | MCP Tool에서 Model 구현 세부사항 비노출 | 확정 |
| MCP-007 | MCP 서버 기본 실행 방식은 stdio 기반 | 확정 |
| MCP-008 | MCP Tool 공통 오류 응답 형식 제공 | 확정 |

### 16.1 MCP Server Execution Mode

MVP에서는 일반적으로 많이 사용되는 **stdio 기반 MCP Server** 방식으로 실행한다.

HTTP/SSE 등 다른 실행 방식은 MVP 필수 범위에 포함하지 않는다.

---

## 17. 기술 스택

| 영역 | 기술 |
|---|---|
| MCP Server | Python |
| ML | CatBoost |
| Search DB | SQLite |
| Raw Dataset | JSON |
| Dataset Size | 100,000 records |
| Target | Luminance (cd/m²) |
| Device Structure | 7-Layer |
| MCP Client | AI Agent + Application |
| MCP Execution Mode | stdio |
| Model Architecture | Model Interface 기반 교체 가능 구조 |

---

## 18. MVP 개발 순서

개발은 다음 순서로 진행하는 것을 권장한다.

### Phase 1. Synthetic Dataset 생성

1. Material Pool 생성
2. 7-Layer 구조 정의
3. Host/Dopant Material Pool 생성
4. HOMO/LUMO/T1/S1 생성
5. Layer Thickness 생성
6. Dopant Concentration 생성
7. Voltage / Current Density 생성
8. OLED 물리 관계를 반영한 Luminance 생성
9. 100,000건 Dataset 생성
10. JSON 파일 저장

### Phase 2. SQLite 구축

```text
oled_dataset.json
       ↓
JSON Loader
       ↓
SQLite
       ↓
Search Repository
```

SQLite는 `devices`, `layers` 테이블과 주요 검색 필드 index를 포함한다.

### Phase 3. CatBoost Model

```text
JSON Dataset
     ↓
Feature Engineering
     ↓
Train / Validation / Test
     ↓
CatBoost Training
     ↓
Evaluation
     ↓
luminance_model.cbm
```

### Phase 4. Prediction Service

```text
OLED JSON
    ↓
Validation
    ↓
Feature Engineering
    ↓
CatBoost
    ↓
Luminance
```

### Phase 5. MCP Server

세 가지 Tool을 구현한다.

```text
predict_luminance
search_oled_devices
inverse_design_oled
```

### Phase 6. Integration Test

다음 Client에서 MCP Server를 테스트한다.

```text
AI Agent
   +
Python Application
```

MVP 테스트 완료 기준은 세 가지 MCP Tool 단위 테스트를 모두 통과하는 것이다.

```text
predict_luminance      PASS
search_oled_devices    PASS
inverse_design_oled    PASS
```

단위 테스트는 정상 입력, validation 오류, 모델/DB 미초기화 오류, 빈 검색 결과, 빈 역설계 후보 결과를 포함한다.

---

## 19. 향후 확장 가능성

현재 MVP에서는 Luminance 하나만 예측하지만, 구조적으로 향후 다음 Target을 추가할 수 있도록 설계한다.

예:

- Current Efficiency (cd/A)
- Power Efficiency (lm/W)
- EQE (%)
- Operating Voltage
- Lifetime
- CIE Color Coordinates

또한 향후 다음 기능으로 확장할 수 있다.

- Multi-objective Optimization
- Bayesian Optimization
- Explainable AI
- 신규 Material 예측
- Material Recommendation
- Device Structure Optimization
- 실험 데이터 기반 모델 재학습
- 실험 결과 자동 저장

단, 이러한 기능은 현재 MVP 범위에는 포함하지 않는다.

---

## 20. MVP 범위 요약

최초 구현 버전의 핵심 범위는 다음과 같다.

```text
┌─────────────────────────────────────────────┐
│          OLED Luminance MCP Server          │
├─────────────────────────────────────────────┤
│                                             │
│  7-Layer OLED Device                       │
│       ↓                                     │
│  Material / Property / Structure            │
│       ↓                                     │
│  Operating Condition                        │
│       ↓                                     │
│  ┌───────────────────────────────────────┐  │
│  │              MCP Server               │  │
│  │                                       │  │
│  │  predict_luminance                    │  │
│  │  search_oled_devices                  │  │
│  │  inverse_design_oled                  │  │
│  └───────────────────────────────────────┘  │
│       ↓                  ↓                  │
│   CatBoost            SQLite               │
│       ↓                  ↑                  │
│   Prediction       100K OLED Data          │
│                                             │
└─────────────────────────────────────────────┘
```

### 핵심 사양

- **Python MCP Server**
- **7-Layer OLED Device**
- **EML = Host + Dopant**
- **Material Property = HOMO / LUMO / T1 / S1**
- **Operating Condition = Voltage / Current Density**
- **Synthetic Dataset = 100,000건**
- **Raw Data = 단일 JSON 파일**
- **Search DB = SQLite**
- **SQLite Schema = devices + layers**
- **ML = CatBoost**
- **CatBoost 평가 기준 = Test R² 0.90 이상**
- **Target = Luminance 100~30,000 cd/m²**
- **MCP Tools = Prediction / Search / Inverse Design**
- **MCP 실행 방식 = stdio 기반**
- **Search = eq/gte/lte, sort, limit, offset, optional device JSON**
- **Error Response = 공통 error.code/message/details 형식**
- **Inverse Design = EML 조건만 변경**
- **Inverse Design Target = Luminance**
- **Inverse Design 목표 만족 기준 = 예측 Luminance가 Target 이상**
- **테스트 완료 기준 = 세 가지 MCP Tool 단위 테스트 전부 통과**
- **Client = AI Agent + 일반 Application**
- **Model 교체 가능한 Architecture**
