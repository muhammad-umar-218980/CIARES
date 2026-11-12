# CIARES — Demo and Viva Guide

**Cybersecurity Incident Analysis and Response Expert System**

This guide is for demonstrating CIARES when the examiner sees only the screen. Every claim
below is verifiable from a screen in the application. Exact labels, expected numbers and safe
answers are included.

The application has two surfaces:

* the **public portal** at `/` — Home, Investigate, Scenarios, Results;
* the **admin portal** at `/admin` — Dashboard, Knowledge base, Inference engine, Decision
  engine, Audit, System map.

`/admin` is not linked anywhere. The sidebar, the pages and the buttons never mention it.
That is intentional and worth saying out loud: the examiner is shown the whole expert system,
while the public demo stays uncluttered.

---

## 1. The 30-second opening pitch

> "CIARES is a rule-based Expert System for cybersecurity incident response. It takes raw
> observations, reasons over a knowledge base of 60 manually authored IF–THEN rules using
> forward chaining, derives findings, recommends a response, executes that response in a
> simulated environment, and explains every decision. There is no machine learning and no
> external AI service — every conclusion is traceable to a specific rule and specific facts."

Then point at the Home page metrics: **60 rules · 85 logical conditions · 5 modules**. That
single row answers the two largest marking criteria.

---

## 2. What the examiner can verify from the UI alone

| Requirement | Where to click | What he sees |
|---|---|---|
| No login for analysts | `/` | Home opens immediately |
| 60 rules | `/admin` → Knowledge base | 12 rules per module tab; count in the metrics |
| 50+ logical conditions | `/admin` → Knowledge base | 85 conditions, 80 distinct fact fields |
| Rules are real IF–THEN | `/admin` → Knowledge base → any rule expander | Field, operator, value, conclusion, severity, source |
| Five cybersecurity modules | `/admin` → Knowledge base tabs | AUTH, MAL, NET, DATA, POL — 12 rules each |
| Forward chaining | `/admin` → Inference engine → Activation sequence | `AUTH-01 → 02 → 03 → 04`, then **fixed point** |
| Working memory | `/admin` → Inference engine → Working memory | Observations, derived facts, deriving rule |
| Three-valued logic | Investigate → boolean dropdowns | True / False / **Unknown** |
| Explanation facility | Results → **Why this finding?** | Per-condition expected vs observed vs status |
| Decision engine | Results → Proposed responses | Phase, priority, target, executable, blocked reason |
| Simulated response | Results → Execute approved actions | `status=Active → status=Disabled` |
| Target validation | `/admin` → Decision engine → Target validation lab | `USER-999` rejected with a reason |
| Knowledge acquisition | `/admin` → Knowledge base green banner | Catalogue validated; approved sources shown |
| Persistence / audit | `/admin` → Audit | Records survive refresh; JSON/CSV download |
| Hidden admin | Inspect the sidebar | Only four entries; no “Admin” text anywhere |

**Say explicitly:** "The UI is not a mock-up. Every count, table and state change is generated
from the rule objects and the engine at runtime."

---

## 3. Two-minute setup before the viva

1. Open `/admin`, sign in, go to **Audit → Danger zone → Clear all records**. This gives a
   clean dashboard. (Public users have no way to see or clear records.)
2. Reload `/` and confirm the sidebar shows exactly **Home, Investigate, Scenarios, Results**.
3. Confirm Home prints **60 rules, 85 conditions, 80 fact fields, 5 modules** with no warning.
4. Keep three input patterns ready for the public form:

| Test | Inputs |
|---|---|
| Below threshold | Failed login attempts = `3`; everything else Unknown |
| Full compromise | `25` failures + Successful login after failures = **True** + Unusual login location = **True** |
| Unknown test | Numbers `0`; booleans left on **Unknown** |

5. Use **SCN-001** as the main story, with **SCN-002** or **SCN-005** as supporting evidence.
6. Never call the thresholds "industry standards". Say: **"configurable CIARES project
   assumptions, documented in the report."**
7. Remember: numeric fields default to `0` and count as known; boolean fields default to
   **Unknown**. Use the Unknown option deliberately when demonstrating uncertainty.

---

## 4. The 14–16 minute demonstration script

### Step 1 — Home (1 minute)

**Click:** Home.

