# CIARES Expert System - Viva Evaluation Guide

## Table of Contents
1. [UI Questions for User/Investigator](#ui-questions-for-userinvestigator)
2. [UI Questions for Admin](#ui-questions-for-admin)
3. [Code Questions (Easy to Difficult)](#code-questions-easy-to-difficult)
4. [Expert System Theory Questions](#expert-system-theory-questions)
5. [Scenario-Based Questions](#scenario-based-questions)
6. [Final Tips for Evaluation](#final-tips-for-evaluation)

---

## UI Questions for User/Investigator

### Basic Navigation
**Q: How do you start a new investigation?**
A: From the Home page, click the "Start an investigation" button (primary, green). This navigates to the Investigate section where you can enter observations.

**Q: How do you try a predefined scenario?**
A: On the Home page, click "Try a scenario" (icon: science beaker). This presents a dropdown of 6 scenarios (SCN-001 through SCN-006). Select one, and it will auto-populate observations based on that scenario's predefined data.

**Q: What are the 5 modules of observations you need to fill?**
A:
1. **Authentication & Account Security** - failed login attempts, successful login after failures, unusual login location, login outside working hours, login to disabled account, is admin account, concurrent sessions, MFA failures, unauthorized password change, impossible travel detected
2. **Malware & Process Security** - process runs from unapproved path, process on approved list, unauthorized operation attempted, protected file modified, file is signed, spawns shell, persistence entry added, security log cleared, executable hash known, file in temp directory
3. **Network Security** - destination authorized, port approved, remote access authorized, suspicious inbound connection, beaconing interval detected, unexpected listening service, outbound traffic (MB), connection attempts, denied request count
4. **Data Security & Protection** - transfer volume (MB), download count, transfer destination authorized, restricted file accessed unauthorized, sensitive file shared externally, access outside permitted hours, data modified without approval, protected data deleted
5. **Privilege & Security Policy** - unauthorized privilege escalation, admin privileges granted, permission change approved, security control disabled, admin operation unauthorized, security config changed unapproved, self approval detected, dormant account privileged, restricted resource accessed unauthorized

**Q: What do the TRI options mean?**
A: TRI_OPTIONS = ("Unknown", "True", "False")
- **True** = the fact was observed and confirmed
- **False** = the fact was observed and confirmed to be absent
- **Unknown** = the fact was not provided (key is absent). This is deliberately different from False; a rule needing True will not fire just because nobody asked.

**Q: After running an investigation, what do you see on the Results page?**
A: The Results page shows:
- Threat meter (numeric score + severity sentence)
- Headline finding with severity chip
- Overview paragraph summarizing the incident
- Findings with severity chips (Critical/High/Medium/Low)
- "What led to this" - plain-language reasoning paragraphs
- Recommended responses with checkboxes for approval
- Technical evidence expander showing rule IDs for audit
- Download response plan button

### Investigation Process
**Q: Walk me through the 4-step investigation process.**
A:
1. **Step 1 · Describe** - Enter what was observed in the 5 module fields
2. **Step 2 · Read** - Click "Run investigation"; the system performs forward-chaining inference and shows the diagnosis (findings with severity, overview, reasoning)
3. **Step 3 · Approve** - Review recommended responses (phase-ordered: Containment → Eradication → Recovery → Escalation); tick the actions you accept; click "Approve selected recommendations"
4. **Step 4 · Plan** - After approval, a structured response plan is generated with steps organized by phase; can be downloaded as .txt file

**Q: What happens if I don't provide all observations?**
A: Unknown facts are allowed. Rules with Unknown conditions simply become ineligible (they don't fire). The system will still diagnose based on the facts provided. You can leave fields as "Unknown" (default selection).

**Q: Can I use CIARES on real systems?**
A: No. CIARES explicitly advises a human analyst. It does not disable accounts, isolate hosts, or change any real systems. All it does is diagnose, explain reasoning, recommend responses, and write a plan that a human must approve and carry out.

**Q: What is the threat score and how is it calculated?**
A: The threat score is a numeric value calculated from the investigation's findings (using `threat_score()` in `engine/report.py`). It reflects the overall severity and is displayed on the Results page threat meter.

---

## UI Questions for Admin

### Authentication & Access
**Q: How do you access the admin portal?**
A: The admin portal is at the `/admin` route and is password-protected. You need the administrator email and password configured in `.streamlit/secrets.toml`. The login form requires both correct email and password (constant-time verification).

**Q: What if I forget the admin password?**
A: The admin credentials are not stored in source control. You would need to configure a new admin password in the Streamlit secrets configuration (`[auth]` section with `admin_password` or `admin_password_hash`).

**Q: How many admin login attempts are allowed?**
A: Maximum 5 attempts. After 5 failures, sign-in is locked for that session.

### Admin Tabs & Functions
**Q: What are the 6 tabs in the admin portal?**
A: 1. **Dashboard** - Aggregated statistics, findings by severity/module, knowledge base validation status
2. **Knowledge Base** - Browse all 60 rules, view conditions, conclusions, severities, sources; search by module
3. **Inference Engine** - View activation sequences, justifications, working memory provenance for stored investigations
4. **Decision Engine** - View decision rules, recommendations, action catalogue (all 15 possible responses)
5. **Audit** - Search and filter investigations, inspect findings/observations/activations/recommendations, download records
6. **System Map** - Documentation of codebase structure and function responsibilities

**Q: What does the Knowledge Base tab show?**
A: It displays all 60 rules organized by 5 modules. For each rule you can see:
- Rule ID and name
- Number of conditions
- Conclusion label and severity
- Source (MITRE ATT&CK, NIST, CISA, or project assumption)
- Full condition details (field, operator, value)
- Recommended action and phase (if actionable)

**Q: What can you do in the Inference Engine tab?**
A: Select a stored investigation and view:
- **Activation sequence** - ordered list of rule firings with step numbers and event types
- **Justification** - for a selected rule activation: every condition with observed value and satisfaction status
- **Working memory** - all observations and derived facts with provenance (which rule derived each fact)

**Q: What does the Decision Engine tab show?**
A: It displays:
- The 5 decision rules CIARES follows (response recommended only when rule asks, identical actions collapsed, recovery deferred while containment open, ordered by phase then priority, analyst approves)
- Recommendations for the selected investigation (with status: Awaiting approval/Approved/Deferred)
- The full action catalogue - all 15 possible responses with their phase, priority, and description

**Q: What can you do in the Audit tab?**
A: 
- Filter investigations by source (all/manual/scenario) and scenario ID
- Search with a limit of 10-200 rows
- Click on any investigation to inspect:
  - Findings (label, severity, module, supporting rule IDs)
  - Observations (fact key and value)
  - Activations (rule ID, conclusion, evaluation details)
  - Recommendations (action ID, phase, priority, status)
- Download individual records as JSON or all as CSV
- "Danger zone": delete all investigation records (requires confirmation)

**Q: What is stored in the SQLite database?**
A: The database (`data/ciares.db`) stores:
- **Investigations table**: one row per investigation with metadata (ID, name, source, scenario ID, activation/finding/severity/action counts, score, terminated reason) + full JSON payload for replay
- **Admin events table**: audit trail of sign-in activity (timestamp, event type, detail)

---

## Code Questions (Easy to Difficult)

### EASY LEVEL

**Q: What is the entry point file for the public portal?**
A: `app.py` - contains the `main()` function and `public_portal()` function that renders the Streamlit web application with routes for Home, Investigate, Scenarios, and Results.

**Q: Where are the 60 rules defined?**
A: In `knowledge_base/` directory across 5 module files:
- `authentication.py` - AUTH-01 to AUTH-12 (Authentication & Account Security)
- `malware.py` - MAL-01 to MAL-12 (Malware & Process Security)
- `network.py` - NET-01 to NET-12 (Network Security)
- `data_security.py` - DATA-01 to DATA-12 (Data Security & Protection)
- `security_policy.py` - POL-01 to POL-12 (Privilege & Security Policy)

**Q: What does the inference engine do?**
A: `engine/inference_engine.py` - Implements forward-chaining reasoning. Evaluates rules one cycle at a time, fires eligible rules (highest priority first), records activation order, stops at fixed point or cycle limit.

**Q: What are the five main modules in CIARES?**
A: Listed in `knowledge_base/rule_registry.py`:
1. Authentication & Account Security
2. Malware & Process Security
3. Network Security
4. Data Security & Protection
5. Privilege & Security Policy

**Q: Where is the threat score calculated?**
A: `engine/report.py` - contains `threat_score()` function that computes a numeric score from an investigation's findings.

**Q: What does the Working Memory class do?**
A: `engine/working_memory.py` - Holds per-investigation facts with three-valued logic (True/False/Unknown). Supports adding observations, inference of derived facts, and checking if facts are known.

**Q: How many predefined scenarios are there and what are their IDs?**
A: 6 scenarios in `scenarios/sample_scenarios.py`:
- SCN-001: Account Compromise Investigation
- SCN-002: Malware Activity Investigation
- SCN-003: Network Intrusion Investigation
- SCN-004: Data Exfiltration Investigation
- SCN-005: Privilege Escalation Investigation
- SCN-006: Credential Abuse and Data Integrity Investigation

### MEDIUM LEVEL

**Q: Explain the forward-chaining algorithm in the inference engine.**
A: From `engine/inference_engine.py`:
1. Evaluate every rule against working memory
2. A rule is eligible only when every condition is satisfied (Unknown makes it ineligible)
3. Build activation key from rule ID + supporting facts, discard duplicates
4. Fire the highest-priority eligible rule (sorted by: -severity rank, then priority, then rule ID)
5. Record the activation, insert conclusion into working memory
6. Repeat from step 1 until no eligible activations remain (fixed point) or max cycles reached

**Q: How does the decision engine order recommendations?**
A: From `engine/decision_engine.py`:
- Recommendations are sorted by: (phase order, priority, action name)
- Phase order: Containment (1) → Eradication (2) → Recovery (3) → Escalation (4)
- Recovery actions are deferred while any containment action is still open
- Identical actions are collapsed into a single recommendation

**Q: What is the rule data structure and where is it defined?**
A: From `engine/models.py` - The `Rule` dataclass has fields: id, name, module, description, conditions (tuple of Condition), conclusion_key, conclusion_label, severity, source, recommended_action (optional), action_phase (default ESCALATION), priority (default 100), tags (optional).

**Q: Explain Condition objects and how they evaluate.**
A: From `engine/models.py` - A `Condition` has field, operator, value, and label. The `evaluate()` method uses three-valued logic:
- If fact is Unknown → returns (None, "cannot evaluate")
- If operator is comparison (> , >= , < , <=) → checks numeric equality
- If operator is == → checks values_equal (handles bool/number distinction)
- If operator is != → negates equality
- Returns (satisfied_bool, note_string)

**Q: How does the pipeline orchestrate an investigation?**
A: From `engine/pipeline.py` - `run_investigation()` function:
1. Create Investigation object with ID, name, observations, scenario_id
2. Create WorkingMemory and add observations
3. Run InferenceEngine with ALL_RULES → get InferenceResult (activations, cycles)
4. Build findings from activations (strongest severity wins, merge supporting rules)
5. Run DecisionEngine.decide() → produce ordered ResponseActions
6. Populate investigation with activations, findings, actions, trace, terminated reason
7. Return Investigation object

**Q: What is the rule registry and how are ALL_RULES assembled?**
A: From `knowledge_base/rule_registry.py` - Imports AUTH_RULES, MALWARE_RULES, NETWORK_RULES, DATA_RULES, POLICY_RULES from their respective module files. ALL_RULES is a tuple combining all rules from all 5 modules, ordered by module sequence.

**Q: How does the admin authentication work?**
A: From `admin.py` and `passwords.py` - Uses Streamlit secrets (`.streamlit/secrets.toml`) with PBKDF2-SHA256 hashed passwords. Verification is constant-time using `hmac.compare_digest()`. Email is also verified. Maximum 5 attempts before lockout.

**Q: How are investigations stored and retrieved?**
A: From `storage/db.py` - SQLite database (`data/ciares.db`). Uses `save_investigation()` to INSERT OR REPLACE, `list_investigations()` to query with filters, `load_investigation()` to rehydrate from stored payload JSON. Schema includes 20+ columns plus a payload column for full investigation replay.

### HARD LEVEL

**Q: Explain the three-valued logic and Unknown handling in the inference engine.**
A: From `engine/models.py` `Condition.evaluate()` and `engine/inference_engine.py`:
- **True** = observed and confirmed fact
- **False** = observed and confirmed to be absent  
- **Unknown** = fact not provided (key absent in working memory)
- A rule with an Unknown condition is **ineligible** (never fires, never assumed)
- This differs from False: a rule needing `unusual_login_location is True` must not fire just because nobody asked
- The inference engine's `evaluate_rule()` checks `memory.is_known(condition.field)` - if not known, rule is not eligible
- The working memory `is_known()` returns True only when fact.value is not None
- This design ensures rules only fire on provided observations, making the system deterministic and auditable

**Q: Explain the forward-chaining fixed-point cycle and cycle limit.**
A: From `engine/inference_engine.py` `run()` method:
- Starts with `fired: set[str]` to track activation keys already used
- Loop runs while `result.cycles < self.max_cycles` (default: `max(100, len(self.rules) * 5)` = ~400 for 60 rules)
- In each cycle: find eligible activations, fire the highest-priority one
- Record activation key to prevent same rule firing twice on identical evidence
- If no eligible activations: terminate with "fixed point: no further eligible rules"
- If cycle limit reached: terminate with "cycle limit reached"
- After loop: record finish trace with activation count and terminated reason

**Q: How does the explanation facility produce trace and justification explanations?**
A: From `engine/explanation_engine.py`:
- **Trace explanation**: `trace_rows()` returns ordered sequence of rule activations with step, event kind, and message. Based on investigation.trace which is recorded by working_memory during inference.
- **Justification explanation**: `justification()` for a RuleActivation returns rule details + every condition with field, operator, expected value, observed value, status (Satisfied/Not satisfied/Unknown), and note. `justification_markdown()` formats this as markdown table.
- **Activation rows**: `activation_rows()` returns table with step #, rule ID, rule name, module, conclusion label, severity, whether new fact was inserted
- These interpretations use records already produced by the engine; they don't re-run reasoning

**Q: Explain the decision engine's defer-recovery logic.**
A: From `engine/decision_engine.py` `_defer_recovery()` static method:
- After producing the proposed list of recommendations
- Checks if any containment action is in the list
- If containment present AND recovery actions exist: mark all recovery actions as `deferred=True`
- Set `defer_reason`: "Deferred: a containment action is still in progress. Recovery is only started once containment has been verified."
- If no containment action: no deferral needed
- This ensures realistic incident response ordering (contain before restore)

**Q: How does the knowledge base validation work?**
A: From `knowledge_base/knowledge_acquisition.py` (imported in app.py as `validate_catalogue`) and used in admin portal:
- Validates that ALL_RULES structure is correct
- Checks for unique rule IDs, conditions present, valid severities and sources
- Reports errors or success status
- Displayed in both home page ("What it does" card count) and admin dashboard

**Q: Explain the complete data flow from user observation to response plan.**
A: From `app.py` `investigate()` through `engine/pipeline.py` `run_investigation()`:
1. User fills observation form in `app.py` `_collect()` → dict of key-value pairs
2. `launch()` calls `run_investigation(observations=..., name=...)`
3. Pipeline creates `WorkingMemory()`, adds observations via `add_observations()`
4. `InferenceEngine(rules).run(memory)` → forward chaining, returns `InferenceResult` with activations
5. `build_findings(activations)` → groups activations into `Finding` objects (merging same conclusions, keeping strongest severity, collecting all rule IDs)
6. `DecisionEngine().decide(findings)` → maps findings to `ResponseAction` objects with phase, priority, reason
7. Investigation object populated with: activations, findings, actions, trace, terminated_reason, scenario_id
8. Returned to `app.py` → stored in `st.session_state.investigation` → navigated to "Results" section
9. Results page displays: headline, findings with severity chips, reasoning paragraphs, recommended actions with checkboxes, evidence expander, download plan button
10. User taps "Approve selected recommendations" → `admin.approve()` → saves investigation with `approved_at` timestamp → shows approved plan

**Q: How does the system handle contradictory observations?**
A: From `engine/working_memory.py` `add_observation()`:
- Raises `ContradictionError` if a new observation contradicts an existing derived fact
- Prevents silent overwriting of derived facts by observations
- If same fact observed with same value (equality): returns False (no duplicate fact created)
- If same fact observed with different value: raises error
- This ensures data integrity in the working memory

### EXPERT SYSTEM THEORY QUESTIONS

**Q: How does CIARES qualify as an expert system?**
A: It has all four required elements from the project guidelines:
1. **Decision Making** - `engine/decision_engine.py` with 5 explicit decision rules
2. **Decision Support System** - `engine/pipeline.py` orchestrates the full investigation process
3. **Inferencing** - `engine/inference_engine.py` with forward-chaining, 60 IF-THEN rules
4. **Diagnosis** - Produces findings with severities, root causes, supporting rules, and recommended actions

Additionally, CIARES has:
- Explicit knowledge base (60 manually authored rules from MITRE ATT&CK, NIST, CISA)
- Forward-chaining inference engine with three-valued logic
- Diagnosis production (findings grouped by severity, module, rule IDs)
- Decision support (ordered recommendations requiring human approval)
- Explanation facility (trace and justification)
- Decision boundary (CIARES never executes actions; all recommendations require analyst approval)

**Q: What is the difference between a rule-based expert system and a machine learning system?**
A: 
- **Expert system (CIARES)**: Knowledge is explicitly encoded by humans as IF-THEN rules. All reasoning is transparent, auditable, and deterministic. No training data needed. Rules can be inspected, modified, and understood individually.
- **Machine learning**: Patterns are learned from data. Reasoning is often opaque ("black box"). Requires training/tuning data. Performance depends on data quality and representativeness.

CIARES is the former: all 60 rules are hand-authored, every conclusion can be traced to specific rules and conditions, and the system is designed for security auditability.

**Q: Explain the significance of Unknown ≠ False in CIARES.**
A: This is a deliberate design choice stated in the code comments (`engine/working_memory.py`):
- A rule that needs `unusual_login_location is True` must not fire just because the user didn't provide that fact
- If Unknown were treated as False, rules could fire on absent data, leading to false diagnoses
- By making Unknown ineligible, the system only diagnoses based on provided observations
- Missing facts simply mean rules don't fire, not that they fire with opposite conclusions
- This makes the system conservative and safe for a security advisory context

**Q: What are the project assumptions in CIARES and where are they?**
A: From `config.py`:
- **Thresholds** are project assumptions, not universal standards: failed_login_attempts (10), concurrent_sessions (3), mfa_failures (5), outbound_traffic_mb (500), transfer_volume_mb (1000), download_count (100), connection_attempts (20), denied_requests (15)
- **Working hours**: 08:00-18:00 (after-hours = outside this window, used by after-hours rules)
- **Approved knowledge sources**: NIST SP 800-61 Rev. 3, NIST Cybersecurity Framework 2.0, MITRE ATT&CK, CISA Guidance, CIARES Project Assumption
- These are grouped in one place so they can be tuned during demonstration and cited honestly as "CIARES assumptions"

### SCENARIO-BASED QUESTIONS

**Q: Walk through scenario SCN-001 (Account Compromise Investigation).**
A: From `scenarios/sample_scenarios.py` SCN_001:
- **Summary**: Twenty-five failed logins followed by a successful login from an unusual location. Classic credential-guessing pattern.
- **Observations provided**: failed_login_attempts=25, successful_login_after_failures=True, unusual_login_location=True, login_to_disabled_account=False, is_admin_account=True
- **Expected findings** (what the engine should diagnose):
  1. repeated_authentication_failures (AUTH-01, threshold >= 10)
  2. suspicious_login_sequence (AUTH-02, success after failures)
  3. unusual_location_login (AUTH-03, unusual location True)
  4. possible_account_compromise (AUTH-04, corroborating all three: repeated failures + success after + unusual location) - CRITICAL severity, recommends disable_account (containment)
- **How it runs**: The inference engine fires AUTH-01 (25 >= 10), then AUTH-02 (success after failures), then AUTH-03 (unusual location), then AUTH-04 (all three corroborating → possible account compromise). The decision engine then recommends disabling the account.

**Q: Walk through scenario SCN-002 (Malware Activity Investigation).**
A: From `scenarios/sample_scenarios.py` SCN_002:
- **Summary**: An unsigned executable in a temporary directory spawns a shell, modifies a protected file, installs persistence and then clears the security log.
- **Observations**: process_runs_from_unapproved_path=True, process_on_approved_list=False, unauthorized_operation_attempted=True, protected_file_modified=True, file_is_signed=False, spawns_shell=True, persistence_entry_added=True, security_log_cleared=True, executable_hash_known=False, file_in_temp_directory=True
- **Expected findings**: unapproved_process, suspicious_process_activity, persistence_mechanism_detected, log_tampering_detected, active_intrusion_with_concealment
- **Key rule chain**: MAL-01 (unapproved path) → MAL-02 (not on approved list) → MAL-03 (unauthorized operation) → MAL-04 (unapproved + policy violating) → MAL-08 (persistence entry) → MAL-11 (log clearing) → MAL-12 (persistence + log clearing = active intrusion with concealment, CRITICAL, isolate_endpoint). Decision engine recommends isolate_endpoint first (containment), then terminate_process (eradication), then quarantine_file (eradication).

**Q: What would happen if you ran SCN-004 (Data Exfiltration) with incomplete observations?**
A: If some observation fields are left as "Unknown" (default), rules requiring those facts become ineligible. For example, if transfer_volume_mb is Unknown, DATA-01 (unusual data transfer threshold) won't fire. However, other rules like DATA-02 (unauthorized transfer destination) might still fire if that fact is provided. The diagnosis would be partial - only the observations provided would be assessed. This demonstrates the system's conservative approach: no rule fires on Unknown facts.

**Q: Can two different scenarios produce the same diagnosis?**
A: Yes, because scenarios supply only observations, and the same inference engine processes both manual input and scenarios. For example, SCN-001 (account compromise via credential guessing) and a manual investigation with observations {failed_login_attempts: 25, successful_login_after_failures: True, unusual_login_location: True} would produce identical diagnoses because the engine reasons from observations alone, not from scenario identity.

---

## FINAL TIPS FOR EVALUATION

1. **Know the file layout**: Be able to point to any file when asked (app.py, admin.py, engine/inference_engine.py, engine/decision_engine.py, knowledge_base/authentication.py, etc.)

2. **Understand the big picture**: Remember the 4 required elements (decision making, decision support, inferencing, diagnosis) and where each lives in the code.

3. **Know the 60 rules**: Which module they're in, their IDs (AUTH-01 to AUTH-12, MAL-01 to MAL-12, etc.), and what each one detects.

4. **Understand the three-valued logic**: True/False/Unknown, and why Unknown ≠ False is intentional for safety.

5. **Know the decision rules**: 5 decision rules from the admin portal's "Decision engine" tab.

6. **Know the cybersecurity framework references**: MITRE ATT&CK, NIST SP 800-61, CISA Guidance, and the 5 knowledge modules.

7. **Know the thresholds**: They're in config.py as project assumptions, not standards.

8. **Know the user flow**: Home → Investigate/Scenarios → enter observations → Run investigation → Results (diagnosis + recommendations) → Approve → Plan.

9. **Know the admin flow**: Login → Dashboard/KB/Inference/Decision/Audit/System Map → use filters and inspect tools.

10. **Be honest about project assumptions**: The thresholds and working-hour assumptions are CIARES-specific, not universal cybersecurity standards. This was deliberately designed to make the system deterministic and testable.

Good luck with your evaluation tomorrow! Remember: your sir will likely ask about the 4 required elements, the 60 rules location, how inference works, and the user/admin UI. The viva.txt and this evaluation guide should give you comprehensive coverage.