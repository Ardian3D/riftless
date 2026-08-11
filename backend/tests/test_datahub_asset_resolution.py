from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.integrations.datahub.asset_resolution import (
    RESOLUTION_VERSION,
    DataHubAssetCandidateResolution,
    DataHubAssetResolutionConfidence,
    DataHubAssetResolutionError,
    DataHubAssetResolutionMethod,
    DataHubAssetResolutionStatus,
    DataHubAssetResolutionSubject,
    build_datahub_asset_resolution_subject,
    build_datahub_asset_search_query,
    build_datahub_resolved_subject_from_resolution,
    resolve_datahub_asset_candidate,
)
from app.integrations.datahub.search_execution import DataHubDatasetSearchRecord, DataHubSearchExecutionResult
from app.schemas.changes import NormalizedChange
from app.schemas.datahub_context import DataHubResolutionMethod, DataHubResolvedSubject

RESOLVED = DataHubAssetResolutionStatus.RESOLVED
AMBIGUOUS = DataHubAssetResolutionStatus.AMBIGUOUS
UNRESOLVED = DataHubAssetResolutionStatus.UNRESOLVED
EXACT = DataHubAssetResolutionConfidence.EXACT
HIGH = DataHubAssetResolutionConfidence.HIGH
FQ_METHOD = DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED
DATASET_METHOD = DataHubAssetResolutionMethod.EXACT_DATASET_NAME
DISPLAY_METHOD = DataHubAssetResolutionMethod.EXACT_DISPLAY_NAME
URN_METHOD = DataHubAssetResolutionMethod.EXACT_URN_DATASET_NAME

ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,PROD)"
ORDERS_URN_ALT = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,DEV)"
BIGQUERY_ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:bigquery,analytics.core.orders,PROD)"
UNPARSEABLE_URN = "urn:li:dataset:(urn:li:dataPlatform,no-comma-shape)"


def subject(**overrides) -> DataHubAssetResolutionSubject:
    values = {"platform": "snowflake", "database": "analytics", "schema_name": "core", "table_name": "orders", "affected_column": "customer_id"}
    values.update(overrides)
    return DataHubAssetResolutionSubject(**values)


def record(urn: str = ORDERS_URN, display: str | None = None, position: int = 0) -> DataHubDatasetSearchRecord:
    return DataHubDatasetSearchRecord(dataset_urn=urn, display_name=display, source_position=position)


def result(*records) -> DataHubSearchExecutionResult:
    return DataHubSearchExecutionResult(
        request_id=3,
        next_request_id=4,
        search_request_fingerprint="a" * 64,
        input_schema_fingerprint="b" * 64,
        records=tuple(records),
        provider_start=0,
        provider_count=len(records),
        provider_total=len(records),
        non_dataset_result_count=0,
        result_version="1.0",
    )


def normalize_change(**overrides) -> NormalizedChange:
    payload = {
        "change_type": "rename_column",
        "asset": {"platform": "snowflake", "database": "analytics", "schema": "core", "name": "orders"},
        "source_column": "customer_id",
        "target_column": "account_id",
        "reason": None,
    }
    payload.update(overrides)
    return NormalizedChange.model_validate(payload)


