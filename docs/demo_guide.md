# CIARES — Demo and Viva Guide

**Cybersecurity Incident Analysis and Response Expert System**

This guide is for demonstrating CIARES when the examiner sees only the screen. Every claim
below is verifiable from a screen in the application, with exact labels and expected numbers.

The application has two routes:

* the **public portal** at `/` — Home, Investigate, Scenarios and Results as sidebar sections;
* the **administration portal** at `/admin` — six tabs behind a sign-in gate.

`/admin` is not linked anywhere. The sidebar, the pages and the buttons never mention it.

---

## 1. The 30-second opening pitch

> "CIARES is a rule-based Expert System for cybersecurity incident response. It takes raw
> observations, reasons over 60 manually authored IF–THEN rules using forward chaining, derives
> findings, explains them in plain language, recommends a response, and — once the analyst
> approves it — writes the response plan. There is no machine learning, no external AI service
> and no simulation: every conclusion is traceable to a rule, and every action is carried out by
> a human."

Point at the Home metrics: **60 rules · 85 logical conditions · 5 modules**.

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
| Explanation facility | `/admin` → Inference engine → Justification | Per-condition expected vs observed vs status |
| Prose explanation | Results → "What led to this" | Sentences only; no rule identifiers |
| Rule ids on demand | Results → **Technical evidence (administrative)** | Collapsed table; rule ids only when opened |
| Decision engine | `/admin` → Decision engine | Decision rules, recommendations, 15-action catalogue |
| Human approval | Results → tick recommendations → Approve | Response plan appears; nothing executed by CIARES |
| Written plan | Results after approval | Numbered steps + `.txt` download |
| Knowledge acquisition | `/admin` → Knowledge base green banner | Catalogue validated; approved sources shown |
| Persistence / audit | `/admin` → Audit | Records survive refresh; JSON/CSV download |
| Hidden admin | Inspect the sidebar | Only four sections; no "Admin" text anywhere |

**Say explicitly:** "The UI is not a mock-up. Every count, table and sentence is generated from
the rule objects and the engine at runtime."

---

## 3. Two-minute setup before the viva

1. Open `/admin`, sign in, go to **Audit → Danger zone → Clear all records**. This gives a clean
   dashboard. (Public users have no way to see or clear records.)
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
   **Unknown**.

---

## 4. The demonstration script

### Step 1 — Home (1 minute)

**Click:** Home.

**Say:**

- "This is what an analyst sees. No account, no sign-in, immediate access."
- "The counts are computed from the loaded rule objects at runtime, not typed into the page."
- "Five knowledge modules, six scenarios, fifteen response types."
- "The sidebar has four sections. Investigate, Scenarios and Results are not separate URLs."

---

### Step 2 — Scenario laboratory, SCN-001 (2 minutes)

**Click:** Scenarios → keep `SCN-001`.

**Say:**

- "The scenario supplies observations only. It does not supply findings or the answer."
- "The expander lists the observations; the diagnosis will come from the engine."

**Click Run this scenario.**

Expected: **4 rule activations, 4 findings**, threat level **100/100**.

**Say:**

- "Four rules fired: repeated failures, suspicious login sequence, unusual location, and finally
  possible account compromise."
- "The fourth rule could only fire after the first three inserted their conclusions into working
  memory. That is forward chaining in action."

---

### Step 3 — Results, the analyst view (3 minutes)

**Point at the threat meter:** `100/100` with the sentence "Threat level 100 out of 100 —
Critical severity: the evidence is conclusive or the activity is still in progress, so
containment should begin immediately."

**Say:** "The score is a documented project assumption: Critical 50, High 25, Medium 10, Low 5,
capped at 100. It is deterministic, not probabilistic."

**Point at the headline and findings:** Possible account compromise (critical), repeated
authentication failures (high), suspicious login sequence (high), unusual-location login
(medium).

**Say:** "Findings are in sentences and ordered by severity. Severity sorts them; it never
deletes one."

