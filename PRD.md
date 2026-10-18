# PRD — DORA Metrics Dashboard

**Author:** Shubham Wagdarkar
**Status:** Shipped (Week 25)
**Last Updated:** 2026-10-18

---

## Problem Statement

Engineering teams at AIOps and enterprise software companies lack a consistent, data-driven view of their delivery performance. DORA metrics are industry-standard but are either locked inside expensive commercial tools (LinearB, Sleuth, Cortex) or require manual data collection in spreadsheets. Teams can't improve what they can't measure — and without a common baseline, TPMs and engineering managers can't have grounded conversations about delivery health.

**Why now:** DORA 2023 updated performance thresholds. Most open-source tools still use 2021 thresholds.

---

## Target Users

| User | Goal | Pain today |
|------|------|-----------|
| Engineering Manager | Understand team delivery health week-over-week | No single view across GitHub + PagerDuty |
| TPM / Staff PM | Ground roadmap conversations in delivery data | Manual spreadsheet tracking |
| On-call SRE | Understand MTTR trends after incident | PagerDuty analytics require premium tier |
| Platform team lead | Benchmark CI/CD maturity for exec reporting | DORA tools are expensive or require agents |

---

## Goals & Success Metrics

| Goal | Metric | Target |
|------|--------|--------|
| Teams can generate a DORA report without a commercial tool | Time-to-first-report | < 5 minutes from `pip install` |
| Report is accurate for GitHub-native workflows | Lead time accuracy vs manual spot-check | Within ±10% |
| Supports both live and offline use | Demo mode requires zero credentials | Pass |
| Output is machine-consumable | JSON output parseable by CI scripts | Pass |

---

## Feature Requirements

### P0 — Must Have
- **F1:** Compute all four DORA metrics from GitHub Deployments API + PagerDuty Incidents API
- **F2:** Classify each metric into Elite / High / Medium / Low per DORA 2023 thresholds
- **F3:** Terminal report with colour-coded bands (Rich)
- **F4:** Markdown report export (`--format markdown --output report.md`)
- **F5:** JSON report export (`--format json`) for downstream tooling
- **F6:** Demo mode with built-in sample data (zero credentials)
- **F7:** Lead time computed from first PR commit → deployment (not merge → deployment)

### P1 — Should Have
- **F8:** Configurable analysis window (`--days`)
- **F9:** Configurable environment filter (`--environment staging`)
- **F10:** Graceful degradation when PagerDuty key absent (MTTR skipped, others computed)

### P2 — Nice to Have
- **F11:** Historical trend (compare last N windows) — not implemented in v1
- **F12:** Slack webhook output — not implemented in v1
- **F13:** GitHub Actions integration — not implemented in v1

---

## Non-Functional Requirements

| NFR | Requirement |
|-----|-------------|
| Performance | Report generation < 30s for 100 deployments (bounded by GitHub API rate limits) |
| Reliability | Graceful error messages for missing env vars, HTTP failures |
| Testability | All business logic testable without network calls (session injection pattern) |
| Security | No credentials in code; `.env` gitignored; `.env.example` committed |

---

## Out of Scope

- Web UI or interactive dashboard (Streamlit, Grafana)
- Historical trend tracking / time-series storage
- Non-GitHub VCS (GitLab, Bitbucket)
- Non-PagerDuty incident sources (OpsGenie, Squadcast)
- Alerting or Slack notifications

---

## Open Questions

1. **DORA threshold versioning:** DORA updates thresholds. Should the classifier be config-driven rather than hardcoded? (Deferred to v2 — adds complexity without current value.)
2. **CFR definition:** Should "failure" be defined by deployment status or by incident-to-deployment correlation (deploy → incident within 1h)? Both are valid; v1 uses deployment status.
3. **Lead time for non-PR workflows:** Direct commits to main have no PR and no lead time data. v1 skips them. A future version could use commit timestamp directly.
