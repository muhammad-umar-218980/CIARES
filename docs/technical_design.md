# CIARES Technical Design

This document explains how CIARES is implemented. It is the technical companion to
`README.md` and the source for report writing and the viva.

## 1. Design constraints

1. **No trained model, no LLM, no external reasoning service.** Every conclusion must be
   traceable to a manually authored rule.
2. **Streamlit is the only interface.** No Flask, no FastAPI, no separate frontend.
3. **Decision support only.** CIARES reads observations, recommends a response and writes a
   plan. It never executes anything against a real account, host, process or network.
4. **Explainability over cleverness.** If a decision cannot be justified from facts and rules,
   it is not made.
5. **Two routes only.** `/` for the public portal and `/admin` for administration. Everything
   else is a sidebar section or a tab, never a URL.

## 2. Component map

```
                     ┌──────────────────────────────┐
                     │ app.py  (public portal, /)   │
                     │ admin.py (administration)    │
                     └──────────────┬───────────────┘
                                    │ run_investigation()
┌───────────────────────────────────▼──────────────────────────────────────────┐
│ engine/pipeline.py                                                           │
│  1. load observations into working memory                                    │
│  2. run inference                                                            │
│  3. build findings                                                           │
│  4. run the decision engine                                                  │
└───┬───────────────┬────────────────┬──────────────────┬──────────────────────┘
    │               │                │                  │
┌───▼─────┐  ┌──────▼──────┐  ┌──────▼───────┐  ┌───────▼──────────────┐
│working  │  │inference    │  │decision      │  │engine/report.py      │
│memory   │  │engine       │  │engine        │  │score, prose, plan    │
│facts +  │  │forward      │  │action library│  │                      │
│provenance│ │chaining     │  │+ deferral    │  │                      │
└─────────┘  └──────┬───────┘  └──────────────┘  └──────────────────────┘
                    │
             ┌──────▼───────┐
             │knowledge_base│
             │ALL_RULES     │
             └──────────────┘
```

## 3. Data model (`engine/models.py`)

| Structure | Purpose | Key fields |
|---|---|---|
| `Condition` | One logical condition | `field`, `operator`, `value`, `label` |
| `Rule` | One IF-THEN rule | `id`, `conditions`, `conclusion_key`, `severity`, `source`, `recommended_action`, `action_phase`, `priority` |
| `Fact` | A working-memory entry | `key`, `value`, `derived`, `rule_id`, `supporting`, `sequence` |
| `ConditionEvaluation` | Result of evaluating a condition | `satisfied` (True/False/None), `observed`, `note` |
| `RuleActivation` | One rule firing | `sequence`, `rule`, `evaluations`, `activation_key`, `inserted_new_fact` |
| `Finding` | A diagnosis | `key`, `label`, `severity`, `module`, `rule_ids`, `description`, `recommended_action` |
| `ResponseAction` | A recommendation | `action`, `label`, `phase`, `priority`, `reason`, `approved`, `deferred`, `defer_reason` |
| `Investigation` | Whole run | observations, activations, findings, actions, trace, `approved_at` |

Conditions are **declarative data**, not lambdas. That is what makes rule inspection and
justification possible:

```python
Condition(
    "failed_login_attempts", ">=", THRESHOLDS["failed_login_attempts"],
    f"failed login attempts >= {THRESHOLDS['failed_login_attempts']}",
)
```

## 4. Knowledge representation

* A rule is an implication `C1 AND C2 AND ... -> conclusion`.
* All rules assert a conclusion with value `True`. The system does not model retraction;
  inference is monotonic by design.
* A rule either derives an **indicator** (no action) or a **finding with a recommended
  response** (`recommended_action`, `action_phase`).
* Rule priority is used only for deterministic firing order. It never discards findings.
* Thresholds live in `config.py`; the knowledge base contains no magic numbers.
* Sources are restricted to the approved list (`config.APPROVED_SOURCES`), enforced by the
  knowledge acquisition module.

## 5. Working memory and three-valued logic

Fact states:

| State | Storage | Meaning |
|---|---|---|
| True | `Fact(value=True)` | Confirmed observation or derived conclusion |
| False | `Fact(value=False)` | Explicitly observed as absent |
| Unknown | key missing, or `Fact(value=None)` | Not established |

`Condition.evaluate(observed, known)` returns a triple. When the fact is not known:

```python
return None, "field is Unknown - condition cannot be evaluated"
```

Rules require **every** condition to evaluate to `True`. A single `None` or `False` makes the
rule ineligible. This is why the system never treats "we did not ask" as "it did not happen".

Provenance is stored on every derived fact:

```python
Fact(key="possible_account_compromise", value=True, derived=True,
     rule_id="AUTH-04",
     supporting=(("repeated_authentication_failures", True),
                 ("suspicious_login_sequence", True),
                 ("unusual_location_login", True)))
```

