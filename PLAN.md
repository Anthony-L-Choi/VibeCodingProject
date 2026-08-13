# OLED 소자 특성 예측 MCP 개발

**Capstone 트랙**: 트랙 B — 자동화 Agent · Workflow
**구현에 쓸 수 있는 시간**: 코칭 전후·저녁 + 다음 날 발표 전까지 (실질 6~8시간)

## ① 문제 정의 — 지금 무엇이 불편한가
- 누가 / 언제 / 어떤 일에서: OLED 소자 설계 연구원이 신소재 조합을 검토할 때
- 줄이는 비용 (반복 / 대기 / 검증 중 하나): 반복
- 지금 걸리는 시간·횟수: 신소재 조합 하나 검토하는 데 5일 정도

## ② AI 에이전트에게 맡길 부분
- 에이전트가 대신할 일: Phase 1~4 전부 (Dataset 생성, CatBoost 모델 학습, Inference 모듈, MCP 서버 개발)
- 사람이 계속 할 일: 없음
- 쓸 도구 (서브에이전트·MCP·스킬·hook·병렬 중 필요한 것만): 없음

## ③ 범위 — 반드시 / 되면 좋은 / 안 하는 것
- 반드시 (이게 안 되면 실패): Synthetic OLED Dataset 생성 + CatBoost 모델 생성(성능 목표 없이 학습만) + `predict_luminance` MCP Tool(stdio) 1개 제공
- 되면 좋은: 없음
- 이번엔 안 하는 것: `search_oled_devices`, `inverse_design_oled`, SQLite 구축, CatBoost 성능 검증(R² 기준), Feature Importance/설명가능성

## ④ Phase 분할과 각 Phase 완료 기준
1. 샘플 Dataset 생성 — 완료: `data/data.json`에 데이터 10,000건이 있다
2. 모델 개발 — 완료: `models` 폴더에 `.cbm` 파일로 CatBoost 모델이 저장되어 있다
3. Inference 모듈 구축 — 완료: input 값을 넣었을 때 Luminance 결과값이 나오는 module이 존재한다
4. MCP 개발 — 완료: MCP 서버를 실행한 뒤 `predict_luminance` Tool을 샘플 입력으로 호출하면 `luminance` 필드를 가진 응답이 온다

## ⑤ 완료를 판정할 방법 (검증 게이트)
- 기계가 판정하는 것: ④의 Phase별 "완료:" 조건 자체 (데이터 건수, 모델 파일 존재, 함수 실행 결과, MCP 응답 필드)
- 사람이 눈으로 보는 것: 없음
- 내가 직접 승인할 지점: Git 커밋/초기화 시점

## GitHub 저장소 URL
https://github.com/Anthony-L-Choi/VibeCodingProject

## 1:1 코칭에서 가장 묻고 싶은 것
- 해당 프로젝트가 가능한 주제인지
- MCP 개발 시 개발 워크플로우
- MCP 개발의 최종 목표를 어떻게 설정하는지

---
(아래는 폼에 넣지 않는 작업 메모)

## 참고 자료
- OLED_Luminance_Prediction_MCP_Server_Requirements_v1.0.md (요구사항 정의서 v1.0, 7-Layer 구조 / CatBoost / SQLite 검색 / 역설계 MCP 서버)

## 되돌아갈 지점과 데이터
- 되돌리는 방법: `git init` + 첫 커밋(`e51dbbb`) 완료. 이후 문제 생기면 이 커밋으로 되돌린다.
- 실데이터·자격증명 없이 되게 만드는 방법 (샘플로 대체할 부분): 프로젝트 전체가 Synthetic Dataset(Phase 1) 기반이라 실데이터 불필요. 물성값(HOMO/LUMO/T1/S1)·Operating Condition은 요구사항 문서의 예시 형식을 따라 직접 생성한다.

## 고칠 곳 (4단계 반박 결과)
1. [③④] Phase 1~4의 "완료:" 기준이 전부 결과물의 **존재 여부**만 확인한다 (건수, 파일 존재, 반환값 존재). Dataset이 물리적으로 타당한 관계(HOMO/LUMO 정렬 등)를 반영했는지, 모델이 실제로 유의미하게 학습했는지는 어떤 Phase도 검증하지 않는다.
2. [②⑤] "사람이 계속 할 일: 없음" + "사람이 눈으로 보는 것: 없음" + 승인 지점이 Git 커밋 하나뿐이라, 완전히 무작위인 데이터로 10,000건을 생성하고 그걸로 CatBoost를 학습시켜도 4개 Phase의 "완료:" 조건을 전부 통과한다. 결과물이 OLED 도메인과 실제로 맞는지 사람이 확인하는 지점이 계약에 없다.

<!-- 기획 시작 09:21 -->
