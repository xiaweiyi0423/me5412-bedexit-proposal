// Render each slide fragment at 1920x1080. Blob images are swapped for local equivalents where known.
const { chromium } = require('playwright');
const fs = require('fs');
const ROOT = require('path').resolve(__dirname, '..', '..');
const OUT = process.argv[2];
const deck = JSON.parse(fs.readFileSync(ROOT + '/presentation/deck.json'));
// v5.2: images uploaded for the seat slides map back to local files through animations/blobs.json (name -> /_blob/ url)
let BLOBS = {}; try { const bj = JSON.parse(fs.readFileSync(ROOT + '/presentation/animations/blobs.json')); for (const [n, u] of Object.entries(bj)) BLOBS[u] = `presentation/animations/${n}${n === 'seat_rise' ? '.gif' : '.png'}`; } catch (e) {}
const LOCAL = { sizing: 'model/calc_v12/lift_sizing.png', stability: 'model/calc_v12/stability_top.png',
  speed: 'model/calc_v12/controller_timelines.png', statemachine: 'model/calc_v12/state_machine.png',
  motion: 'presentation/animations/use_sequence.gif', risk: 'presentation/animations/safety_sitback.gif' };
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const [i, sid] of deck.order.entries()) {
    let h = fs.readFileSync(`${ROOT}/presentation/slides/${sid}.html`, 'utf8').replace(/<aside>[\s\S]*?<\/aside>/, '');
    h = h.replace(/<img src="(\/_blob\/[0-9a-f]+)" alt="([^"]*)"/g, (m, url, alt) => BLOBS[url] ? `<img src="file://${ROOT}/${BLOBS[url]}" alt="${alt}"` : LOCAL[sid]
      ? `<img src="file://${ROOT}/${LOCAL[sid]}" alt="${alt}"`
      : `<img src="data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400'><rect width='100%' height='100%' fill='#ddd'/><text x='20' y='200' font-size='22' font-family='WenQuanYi Zen Hei'>[图] ${alt.slice(0,24)}</text></svg>`)}" alt="${alt}"`);
    const doc = `<!doctype html><meta charset=utf-8><style>*{margin:0;box-sizing:border-box} body{width:1920px;height:1080px;overflow:hidden;font-family:'Noto Sans SC','WenQuanYi Zen Hei',sans-serif} section{position:relative;width:1920px;height:1080px}</style>${h}`;
    fs.writeFileSync(`${OUT}/tmp.html`, doc);
    await p.goto('file://' + OUT + '/tmp.html'); await p.waitForTimeout(400);
    await p.screenshot({ path: `${OUT}/img/full_${String(i + 1).padStart(2, '0')}_${sid}.png` });
  }
  await b.close();
})();