**Say:**

- "This is what an analyst sees. No account, no sign-in, immediate access."
- "The counts are computed from the loaded rule objects at runtime, not typed into the page."
- "Five knowledge modules, six scenarios, fifteen simulated response types."
- "The sidebar has exactly four pages. There is no history page and no admin link — the
  internal machinery is not part of the analyst's job."

---

### Step 2 — Scenario laboratory, SCN-001 (2 minutes)

**Click:** Scenarios → keep `SCN-001`.

**Say:**

- "The scenario supplies observations only. It does not supply findings, responses or the
  answer."
- "The verification expander is a list the test suite asserts, not an input. If the engine
  fails to derive one of those facts, the page shows a red regression error."

**Point at the observations:** 25 failed logins, success after failures, unusual location.
**Point at the entities:** `USER-101`, `SESSION-204`.

**Click Run scenario.**

Expected: **4 rule activations, 4 findings**.

**Say:**

- "Four rules fired: repeated failures, suspicious login sequence, unusual location, and
  finally possible account compromise."
- "The fourth rule could only fire after the first three inserted their conclusions into
  working memory. That is forward chaining in action."

**Click Open full results.**

---

### Step 3 — Results, the analyst view (3 minutes)

**Point at the threat summary:** `1 critical · 2 high · 1 medium · 0 low`, and the severity
chart beside it.

**Say:** "This is the diagnosis. It is ordered by severity, and severity never discards a
finding — it only sorts it."

**Open the expanders marked “Why this finding?”.** There is one per finding.

- Pick **Possible account compromise**.
- Show the rules behind it (`AUTH-04`) and the condition table: condition, observed value,
  status.
- Show the THEN line: `possible_account_compromise = True`.

**Say:**

> "This is the explanation facility exposed to the analyst. Every finding can be opened to
> show the rule that produced it, the facts it read and whether each condition was satisfied.
> Nothing is a black box — and this is the same data the admin trace uses."

**Point at Proposed responses:**

- `ACT-001 · Disable affected account`
- Phase: Containment
- Target: `account:USER-101`
- Finding: Possible account compromise
- Executable: Yes

**Scroll to “Why these actions”.**

**Say:**

- "Not every finding produces an action. Diagnostic rules only diagnose; only rules that
  recommend a response create an action."
- "The Decision Engine chooses the target, checks that it exists and is in a valid state,
  removes duplicates, and orders actions by phase and priority."
- "Each action states why it qualifies, in the analyst's language."

**Click Execute approved actions.**

Show:

- `Execution: Success — Account USER-101 changed from Active to Disabled`
- `State change: status=Active → status=Disabled`
- **Simulated environment after execution**: `USER-101` is now `Disabled`.

**Say:** "This is a simulated environment. No real account was touched. The before → after
state change proves the action executed against the simulator rather than being printed as
text. The analyst approves; the system does not act on its own."

---

### Step 4 — The hidden admin portal (1 minute)

**Type the URL:** `/admin`.

**Say:** "This is not linked anywhere — not in the sidebar, not in a button. It exists so the
knowledge base and the reasoning can be inspected without exposing them to every analyst."

**Sign in** with the configured administrator email and password.

Point at the six tabs: **Dashboard, Knowledge base, Inference engine, Decision engine, Audit,
System map**.

**Say:** "Public users get the diagnosis. Administrators get the engine. Same code, two
surfaces."

---

### Step 5 — Dashboard + Knowledge base (3 minutes) — the most important tab

**Click:** Dashboard.

**Say:**

- "These numbers are computed from investigations actually stored in SQLite, not hardcoded."
- "Findings by severity and by module aggregate across every run."
- "The inventory panel is the fixed simulated world that response actions operate on."

**Click:** Knowledge base.

**Point to the metrics:** 60 rules, 85 logical conditions, 80 distinct fact fields, 5 modules.

**Say:**

- "Each module has exactly 12 manually authored rules."
- "The condition inventory at the bottom is machine-generated from the rule objects. That is
  the evidence for the 50-condition requirement — 85 conditions across 80 distinct facts."

**Open `AUTH-04 · Possible Account Compromise`.** It shows:

- IF three derived facts are true
- THEN `possible_account_compromise`
- Severity: Critical
- Source: NIST SP 800-61 Rev. 3
- Response: `disable_account`

