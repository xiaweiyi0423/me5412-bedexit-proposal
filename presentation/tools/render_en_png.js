// Render the English slides (presentation/slides_en, blobs mapped through .work/en_build/plan.json) to PNG at 1.5x,
// and record where each video poster sits. Usage: node render_en_png.js <out_dir>
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const R = path.resolve(__dirname, '..', '..'), P = R + '/presentation';
const plan = JSON.parse(fs.readFileSync(R + '/.work/en_build/plan.json'));
const order = JSON.parse(fs.readFileSync(P + '/deck.json')).order.filter(s => fs.existsSync(`${P}/slides_en/${s}.html`));
(async () => {
  const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1.5 });
  const meta = [];
  for (const sid of order) {
    const raw = fs.readFileSync(`${P}/slides_en/${sid}.html`, 'utf8');
    const notes = (raw.match(/<aside>([\s\S]*?)<\/aside>/) || [, ''])[1].trim();
    const vids = [];
    let h = raw.replace(/<aside>[\s\S]*?<\/aside>/, '').replace(/<img ([^>]*?)src="\/_blob\/([0-9a-f]{32})"([^>]*?)>/g, (m, a, id, c) => {
      const all = a + c, vm = all.match(/data-video="\/_blob\/([0-9a-f]{32})"/);
      const f = plan.map[id] ? path.join(R, plan.map[id]) : '';
      if (vm) vids.push({ poster: plan.map[id], video: plan.map[vm[1]] });
      return `<img ${a}src="file://${f}"${c}${vm ? ` data-vid="${vids.length - 1}"` : ''}>`;
    });
    const doc = `<!doctype html><meta charset=utf-8><style>*{margin:0;padding:0;box-sizing:border-box} body{width:1920px;height:1080px;overflow:hidden;font-family:'Inter',sans-serif} section{position:relative;width:1920px;height:1080px} ul,ol{padding-left:1.2em} th{text-align:left}</style>${h}`;
    const tmp = path.join(out, '_tmp.html'); fs.writeFileSync(tmp, doc); await p.goto('file://' + path.resolve(tmp)); await p.waitForTimeout(500);
    const boxes = await p.evaluate(() => [...document.querySelectorAll('img[data-vid]')].map(e => { const r = e.getBoundingClientRect(); return { i: +e.dataset.vid, x: r.x, y: r.y, w: r.width, h: r.height }; }));
    boxes.forEach(bx => Object.assign(vids[bx.i], bx));
    await p.screenshot({ path: path.join(out, sid + '.png') });
    meta.push({ id: sid, notes, videos: vids });
  }
  fs.writeFileSync(path.join(out, 'meta.json'), JSON.stringify(meta, null, 1)); await b.close(); console.log('rendered', meta.length);
})();
