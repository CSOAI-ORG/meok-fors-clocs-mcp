#!/usr/bin/env python3
"""
MEOK FORS / CLOCS Compliance MCP
================================

By MEOK AI Labs · https://haulage.app · MIT
<!-- mcp-name: io.github.CSOAI-ORG/meok-fors-clocs-mcp -->

WHAT THIS DOES
--------------
UK general haulage + plant-hire operators face three overlapping audit regimes
that are TENDER-GATING (a Tier-1 contractor or public-sector buyer will not
engage you without them):

  - FORS (Fleet Operator Recognition Scheme) — Bronze / Silver / Gold
  - CLOCS (Construction Logistics And Community Safety) — for construction
    work originating in the GLA, HS2 supply chain, or any project that
    contractually requires it
  - DVSA Earned Recognition (ER) — the regulator's "trusted operator" scheme,
    requires a 4-weekly KPI data feed from your tachograph + maintenance
    systems via an approved IT supplier

Preparing for these audits today commonly costs 80+ consultancy hours at
£300-£500/hr. This MCP gives operators, transport managers, and compliance
consultants a callable readiness toolkit that:

  - Scores the operator against the published standards
  - Lists exactly what evidence is missing
  - Builds an audit pack checklist tied to the S1-S15 standard codes
  - Cross-walks FORS evidence to CLOCS requirements (>80% overlap)
  - Forecasts renewal windows and corrective-action plans

HONESTY NOTE
------------
This MCP SUPPORTS auditors, transport managers, and operators preparing for
the formal FORS / CLOCS / DVSA-ER audit. It does NOT and CANNOT replace the
formal audit itself. FORS audits are conducted by FORS-approved auditors;
CLOCS Champion status is awarded by the CLOCS Community; DVSA-ER admission
is granted by DVSA following a desktop + onsite review. Treat the outputs
as a readiness gap analysis, not an accreditation.

TOOLS (9)
---------
- check_fors_bronze_readiness(operator_data)              → Bronze gap report
- check_fors_silver_readiness(operator_data)              → Silver gap report
- check_fors_gold_readiness(operator_data)                → Gold gap report
- prepare_fors_audit_pack(operator_data, target_level)    → S1-S15 checklist
- check_clocs_compliance(operator_data, project_type)     → CLOCS v3.0 score
- audit_dvsa_earned_recognition_data_feed(operator_data)  → ER KPI feed audit
- forecast_fors_renewal(current_level, last_audit_date)   → renewal window
- crosswalk_fors_to_clocs(fors_level)                     → evidence reuse map
- generate_corrective_action_plan(audit_gaps)             → prioritised CAP

WHY YOU PAY
-----------
A single FORS Bronze audit consultancy engagement is £4-12k. A blocked tender
because you lack FORS Silver loses £100k-£1m in revenue. The Pro plan pays
for itself the first time you reuse evidence between FORS and CLOCS audits.

PRICING
-------
Free MIT self-host · £49 Starter · £149 Pro · £499 Fleet · £1,499 ER tier.

REGULATORY BASIS
----------------
FORS Standard v6.1 (in force 2026)
CLOCS Standard v3.0
TfL Construction Logistics Plan guidance
DVSA Earned Recognition data-feed specification
DVS PSS (Direct Vision Standard — Progressive Safe System), 3-star+ mandatory
in London from 28 October 2024
HSE INDG403 (Driving at Work risk management)
ISO 39001 (Road Traffic Safety Management) — referenced by FORS Gold
"""

from __future__ import annotations
import urllib.request as _meter_urlreq
import urllib.error as _meter_urlerr
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("meok-fors-clocs")
_HMAC_SECRET = os.environ.get("MEOK_HMAC_SECRET", "")


# ──────────────────────────────────────────────────────────────────────
# Regulatory tables (FORS v6.1, CLOCS v3.0, DVSA-ER)
# ──────────────────────────────────────────────────────────────────────

