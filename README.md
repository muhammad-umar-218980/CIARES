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

## 2. The five Expert System components

| Component | Implementation | File |
|---|---|---|
| Knowledge Base | 5 modules of manually authored IF-THEN rules | `knowledge_base/` |
| Inference Engine | Forward chaining to a fixed point, activation tracking | `engine/inference_engine.py` |
| User Interface | 7-section Streamlit application | `app.py` |
| Explanation Facility | Trace explanation + justification explanation | `engine/explanation_engine.py` |
| Knowledge Acquisition | Structural validation and registration of curated rules | `knowledge_base/knowledge_acquisition.py` |

Supporting components: working memory with True/False/Unknown facts, a decision engine with
action priorities and conflict resolution, a simulated environment, predefined scenarios,
a pytest suite and documentation.

## 3. Current status

| Area | Status |
|---|---|
| Project scaffolding (32+ files) | complete |
| `models`, `working_memory`, `inference_engine` | complete and tested |
| `knowledge_acquisition`, `rule_registry` | complete and tested |
| `decision_engine`, `explanation_engine` | complete and tested |
| Simulated environment + all 15 actions | complete and tested |
| Streamlit UI, 7 sections | complete |
| Knowledge base | **60 of 60 rules**, 85 logical conditions, 5 modules |
| Scenarios SCN-001..006 | complete, all 60 rules reachable |
| Test suite | **90 passed, 0 skipped** |
| Public deployment | pending (needs your Streamlit Cloud account) |
| PDF + ZIP submission | pending |

The engine is generic, so each new rule is a data addition: write the `Rule`,
add a test, and it appears in the Knowledge Base page, the inference engine and
the scenario coverage automatically. See [section 8](#8-adding-rules-phase-3).

## 4. Architecture

```
app.py (Streamlit UI — no knowledge, no reasoning)
  │
  ├── scenarios/sample_scenarios.py ── observations + entity IDs
  │
  └── engine/pipeline.py ── run_investigation()
        │
        ├── engine/working_memory.py ── facts (True / False / Unknown) + provenance
        ├── knowledge_base/rule_registry.py ── ALL_RULES (60 rules)
        ├── engine/inference_engine.py ── forward chaining, activation tracking
        ├── engine/decision_engine.py ── findings -> targeted response actions
        ├── simulation/ ── simulated entities + 15 action handlers
        └── engine/explanation_engine.py ── trace + justification + Markdown report
```

Key separation:

* `knowledge_base/` defines **what CIARES knows**.
* `engine/` defines **how CIARES reasons**.
* `simulation/` performs **simulated responses**.
* `app.py` lets a human **interact** with all of it.

## 5. Installation and run

Requires Python 3.10+ (developed on 3.13).

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>.

Run the test suite:

```powershell
python -m pytest
```

Expected: **90 passed, 0 skipped**. The suite includes a coverage test that fails if
any of the 60 rules cannot fire in at least one shipped scenario.

## 6. Using the application

1. **Security Overview** — statistics computed from real investigation records.
2. **New Investigation** — enter observations. Booleans are True / False / **Unknown**.
3. **Scenario Laboratory** — run SCN-001 (account compromise), SCN-002 (malware),
   SCN-003 (network intrusion), SCN-004 (data exfiltration), SCN-005 (privilege abuse)
   or SCN-006 (credential abuse + data integrity).
4. **Knowledge Base** — inspect every rule, its conditions and the machine-generated
   condition inventory (evidence for the 50-condition requirement).
5. **Inference Trace** — activation order, per-rule justification, working-memory provenance.
6. **Response Center** — approve and execute simulated actions, see before/after state.
7. **Investigation History** — session state plus `data/investigations.json`.

## 7. Folder structure

```
CIARES/
├── app.py                  Streamlit UI (7 sections)
├── config.py               thresholds, approved sources, paths
├── requirements.txt
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
│   └── pipeline.py         run_investigation()
├── simulation/
│   ├── environment.py      simulated entities + transitions
│   ├── account_actions.py
│   ├── network_actions.py
│   ├── process_actions.py
│   └── data_policy_actions.py
├── scenarios/sample_scenarios.py   SCN-001..006
├── tests/                  6 test files + conftest
└── docs/
    ├── rule_catalogue.md   all 60 rules, conditions, status
    ├── rule_sources.md     NIST / CSF / ATT&CK / CISA mapping
    └── technical_design.md algorithms and design decisions
```

## 8. Extending the knowledge base

The 60-rule catalogue is complete. To add or change a rule:

1. Add/edit a `Rule(...)` object in the relevant module's tuple.
2. Use fact keys consistently with `app.py`'s observation schema
   (`failed_login_attempts`, `protected_file_modified`, ...).
3. Prefer chaining: derive indicators with Tier 1 rules and combine them in Tier 2/3 rules.
4. If the rule recommends a response, the action key must exist in
   `engine/decision_engine.py` (`ACTION_LIBRARY`) and in `simulation/`.
5. Run `python -m pytest`. `test_rules.py` validates structure, `test_scenarios.py`
   checks the expected chains, and `test_coverage.py` fails if a rule cannot fire.

Rules are validated automatically for: id format, uniqueness, description, at least one
condition, no self-supporting conclusion, valid severity, approved source, and action/entity
consistency.

## 9. Threshold assumptions

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

## 10. Deployment (pending)

1. Push this repository to GitHub (already initialised here).
2. Create an app on Streamlit Community Cloud pointing at `app.py`.
3. Ensure `requirements.txt` is committed (it is).
4. Test the public URL in an incognito window and on another device.

`data/investigations.json` is intentionally git-ignored: Streamlit Community Cloud has an
ephemeral filesystem, so the app degrades gracefully to session-only history when the file
cannot be written.

## 11. Limitations

* Simulated responses only. CIARES never connects to a real system.
* Manual knowledge acquisition: no learning, no external AI service.
* Single-entity-focus per investigation (one account/session/process per run).
* Numeric inputs are always considered provided; boolean inputs support Unknown.
* Thresholds are illustrative and configurable, not audited standards.

## 12. Submission checklist

- [x] Working inference engine with activation tracking and fixed point
- [x] Three-valued working memory and fact provenance
- [x] 60 rules / 85 logical conditions / 5 modules
- [x] Decision engine with target validation and conflict handling
- [x] Simulated execution for 15 actions
- [x] Trace and justification explanations
- [x] Seven-section Streamlit UI
- [x] Pytest suite
- [ ] Public Streamlit URL
- [ ] PDF code explanation and ZIP submission
