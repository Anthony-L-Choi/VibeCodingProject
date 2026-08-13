---
paths:
  - "models/train_model.py"
  - "inference/predict.py"
---

# Feature 순서 불변식 (학습·추론 코드를 고칠 때)

- `models/train_model.py`의 `FEATURE_ORDER`와 `inference/predict.py`가 입력을
  벡터로 변환할 때 쓰는 필드 순서는 반드시 동일해야 한다.
- 한쪽만 고치고 다른 쪽을 맞추지 않으면 에러 없이 조용히 잘못된 예측값이
  나온다 — 두 파일의 순서를 대조하기 전에는 변경을 끝낸 것으로 보지 않는다.
- Feature를 추가·삭제·순서 변경할 때는 두 파일을 같은 커밋에서 함께 수정한다.