# FORS Bronze — 22 requirements grouped under standard codes M (Management),
# V (Vehicle), D (Driver), O (Operations). This is the public-tender floor.
FORS_BRONZE_REQUIREMENTS = {
    "M1_management_responsibility": "Named transport manager + responsibility statement",
    "M2_health_and_safety_policy": "Written H&S policy reviewed within 12 months",
    "M3_responsibilities": "Documented roles + responsibilities (org chart)",
    "M4_communication": "Toolbox talks / staff briefings log",
    "M5_regulatory_licensing": "Valid O-Licence + ID checks on file",
    "V1_serviceability": "Daily walk-around check records (driver defect reporting)",
    "V2_safety_equipment": "Class V / VI mirrors, side-guards, audible reverse alarm (where required)",
    "V3_emissions": "Emissions standards meet local CAZ / ULEZ minima",
    "V4_load_restraint": "Documented load-restraint policy + driver training",
    "V5_in_vehicle_telematics": "Tracking + harsh-event capture (recommended Bronze, required Silver)",
    "D1_licensing": "Driver licence checks every 6 months minimum",
    "D2_health_and_eyesight": "Pre-employment + ongoing medical / eyesight records",
    "D3_induction": "Documented driver induction within first 4 weeks",
    "D4_training": "Driver CPC + initial FORS e-learning (Smart Driving etc.)",
    "D5_drivers_handbook": "Issued driver handbook (signed receipt log)",
    "O1_routing_and_scheduling": "Route-planning evidence (avoid restricted areas)",
    "O2_working_time": "Domestic + EU/GB working-time compliance records",
    "O3_collisions_incidents": "Incident log + RIDDOR procedure",
    "O4_road_traffic_collisions": "Documented post-collision investigation procedure",
    "O5_passes_compliments_complaints": "Complaints / compliments log",
    "O6_environmental_protection": "Spill-kit policy + waste-disposal records",
    "O7_subcontractors": "Subcontractor due-diligence + flow-down register",
}

# FORS Silver — Bronze + 12 additional. Silver is the typical Tier-1
# construction-contractor requirement (e.g. Mace, Skanska, Balfour Beatty
# CLPs commonly cite Silver as the floor for site access).
FORS_SILVER_ADDITIONAL = {
    "S1_kpi_tracking": "Quarterly KPI tracking: MPG, idling, collisions, infringements, PCNs",
    "S2_vulnerable_road_user_training": "VRU classroom + e-learning for all drivers (refresher 5y)",
    "S3_driving_for_work_risk_assessment": "DfW risk assessment per HSE INDG403",
    "S4_fuel_and_emissions_strategy": "Documented fuel + emissions reduction strategy",
    "S5_anti_idling": "Driver anti-idling policy + telematics evidence",
    "S6_lcv_camera_systems": "Camera systems on N3 / N2 vehicles in urban use",
    "S7_blind_spot_minimisation": "Class V/VI mirrors + close-proximity cameras / sensors",
    "S8_safe_urban_driving": "FORS Safe Urban Driving (SUD) practical course completed by all relevant drivers",
    "S9_vrm_check_telematics": "VRM-linked telematics + posted-speed compliance reporting",
    "S10_noise_pollution": "Out-of-hours / quiet-delivery procedure",
    "S11_driver_communication": "Documented two-way driver communication channel",
    "S12_load_securing_competence": "EUMOS 40509 / NPORS / equivalent for load-securing personnel",
}

# FORS Gold — Silver + 8 additional. Gold requires PEER BENCHMARKING and a
# 12-month KPI history showing year-on-year improvement.
FORS_GOLD_ADDITIONAL = {
    "G1_kpi_12_month_history": "12 consecutive months of KPI data submitted",
    "G2_peer_benchmark_percentile": "Performance >= 75th percentile vs FORS peer group",
    "G3_accident_reduction": "Documented reduction in collisions / PCNs vs prior 12mo",
    "G4_in_cab_cameras": "In-cab driver-facing + forward-facing cameras",
    "G5_recognised_perf_mgmt": "ISO 39001 or equivalent recognised perf-mgmt framework",
    "G6_environmental_reporting": "Carbon reporting (Scope 1 vehicle emissions, kgCO2e/km)",
    "G7_case_study_published": "Published case study or best-practice contribution to FORS community",
    "G8_continuous_improvement": "Documented continuous-improvement plan signed by director",
}

# CLOCS Standard v3.0 — 6 sections, ~40 line items. Most overlap with FORS
# Silver. CLOCS is the standard CONSTRUCTION CLIENTS require.
CLOCS_REQUIREMENTS = {
    "C1_management_commitment": "Director-level signoff on CLOCS commitment",
    "C2_named_clocs_champion": "Named CLOCS Champion within the organisation",
    "C3_driver_training_vru": "Driver VRU + Safe Urban Driving training (refresher 5y)",
    "C4_dvs_pss_3_star": "DVS PSS 3-star+ rating (London Direct Vision Standard, mandatory 28 Oct 2024)",
    "C5_side_guards_camera": "Side-guards + close-proximity camera systems on N3 vehicles",
    "C6_audible_reverse": "Audible reverse alarm + warning signage",
    "C7_left_turn_warning": "Left-turn audible warning device",
    "C8_class_vi_mirror": "Class VI front-down mirror or equivalent sensor system",
    "C9_site_access_protocol": "Documented construction-site access + booking protocol",
    "C10_subcontractor_flowdown": "CLOCS flow-down to all subcontractors carrying for the project",
    "C11_incident_reporting": "CLOCS incident reporting + RIDDOR + project-team notification within 24h",
    "C12_continuous_improvement": "Annual CLOCS performance review with project team",
}

