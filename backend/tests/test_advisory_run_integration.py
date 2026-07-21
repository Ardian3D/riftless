"""F7.5 — Optional advisory integration on POST /api/v1/runs/analyze.

No live DeepSeek calls. Provider traffic uses FakeTransport injection only.
"""

from __future__ import annotations

import asyncio
import copy
import inspect
import json
import uuid
from typing import Any, Mapping
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.routes import runs as runs_route
from app.main import app
from app.schemas.advisory import AdvisoryArtifact
from app.schemas.changes import ChangeIntakeRequest
from app.schemas.deepseek_advisory import (
    DEEPSEEK_ADVISORY_MODEL,
    REQUIRED_ADVISORY_LIMITATIONS,
)
from app.schemas.risk import EvaluationContext
from app.schemas.runs import (
    RUN_ARTIFACT_VERSION,
    AdvisoryRunOptions,
    AnalysisRunData,
    AnalysisRunRequest,
)
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
    ValidationArtifact,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.services.advisory_context_builder import AdvisoryContextBuildError
from app.services.change_intake import process_change_intake
from app.services.deepseek_http_transport import (
    DEEPSEEK_CHAT_COMPLETIONS_URL,
    DeepSeekHTTPResponse,
    DeepSeekTransportError,
)
from app.services.deepseek_provider_config import DEEPSEEK_API_KEY_ENV
from app.services.run_orchestrator import analysis_run_meta, orchestrate_analysis_run
from app.services.validation_engine import build_validation_artifact

ANALYZE_PATH = "/api/v1/runs/analyze"
API_KEY_CANARY = "test_deepseek_key_do_not_log_f75"
PROVIDER_ERROR_CANARY = "PROVIDER_ERROR_BODY_CANARY_F75_DO_NOT_LEAK"

CANARY_DB = "CANARY_DB_ACME_ANALYTICS_F75"
CANARY_SCHEMA = "CANARY_SCHEMA_CORE_F75"
CANARY_ASSET = "CANARY_TABLE_CUSTOMERS_F75"
CANARY_SOURCE = "CANARY_COL_CUSTOMER_ID_F75"
CANARY_TARGET = "CANARY_COL_ACCOUNT_ID_F75"
CANARY_REASON = "CANARY_REASON_TEXT_DO_NOT_LEAK_F75"
CANARY_SQL = "SELECT CANARY_SQL_SECRET_F75 FROM nowhere"
CANARY_FIXTURE = "CANARY_FIXTURE_ROW_VALUE_F75"
CANARY_EVIDENCE_MSG = "CANARY_EVIDENCE_MESSAGE_DO_NOT_LEAK_F75"


# ---- Fake transport (mirrors F7.4 test double; no live sockets) --------------


class FakeTransport:
    """Injectable transport that records calls and returns a fixed response."""

    def __init__(
        self,
        response: DeepSeekHTTPResponse | None = None,
        *,
        error: DeepSeekTransportError | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> DeepSeekHTTPResponse:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout_seconds": timeout_seconds,
                "max_response_bytes": max_response_bytes,
            }
        )
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise DeepSeekTransportError(
                code="network_unavailable",
                message="Fake transport has no response.",
            )
        return self.response


def _client() -> TestClient:
    return TestClient(app)


def _change(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "change_type": "rename_column",
        "asset": {
            "platform": "snowflake",
            "database": CANARY_DB,
            "schema": CANARY_SCHEMA,
            "name": CANARY_ASSET,
        },
        "source_column": CANARY_SOURCE,
        "target_column": CANARY_TARGET,
        "reason": CANARY_REASON,
    }
    data.update(overrides)
    return data


def _allow_ctx() -> dict[str, Any]:
    return {
        "context_complete": True,
        "downstream_dependency_count": 0,
        "protected_asset": False,
    }


def _warn_ctx() -> dict[str, Any]:
    return {
        "context_complete": True,
        "downstream_dependency_count": 3,
        "protected_asset": False,
    }


def _block_ctx() -> dict[str, Any]:
    return {
        "context_complete": False,
        "downstream_dependency_count": None,
        "protected_asset": True,
    }


def _validation_block(
    *,
    sql: str | None = None,
    fixture_value: str = CANARY_FIXTURE,
) -> dict[str, Any]:
    if sql is None:
        sql = f"select {CANARY_SOURCE} as {CANARY_TARGET} from {CANARY_ASSET}"
    return {
        "checks": {
            "sql_parse": {
                "sql": sql,
                "dialect": "snowflake",
                "required": True,
            },
            "duckdb_execution": {
                "fixture": {
                    "columns": [
                        {
                            "name": CANARY_SOURCE,
                            "type": "varchar",
                            "nullable": False,
                        }
                    ],
                    "rows": [[fixture_value]],
                },
                "required": True,
            },
            "dbt_validation": {
                "model_name": "customers_renamed",
                "model_sql": sql,
                "required": False,
            },
        }
    }


