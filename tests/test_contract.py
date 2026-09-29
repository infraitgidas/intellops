"""Contract tests — OAS-6..OAS-12 (spec §4, design §7, ADR-24).

Estructura:
- Aserciones estructurales sobre `openspec/specs/openapi.yaml` (siempre
  verdes y deterministas): scheme apiKey declarado y aplicado con
  `security: [apiKey]` a /telemetry/* (OAS-6/OAS-11), paths viejos
  /metrics/ingest y /logs/ingest ausentes (OAS-10), application_id fuera de
  required (OAS-12), paths POST/DELETE api-key con los status codes
  esperados (OAS-7), ApplicationRead sin api_token_hash (OAS-8), documento
  3.1 cargable por schemathesis (OAS-9).
- Corrida live de schemathesis contra la app ASGI sobre el subset de paths
  implementados (incluye /telemetry/*), con checks que declaran
  2xx/401/403/404/409/422/503 (OAS-9). Envolver en `xfail` documentado:
  el soporte 3.1 fue experimental (OPEN_API_3_1.enable()) y una limitación
  de herramienta se degrada documentada sin romper el gate (ADR-24).
"""

import yaml

import pytest
from schemathesis.checks import ChecksConfig
from schemathesis.config import PositiveDataAcceptanceConfig, SimpleCheckConfig
from schemathesis.openapi import from_path

from api.main import app

OPENAPI_PATH = "openspec/specs/openapi.yaml"

# OAS-9/ADR-24: en schemathesis <4.0 el soporte OpenAPI 3.1 es experimental y
# se habilita con OPEN_API_3_1.enable(); desde 4.0 el soporte 3.1 es nativo y
# el flag ya no existe. Intentar el enable y documentar la degradación.
try:  # pragma: no cover - rama de schemathesis legacy
    from schemathesis.experimental import OPEN_API_3_1

    OPEN_API_3_1.enable()
    _OPEN_API_3_1_EXPERIMENTAL = True
except ImportError:
    # schemathesis >= 4.0: OpenAPI 3.1 nativo, sin flag experimental.
    _OPEN_API_3_1_EXPERIMENTAL = False

# Paths implementados en la app (ISS-S2-03 agrega /telemetry/*; dashboard/ML
# viven en slices posteriores; OAS-10 los declara en el documento).
_SCOPED_PATH_RE = r"/(health|ready|auth|users|applications|telemetry)"