**Point at "What led to this":** four paragraphs, each naming the observations that supported
the conclusion.

**Say:**

> "This is the explanation facility as the analyst sees it. Notice there is not a single rule
> identifier: the reasoning is stated in the analyst's language. An auditor who wants the rule
> ids can open the collapsed technical evidence table at the bottom — that is the same data the
> admin trace uses."

**Point at Recommended response:** `ACT-001 · Disable affected account`, phase Containment, with
the reason.

**Say:**

- "Not every finding produces an action. Diagnostic rules only diagnose; only rules that
  recommend a response create a recommendation."
- "The Decision Engine deduplicates, defers recovery until containment is verified, and orders
  by phase and priority."
- "Nothing happens until the analyst approves."

**Click Approve selected recommendations.**

Show the **Response plan**: "Approved … 1 recommendation(s) accepted", the numbered step, the
download button and the **Revise the approval** expander.

**Say:** "This is the hand-over point. CIARES writes the plan; the analyst carries it out. No
real account is touched, because CIARES has no connection to any system."

---

### Step 4 — The hidden administration portal (1 minute)

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
- "Approved actions counts the recommendations an analyst accepted."

**Click:** Knowledge base.

**Point to the metrics:** 60 rules, 85 logical conditions, 80 distinct fact fields, 5 modules.

**Say:**

- "Each module has exactly 12 manually authored rules."
- "The condition inventory at the bottom is machine-generated from the rule objects. That is the
  evidence for the 50-condition requirement — 85 conditions across 80 distinct facts."

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

**Say:** "This rule fires only on an explicit False. If the fact is Unknown, it cannot fire. That
is the difference between 'not approved' and 'not checked'."

**Open `POL-12 · Coordinated Privilege Compromise`:** show that its conditions reference
`possible_account_compromise`, which is the conclusion of AUTH-04.

**Say:** "This is cross-module chaining: privilege abuse is escalated to a coordinated
compromise only if the authentication module has already reached its own conclusion."

**If he asks how the rules are validated:** point at the green banner.

> "The knowledge acquisition module validates every rule on load — ID format, uniqueness,
> description, at least one condition, no self-supporting conclusion, approved source, and a
> well-formed action key and phase. Any failure is shown as a red error here."

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

**Say:** "The trace explanation tells you what fired, in what order. The justification tells you
why this rule fired, with the exact facts that satisfied each condition."

**Working memory tab:** show observations, derived conclusions and the deriving rule.

**Say:** "Every derived fact records which rule produced it and which facts supported it. That is
provenance, and it is why the explanation is not post-hoc storytelling."

**Reasoning log tab:** show start → observations → activations → diagnosis → decision → finish.

---

### Step 7 — Decision engine (2 minutes)

**Click:** Decision engine.

**Point at the decision rules**, then the recommendations table for the selected record.

**Say:** "The inference engine answers *what is happening*; this layer decides *what should be
done about it* — selection, deduplication, containment before recovery, and ordering by phase
and priority."

**Scroll to the action catalogue.** Show the 15 actions with phase, priority and what each does.

**Say:** "Requests are pure policy. The catalogue is the set of recommendations CIARES can make;
there is no execution layer because a decision-support system should leave the action to the
accountable human."

---

### Step 8 — Audit (1 minute)

**Click:** Audit.

Show:

- each investigation with source, scenario ID, findings, critical count, approved count;
- filter by source and scenario;
- select one → findings, observations, activations, recommendations;
- **Download record (JSON)** and **Download summary (CSV)**;
- the **Admin events** tab: sign-in, sign-out and clear actions.

**Say:** "A record is written after every investigation and updated after approval, so the audit
trail is the engine's output, not a separate log I typed. Records live in SQLite; on Streamlit
Community Cloud the filesystem is ephemeral, which the dashboard states honestly."

---

### Step 9 — Prove it is general, not scripted (2 minutes)

Go back to **Scenarios** (public).