# DVSA Earned Recognition — admission criteria + 4-weekly KPI data feed
# requirements. ER is the regulator's "trusted operator" scheme — lower
# roadside checks, fewer audits, public listing.
DVSA_ER_KPIS = {
    "K1_drivers_hours_infringements": "Per-driver tacho infringements (4-weekly)",
    "K2_working_time_directive": "WTD compliance (4-weekly)",
    "K3_missing_mileage": "Missing-mileage % per driver (4-weekly)",
    "K4_vehicle_first_use_check": "Daily walk-around check completion %",
    "K5_driver_defect_reports": "Driver defect-reporting rate",
    "K6_safety_inspections_on_time": "Safety inspections on-time % (10 weekly typical)",
    "K7_pmi_completion": "PMI (Preventative Maintenance Inspection) completion vs schedule",
    "K8_mot_first_time_pass": "MOT first-time pass rate (annual rolling)",
    "K9_prohibitions": "DVSA prohibitions (any) — must be zero PG9s for admission",
}

# DVSA-accredited IT suppliers for ER data feed (as published by DVSA;
# operators must use one of these to be considered for ER admission).
DVSA_ER_ACCREDITED_IT_SUPPLIERS = {
    "tachomaster": "TruTac TachoMaster",
    "tachosense": "AAA TachoSense",
    "isotrak": "Isotrak Active Vehicle Management",
    "fleetcheck": "FleetCheck",
    "freight_management": "Freight Management Compliance",
    "transport_thinking": "Transport Thinking Compliance Dashboard",
    "vis_tac": "VisTac",
    "stoneridge": "Stoneridge OPTAC3",
    "veriforce": "Veriforce CHAS / equivalent",
}

# Standard codes used by FORS auditors during sample evidence checks
FORS_STANDARD_CODES = (
    "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8",
    "S9", "S10", "S11", "S12", "S13", "S14", "S15",
)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _sign(payload: dict) -> str:
    """HMAC-sign the response for tamper-evident audit."""
    if not _HMAC_SECRET:
        return "unsigned-no-key-configured"
    return hmac.new(
        _HMAC_SECRET.encode(),
        json.dumps(payload, sort_keys=True, default=str).encode(),
        hashlib.sha256,
    ).hexdigest()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _attestation(payload: dict) -> dict:
    return {
        **payload,
        "ts": _ts(),
        "sig": _sign(payload),
        "issuer": "meok-fors-clocs-mcp",
        "version": "1.0.0",
        "disclaimer": (
            "Readiness gap analysis only — does not replace the formal FORS / CLOCS "
            "/ DVSA-ER audit. Engage a FORS-approved auditor for accreditation."
        ),
    }


def _evaluate_requirements(operator_data: dict, requirements: dict) -> tuple[list, list, float]:
    """Return (present, missing, pct) for a requirement set against operator_data.

    operator_data values are interpreted as truthy/falsy. A requirement is
    considered MET if the key is present and its value is truthy.
    """
    present, missing = [], []
    for req_key, req_label in requirements.items():
        if operator_data.get(req_key):
            present.append({"code": req_key, "label": req_label})
        else:
            missing.append({"code": req_key, "label": req_label})
    total = len(requirements)
    pct = round((len(present) / total) * 100, 1) if total else 0.0
    return present, missing, pct