class TestSubjectContract:
    def test_valid_subject_from_existing_normalized_change_fields(self) -> None:
        s = build_datahub_asset_resolution_subject(normalized=normalize_change())
        assert s.platform == "snowflake"
        assert s.database == "analytics"
        assert s.schema_name == "core"
        assert s.table_name == "orders"
        assert s.affected_column == "customer_id"

    def test_subject_is_immutable(self) -> None:
        s = subject()
        assert s.model_config["frozen"] is True
        with pytest.raises(ValidationError):
            s.platform = "postgres"
        with pytest.raises(ValidationError):
            s.affected_column = "other"

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            subject(query="/q orders")
        with pytest.raises(ValidationError):
            subject(asset_kind="dataset")

    def test_blank_required_identifier_rejected(self) -> None:
        for field in ("platform", "database", "schema_name", "table_name"):
            with pytest.raises(ValidationError):
                subject(**{field: "   "})

    def test_oversized_identifier_rejected(self) -> None:
        with pytest.raises(ValidationError):
            subject(table_name="x" * 257)
        with pytest.raises(ValidationError):
            subject(database="x" * 129)
        with pytest.raises(ValidationError):
            subject(platform="x" * 65)

    def test_null_and_control_characters_rejected(self) -> None:
        with pytest.raises(ValidationError):
            subject(table_name="bad\x00name")
        with pytest.raises(ValidationError):
            subject(schema_name="bad\nname")
        with pytest.raises(ValidationError):
            subject(affected_column="bad\x01column")

    def test_raw_sql_is_not_carried(self) -> None:
        s = build_datahub_asset_resolution_subject(normalized=normalize_change(reason="select * from orders"))
        assert s.model_dump() == {
            "platform": "snowflake",
            "database": "analytics",
            "schema_name": "core",
            "table_name": "orders",
            "affected_column": "customer_id",
        }
        assert "sql" not in s.model_dump()

    def test_no_arbitrary_query_field(self) -> None:
        with pytest.raises(ValidationError):
            subject(query="free text")
        assert "query" not in subject().model_dump()

    def test_no_credentials(self) -> None:
        with pytest.raises(ValidationError):
            subject(endpoint="https://datahub.example.com/mcp")
        with pytest.raises(ValidationError):
            subject(token="secret")
        with pytest.raises(ValidationError):
            subject(session_id="session-1")

    def test_no_risk_or_validation_fields(self) -> None:
        dumped = subject().model_dump()
        for key in ("decision", "risk_score", "outcome", "validation_result", "deployment_authorized", "writeback"):
            assert key not in dumped
        with pytest.raises(ValidationError):
            subject(decision="ALLOW")

    def test_invalid_subject_builder_input(self) -> None:
        with pytest.raises(DataHubAssetResolutionError) as exc:
            build_datahub_asset_resolution_subject(normalized=object())
        assert exc.value.code == "invalid_asset_resolution_subject"


class TestQueryBuilder:
    def test_deterministic_and_same_subject_same_query(self) -> None:
        assert build_datahub_asset_search_query(subject=subject()) == build_datahub_asset_search_query(subject=subject())

    def test_exact_q_prefix(self) -> None:
        query = build_datahub_asset_search_query(subject=subject())
        assert query == "/q analytics.core.orders"
        assert query.startswith("/q ")

    def test_length_bounded_and_no_newline_or_control(self) -> None:
        query = build_datahub_asset_search_query(subject=subject())
        assert 4 <= len(query) <= 512
        assert "\n" not in query and "\r" not in query
        assert not any(ord(ch) < 32 or ord(ch) == 127 for ch in query)
        assert "\x00" not in query

    def test_no_markdown_fence(self) -> None:
        assert "```" not in build_datahub_asset_search_query(subject=subject())

    def test_no_raw_sql(self) -> None:
        query = build_datahub_asset_search_query(subject=subject())
        assert "select" not in query and "insert" not in query and "update" not in query and "delete" not in query

    def test_derived_only_from_normalized_identity(self) -> None:
        assert build_datahub_asset_search_query(subject=subject()) == "/q analytics.core.orders"
        assert build_datahub_asset_search_query(subject=subject(database="raw")) == "/q raw.core.orders"

    def test_caller_cannot_supply_arbitrary_query(self) -> None:
        assert "query" not in inspect.signature(build_datahub_asset_search_query).parameters
        with pytest.raises(TypeError):
            build_datahub_asset_search_query(subject=subject(), query="/q custom")

    def test_subject_instance_required(self) -> None:
        with pytest.raises(DataHubAssetResolutionError) as exc:
            build_datahub_asset_search_query(subject="orders")
        assert exc.value.code == "invalid_asset_resolution_subject"

    def test_qualified_name_fallback_when_too_long(self) -> None:
        s = subject(database="d" * 128, schema_name="s" * 128, table_name="t" * 256)
        assert build_datahub_asset_search_query(subject=s) == "/q " + "t" * 256

    def test_sql_like_query_content_is_rejected(self) -> None:
        s = subject(database="d" * 128, schema_name="s" * 128, table_name="select " + "x" * 245)
        with pytest.raises(DataHubAssetResolutionError) as exc:
            build_datahub_asset_search_query(subject=s)
        assert exc.value.code == "asset_resolution_query_invalid"


