# User Stories — dora-metrics-dashboard

---

## Epic: Generate DORA Metrics Report

### US-001 — Terminal Report
**As an** engineering manager,
**I want to** run a single CLI command and see my team's DORA metrics in the terminal with colour-coded performance bands,
**so that** I can quickly assess delivery health without opening any dashboards.

**Acceptance criteria:**
- [ ] Command completes with a formatted table showing all four metrics
- [ ] Each metric shows its value, performance band, and band colour (green=Elite, cyan=High, yellow=Medium, red=Low)
- [ ] Overall band (worst of the four) is shown prominently in the header
- [ ] Runs in < 30 seconds for 100 deployments

---

### US-002 — Markdown Export for Async Sharing
**As a** TPM,
**I want to** export the DORA report as a Markdown file,
**so that** I can paste it into a Confluence page or GitHub wiki without reformatting.

**Acceptance criteria:**
- [ ] `--format markdown --output report.md` writes a valid Markdown file
- [ ] File includes a table with all four metrics and their bands
- [ ] File includes team name, window, and generation timestamp

---

### US-003 — JSON Export for Tooling Integration
**As a** platform engineer,
**I want to** get DORA metrics as JSON,
**so that** I can pipe the output into a Slack bot, Grafana annotation, or CI gate script.

**Acceptance criteria:**
- [ ] `--format json` outputs valid JSON
- [ ] All metric values and bands are present as structured fields
- [ ] Output can be parsed by `jq` or any standard JSON library

---

### US-004 — Demo Without API Keys
**As a** new user evaluating the tool,
**I want to** run a demo with built-in sample data,
**so that** I can see what the report looks like before setting up API credentials.

**Acceptance criteria:**
- [ ] `python main.py demo` runs without any environment variables
- [ ] Output shows a realistic-looking DORA report
- [ ] No external API calls are made in demo mode

---

### US-005 — Live GitHub Data
**As an** engineering manager,
**I want to** pull real deployment data from my GitHub repository,
**so that** the DORA metrics reflect my actual team's delivery performance.

**Acceptance criteria:**
- [ ] Client fetches deployments filtered to the `production` environment
- [ ] Only deployments within the analysis window (`--days`) are included
- [ ] Deployment failures are identified from the latest deployment status
- [ ] Lead time is enriched from PR commit history when available

---

### US-006 — MTTR from PagerDuty
**As an** SRE,
**I want to** have MTTR calculated from real PagerDuty incident data,
**so that** the recovery time metric is accurate and not self-reported.

**Acceptance criteria:**
- [ ] Client fetches all incidents (triggered, acknowledged, resolved) in the window
- [ ] MTTR uses resolved_at - created_at for resolved incidents only
- [ ] Unresolved incidents contribute to the total count but not the average
- [ ] If `PAGERDUTY_API_KEY` is not set, a warning is shown and MTTR shows "No data"

---

### US-007 — Configurable Analysis Window
**As a** TPM running a quarterly review,
**I want to** configure the time window for the report,
**so that** I can compare DORA metrics across different periods (7-day sprint, 30-day month, 90-day quarter).

**Acceptance criteria:**
- [ ] `--days 7` limits the analysis to the last 7 days
- [ ] `--days 90` extends the window to 90 days
- [ ] All four metrics are computed within the specified window consistently
