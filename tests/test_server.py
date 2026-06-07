"""Smoke tests for meok-fors-clocs-mcp."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    check_fors_bronze_readiness,
    check_fors_silver_readiness,
    check_fors_gold_readiness,
    prepare_fors_audit_pack,
    check_clocs_compliance,
    audit_dvsa_earned_recognition_data_feed,
    forecast_fors_renewal,
    crosswalk_fors_to_clocs,
    generate_corrective_action_plan,
    FORS_BRONZE_REQUIREMENTS,
    FORS_SILVER_ADDITIONAL,
    FORS_GOLD_ADDITIONAL,
    CLOCS_REQUIREMENTS,
    DVSA_ER_KPIS,
    DVSA_ER_ACCREDITED_IT_SUPPLIERS,
    FORS_STANDARD_CODES,
)


def _call(tool, **kwargs):
    """FastMCP wraps tools as Tool objects — extract the callable."""
    fn = tool.fn if hasattr(tool, "fn") else tool
    return fn(**kwargs)


def _all_true(keys):
    return {k: True for k in keys}


# ──────────────────────────────────────────────────────────────────────
# FORS Bronze
# ──────────────────────────────────────────────────────────────────────

def test_bronze_empty_operator_is_zero_pct():
    r = _call(check_fors_bronze_readiness, operator_data={})
    assert r["readiness_pct"] == 0.0
    assert r["requirements_met"] == 0
    assert r["estimated_weeks_to_ready"] >= 1
    assert r["level"] == "Bronze"


def test_bronze_fully_compliant_is_100_pct():
    full = _all_true(FORS_BRONZE_REQUIREMENTS.keys())
    r = _call(check_fors_bronze_readiness, operator_data=full)
    assert r["readiness_pct"] == 100.0
    assert r["missing_items"] == []
    assert r["estimated_weeks_to_ready"] == 0
    assert "Bronze-ready" in r["advisory"]


def test_bronze_partial_lists_missing():
    partial = {k: True for k in list(FORS_BRONZE_REQUIREMENTS.keys())[:10]}
    r = _call(check_fors_bronze_readiness, operator_data=partial)
    assert 0 < r["readiness_pct"] < 100
    assert len(r["missing_items"]) == len(FORS_BRONZE_REQUIREMENTS) - 10


# ──────────────────────────────────────────────────────────────────────
# FORS Silver
# ──────────────────────────────────────────────────────────────────────

def test_silver_requires_bronze_floor():
    # Silver requirements without Bronze underneath — advisory should warn
    silver_only = _all_true(FORS_SILVER_ADDITIONAL.keys())
    r = _call(check_fors_silver_readiness, operator_data=silver_only)
    assert r["bronze_floor_complete"] is False
    assert "Bronze first" in r["advisory"]


def test_silver_fully_compliant_is_100_pct():
    combined = {**_all_true(FORS_BRONZE_REQUIREMENTS.keys()),
                **_all_true(FORS_SILVER_ADDITIONAL.keys())}
    r = _call(check_fors_silver_readiness, operator_data=combined)
    assert r["readiness_pct"] == 100.0
    assert r["silver_specific_gaps"] == []
    assert "Silver-ready" in r["advisory"]


def test_silver_bronze_only_flags_silver_gaps():
    bronze_only = _all_true(FORS_BRONZE_REQUIREMENTS.keys())
    r = _call(check_fors_silver_readiness, operator_data=bronze_only)
    assert r["bronze_floor_complete"] is True
    assert len(r["silver_specific_gaps"]) == len(FORS_SILVER_ADDITIONAL)


# ──────────────────────────────────────────────────────────────────────
# FORS Gold
# ──────────────────────────────────────────────────────────────────────

def test_gold_silver_only_blocks_on_hard_gates():
    silver_complete = {**_all_true(FORS_BRONZE_REQUIREMENTS.keys()),
                       **_all_true(FORS_SILVER_ADDITIONAL.keys())}
    r = _call(check_fors_gold_readiness, operator_data=silver_complete)
    # G1 (12mo KPI) and G2 (75th percentile) should be blocking gates
    assert any("G1_kpi_12_month_history" in g for g in r["blocking_gates"])
    assert any("G2_peer_benchmark_percentile" in g for g in r["blocking_gates"])


def test_gold_fully_compliant_no_blocking_gates():
    full = {**_all_true(FORS_BRONZE_REQUIREMENTS.keys()),
            **_all_true(FORS_SILVER_ADDITIONAL.keys()),
            **_all_true(FORS_GOLD_ADDITIONAL.keys())}
    r = _call(check_fors_gold_readiness, operator_data=full)
    assert r["readiness_pct"] == 100.0
    assert r["blocking_gates"] == []
    assert "Gold-ready" in r["advisory"]


def test_bronze_lt_silver_lt_gold_progression():
    """Same partial data: Gold should always score <= Silver <= Bronze when scoring
    against the level-specific superset (more requirements => lower or equal pct)."""
    partial = {k: True for k in list(FORS_BRONZE_REQUIREMENTS.keys())[:15]}
    rb = _call(check_fors_bronze_readiness, operator_data=partial)
    rs = _call(check_fors_silver_readiness, operator_data=partial)
    rg = _call(check_fors_gold_readiness, operator_data=partial)
    assert rb["readiness_pct"] >= rs["readiness_pct"] >= rg["readiness_pct"]


# ──────────────────────────────────────────────────────────────────────
# FORS Audit Pack
# ──────────────────────────────────────────────────────────────────────

def test_audit_pack_bronze_has_all_standard_codes():
    r = _call(prepare_fors_audit_pack, target_level="bronze")
    assert r["target_level"] == "Bronze"
    assert set(r["standard_code_buckets"].keys()) == set(FORS_STANDARD_CODES)
    assert r["total_evidence_items"] == len(FORS_BRONZE_REQUIREMENTS)
    assert r["outstanding_items"] == len(FORS_BRONZE_REQUIREMENTS)


def test_audit_pack_silver_includes_silver_requirements():
    r = _call(prepare_fors_audit_pack, target_level="silver")
    assert r["target_level"] == "Silver"
    assert r["total_evidence_items"] == len(FORS_BRONZE_REQUIREMENTS) + len(FORS_SILVER_ADDITIONAL)


def test_audit_pack_invalid_level_errors():
    r = _call(prepare_fors_audit_pack, target_level="platinum")
    assert "error" in r


# ──────────────────────────────────────────────────────────────────────
# CLOCS
# ──────────────────────────────────────────────────────────────────────

def test_clocs_london_without_dvs_blocks():
    # All other items met, but C4_dvs_pss_3_star missing
    partial = {k: True for k in CLOCS_REQUIREMENTS if k != "C4_dvs_pss_3_star"}
    r = _call(check_clocs_compliance, operator_data=partial, project_type="tfl_construction")
    assert r["london_dvs_pss_gate_blocked"] is True
    assert "BLOCKED" in r["advisory"]


def test_clocs_full_compliance_passes():
    full = _all_true(CLOCS_REQUIREMENTS.keys())
    r = _call(check_clocs_compliance, operator_data=full, project_type="tfl_construction")
    assert r["compliance_pct"] == 100.0
    assert r["london_dvs_pss_gate_blocked"] is False


def test_clocs_non_london_project_dvs_not_blocking():
    partial = {k: True for k in CLOCS_REQUIREMENTS if k != "C4_dvs_pss_3_star"}
    r = _call(check_clocs_compliance, operator_data=partial, project_type="private_developer")
    assert r["london_dvs_pss_gate_blocked"] is False


# ──────────────────────────────────────────────────────────────────────
# DVSA Earned Recognition
# ──────────────────────────────────────────────────────────────────────

def test_dvsa_er_unaccredited_supplier_blocks():
    r = _call(audit_dvsa_earned_recognition_data_feed,
              operator_data={"it_supplier": "RandomSpreadsheet"})
    assert r["it_supplier_accredited"] is False
    assert r["er_admission_ready"] is False
    assert any("not DVSA-accredited" in i.replace(" ", "") or
               "not\nDVSA-accredited" in i.replace(" ", "") or
               "not-DVSA-accredited" in i.replace(" ", "") or
               "DVSA-accredited" in i for i in r["blocking_issues"])


def test_dvsa_er_full_compliance_admission_ready():
    op = {
        "it_supplier": "tachomaster",
        "audit_history_12mo_clean": True,
        "pg9_prohibitions_last_12mo": 0,
    }
    for k in DVSA_ER_KPIS.keys():
        op[k] = True
    r = _call(audit_dvsa_earned_recognition_data_feed, operator_data=op)
    assert r["er_admission_ready"] is True
    assert r["it_supplier_accredited"] is True


def test_dvsa_er_pg9_prohibitions_block():
    op = {
        "it_supplier": "isotrak",
        "audit_history_12mo_clean": True,
        "pg9_prohibitions_last_12mo": 2,
    }
    for k in DVSA_ER_KPIS.keys():
        op[k] = True
    r = _call(audit_dvsa_earned_recognition_data_feed, operator_data=op)
    assert r["er_admission_ready"] is False
    assert any("PG9" in i for i in r["blocking_issues"])


# ──────────────────────────────────────────────────────────────────────
# Renewal forecast
# ──────────────────────────────────────────────────────────────────────

def test_renewal_open_window_when_recent():
    from datetime import date, timedelta
    last = (date.today() - timedelta(days=320)).isoformat()  # 45 days to expiry → in window
    r = _call(forecast_fors_renewal, current_level="silver", last_audit_date=last)
    assert r["status"] == "RENEWAL_WINDOW_OPEN"


def test_renewal_not_yet_due_when_fresh():
    from datetime import date, timedelta
    last = (date.today() - timedelta(days=30)).isoformat()  # 335 days to expiry
    r = _call(forecast_fors_renewal, current_level="bronze", last_audit_date=last)
    assert r["status"] == "NOT_YET_DUE"


def test_renewal_lapsed_when_long_overdue():
    from datetime import date, timedelta
    last = (date.today() - timedelta(days=420)).isoformat()  # 55 days lapsed
    r = _call(forecast_fors_renewal, current_level="gold", last_audit_date=last)
    assert r["status"] == "LAPSED_REAPPLY_AS_NEW"


def test_renewal_invalid_level_errors():
    r = _call(forecast_fors_renewal, current_level="platinum",
              last_audit_date="2026-01-01")
    assert "error" in r


# ──────────────────────────────────────────────────────────────────────
# FORS → CLOCS crosswalk
# ──────────────────────────────────────────────────────────────────────

def test_crosswalk_silver_covers_majority_of_clocs():
    r = _call(crosswalk_fors_to_clocs, fors_level="silver")
    # Spec says >80% overlap is the goal — Silver should hit at least ~60%
    # (DVS PSS + CLOCS Champion are CLOCS-only by design).
    assert r["clocs_coverage_pct"] >= 60.0
    assert "C4_dvs_pss_3_star" in r["clocs_specific_gaps"]


def test_crosswalk_gold_covers_more_than_silver():
    rs = _call(crosswalk_fors_to_clocs, fors_level="silver")
    rg = _call(crosswalk_fors_to_clocs, fors_level="gold")
    assert rg["clocs_coverage_pct"] >= rs["clocs_coverage_pct"]


def test_crosswalk_invalid_level_errors():
    r = _call(crosswalk_fors_to_clocs, fors_level="diamond")
    assert "error" in r


# ──────────────────────────────────────────────────────────────────────
# Corrective Action Plan
# ──────────────────────────────────────────────────────────────────────

def test_cap_empty_gaps_returns_empty_plan():
    r = _call(generate_corrective_action_plan, audit_gaps=[])
    assert r["total_gaps"] == 0
    assert r["cap_items"] == []


def test_cap_sorts_critical_first():
    gaps = [
        {"code": "M1", "label": "Low priority bit", "severity": "low"},
        {"code": "V2", "label": "Critical safety equipment gap", "severity": "critical"},
        {"code": "D3", "label": "Medium training gap", "severity": "medium"},
        {"code": "S1", "label": "High priority KPI gap", "severity": "high"},
    ]
    r = _call(generate_corrective_action_plan, audit_gaps=gaps)
    assert r["total_gaps"] == 4
    assert r["cap_items"][0]["severity"] == "critical"
    assert r["critical_count"] == 1
    assert r["high_count"] == 1


def test_cap_handles_string_gaps():
    r = _call(generate_corrective_action_plan,
              audit_gaps=["Missing driver handbook", "No PMI schedule"])
    assert r["total_gaps"] == 2
    for item in r["cap_items"]:
        assert "evidence_required" in item
        assert item["owner"]


# ──────────────────────────────────────────────────────────────────────
# Attestation + tables
# ──────────────────────────────────────────────────────────────────────

def test_attestation_carries_ts_sig_issuer():
    r = _call(check_fors_bronze_readiness, operator_data={})
    assert "ts" in r and "sig" in r and "issuer" in r
    assert r["issuer"] == "meok-fors-clocs-mcp"
    assert "disclaimer" in r


def test_tables_sizes_match_spec():
    # FORS Bronze ~22, Silver +12, Gold +8; CLOCS 12; ER 9 KPIs
    assert len(FORS_BRONZE_REQUIREMENTS) == 22
    assert len(FORS_SILVER_ADDITIONAL) == 12
    assert len(FORS_GOLD_ADDITIONAL) == 8
    assert len(CLOCS_REQUIREMENTS) == 12
    assert len(DVSA_ER_KPIS) == 9
    assert len(DVSA_ER_ACCREDITED_IT_SUPPLIERS) >= 5
    assert len(FORS_STANDARD_CODES) == 15


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