class TestExactMatching:
    def test_zero_candidates_is_unresolved(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result())
        assert resolution.status is UNRESOLVED
        assert resolution.confidence is DataHubAssetResolutionConfidence.NONE
        assert resolution.resolution_method is DataHubAssetResolutionMethod.UNRESOLVED

    def test_one_exact_candidate_is_resolved(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()))
        assert resolution.status is RESOLVED
        assert resolution.selected_dataset_urn == ORDERS_URN
        assert resolution.resolution_method is FQ_METHOD
        assert resolution.confidence is EXACT

    def test_unique_strongest_exact_candidate_beats_weaker(self) -> None:
        strong = record(ORDERS_URN)
        weak = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)", display="orders")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(weak, strong))
        assert resolution.status is RESOLVED
        assert resolution.selected_dataset_urn == ORDERS_URN
        assert resolution.resolution_method is FQ_METHOD

    def test_two_strongest_exact_candidates_is_ambiguous(self) -> None:
        first = record(ORDERS_URN)
        second = record(ORDERS_URN_ALT)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(first, second))
        assert resolution.status is AMBIGUOUS
        assert resolution.strongest_match_count == 2

    def test_exact_display_name_match_resolves(self) -> None:
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)", display="orders")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is RESOLVED
        assert resolution.resolution_method is DISPLAY_METHOD
        assert resolution.confidence is HIGH

    def test_exact_urn_dataset_name_match_resolves(self) -> None:
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,orders,PROD)")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is RESOLVED
        assert resolution.resolution_method is DATASET_METHOD

    def test_case_normalized_exact_comparison(self) -> None:
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,ANALYTICS.CORE.ORDERS,PROD)")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is RESOLVED
        assert resolution.selected_dataset_urn == candidate.dataset_urn

    def test_whitespace_normalized_subject_matches(self) -> None:
        s = DataHubAssetResolutionSubject(platform="snowflake", database=" analytics ", schema_name="core", table_name=" orders ", affected_column="customer_id")
        resolution = resolve_datahub_asset_candidate(subject=s, search_result=result(record()))
        assert s.database == "analytics" and s.table_name == "orders"
        assert resolution.status is RESOLVED

    def test_non_matching_candidate_is_unresolved(self) -> None:
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)", display="customers")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is UNRESOLVED
        assert resolution.strongest_match_count == 0

    def test_provider_position_alone_never_resolves(self) -> None:
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:other,other.table,PROD)", display="unrelated", position=0)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is UNRESOLVED

    def test_first_result_is_not_automatically_winner(self) -> None:
        first = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)", position=0)
        last = record(ORDERS_URN, position=1)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(first, last))
        assert resolution.status is RESOLVED
        assert resolution.selected_dataset_urn == ORDERS_URN
        assert resolution.selected_source_position == 1

    def test_last_result_may_win_when_exact(self) -> None:
        first = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)", position=0)
        last = record(ORDERS_URN, position=4)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(first, last))
        assert resolution.selected_dataset_urn == ORDERS_URN
        assert resolution.selected_source_position == 4

    def test_lexical_urn_order_does_not_decide_tie(self) -> None:
        a = record(ORDERS_URN)
        b = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,ZZZ)")
        for ordered in ((a, b), (b, a)):
            resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(*ordered))
            assert resolution.status is AMBIGUOUS


class TestOrderIndependence:
    @pytest.mark.parametrize("order", [(0, 1, 2), (2, 1, 0), (1, 2, 0), (2, 0, 1)])
    def test_unique_exact_candidate_stable_across_permutations(self, order) -> None:
        exact = record(ORDERS_URN)
        weak = record("urn:li:dataset:(urn:li:dataPlatform:other,other.thing,PROD)", display="orders")
        other = record("urn:li:dataset:(urn:li:dataPlatform:other,other.table,PROD)", display="products")
        candidates = [exact, weak, other]
        reordered = [candidates[index] for index in order]
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(*reordered))
        assert resolution.status is RESOLVED
        assert resolution.selected_dataset_urn == exact.dataset_urn

    def test_winner_unchanged_when_candidate_order_reversed(self) -> None:
        exact = record(ORDERS_URN)
        weak = record("urn:li:dataset:(urn:li:dataPlatform:other,other.thing,PROD)", display="orders")
        forward = resolve_datahub_asset_candidate(subject=subject(), search_result=result(weak, exact))
        reversed_result = resolve_datahub_asset_candidate(subject=subject(), search_result=result(exact, weak))
        assert forward.selected_dataset_urn == reversed_result.selected_dataset_urn == exact.dataset_urn
        assert forward.status is reversed_result.status is RESOLVED

    def test_ambiguous_unchanged_when_candidate_order_reversed(self) -> None:
        a = record(ORDERS_URN, position=0)
        b = record(ORDERS_URN_ALT, position=1)
        forward = resolve_datahub_asset_candidate(subject=subject(), search_result=result(a, b))
        reversed_result = resolve_datahub_asset_candidate(subject=subject(), search_result=result(b, a))
        assert forward.status is reversed_result.status is AMBIGUOUS
        assert forward.selected_dataset_urn is None and reversed_result.selected_dataset_urn is None

    def test_unresolved_unchanged_under_permutation(self) -> None:
        candidates = [
            record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)", display="customers"),
            record("urn:li:dataset:(urn:li:dataPlatform:other,other.table,PROD)", display="other"),
        ]
        for order in ((0, 1), (1, 0)):
            resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(*[candidates[i] for i in order]))
            assert resolution.status is UNRESOLVED

    def test_source_position_never_breaks_strongest_match_tie(self) -> None:
        a = record(ORDERS_URN, position=0)
        b = record(ORDERS_URN_ALT, position=9)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(a, b))
        assert resolution.status is AMBIGUOUS
        assert resolution.selected_source_position is None


