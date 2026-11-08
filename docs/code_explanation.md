## 2. Project introduction

CIARES — the **Cybersecurity Incident Analysis and Response Expert System** — is a
Python-based rule-based Expert System. It accepts observations about a security incident,
reasons over a knowledge base of 60 manually authored IF–THEN rules, derives findings,
recommends a response, executes that response against an internal simulated environment,
and explains every conclusion.

The project was built for a Streamlit-only assignment in which the examiner interacts with
the application exclusively through its user interface. Everything described in this
document is therefore visible in the running application: rule counts, conditions,
activations, justifications, working-memory provenance, decisions and before/after state
changes are all generated at runtime from the same engine that the automated tests exercise.

### 2.1 What makes CIARES an Expert System

An Expert System is not a dashboard with security labels. It must contain encoded domain
expertise, a reasoning mechanism, and an explanation facility. CIARES implements the five
components required by the course material:

| Component | CIARES implementation |
|---|---|
| Knowledge Base | 60 IF–THEN rules across five cybersecurity modules |
| Inference Engine | Forward chaining with deterministic conflict resolution |
| Working Memory | Per-investigation facts with three-valued logic and provenance |
| Explanation Facility | Trace explanations and per-rule justification explanations |
| Knowledge Acquisition | Manual curation plus structural validation and registration |
| User Interface | Seven-page Streamlit application |

The system deliberately contains **no trained model, no large language model and no external
reasoning service**. Every conclusion can be traced to a named rule, and every rule can be
traced to declared conditions and an approved source. That constraint is the point of the
project: transparent, auditable reasoning rather than statistical prediction.

### 2.2 How to read this document

Sections 3–5 state the problem, objectives, requirements and scope. Sections 6–15 explain the
architecture and each engine component, with code-level detail. Section 16 lists the complete
folder structure, Section 17 explains each Python file, Section 18 presents the interface
evidence, Section 19 reports testing, Section 20 records deployment status, and Section 21
states limitations and conclusions. The appendices contain the full 60-rule catalogue, the
condition inventory and the scenario matrix.

All screenshots in Section 18 were captured from the running application, not mocked up.

---

## 3. Problem identification

### 3.1 The operational problem

Security operations centres receive more alerts than analysts can investigate manually. The
difficulty is not only volume. Three deeper problems make incident triage hard:

1. **Expertise is tacit.** Experienced analysts combine weak signals — a failed-login count,
   a successful login, an unusual location — into a judgement. That reasoning is rarely
   written down, so it cannot be audited, taught or reproduced consistently.
2. **Evidence is incomplete.** Real investigations always contain missing facts. A system
   that treats "not observed" as "did not happen" produces false conclusions. A system that
   assumes the safest case produces false negatives.
3. **Responses must be justified.** Disabling an account or isolating an endpoint has
   operational cost. A recommendation must identify the finding that justified it, the
   target it applies to and why execution is safe.

Rule-based machine learning does not solve these problems by itself. A classifier may score
an alert, but it typically cannot show which conditions were satisfied, which rule produced a
conclusion, or why a specific response was selected. That opacity is unacceptable in an
incident-response decision.

### 3.2 Problem statement

> There is a need for a transparent Expert System that converts incomplete security
> observations into traceable findings and justified responses, using explicit cybersecurity
> knowledge rather than an opaque model, and that can demonstrate the complete reasoning
> chain through a single user interface.

### 3.3 Why an Expert System is the right tool

Incident triage is a bounded, knowledge-intensive domain. Practitioners already reason with
rules of thumb ("repeated failures followed by a success are suspicious"). Those rules can be
elicited, written as IF–THEN implications, validated and executed. When the rule set is
explicit, the system can explain itself by construction, and a domain expert can correct a
rule without retraining a model.

CIARES therefore treats the problem as **symbolic knowledge representation and forward
inference**, not as classification.

---

## 4. Project objectives

| # | Objective | How CIARES achieves it | Evidence |
|---|---|---|---|
| O1 | Build a genuine rule-based Expert System in Python | Declarative `Rule` and `Condition` objects executed by a forward-chaining engine | Sections 7, 11; Figures 2–3 |
| O2 | Provide at least 60 rules | 12 rules in each of five modules | {{RULE_COUNT}} rules; Appendix A |
| O3 | Provide at least 50 logical conditions | Conditions are counted from rule objects, not from rule IDs | {{CONDITION_COUNT}} conditions across {{FACT_FIELD_COUNT}} fact fields; Appendix B |
| O4 | Cover five cybersecurity modules | AUTH, MAL, NET, DATA and POL | Section 8; Figure 2 |
| O5 | Reason with incomplete information | Three-valued logic: True, False, Unknown | Section 10; Figure 16 |
| O6 | Derive findings and recommend responses | Separate diagnosis and decision stages | Sections 11–12; Figures 9–10 |
| O7 | Execute responses safely | Fixed simulated inventory, target and state validation | Section 13; Figures 11, 17–18 |
| O8 | Explain conclusions and actions | Trace explanation and condition-level justification | Section 14; Figures 7–8 |
| O9 | Validate knowledge on entry | Knowledge Acquisition module with structural checks | Section 15; Figure 2 |
| O10 | Verify behaviour automatically | 92 pytest tests, including a coverage guard | Section 19 |
| O11 | Deliver a Streamlit-only interface | Seven pages, no other frontend | Section 18 |

The objectives are deliberately measurable. Each one maps to a screen or a test result, which
is what makes the project demonstrable in a viva.

---

## 5. Project requirements and scope

### 5.1 Assignment requirements mapped to implementation

