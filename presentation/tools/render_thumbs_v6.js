// render deck_live slides (ids from argv) at 1920x1080 with blob images mapped to local files
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const S = __dirname, R = '/home/user/me5412-bedexit-proposal/presentation', D = S + '/deck_live/project/slides', A = S + '/deck_assets';
const bj = JSON.parse(fs.readFileSync(R + '/animations/blobs.json'));
const V57 = { cad_3d_shell: '3d_a_shell.png', cad_3d_open: '3d_b_open.png', cad_poses: '3d_poses_strip.png', cad_joint: '3d_d_joint.png', fig_section: 'fig_section.png', fig_side: 'fig_side.png', fig_top: 'fig_top.png',
  md_target: 'md_target.png', md_candidates: 'md_candidates.png', md_synthesis: 'md_synthesis.png', dw_assembly: 'dw_assembly_flush.png', dw_C1: 'dw_C1.png', dw_J3: 'dw_J3.png', dw_S7: 'dw_S7.png', dw_J1: 'dw_J1.png' };
const MAP = {};
for (const [n, u] of Object.entries(bj)) { const id = u.split('/').pop(); const c = [R + '/animations/' + n + '.png', R + '/animations/' + n + '.gif', V57[n] ? R + '/assets_v57/' + V57[n] : '']; MAP[id] = c.find(f => f && fs.existsSync(f)); }
Object.assign(MAP, { cce52c77347373ea793ff779e129e5f9: A + '/icons/opt_lowbed.svg', d3b35427318241aae1961dad250d24c9: A + '/icons/opt_highbed.svg', '5040f5f7cf3e67828d619170e1e44709': A + '/icons/opt_vertical.svg',
  '345c913f14d872c0e69ea4b5d657dee8': A + '/icons/opt_ours.svg', '18995dee61fcd2688574845019f6b8fd': A + '/icons/prior_liftchair.svg', b1e4fd0707022517d24ae7f55e36dffb: A + '/icons/prior_highbed.svg',
  '3365a26b887c8155c3f4a211646945c4': A + '/icons/prior_cushion.svg', '9f3e5f735f958bd461f2acde3ce0f972': A + '/icons/prior_research.svg', '91ed3c44eefc6bb91478790accb69e2e': A + '/still_film.jpg',
  f82cfc5199a8b9a9527dc9dcdd41b6b5: A + '/still_motion.jpg', d1a7c20cadc9371c21641845ceae9374: A + '/still_sensing.jpg' });
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const sid of process.argv.slice(2)) {
    let h = fs.readFileSync(`${D}/${sid}.html`, 'utf8').replace(/<aside>[\s\S]*?<\/aside>/, '');
    const miss = [];
    h = h.replace(/src="\/_blob\/([0-9a-f]+)"/g, (m, id) => { if (MAP[id]) return `src="file://${MAP[id]}"`; miss.push(id); return 'src=""'; });
    const doc = `<!doctype html><meta charset=utf-8><style>*{margin:0;padding:0;box-sizing:border-box} body{width:1920px;height:1080px;overflow:hidden} section{position:relative;width:1920px;height:1080px} ul,ol{padding-left:1.2em} th{text-align:left}</style>${h}`;
    fs.writeFileSync(S + '/thumbs/tmp.html', doc); await p.goto('file://' + S + '/thumbs/tmp.html'); await p.waitForTimeout(500);
    // overflow check: any text element whose bottom passes 1080-64 or right edge 1920-128 (except pinned footers)
    const over = await p.evaluate(() => [...document.querySelectorAll('section *')].filter(e => { const r = e.getBoundingClientRect(); return (r.bottom > 1080 || r.right > 1920) && r.width > 0; }).map(e => e.tagName + ':' + Math.round(e.getBoundingClientRect().bottom) + ':' + (e.textContent || '').slice(0, 20)));
    await p.screenshot({ path: `${S}/thumbs/${sid}.png` }); console.log(sid, miss.length ? 'MISSING ' + miss.join(',') : '', over.length ? 'OVERFLOW ' + over.slice(0, 3).join(' | ') : 'ok');
  }
  await b.close();
})();