class TestAmbiguity:
    def test_distinct_urns_with_same_strongest_name_ambiguous(self) -> None:
        a = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,db1.orders,PROD)")
        b = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,db2.orders,PROD)")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(a, b))
        assert resolution.status is AMBIGUOUS
        assert resolution.strongest_match_count == 2

    def test_ambiguous_selected_dataset_urn_is_null(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN), record(ORDERS_URN_ALT)))
        assert resolution.status is AMBIGUOUS
        assert resolution.selected_dataset_urn is None

    def test_ambiguous_selected_source_position_is_null(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN), record(ORDERS_URN_ALT)))
        assert resolution.status is AMBIGUOUS
        assert resolution.selected_source_position is None

    def test_ambiguous_strongest_match_count_at_least_two(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN), record(ORDERS_URN_ALT)))
        assert resolution.strongest_match_count >= 2

    def test_ambiguity_never_downgraded_to_weaker_unique_candidate(self) -> None:
        strong_a = record(ORDERS_URN)
        strong_b = record(ORDERS_URN_ALT)
        weak = record("urn:li:dataset:(urn:li:dataPlatform:other,other.thing,PROD)", display="orders")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(strong_a, strong_b, weak))
        assert resolution.status is AMBIGUOUS
        assert resolution.selected_dataset_urn is None

    def test_ambiguity_never_uses_provider_order_as_tiebreaker(self) -> None:
        a = record(ORDERS_URN)
        b = record(ORDERS_URN_ALT)
        for ordered in ((a, b), (b, a)):
            resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(*ordered))
            assert resolution.status is AMBIGUOUS
            assert resolution.selected_source_position is None