**Option A — SCN-002 (malware):** 12 findings, 4 recommendations.

- isolate endpoint
- isolate process
- terminate process
- quarantine file

**Say:** "The same engine and decision logic, a different module. It chose a different action
chain because the findings were different."

**Option B — SCN-005 (cross-module privilege abuse):** 16 findings, including **Coordinated
privilege compromise**.

**Say:** "This finding required the authentication module to derive a possible account
compromise and the policy module to derive privilege escalation. It is the strongest proof of
cross-module inference."

Point out the recommendations: 2 ready to approve and 1 **deferred** in the "Deferred until
containment is verified" expander.

**Say:** "The recovery action `revoke_permissions` is deferred because a containment action is
open. CIARES refuses to restore access while containment is in effect."

---

### Step 10 — Edge cases the examiner may test (2 minutes)

Use **Investigate** (public).

#### Test A — threshold not met

- Failed login attempts = `3`
- Everything else Unknown
- Run

**Expected:** headline "No incident detected", threat level `0/100`, no findings.

**Say:** "No evidence, no finding. The system does not invent an incident from weak signals."

#### Test B — Unknown is not False

- Failed login attempts = `0`
- Successful login after failures = **Unknown**
- Unusual login location = **Unknown**
- Run

**Expected:** no findings.

**Say:** "Unknown means 'not established'. It never satisfies a rule. A rule that needs a fact to
be True cannot fire just because nobody provided it."

#### Test C — the evidence table

- Run any scenario → Results → open **Technical evidence (administrative)**

**Expected:** rule ids, names, conclusions and severities.

**Say:** "The public narrative hides the ids, but they are one click away for audit. Nothing is
hidden; it is only kept out of the analyst's reading flow."

---

## 5. Scenario cheat sheet

| Scenario | What it proves | Activations | Findings | Recommendations |
|---|---|---|---|---|
| **SCN-001** Account Compromise | classic chaining AUTH-01 → 04 | 4 | 4 | 1: disable account |
| **SCN-002** Malware | multi-stage process/file/endpoint response | 12 | 12 | 4: isolate endpoint, isolate process, terminate, quarantine file |
| **SCN-003** Network Intrusion | C2 + exfiltration reasoning | 12 | 12 | 4: isolate endpoint, block destination, restrict connection, escalate |
| **SCN-004** Data Exfiltration | volume + unauthorized destination | 9 | 9 | 2: restrict transfer, restrict data access |
| **SCN-005** Privilege Escalation | cross-module POL-12 | 16 | 16 | 3: disable account, 1 deferred recovery, escalate |
| **SCN-006** Credential Abuse + Integrity | tri-state auth + integrity breach | 15 | 15 | 3: disable account, revoke session, escalate |

Memorise the SCN-001 numbers: **4 rules, 4 findings, 1 recommendation, 1 written plan**.

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
conclusions until a fixed point. Backward chaining would start from a hypothesis, which is less
suitable when the incident type is unknown.

**Q: What is working memory?**
A: The facts of the current investigation only. Each fact is True, False or Unknown, and every
derived fact records which rule produced it and which facts supported it.

**Q: How do you handle uncertainty?**
A: Three-valued logic. Unknown is distinct from False. A rule requires every condition to
evaluate to True; an Unknown condition makes the rule ineligible. Explicit False can satisfy a
negative condition such as "process is not on the approved list", but never "fact is True".

**Q: How do you stop rules firing forever?**
A: Facts are only added, never retracted, and each activation key — rule id plus the exact
supporting facts — can fire once. The engine stops at a fixed point, with a cycle cap as a
safety guard.

**Q: How do you resolve conflicts between rules?**
A: Firing order is deterministic: severity, then author priority, then rule id. Findings are
never discarded because another finding is more severe. Recommendations are deduplicated by
action key, and recovery is deferred while containment is open.

**Q: What is the difference between a finding and a recommendation?**
A: Findings are diagnoses. Only rules marked actionable carry a recommended response and phase.
So the system can report a problem without inventing a response.

