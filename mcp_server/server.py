import os
import sys

sys.path.insert(0, os.environ.get("CLAUDE_PROJECT_DIR", os.path.dirname(os.path.dirname(__file__))))

from fastmcp import FastMCP

from inference.predict import predict_luminance as run_prediction

mcp = FastMCP(
    "oled-luminance",
    instructions=(
        "OLED 소자의 EML(발광층) Host/Dopant 물성치와 구동조건(전압, 전류밀도)을 입력받아 "
        "CatBoost 회귀 모델로 Luminance(cd/m^2)를 예측하는 서버다. "
        "predict_luminance Tool 1개만 제공하며, 이 서버는 학습 데이터가 완전 무작위로 생성된 "
        "Synthetic 데이터 기반이라 예측값에 물리적 신뢰성은 없다 — MCP 파이프라인(Dataset 생성, "
        "모델 학습, 추론, Tool 호출) 자체가 정상 동작하는지 확인하기 위한 프로토타입이다."
    ),
)

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
    host_material_id: str | None = None,
    host_homo: float | None = None,
    host_lumo: float | None = None,
    host_t1: float | None = None,
    host_s1: float | None = None,
    dopant_material_id: str | None = None,
    dopant_homo: float | None = None,
    dopant_lumo: float | None = None,
    dopant_t1: float | None = None,
    dopant_s1: float | None = None,
    eml_thickness_nm: float | None = None,
    dopant_concentration_percent: float | None = None,
    voltage_v: float | None = None,
    current_density_ma_cm2: float | None = None,
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
    # 로컬 전용 원격(streamable-HTTP) 서버. 127.0.0.1에만 바인딩해 이 컴퓨터 밖에서는
    # 접근할 수 없다 — 외부 공개 배포(Cloudflare Workers 등)는 SPEC.md#9에 비범위로 명시.
    mcp.run(transport="http", host="127.0.0.1", port=8090, path="/mcp")