class TestPlatformEligibility:
    def test_matching_fq_and_platform_resolves(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN)))
        assert resolution.status is RESOLVED
        assert resolution.resolution_method is FQ_METHOD

    def test_matching_fq_wrong_platform_not_resolved(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(BIGQUERY_ORDERS_URN)))
        assert resolution.status is UNRESOLVED
        assert resolution.strongest_match_count == 0

    def test_matching_table_name_wrong_platform_not_resolved(self) -> None:
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:bigquery,legacy.other.orders,PROD)")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is UNRESOLVED

    def test_matching_display_name_wrong_platform_not_resolved(self) -> None:
        candidate = record(BIGQUERY_ORDERS_URN, display="analytics.core.orders")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is UNRESOLVED

    def test_matching_display_name_unparseable_platform_not_resolved(self) -> None:
        candidate = record(UNPARSEABLE_URN, display="analytics.core.orders")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is UNRESOLVED

    def test_matching_table_name_unparseable_platform_not_resolved(self) -> None:
        candidate = record(UNPARSEABLE_URN, display="orders")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is UNRESOLVED

    def test_case_normalized_platform_equality_accepted(self) -> None:
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:SNOWFLAKE,analytics.core.orders,PROD)")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.status is RESOLVED
        assert resolution.resolution_method is FQ_METHOD

    def test_no_platform_alias_postgres_not_postgresql(self) -> None:
        s = subject(platform="postgres")
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:postgresql,analytics.core.orders,PROD)")
        resolution = resolve_datahub_asset_candidate(subject=s, search_result=result(candidate))
        assert resolution.status is UNRESOLVED

    def test_same_name_one_matching_one_wrong_platform_matching_wins(self) -> None:
        wrong = record("urn:li:dataset:(urn:li:dataPlatform:bigquery,legacy.other.orders,PROD)", display="orders")
        right = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,legacy.other.orders,PROD)", display="orders")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(wrong, right))
        assert resolution.status is RESOLVED
        assert resolution.selected_dataset_urn == right.dataset_urn

    def test_two_fq_same_name_different_platform_only_subject_platform_eligible(self) -> None:
        wrong = record(BIGQUERY_ORDERS_URN)
        right = record(ORDERS_URN)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(wrong, right))
        assert resolution.status is RESOLVED
        assert resolution.selected_dataset_urn == ORDERS_URN
        assert resolution.strongest_match_count == 1

    def test_two_fq_same_name_same_platform_different_urns_ambiguous(self) -> None:
        a = record(ORDERS_URN)
        b = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,DEV)")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(a, b))
        assert resolution.status is AMBIGUOUS
        assert resolution.strongest_match_count == 2

    def test_wrong_platform_first_cannot_win(self) -> None:
        wrong = record(BIGQUERY_ORDERS_URN, position=0)
        right = record(ORDERS_URN, position=1)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(wrong, right))
        assert resolution.selected_dataset_urn == ORDERS_URN

    def test_wrong_platform_last_cannot_win(self) -> None:
        right = record(ORDERS_URN, position=0)
        wrong = record(BIGQUERY_ORDERS_URN, position=1)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(right, wrong))
        assert resolution.selected_dataset_urn == ORDERS_URN

    def test_reversing_provider_order_does_not_change_selected_urn(self) -> None:
        right = record(ORDERS_URN)
        wrong = record(BIGQUERY_ORDERS_URN)
        forward = resolve_datahub_asset_candidate(subject=subject(), search_result=result(wrong, right))
        reversed_result = resolve_datahub_asset_candidate(subject=subject(), search_result=result(right, wrong))
        assert forward.selected_dataset_urn == reversed_result.selected_dataset_urn == ORDERS_URN

    def test_source_position_cannot_rescue_wrong_platform(self) -> None:
        wrong = record(BIGQUERY_ORDERS_URN, position=0)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(wrong))
        assert resolution.status is UNRESOLVED
        weak = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,legacy.other.customers,PROD)", display="customers", position=1)
        combined = resolve_datahub_asset_candidate(subject=subject(), search_result=result(wrong, weak))
        assert combined.status is UNRESOLVED

    def test_weaker_same_platform_beats_stronger_looking_wrong_platform(self) -> None:
        wrong_fq = record(BIGQUERY_ORDERS_URN, position=0)
        right_dataset = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,legacy.other.orders,PROD)", position=1)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(wrong_fq, right_dataset))
        assert resolution.status is RESOLVED
        assert resolution.selected_dataset_urn == right_dataset.dataset_urn
        assert resolution.resolution_method is DATASET_METHOD

    def test_conversion_confirms_candidate_platform_before_success(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN)))
        resolved = build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=resolution)
        assert resolved.platform == "snowflake"

    def test_conversion_rejects_platform_inconsistency(self) -> None:
        resolution = DataHubAssetCandidateResolution(
            status=RESOLVED,
            selected_dataset_urn=BIGQUERY_ORDERS_URN,
            confidence=EXACT,
            resolution_method=FQ_METHOD,
            candidate_count=1,
            strongest_match_count=1,
            selected_source_position=0,
        )
        with pytest.raises(DataHubAssetResolutionError) as exc:
            build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=resolution)
        assert exc.value.code == "asset_resolution_invariant_violation"

    def test_ambiguous_and_unresolved_conversion_remains_rejected(self) -> None:
        ambiguous = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN), record(ORDERS_URN_ALT)))
        unresolved = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(BIGQUERY_ORDERS_URN)))
        with pytest.raises(DataHubAssetResolutionError):
            build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=ambiguous)
        with pytest.raises(DataHubAssetResolutionError):
            build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=unresolved)

    def test_exact_confidence_does_not_claim_environment_verification(self) -> None:
        single = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,DEV)")))
        assert single.status is RESOLVED
        assert single.confidence is EXACT
        assert "environment" not in subject().model_dump()
        assert "environment" not in single.model_dump()
        readme = Path(__file__).parents[1].joinpath("README.md").read_text(encoding="utf-8")
        assert "does not verify the" in readme and "DataHub environment" in readme

    def test_hierarchy_overlap_predicates_are_distinct_and_deterministic(self) -> None:
        dataset_candidate = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,legacy.orders,PROD)")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(dataset_candidate))
        assert resolution.resolution_method is DATASET_METHOD
        same_raw = record(ORDERS_URN, display="analytics.core.orders")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(same_raw))
        assert resolution.resolution_method is FQ_METHOD

    def test_no_network_or_provider_call_introduced(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/asset_resolution.py").read_text(encoding="utf-8")
        for token in ("post_request", "tools/call", "import requests", "import httpx", "import aiohttp", "urllib", "http.client"):
            assert token not in source


class TestResultContract:
    def test_resolved_result_exact_fields(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()))
        assert resolution.model_dump() == {
            "status": "resolved",
            "selected_dataset_urn": ORDERS_URN,
            "confidence": "exact",
            "resolution_method": "exact_fully_qualified",
            "candidate_count": 1,
            "strongest_match_count": 1,
            "selected_source_position": 0,
            "resolution_version": "1.0",
        }

    def test_unresolved_result_exact_fields(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result())
        assert resolution.model_dump() == {
            "status": "unresolved",
            "selected_dataset_urn": None,
            "confidence": "none",
            "resolution_method": "unresolved",
            "candidate_count": 0,
            "strongest_match_count": 0,
            "selected_source_position": None,
            "resolution_version": "1.0",
        }

    def test_ambiguous_result_exact_fields(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN), record(ORDERS_URN_ALT)))
        assert resolution.model_dump() == {
            "status": "ambiguous",
            "selected_dataset_urn": None,
            "confidence": "ambiguous",
            "resolution_method": "ambiguous",
            "candidate_count": 2,
            "strongest_match_count": 2,
            "selected_source_position": None,
            "resolution_version": "1.0",
        }

    def test_candidate_count_is_derived(self) -> None:
        assert resolve_datahub_asset_candidate(subject=subject(), search_result=result()).candidate_count == 0
        distinct = [
            record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)"),
            record("urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.products,PROD)"),
            record("urn:li:dataset:(urn:li:dataPlatform:other,other.table,PROD)"),
        ]
        assert resolve_datahub_asset_candidate(subject=subject(), search_result=result(*distinct)).candidate_count == 3

    def test_strongest_match_count_is_derived(self) -> None:
        assert resolve_datahub_asset_candidate(subject=subject(), search_result=result(record())).strongest_match_count == 1
        assert resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN), record(ORDERS_URN_ALT))).strongest_match_count == 2
        assert resolve_datahub_asset_candidate(subject=subject(), search_result=result()).strongest_match_count == 0

    def test_result_is_immutable(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()))
        assert resolution.model_config["frozen"] is True
        with pytest.raises(ValidationError):
            resolution.status = "resolved"

    def test_resolution_version_is_fixed(self) -> None:
        assert RESOLUTION_VERSION == "1.0"
        assert resolve_datahub_asset_candidate(subject=subject(), search_result=result(record())).resolution_version == "1.0"

    def test_selected_urn_structurally_valid_when_resolved(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()))
        urn = resolution.selected_dataset_urn
        assert urn is not None
        assert urn.startswith("urn:li:dataset:(") and urn.endswith(")")
        assert len(urn) >= 8 and not any(ch.isspace() for ch in urn)

    def test_no_selected_urn_for_ambiguous(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN), record(ORDERS_URN_ALT)))
        assert resolution.status is AMBIGUOUS
        assert resolution.selected_dataset_urn is None

    def test_no_selected_urn_for_unresolved(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result())
        assert resolution.status is UNRESOLVED
        assert resolution.selected_dataset_urn is None

    def test_no_raw_candidate_payload_or_query(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(display="orders")))
        dumped = json.dumps(resolution.model_dump())
        for token in ("records", "searchResults", "structuredContent", "facets", "isError", "display_name", "query", "endpoint", "session", "authority"):
            assert token not in dumped

    def test_no_risk_or_writeback_authority(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()))
        dumped = resolution.model_dump()
        for key in ("decision", "risk_score", "outcome", "validation_result", "deployment_authorized", "writeback_authorized"):
            assert key not in dumped

    def test_invalid_candidate_set_rejected(self) -> None:
        with pytest.raises(DataHubAssetResolutionError) as exc:
            resolve_datahub_asset_candidate(subject=subject(), search_result=object())
        assert exc.value.code == "invalid_asset_resolution_candidate"
        with pytest.raises(DataHubAssetResolutionError) as exc:
            resolve_datahub_asset_candidate(subject="orders", search_result=result(record()))
        assert exc.value.code == "invalid_asset_resolution_subject"


