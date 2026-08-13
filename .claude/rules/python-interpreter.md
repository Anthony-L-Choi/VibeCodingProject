---
paths:
  - "**/*.py"
  - "requirements.txt"
---

# Python 인터프리터 규칙 (Python 스크립트를 실행할 때)

- 이 컴퓨터의 기본 `python`은 3.9다. `fastmcp`·`catboost` 등 이 프로젝트 의존성은
  3.10 이상이 필요하므로 반드시 `py -3.12`로 실행한다.
- `python`이나 `python3` 명령으로 직접 실행하지 않는다 — 버전이 안 맞으면 import
  에러가 나서 원인이 헷갈린다.
- 실행 안내문·스크립트 주석에 명령을 적을 때도 `py -3.12`를 명시한다.
