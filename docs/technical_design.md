# CIARES Technical Design

This document explains how CIARES is implemented. It is the technical companion to
`README.md` and the source for report writing and the viva.

## 1. Design constraints

1. **No trained model, no LLM, no external reasoning service.** Every conclusion must be
   traceable to a manually authored rule.
2. **Streamlit is the only interface.** No Flask, no FastAPI, no separate frontend.
3. **Simulated responses only.** No real account, process, host or network is touched.
4. **Explainability over cleverness.** If a decision cannot be justified from facts and
   rules, it is not made.

## 2. Component map

```
                         ┌──────────────────────────┐
                         │  app.py (7 Streamlit)    │
                         └────────────┬─────────────┘
                                      │ run_investigation()
┌─────────────────────────────────────▼──────────────────────────────────────┐
│ engine/pipeline.py                                                         │
│  1. load observations into working memory                                  │
│  2. run inference                                                          │
│  3. build findings                                                         │
│  4. run decision engine                                                    │
└───┬───────────────┬────────────────┬──────────────────┬────────────────────┘
    │               │                │                  │
┌───▼─────┐  ┌──────▼──────┐  ┌──────▼───────┐  ┌───────▼────────┐
│working  │  │inference    │  │decision      │  │simulation/     │
│memory   │  │engine       │  │engine        │  │environment +   │
│facts +  │  │forward      │  │action library│  │15 action       │
│provenance│ │chaining     │  │+ validation  │  │handlers        │
└─────────┘  └──────┬───────┘  └──────────────┘  └───────┬────────┘
                    │                                   │
             ┌──────▼───────┐                  ┌────────▼─────────┐
             │knowledge_base│                  │explanation_engine│
             │ALL_RULES     │                  │trace + justify   │
             └──────────────┘                  └──────────────────┘
```

## 3. Data model (`engine/models.py`)

| Structure | Purpose | Key fields |
|---|---|---|
| `Condition` | One logical condition | `field`, `operator`, `value`, `label` |
| `Rule` | One IF-THEN rule | `id`, `conditions`, `conclusion_key`, `severity`, `source`, `recommended_action`, `action_phase`, `entity_type`, `priority` |
| `Fact` | A working-memory entry | `key`, `value`, `derived`, `rule_id`, `supporting`, `sequence` |
| `ConditionEvaluation` | Result of evaluating a condition | `satisfied` (True/False/None), `observed`, `note` |
| `RuleActivation` | One rule firing | `sequence`, `rule`, `evaluations`, `activation_key`, `inserted_new_fact` |
| `Finding` | A diagnosis | `key`, `label`, `severity`, `module`, `rule_ids`, `recommended_action` |
| `ResponseAction` | A proposed response | `action`, `phase`, `priority`, `target_type`, `target_id`, `executable`, `blocked_reason`, `status` |
| `ExecutionResult` | Outcome of simulation | `success`, `message`, `before`, `after` |
| `Investigation` | Whole run | observations, activations, findings, actions, trace, environment |

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
  response** (`recommended_action`, `action_phase`, `entity_type`).
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

`Condition.evaluate(observed, known)` returns a triple:

```python
if not known:
    return None, "field is Unknown - condition cannot be evaluated"
```

Rules require **every** condition to evaluate to `True`. A single `None` or `False` makes
the rule ineligible. This is why the system never treats "we did not ask" as "it did not
happen".

Provenance is stored on every derived fact:

```python
Fact(key="possible_account_compromise", value=True, source="AUTH-04", derived=True,
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
        key = activation_key(rule, memory.entities, evaluations)
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
  once. The reachable fact set is finite, so the loop reaches a fixed point. `max_cycles`
  is a safety guard (`max(100, 5 * rule_count)`), and the termination reason is reported.
* **Batch vs incremental.** Batch firing all eligible rules in one pass would record an
  ordering that did not actually drive the reasoning; CIARES refuses that.

## 7. Activation tracking

```
activation_key = rule_id "::" sorted(entity_id=value) "::" condition_field=observed_value
```

Consequences:

* AUTH-01 cannot fire ten times against the same observations (key repeats).
* The same rule can fire once per entity set, which supports multi-account analysis.
* If a supporting value changes (for example a new failed-login count), the key changes and
  the rule may fire again - correct, because the evidence changed.

## 8. Conflict resolution

### Inference conflicts

Multiple rules may derive different findings from the same evidence. CIARES **keeps all of
them**: `build_findings()` merges support for identical conclusions but never drops a
finding because another one is more severe. The admin dashboard therefore counts all
findings.

### Response conflicts

`DecisionEngine._suppress_recovery_after_containment()` implements an explicit safety rule:
if a containment action targets an entity, recovery actions against the same entity are
marked `Skipped` with a reason. Example: `disable_account` plus `restore_permissions` on
`USER-101` yields containment first and a deferred recovery, never a contradictory pair.

## 9. Decision Engine (`engine/decision_engine.py`)

Each action key is described by an `ActionSpec`:

```python
"disable_account": ActionSpec(
    key="disable_account", label="Disable affected account",
    phase=Phase.CONTAINMENT, priority=1, target_type="account",
    required_field="status", required_values=frozenset({"Active", "Locked"}),
)
```

Decision procedure:

1. Keep only findings with `recommended_action`; sort by severity then derivation order.
2. Resolve the target from the investigation's entity map (`account_id`, `session_id`, ...).
3. Validate:
   * target identifier present,
   * target exists in the simulated environment,
   * target is in a required state (`Active`, `Present`, `Running`, ...).
   Failures produce `executable=False` plus a human-readable `blocked_reason`; the action is
   shown, not hidden.
4. Collapse duplicates `(action, target)` into one action and append the second finding to
   the reason.
5. Suppress recovery after containment on the same target.
6. Sort by phase (Containment → Eradication → Recovery → Escalation), then priority, then
   action key; assign `ACT-001`-style ids.

The decision engine never mutates simulated state.

## 10. Simulation layer (`simulation/`)

Entity types and default states:

| Entity | Default | Terminal states used by CIARES |
|---|---|---|
| account | Active | Disabled, Locked, Active (restored) |
| account.permissions | Approved | Revoked, Elevated, Approved (restored) |
| account.data_access | Unrestricted | Restricted |
| session | Active | Revoked |
| process | Running | Isolated, Terminated |
| file | Present | Quarantined |
| transfer | Active | Restricted |
| destination | Reachable | Blocked |
| endpoint | Online | Isolated |
| connection | Open | Restricted |

`SimulatedEnvironment.transition()` enforces `allowed_from` sets, so an illegal transition
(e.g. disabling an already disabled account) is rejected with an explanation. Actions are
routed through `simulation.execute()`, which also refuses actions the decision engine marked
non-executable.

The environment is seeded with `USER-101`, `SESSION-204`, `PROCESS-401`, `FILE-501`,
`TRANSFER-301`, `DEST-901`, `ENDPOINT-701` and `CONN-801`. Entities named in an
investigation are **not** auto-created: the inventory is fixed, so a response aimed at
`USER-999` is rejected with an explanation, demonstrating target validation end to end.

## 11. Explanation Facility (`engine/explanation_engine.py`)

| Output | Content |
|---|---|
| Trace explanation | Ordered activation list plus the reasoning log (start, observations, activations, diagnosis, decision, finish) |
| Justification explanation | Per activation: rule metadata, each condition with expected/observed/status, conclusion |
| Action explanation | Why the action was selected, target-check outcome, execution status and `before -> after` state |
| Markdown report | Full investigation export for report appendices |

The facility reads records; it never re-reasons.

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
| Action key, phase and entity type consistent | error |

`validate_catalogue()` additionally counts rules, conditions and distinct fact fields, and
reports the 50-condition / 60-rule targets as warnings if a future edit drops below them.
`KnowledgeAcquisition.register()` refuses invalid rules outright.

## 13. Pipeline (`engine/pipeline.py`)

`run_investigation()` is the only entry point used by the UI and by scenario tests:

```
observations + entities
  -> Investigation record
  -> WorkingMemory + observations
  -> InferenceEngine.run()
  -> build_findings()
  -> SimulatedEnvironment.provision_from_entities()
  -> DecisionEngine.decide()
  -> Investigation(activations, findings, actions, trace, environment)
```

Because the Streamlit page, the Scenario Laboratory and pytest all call this function, there
is no second code path that could behave differently.

## 14. UI architecture (`app.py`)

* One `st.form` for manual entry; booleans are `Unknown / True / False` select boxes.
* `st.session_state` holds the active investigation, its environment and the history list.
* History is mirrored to `data/investigations.json` (best effort). On a read-only
  filesystem the app keeps working with session-only history.
* Seven pages are plain functions dispatched from a sidebar radio. No routing library.
* The Knowledge Base page computes its counts from `ALL_RULES`, so the 60-rule / 50-condition
  evidence is always current.

## 15. Testing strategy

| File | Covers |
|---|---|
| `test_rules.py` | threshold behaviour, Unknown vs False, corroboration, condition semantics, catalogue integrity |
| `test_inference.py` | chaining order, fixed point, no re-fire, activation keys, provenance, contradiction handling |
| `test_decisions.py` | target validation, state validation, duplicates, containment/recovery conflict, ordering, action-library consistency |
| `test_simulation.py` | successful transitions, rejected transitions, missing targets, blocked actions, snapshots |
| `test_scenarios.py` | six end-to-end scenarios, JSON-serialisable records, no preloaded diagnoses, missing-evidence behaviour |
| `test_coverage.py` | exactly 60 rules / 12 per module, ≥50 conditions, every rule reachable, every actionable rule produces a response, every executable action succeeds, phases ordered, explanations complete |

The suite is completist by design: 92 tests, no skips. The coverage test fails if a rule can
never fire, which prevents the catalogue from being padded with cosmetic rules.

## 16. Extending the system

1. Add the rule to the module tuple; keep conclusion keys distinct from observation keys.
2. Add or reuse an action in `ACTION_LIBRARY` and in a `simulation/*_actions.py` module.
3. Run `python -m pytest`; then `streamlit run app.py` and run SCN-00x.
4. Update `docs/rule_catalogue.md`.
5. Add the new rule to a scenario and to `expected_findings`; the coverage test requires
   every registered rule to fire at least once.

## 17. Limitations

* Monotonic inference: no retraction or non-monotonic reasoning.
* One primary entity per type per investigation; multi-entity correlation is a future
  extension (the activation key already supports it).
* Numeric observations are always considered known; only booleans use Unknown.
* No authentication or multi-user persistence; history is local and ephemeral on Streamlit
  Community Cloud.
* Thresholds are illustrative project assumptions, not audited standards.
