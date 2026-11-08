// Capture UI screenshots for the CIARES PDF report.
// Usage: node <browser-automation>/browser.mjs http://localhost:8501 --session pdf --script ./scripts/capture_screenshots.mjs
const OUT = 'D:/CIARES/docs/screenshots';

export default async function run(page, ui) {
  const done = [];
  const notes = [];
  await page.setViewportSize({ width: 1500, height: 1050 });

  const wait = (ms = 900) => page.waitForTimeout(ms);

  async function idle(extra = 900) {
    try {
      await page.waitForFunction(
        () => !Array.from(document.querySelectorAll('button')).some((b) => b.textContent.trim() === 'Stop'),
        null,
        { timeout: 20000 },
      );
    } catch {
      notes.push('idle wait timed out');
    }
    await wait(extra);
  }

  async function scrollMainTop() {
    await page.evaluate(() => {
      const m = document.querySelector('[data-testid="stMain"]');
      if (m) m.scrollTo(0, 0);
    });
    await wait(500);
  }

  async function scrollElement(locator, offset = 80) {
    await locator.first().evaluate((el, off) => {
      const m = document.querySelector('[data-testid="stMain"]');
      const y = el.getBoundingClientRect().top - m.getBoundingClientRect().top + m.scrollTop - off;
      m.scrollTo(0, Math.max(0, y));
    }, offset);
    await wait(600);
  }

  async function scrollToHeading(name, offset = 80) {
    await scrollElement(page.getByRole('heading', { name, exact: true }), offset);
  }

  async function go(name) {
    await page.getByText(name, { exact: true }).first().click();
    await idle();
  }

  async function shot(name) {
    await wait(500);
    await page.screenshot({ path: `${OUT}/${name}.png` });
    done.push(name);
  }

  async function choose(labelText, optionText) {
    await page.getByRole('combobox', { name: labelText }).first().click();
    await wait(500);
    await page.getByRole('option', { name: optionText, exact: true }).first().click();
    await idle();
  }

  async function tab(name) {
    await page.getByRole('tab', { name, exact: true }).first().click();
    await wait(1000);
  }

  async function numberField(label, value) {
    const field = page.getByLabel(label);
    await field.fill(String(value));
    await field.blur();
    await wait(500);
  }

  // ---- 0. Reset history so the dashboard is deterministic -----------------
  await go('Investigation History');
  const clear = page.getByRole('button', { name: 'Clear history' });
  if (await clear.count()) {
    await clear.click();
    await idle(1500);
    notes.push('history cleared');
  }

  // ---- 1. SCN-001 scenario run -------------------------------------------
  await go('Scenario Laboratory');
  await scrollMainTop();
  await page.getByRole('button', { name: 'Run scenario' }).click();
  await idle(1600);
  await scrollMainTop();
  await shot('05_scenario_scn001_result');

  // ---- 2. Inference trace -------------------------------------------------
  await go('Inference Trace');
  await scrollToHeading('Rule activations', 60);
  await shot('06_trace_activations');

  await tab('Justification');
  await choose('Rule activation', 'AUTH-04');
  await scrollMainTop();
  await shot('07_justification_auth04');

  await tab('Working memory');
  await scrollToHeading('Derived conclusions (with provenance)', 70);
  await shot('08_working_memory');

  // ---- 3. Response center -------------------------------------------------
  await go('Response Center');
  await scrollMainTop();
  await shot('09_response_proposed');

  const execute = page.getByRole('button', { name: 'Execute approved actions' });
  if (await execute.count()) {
    await execute.click();
    await idle(1600);
    await scrollToHeading('Execution results', 80);
    await shot('10_response_executed');
  } else {
    notes.push('no execute button on SCN-001');
  }

  // ---- 4. Cross-module scenario SCN-005 ----------------------------------
  await go('Scenario Laboratory');
  await choose('Scenario', 'SCN-005 · Privilege Escalation Investigation');
  await page.getByRole('button', { name: 'Run scenario' }).click();
  await idle(1800);
  await scrollElement(page.getByText('Scenario', { exact: true }).first(), 55);
  await shot('11_scn005_result');

  // ---- 5. Knowledge base --------------------------------------------------
  await go('Knowledge Base');
  await scrollMainTop();
  await shot('02_knowledge_base');

  const auth04 = page.getByText('AUTH-04 · Possible Account Compromise', { exact: true }).first();
  await auth04.scrollIntoViewIfNeeded();
  await auth04.click();
  await idle(700);
  await scrollElement(auth04, 70);
  await shot('03_rule_auth04');

  await scrollToHeading('Condition inventory', 70);
  await shot('04_condition_inventory');

  // ---- 6. Manual investigation: invalid target ---------------------------
  await go('New Investigation');
  await scrollMainTop();
  await shot('12_new_investigation');

  await numberField('Failed login attempts', 25);
  await choose('Successful login after failures', 'True');
  await choose('Unusual login location', 'True');
  const account = page.getByLabel('Account ID');
  await account.fill('USER-999');
  await account.blur();
  await wait(400);
  await page.getByRole('button', { name: 'Run Investigation' }).click();
  await idle(1800);
  await scrollElement(page.getByText('Authentication & Account Security', { exact: true }).first(), 70);
  await shot('14_edge_invalid_target');

  // blocked actions on the response page
  await go('Response Center');
  const blocked = page.getByText(/Blocked actions \(/).first();
  if (await blocked.count()) {
    await blocked.scrollIntoViewIfNeeded();
    await blocked.click();
    await idle(700);
    await scrollElement(blocked, 120);
  }
  await shot('14b_blocked_actions');

  // ---- 7. Below-threshold manual investigation ---------------------------
  await go('New Investigation');
  await numberField('Failed login attempts', 3);
  await page.getByRole('button', { name: 'Run Investigation' }).click();
  await idle(1800);
  await scrollElement(page.getByText('Authentication & Account Security', { exact: true }).first(), 70);
  await shot('15_edge_no_finding');

  // ---- 8. History ---------------------------------------------------------
  await go('Investigation History');
  await scrollMainTop();
  await shot('13_history');

  await page.getByRole('combobox', { name: 'Inspect investigation' }).click();
  await wait(500);
  await page.getByRole('option', { name: /Privilege Escalation Investigation/ }).first().click();
  await idle();
  await scrollToHeading('Findings', 80);
  await shot('13b_history_detail');

  // ---- 9. Populated overview ---------------------------------------------
  await go('Security Overview');
  await scrollMainTop();
  await wait(2500);
  await shot('01_overview');

  return { done, notes };
}