| Requirement | CIARES implementation | Where the examiner can verify it |
|---|---|---|
| Streamlit-only UI | All seven pages are Streamlit functions | Every screenshot |
| Python rule engine | `engine/` package; no external inference service | Section 6 |
| Minimum 60 rules | Exactly 60 registered rules | Knowledge Base metrics; Appendix A |
| Minimum 50 conditions | {{CONDITION_COUNT}} logical conditions | Knowledge Base metrics; Appendix B |
| Five cybersecurity modules | AUTH, MAL, NET, DATA, POL | Knowledge Base tabs |
| Working memory | Per-investigation fact store with provenance | Inference Trace → Working memory |
| Forward chaining | One-rule-per-cycle inference to a fixed point | Inference Trace → Activation sequence |
| Explanation facility | Trace and justification explanations | Inference Trace → Justification |
| Decision and response | Action selection, validation, ordering | Response Center |
| Simulated execution | Before/after state changes in a simulated environment | Response Center → Execute |
| Knowledge acquisition | Validation and registration of rules | Knowledge Base validation banner |
| History | Session history mirrored to JSON | Investigation History |
| Testing | 92 automated tests | Section 19 |
| PDF explanation | This document | — |
| Live URL | Recorded in Section 20 | — |

### 5.2 Functional scope

**In scope**

- Manual observation entry with numeric, text and tri-state boolean fields.
- Six predefined scenarios that supply observations and entity identifiers only.
- Forward-chaining inference over the complete rule set.
- Finding construction with severity and supporting rule identifiers.
- Response recommendation with phase, priority, target, executability and reason.
- Simulated execution of 15 response actions across 8 entity types.
- Trace, justification, working-memory and action explanations.
- Session history with JSON export and a JSON mirror on disk.
- Knowledge-base validation and a machine-generated condition inventory.

**Out of scope**

- Real integration with operating systems, directories, firewalls or endpoint tools.
- Authentication, multi-tenancy or role-based access control.
- Model training, anomaly detection or natural-language processing.
- Automatic rule learning or rule mining.
- Concurrent multi-incident correlation within a single investigation.
- Production-grade persistence (the JSON mirror is single-user and best effort).

### 5.3 Assumptions

Numeric cut-offs are **CIARES project assumptions**, not universal cybersecurity standards.
They are grouped in `config.py` so that they can be inspected and changed, and they are
identified as assumptions wherever they appear in the application and in this document.

{{THRESHOLD_TABLE}}

The working-day assumption is 08:00–18:00. Sources are restricted to an approved list:
NIST SP 800-61 Rev. 3, NIST Cybersecurity Framework 2.0, MITRE ATT&CK, CISA Guidance and
CIARES Project Assumption.

---

## 6. Expert System architecture

### 6.1 Layered design

CIARES is organised into strict layers. The user interface never contains rule logic, and the
knowledge base never contains execution logic.

```
┌──────────────────────────────────────────────────────────────────┐
│ app.py — seven Streamlit pages                                   │
│ Overview · New Investigation · Scenarios · Knowledge Base        │
│ Inference Trace · Response Center · History                      │
└───────────────────────────────┬──────────────────────────────────┘
                                │ run_investigation()
┌───────────────────────────────▼──────────────────────────────────┐
│ engine/pipeline.py — the single investigation pipeline           │
│ observations → working memory → inference → findings → decision  │
└───┬───────────────┬────────────────┬─────────────────────────────┘
    │               │                │
┌───▼─────────┐ ┌───▼──────────┐ ┌───▼──────────────┐ ┌────────────┐
│ working_    │ │ inference_   │ │ decision_engine  │ │ simulation │
│ memory      │ │ engine       │ │ action library   │ │ environment│
│ facts +     │ │ forward      │ │ target + state   │ │ 15 action  │
│ provenance  │ │ chaining     │ │ validation       │ │ handlers   │
└─────────────┘ └───┬──────────┘ └──────────────────┘ └─────┬──────┘
                    │                                      │
             ┌──────▼────────┐                    ┌────────▼────────┐
             │ knowledge_base│                    │ explanation_    │
             │ 60 rules      │                    │ engine          │
             └───────────────┘                    └─────────────────┘
```

### 6.2 Responsibilities

| Layer | Responsibility | Must not do |
|---|---|---|
| `app.py` | Collect input, call the pipeline, render results | Contain rule logic or mutate simulated state directly |
| `engine/pipeline.py` | Orchestrate one investigation end to end | Re-implement inference or decision rules |
| `engine/working_memory.py` | Store facts, provenance, contradictions, trace | Decide which rule fires |
| `engine/inference_engine.py` | Evaluate rules and fire them to a fixed point | Invent facts or skip conditions |
| `engine/decision_engine.py` | Turn findings into validated, ordered actions | Change simulated state |
| `knowledge_base/` | Define and validate cybersecurity knowledge | Know about Streamlit or simulation |
| `simulation/` | Apply validated state transitions | Decide whether an action is appropriate |
| `engine/explanation_engine.py` | Read records and explain them | Re-run inference |

### 6.3 The single pipeline

`engine/pipeline.py::run_investigation()` is the only entry point used by manual
investigations, scenario runs and tests. This is an architectural safeguard: there is no
second code path in which a scenario could be hardcoded to produce a particular answer.

The pipeline performs six steps:

1. Create an `Investigation` record and a `WorkingMemory` populated with observations.
2. Run `InferenceEngine` to a fixed point, recording every activation.
3. Convert activations into findings with `build_findings()`.
4. Create a fresh `SimulatedEnvironment` (fixed inventory).
5. Ask `DecisionEngine` to recommend and validate response actions.
6. Attach activations, findings, actions, trace, termination reason and environment to the
   investigation record.

Because the environment is created per investigation, executing an action in one scenario
cannot contaminate another scenario. Because the environment is seeded with a fixed
inventory, a target such as `USER-999` is rejected rather than silently created.

### 6.4 Design constraints

Four constraints drove most implementation decisions:

1. **No hidden reasoning.** A conclusion that cannot be derived from a rule is not produced.
2. **Unknown is not False.** Missing evidence must never satisfy a positive condition.
3. **One reasoning path.** UI, scenarios and tests use the same pipeline.
4. **Simulation only.** No real system is contacted, and the UI says so on every relevant page.

---

## 7. Knowledge Base

