---
paths:
  - "mcp_server/**"
  - ".mcp.json"
  - "demo/**"
---

# MCP 서버 규칙 (MCP 서버를 다루거나 테스트·데모를 실행할 때)

- 이 서버는 stdio가 아니라 `http://127.0.0.1:8090/mcp`에 바인딩한 로컬 전용
  HTTP다. Claude Code가 대신 실행해주지 않는다.
- `predict_luminance` Tool을 호출하거나 `demo/app.py`를 쓰기 전에, 사람이
  먼저 `py -3.12 mcp_server/server.py`로 서버를 띄워둬야 한다.
- 서버가 안 떠 있으면 `claude mcp list`에서 연결 실패로 뜬다 — 연결 에러가
  나면 먼저 서버 프로세스가 살아있는지부터 확인한다.
- 입력 검증과 에러 응답을 포함한다 — 필수 필드 누락·타입 오류 시 SPEC.md
  6.3절의 공통 에러 스키마(`{ "error": { "code", "message", "details" } }`)로
  응답한다.
- Tool은 `predict_luminance` 1개만 등록한다 — Action이 적을 땐 tool을 나누지
  않고 하나로 유지한다는 결정을 따른다.
- MCP 서버는 local 범위가 아니라 project 범위로 등록한다 — 저장소 루트의
  `.mcp.json`에 등록해 클론한 사람 누구나 같은 서버를 쓸 수 있게 한다.
