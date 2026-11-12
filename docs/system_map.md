# CIARES system map

This page exists so the internals can be explained on screen, without opening an
editor. It answers two questions: *what does this file do?* and *what happens
if it is deleted?*

---

## 1. One request, end to end

```
 analyst observations
        │
        ▼
 WorkingMemory          engine/working_memory.py
 (True / False / Unknown, with provenance)
        │
        ▼
 InferenceEngine        engine/inference_engine.py
 forward chaining, one rule per cycle, activation keys
        │
        ▼
 build_findings()       engine/pipeline.py
 one conclusion = one finding, severity ranks but never deletes
        │
        ▼
 DecisionEngine         engine/decision_engine.py
 selection → target validation → dedup → containment before recovery → ordering
        │
        ▼
 simulation/            guarded state transitions on a fixed inventory
        │
        ▼
 storage/db.py          SQLite record for the admin portal
```

The same pipeline is used by the public form, the six scenarios and the test
suite. There is no second reasoning path.

---

## 2. File responsibilities

| File | Responsibility |
|---|---|
| `app.py` | Entry point only: page registration, navigation, session bootstrap |
| `ui/nav.py` | Page registry (also used for in-app navigation) |
| `ui/schema.py` | Observation form metadata (fact names, labels, input type) |
| `ui/shared/layout.py` | Theme, headings, metrics, tables, charts |
| `ui/shared/investigation.py` | Single `launch()` entry point; executes approved actions |
| `ui/shared/auth.py` | `/admin` sign-in gate and session state |
| `ui/shared/passwords.py` | PBKDF2 hashing and constant-time credential checks |
| `ui/user/*` | Public pages: home, investigate, scenarios, results |
| `ui/admin/*` | Hidden portal: dashboard, knowledge base, inference, decision, audit, system map |
| `storage/db.py` | SQLite schema, save/load, aggregates, admin event log |
| `knowledge_base/*.py` | The 60 rules, grouped into five modules |
| `knowledge_base/knowledge_acquisition.py` | Structural validation of the rule catalogue |
| `knowledge_base/rule_registry.py` | Assembles `ALL_RULES` from the five modules |
| `engine/models.py` | Dataclasses: Rule, Condition, Fact, Finding, ResponseAction, Investigation |
| `engine/working_memory.py` | Per-investigation fact store with three-valued logic |
| `engine/inference_engine.py` | Forward chaining to a fixed point |
| `engine/pipeline.py` | End-to-end orchestration; builds findings |
| `engine/decision_engine.py` | Action library, target validation, ordering, suppression |
| `engine/explanation_engine.py` | Trace and justification explanations |
| `engine/entities.py` | Default targets taken from the simulated inventory |
| `simulation/` | Action handlers and the guarded simulated environment |
| `scenarios/` | Six predefined investigation inputs |
| `tests/` | 92 behavioural tests plus the new storage/auth/entity tests |

---

## 3. What breaks if a module is removed

| Removed | Effect on the running system |
|---|---|
| `knowledge_base/` rules | No rule can fire; the engine reaches a fixed point immediately; 0 findings. The coverage test fails. |
| `engine/working_memory.py` | Rules cannot read conditions; the engine cannot run at all. |
| `engine/inference_engine.py` | Nothing is derived; findings and actions are both empty. |
| `engine/pipeline.py` | Each page would have to wire the engines itself; the UI, scenarios and tests would diverge. |
| `engine/decision_engine.py` | Findings still appear, but no action is proposed; Results reports “no actionable finding”. |
| `engine/explanation_engine.py` | Execution still works, but “Why this finding?” and the action rationale disappear. |
| `simulation/` | Actions are still marked executable, but execution is rejected because there is no environment to act on. |
| `knowledge_base/knowledge_acquisition.py` | The validation banner disappears and invalid rules could be registered silently. |
| `storage/db.py` | The admin audit and dashboard are empty; public investigations still work. |
| `ui/` | No interface at all; the engines remain importable and testable. |

---

## 4. Three-valued logic

| Value | Meaning |
|---|---|
| `True` | Confirmed by the analyst or derived by a rule |
| `False` | Explicitly observed to be absent |
| `Unknown` | Not provided |

A condition that references an `Unknown` fact evaluates to *undecidable*, and a
rule containing an undecidable condition is not eligible. This is the main
protection against inventing incidents from missing telemetry.

---

## 5. Activation keys and termination

Every firing records a key built from the rule id, the entity identifiers and
the supporting values. The same rule therefore cannot fire twice on identical
evidence, while changed evidence produces a new key. The loop ends when no rule
is eligible — the recorded termination reason is
`fixed point: no further eligible rules`.

---

## 6. Public portal vs admin portal

| Capability | Public | Admin |
|---|---|---|
| Enter observations, run scenarios | ✅ | ✅ |
| See findings, severity chart | ✅ | ✅ |
| Open “Why this finding?” | ✅ | ✅ |
| Approve and execute simulated actions | ✅ | ✅ |
| Browse all 60 rules and conditions | ❌ | ✅ |
| Activation order, justification, working memory | ❌ | ✅ |
| Decision rules, action catalogue, target lab | ❌ | ✅ |
| All investigations, exports, admin events | ❌ | ✅ |

The split is a product decision: an analyst needs the diagnosis and the
recommendation, not the engine's internals.