### 7.1 Representation

The knowledge base is a collection of immutable `Rule` objects. Each rule contains declarative
metadata and a tuple of `Condition` objects:

```python
Rule(
    id="AUTH-01",
    name="Repeated Authentication Failure Detection",
    module="Authentication & Account Security",
    description="A sustained series of failed logins indicates credential guessing.",
    conditions=(
        Condition("failed_login_attempts", ">=", THRESHOLDS["failed_login_attempts"],
                  "failed login attempts are at or above the configured threshold"),
    ),
    conclusion_key="repeated_authentication_failures",
    conclusion_label="Repeated authentication failures",
    severity=Severity.HIGH,
    source="MITRE ATT&CK",
)
```

A condition is a triple `(field, operator, value)` plus an optional human label. It is **data,
not a lambda**, for three reasons:

- it can be printed exactly as authored;
- it can be validated structurally;
- it can be evaluated with three-valued logic and recorded in an explanation.

Supported operators are `==`, `!=`, `>`, `>=`, `<`, `<=`, `in` and `not in`.

### 7.2 Rules versus conditions

The assignment distinguishes rules from logical conditions. CIARES makes the distinction
explicit:

- a **rule** is one IF–THEN implication;
- a **condition** is one comparison inside the IF part.

A three-condition rule therefore counts as one rule and three conditions. The Knowledge Base
page computes both numbers from the rule objects, which prevents the condition count from
drifting away from the code.

Current totals:

| Metric | Value |
|---|---|
| Rules | {{RULE_COUNT}} |
| Logical conditions | {{CONDITION_COUNT}} |
| Distinct fact fields referenced by conditions | {{FACT_FIELD_COUNT}} |
| Modules | {{MODULE_COUNT}} |
| Actionable rules | {{ACTIONABLE_COUNT}} |

### 7.3 Module distribution

{{MODULE_TABLE}}

Each module contains exactly 12 rules. The condition count varies because some rules
corroborate several indicators while others test a single fact.

### 7.4 Severity distribution

{{SEVERITY_TABLE}}

Severity is a property of a finding, not a filter. A Critical finding never suppresses a High
finding; both remain visible and both are counted on the Security Overview.

### 7.5 Authoring principles

1. **One conclusion per rule.** A rule may not derive two facts. This keeps justification
   unambiguous.
2. **Conclusions are snake_case fact keys.** They can be referenced by later rules, which is
   how chaining works.
3. **No self-supporting rules.** A rule's conclusion may not also be one of its conditions.
   The Knowledge Acquisition module rejects this.
4. **Actionable rules declare phase and entity type.** Diagnostic rules deliberately carry no
   action.
5. **Approved sources only.** A rule must cite one of the approved references.
6. **Thresholds live in `config.py`.** The knowledge base contains no unexplained magic
   numbers.
7. **Distinct, meaningful conclusions.** Rules are not padding; the coverage test requires
   every rule to fire in at least one shipped scenario.

---

## 8. Five knowledge modules

The knowledge base is divided into five specialised modules, each with 12 rules. The
division mirrors how security teams separate identity, endpoint, network, data and policy
concerns.

### 8.1 Authentication & Account Security (AUTH-01 … AUTH-12)

Investigates credential attacks, suspicious login sequences and session misuse. Key facts
include failed login attempts, successful login after failures, unusual location, disabled
account access, administrator privilege, concurrent sessions, MFA failures, password changes,
impossible travel and active session state.

Representative rules:

- **AUTH-01** derives repeated authentication failures when the failure count reaches the
  configured threshold.
- **AUTH-04** combines three independent indicators into a possible account compromise.
- **AUTH-05** detects an attempt to authenticate to a disabled account.
- **AUTH-10** detects impossible travel.
- **AUTH-12** recognises a suspicious active session.

### 8.2 Malware & Process Security (MAL-01 … MAL-12)

Investigates suspicious executables, process behaviour, persistence and log tampering. Facts
include unapproved paths, approved-list membership, unauthorized operations, protected-file
modification, digital signatures, shell spawning, persistence entries, cleared logs, known
hashes and temporary-directory placement.

Representative rules:

- **MAL-01** detects execution from an unapproved directory.
- **MAL-02** fires only when a process is *explicitly* not on the approved list — an Unknown
  value cannot satisfy it.
- **MAL-07** detects shell spawning by an untrusted process.
- **MAL-08** detects persistence mechanisms.
- **MAL-12** escalates active intrusion with concealment.

### 8.3 Network Security (NET-01 … NET-12)

Investigates connections, destinations, ports, traffic volume, beaconing and remote access.
Facts include destination authorization, port approval, remote-access authorization,
inbound connections, beaconing intervals, listening services, outbound volume, connection
attempts and denied requests.

Representative rules:

- **NET-01** detects access to an unauthorized destination.
- **NET-02** detects unusual outbound volume.
- **NET-07** detects command-and-control beaconing.
- **NET-10** detects an unexpected listening service.
- **NET-12** escalates an active network compromise.

### 8.4 Data Security & Protection (DATA-01 … DATA-12)

Investigates data movement, unauthorized access, external sharing, after-hours access,
unapproved modification and deletion. Facts include transfer volume, download count,
destination authorization, restricted-file access, external sharing, access hours,
unapproved modification and protected-data deletion.

Representative rules:

- **DATA-01** detects an unusual data transfer.
- **DATA-03** detects unauthorized access to restricted files.
- **DATA-04** combines transfer volume and destination authorization into possible
  exfiltration.
- **DATA-11** chains unusual transfer and unauthorized destination into a two-stage
  exfiltration finding.
- **DATA-12** escalates confirmed data exfiltration.

### 8.5 Privilege & Security Policy (POL-01 … POL-12)

Investigates privilege escalation, unauthorized administrative operations, control tampering,
separation-of-duties violations and coordinated attacks. Facts include privilege escalation,
administrator grants, approval state, disabled controls, unauthorized admin operations,
unapproved configuration changes, self-approval, dormant privileged accounts and restricted
resource access.

