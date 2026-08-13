import os

from catboost import CatBoostRegressor

# 순서가 models/train_model.py의 FEATURE_ORDER와 반드시 동일해야 한다.
FEATURE_ORDER = [
    "host_homo",
    "host_lumo",
    "host_t1",
    "host_s1",
    "dopant_homo",
    "dopant_lumo",
    "dopant_t1",
    "dopant_s1",
    "eml_thickness_nm",
    "dopant_concentration_percent",
    "voltage_v",
    "current_density_ma_cm2",
]

_PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", ".")
_MODEL_PATH = os.path.join(_PROJECT_DIR, "models", "luminance_model.cbm")

_model = None


def _load_model() -> CatBoostRegressor:
    global _model
    if _model is None:
        model = CatBoostRegressor()
        model.load_model(_MODEL_PATH)
        _model = model
    return _model


def predict_luminance(input_data: dict) -> float:
    """input_data는 SPEC.md 2.1의 14개 필드 입력 스키마를 따른다.
    models/luminance_model.cbm을 로드해 luminance_cd_m2를 반환한다."""
    model = _load_model()
    feature_vector = [[input_data[field] for field in FEATURE_ORDER]]
    prediction = model.predict(feature_vector)
    return float(prediction[0])


if __name__ == "__main__":
    sample = {
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
        "current_density_ma_cm2": 10.0,
    }
    print(predict_luminance(sample))
