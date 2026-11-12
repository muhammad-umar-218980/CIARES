# CIARES system map

This document is rendered inside the app at **Administration → System map**. It answers two
questions: *what does this file do?* and *what happens if it is deleted?*

---

## 1. One investigation, end to end

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
 selection -> dedup -> containment before recovery -> ordering
        │
        ▼
 ReportWriter           engine/report.py
 threat score, prose diagnosis, approval, response plan
        │
        ▼
 storage/db.py          SQLite record for the administration portal
```

The same pipeline is used by the manual form, the six scenarios and the test suite. There is
no second reasoning path.

---

## 2. File responsibilities

| File | Responsibility |
|---|---|
| `app.py` | Public portal at `/`: sidebar sections, observation form, prose results, approval, plan download |
| `admin.py` | Administration at `/admin`: sign-in gate then six tabs |
| `theme.py` | Poppins, hero, cards, metric row, threat meter, severity chips, footer |
| `passwords.py` | PBKDF2 hashing and constant-time credential checks |
| `config.py` | App metadata, thresholds, approved sources, paths |
| `storage/db.py` | SQLite schema, save/load, aggregates, admin event log |
| `knowledge_base/*.py` | The 60 rules, grouped into five modules |
| `knowledge_base/knowledge_acquisition.py` | Structural validation of the rule catalogue |
| `knowledge_base/rule_registry.py` | Assembles `ALL_RULES` from the five modules |
| `engine/models.py` | Dataclasses: Rule, Condition, Fact, Finding, ResponseAction, Investigation |
| `engine/working_memory.py` | Per-investigation fact store with three-valued logic |
| `engine/inference_engine.py` | Forward chaining to a fixed point |
| `engine/pipeline.py` | End-to-end orchestration; builds findings |
| `engine/decision_engine.py` | Action catalogue, deduplication, deferral, ordering |
| `engine/report.py` | Threat score, prose diagnosis, approval and response plan |
| `engine/explanation_engine.py` | Trace and justification tables for the admin portal |
| `scenarios/` | Six predefined investigation inputs |
| `tests/` | 106 tests covering rules, inference, decisions, scenarios, storage and auth |

---

## 3. What breaks if a module is removed

| Removed | Effect on the running system |
|---|---|
| `knowledge_base/` rules | No rule can fire; the engine reaches a fixed point immediately; 0 findings. The coverage test fails. |
| `engine/working_memory.py` | Rules cannot read conditions; the engine cannot run at all. |
| `engine/inference_engine.py` | Nothing is derived; findings and recommendations are both empty. |
| `engine/pipeline.py` | Each surface would have to wire the engines itself; the portal, scenarios and tests would diverge. |
| `engine/decision_engine.py` | Findings still appear, but no recommendation is produced; Results says the findings are diagnostic. |
| `engine/report.py` | The public portal has no prose, score, approval or plan; only raw records remain. |
| `engine/explanation_engine.py` | Administration still works, but the trace and justification tabs are empty. |
| `knowledge_base/knowledge_acquisition.py` | The validation banner disappears and invalid rules could be registered silently. |
| `storage/db.py` | The audit tab and dashboard are empty; public investigations still work. |
| `theme.py` | The app runs, but loses Poppins, the hero, the cards and the threat meter. |
| `app.py` | No public interface; the engine remains importable and testable. |
| `admin.py` | `/admin` no longer resolves; the public portal is unaffected. |

---

## 4. Three-valued logic

| Value | Meaning |
|---|---|
| `True` | Confirmed by the analyst or derived by a rule |
| `False` | Explicitly observed to be absent |
| `Unknown` | Not provided |

A condition that references an `Unknown` fact evaluates to *undecidable*, and a rule containing
an undecidable condition is not eligible. This is the main protection against inventing
incidents from missing telemetry.

---

## 5. Activation keys and termination

Every firing records a key built from the rule id and the supporting values. The same rule
therefore cannot fire twice on identical evidence, while changed evidence produces a new key.
The loop ends when no rule is eligible — the recorded termination reason is
`fixed point: no further eligible rules`.

---

## 6. Public portal vs administration

| Capability | Public `/` | Admin `/admin` |
|---|---|---|
| Enter observations, run scenarios | ✅ | — |
| Threat meter, findings and reasoning in prose | ✅ | — |
| Approve recommendations, get the response plan | ✅ | — |
| Collapsed evidence table with rule ids | ✅ (closed) | ✅ |
| Browse all 60 rules and conditions | ❌ | ✅ |
| Activation order, justification, working memory | ❌ | ✅ |
| Decision rules, action catalogue | ❌ | ✅ |
| All investigations, exports, admin events | ❌ | ✅ |

The split is a product decision: an analyst needs the diagnosis and the recommendation, not
the engine's internals. The public portal keeps the same information available as a single
collapsed administrative table, so nothing is hidden from an auditor.