Representative rules:

- **POL-01** detects privilege escalation.
- **POL-02** detects an unauthorized privilege assignment.
- **POL-05** detects a security-policy violation.
- **POL-10** detects active control tampering.
- **POL-12** is a cross-module rule: its condition `possible_account_compromise` is the
  conclusion of AUTH-04.

### 8.6 Cross-module chaining

Modules are not isolated. A conclusion derived in AUTH becomes a fact that a POL rule can
use. SCN-005 demonstrates this explicitly: AUTH-01 through AUTH-04 derive a possible account
compromise, and POL-12 then combines that fact with privilege escalation to conclude a
coordinated privilege compromise. This is the strongest evidence that the rules form a
knowledge base rather than five unrelated lists.

---

## 9. IF–THEN rule examples and condition inventory

### 9.1 Example 1 — a simple threshold rule (AUTH-01)

```
IF  failed_login_attempts >= 10
THEN repeated_authentication_failures = True
Severity: High
```

The threshold is a CIARES project assumption. It is read from `config.THRESHOLDS`, so changing
the configuration changes the rule's behaviour without editing the rule. A count of 3 does not
satisfy the condition, and the application reports that no rule fired (Figure 16).

### 9.2 Example 2 — evidence combination (AUTH-04)

```
IF  repeated_authentication_failures = True
AND suspicious_login_sequence = True
AND unusual_location_login = True
THEN possible_account_compromise = True
Severity: Critical
Response: disable_account
```

AUTH-04 is the clearest demonstration of AND logic. One indicator alone is insufficient: the
rule fires only when three independently derived facts corroborate each other. This is
evidence combination, not a list of alerts. Its conclusion is then available to POL-12.

### 9.3 Example 3 — the meaning of False (MAL-02)

```
IF  process_on_approved_list == False
THEN unapproved_process = True
Severity: High
```

MAL-02 fires only on an explicit `False`. If the fact is `Unknown`, the condition cannot be
evaluated and the rule is ineligible. That is the operational difference between "the process
is not approved" and "nobody checked whether the process is approved". A system that confused
the two would generate false incidents from missing data.

### 9.4 Example 4 — cross-module reasoning (POL-12)

```
IF  privilege_escalation_detected = True
AND possible_account_compromise = True
THEN coordinated_privilege_compromise = True
Severity: Critical
```

The second condition is the conclusion of AUTH-04. POL-12 therefore cannot fire until the
authentication module has completed its own reasoning. This is forward chaining across module
boundaries.

### 9.5 Condition inventory

The inventory is machine-generated by `validate_catalogue()`. For every condition field it
records how many conditions reference the field and how many distinct rules use it. The full
80-row inventory appears in Appendix B; the application renders the same table at the bottom
of the Knowledge Base page (Figure 5).

The top of the inventory shows the most reused facts. For example,
`possible_account_compromise` is referenced by two conditions in two rules, which is exactly
what cross-module chaining requires.

### 9.6 Full catalogue

Appendix A lists all 60 rules with their IF conditions, conclusions, severity, recommended
response and source. The catalogue is generated from the registered objects, so it cannot
disagree with the running system. The Knowledge Base page renders the same data live
(Figure 2).

---

## 10. Working Memory

### 10.1 Definition

Working memory is the set of facts that are true of **this investigation**. It is created
afresh for every run and discarded when the investigation ends. The knowledge base is general
and permanent; working memory is particular and temporary.

### 10.2 Three-valued logic

| State | Storage | Meaning | Example |
|---|---|---|---|
| True | `Fact(value=True)` | Confirmed observation or derived conclusion | Unusual location detected |
| False | `Fact(value=False)` | Explicitly observed as absent | Process is not on the approved list |
| Unknown | key absent or `Fact(value=None)` | Not established | Login location not provided |

`Condition.evaluate(observed, known)` returns `(True | False | None, note)`. A rule is eligible
only if **every** condition returns `True`. A single `None` or `False` makes the rule
ineligible. This is the core defence against inventing incidents from missing evidence.

The Boolean fields in the UI default to **Unknown**, while numeric fields default to 0 and are
treated as known. That asymmetry is deliberate: a zero count is a measurement; an unanswered
Boolean is not.

### 10.3 Fact structure and provenance

Every fact records where it came from:

```python
Fact(
    key="possible_account_compromise",
    value=True,
    source="AUTH-04",
    derived=True,
    rule_id="AUTH-04",
    supporting=(
        ("repeated_authentication_failures", True),
        ("suspicious_login_sequence", True),
        ("unusual_location_login", True),
    ),
)
```

Provenance is what makes the Explanation Facility possible. The working-memory page shows
each derived fact, the rule that derived it and the supporting facts (Figure 9).

### 10.4 Contradiction handling

A fact is never silently overwritten. Working memory raises `ContradictionError` when:

- an observation tries to overwrite a derived fact;
- two observations assert different values for the same fact;
- a rule derives a value different from an established value.

Rejecting contradictions is safer than last-write-wins. It makes inconsistent evidence visible
instead of hiding it.

### 10.5 Trace

Working memory also records the reasoning log: observations, start, each activation, diagnosis,
decision and finish. The trace is the raw material for the trace explanation and for the
Markdown investigation report.

### 10.6 SCN-001 working memory

{{SCN001_MEMORY}}

---

## 11. Forward-Chaining Inference Engine

### 11.1 Why forward chaining

Incident analysis is evidence-first: the analyst starts with observations and asks what they
imply. Forward chaining matches that direction. Backward chaining would start from a
hypothesis ("the account is compromised") and search for support, which is less suitable when
the incident type is unknown and multiple conclusions may coexist.

### 11.2 Algorithm

The engine uses a **one-rule-per-cycle** loop:

