/*
 * Print a local HTML file to PDF using the Chromium build that patchright pins.
 * Usage: node scripts/print_pdf.cjs <input.html> <output.pdf>
 */
const path = require('node:path');
const fs = require('node:fs');

const RUNTIME = process.env.CIARES_PATCHRIGHT
  || 'C:/Users/muham/.vscode/extensions/danielsanmedium.dscodegpt-3.24.81/standalone/node_modules/patchright';
const CHROME = process.env.CIARES_CHROME
  || 'C:/Users/muham/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe';

const { chromium } = require(RUNTIME);

(async () => {
  const input = path.resolve(process.argv[2]);
  const output = path.resolve(process.argv[3]);
  const plain = process.argv[4] === 'plain';
  if (!fs.existsSync(input)) throw new Error(`missing input: ${input}`);

  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const page = await browser.newPage();
  await page.goto('file:///' + input.replace(/\\/g, '/'), { waitUntil: 'load' });
  await page.emulateMedia({ media: 'print' });
  await page.waitForTimeout(400);

  const footer = `
    <div style="width:100%; font-family: 'Segoe UI', Arial, sans-serif; font-size:7.5pt;
                color:#6b7a90; padding:0 16mm; display:flex; justify-content:space-between;">
      <span>CIARES — Technical and Code Explanation</span>
      <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
    </div>`;
  const header = `
    <div style="width:100%; font-family: 'Segoe UI', Arial, sans-serif; font-size:7pt;
                color:#9aa7b8; padding:0 16mm; text-align:right;">
      Cybersecurity Incident Analysis and Response Expert System
    </div>`;

  await page.pdf({
    path: output,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: !plain,
    headerTemplate: header,
    footerTemplate: footer,
    margin: { top: '16mm', bottom: '16mm', left: '15mm', right: '15mm' },
    preferCSSPageSize: false,
  });
  await browser.close();
  console.log(`wrote ${output} (${(fs.statSync(output).size / 1024 / 1024).toFixed(2)} MB)`);
})().catch((error) => { console.error(error); process.exit(1); });