class TestF8Compatibility:
    def test_resolved_conversion_succeeds(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()))
        resolved = build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=resolution)
        assert isinstance(resolved, DataHubResolvedSubject)
        assert resolved.dataset_urn == resolution.selected_dataset_urn == ORDERS_URN
        assert resolved.entity_kind.value == "dataset"
        assert resolved.platform == "snowflake"
        assert resolved.resolution_method is DataHubResolutionMethod.DATAHUB_SEARCH
        assert resolved.confidence == 1.0
        assert resolved.field_path == "customer_id"

    def test_high_confidence_resolution_maps_to_fixed_float(self) -> None:
        candidate = record("urn:li:dataset:(urn:li:dataPlatform:snowflake,db.orders,PROD)")
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(candidate))
        assert resolution.resolution_method is DATASET_METHOD
        assert resolution.confidence is HIGH
        resolved = build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=resolution)
        assert 0.0 <= resolved.confidence <= 1.0
        assert resolved.confidence < 1.0

    def test_ambiguity_cannot_convert_as_successful_resolution(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record(ORDERS_URN), record(ORDERS_URN_ALT)))
        with pytest.raises(DataHubAssetResolutionError) as exc:
            build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=resolution)
        assert exc.value.code == "asset_resolution_invariant_violation"

    def test_unresolved_cannot_fabricate_resolved_subject(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result())
        with pytest.raises(DataHubAssetResolutionError) as exc:
            build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=resolution)
        assert exc.value.code == "asset_resolution_invariant_violation"

    def test_f8_1_confidence_and_method_contract(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()))
        resolved = build_datahub_resolved_subject_from_resolution(subject=subject(), resolution=resolution)
        assert 0.0 <= resolved.confidence <= 1.0
        assert isinstance(resolved.resolution_method, DataHubResolutionMethod)
        assert resolved.resolution_method in {DataHubResolutionMethod.DATAHUB_SEARCH}
        revalidated = DataHubResolvedSubject(**resolved.model_dump())
        assert revalidated.dataset_urn == resolved.dataset_urn

    def test_f8_1_model_fields_remain_unchanged(self) -> None:
        assert set(DataHubResolvedSubject.model_fields) == {"dataset_urn", "entity_kind", "platform", "field_path", "resolution_method", "confidence"}