```
fired = {}
while cycles < max_cycles:
    eligible = []
    for rule in rules:
        evaluations = evaluate(rule, memory)
        if not all_satisfied(evaluations): continue
        key = activation_key(rule, entities, evaluations)
        if key in fired: continue
        eligible.append((rule, evaluations, key))

    if eligible is empty:
        terminated_reason = "fixed point"
        break

    sort eligible by (severity desc, priority asc, rule id)
    rule, evaluations, key = eligible[0]
    memory.infer(rule.conclusion, True, rule, support)
    fired.add(key)
    record_activation(...)
```

Three decisions matter:

1. **Fire one rule, then re-evaluate.** Firing every eligible rule in one batch is faster but
   records an order that did not actually drive the reasoning. CIARES prioritises a truthful
   trace.
2. **Deterministic conflict resolution.** Highest severity, then author priority, then rule
   ID. Ties never depend on dictionary iteration order.
3. **Explicit termination.** If no eligible activation remains, the engine reports a fixed
   point. A cycle cap (`max(100, 5 × rule count)`) is a safety guard, not the normal exit.

### 11.3 Activation tracking

An activation key is:

```
rule_id :: sorted(entity_id=value) :: condition_field=observed_value
```

This prevents the same rule from firing repeatedly on identical evidence. It also allows the
same rule to fire once per entity set, which is the foundation for future multi-account
analysis. If a supporting value changes, the key changes and the rule may legitimately fire
again.

### 11.4 Termination

Working memory is monotonic: facts are added, never retracted. The set of derivable facts is
finite, and each activation key can fire at most once. The loop therefore reaches a fixed
point. In all six shipped scenarios the reported reason is
`fixed point: no further eligible rules`.

### 11.5 SCN-001 trace

{{SCN001_TRACE}}

The order is the real reasoning order, recorded as the engine ran. AUTH-04 could not fire until
AUTH-01, AUTH-02 and AUTH-03 had inserted their conclusions into working memory.

### 11.6 Complexity and scale

With 60 rules and a bounded number of facts, the engine is trivially fast in practice. Each
cycle evaluates at most 60 rules, and the number of cycles is bounded by the number of
distinct activations. The design favours explainability and determinism over asymptotic
cleverness. That is appropriate for an Expert System whose rule base is authored by humans.

---

## 12. Decision and Response Engine

### 12.1 Diagnosis versus decision

The inference engine answers **"what is happening?"**; the decision engine answers **"what
should we do about it?"**. They are separate for a reason: a diagnostic rule can report a
problem without inventing a response, and an actionable rule can recommend a response only
when it has produced a finding.

A `Finding` is a diagnosis with severity, module, supporting rule IDs and an optional
recommended action. A `ResponseAction` is a concrete instruction with phase, priority, target
type, target ID, executability, status and reason.

### 12.2 Action library

{{ACTION_TABLE}}

Fifteen action keys are declared once and shared by the rules, the decision engine and the
simulation dispatcher. A test asserts that the decision library and the implemented handlers
are exactly the same set, so a rule cannot recommend an action that has no simulator.

### 12.3 Decision procedure

1. Keep only findings that carry a `recommended_action`.
2. Sort by severity, then derivation order.
3. Resolve the target from the investigation's entity map (`account_id`, `session_id`, …).
4. Validate the target:
    - an identifier must be present;
    - the entity must exist in the simulated environment;
    - the entity must be in a state where the action makes sense.
5. Collapse duplicate `(action, target)` pairs into one action, merging the reasons.
6. Suppress recovery actions when containment already applies to the same target.
7. Sort by phase (Containment → Eradication → Recovery → Escalation), then priority, then
   action key; assign `ACT-001`-style identifiers.

Validation failures do not hide the action. The action is shown with `Executable: No` and a
human-readable `Blocked reason`, which is both safer and more informative than dropping it.

### 12.4 Target validation example

SCN-001 with `account_id = USER-101` produces one executable containment action: disable the
account. The same reasoning with `account_id = USER-999` produces exactly the same finding,
but the action is blocked because `USER-999` does not exist in the simulated inventory
(Figures 17–18). The difference proves that the decision layer validates rather than
hardcodes.

### 12.5 Conflict handling

Two kinds of conflict are handled explicitly:

- **Inference conflicts.** Multiple rules may derive different findings from the same
  evidence. All findings are kept; severity orders presentation but never deletes a finding.
- **Response conflicts.** If a containment action targets an entity, a recovery action on the
  same entity is marked `Skipped` with a reason. Restoring access while containment is in
  effect would be contradictory. SCN-005 demonstrates this: 3 actions are proposed, 2 are
  executable, and 1 recovery action is skipped.

### 12.6 SCN-001 findings and actions

{{SCN001_FINDINGS}}

The response is deliberately modest: one finding is actionable and one action is proposed.
The other three findings are diagnostic. The system reports the full diagnosis without
inventing a response for every line.

---

## 13. Simulated Environment

### 13.1 Purpose

CIARES must demonstrate response execution without touching a real account, process, host or
network. The simulation layer provides a small in-memory world whose state can be changed and
inspected.

### 13.2 Entities and states

| Entity type | Default state | States used by actions |
|---|---|---|
| account | Active | Active, Disabled, Locked |
| account.permissions | Approved | Approved, Revoked, Elevated |
| account.data_access | Unrestricted | Unrestricted, Restricted |
| session | Active | Active, Revoked |
| process | Running | Running, Isolated, Terminated |
| file | Present | Present, Quarantined |
| transfer | Active | Active, Restricted |
| destination | Reachable | Reachable, Blocked |
| endpoint | Online | Online, Isolated |
| connection | Open | Open, Restricted |

The seeded inventory contains two accounts (`USER-101`, `USER-202`), two sessions
(`SESSION-204`, `SESSION-311`) and one each of process, file, transfer, destination, endpoint
and connection. This is enough to demonstrate every action while keeping the world
understandable.

### 13.3 Guarded transitions

`SimulatedEnvironment.transition()` accepts an `allowed_from` set. A transition is rejected if
the entity does not exist, if no target was supplied, or if the current state is not in
`allowed_from`. Rejections return a reason instead of raising, so the UI can display exactly
why an action failed.

