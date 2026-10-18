# dora-metrics-dashboard

Pulls live deployment and incident data from **GitHub** and **PagerDuty**, computes the four DORA metrics, and renders a colour-coded performance report in the terminal, Markdown, or JSON.

## The Four DORA Metrics

| Metric | What it measures | Elite threshold |
|--------|-----------------|-----------------|
| **Deployment Frequency** | How often the team ships to production | >= 1/day |
| **Lead Time for Changes** | First commit → production | < 1 hour |
| **Change Failure Rate** | % of deploys that cause an incident | < 5% |
| **Mean Time to Recovery** | Time to restore service after failure | < 1 hour |

Performance bands follow the [DORA 2023 State of DevOps Report](https://dora.dev/): **Elite / High / Medium / Low**.

## Quick Start

```bash
pip install -r requirements.txt

# Demo mode — no API keys needed
python main.py demo

# Live report from GitHub + PagerDuty
cp .env.example .env  # fill in GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO
python main.py report --owner my-org --repo my-repo --days 30
```

## Commands

```
python main.py --help
python main.py report --owner <org> --repo <repo> [--team <name>] [--days 30] [--format terminal|markdown|json] [--output report.md]
python main.py demo [--days 30] [--format terminal|markdown|json]
```

## Architecture

```
GitHub API ──► GitHubClient.get_deployments()
                  └── enrich_with_pr_data()   ← adds lead time via PR commits
PagerDuty  ──► PagerDutyClient.get_incidents()

                         ↓
              MetricsCalculator
                  ├── compute_deployment_frequency()
                  ├── compute_lead_time()
                  ├── compute_change_failure_rate()
                  └── compute_mttr()
                         ↓
              DORAClassifier  ← Elite / High / Medium / Low
                         ↓
              DORAReporter    ← terminal (Rich) | Markdown | JSON
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token (`repo` scope) |
| `GITHUB_OWNER` | Yes | GitHub org or username |
| `GITHUB_REPO` | Yes | Repository name |
| `PAGERDUTY_API_KEY` | No | PagerDuty REST API key (MTTR skipped if absent) |

## Running Tests

```bash
pytest tests/ -v
# 124/124 passing
```

## Project Structure

```
dora-metrics-dashboard/
├── main.py                        # Typer CLI (report, demo commands)
├── src/
│   ├── models.py                  # Pydantic models (Deployment, Incident, DORAReport)
│   ├── classifier.py              # DORA band classification logic
│   ├── metrics_calculator.py      # Core metric computation
│   ├── github_client.py           # GitHub REST API client
│   ├── pagerduty_client.py        # PagerDuty REST API client
│   ├── sample_loader.py           # Built-in sample data for demo mode
│   └── reporter.py                # Rich terminal / Markdown / JSON renderer
├── tests/                         # pytest test suite (124 tests)
├── config/settings.yaml
├── requirements.txt
└── .env.example
```

## What I Learned

DORA metrics are deceptively simple to define but surprisingly nuanced to compute correctly. Lead time requires joining deployment records to PR commit history — GitHub's API doesn't provide this in a single call, so you need to correlate deployments → PRs → first commits. Change failure rate also requires deciding what "failure" means at the deployment level (I use the latest deployment status, since a rollback/re-deploy clears the failure). The DORA 2023 report updated some thresholds from prior years, and the distinction between "Elite" and "High" for deployment frequency (>=1/day vs 1/day–1/week) is worth knowing precisely.

## Stack

Python · Pydantic v2 · Typer · Rich · requests · pytest