def _body(
    context: dict[str, Any] | None = None,
    *,
    change: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    advisory: dict[str, Any] | None = None,
    include_advisory: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "change": change or _change(),
        "evaluation_context": context or _allow_ctx(),
    }
    if validation is not None:
        payload["validation"] = validation
    if include_advisory or advisory is not None:
        payload["advisory"] = advisory if advisory is not None else {"requested": True}
    return payload


def _valid_advisory_content_json() -> str:
    return json.dumps(
        {
            "response_version": "1.0",
            "content": {
                "summary": "A bounded advisory summary for human reviewers.",
                "observations": ["Risk and validation remain independent."],
                "review_questions": ["Has a human reviewed the validation artifact?"],
                "limitations": list(REQUIRED_ADVISORY_LIMITATIONS),
            },
        },
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _provider_envelope(
    *,
    content: str | None = None,
    finish_reason: str = "stop",
) -> dict[str, Any]:
    if content is None:
        content = _valid_advisory_content_json()
    return {
        "id": "chatcmpl-must-not-persist",
        "object": "chat.completion",
        "created": 1_700_000_000,
        "model": DEEPSEEK_ADVISORY_MODEL,
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


def _http_ok(envelope: dict[str, Any] | None = None) -> DeepSeekHTTPResponse:
    if envelope is None:
        envelope = _provider_envelope()
    return DeepSeekHTTPResponse(
        status_code=200,
        content_type="application/json",
        body=json.dumps(envelope, separators=(",", ":")).encode("utf-8"),
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )


def _http_status(status_code: int) -> DeepSeekHTTPResponse:
    return DeepSeekHTTPResponse(
        status_code=status_code,
        content_type="application/json",
        body=json.dumps({"error": PROVIDER_ERROR_CANARY}).encode("utf-8"),
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )


def _request(
    *,
    context: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    advisory_requested: bool | None = None,
) -> AnalysisRunRequest:
    data: dict[str, Any] = {
        "change": _change(),
        "evaluation_context": context or _allow_ctx(),
    }
    if validation is not None:
        data["validation"] = validation
    if advisory_requested is not None:
        data["advisory"] = {"requested": advisory_requested}
    return AnalysisRunRequest.model_validate(data)


def _run(
    *,
    context: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    advisory_requested: bool = True,
    environ: Mapping[str, str] | None = None,
    transport: FakeTransport | None = None,
) -> AnalysisRunData:
    return orchestrate_analysis_run(
        _request(
            context=context,
            validation=validation,
            advisory_requested=advisory_requested,
        ),
        advisory_environ=environ if environ is not None else {DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
        advisory_transport=transport if transport is not None else FakeTransport(response=_http_ok()),
    )


def _status(artifact: AdvisoryArtifact | None) -> str | None:
    if artifact is None:
        return None
    s = artifact.execution_status
    return s.value if hasattr(s, "value") else str(s)


def _assert_no_provider_secrets(obj: Any) -> None:
    """Provider secrets / raw envelopes must never appear in API surfaces."""
    text = json.dumps(obj, default=str) if not isinstance(obj, str) else obj
    for banned in (
        API_KEY_CANARY,
        PROVIDER_ERROR_CANARY,
        "Bearer ",
        "chatcmpl-must-not-persist",
        "prompt_tokens",
    ):
        assert banned not in text, f"provider secret leaked: {banned}"


def _assert_advisory_surface_clean(obj: Any) -> None:
    """Advisory artifact / provider path must not carry raw canaries."""
    text = json.dumps(obj, default=str) if not isinstance(obj, str) else obj
    _assert_no_provider_secrets(text)
    for banned in (
        CANARY_SQL,
        CANARY_FIXTURE,
        CANARY_EVIDENCE_MSG,
        "CONTEXT_JSON_START",
    ):
        assert banned not in text, f"advisory surface leak: {banned}"


def _evidence(code: str = "engine_error") -> ValidationEvidence:
    return ValidationEvidence(code=code, message=CANARY_EVIDENCE_MSG, details={"sql": CANARY_SQL})


def _check(
    *,
    check_kind: CheckKind = CheckKind.SQL_PARSE,
    required: bool = True,
    execution_status: CheckExecutionStatus = CheckExecutionStatus.COMPLETED,
    outcome: CheckOutcome | None = CheckOutcome.PASS,
    evidence: list[ValidationEvidence] | None = None,
) -> ValidationCheckResult:
    if evidence is None:
        evidence = [_evidence("sql_parse_succeeded")]
    return ValidationCheckResult(
        check_id=uuid.uuid4(),
        check_kind=check_kind,
        required=required,
        execution_status=execution_status,
        outcome=outcome,
        scope="test scope",
        summary="test check summary",
        evidence=evidence,
        engine_name="test",
        engine_version="0",
    )


# ==============================================================================
# Request contract
# ==============================================================================


def test_request_without_advisory_valid() -> None:
    req = AnalysisRunRequest.model_validate(
        {"change": _change(), "evaluation_context": _allow_ctx()}
    )
    assert req.advisory is None


def test_omitted_advisory_means_not_requested() -> None:
    result = orchestrate_analysis_run(
        _request(advisory_requested=None),
        advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
        advisory_transport=FakeTransport(response=_http_ok()),
    )
    assert result.advisory_requested is False
    assert result.advisory_artifact is None


def test_advisory_requested_false_accepted() -> None:
    req = AnalysisRunRequest.model_validate(
        {
            "change": _change(),
            "evaluation_context": _allow_ctx(),
            "advisory": {"requested": False},
        }
    )
    assert req.advisory is not None
    assert req.advisory.requested is False


def test_advisory_requested_true_accepted() -> None:
    req = AnalysisRunRequest.model_validate(
        {
            "change": _change(),
            "evaluation_context": _allow_ctx(),
            "advisory": {"requested": True},
        }
    )
    assert req.advisory is not None
    assert req.advisory.requested is True


@pytest.mark.parametrize(
    "extra",
    [
        {"api_key": "sk-x"},
        {"model": "deepseek-v4-flash"},
        {"prompt": "hello"},
        {"context_pack": {}},
        {"timeout": 30},
        {"retry": 3},
        {"provider": "deepseek"},
        {"temperature": 0.0},
        {"endpoint": "https://example.com"},
        {"transport": "stdlib"},
    ],
)
def test_unknown_advisory_fields_rejected(extra: dict[str, Any]) -> None:
    body = {"requested": True, **extra}
    with pytest.raises(ValidationError):
        AdvisoryRunOptions.model_validate(body)
    payload = _body(advisory=body, include_advisory=True)
    assert _client().post(ANALYZE_PATH, json=payload).status_code == 422


def test_top_level_legacy_fields_still_work() -> None:
    response = _client().post(ANALYZE_PATH, json=_body())
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    assert data["advisory_requested"] is False


# ==============================================================================
# No-advisory path
# ==============================================================================


def test_no_advisory_artifact_null_and_version() -> None:
    result = orchestrate_analysis_run(_request())
    assert result.advisory_requested is False
    assert result.advisory_artifact is None
    assert result.run_artifact_version == "1.2"
    assert result.run_artifact_version == RUN_ARTIFACT_VERSION
    assert result.validation_artifact is None
    assert result.orchestration_status == "completed"


def test_requested_false_artifact_null() -> None:
    result = orchestrate_analysis_run(_request(advisory_requested=False))
    assert result.advisory_requested is False
    assert result.advisory_artifact is None


def test_no_advisory_does_not_load_config_or_env() -> None:
    transport = FakeTransport(response=_http_ok())

    def _deny_getenv(*_a: Any, **_k: Any) -> str:
        raise AssertionError("must not read environment when advisory not requested")

    with patch(
        "app.services.run_orchestrator.load_deepseek_provider_config",
        side_effect=AssertionError("config loader must not run"),
    ):
        with patch("os.getenv", side_effect=_deny_getenv):
            with patch("os.environ.get", side_effect=_deny_getenv):
                result = orchestrate_analysis_run(
                    _request(),
                    advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
                    advisory_transport=transport,
                )
    assert result.advisory_artifact is None
    assert transport.calls == []


def test_no_advisory_transport_post_not_called() -> None:
    transport = FakeTransport(response=_http_ok())
    orchestrate_analysis_run(
        _request(advisory_requested=False),
        advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
        advisory_transport=transport,
    )
    assert transport.calls == []


def test_no_advisory_existing_fields_present_http() -> None:
    data = _client().post(ANALYZE_PATH, json=_body()).json()["data"]
    assert set(data.keys()) == {
        "run_id",
        "orchestration_status",
        "change_intake",
        "risk_evaluation",
        "validation_artifact",
        "advisory_requested",
        "advisory_artifact",
        "run_artifact_version",
    }
    assert data["run_artifact_version"] == "1.2"


# ==============================================================================
# Missing config
# ==============================================================================


def test_missing_config_unavailable_no_transport() -> None:
    transport = FakeTransport(response=_http_ok())
    result = orchestrate_analysis_run(
        _request(advisory_requested=True),
        advisory_environ={},
        advisory_transport=transport,
    )
    assert result.advisory_requested is True
    assert result.advisory_artifact is not None
    assert _status(result.advisory_artifact) == "unavailable"
    assert result.advisory_artifact.status_detail is not None
    assert result.advisory_artifact.status_detail.code == "provider_not_configured"
    assert transport.calls == []
    assert result.orchestration_status == "completed"
    assert result.risk_evaluation.decision == "ALLOW"
    dumped = result.model_dump(mode="json")
    _assert_no_provider_secrets(dumped)
    _assert_advisory_surface_clean(dumped["advisory_artifact"])


def test_missing_config_http_200() -> None:
    with patch(
        "app.services.run_orchestrator.load_deepseek_provider_config",
        return_value=None,
    ):
        with patch(
            "app.services.run_orchestrator.StdlibDeepSeekHTTPSTransport",
            return_value=FakeTransport(response=_http_ok()),
        ):
            response = _client().post(
                ANALYZE_PATH, json=_body(advisory={"requested": True}, include_advisory=True)
            )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["orchestration_status"] == "completed"
    assert data["advisory_requested"] is True
    assert data["advisory_artifact"]["execution_status"] == "unavailable"
    assert data["advisory_artifact"]["status_detail"]["code"] == "provider_not_configured"
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    _assert_no_provider_secrets(response.json())
    _assert_advisory_surface_clean(data["advisory_artifact"])


# ==============================================================================
# Completed advisory
# ==============================================================================


def test_completed_advisory_fields() -> None:
    transport = FakeTransport(response=_http_ok())
    result = _run(transport=transport)
    art = result.advisory_artifact
    assert art is not None
    assert _status(art) == "completed"
    assert art.model_name == "deepseek-v4-flash"
    assert art.subject_fingerprint == result.change_intake.content_fingerprint
    assert len(art.context_fingerprint) == 64
    assert art.content is not None
    assert art.content.summary.startswith("A bounded advisory")
    assert art.authority == "advisory_only"
    assert art.risk_effect == "none"
    assert art.validation_effect == "none"
    assert art.deployment_authorized is False
    assert art.persistence == "none"
    assert art.retrieval_available is False
    assert len(transport.calls) == 1
    assert transport.calls[0]["url"] == DEEPSEEK_CHAT_COMPLETIONS_URL
    dumped = result.model_dump(mode="json")
    text = json.dumps(dumped)
    assert "chatcmpl-must-not-persist" not in text
    assert "prompt_tokens" not in text
    assert "context_pack" not in text
    assert "CONTEXT_JSON_START" not in text
    assert API_KEY_CANARY not in text
    assert result.orchestration_status == "completed"


def test_completed_advisory_http_200() -> None:
    transport = FakeTransport(response=_http_ok())
    with patch(
        "app.services.run_orchestrator.load_deepseek_provider_config",
        side_effect=lambda environ=None: __import__(
            "app.services.deepseek_provider_config", fromlist=["DeepSeekProviderConfig"]
        ).DeepSeekProviderConfig(api_key=API_KEY_CANARY),
    ):
        with patch(
            "app.services.run_orchestrator.StdlibDeepSeekHTTPSTransport",
            return_value=transport,
        ):
            response = _client().post(
                ANALYZE_PATH,
                json=_body(advisory={"requested": True}, include_advisory=True),
            )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["advisory_artifact"]["execution_status"] == "completed"
    assert data["advisory_artifact"]["model_name"] == "deepseek-v4-flash"
    assert len(transport.calls) == 1
    meta = response.json()["meta"]
    assert meta["advisory_requested"] is True
    assert meta["model_used"] is True
    assert meta["advisory_authority"] == "advisory_only"
    assert meta["deployment_authorized"] is False
    _assert_no_provider_secrets(response.json())
    _assert_advisory_surface_clean(data["advisory_artifact"])


# ==============================================================================
# Provider failures
# ==============================================================================


@pytest.mark.parametrize(
    "error,status,code",
    [
        (
            DeepSeekTransportError(code="timeout", message="timed out"),
            "unavailable",
            "provider_timeout",
        ),
    ],
)
def test_transport_timeout_unavailable(
    error: DeepSeekTransportError, status: str, code: str
) -> None:
    transport = FakeTransport(error=error)
    result = _run(transport=transport)
    assert _status(result.advisory_artifact) == status
    assert result.advisory_artifact is not None
    assert result.advisory_artifact.status_detail is not None
    assert result.advisory_artifact.status_detail.code == code
    assert result.orchestration_status == "completed"
    assert result.risk_evaluation.decision == "ALLOW"


@pytest.mark.parametrize(
    "http_status,exec_status,code",
    [
        (401, "error", "provider_authentication_failed"),
        (429, "unavailable", "provider_rate_limited"),
        (500, "unavailable", "provider_unavailable"),
    ],
)
def test_provider_http_failures_map_to_artifact(
    http_status: int, exec_status: str, code: str
) -> None:
    transport = FakeTransport(response=_http_status(http_status))
    result = _run(transport=transport)
    assert result.orchestration_status == "completed"
    assert _status(result.advisory_artifact) == exec_status
    assert result.advisory_artifact is not None
    assert result.advisory_artifact.status_detail is not None
    assert result.advisory_artifact.status_detail.code == code
    assert result.risk_evaluation.decision == "ALLOW"
    text = json.dumps(result.model_dump(mode="json"))
    assert PROVIDER_ERROR_CANARY not in text


def test_invalid_provider_envelope_error() -> None:
    transport = FakeTransport(
        response=DeepSeekHTTPResponse(
            status_code=200,
            content_type="application/json",
            body=b'{"not":"a valid envelope"}',
            final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
        )
    )
    result = _run(transport=transport)
    assert _status(result.advisory_artifact) == "error"
    assert result.orchestration_status == "completed"


def test_invalid_advisory_json_error() -> None:
    env = _provider_envelope(content="not-json{")
    transport = FakeTransport(response=_http_ok(env))
    result = _run(transport=transport)
    assert _status(result.advisory_artifact) == "error"
    assert result.orchestration_status == "completed"


def test_missing_canonical_limitations_error() -> None:
    content = json.dumps(
        {
            "response_version": "1.0",
            "content": {
                "summary": "x" * 20,
                "observations": ["o"],
                "review_questions": ["q"],
                "limitations": ["only one limitation string here"],
            },
        }
    )
    transport = FakeTransport(response=_http_ok(_provider_envelope(content=content)))
    result = _run(transport=transport)
    assert _status(result.advisory_artifact) == "error"
    assert result.orchestration_status == "completed"


def test_provider_failure_no_endpoint_500() -> None:
    transport = FakeTransport(
        error=DeepSeekTransportError(code="timeout", message="timed out")
    )
    with patch(
        "app.services.run_orchestrator.load_deepseek_provider_config",
        side_effect=lambda environ=None: __import__(
            "app.services.deepseek_provider_config", fromlist=["DeepSeekProviderConfig"]
        ).DeepSeekProviderConfig(api_key=API_KEY_CANARY),
    ):
        with patch(
            "app.services.run_orchestrator.StdlibDeepSeekHTTPSTransport",
            return_value=transport,
        ):
            response = _client().post(
                ANALYZE_PATH,
                json=_body(advisory={"requested": True}, include_advisory=True),
            )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["orchestration_status"] == "completed"
    assert data["advisory_artifact"]["execution_status"] == "unavailable"


def test_provider_failure_does_not_change_risk_or_validation() -> None:
    transport = FakeTransport(response=_http_status(500))

    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(
                    outcome=CheckOutcome.PASS,
                    evidence=[_evidence("sql_parse_succeeded")],
                )
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        result = _run(
            context=_block_ctx(),
            validation=_validation_block(),
            transport=transport,
        )
    assert result.risk_evaluation.decision == "BLOCK"
    assert result.validation_artifact is not None
    assert result.validation_artifact.outcome == CheckOutcome.PASS.value
    assert _status(result.advisory_artifact) == "unavailable"
    assert len(transport.calls) == 1  # no automatic retry


# ==============================================================================
# Validation compatibility
# ==============================================================================


def test_advisory_without_validation() -> None:
    result = _run(validation=None)
    assert result.validation_artifact is None
    assert _status(result.advisory_artifact) == "completed"


def test_advisory_with_validation_pass() -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(
                    execution_status=CheckExecutionStatus.COMPLETED,
                    outcome=CheckOutcome.PASS,
                )
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block())
    assert result.validation_artifact is not None
    assert result.validation_artifact.outcome == "pass"
    assert _status(result.advisory_artifact) == "completed"


def test_advisory_with_validation_fail() -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(
                    outcome=CheckOutcome.FAIL,
                    evidence=[_evidence("rule_fail")],
                )
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block())
    assert result.validation_artifact is not None
    assert result.validation_artifact.outcome == "fail"
    assert _status(result.advisory_artifact) == "completed"


def test_advisory_with_validation_inconclusive() -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(outcome=CheckOutcome.PASS),
                _check(
                    check_kind=CheckKind.DUCKDB_EXECUTION,
                    outcome=CheckOutcome.INCONCLUSIVE,
                ),
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block())
    assert result.validation_artifact is not None
    assert result.validation_artifact.outcome == "inconclusive"
    assert _status(result.advisory_artifact) == "completed"