Examples:

- disabling an already disabled account is rejected;
- terminating a process that is not Running or Isolated is rejected;
- acting on `USER-999` is rejected because the entity does not exist.

### 13.4 Execution dispatch

`simulation.execute(environment, action)` is the only execution entry point. It:

1. looks up the handler for the action key;
2. refuses to run if the decision engine marked the action non-executable;
3. calls the handler, which performs a guarded transition;
4. stores an `ExecutionResult` on the action and sets its status to `Executed` or `Rejected`.

The decision engine never mutates state, and the simulation layer never decides whether an
action is appropriate. Each layer has one job.

### 13.5 A deliberate design fix

An earlier implementation provisioned entities named in an investigation on demand. That made
`USER-999` executable: the act of naming it created it. The pipeline now uses only the fixed
inventory. A regression test asserts that an unknown target is blocked at the pipeline level,
not merely at the UI level. This is a good example of a safety property that emerged from
testing rather than from the original design.

---

## 14. Explanation Facility

### 14.1 Two explanations

The Explanation Facility produces the two explanation types used in the course material:

- a **trace explanation** — what fired, in what order, and what it concluded;
- a **justification explanation** — for one activation, every condition with its expected
  value, observed value and satisfaction status.

It also explains actions: why the action was selected, whether the target check passed, what
happened on execution and the before/after state.

### 14.2 Reading records, not re-reasoning

`ExplanationEngine` never re-runs inference. It reads the activation records, condition
evaluations, trace entries and execution results that the engine already produced. That is
important: an explanation generated by a second reasoning pass could disagree with the first.
Here the explanation is a view of the same evidence.

### 14.3 Trace output

The trace includes:

- the ordered activation table;
- the reasoning log with observation, start, activation, diagnosis, decision and finish
  events;
- the termination reason.

### 14.4 Justification output

{{SCN001_JUSTIFICATION}}

Each condition shows the field, operator, expected value, observed value and status. The
closing statement explains that all conditions were satisfied and the conclusion was inserted
into working memory.

### 14.5 Export

The same records generate a Markdown investigation report containing observations, findings,
the activation trace, actions and limitations. This makes the explanation portable and
suitable for a report appendix.

---

## 15. Knowledge Acquisition

### 15.1 Manual, curated knowledge

CIARES does not learn from data. Knowledge is elicited from approved cybersecurity references,
written as explicit rules and validated before registration. This is a deliberate choice:
manual curation keeps every rule inspectable and keeps the system's behaviour attributable.

### 15.2 Validation checks

`validate_rule()` enforces:

| Check | Failure mode |
|---|---|
| ID matches `(AUTH|MAL|NET|DATA|POL)-NN` | error |
| ID is unique in the catalogue | error |
| Name and description present | error |
| At least one condition | error |
| Conclusion present and not one of its own conditions | error |
| Severity is a `Severity` value | error |
| Source is approved | error |
| Actionable rule has a snake_case action key | error |
| Actionable rule declares a phase and a valid entity type | error |

`validate_catalogue()` additionally counts rules, conditions and distinct fact fields, builds
the condition inventory, and emits warnings if a future edit drops below 60 rules or 50
conditions. `KnowledgeAcquisition.register()` refuses invalid rules outright.

### 15.3 Where validation is visible

The Knowledge Base page runs validation on every render. A green banner reports that the
catalogue is valid; a red banner would list every error. The sidebar repeats the rule and
condition counts, so a broken catalogue is visible from every page.

### 15.4 Adding a rule

The documented extension procedure is:

1. add the rule to the relevant module tuple;
2. reuse or add an action in `ACTION_LIBRARY` and a handler in `simulation/`;
3. run `python -m pytest`;
4. add the rule to a scenario so the coverage test can prove it is reachable;
5. update `docs/rule_catalogue.md`.

The coverage requirement is intentional: a rule that can never fire is not knowledge, it is
decoration.

### 15.5 Sources

Each rule cites one approved source. The source is displayed in the Knowledge Base and in the
justification, so a reader can see whether a rule is grounded in NIST guidance, MITRE ATT&CK,
CISA guidance or an explicit project assumption. Numeric thresholds are always identified as
assumptions, never as standards.

---

## 16. Complete folder structure

{{FILE_TREE}}

The project separates knowledge, reasoning, simulation, presentation, tests and documentation.
That separation is what allows the same engine to be used by the UI, the scenarios and the
test suite.

### 16.1 File inventory

{{FILE_TABLE}}

---

## 17. Explanation of each Python file

### 17.1 Root-level files

**`app.py`** — the Streamlit entry point. It configures the page, injects the CSS theme,
renders the sidebar and dispatches to seven page functions: `page_overview`,
`page_new_investigation`, `page_scenarios`, `page_knowledge_base`, `page_trace`,
`page_response_center` and `page_history`. It owns session state (active investigation,
history list) and calls the pipeline. It contains no rule logic.

**`config.py`** — central configuration. Contains the application identity, data paths,
threshold assumptions, approved sources and the working-day assumption. Keeping thresholds
here is what allows the report to say honestly that they are configurable project assumptions.

**`requirements.txt`** — runtime dependencies: Streamlit, pandas and pytest. Documentation
build dependencies are intentionally not part of the application requirements.

### 17.2 `engine/`

**`models.py`** — pure data structures: `Severity`, `Phase`, `Condition`, `Rule`, `Fact`,
`ConditionEvaluation`, `RuleActivation`, `Finding`, `ResponseAction`, `ExecutionResult` and
`Investigation`. It also implements three-valued condition evaluation and boolean-safe
equality (so `True` does not equal `1`). No business logic lives here.

**`working_memory.py`** — per-investigation fact store. Adds observations, inserts derived
facts with provenance, rejects contradictions, records the trace and exposes observations,
derived facts and provenance queries.