class TestScopeRegression:
    def test_scope_regression_source_audit(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/asset_resolution.py").read_text(encoding="utf-8")
        forbidden = (
            "post_request", "tools/call", "tools/list", "initialize", "get_entities", "list_schema_fields",
            "get_lineage", "DeepSeek", "logging", "print(", "except Exception", "subprocess", "os.environ",
            "import requests", "import httpx", "import aiohttp", "urllib", "http.client", "persistence",
            "writeback", "score",
        )
        assert all(token not in source for token in forbidden)

    def test_resolver_has_no_transport_or_network_parameters(self) -> None:
        assert set(inspect.signature(resolve_datahub_asset_candidate).parameters) == {"subject", "search_result"}
        with pytest.raises(TypeError):
            resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()), transport=object())

    def test_resolution_is_pure_and_side_effect_free(self) -> None:
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=result(record()))
        assert resolution.status is RESOLVED
        assert resolution.model_dump() == resolve_datahub_asset_candidate(subject=subject(), search_result=result(record())).model_dump()

    def test_production_openapi_route_count_remains_exactly_six(self) -> None:
        routes_dir = Path(__file__).parents[1].joinpath("app/api/routes")
        paths: set[tuple[str, str]] = set()
        for path in sorted(routes_dir.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for match in re.finditer(r"@router\.(get|post)\(\s*\n\s*\"([^\"]+)\"", source):
                paths.add((match.group(1), match.group(2)))
        assert paths == {
            ("get", "/health"),
            ("get", "/ready"),
            ("post", "/changes/intake"),
            ("post", "/risk/evaluate"),
            ("post", "/runs/analyze"),
            ("post", "/validations/execute"),
        }
        assert len(paths) == 6