def test_advisory_with_validation_partial() -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(outcome=CheckOutcome.PASS),
                _check(
                    check_kind=CheckKind.DUCKDB_EXECUTION,
                    execution_status=CheckExecutionStatus.ERROR,
                    outcome=None,
                    evidence=[_evidence("engine_error")],
                ),
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block())
    assert result.validation_artifact is not None
    assert (
        result.validation_artifact.execution_status
        == OverallExecutionStatus.PARTIAL.value
    )
    assert _status(result.advisory_artifact) == "completed"


def test_advisory_with_execution_failed() -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(
                    execution_status=CheckExecutionStatus.ERROR,
                    outcome=None,
                    evidence=[_evidence("engine_error")],
                )
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block())
    assert result.validation_artifact is not None
    assert (
        result.validation_artifact.execution_status
        == OverallExecutionStatus.EXECUTION_FAILED.value
    )
    assert result.validation_artifact.outcome == "inconclusive"
    assert _status(result.advisory_artifact) == "completed"


def test_advisory_with_not_run_empty_checks() -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block())
    assert result.validation_artifact is not None
    assert result.validation_artifact.execution_status == "not_run"
    assert result.validation_artifact.checks == []
    assert _status(result.advisory_artifact) == "completed"


@pytest.mark.parametrize(
    "status",
    [
        CheckExecutionStatus.ERROR,
        CheckExecutionStatus.UNAVAILABLE,
        CheckExecutionStatus.SKIPPED,
    ],
)
def test_advisory_with_null_check_outcomes(status: CheckExecutionStatus) -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(
                    execution_status=status,
                    outcome=None,
                    evidence=[_evidence("engine_error")],
                )
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block())
    assert result.validation_artifact is not None
    assert result.validation_artifact.checks[0].outcome is None
    assert _status(result.advisory_artifact) == "completed"


