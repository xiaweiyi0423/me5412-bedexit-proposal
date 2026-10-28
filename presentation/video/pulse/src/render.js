// node render.js prev t0 t1 ...  -> prev/p_<t>.png ;  node render.js video from to -> frames/f%04d.png (resumable)
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const HERE = __dirname; const [mode, ...rest] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto('file://' + path.join(HERE, 'pulse.html')); await p.waitForFunction(() => document.title === 'ready', null, { timeout: 120000 });
  if (mode === 'video') {
    const fps = 30, from = +rest[0], to = +rest[1]; const dir = path.join(HERE, 'frames'); fs.mkdirSync(dir, { recursive: true });
    for (let i = from; i < to; i++) { const f = path.join(dir, `f${String(i).padStart(4, '0')}.png`); if (fs.existsSync(f)) continue;
      await p.evaluate(t => window.renderAt(t), (i + 0.5) / fps); await p.screenshot({ path: f }); if (i % 30 === 0) console.log('frame', i); }
  } else {
    for (const t of rest.map(Number)) { await p.evaluate(tt => window.renderAt(tt), t); await p.screenshot({ path: path.join(HERE, 'prev', `p_${t.toFixed(2)}.png`) }); }
  }
  if (errs.length) console.log('ERRORS', errs.slice(0, 8));
  await b.close();
})();