**`inference_engine.py`** — the forward-chaining loop. Evaluates every rule, computes
activation keys, sorts eligible rules deterministically, fires one rule per cycle, inserts its
conclusion and repeats to a fixed point.

**`decision_engine.py`** — the action library and decision procedure. Resolves targets,
validates existence and state, deduplicates actions, suppresses recovery after containment,
orders actions by phase and priority and assigns action identifiers.

**`pipeline.py`** — the single investigation pipeline. Builds findings from activations,
creates the simulated environment, invokes the decision engine and assembles the
`Investigation` record. Also contains severity aggregation for the dashboard.

**`explanation_engine.py`** — converts records into trace rows, justification tables, action
explanations and a Markdown report. It never re-reasons.

### 17.3 `knowledge_base/`

**`authentication.py`** — AUTH-01 to AUTH-12. Twelve rules covering failures, suspicious
sequences, locations, disabled accounts, off-hours admin logins, concurrent sessions,
password changes, MFA brute force, impossible travel, confirmed compromise and suspicious
sessions.

**`malware.py`** — MAL-01 to MAL-12. Twelve rules covering unapproved paths, approved-list
membership, unauthorized operations, protected files, signatures, shell spawning,
persistence, log tampering, unknown hashes, temporary directories and coordinated malware
activity.

**`network.py`** — NET-01 to NET-12. Twelve rules covering unauthorized destinations, traffic
volume, ports, repeated connections, remote access, inbound connections, beaconing, denied
requests, listening services, data transfer and active compromise.

**`data_security.py`** — DATA-01 to DATA-12. Twelve rules covering transfer volume, downloads,
destination authorization, restricted files, external sharing, after-hours access,
modification, deletion, bulk access, exfiltration and integrity violations.

**`security_policy.py`** — POL-01 to POL-12. Twelve rules covering privilege escalation,
unauthorized assignment, control changes, suspicious privileged activity, policy violations,
unauthorized admin operations, configuration changes, separation of duties, dormant
privileged accounts, control tampering, insider threat and coordinated compromise.

**`rule_registry.py`** — concatenates the five module tuples into `ALL_RULES`, exposes
`RULES_BY_MODULE`, `MODULES` and `module_summary()`. The inference engine imports `ALL_RULES`
rather than importing each module separately.

**`knowledge_acquisition.py`** — validation and registration. Checks structure, uniqueness,
severity, source, conclusion and action consistency; counts conditions and distinct fact
fields; builds the condition inventory.

### 17.4 `simulation/`

**`environment.py`** — the simulated world. Declares entity types, default states and the
seeded inventory; implements existence checks, snapshots and guarded state transitions;
provides `apply_change()` for action modules.

**`account_actions.py`** — disable, lock, restore, revoke session and permission recovery
handlers.

**`network_actions.py`** — restrict connection, block destination and isolate endpoint
handlers.

**`process_actions.py`** — isolate process, terminate process and quarantine file handlers.

**`data_policy_actions.py`** — restrict transfer, data-access restriction and permission
revocation handlers.

**`__init__.py`** — aggregates all handlers into `ALL_ACTIONS`, exposes `available_actions()`
and implements `execute()`, including refusal of non-executable actions.

### 17.5 `scenarios/`

**`sample_scenarios.py`** — six scenario definitions. Each supplies observations, entity IDs
and expected finding keys for verification. No scenario supplies a diagnosis or a response.

### 17.6 `tests/`

**`conftest.py`** — adds the project root to `sys.path` so tests run without installation.

**`test_rules.py`** — 17 tests: threshold behaviour, Unknown versus False, corroboration,
condition semantics, catalogue integrity.

**`test_inference.py`** — 10 tests: chaining order, fixed point, no re-fire, activation keys,
provenance, contradiction handling.

**`test_decisions.py`** — 11 tests: target validation, state validation, duplicates,
containment/recovery conflict, ordering, action-library consistency.

**`test_simulation.py`** — 11 tests: successful transitions, rejected transitions, missing
targets, blocked actions, snapshots.

**`test_scenarios.py`** — 30 tests: six end-to-end scenarios, JSON-serialisable records, no
preloaded diagnoses, missing-evidence behaviour.

**`test_coverage.py`** — 13 tests: exactly 60 rules and 12 per module, at least 50 conditions,
every rule reachable, every actionable rule produces a response, every executable action
succeeds, phase ordering, explanation completeness.

### 17.7 Documentation and scripts

`README.md` explains installation, architecture and usage. `docs/rule_catalogue.md` documents
all 60 rules. `docs/rule_sources.md` maps rules to references. `docs/technical_design.md`
explains the implementation. `docs/demo_guide.md` is the UI-only viva script.
`docs/screenshots/` stores the evidence images. `scripts/build_pdf.py` and
`scripts/print_pdf.cjs` reproduce this document, and `scripts/capture_screenshots.mjs`
captures the interface evidence.

---

## 18. Streamlit interface screenshots

All screenshots were captured from the running application at 1500 × 1050. They show the
actual computed values, not illustrative mock-ups. Each caption identifies what the examiner
should notice.

{{FIGURES}}

The sequence tells a complete story: the dashboard, the knowledge base, the rule details, the
scenario run, the reasoning trace, the justification, working memory, the proposed response,
the executed state change, cross-module inference, history, manual entry and the three edge
cases.

---

## 19. Testing and results

### 19.1 Strategy

The test suite verifies both components and behaviour. Rule tests check individual
conditions; engine tests check chaining and termination; decision tests check safety;
simulation tests check state transitions; scenario tests check complete investigations; and
the coverage test prevents the knowledge base from being padded with unreachable rules.

{{TEST_FILE_TABLE}}

### 19.2 Coverage guards

`test_coverage.py` enforces the assignment's quantitative claims:

- exactly 60 rules and exactly 12 per module;
- at least 50 logical conditions;
- every registered rule fires in at least one shipped scenario;
- every actionable rule produces a response action;
- every executable action succeeds against the simulated environment;
- actions are ordered by response phase;
- every activation has a complete justification.