def test_validation_artifact_not_mutated() -> None:
    captured: dict[str, Any] = {}

    def _orch(plan: Any) -> ValidationArtifact:
        art = build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[_check()],
        )
        captured["before"] = copy.deepcopy(art.model_dump(mode="json"))
        captured["obj"] = art
        return art

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        _run(validation=_validation_block())
    assert captured["obj"].model_dump(mode="json") == captured["before"]


# ==============================================================================
# Independence matrix
# ==============================================================================


def test_allow_plus_advisory_unavailable_stays_allow() -> None:
    result = _run(
        context=_allow_ctx(),
        environ={},
        transport=FakeTransport(response=_http_ok()),
    )
    assert result.risk_evaluation.decision == "ALLOW"
    assert _status(result.advisory_artifact) == "unavailable"


def test_warn_plus_advisory_error_stays_warn() -> None:
    transport = FakeTransport(response=_http_status(401))
    result = _run(context=_warn_ctx(), transport=transport)
    assert result.risk_evaluation.decision == "WARN"
    assert _status(result.advisory_artifact) == "error"


def test_block_plus_advisory_completed_stays_block() -> None:
    result = _run(context=_block_ctx())
    assert result.risk_evaluation.decision == "BLOCK"
    assert _status(result.advisory_artifact) == "completed"