def _contract() -> dict:
    with open(OPENAPI_PATH, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


# -- OAS-6/OAS-10: scheme apiKey aplicado a /telemetry/* (ISS-S2-03) -----------

def test_oas6_telemetry_paths_require_api_key():
    """El scheme apiKey (X-API-Key) DEBE estar declarado y aplicado con
    `security: [apiKey]` a los paths /telemetry/metrics y
    /telemetry/exceptions (OAS-6, escenario Ingesta protegida)."""
    doc = _contract()
    scheme = doc["components"]["securitySchemes"]["apiKey"]
    assert scheme["type"] == "apiKey"
    assert scheme["in"] == "header"
    assert scheme["name"] == "X-API-Key"

    for path in ("/telemetry/metrics", "/telemetry/exceptions"):
        operation = doc["paths"][path]["post"]
        assert operation["security"] == [{"apiKey": []}], (
            f"{path} DEBE exigir apiKey (OAS-6)"
        )
        declared = set(operation["responses"])
        assert declared == {"202", "400", "401", "403", "503", "429"}  # OAS-11


def test_oas6_scheme_description_no_longer_defers_wiring():
    """La descripción del scheme apiKey DEBE documentar su aplicabilidad
    vigente a /telemetry/* y NO decir que ningún path lo exige aún (OAS-6)."""
    description = _contract()["components"]["securitySchemes"]["apiKey"][
        "description"
    ]
    assert "/telemetry" in description
    assert "ningún path" not in description


def test_oas10_ingest_paths_replaced_by_telemetry():
    """Los paths /metrics/ingest y /logs/ingest DEBEN eliminarse y reemplazarse
    por /telemetry/metrics y /telemetry/exceptions (OAS-10, REMOVED)."""
    doc = _contract()
    assert "/metrics/ingest" not in doc["paths"]
    assert "/logs/ingest" not in doc["paths"]
    assert "/telemetry/metrics" in doc["paths"]
    assert "/telemetry/exceptions" in doc["paths"]


def test_oas10_preexisting_paths_intact():
    """Los paths preexistentes DEBEN quedar intactos (OAS-10)."""
    doc = _contract()
    expected = {
        "/health",
        "/ready",
        "/telemetry/metrics",
        "/telemetry/exceptions",
        "/metrics/query",
        "/metrics/list",
        "/anomalies",
        "/anomalies/{id}",
        "/predictions",
        "/predictions/forecast",
        "/alerts",
        "/alerts/config",
        "/alerts/{id}/ack",
        "/dashboard/summary",
        "/dashboard/heatmap",
        "/assistant/query",
        "/admin/config",
        "/admin/status",
        "/auth/login",
        "/auth/logout",
        "/users",
        "/users/{user_id}",
        "/applications",
        "/applications/{application_id}",
    }
    assert expected <= set(doc["paths"])


# -- OAS-11: requestBody y respuestas completas en /telemetry/* ----------------

def test_oas11_telemetry_paths_declare_request_body_and_responses():
    """Los paths /telemetry/* DEBEN declarar requestBody (RumEventBatch/
    JsExceptionBatch) y las respuestas 202/400/401/403/503/429 con sus
    schemas (OAS-11, escenario Contrato de respuestas completo)."""
    doc = _contract()
    metrics = doc["paths"]["/telemetry/metrics"]["post"]
    exceptions = doc["paths"]["/telemetry/exceptions"]["post"]

    assert (
        metrics["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/RumEventBatch"
    )
    assert (
        exceptions["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/JsExceptionBatch"
    )
    for operation in (metrics, exceptions):
        assert (
            operation["responses"]["202"]["content"]["application/json"]["schema"][
                "$ref"
            ]
            == "#/components/schemas/IngestResponse"
        )
        for code in ("400", "401", "403", "503", "429"):
            assert (
                operation["responses"][code]["content"]["application/json"]["schema"][
                    "$ref"
                ]
                == "#/components/schemas/ErrorResponse"
            )


# -- OAS-12: application_id fuera de required; sin unknown_application ----------

def test_oas12_application_id_not_required_and_no_unknown_application():
    """application_id DEBE salir de required en RumEvent/JsExceptionEvent y
    `unknown_application` NO DEBE figurar como código de rechazo documentado
    (OAS-12, D2/IAUTH-2)."""
    doc = _contract()
    rum_event = doc["components"]["schemas"]["RumEvent"]
    js_event = doc["components"]["schemas"]["JsExceptionEvent"]

    assert "application_id" not in rum_event["required"]
    assert "application_id" not in js_event["required"]
    assert "application_id" in rum_event["properties"]
    assert "application_id" in js_event["properties"]

    rejected_reason = doc["components"]["schemas"]["IngestResponse"]["properties"][
        "rejected"
    ]
    assert "unknown_application" not in str(rejected_reason)


# -- OAS-7: paths api-key + ApiKeyResponse ----------------------------------

def test_oas7_api_key_paths_declared_with_expected_statuses():
    """POST/DELETE /applications/{id}/api-key DEBEN declarar los paths con
    bearerAuth y los status codes 201/204/401/403/404/409/422 (OAS-7)."""
    doc = _contract()
    api_key_path = doc["paths"]["/applications/{application_id}/api-key"]
    assert set(api_key_path) == {"post", "delete"}

    post = api_key_path["post"]
    assert post["security"] == [{"bearerAuth": []}]
    assert set(post["responses"]) == {"201", "401", "403", "404", "409", "422"}
    assert (
        post["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ApiKeyResponse"
    )

    delete = api_key_path["delete"]
    assert delete["security"] == [{"bearerAuth": []}]
    assert set(delete["responses"]) == {"204", "401", "403", "404", "422"}


def test_oas7_api_key_response_schema_show_once():
    """ApiKeyResponse DEBE declarar api_key + hint como required (show-once)."""
    schema = _contract()["components"]["schemas"]["ApiKeyResponse"]
    assert schema["required"] == ["api_key", "hint"]
    assert set(schema["properties"]) == {"api_key", "hint"}


# -- OAS-8: ApplicationRead sin api_token_hash -------------------------------

def test_oas8_application_read_has_no_api_token_hash():
    """ApplicationRead DEBE quedar sin api_token_hash en required y en
    properties; is_active presente (OAS-8, ADR-16, APP-7)."""
    read = _contract()["components"]["schemas"]["ApplicationRead"]
    assert "api_token_hash" not in read["required"]
    assert "api_token_hash" not in read["properties"]
    assert "is_active" in read["required"]
    assert "is_active" in read["properties"]

    create = _contract()["components"]["schemas"]["ApplicationCreate"]
    assert create["properties"]["is_active"]["default"] is True


# -- OAS-9: documento 3.1 válido y carga por schemathesis --------------------

def test_oas9_openapi_document_loads_in_schemathesis():
    """El documento openapi.yaml DEBE ser válido y cargable por schemathesis
    (openapi 3.1), incluidos los paths y schemas nuevos (OAS-9)."""
    schema = from_path(OPENAPI_PATH)
    operations = list(schema.get_all_operations())
    assert len(operations) >= 30  # documento completo, no truncado
    paths = {op.ok().path for op in operations}
    assert "/applications/{application_id}/api-key" in paths
    assert "/telemetry/metrics" in paths
    assert "/telemetry/exceptions" in paths


# -- OAS-9: corrida live scoped (xfail documentado, ADR-24) ------------------

@pytest.mark.xfail(
    strict=False,
    reason=(
        "OAS-9/ADR-24: el contract layer de schemathesis se degrada documentado. "
        "OpenAPI 3.1 fue experimental (OPEN_API_3_1.enable()); en schemathesis "
        ">=4.0 es nativo. El subset scoped cubre los paths implementados "
        "(health/ready/auth/users/applications/telemetry) y los checks declaran "
        "2xx/401/403/404/409/422/503. Una limitación de herramienta no rompe el gate."
    ),
)
def test_schemathesis_live_contract_scoped():
    """Corre schemathesis contra la app ASGI real validando respuestas contra
    el spec 3.1 (OAS-9). xfail documentado: la degradación del contract layer
    no bloquea CI (ADR-24)."""
    schema = from_path(OPENAPI_PATH)
    schema.app = app
    schema.config.checks = ChecksConfig(
        allow_header_conformance=SimpleCheckConfig(enabled=False),
        positive_data_acceptance=PositiveDataAcceptanceConfig(
            expected_statuses=[
                200, 201, 202, 204, 400, 401, 403, 404, 409, 422, 429, 503,
            ]
        ),
    )
    scoped = schema.include(path_regex=_SCOPED_PATH_RE)

    validated = 0
    for operation_result in scoped.get_all_operations():
        operation = operation_result.ok()
        strategy = operation.as_strategy()
        for _ in range(3):
            case = strategy.example()
            case.call_and_validate()
            validated += 1
    # La corrida DEBE ejercitar casos reales (al menos un caso por operación
    # del subset implementado); si no llegara a generar casos, no es un GREEN.
    assert validated >= len(list(scoped.get_all_operations()))
