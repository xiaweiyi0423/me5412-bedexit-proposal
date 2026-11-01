// Render deck slides locally at 1920x1080 (for checking layout and for talk-guide thumbnails).
// Usage: node presentation/tools/render_slide_local.js <out_dir> <slide_id> [...]
//   Reads presentation/slides/<id>.html. Images: src="/_blob/<id>" is mapped to a local file through
//   presentation/animations/blobs.json (+ assets_v57 / assets_v6 copies); src="ASSET:<repo-relative path>" is a
//   not-yet-uploaded local file. Prints, per slide: missing images and any element that spills past the slide edge
//   or (for non-pinned elements) into the bottom 160 px margin.
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const R = path.resolve(__dirname, '..', '..'), P = R + '/presentation';
const bj = JSON.parse(fs.readFileSync(P + '/animations/blobs.json'));
const ALT = { cad_3d_shell: 'assets_v57/3d_a_shell.png', cad_3d_open: 'assets_v57/3d_b_open.png', cad_poses: 'assets_v57/3d_poses_strip.png', cad_joint: 'assets_v57/3d_d_joint.png',
  fig_section: 'assets_v57/fig_section.png', fig_side: 'assets_v57/fig_side.png', fig_top: 'assets_v57/fig_top.png', md_target: 'assets_v57/md_target.png', md_candidates: 'assets_v57/md_candidates.png',
  md_synthesis: 'assets_v57/md_synthesis.png', dw_assembly: 'assets_v57/dw_assembly_flush.png', dw_C1: 'assets_v57/dw_C1.png', dw_J3: 'assets_v57/dw_J3.png', dw_S7: 'assets_v57/dw_S7.png', dw_J1: 'assets_v57/dw_J1.png',
  fea_c1: 'assets_v57/fig_fea_c1.png', fea_beam: 'assets_v57/fig_fea_beam.png', fea_house: 'assets_v57/fig_fea_house.png', fea_rail: 'assets_v57/fig_fea_rail.png',
  still_film: 'assets_v6/still_film.jpg', still_motion: 'assets_v6/still_motion.jpg', still_sensing: 'assets_v6/still_sensing.jpg' };
const MAP = {};
for (const [n, u] of Object.entries(bj)) {
  const id = u.split('/').pop();
  const c = [ALT[n] && P + '/' + ALT[n], n.startsWith('v7_') && P + '/assets_v7/' + n.slice(3) + '.png', P + '/assets_v6/icons/' + n + '.svg', P + '/animations/' + n + '.png', P + '/animations/' + n + '.gif'].filter(Boolean);
  MAP[id] = c.find(f => fs.existsSync(f));
}
(async () => {
  const [out, ...ids] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const sid of ids) {
    let h = fs.readFileSync(`${P}/slides/${sid}.html`, 'utf8').replace(/<aside>[\s\S]*?<\/aside>/, '');
    const miss = [];
    h = h.replace(/src="\/_blob\/([0-9a-f]+)"/g, (m, id) => { if (MAP[id]) return `src="file://${MAP[id]}"`; miss.push(id); return 'src=""'; });
    h = h.replace(/src="ASSET:([^"]+)"/g, (m, f) => { const fp = path.resolve(R, f); if (!fs.existsSync(fp)) miss.push(f); return `src="file://${fp}"`; });
    const doc = `<!doctype html><meta charset=utf-8><style>*{margin:0;padding:0;box-sizing:border-box} body{width:1920px;height:1080px;overflow:hidden;font-family:'Noto Sans SC','WenQuanYi Zen Hei',sans-serif} section{position:relative;width:1920px;height:1080px} ul,ol{padding-left:1.2em} th{text-align:left}</style>${h}`;
    const tmp = path.join(out, '_tmp.html'); fs.writeFileSync(tmp, doc); await p.goto('file://' + path.resolve(tmp)); await p.waitForTimeout(600);
    const bad = await p.evaluate(() => [...document.querySelectorAll('section *')].filter(e => {
      const r = e.getBoundingClientRect(); if (!r.width) return false;
      let pinned = false; for (let x = e; x && x.tagName !== 'SECTION'; x = x.parentElement) if (getComputedStyle(x).position === 'absolute') pinned = true;
      return r.right > 1921 || r.bottom > 1081 || (!pinned && r.bottom > 1080 - 150 && e.textContent.trim());
    }).map(e => e.tagName + '@' + Math.round(e.getBoundingClientRect().bottom) + ':' + e.textContent.trim().slice(0, 16)));
    await p.screenshot({ path: path.join(out, sid + '.png') });
    console.log(sid, miss.length ? 'MISSING ' + miss.join(',') : 'images ok', bad.length ? 'SPILL ' + bad.slice(0, 4).join(' | ') : 'layout ok');
  }
  await b.close();
})();
