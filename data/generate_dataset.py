import json
import os
import random

RANGES = {
    "homo": (-6.0, -5.0),
    "lumo": (-3.0, -2.0),
    "t1": (2.0, 3.0),
    "s1": (2.5, 3.5),
    "eml_thickness_nm": (10, 50),
    "dopant_concentration_percent": (1, 15),
    "voltage_v": (3.0, 6.0),
    "current_density_ma_cm2": (1, 20),
    "luminance_cd_m2": (100, 30000),
}

HOST_POOL = [f"HOST_{i:03d}" for i in range(1, 51)]
DOPANT_POOL = [f"DOPANT_{i:03d}" for i in range(1, 51)]

RECORD_COUNT = 10000


def make_record(device_id: str) -> dict:
    lo, hi = RANGES["homo"]
    host_homo = round(random.uniform(lo, hi), 2)
    lo, hi = RANGES["lumo"]
    host_lumo = round(random.uniform(lo, hi), 2)
    lo, hi = RANGES["t1"]
    host_t1 = round(random.uniform(lo, hi), 2)
    lo, hi = RANGES["s1"]
    host_s1 = round(random.uniform(lo, hi), 2)

    lo, hi = RANGES["homo"]
    dopant_homo = round(random.uniform(lo, hi), 2)
    lo, hi = RANGES["lumo"]
    dopant_lumo = round(random.uniform(lo, hi), 2)
    lo, hi = RANGES["t1"]
    dopant_t1 = round(random.uniform(lo, hi), 2)
    lo, hi = RANGES["s1"]
    dopant_s1 = round(random.uniform(lo, hi), 2)

    lo, hi = RANGES["eml_thickness_nm"]
    eml_thickness_nm = round(random.uniform(lo, hi), 1)
    lo, hi = RANGES["dopant_concentration_percent"]
    dopant_concentration_percent = round(random.uniform(lo, hi), 1)
    lo, hi = RANGES["voltage_v"]
    voltage_v = round(random.uniform(lo, hi), 2)
    lo, hi = RANGES["current_density_ma_cm2"]
    current_density_ma_cm2 = round(random.uniform(lo, hi), 1)

    lo, hi = RANGES["luminance_cd_m2"]
    luminance_cd_m2 = round(random.uniform(lo, hi), 1)

    return {
        "device_id": device_id,
        "host_material_id": random.choice(HOST_POOL),
        "host_homo": host_homo,
        "host_lumo": host_lumo,
        "host_t1": host_t1,
        "host_s1": host_s1,
        "dopant_material_id": random.choice(DOPANT_POOL),
        "dopant_homo": dopant_homo,
        "dopant_lumo": dopant_lumo,
        "dopant_t1": dopant_t1,
        "dopant_s1": dopant_s1,
        "eml_thickness_nm": eml_thickness_nm,
        "dopant_concentration_percent": dopant_concentration_percent,
        "voltage_v": voltage_v,
        "current_density_ma_cm2": current_density_ma_cm2,
        "target": {"luminance_cd_m2": luminance_cd_m2},
    }


def generate_dataset(count: int = RECORD_COUNT) -> list:
    return [make_record(f"OLED_{i:06d}") for i in range(1, count + 1)]


def main():
    records = generate_dataset(RECORD_COUNT)
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    out_path = os.path.join(project_dir, "data", "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
    print(f"wrote {len(records)} records to {out_path}")


if __name__ == "__main__":
    main()