def _weeks_to_ready(missing_count: int) -> int:
    """Heuristic: ~1 week effort per 2 missing items, min 1, capped at 26."""
    if missing_count == 0:
        return 0
    return max(1, min(26, (missing_count + 1) // 2))


# ──────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────


def _server_meter_check(api_key: str = "") -> dict:
    """Calls the live /verify endpoint for server-side metering. Fail-open."""
    try:
        data = json.dumps({"api_key": api_key, "tool": ""}).encode()
        req = _meter_urlreq.Request(_METER_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with _meter_urlreq.urlopen(req, timeout=2.5) as r:
            d = json.loads(r.read())
            if isinstance(d, dict) and "allowed" in d:
                return d
    except Exception:
        pass
    return {"allowed": True, "tier": "anonymous", "remaining": 200, "upgrade_url": "https://meok.ai/pricing"}


_METER_URL = "https://proofof.ai/verify"


@mcp.tool()
def check_fors_bronze_readiness(operator_data: Optional[dict] = None) -> dict:
    """Score an operator against FORS Bronze (v6.1) requirements.

    Args:
      operator_data: dict where each FORS Bronze requirement code maps to a
        truthy/falsy value indicating whether the evidence is in place.

        Example keys: 'M1_management_responsibility', 'V1_serviceability',
        'D1_licensing', 'O1_routing_and_scheduling'.

    Returns readiness pct, missing items, estimated weeks to ready.
    """
    operator_data = operator_data or {}
    present, missing, pct = _evaluate_requirements(operator_data, FORS_BRONZE_REQUIREMENTS)
    weeks = _weeks_to_ready(len(missing))

    payload = {
        "tool": "check_fors_bronze_readiness",
        "level": "Bronze",
        "readiness_pct": pct,
        "requirements_total": len(FORS_BRONZE_REQUIREMENTS),
        "requirements_met": len(present),
        "missing_items": missing,
        "estimated_weeks_to_ready": weeks,
        "advisory": (
            "Bronze-ready — book audit." if pct >= 95
            else f"Close {len(missing)} gaps before booking audit."
        ),
        "reference": "FORS Standard v6.1 — Bronze",
    }
    return _attestation(payload)


@mcp.tool()
def check_fors_silver_readiness(operator_data: Optional[dict] = None) -> dict:
    """Score an operator against FORS Silver (v6.1) requirements.

    Silver = Bronze + 12 additional Silver-specific requirements.

    Args:
      operator_data: dict of requirement codes -> truthy/falsy. Combines
        Bronze codes (M1..O7) and Silver codes (S1..S12).
    """
    operator_data = operator_data or {}
    combined = {**FORS_BRONZE_REQUIREMENTS, **FORS_SILVER_ADDITIONAL}
    present, missing, pct = _evaluate_requirements(operator_data, combined)

    # Bronze must be effectively complete before Silver is considered
    _, bronze_missing, bronze_pct = _evaluate_requirements(
        operator_data, FORS_BRONZE_REQUIREMENTS
    )
    silver_only_missing = [m for m in missing if m["code"] in FORS_SILVER_ADDITIONAL]
    weeks = _weeks_to_ready(len(missing))

    payload = {
        "tool": "check_fors_silver_readiness",
        "level": "Silver",
        "readiness_pct": pct,
        "bronze_floor_pct": bronze_pct,
        "bronze_floor_complete": bronze_pct >= 95,
        "requirements_total": len(combined),
        "requirements_met": len(present),
        "silver_specific_gaps": silver_only_missing,
        "all_missing_items": missing,
        "estimated_weeks_to_ready": weeks,
        "advisory": (
            "Silver-ready." if pct >= 95
            else "Achieve Bronze first." if bronze_pct < 95
            else f"Close {len(silver_only_missing)} Silver-specific gaps."
        ),
        "reference": "FORS Standard v6.1 — Silver",
    }
    return _attestation(payload)


@mcp.tool()
def check_fors_gold_readiness(operator_data: Optional[dict] = None) -> dict:
    """Score an operator against FORS Gold (v6.1) requirements.

    Gold = Silver + 8 additional Gold-specific requirements including a
    12-month KPI history and >=75th-percentile peer benchmarking.

    Args:
      operator_data: dict combining Bronze (M1..O7), Silver (S1..S12) and
        Gold (G1..G8) requirement codes -> truthy/falsy values.
    """
    operator_data = operator_data or {}
    combined = {
        **FORS_BRONZE_REQUIREMENTS,
        **FORS_SILVER_ADDITIONAL,
        **FORS_GOLD_ADDITIONAL,
    }
    present, missing, pct = _evaluate_requirements(operator_data, combined)

    _, _, silver_pct = _evaluate_requirements(
        operator_data, {**FORS_BRONZE_REQUIREMENTS, **FORS_SILVER_ADDITIONAL}
    )
    gold_only_missing = [m for m in missing if m["code"] in FORS_GOLD_ADDITIONAL]

    # Hard gate: G1 (12-month KPI history) and G2 (75th-percentile benchmark)
    blocking_gates = []
    if not operator_data.get("G1_kpi_12_month_history"):
        blocking_gates.append("G1_kpi_12_month_history — 12mo KPI history is a hard prerequisite")
    if not operator_data.get("G2_peer_benchmark_percentile"):
        blocking_gates.append("G2_peer_benchmark_percentile — >=75th percentile peer benchmark required")

    weeks = _weeks_to_ready(len(missing))

    payload = {
        "tool": "check_fors_gold_readiness",
        "level": "Gold",
        "readiness_pct": pct,
        "silver_floor_pct": silver_pct,
        "silver_floor_complete": silver_pct >= 95,
        "requirements_total": len(combined),
        "requirements_met": len(present),
        "gold_specific_gaps": gold_only_missing,
        "blocking_gates": blocking_gates,
        "all_missing_items": missing,
        "estimated_weeks_to_ready": weeks,
        "advisory": (
            "Gold-ready." if pct >= 95 and not blocking_gates
            else "Achieve Silver first." if silver_pct < 95
            else "Blocked by hard gates." if blocking_gates
            else f"Close {len(gold_only_missing)} Gold-specific gaps."
        ),
        "reference": "FORS Standard v6.1 — Gold + ISO 39001 alignment",
    }
    return _attestation(payload)


@mcp.tool()
def prepare_fors_audit_pack(
    operator_data: Optional[dict] = None,
    target_level: str = "bronze",
) -> dict:
    """Generate a complete evidence checklist tied to FORS standard codes
    S1-S15 for the requested audit level.

    Args:
      operator_data: dict of requirement codes -> truthy/falsy (used to mark
        which evidence items are already in place vs outstanding)
      target_level: 'bronze' / 'silver' / 'gold'
    """
    operator_data = operator_data or {}
    level = target_level.lower().strip()
    if level not in ("bronze", "silver", "gold"):
        return _attestation({
            "tool": "prepare_fors_audit_pack",
            "error": f"Unknown target_level '{target_level}'. Use bronze / silver / gold.",
        })

    if level == "bronze":
        reqs = dict(FORS_BRONZE_REQUIREMENTS)
    elif level == "silver":
        reqs = {**FORS_BRONZE_REQUIREMENTS, **FORS_SILVER_ADDITIONAL}
    else:
        reqs = {
            **FORS_BRONZE_REQUIREMENTS,
            **FORS_SILVER_ADDITIONAL,
            **FORS_GOLD_ADDITIONAL,
        }

    # Map requirements onto the auditor's sample-check standard codes S1..S15.
    # FORS auditors group the requirements into sampling buckets at the
    # desktop + on-site stage. This is a representative mapping — we
    # round-robin items across S1..S15 so every requirement lands in
    # exactly one bucket regardless of the total count.
    items = list(reqs.items())
    sample_buckets = {code: [] for code in FORS_STANDARD_CODES}
    for idx, (k, v) in enumerate(items):
        code = FORS_STANDARD_CODES[idx % len(FORS_STANDARD_CODES)]
        sample_buckets[code].append({
            "requirement": k,
            "evidence": v,
            "status": "PRESENT" if operator_data.get(k) else "OUTSTANDING",
        })

    outstanding = [
        item for bucket in sample_buckets.values()
        for item in bucket if item["status"] == "OUTSTANDING"
    ]

    payload = {
        "tool": "prepare_fors_audit_pack",
        "target_level": level.title(),
        "total_evidence_items": len(reqs),
        "outstanding_items": len(outstanding),
        "ready_pct": round(((len(reqs) - len(outstanding)) / len(reqs)) * 100, 1),
        "standard_code_buckets": sample_buckets,
        "auditor_sample_codes": list(FORS_STANDARD_CODES),
        "next_steps": [
            f"Collect outstanding evidence for {len(outstanding)} items",
            "Upload to FORS Compliance portal",
            "Book desktop audit (Bronze) or on-site audit (Silver/Gold)",
            "Allow 2-4 weeks between audit booking and visit",
        ],
        "reference": "FORS Standard v6.1 sampling protocol",
    }
    return _attestation(payload)


@mcp.tool()
def check_clocs_compliance(
    operator_data: Optional[dict] = None,
    project_type: str = "tfl_construction",
) -> dict:
    """Score an operator against CLOCS Standard v3.0 for a named project type.

    Args:
      operator_data: dict of CLOCS requirement codes (C1..C12) -> truthy/falsy
      project_type: 'tfl_construction' / 'hs2' / 'gla_major_project' /
        'tier1_contractor' / 'private_developer'
    """
    operator_data = operator_data or {}
    present, missing, pct = _evaluate_requirements(operator_data, CLOCS_REQUIREMENTS)

    # DVS PSS 3-star is a hard gate for any London / GLA project
    london_gate_blocked = False
    if project_type.lower() in ("tfl_construction", "gla_major_project"):
        if not operator_data.get("C4_dvs_pss_3_star"):
            london_gate_blocked = True

    weeks = _weeks_to_ready(len(missing))

    payload = {
        "tool": "check_clocs_compliance",
        "project_type": project_type,
        "compliance_pct": pct,
        "requirements_total": len(CLOCS_REQUIREMENTS),
        "requirements_met": len(present),
        "missing_items": missing,
        "london_dvs_pss_gate_blocked": london_gate_blocked,
        "estimated_weeks_to_ready": weeks,
        "advisory": (
            "BLOCKED: DVS PSS 3-star+ rating mandatory for London (28 Oct 2024)."
            if london_gate_blocked
            else "CLOCS-compliant." if pct >= 95
            else f"Close {len(missing)} CLOCS gaps before site mobilisation."
        ),
        "reference": "CLOCS Standard v3.0 + TfL Construction Logistics Plan + DVS PSS",
    }
    return _attestation(payload)


@mcp.tool()
def audit_dvsa_earned_recognition_data_feed(
    operator_data: Optional[dict] = None,
) -> dict:
    """Audit an operator's readiness for DVSA Earned Recognition (ER) data feed.

    ER requires a 4-weekly KPI data feed on tachograph + maintenance via a
    DVSA-accredited IT supplier, plus zero PG9 prohibitions in the assessment
    period.

    Args:
      operator_data: dict including:
        - 'it_supplier' (str): name of IT supplier (must be DVSA-accredited)
        - 'kpi_<K1..K9>' (bool): whether each KPI is fed automatically
        - 'pg9_prohibitions_last_12mo' (int): count of PG9 prohibitions
        - 'audit_history_12mo_clean' (bool)
    """
    operator_data = operator_data or {}
    supplier_key = (operator_data.get("it_supplier") or "").lower().strip()
    supplier_accredited = supplier_key in DVSA_ER_ACCREDITED_IT_SUPPLIERS

    kpi_status = {}
    kpi_missing = []
    for kpi_code, kpi_label in DVSA_ER_KPIS.items():
        key = f"kpi_{kpi_code}".lower()
        is_fed = bool(operator_data.get(key) or operator_data.get(kpi_code))
        kpi_status[kpi_code] = {"label": kpi_label, "fed": is_fed}
        if not is_fed:
            kpi_missing.append(kpi_code)

    pg9_count = int(operator_data.get("pg9_prohibitions_last_12mo", 0) or 0)
    audit_clean = bool(operator_data.get("audit_history_12mo_clean", False))

    blocking_issues = []
    if not supplier_accredited:
        blocking_issues.append(
            f"IT supplier '{operator_data.get('it_supplier','(none)')}' is not "
            "DVSA-accredited — admission blocked."
        )
    if pg9_count > 0:
        blocking_issues.append(
            f"{pg9_count} PG9 prohibition(s) in last 12 months — must be zero."
        )
    if kpi_missing:
        blocking_issues.append(
            f"{len(kpi_missing)} of {len(DVSA_ER_KPIS)} required KPIs are not fed."
        )
    if not audit_clean:
        blocking_issues.append("12-month audit history not clean.")

    payload = {
        "tool": "audit_dvsa_earned_recognition_data_feed",
        "it_supplier": operator_data.get("it_supplier"),
        "it_supplier_accredited": supplier_accredited,
        "accredited_supplier_options": list(DVSA_ER_ACCREDITED_IT_SUPPLIERS.values()),
        "kpi_status": kpi_status,
        "kpis_fed": len(DVSA_ER_KPIS) - len(kpi_missing),
        "kpis_total": len(DVSA_ER_KPIS),
        "kpis_missing": kpi_missing,
        "pg9_prohibitions_last_12mo": pg9_count,
        "audit_history_12mo_clean": audit_clean,
        "er_admission_ready": not blocking_issues,
        "blocking_issues": blocking_issues,
        "advisory": (
            "ER-admission-ready — apply via DVSA portal." if not blocking_issues
            else "ER application would be rejected — close blocking issues first."
        ),
        "reference": "DVSA Earned Recognition data-feed specification (2026)",
    }
    return _attestation(payload)


@mcp.tool()
def forecast_fors_renewal(
    current_level: str,
    last_audit_date: str,
) -> dict:
    """Forecast the FORS audit renewal window for an operator.

    FORS Bronze, Silver, and Gold are each valid for 12 months. The renewal
    window opens 60 days before expiry. Missing the renewal window means
    re-application as a NEW operator (a full Bronze audit before any
    Silver / Gold re-application).

    Args:
      current_level: 'bronze' / 'silver' / 'gold'
      last_audit_date: ISO date YYYY-MM-DD of last successful audit

    Returns next_audit_due, weeks_remaining, status.
    """
    level = current_level.lower().strip()
    if level not in ("bronze", "silver", "gold"):
        return _attestation({
            "tool": "forecast_fors_renewal",
            "error": f"Unknown level '{current_level}'.",
        })

    try:
        last = date.fromisoformat(last_audit_date)
    except Exception:
        return _attestation({
            "tool": "forecast_fors_renewal",
            "error": "last_audit_date must be ISO YYYY-MM-DD.",
        })

    next_due = last + timedelta(days=365)
    window_opens = next_due - timedelta(days=60)
    today = date.today()
    days_remaining = (next_due - today).days
    weeks_remaining = days_remaining // 7

    if today < window_opens:
        status = "NOT_YET_DUE"
    elif window_opens <= today <= next_due:
        status = "RENEWAL_WINDOW_OPEN"
    elif 0 > days_remaining >= -30:
        status = "OVERDUE_GRACE"
    elif days_remaining < -30:
        status = "LAPSED_REAPPLY_AS_NEW"
    else:
        status = "EXPIRES_TODAY"

    payload = {
        "tool": "forecast_fors_renewal",
        "current_level": level.title(),
        "last_audit_date": last.isoformat(),
        "next_audit_due": next_due.isoformat(),
        "renewal_window_opens": window_opens.isoformat(),
        "days_remaining": days_remaining,
        "weeks_remaining": weeks_remaining,
        "status": status,
        "advisory": {
            "NOT_YET_DUE": f"On track — renewal window opens {window_opens.isoformat()}.",
            "RENEWAL_WINDOW_OPEN": "Book renewal audit NOW — 4-6 week lead time typical.",
            "OVERDUE_GRACE": "OVERDUE — apply within 30 days or lose accreditation.",
            "LAPSED_REAPPLY_AS_NEW": "LAPSED — must re-apply as a new operator (Bronze first).",
            "EXPIRES_TODAY": "Expires today — emergency renewal call required.",
        }.get(status, ""),
        "reference": "FORS accreditation lifecycle (v6.1)",
    }
    return _attestation(payload)


@mcp.tool()
def crosswalk_fors_to_clocs(fors_level: str) -> dict:
    """Show which FORS evidence items satisfy which CLOCS requirements.

    Roughly 80%+ of CLOCS evidence is reusable from FORS Silver. This tool
    saves duplicated audit prep work by mapping FORS evidence onto CLOCS
    requirements.

    Args:
      fors_level: 'bronze' / 'silver' / 'gold'
    """
    level = fors_level.lower().strip()
    if level not in ("bronze", "silver", "gold"):
        return _attestation({
            "tool": "crosswalk_fors_to_clocs",
            "error": f"Unknown fors_level '{fors_level}'.",
        })

    # Hand-curated mapping: which FORS requirement satisfies which CLOCS req.
    full_map = {
        "C1_management_commitment": ["M1_management_responsibility", "M3_responsibilities"],
        "C2_named_clocs_champion": ["M3_responsibilities"],  # partial — needs CLOCS-specific naming
        "C3_driver_training_vru": ["S2_vulnerable_road_user_training", "S8_safe_urban_driving"],
        "C4_dvs_pss_3_star": [],  # CLOCS-specific — no FORS equivalent
        "C5_side_guards_camera": ["V2_safety_equipment", "S6_lcv_camera_systems", "S7_blind_spot_minimisation"],
        "C6_audible_reverse": ["V2_safety_equipment"],
        "C7_left_turn_warning": ["S7_blind_spot_minimisation"],
        "C8_class_vi_mirror": ["V2_safety_equipment", "S7_blind_spot_minimisation"],
        "C9_site_access_protocol": ["O1_routing_and_scheduling", "S10_noise_pollution"],
        "C10_subcontractor_flowdown": ["O7_subcontractors"],
        "C11_incident_reporting": ["O3_collisions_incidents", "O4_road_traffic_collisions"],
        "C12_continuous_improvement": ["G8_continuous_improvement"],  # Gold-only
    }

    if level == "bronze":
        available = set(FORS_BRONZE_REQUIREMENTS.keys())
    elif level == "silver":
        available = set(FORS_BRONZE_REQUIREMENTS.keys()) | set(FORS_SILVER_ADDITIONAL.keys())
    else:
        available = (
            set(FORS_BRONZE_REQUIREMENTS.keys())
            | set(FORS_SILVER_ADDITIONAL.keys())
            | set(FORS_GOLD_ADDITIONAL.keys())
        )

    coverage = {}
    satisfied = 0
    for clocs_code, fors_codes in full_map.items():
        usable = [c for c in fors_codes if c in available]
        is_satisfied = bool(usable)
        coverage[clocs_code] = {
            "label": CLOCS_REQUIREMENTS[clocs_code],
            "fors_evidence_codes": usable,
            "satisfied_by_fors": is_satisfied,
        }
        if is_satisfied:
            satisfied += 1

    pct = round((satisfied / len(CLOCS_REQUIREMENTS)) * 100, 1)

    payload = {
        "tool": "crosswalk_fors_to_clocs",
        "fors_level": level.title(),
        "clocs_requirements_total": len(CLOCS_REQUIREMENTS),
        "clocs_satisfied_by_fors": satisfied,
        "clocs_coverage_pct": pct,
        "coverage_detail": coverage,
        "clocs_specific_gaps": [
            c for c, v in coverage.items() if not v["satisfied_by_fors"]
        ],
        "advisory": (
            f"FORS {level.title()} covers {pct}% of CLOCS — close DVS PSS + "
            "CLOCS Champion gaps separately."
        ),
        "reference": "CLOCS v3.0 mapped against FORS Standard v6.1",
    }
    return _attestation(payload)


@mcp.tool()
def generate_corrective_action_plan(
    audit_gaps: Optional[list] = None,
) -> dict:
    """Turn a list of audit gaps into a prioritised Corrective Action Plan (CAP).

    A CAP is a standard FORS / CLOCS / DVSA artefact. Each gap is given an
    owner role, due date, evidence required, and priority based on whether
    it is a hard regulatory gate, a tender-blocking item, or a quality gap.

    Args:
      audit_gaps: list of strings (gap descriptions) or dicts with keys
        {code, label, severity}. Severity: 'critical' / 'high' / 'medium' /
        'low'. Defaults to 'medium' if not provided.
    """
    audit_gaps = audit_gaps or []
    today = date.today()

    # Map gap codes / keywords to suggested owner + due-date offset
    owner_rules = [
        ("M", "Transport Manager", 14),
        ("V", "Workshop Supervisor", 21),
        ("D", "Driver Training Manager", 30),
        ("O", "Operations Manager", 21),
        ("S", "Compliance Lead", 28),
        ("G", "Director / Board Sponsor", 60),
        ("C", "CLOCS Champion", 21),
        ("K", "Data / IT Manager", 28),
    ]

    sev_due_offset = {"critical": 7, "high": 14, "medium": 28, "low": 60}
    sev_priority_order = {"critical": 1, "high": 2, "medium": 3, "low": 4}

    cap_items = []
    for gap in audit_gaps:
        if isinstance(gap, str):
            code, label, severity = "", gap, "medium"
        elif isinstance(gap, dict):
            code = gap.get("code", "")
            label = gap.get("label", code or "(unnamed gap)")
            severity = str(gap.get("severity", "medium")).lower()
            if severity not in sev_due_offset:
                severity = "medium"
        else:
            continue

        # Owner
        owner = "Compliance Lead"
        owner_default_days = 28
        for prefix, role, days in owner_rules:
            if code.startswith(prefix):
                owner = role
                owner_default_days = days
                break

        days_to_due = min(sev_due_offset[severity], owner_default_days)
        due = today + timedelta(days=days_to_due)

        cap_items.append({
            "code": code,
            "gap": label,
            "severity": severity,
            "priority": sev_priority_order[severity],
            "owner": owner,
            "due_date": due.isoformat(),
            "evidence_required": _evidence_for(code, label),
        })

    # Sort by priority ascending, then due date
    cap_items.sort(key=lambda x: (x["priority"], x["due_date"]))

    payload = {
        "tool": "generate_corrective_action_plan",
        "generated_at": today.isoformat(),
        "total_gaps": len(cap_items),
        "critical_count": sum(1 for c in cap_items if c["severity"] == "critical"),
        "high_count": sum(1 for c in cap_items if c["severity"] == "high"),
        "cap_items": cap_items,
        "next_review_date": (today + timedelta(days=14)).isoformat(),
        "advisory": (
            "Walk this CAP at a weekly compliance stand-up until all critical + "
            "high items are CLOSED with evidence uploaded."
        ),
        "reference": "FORS / CLOCS / DVSA-ER Corrective Action Plan format",
    }
    return _attestation(payload)


def _evidence_for(code: str, label: str) -> list:
    """Suggest evidence artefacts for a CAP item based on its code/label."""
    label_l = (label or "").lower()
    suggestions = []
    if any(k in label_l for k in ("policy", "handbook", "statement")):
        suggestions.append("Signed + dated policy document (PDF)")
    if any(k in label_l for k in ("training", "cpc", "induction", "e-learning")):
        suggestions.append("Training records / certificates")
        suggestions.append("Attendance log + signed register")
    if any(k in label_l for k in ("kpi", "telematics", "monitoring", "tracking")):
        suggestions.append("4-weekly KPI export (CSV / dashboard screenshot)")
    if any(k in label_l for k in ("check", "inspection", "walk-around", "pmi")):
        suggestions.append("Defect / inspection report sample (≥10 entries)")
    if any(k in label_l for k in ("camera", "mirror", "sensor", "guard", "dvs")):
        suggestions.append("Photo evidence + invoice / installation cert")
    if code.startswith("G"):
        suggestions.append("Director-signed annual review document")
    if not suggestions:
        suggestions.append("Documented procedure + evidence of recent use")
    return suggestions


# ──────────────────────────────────────────────────────────────────────
# Server entry
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/5kQ6oJ0xS3ce8sl7ew8k91j"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