def test_validation_fail_plus_advisory_completed_stays_fail() -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(
                    outcome=CheckOutcome.FAIL,
                    evidence=[_evidence("rule_fail")],
                )
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block())
    assert result.validation_artifact is not None
    assert result.validation_artifact.outcome == "fail"
    assert _status(result.advisory_artifact) == "completed"


def test_validation_pass_plus_advisory_unavailable_stays_pass() -> None:
    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[_check(outcome=CheckOutcome.PASS)],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(
            validation=_validation_block(),
            environ={},
            transport=FakeTransport(response=_http_ok()),
        )
    assert result.validation_artifact is not None
    assert result.validation_artifact.outcome == "pass"
    assert _status(result.advisory_artifact) == "unavailable"


def test_block_does_not_skip_requested_advisory() -> None:
    transport = FakeTransport(response=_http_ok())
    result = _run(context=_block_ctx(), transport=transport)
    assert result.risk_evaluation.decision == "BLOCK"
    assert len(transport.calls) == 1
    assert _status(result.advisory_artifact) == "completed"


def test_validation_fail_does_not_skip_requested_advisory() -> None:
    transport = FakeTransport(response=_http_ok())

    def _orch(plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint=plan.intake_reference.content_fingerprint,
            checks=[
                _check(
                    outcome=CheckOutcome.FAIL,
                    evidence=[_evidence("rule_fail")],
                )
            ],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation", side_effect=_orch
    ):
        result = _run(validation=_validation_block(), transport=transport)
    assert result.validation_artifact is not None
    assert result.validation_artifact.outcome == "fail"
    assert len(transport.calls) == 1
    assert _status(result.advisory_artifact) == "completed"


