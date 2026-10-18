# Architecture Decision Records — dora-metrics-dashboard

---

## ADR-001: GitHub Deployments API vs Workflow Runs API

**Status:** Accepted

**Context:** Two GitHub APIs can surface deployment events: the Deployments API (`/repos/{owner}/{repo}/deployments`) and the Actions API (`/repos/{owner}/{repo}/actions/runs`). We need to choose which to use as the source of truth for Deployment Frequency and Lead Time.

**Decision:** Use the GitHub Deployments API filtered by `environment=production`.

**Rationale:**
- Workflow runs include non-production runs (PR checks, staging deploys, scheduled jobs). Counting them would inflate Deployment Frequency.
- The Deployments API has an explicit `environment` field and a `state` endpoint for success/failure — exactly what we need for CFR.
- Teams that don't use GitHub Deployments API will need to adapt, but this is the correct semantic boundary.

**Consequences:**
- Teams using CD tools (ArgoCD, Spinnaker) that don't post to GitHub Deployments API won't get data without adapting their pipelines.
- Accepted limitation: documented in README.

---

## ADR-002: Lead Time — First Commit vs Merge Commit

**Status:** Accepted

**Context:** Lead time can be measured from: (a) first commit in the feature branch, (b) PR merge commit, or (c) deployment trigger. These give different values and different business meanings.

**Decision:** Measure from first commit in the PR to deployment.

**Rationale:**
- DORA definition: "time it takes to go from code committed to code successfully running in production."
- "Code committed" means the developer's first commit — not when it merged. Merge-to-deploy only measures the integration pipeline, ignoring review time.
- First-commit-to-deploy is a fuller picture of the value stream.

**Consequences:**
- Requires two extra API calls per deployment (commit→PR lookup, then PR commits list).
- Deployments without associated PRs (direct commits) have no lead time data and are excluded from the sample. This is logged at WARNING level.

---

## ADR-003: Session Injection for HTTP Clients

**Status:** Accepted

**Context:** Both `GitHubClient` and `PagerDutyClient` make HTTP calls. We need a testing strategy that doesn't require live API credentials or HTTP mocking at the transport level.

**Decision:** Both clients accept an optional `session: requests.Session` parameter. If `None`, they create their own. Tests pass mock sessions directly.

**Rationale:**
- Cleaner than `unittest.mock.patch` at the import level — tests are explicit about what's mocked.
- Pattern is idiomatic in Python HTTP client testing.
- No third-party HTTP mocking library required (no `responses`, `httpretty`, `pytest-httpserver`).

**Consequences:**
- Slightly non-standard constructor signature (`session` is an implementation detail, not a domain concept).
- Accepted: the alternative (patching) is more brittle.

---

## ADR-004: DORAClassifier as Separate Class

**Status:** Accepted

**Context:** DORA thresholds are defined externally (dora.dev) and updated annually. They could be hardcoded inside `MetricsCalculator` or extracted to a separate class.

**Decision:** Extract to `DORAClassifier`.

**Rationale:**
- Separation of concerns: calculation logic (what is the MTTR?) vs classification logic (is 3h MTTR "High" or "Medium"?).
- Thresholds are independently testable without constructing full metric objects.
- If thresholds need to be configurable per-team (some orgs use different SLOs), the classifier can be subclassed or injected.

**Consequences:**
- One extra class to understand.
- `MetricsCalculator` accepts an optional `classifier` for injection — useful in tests that want to override bands.

---

## ADR-005: Pydantic v2 for All Data Models

**Status:** Accepted

**Context:** Data flowing between API clients, calculator, and reporter needs to be validated and serialisable. Options: plain dataclasses, TypedDict, Pydantic v1, Pydantic v2.

**Decision:** Pydantic v2.

**Rationale:**
- JSON serialisation via `model_dump_json()` with no custom code — critical for the `--format json` output.
- Datetime validation: Pydantic v2 enforces timezone-aware datetimes when the field type is `datetime`.
- Consistent with the rest of the portfolio (Weeks 15-24 all use Pydantic v2).

**Consequences:**
- v2 is not backwards-compatible with v1 (different import paths, `model_dump` replaces `dict()`).
- Accepted: v2 is the current standard; we don't support v1.
