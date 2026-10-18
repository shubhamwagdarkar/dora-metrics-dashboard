# User Journeys — dora-metrics-dashboard

---

## Journey 1: Engineering Manager — First Weekly Health Check

**Actor:** Engineering Manager, 8-person platform team
**Goal:** Establish a weekly DORA baseline before a roadmap review

**Steps:**
1. `pip install -r requirements.txt` — install in a virtualenv
2. `cp .env.example .env` — copy template
3. Fill in `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO` in `.env`
4. (Optional) Add `PAGERDUTY_API_KEY` for MTTR
5. `python main.py demo` — sanity-check the output format
6. `python main.py report --team platform-team --days 30` — live report
7. Review the colour-coded table: team is **High** overall, dragged down by MTTR
8. Screenshot the terminal output for the weekly eng sync

**Outcome:** Manager has a quantified view of delivery health in < 10 minutes, no commercial tooling required.

---

## Journey 2: TPM — Quarterly Business Review Preparation

**Actor:** Staff TPM preparing a QBR deck for engineering leadership
**Goal:** Produce a Markdown-formatted DORA report for the last 90 days to embed in Confluence

**Steps:**
1. Run report for 90-day window and export to Markdown:
   ```bash
   python main.py report \
     --team platform-team \
     --days 90 \
     --format markdown \
     --output q3-dora-report.md
   ```
2. Open `q3-dora-report.md` — confirm all four metrics and bands are present
3. Paste the Markdown table into Confluence
4. Add commentary: "Lead time improved from High → Elite this quarter; MTTR still Medium, action item for Q4"
5. Share with VPE before the QBR

**Outcome:** TPM has a data-driven, standardised DORA summary ready in 2 minutes, formatted for the audience.

---

## Journey 3: Platform Engineer — CI Gate Integration

**Actor:** Platform engineer building a deployment quality gate
**Goal:** Fail the CI pipeline if Change Failure Rate exceeds 15% in the last 7 days

**Steps:**
1. Add a step to the GitHub Actions workflow:
   ```yaml
   - name: DORA gate
     run: |
       python main.py report --days 7 --format json --output dora.json
       python - <<'EOF'
       import json, sys
       r = json.load(open("dora.json"))
       cfr = r["change_failure_rate"]["failure_rate_pct"]
       band = r["change_failure_rate"]["band"]
       print(f"CFR: {cfr}% ({band})")
       if band == "Low":
           print("GATE FAILED: CFR is Low — block deployment")
           sys.exit(1)
       EOF
   ```
2. Commit the workflow
3. On next deploy, CFR is 8% (High) → gate passes
4. After a bad week with 18% CFR → gate blocks deployment, Slack alert fires

**Outcome:** DORA metrics are enforced as a quality gate, not just a reporting exercise.

---

## Journey 4: SRE — Post-Incident MTTR Audit

**Actor:** On-call SRE reviewing recovery performance after a P1 incident week
**Goal:** Understand whether MTTR is trending toward Elite or worsening

**Steps:**
1. Run MTTR-focused report for the last 14 days:
   ```bash
   python main.py report --days 14 --format json | python -c "
   import json, sys
   r = json.load(sys.stdin)
   mttr = r['mttr']
   print(f\"Incidents: {mttr['total_incidents']}\")
   print(f\"Avg MTTR: {mttr['avg_mttr_hours']:.1f}h ({mttr['band']})\")
   "
   ```
2. Output shows: `Avg MTTR: 3.2h (High)` — improved from last week's 6.8h (Medium)
3. SRE notes this in the incident postmortem: "MTTR improved due to new runbook added to Resolve"
4. Adds MTTR tracking to weekly SRE review agenda

**Outcome:** SRE has a quantified MTTR trend without needing PagerDuty premium analytics.