**Say:**

- "This rule is deliberately multi-condition. It fires only when three independent indicators
  corroborate each other. One indicator alone is not enough."
- "This is why the system is not a list of alerts — it performs evidence combination."

**Open `AUTH-01`:** show `failed_login_attempts >= 10`.

**Say:** "That number is a CIARES assumption, not a universal standard. It lives in one
configuration file, and changing it changes the behaviour."

**Open `MAL-02`:** show `process_on_approved_list is False`.

**Say:** "This rule fires only on an explicit False. If the fact is Unknown, it cannot fire.
That is the difference between 'not approved' and 'not checked'."

**Open `POL-12 · Coordinated Privilege Compromise`:** show that its conditions reference
`possible_account_compromise`, which is the conclusion of AUTH-04.

**Say:** "This is cross-module chaining: privilege abuse is escalated to a coordinated
compromise only if the authentication module has already reached its own conclusion."

**If he asks how the rules are validated:** point at the green banner.

> "The knowledge acquisition module validates every rule on load — ID format, uniqueness,
> description, at least one condition, no self-supporting conclusion, approved source, and
> action/entity consistency. Any failure is shown as a red error here."

---

### Step 6 — Inference engine (2 minutes)

**Click:** Inference engine. Select the SCN-001 record.

**Activation sequence table:** `AUTH-01`, `AUTH-02`, `AUTH-03`, `AUTH-04` in order.

**Say:** "The order is the real reasoning order. The engine fires one rule at a time and
re-evaluates, so the trace is not reconstructed afterwards."

**Point at the caption:** `fixed point: no further eligible rules`.

**Say:** "The engine ran until no rule could add new knowledge. That is the forward-chaining
termination condition."

**Justification tab:** select `AUTH-04`. Show each condition with the observed value and
`Satisfied`, then the conclusion and the source.

**Say:** "The trace explanation tells you what fired, in what order. The justification tells
you why this rule fired, with the exact facts that satisfied each condition."

**Working memory tab:** show observations, derived conclusions and the deriving rule.

**Say:** "Every derived fact records which rule produced it and which facts supported it. That
is provenance, and it is why the explanation is not post-hoc storytelling."

**Reasoning log tab:** show start → observations → activations → diagnosis → decision →
finish.

---

### Step 7 — Decision engine + target validation lab (2 minutes)

**Click:** Decision engine.

**Point at the six decision rules**, then the proposed-actions table for the selected record.

**Say:** "The inference engine answers *what is happening*; this layer decides *what should be
done about it* — selection, target validation, deduplication, containment before recovery,
and ordering by phase and priority."

**Scroll to the action catalogue.** Show the phase, priority, target type, required field and
valid states.

**Scroll to Target validation lab.**

- Choose `disable_account`.
- Type `USER-999` → **Validate target**.
- Expected: *"Account USER-999 does not exist in the simulated environment; execution would be
  rejected."*

**Say:** "The Decision Engine validates the target against the simulated environment. An
unknown identifier is blocked with a reason instead of silently succeeding. This is a safety
property, not an error — and it is why the public form assigns valid targets automatically
rather than letting analysts invent identifiers."

- Type `USER-101` → **Validate target** → success.

---

### Step 8 — Audit (1 minute)

**Click:** Audit.

Show:

- each investigation with source, scenario ID, findings, critical count, executed count;
- filter by source and scenario;
- select one → findings, observations, activations, actions;
- **Download record (JSON)** and **Download summary (CSV)**;
- the **Admin events** tab: sign-in, sign-out and clear actions.

**Say:** "A record is written after every investigation and refreshed after execution, so the
audit trail is the engine's output, not a separate log I typed. Records live in SQLite; on
Streamlit Community Cloud the filesystem is ephemeral, which the dashboard states honestly."

---

### Step 9 — Prove it is general, not scripted (2 minutes)

Go back to **Scenarios** (public).

**Option A — SCN-002 (malware):** 12 findings, 4 actions.

- isolate process
- terminate process
- quarantine file
- isolate endpoint

Execute them and show `Running → Isolated → Terminated` and `Present → Quarantined`.

**Say:** "The same engine and decision logic, a different module. It chose a different action
chain because the findings were different."