This is the answer to the obvious examiner question: "How do you know the 60 rules are real
and not padding?" If a rule cannot fire, the test suite fails. All 60 are currently reachable.

### 19.3 Results

{{PYTEST_OUTPUT}}

The suite currently reports **{{TEST_COUNT}} passed, 0 failed, 0 skipped**. The tests run in
under two seconds, which makes them usable as a pre-demo check.

### 19.4 Edge cases verified

| Case | Input | Expected and observed |
|---|---|---|
| Threshold not met | 3 failed logins, all Booleans Unknown | 0 activations, 0 findings |
| Unknown is not False | 0 failures, key Booleans Unknown | 0 activations, 0 findings |
| Invalid target | Full evidence, `USER-999` | 4 findings, action `Executable: No`, blocked reason, no Execute button |
| Valid target | Full evidence, `USER-101` | Action executable; `status=Active → status=Disabled` |
| Full reasoning | SCN-001 | AUTH-01 → AUTH-02 → AUTH-03 → AUTH-04, fixed point |

### 19.5 Browser verification

The interface was additionally exercised in a headless Chromium browser across all seven
pages and all six scenarios. The checks covered execution state changes, justification,
working memory, blocked actions, the empty dashboard and the two no-finding cases. The run
reported zero console errors and zero failed network requests.

### 19.6 Re-running the tests

```bash
python -m pytest -q
```

For the interface:

```bash
streamlit run app.py
```

---

## 20. Live Streamlit URL

**Deployment status: pending.** The application has been verified locally at:

```
http://localhost:8501
```

A local address is not a public WAN URL and does not satisfy the live-deployment requirement.
The public Streamlit Community Cloud URL must be inserted here after the project is deployed
with the owner's Streamlit and GitHub accounts. This section is intentionally not fabricated.

### 20.1 Deployment procedure

1. Push the project to a GitHub repository (the ZIP submission is prepared separately).
2. Sign in to Streamlit Community Cloud with GitHub.
3. Create a new app from the repository, selecting `app.py` as the entry point.
4. Confirm that `requirements.txt` installs Streamlit, pandas and pytest.
5. Deploy, open the public URL, and run SCN-001 plus one edge case.
6. Replace the placeholder above with the resulting `https://…streamlit.app` URL and
   regenerate this PDF.

### 20.2 Deployment notes

- History uses `data/investigations.json` when the filesystem is writable and degrades to
  session-only history when it is not.
- The simulated environment is per-investigation and per-session; no state is shared between
  users.
- No secrets, credentials or external services are required.

---

## 21. Limitations and conclusion

### 21.1 Limitations

1. **Simulated responses only.** Every action changes an in-memory object. This is a safety
   feature and a scope boundary, not a claim of real remediation.
2. **Manual knowledge acquisition.** Rules are authored and validated by hand. The system does
   not learn, and it cannot discover new attack patterns.
3. **Single-focus investigations.** The UI supplies one identifier per entity type per run.
   The activation key already supports multiple entities, so multi-entity correlation is an
   extension rather than a redesign.
4. **Monotonic inference.** Facts are added and never retracted. There is no non-monotonic
   reasoning or belief revision.
5. **Numeric observations are always known.** Only Boolean facts are tri-state, so a numeric
   zero is treated as a measurement rather than as missing data.
6. **Thresholds are assumptions.** The cut-offs are configurable CIARES project assumptions,
   not audited industry standards.
7. **Local history.** Persistence is a best-effort JSON mirror with no authentication or
   multi-user isolation.
8. **Static rule coverage.** The six scenarios exercise all 60 rules, but they cannot
   represent every combination of evidence.

### 21.2 Future work

- Multi-entity investigations with correlation across accounts, hosts and sessions.
- A rule editor backed by the Knowledge Acquisition module.
- Confidence factors or fuzzy thresholds for graded evidence.
- Integration adapters for real telemetry, behind an explicit safety boundary.
- Richer response planning, including rollback and verification steps.
- Exportable audit reports with signatures.

### 21.3 Conclusion

CIARES demonstrates that a cybersecurity incident-response Expert System can be built with
transparent symbolic reasoning rather than an opaque model. It contains 60 manually authored
rules and 85 logical conditions across five modules, reasons with three-valued logic, chains
rules across module boundaries, validates response targets, executes actions against a
simulated environment and explains every conclusion at condition level.

The project meets the functional requirements: a Streamlit-only interface, a real Python
inference engine, a knowledge base above the required size, a working-memory model,
decision-making with simulated execution, an explanation facility, knowledge acquisition and a
92-test verification suite. Its boundaries are stated honestly: responses are simulated,
knowledge is curated manually, and thresholds are project assumptions.

That combination — working system, visible evidence and acknowledged limits — is the
strongest position from which to demonstrate and defend the project in a viva.

---

## Appendix A — Complete rule catalogue

{{RULE_CATALOGUE}}

## Appendix B — Condition inventory

{{CONDITION_INVENTORY}}

## Appendix C — Scenario matrix

{{SCENARIO_TABLE}}

{{SCENARIO_RESULT_TABLE}}

## Appendix D — Glossary

| Term | Meaning |
|---|---|
| Activation | One rule firing against the current facts |
| Activation key | Rule ID + entity IDs + supporting values; prevents duplicate firing |
| Antecedent | The IF part of a rule |
| Consequent | The THEN part of a rule |
| Condition | One comparison inside a rule antecedent |
| Finding | A diagnosis derived from a rule conclusion |
| Fixed point | The state in which no further rule is eligible |
| Forward chaining | Data-driven inference from facts to conclusions |
| Justification | Condition-level explanation of why one rule fired |
| Knowledge base | The permanent collection of rules |
| Monotonic | Facts are only added, never retracted |
| Response action | A concrete, validated instruction derived from a finding |
| Three-valued logic | True, False and Unknown, where Unknown is not False |
| Trace | The ordered record of observations, activations and decisions |
| Working memory | The facts of the current investigation |