def test_deployment_authorized_always_false() -> None:
    result = _run()
    assert result.advisory_artifact is not None
    assert result.advisory_artifact.deployment_authorized is False
    meta = analysis_run_meta(validation_requested=False, advisory_requested=True)
    assert meta["deployment_authorized"] is False


def test_block_no_validation_advisory_not_requested() -> None:
    result = orchestrate_analysis_run(
        _request(context=_block_ctx(), advisory_requested=None)
    )
    assert result.risk_evaluation.decision == "BLOCK"
    assert result.validation_artifact is None
    assert result.advisory_requested is False
    assert result.advisory_artifact is None


# ==============================================================================
# Privacy — canaries never enter provider request body
# ==============================================================================


def test_provider_request_redacts_raw_identifiers() -> None:
    transport = FakeTransport(response=_http_ok())
    result = _run(transport=transport)
    assert len(transport.calls) == 1
    body_text = transport.calls[0]["body"].decode("utf-8")
    for canary in (
        CANARY_DB,
        CANARY_SCHEMA,
        CANARY_ASSET,
        CANARY_SOURCE,
        CANARY_TARGET,
        CANARY_REASON,
        CANARY_SQL,
        CANARY_FIXTURE,
        CANARY_EVIDENCE_MSG,
        API_KEY_CANARY,
    ):
        assert canary not in body_text
    assert "asset_1" in body_text
    assert "column_1" in body_text
    assert "column_2" in body_text
    dumped = result.model_dump(mode="json")
    assert "validation" not in dumped or "context_pack" not in json.dumps(dumped)
    # Run response must not embed the context pack object.
    assert "context_pack_version" not in json.dumps(dumped)
    assert "redaction" not in json.dumps(dumped) or "excluded_categories" not in json.dumps(
        dumped.get("advisory_artifact") or {}
    )


