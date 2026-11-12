# CIARES

**Cybersecurity Incident Analysis and Response Expert System**

A Python-based, rule-driven Expert System that investigates security incidents, derives
findings with forward chaining, recommends responses, executes them in a simulated
environment and explains every decision.

Built with **Python + Streamlit only**. No trained model, no external reasoning service:
every conclusion is traceable to a manually authored IF-THEN rule.

---

## 1. What problem does it solve?

A security dashboard shows events. CIARES reasons about them.

```
Observations (25 failed logins, success after failures, unusual location)
        -> Working Memory
        -> Knowledge Base (AUTH-01, AUTH-02, AUTH-03)
        -> Inference Engine (forward chaining)
        -> AUTH-04: Possible account compromise
        -> Decision Engine: disable USER-101
        -> Simulated execution: USER-101 now Disabled
        -> Explanation: which rules fired, on which facts, why the action ran
```

## 2. Two portals, one engine

The application is deliberately split into two surfaces so the public demo stays simple
while the internals remain examinable.

| | Public portal | Admin portal |
|---|---|---|
| URL | `/` | `/admin` (typed manually — no link anywhere) |
| Login | none | email + password |
| Pages | Home, Investigate, Scenarios, Results | Dashboard, Knowledge base, Inference engine, Decision engine, Audit, System map |
| Audience | analyst / examiner | you, during the viva |

Both surfaces call the same `rule_registry`, `inference_engine`, `decision_engine` and
`simulation` code. The split is presentation only — there is no second reasoning path.

The admin nav entry is hidden with CSS, so `Admin portal` never appears in the sidebar, the
page list or any in-app button. Typing `/admin` is the only way in.

## 3. The five Expert System components

| Component | Implementation | File |
|---|---|---|
| Knowledge Base | 5 modules of manually authored IF-THEN rules | `knowledge_base/` |
| Inference Engine | Forward chaining to a fixed point, activation tracking | `engine/inference_engine.py` |
| User Interface | Public portal + hidden admin portal | `app.py`, `ui/` |
| Explanation Facility | Trace explanation, justification, "Why this finding?" | `engine/explanation_engine.py`, `ui/user/results.py` |
| Knowledge Acquisition | Structural validation and registration of curated rules | `knowledge_base/knowledge_acquisition.py` |

Supporting components: working memory with True/False/Unknown facts, a decision engine with
action priorities and conflict resolution, a simulated environment, predefined scenarios,
SQLite persistence, a pytest suite and documentation.

## 4. Current status

| Area | Status |
|---|---|
| `models`, `working_memory`, `inference_engine` | complete and tested |
| `knowledge_acquisition`, `rule_registry` | complete and tested |
| `decision_engine`, `explanation_engine` | complete and tested |
| Simulated environment + all 15 actions | complete and tested |
| Public portal (4 pages) | complete |
| Admin portal (6 tabs, login gate) | complete |
| Knowledge base | **60 of 60 rules**, 85 logical conditions, 5 modules |
| Scenarios SCN-001..006 | complete, all 60 rules reachable |
| SQLite persistence + audit trail | complete |
| Test suite | **111 passed, 0 skipped** |
| Public deployment | pending (needs your Streamlit Cloud account) |
| PDF + ZIP submission | deferred |

