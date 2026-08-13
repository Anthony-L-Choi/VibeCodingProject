import json
import os
import random

from catboost import CatBoostRegressor

# 순서가 inference/predict.py의 FEATURE_ORDER와 반드시 동일해야 한다.
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

TEST_RATIO = 0.2
RANDOM_SEED = 42


def load_dataset(project_dir: str):
    data_path = os.path.join(project_dir, "data", "data.json")
    with open(data_path, encoding="utf-8") as f:
        records = json.load(f)
    X = [[r[field] for field in FEATURE_ORDER] for r in records]
    y = [r["target"]["luminance_cd_m2"] for r in records]
    return X, y


def train_test_split(X, y, test_ratio: float, seed: int):
    indices = list(range(len(X)))
    random.Random(seed).shuffle(indices)
    split_at = int(len(indices) * (1 - test_ratio))
    train_idx, test_idx = indices[:split_at], indices[split_at:]
    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]
    return X_train, X_test, y_train, y_test


def main():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    X, y = load_dataset(project_dir)
    X_train, X_test, y_train, y_test = train_test_split(X, y, TEST_RATIO, RANDOM_SEED)
    print(f"train: {len(X_train)}")
    print(f"test: {len(X_test)}")

    model = CatBoostRegressor(verbose=False, random_seed=RANDOM_SEED)
    model.fit(X_train, y_train)

    models_dir = os.path.join(project_dir, "models")
    out_path = os.path.join(models_dir, "luminance_model.cbm")
    model.save_model(out_path)
    print(f"saved model to {out_path}")


if __name__ == "__main__":
    main()
