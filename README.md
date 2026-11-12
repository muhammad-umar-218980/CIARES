# CIARES

**Cybersecurity Incident Analysis and Response Expert System**

A small, rule-based Expert System written in **Python + Streamlit**. You describe what was
observed; CIARES decides what it means, explains why in plain language, recommends a
response, and — once you approve it — writes the response plan.

No trained model. No external AI service. No simulation. Every conclusion comes from a
manually authored IF-THEN rule.

---

## 1. The idea

A security dashboard shows events. CIARES reasons about them:

```
25 failed logins + a success afterwards + an unusual location
        -> 4 findings, the worst being "Possible account compromise"
        -> "Critical: examine the account and contain it now"
        -> Recommendation: disable the affected account
        -> You tick the recommendations you accept
        -> A written response plan you can download
```

CIARES never touches a real account, host or network. It is decision support: the analyst
approves, the analyst acts.

## 2. Two routes only

| | Public portal | Administration |
|---|---|---|
| URL | `/` | `/admin` (typed manually, not linked) |
| Login | none | email + password |
| Content | Home, Investigate, Scenarios, Results | Dashboard, Knowledge base, Inference engine, Decision engine, Audit, System map |

`/` is a single page. Home, Investigate, Scenarios and Results are **sidebar sections**, not
separate URLs. `/admin` is protected, hidden from the sidebar, and is the only place where
rule identifiers and technical tables appear by default.

## 3. What a run looks like

1. **Describe** — enter observations. Each boolean is True, False or **Unknown**, and Unknown
   is not the same as False: a rule that needs an unknown fact will not fire.
2. **Diagnose** — forward chaining fires rules until nothing new can be derived. Findings are
   merged by conclusion, and the strongest severity wins.
3. **Explain** — the Results section states the issue, the severity, the threat score and the
   observations behind each conclusion, in sentences. Rule identifiers are not shown.
4. **Approve** — every recommendation is a checkbox. Deferred recovery steps are listed
   separately and cannot be approved while containment is open.
5. **Receive the plan** — after approval, CIARES writes a numbered response plan and offers it
   as a `.txt` download.

A collapsed **Technical evidence (administrative)** table on Results exposes the rule
identifiers for audit. It is closed by default.

## 4. What ships

| Item | Count |
|---|---|
| Rules | 60 (12 per module) |
| Logical conditions | 85 |
| Knowledge modules | 5 |
| Distinct facts | 80 |
| Predefined scenarios | 6 |
| Response actions in the catalogue | 15 |
| Automated tests | 106 |

Modules: Authentication & Account Security, Malware & Process Security, Network Security,
Data Security & Protection, Privilege & Security Policy.

## 5. The five Expert System components

| Component | Implementation |
|---|---|
| Knowledge Base | `knowledge_base/` — five modules of IF-THEN rules |
| Inference Engine | `engine/inference_engine.py` — forward chaining to a fixed point |
| User Interface | `app.py` (public) and `admin.py` (administration) |
| Explanation Facility | `engine/report.py`, `engine/explanation_engine.py` |
| Knowledge Acquisition | `knowledge_base/knowledge_acquisition.py` — validation and registration |

Supporting pieces: three-valued working memory with provenance, a decision engine that turns
findings into ordered recommendations, six scenarios, SQLite persistence and the test suite.

## 6. Engine, in one diagram

```
app.py ── public portal (sections, prose, approval)
admin.py ── administration (six tabs)
   │
   └── engine/pipeline.py :: run_investigation()
         │
         ├── engine/working_memory.py    True / False / Unknown facts + provenance
         ├── knowledge_base/             ALL_RULES (60 rules, 85 conditions)
         ├── engine/inference_engine.py  forward chaining, activation tracking
         ├── engine/decision_engine.py   findings -> ordered recommendations
         ├── engine/report.py            threat score, prose, approval, plan
         └── engine/explanation_engine.py  admin tables and justifications

storage/db.py ── SQLite (data/ciares.db): investigations + admin_events
```

Separation of concerns:

* `knowledge_base/` — **what** CIARES knows.
* `engine/` — **how** it reasons.
* `theme.py`, `app.py`, `admin.py` — **how it is presented**.
* `storage/` — **what happened**, for the audit trail.

## 7. Install and run

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

Generate the hash — never commit the plaintext password:

```powershell
python tools/hash_password.py
```

Run:

```powershell
streamlit run app.py
```

Public portal: <http://localhost:8501>  ·  Administration: <http://localhost:8501/admin>

Test:

```powershell
python -m pytest -q
```

Expected: **106 passed**.

## 8. Using the public portal

