// Screenshots of page/seat_1dof.html (v5) for the round-2 Gemini audit. Usage: node shots_v5.js <out_dir>
const { chromium } = require('playwright');
(async () => {
  const out = process.argv[2]; const fs = require('fs'); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.goto('file://' + require('path').resolve(__dirname, '../../seat_1dof.html')); await p.waitForTimeout(1500);
  await p.evaluate(() => { document.querySelector('nav.steps').style.position = 'static'; });
  const top = await p.$('header.top'); await top.screenshot({ path: out + '/00_header.png' });
  const ids = ['plan', 'posture', 'assist', 'seat', 'mech', 'layout', 'cushion', 'check', 'limits', 'audit', 'v5'];
  for (let i = 0; i < ids.length; i++) { const e = await p.$('#' + ids[i]); await e.screenshot({ path: `${out}/${String(i + 1).padStart(2, '0')}_${ids[i]}.png` }); }
  for (const c of ['u', 'z1', 'z2']) {
    await p.click(`#cushTabs button[data-c="${c}"]`);
    for (const v of [150, 400, 700]) {
      await p.$eval('#prog2', (el, v) => { el.value = v; el.dispatchEvent(new Event('input')); }, v); await p.waitForTimeout(150);
      const e = await p.$('#svgMech'); await e.screenshot({ path: `${out}/20_mech_${c}_${String(v / 10).padStart(2, '0')}pct.png` });
      const e2 = await p.$('#svgCush'); await e2.screenshot({ path: `${out}/21_cush_${c}_${String(v / 10).padStart(2, '0')}pct.png` });
    }
  }
  for (const id of ['svgSag', 'svgFront', 'svgTop', 'svgZone']) { const e = await p.$('#' + id); await e.screenshot({ path: `${out}/30_${id}.png` }); }
  await b.close();
})();
