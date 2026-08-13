# CLAUDE.md

## 명령어
- `pip install -r requirements.txt` — 의존성 설치
- `py -3.12 data/generate_dataset.py` — `data/data.json` 10,000건 생성
- `py -3.12 models/train_model.py` — CatBoost 학습 후 `models/luminance_model.cbm` 저장
- `py -3.12 mcp_server/server.py` — MCP 서버를 `http://127.0.0.1:8090/mcp`에 기동
- `py -3.12 demo/app.py` — 데모 웹페이지를 `http://127.0.0.1:8765`에 기동
- `node tools/backlog.mjs list` — 작업을 id·상태·제목 순으로 출력
- `node tools/backlog.mjs set <id> <status>` — 작업 상태 변경
- `node tools/backlog.mjs validate` — 필수 필드·enums·id 형식 검사
- `claude mcp list` — Claude Code에 등록된 MCP 서버 연결 상태 확인

## 구조
- `PLAN.md` — 문제 정의·범위·Phase별 완료 기준의 기준
- `SPEC.md` — 입력/출력 스키마·에러 코드·전송 방식의 기준
- `backlog.json` — 작업 상태(SSOT)의 기준
- `.mcp.json` — Claude Code가 연결할 MCP 서버 등록 정보의 기준
- `data/generate_dataset.py` — Synthetic Dataset 생성 로직의 기준
- `models/train_model.py` — CatBoost 학습 절차의 기준
- `inference/predict.py` — `predict_luminance()` 함수 시그니처의 기준
- `mcp_server/server.py` — `predict_luminance` Tool의 입력 검증·에러 응답의 기준
- `demo/app.py` — MCP HTTP 호출 흐름 데모의 기준
- `tools/backlog.mjs` — `backlog.json` 읽기/쓰기 방법의 기준

## 항상 지킬 것
- `backlog.json`은 직접 편집하지 않고 `tools/backlog.mjs`(`list`/`set`/`validate`)로만 읽고 쓴다.
- `catboost` import는 `mcp_server/server.py`와 `inference/predict.py`의 모듈 최상단에서만 한다.
- `mcp_server/server.py`와 `demo/app.py`는 `py -3.12`로만 실행한다.
- `mcp_server/server.py`는 사용 전에 사람이 먼저 직접 띄워둔다.
- `mcp_server/` 안에는 `predict_luminance` Tool 1개만 유지한다.
- `mcp_server/server.py`는 `127.0.0.1`에만 바인딩해 로컬 전용으로만 동작시킨다.
- `.mcp.json`은 project 범위로 등록해 저장소에 커밋한다.

## 막히면
- `py -3.12 --version`으로 Python 3.10 이상인지 확인한다.
- `node --version`으로 Node.js가 설치되어 있는지 확인한다.
- `claude mcp list`로 `oled-luminance`가 연결 상태로 나오는지 확인한다 — 안 나오면 `mcp_server/server.py`가 떠 있는지부터 본다.
- `models/luminance_model.cbm` 파일이 존재하는지 확인한다 — 없으면 `MODEL_NOT_LOADED` 에러가 난다.
- `data/data.json` 파일이 존재하고 10,000건인지 확인한다.
- `node tools/backlog.mjs validate`로 `backlog.json`이 VALID인지 확인한다.