* **Home** — what CIARES does, the five modules, the counts, and the two ways in.
* **Investigate** — the observation form, grouped in five expanders with tri-state booleans.
* **Scenarios** — SCN-001 account compromise, SCN-002 malware, SCN-003 network intrusion,
  SCN-004 data exfiltration, SCN-005 privilege escalation, SCN-006 credential abuse and data
  integrity. A scenario supplies observations only; the diagnosis comes from the same engine.
* **Results** — threat meter (score 0-100 plus one sentence), the headline, the findings in
  prose, "what led to this", the recommendations and the approval step, then the plan.

## 9. Using the administration portal

Typing `/admin` is the only way in. After signing in:

| Tab | What it shows |
|---|---|
| Dashboard | Runs, findings, approved actions, rules/conditions, charts, KB health, recent admin events |
| Knowledge base | All 60 rules, per-rule conditions, condition inventory |
| Inference engine | Activation order, justification per activation, working memory with provenance, reasoning log |
| Decision engine | Decision rules, recommendations, full action catalogue |
| Audit | Stored investigations with filters, per-record drill-down, JSON/CSV export, admin events |
| System map | File responsibilities and impact if removed |

The admin portal is the only place that shows rule identifiers, traces and tables by default.

## 10. Folder structure

```
CIARES/
├── app.py                     public portal: routing, form, results, approval
├── admin.py                   administration: login gate + six tabs
├── theme.py                   Poppins, hero, cards, threat meter, footer
├── passwords.py               PBKDF2 hashing and credential checks
├── config.py                  thresholds, approved sources, paths
├── knowledge_base/
│   ├── authentication.py      AUTH-01..12
│   ├── malware.py             MAL-01..12
│   ├── network.py             NET-01..12
│   ├── data_security.py       DATA-01..12
│   ├── security_policy.py     POL-01..12
│   ├── rule_registry.py       assembles ALL_RULES
│   └── knowledge_acquisition.py  validation and registration
├── engine/
│   ├── models.py              Rule, Condition, Fact, Finding, ResponseAction, Investigation
│   ├── working_memory.py      facts, provenance, contradiction protection
│   ├── inference_engine.py    forward chaining
│   ├── decision_engine.py     action catalogue, conflicts, phase ordering
│   ├── report.py              prose diagnosis, approval, response plan
│   ├── explanation_engine.py  admin trace and justification
│   └── pipeline.py            run_investigation()
├── scenarios/sample_scenarios.py   SCN-001..006
├── storage/db.py              SQLite schema, save/load, aggregates, admin events
├── tools/hash_password.py     PBKDF2 hash generator
├── tests/                     engine, rules, scenarios, storage, auth
└── docs/                      system map, technical design, demo guide, rule catalogue
```

## 11. Storage

`data/ciares.db` holds two tables:

* `investigations` — one row per run: summary columns for the dashboard plus the JSON payload
  needed to replay the reasoning and the approved plan.
* `admin_events` — sign-in, sign-out and destructive actions.

On Streamlit Community Cloud the filesystem is ephemeral, so records survive while the
container is awake and reset after a redeploy or a long sleep. `data/*.db` is git-ignored.

## 12. Threshold assumptions

The numbers in `config.THRESHOLDS` are **project assumptions**, not universal standards:

| Fact | Assumed threshold |
|---|---|
| `failed_login_attempts` | 10 |
| `concurrent_sessions` | 3 |
| `mfa_failures` | 5 |
| `outbound_traffic_mb` | 500 |
| `transfer_volume_mb` | 1000 |
| `download_count` | 100 |
| `connection_attempts` | 20 |
| `denied_request_count` | 15 |

The threat score is equally explicit: Critical 50, High 25, Medium 10, Low 5, capped at 100.

## 13. Limitations

* Decision support only — CIARES reads observations and writes a plan; it never executes.
* Manual knowledge acquisition: no learning and no external AI service.
* Booleans support Unknown; numeric inputs are treated as provided.
* Thresholds and the threat score are illustrative and configurable.
* SQLite on Streamlit Community Cloud is ephemeral, as described in section 11.

## 14. Submission checklist

- [x] Forward-chaining inference with activation tracking and a fixed point
- [x] Three-valued working memory and fact provenance
- [x] 60 rules / 85 conditions / 5 modules
- [x] Decision engine with deduplication, recovery deferral and phase ordering
- [x] Prose diagnosis, threat score and human approval
- [x] Written response plan with download
- [x] Public portal at `/` with four sidebar sections
- [x] Hidden administration portal at `/admin` with six tabs
- [x] SQLite persistence and audit trail
- [x] Pytest suite (106 passed)
- [ ] Public Streamlit URL
- [ ] PDF code explanation and ZIP submission (deferred)
