import os
import sys
from typing import Any

sys.path.insert(0, os.environ.get("CLAUDE_PROJECT_DIR", os.path.dirname(os.path.dirname(__file__))))

from fastmcp import FastMCP

from inference.predict import predict_luminance as run_prediction

mcp = FastMCP("oled-luminance")

STRING_FIELDS = ["host_material_id", "dopant_material_id"]
NUMBER_FIELDS = [
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
ALL_FIELDS = STRING_FIELDS + NUMBER_FIELDS


def _error(code: str, message: str, field: str | None = None, reason: str | None = None) -> dict:
    details = {}
    if field is not None:
        details["field"] = field
    if reason is not None:
        details["reason"] = reason
    return {"error": {"code": code, "message": message, "details": details}}


def _validate(values: dict) -> dict | None:
    for field in ALL_FIELDS:
        if values.get(field) is None:
            return _error(
                "VALIDATION_ERROR",
                "Invalid predict_luminance input.",
                field=field,
                reason="required field missing",
            )
    for field in STRING_FIELDS:
        if not isinstance(values[field], str):
            return _error(
                "VALIDATION_ERROR",
                "Invalid predict_luminance input.",
                field=field,
                reason="expected string",
            )
    for field in NUMBER_FIELDS:
        value = values[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return _error(
                "VALIDATION_ERROR",
                "Invalid predict_luminance input.",
                field=field,
                reason="expected number",
            )
    return None


@mcp.tool()
def predict_luminance(
    host_material_id: Any = None,
    host_homo: Any = None,
    host_lumo: Any = None,
    host_t1: Any = None,
    host_s1: Any = None,
    dopant_material_id: Any = None,
    dopant_homo: Any = None,
    dopant_lumo: Any = None,
    dopant_t1: Any = None,
    dopant_s1: Any = None,
    eml_thickness_nm: Any = None,
    dopant_concentration_percent: Any = None,
    voltage_v: Any = None,
    current_density_ma_cm2: Any = None,
) -> dict:
    """OLED EML(Host/Dopant) 물성치와 구동조건으로 Luminance(cd/m^2)를 예측한다.
    HOMO/LUMO/T1/S1, EML 두께, Dopant 농도, 전압, 전류밀도를 입력받아
    학습된 CatBoost 모델로 luminance_cd_m2 하나를 반환한다."""
    values = {field: locals()[field] for field in ALL_FIELDS}

    error = _validate(values)
    if error is not None:
        return error

    try:
        luminance = run_prediction(values)
    except FileNotFoundError:
        return _error("MODEL_NOT_LOADED", "CatBoost model file not found or failed to load.")
    except Exception as exc:  # noqa: BLE001 - 예상 못 한 서버 내부 오류를 공통 형식으로 감싼다
        return _error("INTERNAL_ERROR", str(exc))

    return {"luminance_cd_m2": luminance}


if __name__ == "__main__":
    mcp.run(transport="stdio")