**Option B — SCN-005 (cross-module privilege abuse):** 16 findings, including **Coordinated
privilege compromise**.

**Say:** "This finding required the authentication module to derive a possible account
compromise and the policy module to derive privilege escalation. It is the strongest proof of
cross-module inference."

Point out the action list: 3 proposed, 2 executable, 1 **Skipped** (inside the “Blocked or
deferred actions” expander).

**Say:** "The recovery action `revoke_permissions` was suppressed because a containment action
was already applied to the same account. CIARES refuses to restore access while containment
is in effect."

---

### Step 10 — Edge cases the examiner may test (2 minutes)

Use **Investigate** (public).

#### Test A — threshold not met

- Failed login attempts = `3`
- Everything else Unknown
- Run

**Expected:** "No rule fired for these observations."

**Say:** "No evidence, no finding. The system does not invent an incident from weak signals."

#### Test B — Unknown is not False

- Failed login attempts = `0`
- Successful login after failures = **Unknown**
- Unusual login location = **Unknown**
- Run

**Expected:** no findings.

**Say:** "Unknown means 'not established'. It never satisfies a rule. A rule that needs a fact
to be True cannot fire just because nobody provided it."

#### Test C — blocked target (admin only)

- `/admin` → Decision engine → Target validation lab
- `USER-999` → Validate target

**Expected:** blocked with a reason.

**Say:** "Same decision layer, same validation, demonstrated directly. The public analyst
never sees an identifier field, because the system assigns valid targets from the inventory."

---

## 5. Scenario cheat sheet

| Scenario | What it proves | Activations | Findings | Actions |
|---|---|---|---|---|
| **SCN-001** Account Compromise | classic chaining AUTH-01 → 04 | 4 | 4 | 1: disable account |
| **SCN-002** Malware | multi-stage process/file/endpoint response | 12 | 12 | 4: isolate process, terminate, quarantine file, isolate endpoint |
| **SCN-003** Network Intrusion | C2 + exfiltration reasoning | 12 | 12 | 4: block destination, restrict connection, escalate, isolate endpoint |
| **SCN-004** Data Exfiltration | volume + unauthorized destination | 9 | 9 | 2: restrict transfer, restrict data access |
| **SCN-005** Privilege Escalation | cross-module POL-12 | 16 | 16 | 3 proposed, 2 executable, 1 skipped |
| **SCN-006** Credential Abuse + Integrity | tri-state auth + integrity breach | 15 | 15 | 3: disable account, revoke session, escalate |

Memorise the SCN-001 numbers: **4 rules, 4 findings, 1 action, 1 state change**.

---

## 6. Five rules worth opening during the viva

| Rule | Why it is a good example |
|---|---|
| **AUTH-01** | Simple threshold rule; shows the configurable assumption |
| **AUTH-04** | Three-condition corroboration; shows AND logic |
| **MAL-02** | Fires only on explicit **False** — proves Unknown ≠ False |
| **DATA-11** | Two-stage exfiltration reasoning: unusual transfer + unauthorized destination, then restricted-data access |
| **POL-12** | Cross-module rule; its condition is another module's conclusion |

---

## 7. Likely viva questions and safe answers

**Q: What is the knowledge base here?**
A: 60 manually authored IF–THEN rules across five modules. Each rule is declarative: a set of
`(field, operator, value)` conditions and one conclusion. Nothing is learned from data.

**Q: Forward or backward chaining?**
A: Forward. Incident analysis is evidence-first: we start from observations and derive
conclusions until a fixed point. Backward chaining would start from a hypothesis, which is
less suitable when the incident type is unknown.

**Q: What is working memory?**
A: The facts of the current investigation only. Each fact is True, False or Unknown, and every
derived fact records which rule produced it and which facts supported it.

**Q: How do you handle uncertainty?**
A: Three-valued logic. Unknown is distinct from False. A rule requires every condition to
evaluate to True; an Unknown condition makes the rule ineligible. Explicit False can satisfy a
negative condition such as "process is not on the approved list", but never "fact is True".

**Q: How do you stop rules firing forever?**
A: Facts are only added, never retracted, and each activation key — rule id + entity ids +
the exact supporting facts — can fire once. The engine stops at a fixed point, with a cycle
cap as a safety guard.