Contradictions are rejected rather than overwritten:

* an observation cannot overwrite a derived fact;
* two different observed values for the same fact raise `ContradictionError`;
* a rule deriving a different value for an established fact raises `ContradictionError`.

## 6. Forward-chaining algorithm (`engine/inference_engine.py`)

```python
fired = set()
while cycles < max_cycles:
    eligible = []
    for rule in rules:
        eligible_flag, evaluations = evaluate(rule, memory)   # all conditions True?
        if not eligible_flag:
            continue
        key = activation_key(rule, evaluations)
        if key in fired:
            continue
        eligible.append((rule, evaluations, key))

    if not eligible:
        terminated_reason = "fixed point: no further eligible rules"
        break

    eligible.sort(key=lambda item: (-item[0].severity.rank, item[0].priority, item[0].id))
    rule, evaluations, key = eligible[0]        # fire ONE rule

    memory.infer(rule.conclusion_key, True, rule, support)
    fired.add(key)
    record_activation(rule, evaluations, key)
```

Design notes:

* **One rule per cycle, then re-evaluate.** Correctness of the recorded order matters more
  than a small performance gain with 60 rules.
* **Deterministic conflict resolution.** Highest severity, then author priority, then id.
  Ties never depend on dictionary order.
* **Termination.** Facts are only ever added (monotonic), and every activation key can fire
  once. The reachable fact set is finite, so the loop reaches a fixed point. `max_cycles` is
  a safety guard (`max(100, 5 * rule_count)`), and the termination reason is reported.

## 7. Activation tracking

```
activation_key = rule_id "::" condition_field=observed_value "::" ...
```

Consequences:

* AUTH-01 cannot fire repeatedly against the same observations (the key repeats).
* If a supporting value changes (for example a new failed-login count), the key changes and
  the rule may fire again — correct, because the evidence changed.
* Entity identifiers are deliberately not part of the key: CIARES analyses one incident at a
  time, not an inventory of targets.

## 8. Conflict resolution

### Inference conflicts

Multiple rules may derive different findings from the same evidence. CIARES **keeps all of
them**: `build_findings()` merges support for identical conclusions but never drops a
finding because another one is more severe. The admin dashboard therefore counts all
findings.

### Response conflicts

`DecisionEngine._defer_recovery()` implements an explicit safety rule: if any containment
action is proposed, recovery actions are marked `deferred` with a reason. Example:
`disable_account` plus `revoke_permissions` yields containment first and a deferred recovery,
never a contradictory pair. Deferred actions cannot be approved.

## 9. Decision Engine (`engine/decision_engine.py`)

Each action key is described by an `ActionSpec`:

```python
"disable_account": ActionSpec(
    key="disable_account", label="Disable affected account",
    phase=Phase.CONTAINMENT, priority=1,
    description="Stop all further sign-in with the affected credential.",
)
```

Decision procedure:

1. Keep only findings with `recommended_action`; sort by severity then derivation order.
2. Resolve each action key through `ACTION_LIBRARY`; unknown keys still produce a
   recommendation using the finding's phase.
3. Collapse duplicates by action key into one recommendation and append the second finding to
   the reason; the strongest finding severity is kept.
4. Defer recovery actions while any containment action is present.
5. Sort by phase (Containment → Eradication → Recovery → Escalation), then priority, then
   action key; assign `ACT-001`-style ids.

The decision engine is pure policy. It does not validate a target and it never mutates state.

## 10. Report Writer (`engine/report.py`)

The public portal never shows a wall of rule identifiers. This module produces the sentences
it does show:

| Function | Output |
|---|---|
| `threat_score()` | Additive score: Critical 50, High 25, Medium 10, Low 5, capped at 100 |
| `threat_sentence()` | "Threat level 85 out of 100 — High severity: …" |
| `overview_paragraph()` | Observation count, finding counts by severity, the worst conclusion |
| `finding_paragraphs()` | One plain-language paragraph per finding |
| `reasoning_paragraphs()` | The observations that supported each conclusion — **no rule ids** |
| `evidence_rows()` | Administrative table: rule id, name, conclusion, severity |
| `approve()` | Records the analyst's selection; deferred actions are excluded |
| `plan_steps()` / `plan_text()` | Numbered, imperative response plan and its `.txt` export |

The score is a documented project assumption, not a probability.

## 11. Explanation Facility (`engine/explanation_engine.py`)

| Output | Content |
|---|---|
| Trace explanation | Ordered activation list plus the reasoning log |
| Justification explanation | Per activation: rule metadata, each condition with expected/observed/status |
| Action explanation | Why the action was selected and whether it is approved or deferred |
| Markdown report | Full investigation export for report appendices |

