// Render tiap diagram HTML/SVG menjadi PNG (skala 3x). Butuh Playwright + Chromium.
let pw;
try { pw = require('playwright'); } catch (e) { pw = require('/opt/node22/lib/node_modules/playwright'); }
const { chromium } = pw;
const fs = require('fs'); const path = require('path');
(async () => {
  const meta = JSON.parse(fs.readFileSync(path.join(__dirname, 'meta.json')));  // dibuat oleh: python3 diagrams.py
  const browser = await chromium.launch();
  for (const [name, [w, h]] of Object.entries(meta)) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 3 });
    await page.goto('file://' + path.join(__dirname, name + '.html'));
    await page.locator('svg').screenshot({ path: path.join(__dirname, name + '.png') });
    await page.close();
  }
  await browser.close();
  console.log('rendered', Object.keys(meta).length);
})();