def test_run_response_has_no_context_pack() -> None:
    result = _run()
    dumped = result.model_dump(mode="json")
    assert "context_pack" not in dumped
    assert "subject_origin" not in json.dumps(dumped.get("advisory_artifact") or {})


# ==============================================================================
# API / OpenAPI / handler
# ==============================================================================


def test_endpoint_no_advisory_200() -> None:
    assert _client().post(ANALYZE_PATH, json=_body()).status_code == 200


def test_endpoint_invalid_advisory_extra_422() -> None:
    body = _body(include_advisory=True)
    body["advisory"]["api_key"] = "sk-leak"
    assert _client().post(ANALYZE_PATH, json=body).status_code == 422


def test_response_has_advisory_fields() -> None:
    data = _client().post(ANALYZE_PATH, json=_body()).json()["data"]
    assert "advisory_requested" in data
    assert "advisory_artifact" in data


def test_openapi_no_api_key_or_prompt_fields() -> None:
    schema = app.openapi()
    # AdvisoryRunOptions properties must only be requested (no key/model/prompt).
    components = schema.get("components", {}).get("schemas", {})
    options = components.get("AdvisoryRunOptions")
    assert options is not None
    props = set(options.get("properties", {}).keys())
    assert props == {"requested"}
    for banned in (
        "model",
        "prompt",
        "timeout",
        "retry",
        "transport",
        "temperature",
        "context_pack",
        "api_key",
        "endpoint",
        "DEEPSEEK_API_KEY",
    ):
        assert banned not in props
    # Analysis run request must not expose provider secrets fields.
    run_req = components.get("AnalysisRunRequest")
    assert run_req is not None
    run_props = set(run_req.get("properties", {}).keys())
    assert run_props == {
        "change",
        "evaluation_context",
        "validation",
        "advisory",
    }
    assert "api_key" not in run_props
    assert "model" not in run_props
    assert "prompt" not in run_props
    # Response AnalysisRunData must not add secret fields.
    run_data = components.get("AnalysisRunData")
    assert run_data is not None
    data_props = set(run_data.get("properties", {}).keys())
    assert "api_key" not in data_props
    assert "context_pack" not in data_props


def test_openapi_still_six_routes() -> None:
    schema = app.openapi()
    methods: list[str] = []
    for path, ops in schema.get("paths", {}).items():
        for method in ops:
            if method in ("get", "post", "put", "patch", "delete"):
                methods.append(f"{method.upper()} {path}")
    assert sorted(methods) == sorted(
        [
            "GET /health",
            "GET /ready",
            "POST /api/v1/changes/intake",
            "POST /api/v1/risk/evaluate",
            "POST /api/v1/runs/analyze",
            "POST /api/v1/validations/execute",
        ]
    )
    assert "advisory" not in " ".join(methods).lower()


def test_handler_remains_synchronous() -> None:
    assert not inspect.iscoroutinefunction(runs_route.analyze_run)
    assert not asyncio.iscoroutinefunction(runs_route.analyze_run)


# ==============================================================================
# Internal error boundary
# ==============================================================================