The facility reads records; it never re-reasons. It is used by `/admin`, while
`engine/report.py` is used by the public portal.

## 12. Knowledge Acquisition (`knowledge_base/knowledge_acquisition.py`)

`validate_rule()` enforces:

| Check | Failure mode |
|---|---|
| ID matches `(AUTH|MAL|NET|DATA|POL)-NN` | error |
| ID unique in the catalogue | error |
| Name, description present | error |
| At least one condition | error |
| Conclusion present and not one of its own conditions | error |
| Severity is a `Severity` value | error |
| Source is approved | error |
| Action key is snake_case and phase is a `Phase` value | error |

`validate_catalogue()` additionally counts rules, conditions and distinct fact fields, and
reports the 50-condition / 60-rule targets as warnings if a future edit drops below them.
`KnowledgeAcquisition.register()` refuses invalid rules outright.

## 13. Pipeline (`engine/pipeline.py`)

`run_investigation()` is the only entry point used by the portal and by scenario tests:

```
observations
  -> Investigation record
  -> WorkingMemory + observations
  -> InferenceEngine.run()
  -> build_findings()
  -> DecisionEngine.decide()
  -> Investigation(activations, findings, actions, trace)
```

Because the public portal, the Scenario section and pytest all call this function, there is
no second code path that could behave differently.

## 14. UI architecture

* `/` is a single Streamlit page. A sidebar radio switches between Home, Investigate,
  Scenarios and Results; no URL changes.
* `/admin` is registered with `visibility="hidden"` so Streamlit does not list it. The built-in
  sidebar page list is hidden with CSS, so the only menu is the radio.
* Navigation requested from inside a page is queued in `st.session_state["_goto"]` and applied
  *before* the radio widget is created. Assigning `st.session_state.section` afterwards
  raises `StreamlitAPIException`.
* One `st.form` for manual entry; booleans are `Unknown / True / False` select boxes.
* `theme.py` applies Poppins to text elements. The Material icon font is restored explicitly,
  otherwise Streamlit's arrows and expander chevrons turn into words.
* Approval checkboxes are keyed `approve_<action_id>` and cleared when a new investigation is
  launched.

## 15. Storage schema (`storage/db.py`)

```sql
CREATE TABLE investigations (
    id TEXT PRIMARY KEY, created_at TEXT, name TEXT, source TEXT,
    scenario_id TEXT, activation_count INTEGER, finding_count INTEGER,
    critical_count INTEGER, high_count INTEGER, medium_count INTEGER, low_count INTEGER,
    action_count INTEGER, approved_count INTEGER, score INTEGER,
    terminated_reason TEXT, payload TEXT
);

CREATE TABLE admin_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, event TEXT, detail TEXT
);
```

The summary columns feed the dashboard; `payload` is the full JSON record used to replay the
investigation and the approved plan. `save_investigation()` upserts, so approving a plan
updates the same row.

## 16. Testing strategy

| File | Covers |
|---|---|
| `test_rules.py` | threshold behaviour, Unknown vs False, corroboration, condition semantics, catalogue integrity |
| `test_inference.py` | chaining order, fixed point, no re-fire, activation keys, provenance, contradiction handling |
| `test_decisions.py` | recommendation selection, deduplication, recovery deferral, phase ordering, action-library consistency |
| `test_scenarios.py` | six end-to-end scenarios, JSON-serialisable records, no preloaded diagnoses, prose hides rule ids, approval and plan |
| `test_coverage.py` | exactly 60 rules / 12 per module, ≥50 conditions, every rule reachable, every actionable rule produces a response |
| `test_storage.py` | round-trip, aggregates, approval persistence, admin events |
| `test_auth.py` | hashing, constant-time verification, credential checks |

The suite is completist by design: **106 tests**, no skips. The coverage test fails if a rule
can never fire, which prevents the catalogue from being padded with cosmetic rules.

## 17. Extending the system

1. Add the rule to the module tuple; keep conclusion keys distinct from observation keys.
2. Add or reuse an action in `ACTION_LIBRARY`.
3. Run `python -m pytest`; then `streamlit run app.py` and run SCN-00x.
4. Update `docs/rule_catalogue.md`.
5. Add the new rule to a scenario and to `expected_findings`; the coverage test requires every
   registered rule to fire at least once.

## 18. Limitations

* Monotonic inference: no retraction or non-monotonic reasoning.
* One incident per investigation; CIARES does not correlate multiple entities.
* Numeric observations are always considered known; only booleans use Unknown.
* Single demonstration administrator; no user database or multi-user persistence.
* SQLite is ephemeral on Streamlit Community Cloud.
* Thresholds and the threat score are illustrative project assumptions, not audited standards.