**Q: How is the explanation generated?**
A: The engine records every activation with its condition evaluations. The Explanation Facility
reads those records to produce the admin trace and per-rule justification; the Report Writer
turns the same records into the sentences the public portal shows. Neither re-runs the engine.

**Q: Why are there two portals?**
A: A product decision. The analyst needs the diagnosis, the reasoning and the recommendation;
that is `/`. The knowledge base, activation trace and decision internals are administration
concerns, so they sit behind `/admin`. Both surfaces call the same engine, so there is no second
reasoning path that could drift from the tests.

**Q: Is `/admin` secure?**
A: It is a demonstration gate, not an identity provider: a single administrator, a PBKDF2 hash
in secrets, constant-time comparison, and a five-attempt session lock. The page is hidden from
navigation, but hiding is not security — the credential is what protects it. I describe it as a
session-level control, not enterprise auth.

**Q: How do you know all 60 rules are real and not padding?**
A: A coverage test asserts that every registered rule fires in at least one shipped scenario. If
a rule can never activate, the test suite fails. All 60 are currently reachable.

**Q: Where are the 50 conditions?**
A: 85 logical conditions across 80 distinct fact fields. The Knowledge base tab regenerates the
inventory from the rule objects at runtime, so the count cannot drift from the code.

**Q: Are the thresholds industry standards?**
A: No. They are configurable CIARES project assumptions, stated as such in the report. The
detection logic is sourced from NIST, MITRE ATT&CK and CISA; the numeric cut-offs are
illustrative.

**Q: Does it learn?**
A: No, by design. Knowledge acquisition is manual and validated. The value of the project is
transparent, auditable reasoning, not statistical prediction.

**Q: Can it affect a real system?**
A: No. There is no execution layer at all. CIARES recommends and writes a plan; the analyst
carries it out. That boundary is deliberate for a decision-support system.

**Q: What are its limitations?**
A: Manual knowledge acquisition; one incident per investigation; monotonic inference with no
retraction; numeric inputs are always considered known while booleans are tri-state; thresholds
and the threat score are assumptions; SQLite is ephemeral on Community Cloud.

**Q: Why Streamlit?**
A: It keeps the whole project Python-only and lets the UI call the engine directly, so there is
no second code path between the demo and the tests.

---

## 8. How to phrase the limitations without losing marks

Say this proactively:

> "Three honest limitations: knowledge is manually curated rather than learned; the
> investigation is single-focus — one incident per run; and CIARES deliberately stops at the
> recommendation, because a decision-support system should leave the action to the accountable
> human. The admin gate is a demonstration control, and SQLite on Community Cloud is ephemeral —
> both stated in the app rather than hidden."

Examiners reward acknowledged boundaries far more than overclaiming.

---

## 9. One-page cheat sheet

```text
Routes:       /       public portal (Home, Investigate, Scenarios, Results)
              /admin  typed manually, email + password

Rules:        60   (12 × AUTH, MAL, NET, DATA, POL)
Conditions:   85   (50 required)
Fact fields:  80
Actions:      15
Tests:        106 passed, 0 skipped
Scenarios:    6, all 60 rules reachable

SCN-001 -> 4 activations / 4 findings / 1 recommendation -> disable account
SCN-002 -> 12 / 12 / 4 -> isolate endpoint + process, terminate, quarantine file
SCN-003 -> 12 / 12 / 4 -> isolate endpoint, block destination, restrict connection, escalate
SCN-004 -> 9 / 9 / 2 -> restrict transfer + data access
SCN-005 -> 16 / 16 / 3 -> cross-module POL-12, 1 recovery deferred
SCN-006 -> 15 / 15 / 3 -> disable, revoke session, escalate

Edge cases:
  3 failures                -> No incident detected, 0/100
  Unknown booleans          -> no finding
  Evidence table (Results)  -> rule ids only when expanded
```