**Q: How do you resolve conflicts between rules?**
A: Firing order is deterministic: severity, then author priority, then rule id. Findings are
never discarded because another finding is more severe. Actions are deduplicated by action +
target, and recovery is suppressed while containment applies to the same target.

**Q: What is the difference between a finding and an action?**
A: Findings are diagnoses. Only rules marked actionable carry a recommended response, phase
and target type. So the system can report a problem without inventing a response.

**Q: How is the explanation generated?**
A: The engine records every activation with its condition evaluations. The Explanation
Facility reads those records to produce the trace and the per-rule justification. It never
re-runs or re-reasons.

**Q: Why are there two portals?**
A: A product decision. The analyst needs the diagnosis, the reasoning behind a finding and the
recommended response; that is the public portal. The knowledge base, activation trace and
decision internals are administration concerns, so they sit behind `/admin`. Both surfaces
call the same engine, so there is no second reasoning path that could drift from the tests.

**Q: Is `/admin` secure?**
A: It is a demonstration gate, not an identity provider: a single administrator, a PBKDF2
hash in secrets, constant-time comparison, and a five-attempt session lock. The page is hidden
from navigation, but hiding is not security — the credential is what protects it. I describe
it as a session-level control, not enterprise auth.

**Q: How do you know all 60 rules are real and not padding?**
A: A coverage test asserts that every registered rule fires in at least one shipped scenario.
If a rule can never activate, the test suite fails. All 60 are currently reachable.

**Q: Where are the 50 conditions?**
A: 85 logical conditions across 80 distinct fact fields. The Knowledge base tab regenerates
the inventory from the rule objects at runtime, so the count cannot drift from the code.

**Q: Are the thresholds industry standards?**
A: No. They are configurable CIARES project assumptions, stated as such in the report. The
detection logic is sourced from NIST, MITRE ATT&CK and CISA; the numeric cut-offs are
illustrative.

**Q: Does it learn?**
A: No, by design. Knowledge acquisition is manual and validated. The value of the project is
transparent, auditable reasoning, not statistical prediction.

**Q: Can it affect a real system?**
A: No. Every response executes against an in-memory simulated environment with eight entity
types and fifteen actions. The UI shows before/after state changes inside that simulation.

**Q: What are its limitations?**
A: Simulated responses only; manual knowledge acquisition; one primary entity per type per
investigation; monotonic inference with no retraction; numeric inputs are always considered
known while booleans are tri-state; thresholds are assumptions; SQLite is ephemeral on
Community Cloud.

**Q: Why Streamlit?**
A: It keeps the whole project Python-only and lets the UI call the engine directly, so there
is no second code path between the demo and the tests.

---

## 8. How to phrase the limitations without losing marks

Say this proactively:

> "Three honest limitations: responses are simulated by design; knowledge is manually curated
> rather than learned; and the investigation is single-focus — one account, one session, one
> process per run. The activation key already supports multiple entities, so that is a future
> extension rather than a redesign. The admin gate is a demonstration control, and SQLite on
> Community Cloud is ephemeral — both stated in the app rather than hidden."

Examiners reward acknowledged boundaries far more than overclaiming.

---

## 9. One-page cheat sheet

```text
Routes:       /  /investigate  /scenarios  /results      (public, no login)
              /admin                                      (typed manually, email + password)

Rules:        60   (12 × AUTH, MAL, NET, DATA, POL)
Conditions:   85   (50 required)
Fact fields:  80
Tests:        111 passed, 0 skipped
Scenarios:    6, all 60 rules reachable

SCN-001 -> 4 activations / 4 findings / 1 action -> disable USER-101
SCN-002 -> 12 / 12 / 4 -> isolate+terminate process, quarantine file, isolate endpoint
SCN-003 -> 12 / 12 / 4 -> block destination, restrict connection, escalate, isolate endpoint
SCN-004 -> 9 / 9 / 2 -> restrict transfer + data access
SCN-005 -> 16 / 16 / 3 proposed, 1 skipped -> cross-module POL-12
SCN-006 -> 15 / 15 / 3 -> disable, revoke session, escalate

Edge cases:
  3 failures               -> no finding
  Unknown booleans         -> no finding
  USER-999 (admin lab)     -> Blocked: account does not exist
  USER-101 + full evidence -> Executable, Active -> Disabled
```