The engine is generic, so each new rule is a data addition: write the `Rule`, add a test, and
it appears in the admin knowledge base, the inference engine and the scenario coverage
automatically. See [section 9](#9-extending-the-knowledge-base).

## 5. Architecture

```
app.py (entry point: st.navigation only — no knowledge, no reasoning)
  │
  ├── ui/nav.py ── page registry (4 public pages + hidden /admin)
  ├── ui/shared/ ── theme, session state, auth gate, password hashing
  ├── ui/user/ ── home, investigate, scenarios, results
  └── ui/admin/ ── dashboard, knowledge, inference, decision, audit, system_map
        │
        └── engine/pipeline.py ── run_investigation()
              │
              ├── engine/working_memory.py ── facts (True / False / Unknown) + provenance
              ├── knowledge_base/rule_registry.py ── ALL_RULES (60 rules)
              ├── engine/inference_engine.py ── forward chaining, activation tracking
              ├── engine/decision_engine.py ── findings -> targeted response actions
              ├── simulation/ ── simulated entities + 15 action handlers
              └── engine/explanation_engine.py ── trace + justification + Markdown report

storage/db.py ── SQLite (data/ciares.db): investigations + admin_events
```

Key separation:

* `knowledge_base/` defines **what CIARES knows**.
* `engine/` defines **how CIARES reasons**.
* `simulation/` performs **simulated responses**.
* `ui/` lets a human **interact** with all of it.
* `storage/` records what happened, for the admin portal only.

A full file-by-file map, including *what breaks if a module is removed*, is rendered inside
the app at **Admin → System map** (`docs/system_map.md`).

## 6. Installation and run

Requires Python 3.10+ (developed on 3.13).

```powershell
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` with the admin credential:

```toml
[auth]
admin_email = "admin@ciares.local"
admin_password_hash = "pbkdf2_sha256$260000$<salt>$<digest>"
```

Generate a hash (never commit the plaintext password):

```powershell
python tools/hash_password.py
```

Then run:

```powershell
streamlit run app.py
```

Open <http://localhost:8501> for the public portal and <http://localhost:8501/admin> for the
admin portal.

Run the test suite:

```powershell
python -m pytest
```

Expected: **111 passed, 0 skipped**. The suite includes a coverage test that fails if any of
the 60 rules cannot fire in at least one shipped scenario.

## 7. Using the public portal

1. **Home** — what CIARES does, the five modules, rule/condition counts and entry points.
2. **Investigate** — enter observations. Booleans are True / False / **Unknown**. Response
   targets are assigned automatically from the simulated inventory, so no identifiers are
   typed.
3. **Scenarios** — run SCN-001 (account compromise), SCN-002 (malware), SCN-003 (network
   intrusion), SCN-004 (data exfiltration), SCN-005 (privilege abuse) or SCN-006 (credential
   abuse + data integrity).
4. **Results** — severity summary and chart, the diagnosis, a **Why this finding?** expander
   per finding, every proposed action with its rationale, and the approve → execute step.

Nothing on these pages exposes the rule catalogue or the activation trace.

## 8. Using the admin portal

Navigate to `/admin` and sign in. Six tabs:

| Tab | What it shows |
|---|---|
| Dashboard | Cross-investigation statistics, findings by severity/module, KB health, recent admin activity, simulated inventory |
| Knowledge base | All 60 rules, per-rule condition tables, machine-generated condition inventory |
| Inference engine | Activation order, per-activation justification, working memory with provenance, reasoning log |
| Decision engine | Decision rules, proposed actions, full action catalogue, **target validation lab** |
| Audit | Every stored investigation with filters, per-record drill-down, JSON/CSV export, admin events |
| System map | File responsibilities and impact-if-removed |

The target validation lab is where the blocked-target demonstration now lives: type
`USER-999` and the Decision Engine reports that the account does not exist in the simulated
environment. The public portal never asks for an identifier.

## 9. Extending the knowledge base

The 60-rule catalogue is complete. To add or change a rule:

1. Add/edit a `Rule(...)` object in the relevant module's tuple.
2. Use fact keys consistently with `ui/schema.py` (`failed_login_attempts`,
   `protected_file_modified`, ...).
3. Prefer chaining: derive indicators with Tier 1 rules and combine them in Tier 2/3 rules.
4. If the rule recommends a response, the action key must exist in
   `engine/decision_engine.py` (`ACTION_LIBRARY`) and in `simulation/`.
5. Run `python -m pytest`. `test_rules.py` validates structure, `test_scenarios.py` checks
   the expected chains, and `test_coverage.py` fails if a rule cannot fire.

Rules are validated automatically for: id format, uniqueness, description, at least one
condition, no self-supporting conclusion, valid severity, approved source, and action/entity
consistency.

## 10. Folder structure

```
CIARES/
├── app.py                  entry point (st.navigation)
├── config.py               thresholds, approved sources, paths
├── requirements.txt
├── ui/
│   ├── nav.py              page registry, incl. the hidden /admin page
│   ├── navigation.py       in-app page switching
│   ├── schema.py           observation form metadata
│   ├── shared/             theme, session state, auth, password hashing
│   ├── user/               home, investigate, scenarios, results
│   └── admin/              dashboard, knowledge, inference, decision, audit, system_map
├── storage/
│   └── db.py               SQLite schema, save/load, aggregates, admin events
├── knowledge_base/
│   ├── authentication.py   AUTH-01..12
│   ├── malware.py          MAL-01..12
│   ├── network.py          NET-01..12
│   ├── data_security.py    DATA-01..12
│   ├── security_policy.py  POL-01..12
│   ├── rule_registry.py    assembles ALL_RULES
│   └── knowledge_acquisition.py  validation + registration
├── engine/
│   ├── models.py           Rule, Condition, Fact, Finding, ResponseAction...
│   ├── working_memory.py   facts, provenance, contradiction protection
│   ├── inference_engine.py forward chaining
│   ├── decision_engine.py  action library, target checks, conflicts
│   ├── explanation_engine.py
│   ├── entities.py         default targets from the simulated inventory
│   └── pipeline.py         run_investigation()
├── simulation/
│   ├── environment.py      simulated entities + transitions
│   ├── account_actions.py
│   ├── network_actions.py
│   ├── process_actions.py
│   └── data_policy_actions.py
├── scenarios/sample_scenarios.py   SCN-001..006
├── tools/hash_password.py  PBKDF2 hash generator for the admin credential
├── tests/                  original suite + storage, entities, auth tests
└── docs/
    ├── system_map.md       file responsibilities + impact-if-removed
    ├── demo_guide.md       viva walkthrough
    ├── rule_catalogue.md   all 60 rules, conditions, status
    ├── rule_sources.md     NIST / CSF / ATT&CK / CISA mapping
    └── technical_design.md algorithms and design decisions
```

## 11. Storage

Investigations are written to `data/ciares.db` (SQLite). Two tables:

* `investigations` — one row per run: summary columns for the dashboard plus the full JSON
  payload needed to replay the reasoning.
* `admin_events` — admin sign-in, sign-out and destructive actions.

On Streamlit Community Cloud the filesystem is ephemeral: records survive while the container
is awake and reset after a redeploy or a long sleep. The app states this on the dashboard
rather than pretending the store is durable. `data/*.db` is git-ignored.

## 12. Threshold assumptions

All numbers in `config.THRESHOLDS` are **project assumptions**, not universal standards:

| Fact | Assumed threshold |
|---|---|
| `failed_login_attempts` | 10 |
| `concurrent_sessions` | 3 |
| `mfa_failures` | 5 |
| `outbound_traffic_mb` | 500 |
| `transfer_volume_mb` | 1000 |
| `download_count` | 100 |
| `connection_attempts` | 20 |
| `denied_requests` | 15 |

## 13. Deployment

1. Push this branch to GitHub.
2. Create a Streamlit Community Cloud app pointing at `app.py`.
3. Add the `[auth]` section to the app secrets (same keys as the local file above).
4. Test the public URL and `/admin` in an incognito window and on another device.

No other environment configuration is required — there is no external database or service.

## 14. Limitations

* Simulated responses only. CIARES never connects to a real system.
* Manual knowledge acquisition: no learning, no external AI service.
* Single-entity-focus per investigation (one account/session/process per run).
* Numeric inputs are always considered provided; boolean inputs support Unknown.
* Thresholds are illustrative and configurable, not audited standards.
* SQLite on Streamlit Community Cloud is ephemeral, as described in section 11.

## 15. Submission checklist

- [x] Working inference engine with activation tracking and fixed point
- [x] Three-valued working memory and fact provenance
- [x] 60 rules / 85 logical conditions / 5 modules
- [x] Decision engine with target validation and conflict handling
- [x] Simulated execution for 15 actions
- [x] Trace and justification explanations
- [x] Public portal: Home, Investigate, Scenarios, Results
- [x] Hidden admin portal with six tabs and a login gate
- [x] SQLite persistence and admin audit trail
- [x] Pytest suite (111 passed)
- [ ] Public Streamlit URL
- [ ] PDF code explanation and ZIP submission (deferred)