def test_risk_subject_mismatch_propagates() -> None:
    request = _request(advisory_requested=True)

    class _BadRisk:
        intake_id = uuid.uuid4()
        evaluated_content_fingerprint = "b" * 64
        decision = "ALLOW"

    with patch(
        "app.services.run_orchestrator.evaluate_risk",
        return_value=_BadRisk(),
    ):
        with pytest.raises(RuntimeError, match="risk evaluation"):
            orchestrate_analysis_run(
                request,
                advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
                advisory_transport=FakeTransport(response=_http_ok()),
            )


def test_validation_subject_mismatch_propagates() -> None:
    def _orch(_plan: Any) -> ValidationArtifact:
        return build_validation_artifact(
            subject_fingerprint="c" * 64,
            checks=[_check()],
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        with pytest.raises(RuntimeError, match="validation subject"):
            orchestrate_analysis_run(
                _request(validation=_validation_block(), advisory_requested=True),
                advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
                advisory_transport=FakeTransport(response=_http_ok()),
            )


def test_context_build_error_not_mapped_to_unavailable() -> None:
    transport = FakeTransport(response=_http_ok())
    with patch(
        "app.services.run_orchestrator.build_advisory_context_pack",
        side_effect=AdvisoryContextBuildError(
            code="intake_fingerprint_mismatch",
            message="Intake fingerprint is inconsistent.",
        ),
    ):
        with pytest.raises(AdvisoryContextBuildError):
            orchestrate_analysis_run(
                _request(advisory_requested=True),
                advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
                advisory_transport=transport,
            )
    assert transport.calls == []


def test_programming_error_not_swallowed_as_advisory_error() -> None:
    with patch(
        "app.services.run_orchestrator.build_advisory_context_pack",
        side_effect=RuntimeError("boom programming"),
    ):
        with pytest.raises(RuntimeError, match="boom programming"):
            orchestrate_analysis_run(
                _request(advisory_requested=True),
                advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
                advisory_transport=FakeTransport(response=_http_ok()),
            )


def test_context_build_error_via_api_is_safe_500() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch(
        "app.services.run_orchestrator.build_advisory_context_pack",
        side_effect=AdvisoryContextBuildError(
            code="risk_subject_mismatch",
            message="Risk subject is inconsistent.",
        ),
    ):
        with patch(
            "app.services.run_orchestrator.load_deepseek_provider_config",
            return_value=None,
        ):
            response = client.post(
                ANALYZE_PATH,
                json=_body(advisory={"requested": True}, include_advisory=True),
            )
    # Unhandled service errors surface as 500 envelope (no partial artifact).
    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "internal_error"
    text = json.dumps(body)
    assert API_KEY_CANARY not in text
    assert CANARY_DB not in text


# ==============================================================================
# Purity / mutation
# ==============================================================================


def test_request_objects_not_mutated() -> None:
    request = _request(advisory_requested=True)
    before = request.model_dump(mode="json")
    orchestrate_analysis_run(
        request,
        advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
        advisory_transport=FakeTransport(response=_http_ok()),
    )
    assert request.model_dump(mode="json") == before


def test_fake_transport_injection_without_network_monkeypatch() -> None:
    transport = FakeTransport(response=_http_ok())
    # No urllib/socket patches — injection alone is sufficient.
    result = orchestrate_analysis_run(
        _request(advisory_requested=True),
        advisory_environ={DEEPSEEK_API_KEY_ENV: API_KEY_CANARY},
        advisory_transport=transport,
    )
    assert _status(result.advisory_artifact) == "completed"
    assert len(transport.calls) == 1


def test_analysis_run_data_rejects_requested_without_artifact() -> None:
    intake = process_change_intake(ChangeIntakeRequest.model_validate(_change()))
    from app.schemas.risk import IntakeReference, RiskEvaluateRequest
    from app.schemas.changes import NormalizedChange
    from app.services.risk_engine import evaluate_risk

    risk = evaluate_risk(
        RiskEvaluateRequest(
            intake_reference=IntakeReference(
                intake_id=intake.intake_id,
                normalized_change=NormalizedChange.model_validate(
                    intake.normalized_change
                ),
                content_fingerprint=intake.content_fingerprint,
                artifact_version=intake.artifact_version,
            ),
            evaluation_context=EvaluationContext.model_validate(_allow_ctx()),
        )
    )
    with pytest.raises(ValidationError):
        AnalysisRunData(
            run_id=uuid.uuid4(),
            change_intake=intake,
            risk_evaluation=risk,
            advisory_requested=True,
            advisory_artifact=None,
        )


def test_analysis_run_data_rejects_artifact_when_not_requested() -> None:
    result = _run()
    with pytest.raises(ValidationError):
        AnalysisRunData(
            run_id=result.run_id,
            change_intake=result.change_intake,
            risk_evaluation=result.risk_evaluation,
            advisory_requested=False,
            advisory_artifact=result.advisory_artifact,
        )
