<!-- mcp-name: io.github.CSOAI-ORG/meok-fors-clocs-mcp -->
[![MCP Scorecard: 84/100](https://img.shields.io/badge/proofof.ai-84%2F100-5b21b6)](https://proofof.ai/scorecard/meok-fors-clocs-mcp.html)

# meok-fors-clocs-mcp

[![PyPI](https://img.shields.io/badge/PyPI-1.0.0-blue)](https://pypi.org/project/meok-fors-clocs-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-1.3.0+-green)](https://modelcontextprotocol.io)

> FORS Bronze/Silver/Gold + CLOCS + DVSA Earned Recognition audit-prep toolkit for UK haulage and plant hire. By **MEOK AI Labs**.

## Why this exists

For UK general haulage and plant-hire operators, three accreditation regimes are now **tender-gating** — most public-sector buyers and Tier-1 construction contractors won't engage you without them:

- **FORS** (Fleet Operator Recognition Scheme) — Bronze / Silver / Gold
- **CLOCS** (Construction Logistics And Community Safety) — for any project naming the CLOCS Standard contractually
- **DVSA Earned Recognition** (ER) — the regulator's "trusted operator" scheme, with a 4-weekly KPI data feed

Preparing for these audits today commonly costs **80+ consultancy hours at £300–£500/hr** — and re-doing 80% of the same work the next year for the next regime. This MCP collapses that into a callable readiness toolkit.

## Honesty note

This MCP **supports** auditors, transport managers, and operators preparing for the formal FORS / CLOCS / DVSA-ER audit. It does **not** replace the audit. FORS audits are conducted by FORS-approved auditors; CLOCS Champion status is awarded by the CLOCS Community; DVSA-ER admission is granted by DVSA. Treat the outputs as a readiness gap analysis.

## Install

```bash
pip install meok-fors-clocs-mcp
```

## Claude Desktop config

```json
{
  "mcpServers": {
    "fors-clocs": {
      "command": "meok-fors-clocs-mcp"
    }
  }
}
```

## Tools (9)

| Tool | Use case |
|------|----------|
| `check_fors_bronze_readiness` | Bronze gap analysis — % ready, missing items, weeks to ready. |
| `check_fors_silver_readiness` | Silver = Bronze + 12 additional Silver requirements. |
| `check_fors_gold_readiness` | Gold = Silver + 8 (incl. 12-month KPI history + 75th-percentile benchmark). |
| `prepare_fors_audit_pack` | Build the S1-S15 evidence checklist for the target level. |
| `check_clocs_compliance` | CLOCS v3.0 score per project type — flags London DVS PSS gate. |
| `audit_dvsa_earned_recognition_data_feed` | ER readiness, KPI feed audit, accredited IT supplier check. |
| `forecast_fors_renewal` | Renewal window opens 60 days before expiry — don't lapse. |
| `crosswalk_fors_to_clocs` | Reuse FORS evidence for ~80% of CLOCS — don't double-prep. |
| `generate_corrective_action_plan` | Prioritised CAP with owners + due dates + evidence required. |

## Pricing

- **Free** — MIT self-host
- **Starter** — £49/mo (signed attestations + email support)
- **Pro** — £149/mo (multi-user, audit-export, FORS-CLOCS crosswalk)
- **Fleet** — £499/mo (50+ vehicles, white-label for consultancies)
- **ER tier** — £1,499/mo (DVSA Earned Recognition data-feed assist + monthly review)

[Subscribe Pro → £149/mo](https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t) · [Talk to Nick](mailto:nicholas@meok.ai)

## Regulatory basis

- FORS Standard v6.1 (in force 2026)
- CLOCS Standard v3.0
- TfL Construction Logistics Plan guidance
- DVSA Earned Recognition data-feed specification
- DVS PSS (Direct Vision Standard — Progressive Safe System), 3-star+ mandatory in London from 28 October 2024
- HSE INDG403 (Driving at Work)
- ISO 39001 (Road Traffic Safety Management) — referenced by FORS Gold

## Sign your responses (production)

```bash
export MEOK_HMAC_SECRET="your-secret"
meok-fors-clocs-mcp
```

Every tool response returns an HMAC-SHA256 signature for tamper-evident audit trail.

## Companion MCPs

Part of the **MEOK Haulage** stack on haulage.app:

- `meok-car-transport-uk-mcp` — DVSA + tacho + C&U
- `meok-vehicle-handover-mcp` — NAMA + BVRLA + POD
- `meok-ev-recall-transport-mcp` — ADR Class 9 / EV recalls
- `meok-fors-clocs-mcp` — this one
- (4 more flagships in the pipeline)

## License

MIT © 2026 Nicholas Templeman / MEOK AI Labs · [haulage.app](https://haulage.app)
