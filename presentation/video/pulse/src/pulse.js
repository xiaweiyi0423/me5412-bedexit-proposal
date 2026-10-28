// "Pulse" cut of the bed-exit seat film: 36 s at 120 BPM (beat = 0.5 s). renderAt(t) draws the frame at time t; no clocks.
// Layers: #bg 2D canvas (backgrounds, bed, floor) -> three.js (CAD device, transparent clear) -> #fg 2D canvas (figure, lines) -> #txt DOM type.
// World: metres, x forward from the bed edge, y along the bed (+y = head side), z up.
const W = 1920, H = 1080, D = window.DATA, BEAT = 0.5, DUR = 36;
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t, lerpA = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const eo = (a, b, x) => { const t = clamp((x - a) / (b - a)); return 1 - Math.pow(1 - t, 3); };        // ease-out cubic
const eback = (a, b, x) => { const t = clamp((x - a) / (b - a)), c = 1.6; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
const win = (t, a, b, fi = 0.12, fo = 0.12) => Math.min(ss(a, a + fi, t), 1 - ss(b - fo, b, t));
const C = { ink: '#07090D', ink2: '#0E131A', paper: '#F2F4F7', acc: '#19D3F0', accL: '#0097B8', amb: '#FFB020', red: '#FF4D3A', white: '#FFFFFF', grey: '#8A96A6' };

// ------------------------------------------------------------------ type layer
const TX = {}, txt = document.getElementById('txt');
function T(id, html, css) { const e = document.createElement('div'); e.className = 't ' + (css.cls || ''); e.innerHTML = html; Object.assign(e.style, css.s || {}); txt.appendChild(e); TX[id] = e; return e; }
function show(id, o = {}) {           // o: {op, x, y, sc, dx, dy, blur, ls, col, ax (anchor 0..1)}
  const e = TX[id]; e.style.opacity = o.op ?? 1; if (o.x !== undefined) e.style.left = o.x + 'px'; if (o.y !== undefined) e.style.top = o.y + 'px';
  const ax = o.ax ?? 0, ay = o.ay ?? 0;
  e.style.transform = `translate(${-ax * 100}%,${-ay * 100}%) translate(${o.dx || 0}px,${o.dy || 0}px) scale(${o.sc ?? 1})`;
  e.style.transformOrigin = `${ax * 100}% ${ay * 100}%`;
  e.style.filter = o.blur ? `blur(${o.blur}px)` : 'none'; if (o.ls !== undefined) e.style.letterSpacing = o.ls + 'em'; if (o.col) e.style.color = o.col;
}
const big = (px, w = 900) => ({ fontSize: px + 'px', fontWeight: w, lineHeight: 1.05 });
const mono = (px, col = C.grey) => ({ cls: 'mono', s: { fontSize: px + 'px', color: col } });
// cold open
T('a_tagL', 'ME5412 · ROBOTICS FOR HEALTHCARE', mono(24)); T('a_tagR', 'GROUP 16', mono(24));
T('a_tc', '', mono(24, C.acc));
T('a_h', '夜里，从床沿站起来', { s: big(104) });
['腿力', '床高', '头晕'].forEach((w, i) => T('a_c' + i, w, { s: { ...big(44, 700), padding: '10px 26px', border: '2px solid rgba(255,255,255,.55)', borderRadius: '999px' } }));
// problem
T('b_l1', '床低', { s: { ...big(200), color: C.ink } }); T('b_l2', '→ 站不起来', { s: { ...big(76, 700), color: C.ink } });
T('b_h1', '床高', { s: { ...big(200), color: C.ink } }); T('b_h2', '→ 脚踩不实', { s: { ...big(76, 700), color: C.ink } });
T('b_tag', 'PROBLEM / 问题', mono(24, '#5A6575')); T('b_x', '✕', { s: { ...big(120), color: C.red } }); T('b_x2', '✕', { s: { ...big(120), color: C.red } });
T('b_sum', '固定高度的床，两头难兼顾', { s: { ...big(54, 700), color: C.ink } });
// pivot + title
T('c_1', '平时，<span style="color:#19D3F0">和床一样低</span>。', { s: big(112) });
T('c_2', '起身时，<span style="color:#19D3F0">跟着你升起来</span>。', { s: big(112) });
T('d_t', '床边起身台', { s: { ...big(232), backgroundImage: 'linear-gradient(100deg,#fff 0%,#fff 40%,#9ff3ff 48%,#fff 56%,#fff 100%)', backgroundSize: '300% 100%', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } });
T('d_e', 'BED-EXIT SEAT', { cls: 'lat', s: { fontSize: '62px', fontWeight: 800, color: C.acc, letterSpacing: '.32em' } });
T('d_g', 'ME5412 ROBOTICS FOR HEALTHCARE · GROUP 16', mono(24));
// hero
const PARTS_LAB = ['底座 · 踏板', '导轨安装板 · 连杆支座', '斜导轨 + 滚珠丝杠', '电机 · 失电制动', '滑块', '倾角连杆', '座板 · 分区坐垫', 'L 形扶手 · 握把开关'];
T('e_tag', 'HARDWARE / 结构', mono(24));
PARTS_LAB.forEach((w, i) => T('e_l' + i, `<span class="mono" style="color:#19D3F0;font-size:24px;margin-right:18px">0${i + 1}</span>${w}`, { s: { fontSize: '36px', fontWeight: 700 } }));
T('e_big', '一个电机<br><span style="color:#19D3F0">一个自由度</span>', { s: big(96) });
T('e_sub', 'MOTOR → BELT → BALL SCREW → CARRIAGE', mono(26, '#A8B4C4'));
// mechanism
T('f_tag', 'MOTION / 运动', mono(24));
T('f_1', '座板不是直上直下', { s: big(84) });
T('f_2', '前移 · 上升 · 前倾<br><span style="font-size:52px;font-weight:700;color:#A8B4C4">跟着大腿一起走</span>', { s: big(84) });
T('f_3', '人站稳，<span style="color:#19D3F0">座板停住</span>', { s: big(84) });
['前移', '上升', '前倾'].forEach((w, i) => T('f_a' + i, w, { s: { ...big(40, 700), color: C.acc } }));
// how to
T('g_tag', 'HOW TO / 用法', mono(24, '#5A6575'));
const STEPS = [['挪上座板', '座板和床一样高，平移过去'], ['握紧开关', '握紧才升'], ['一起起身', '座板托着人前移、上升、前倾'], ['松手即停', '座板停在原位，坐回也接得住']];
STEPS.forEach(([a, b], i) => {
  T('g_n' + i, '0' + (i + 1), { cls: 'lat', s: { fontSize: '210px', fontWeight: 900, color: 'transparent', WebkitTextStroke: '3px #07090D', lineHeight: 1 } });
  T('g_a' + i, a, { s: { ...big(96), color: C.ink } });
  T('g_b' + i, b, { s: { ...big(40, 500), color: '#3A4554' } });
});
T('g_stop', 'STOP', { cls: 'lat', s: { fontSize: '44px', fontWeight: 900, color: '#fff', background: C.red, padding: '6px 18px', borderRadius: '8px', letterSpacing: '.08em' } });
// sensing
T('h_tag', 'SENSING / 传感', mono(24));
T('h_1', '四处测力，确认人准备好了', { s: big(76) });
const SENS = [['座下测力', '坐稳了没有'], ['横杆测力', '手在不在'], ['握把开关', '握紧才升'], ['踏板测力', '脚踩实了没有']];
SENS.forEach(([a, b], i) => T('h_s' + i, `<div style="font-size:38px;font-weight:900">${a}</div><div style="font-size:28px;font-weight:500;color:#A8B4C4;margin-top:4px">${b}</div>`, { s: {} }));
T('h_2', '握紧才升 · 松手即停 · <span style="color:#19D3F0">失电制动</span>', { s: big(76) });
// end
T('i_t', '床边起身台', { s: big(176) });
T('i_s', '平时和床一样低 · 起身时跟着你升起来 · 松手就停', { s: { ...big(40, 500), color: '#C9D3DF' } });
T('i_g', 'ME5412 ROBOTICS FOR HEALTHCARE · GROUP 16', mono(24));

// ------------------------------------------------------------------ 2D canvases
const bg = document.getElementById('bg').getContext('2d'), fg = document.getElementById('fg').getContext('2d');
function ecgShape(u) { const g = (m, s, a) => a * Math.exp(-((u - m) ** 2) / (2 * s * s));
  return g(-0.12, 0.025, 0.12) + g(-0.028, 0.008, -0.16) + g(0, 0.011, 1.0) + g(0.027, 0.010, -0.32) + g(0.16, 0.04, 0.22); }
const ecgAt = (tt, gate = () => 1) => { const b = Math.round(tt / BEAT) * BEAT; return ecgShape(tt - b) * gate(b); };
function drawECG(g, o) {     // sweep trace: x0..head, value from times t0 + (x - x0)/speed
  const { x0, y0, t0, t, speed, amp, col, gate } = o; const head = Math.min(o.x1 ?? W, x0 + (t - t0) * speed); if (head <= x0) return;
  g.save(); g.lineJoin = 'round'; g.lineCap = 'round';
  const path = () => { g.beginPath(); for (let x = x0; x <= head; x += 2) { const v = ecgAt(t0 + (x - x0) / speed, gate); x === x0 ? g.moveTo(x, y0 - amp * v) : g.lineTo(x, y0 - amp * v); } };
  const fade = g.createLinearGradient(Math.max(x0, head - (o.tail || 1e9)), 0, head, 0); fade.addColorStop(0, col.replace('1)', '0)')); fade.addColorStop(1, col);
  g.strokeStyle = o.tail ? fade : col; g.globalAlpha = 0.22; g.lineWidth = 14; g.shadowColor = col; g.shadowBlur = 0; path(); g.stroke();
  g.globalAlpha = 1; g.lineWidth = 3.2; path(); g.stroke();
  const hv = ecgAt(t0 + (head - x0) / speed, gate); g.fillStyle = '#fff'; g.shadowColor = col; g.shadowBlur = 30; g.beginPath(); g.arc(head, y0 - amp * hv, 7, 0, 7); g.fill(); g.restore();
}
function fillBG(col) { bg.fillStyle = col; bg.fillRect(0, 0, W, H); }
function vignette(g, a = 0.55) { const r = g.createRadialGradient(W / 2, H / 2, 300, W / 2, H / 2, 1250); r.addColorStop(0, 'rgba(0,0,0,0)'); r.addColorStop(1, `rgba(0,0,0,${a})`); g.fillStyle = r; g.fillRect(0, 0, W, H); }
function grid(g, col, step = 60, a = 0.06) { g.save(); g.strokeStyle = col; g.globalAlpha = a; g.lineWidth = 1; g.beginPath(); for (let x = 0; x <= W; x += step) { g.moveTo(x + 0.5, 0); g.lineTo(x + 0.5, H); } for (let y = 0; y <= H; y += step) { g.moveTo(0, y + 0.5); g.lineTo(W, y + 0.5); } g.stroke(); g.restore(); }

// ------------------------------------------------------------------ figure (flat pictogram) from the 2D rise model
const P = D.pose, [Ls, Lt, Ltr, Lua, Lfa] = P.L, FOOT = P.foot, FR = P.frames, F0 = FR[0], DZ0 = F0.sink, Q0 = D.mech.Q0;
const NSEAT = FR.filter(f => f.seat).length, BAR = D.bar, HAND_BAR = [BAR.x - 0.012, BAR.z + 0.028];
function kneeIK(Hp, An) { const dx = Hp[0] - An[0], dz = Hp[1] - An[1]; let Lr = Math.hypot(dx, dz); Lr = Math.min(Lr, Ls + Lt - 1e-4);
  const a = Math.atan2(dz, dx), b = Math.acos(clamp((Ls * Ls + Lr * Lr - Lt * Lt) / (2 * Ls * Lr), -1, 1));
  const c = [-1, 1].map(s => [An[0] + Ls * Math.cos(a + s * b), An[1] + Ls * Math.sin(a + s * b)]); return c[0][0] > c[1][0] ? c[0] : c[1]; }
function elbowIK(S, Hd) { const dx = Hd[0] - S[0], dz = Hd[1] - S[1]; let L = Math.hypot(dx, dz); const l1 = Lua, l2 = Lfa * 0.93; L = Math.min(L, l1 + l2 - 1e-3);
  const a = Math.atan2(dz, dx), b = Math.acos(clamp((l1 * l1 + L * L - l2 * l2) / (2 * l1 * L), -1, 1));
  const c = [-1, 1].map(s => [S[0] + l1 * Math.cos(a + s * b), S[1] + l1 * Math.sin(a + s * b)]); return c[0][1] < c[1][1] ? c[0] : c[1]; }
function sunk(fr, dz) { if (dz <= 0) return fr; const Hp = [fr.Hp[0], fr.Hp[1] - dz]; return Object.assign({}, fr, { Hp, K: kneeIK(Hp, fr.A) }); }
function poseAt(k) { k = clamp(k, 0, FR.length - 1); const i = Math.min(FR.length - 2, Math.floor(k)), t = k - i, a = FR[i], b = FR[i + 1];
  const o = { Hp: lerpA(a.Hp, b.Hp, t), K: lerpA(a.K, b.K, t), A: lerpA(a.A, b.A, t), tr: lerp(a.tr, b.tr, t) };
  let seat = null; if (a.seat && b.seat) seat = { Q: lerpA(a.seat.Q, b.seat.Q, t), phi: lerp(a.seat.phi, b.seat.phi, t) }; else if (a.seat) seat = a.seat;
  if (!seat) { const last = FR[NSEAT - 1].seat; seat = { Q: last.Q, phi: last.phi, released: true }; } o.seat = seat; return o; }
function joints(p, hands) {           // p: {Hp, K, A, tr}; hands: [x,z] target or null (lap)
  const tr = p.tr * Math.PI / 180, ut = [Math.sin(tr), Math.cos(tr)], S = [p.Hp[0] + Ltr * ut[0], p.Hp[1] + Ltr * ut[1]];
  const up = [ut[0] * 0.45, ut[1] * 0.45 + 0.55], n = Math.hypot(...up), hd = [S[0] + 0.165 * up[0] / n, S[1] + 0.165 * up[1] / n];
  const lap = [lerp(p.Hp[0], p.K[0], 0.66), lerp(p.Hp[1], p.K[1], 0.66) + 0.07];
  const Hd = hands || lap, E = elbowIK(S, Hd);
  const fz = Math.max(0.025, p.A[1] - 0.04), toe = p.toe || [p.A[0] + 0.72 * FOOT, fz], heel = p.heel || [p.A[0] - 0.2 * FOOT, fz];
  return { H: p.Hp, K: p.K, A: p.A, S, hd, E, Hd, toe, heel };
}
const OFF = document.createElement('canvas'); OFF.width = W; OFF.height = H; const og = OFF.getContext('2d');
function ghostFig(g, J, map, sc, col, fillA = 0.10, lw = 4) {   // outline-only figure so the mechanism stays visible
  og.clearRect(0, 0, W, H); og.globalCompositeOperation = 'source-over'; drawFig(og, J, map, sc, col, col, 1, lw);
  og.globalCompositeOperation = 'destination-out'; drawFig(og, J, map, sc, '#000', '#000', 1, 0); og.globalCompositeOperation = 'source-over';
  g.drawImage(OFF, 0, 0); drawFig(g, J, map, sc, col, col, fillA, 0, true);
}
function drawFig(g, J, map, sc, col, bgc, alpha = 1, grow = 0, noGap = false) {     // map: [x,z] -> [px,py]; sc: px per metre; grow: extra px per stroke
  const m = J2 => map(J2), w = v => v * sc + grow; g.save(); g.globalAlpha = alpha; g.lineCap = 'round'; g.lineJoin = 'round';
  const poly = (pts, lw, c) => { g.strokeStyle = c; g.lineWidth = lw; g.beginPath(); pts.forEach((p, i) => { const q = m(p); i ? g.lineTo(...q) : g.moveTo(...q); }); g.stroke(); };
  poly([J.H, J.S], w(0.135), col);                                              // torso
  g.fillStyle = col; g.beginPath(); g.arc(...m(J.hd), w(0.098) - grow / 2, 0, 7); g.fill();  // head
  if (!noGap && !grow) { poly([J.H, J.K, J.A], w(0.118), bgc); poly([J.heel, J.toe], w(0.085), bgc); }   // gap outline
  poly([J.H, J.K, J.A], w(0.088), col); poly([J.heel, J.toe], w(0.055), col);   // leg + foot
  if (!noGap && !grow) poly([J.S, J.E, J.Hd], w(0.098), bgc); poly([J.S, J.E, J.Hd], w(0.068), col);   // arm
  g.restore();
}

// ------------------------------------------------------------------ three.js: CAD device
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H); renderer.setClearColor(0x000000, 0); renderer.outputEncoding = THREE.sRGBEncoding;
document.getElementById('gl').appendChild(renderer.domElement);
const scene = new THREE.Scene();
const pcam = new THREE.PerspectiveCamera(26, W / H, 0.05, 60); pcam.up.set(0, 0, 1);
const ocam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 30); ocam.up.set(0, 0, 1);
const hemi = new THREE.HemisphereLight(0xdfe8ff, 0x20242c, 0.8); scene.add(hemi);
const key = new THREE.DirectionalLight(0xffffff, 1.2); key.position.set(3, -4, 5); scene.add(key);
const rim = new THREE.DirectionalLight(0x5fe6ff, 1.0); rim.position.set(-3, 4, 2.5); scene.add(rim);
const amb = new THREE.AmbientLight(0xffffff, 0.2); scene.add(amb);
const dev = new THREE.Group(); dev.scale.setScalar(0.001); scene.add(dev);
const G = { fixed: new THREE.Group(), seat: new THREE.Group(), carriage: new THREE.Group(), link: new THREE.Group(), ref: new THREE.Group() };
Object.values(G).forEach(g => dev.add(g));
const b64 = (s, Tt) => { const bin = atob(s), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return new Tt(u.buffer); };
function cls(c) {
  if (c === 'S1' || c === 'S2') return 'cush'; if (/^S/.test(c) || ['J1', 'J4', 'J5'].includes(c)) return 'seatframe';
  if (['C1', 'C2', 'C3', 'D2n', 'J2', 'J3'].includes(c)) return 'carriage'; if (c === 'L1' || c === 'L2') return 'link';
  if (['D1', 'D2', 'D2a', 'L3'].includes(c)) return 'rail'; if (['D3', 'D4', 'D5', 'D6', 'B7'].includes(c)) return 'drive';
  if (['H2', 'H3', 'H4', 'H5'].includes(c)) return 'shell'; if (c === 'H1') return 'plate'; if (c === 'B1a' || c === 'B2b') return 'rubber';
  if (c === 'B5') return 'bar'; if (c === 'BED') return 'bed'; return 'frame';
}
const LOOK = {   // [colour, opacity, metalness, roughness]
  hero: { cush: ['#EEF1F5', 1, 0, .7], seatframe: ['#59636F', 1, .4, .5], carriage: ['#19D3F0', 1, .2, .4], link: ['#19D3F0', 1, .2, .4], rail: ['#C2CAD4', 1, .7, .3], drive: ['#2B3139', 1, .4, .5],
    shell: ['#9FB4CC', 0, 0, .3], plate: ['#3A4350', 1, .3, .6], frame: ['#55606D', 1, .5, .45], rubber: ['#15181D', 1, 0, .9], bar: ['#E9EDF2', 1, .2, .4], bed: ['#ffffff', 0, 0, 1] },
  dark: { cush: ['#EEF1F5', 1, 0, .7], seatframe: ['#59636F', 1, .4, .5], carriage: ['#19D3F0', 1, .2, .4], link: ['#19D3F0', 1, .2, .4], rail: ['#AEB8C4', 1, .6, .35], drive: ['#3A424D', 1, .4, .5],
    shell: ['#9FB4CC', 0, 0, .3], plate: ['#2A313B', 0.55, .3, .6], frame: ['#4A5461', 1, .5, .45], rubber: ['#15181D', 1, 0, .9], bar: ['#E9EDF2', 1, .2, .4], bed: ['#ffffff', 0, 0, 1] },
  light: { cush: ['#FFFFFF', 1, 0, .9], seatframe: ['#C9CFD7', 1, 0, .8], carriage: ['#0FB5D6', 1, 0, .6], link: ['#0FB5D6', 1, 0, .6], rail: ['#8D97A3', 1, 0, .7], drive: ['#59626E', 1, 0, .7],
    shell: ['#ffffff', 0, 0, 1], plate: ['#DDE2E8', 0.6, 0, .9], frame: ['#CDD3DA', 1, 0, .8], rubber: ['#2E333A', 1, 0, .9], bar: ['#1A1F26', 1, 0, .6], bed: ['#ffffff', 0, 0, 1] },
};
const EDGE_LOOK = { hero: ['#8BEFFF', 0.16], dark: ['#8BEFFF', 0.20], light: ['#0A0E14', 0.42] };
const PART = {}, PG = {}, MATS = [], EMATS = [];
for (const p of D.mesh.parts) {
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(b64(p.pos, Float32Array), 3)); g.setIndex(new THREE.BufferAttribute(b64(p.idx, Uint32Array), 1)); g.computeVertexNormals(); g.computeBoundingBox();
  const k = cls(p.code), m = new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, side: k === 'shell' ? THREE.DoubleSide : THREE.FrontSide, emissive: new THREE.Color(0, 0, 0) });
  if (k === 'shell' || k === 'bed') m.depthWrite = false;
  const ms = new THREE.Mesh(g, m), em = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.2 }), el = new THREE.LineSegments(new THREE.EdgesGeometry(g, 28), em);
  const pg = new THREE.Group(); pg.add(ms, el); G[p.group].add(pg); PART[p.code] = ms; PG[p.code] = pg;
  MATS.push({ m, k, code: p.code }); EMATS.push({ m: em, k, code: p.code });
}
let LOOKNOW = 'hero';
function setLook(mode, over = {}) {     // over: {code|class: {op, emis}}
  LOOKNOW = mode; const L = LOOK[mode], E = EDGE_LOOK[mode];
  for (const { m, k, code } of MATS) { const [c, op, mt, r] = L[k]; m.color.set(c); m.metalness = mt; m.roughness = r; const ov = over[code] || over[k] || {};
    m.opacity = (ov.op ?? 1) * op; m.visible = m.opacity > 0.003; m.emissive.set(ov.emis || '#000000'); m.emissiveIntensity = ov.ei ?? 1; }
  for (const { m, k, code } of EMATS) { const ov = over[code] || over[k] || {}; m.color.set(ov.ecol || (k === 'bed' ? '#8BEFFF' : E[0]));
    m.opacity = (ov.eop ?? (k === 'shell' ? E[1] * 0.8 : k === 'bed' ? 0 : E[1])) * (ov.op ?? 1); m.visible = m.opacity > 0.003; }
  const lit = mode === 'light' ? [1.05, 0.55, 0.0, 0.35] : mode === 'dark' ? [0.75, 1.0, 0.7, 0.15] : [0.55, 1.25, 1.1, 0.12];
  hemi.intensity = lit[0]; key.intensity = lit[1]; rim.intensity = lit[2]; amb.intensity = lit[3];
}
// switch on the grip
const SW = new THREE.Vector3(0.700, 0.06, 0.972);
const swM = new THREE.MeshStandardMaterial({ color: C.amb, emissive: new THREE.Color(C.amb), emissiveIntensity: 0.2 });
const sw = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.05, 0.016), swM); sw.position.copy(SW); scene.add(sw);
const glowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d'); const r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(0.25, 'rgba(255,255,255,.5)'); r.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); })();
const swGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: new THREE.Color(C.amb), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0 }));
swGlow.scale.set(0.22, 0.22, 1); swGlow.position.copy(SW); scene.add(swGlow);
function setSwitch(v) { swM.emissiveIntensity = 0.15 + 1.6 * v; swGlow.material.opacity = 0.95 * v; }
// floor disc for the hero shots
const discTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 512; const g = c.getContext('2d'); const r = g.createRadialGradient(256, 256, 0, 256, 256, 256);
  r.addColorStop(0, 'rgba(40,70,95,.95)'); r.addColorStop(0.55, 'rgba(20,34,48,.55)'); r.addColorStop(1, 'rgba(10,14,20,0)'); g.fillStyle = r; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = 'rgba(25,211,240,.35)'; g.lineWidth = 2; g.beginPath(); g.arc(256, 256, 170, 0, 7); g.stroke(); g.globalAlpha = 0.5; g.lineWidth = 1; g.beginPath(); g.arc(256, 256, 214, 0, 7); g.stroke();
  const t = new THREE.CanvasTexture(c); return t; })();
const disc = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 2.8), new THREE.MeshBasicMaterial({ map: discTex, transparent: true, depthWrite: false })); disc.position.set(0.4, 0.05, -0.002); scene.add(disc);

// kinematics: stroke s (mm) -> seat / carriage / link
const K = D.kin, RR = D.mesh.frames.rail_rot_deg * Math.PI / 180, BB = D.mesh.frames.B;
function kinAt(s) { let i = 0; while (i < K.length - 2 && K[i + 1][0] < s) i++; const a = K[i], b = K[i + 1], t = clamp((s - a[0]) / ((b[0] - a[0]) || 1)); return a.map((v, k) => v + t * (b[k] - v)); }
function strokeForQz(zm) { const z = zm * 1000; if (z <= K[0][2]) return 0; for (let i = 0; i < K.length - 1; i++) if (K[i + 1][2] >= z) return lerp(K[i][0], K[i + 1][0], (z - K[i][2]) / (K[i + 1][2] - K[i][2])); return K[K.length - 1][0]; }
function setMech(s, off = {}) {
  const f = kinAt(s), o = k => off[k] || [0, 0, 0];
  G.seat.position.set(f[1] + o('seat')[0], o('seat')[1], f[2] + o('seat')[2]); G.seat.rotation.set(0, f[3] * Math.PI / 180, 0);
  G.carriage.position.set(f[4] + o('carriage')[0], o('carriage')[1], f[5] + o('carriage')[2]); G.carriage.rotation.set(0, RR, 0);
  G.link.position.set(BB[0] + o('link')[0], o('link')[1], BB[1] + o('link')[2]); G.link.rotation.set(0, -Math.atan2(f[7] - BB[1], f[6] - BB[0]), 0); return f;
}
function rise(kf) {     // kf in [-1, 27]: -1..0 foam pre-load, then the rise frames
  if (kf < 0) { const w = kf + 1, Q = lerpA(Q0, F0.seat.Q, w), p = sunk(F0, (1 - w) * DZ0); return { pose: Object.assign({}, p, { tr: F0.tr }), s: strokeForQz(Q[1]) }; }
  const p = poseAt(kf); return { pose: p, s: strokeForQz(p.seat.Q[1]), released: !!p.seat.released };
}
const S_REL = strokeForQz(FR[NSEAT - 1].seat.Q[1]);

// cameras
function sideView(cx, cz, hh) {     // orthographic side view from -y; returns map [x,z] -> px and px/m
  const hw = hh * W / H; ocam.left = -hw; ocam.right = hw; ocam.top = hh; ocam.bottom = -hh; ocam.updateProjectionMatrix();
  ocam.position.set(cx, -8, cz); ocam.lookAt(cx, 0, cz); const sc = (H / 2) / hh;
  return { cam: ocam, sc, map: p => [W / 2 + (p[0] - cx) * sc, H / 2 - (p[1] - cz) * sc] };
}
function heroView(az, el, dist, shiftPx = 0) {
  const T0 = new THREE.Vector3(0.40, 0.05, 0.47); pcam.position.set(T0.x + dist * Math.cos(el) * Math.cos(az), T0.y + dist * Math.cos(el) * Math.sin(az), T0.z + dist * Math.sin(el));
  pcam.lookAt(T0); if (shiftPx) pcam.setViewOffset(W, H, shiftPx, 0, W, H); else pcam.clearViewOffset(); pcam.updateProjectionMatrix(); return pcam;
}
function proj(v, cam) { const p = v.clone().project(cam); return [(p.x + 1) / 2 * W, (1 - p.y) / 2 * H]; }
function partAnchor(code, frac = [0.5, 0.5, 0.5]) { const ms = PART[code]; dev.updateMatrixWorld(true); const b = ms.geometry.boundingBox;
  return ms.localToWorld(new THREE.Vector3(lerp(b.min.x, b.max.x, frac[0]), lerp(b.min.y, b.max.y, frac[1]), lerp(b.min.z, b.max.z, frac[2]))); }

// bed + floor in 2D (side views)
function drawBed2D(g, map, sc, top, light, x1 = -1.6) {
  const fill = light ? '#E3E7EC' : '#141A22', line = light ? '#0A0E14' : '#2C3644', matt = light ? '#FFFFFF' : '#1B2330';
  const R = (x0, z0, x1_, z1, f, r = 0) => { const a = map([x0, z1]), b = map([x1_, z0]); g.fillStyle = f; g.strokeStyle = line; g.lineWidth = light ? 3 : 2; g.beginPath(); g.roundRect(a[0], a[1], b[0] - a[0], b[1] - a[1], r * sc); g.fill(); g.stroke(); };
  R(-0.08, 0, -0.02, top - 0.17, fill); R(x1, 0, x1 + 0.06, top - 0.17, fill);
  R(x1, top - 0.24, 0, top - 0.14, fill, 0.01); R(x1 + 0.01, top - 0.15, -0.005, top, matt, 0.035);
}
function floor2D(g, map, col, a = 1) { const y = map([0, 0])[1]; g.save(); g.globalAlpha = a; g.strokeStyle = col; g.lineWidth = 3; g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); g.restore(); }

// ------------------------------------------------------------------ sections
function resetFrame() { for (const k in TX) TX[k].style.opacity = 0; bg.clearRect(0, 0, W, H); fg.clearRect(0, 0, W, H); renderer.clear(); }
let glOn = false;
function renderGL(cam) { renderer.render(scene, cam); glOn = true; }

function secA(t) {   // 0-4 cold open: monitor sweep
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.10); vignette(bg, 0.7);
  drawECG(fg, { x0: 0, y0: 640, t0: 0, t, speed: 480, amp: 210, col: 'rgba(25,211,240,1)', tail: 900 });
  show('a_tagL', { x: 80, y: 64, op: ss(0.1, 0.4, t) }); show('a_tagR', { x: 1840, y: 64, ax: 1, op: ss(0.1, 0.4, t) });
  TX.a_tc.textContent = 'T+' + t.toFixed(2).padStart(5, '0') + ' s'; show('a_tc', { x: 1840, y: 1000, ax: 1, op: 0.85 });
  const h = eo(2.0, 2.25, t); show('a_h', { x: 960, y: 330, ax: 0.5, ay: 0.5, op: h, sc: lerp(1.12, 1, h), blur: (1 - h) * 8 });
  for (let i = 0; i < 3; i++) { const u = eback(3.0 + i * 0.25, 3.25 + i * 0.25, t); show('a_c' + i, { x: 960 + (i - 1) * 230, y: 830, ax: 0.5, ay: 0.5, op: clamp(u * 3), sc: u }); }
}
function problemFig(kind, t, tl) {     // tl: local time in the panel
  if (kind === 'low') {
    const top = 0.40, bump = u => Math.max(0, Math.sin(Math.PI * clamp(u / 0.55))) ;
    const b = Math.max(bump(tl - 0.45), bump(tl - 1.2));
    const Hp = [-0.10 + 0.07 * b, top + 0.085 + 0.02 * b], A = [0.33, 0.062], tr = 12 + 42 * b;
    return { top, J: joints({ Hp, K: kneeIK(Hp, A), A, tr }, null), b };
  }
  const top = 0.66, Hp = [-0.10, top + 0.085], sw = 0.06 * Math.sin(tl * 5.2);
  const Kp = [Hp[0] + 0.392 * Math.cos(-0.12), Hp[1] + 0.392 * Math.sin(-0.12)], ang = -Math.PI / 2 + 0.10 + sw, A = [Kp[0] + Ls * Math.cos(ang), Kp[1] + Ls * Math.sin(ang)];
  const toe = [A[0] + 0.15 * Math.cos(-0.75), A[1] + 0.15 * Math.sin(-0.75)], heel = [A[0] - 0.04, A[1] + 0.01];
  return { top, J: joints({ Hp, K: Kp, A, tr: 6, toe, heel }, null) };
}
function secB(t) {   // 4-8 problem, light
  fillBG(C.paper); grid(bg, '#0A0E14', 60, 0.045);
  const sc = 540, wp = ss(5.95, 6.15, t) * W;          // whip between the two panels
  for (const [kind, ox] of [['low', -wp], ['high', W - wp]]) {
    if (ox <= -W || ox >= W) continue; const map = p => [ox + 1180 + p[0] * sc, 960 - p[1] * sc], tl = kind === 'low' ? t - 4 : t - 6;
    const F = problemFig(kind, t, tl); bg.save(); floor2D(bg, map, '#0A0E14'); drawBed2D(bg, map, sc, F.top, true, -1.8); bg.restore();
    drawFig(fg, F.J, map, sc, C.ink, C.paper);
    if (kind === 'high') {   // gap between the toe and the floor
      const a = map(F.J.toe), b = map([F.J.toe[0], 0]); fg.save(); fg.strokeStyle = C.red; fg.lineWidth = 4; fg.setLineDash([12, 10]); fg.globalAlpha = ss(6.5, 6.8, t);
      fg.beginPath(); fg.moveTo(a[0] + 26, a[1] + 8); fg.lineTo(b[0] + 26, b[1] - 6); fg.stroke(); fg.setLineDash([]); fg.lineWidth = 4; fg.beginPath(); fg.moveTo(b[0] + 6, b[1] - 6); fg.lineTo(b[0] + 46, b[1] - 6); fg.stroke(); fg.restore();
    }
    const l = kind === 'low' ? ['b_l1', 'b_l2', 4.05] : ['b_h1', 'b_h2', 6.1];
    const u = eo(l[2], l[2] + 0.25, t), u2 = eo(l[2] + 0.25, l[2] + 0.5, t);
    show(l[0], { x: ox + 140, y: 140, op: u, dy: (1 - u) * 60 }); show(l[1], { x: ox + 150, y: 370, op: u2, dx: (1 - u2) * -40 });
  }
  const x1 = eback(5.5, 5.75, t); if (t < 6.15) show('b_x', { x: 1560 - wp, y: 330, ax: 0.5, ay: 0.5, op: clamp(x1 * 2), sc: x1 });
  const x2 = eback(7.0, 7.25, t); show('b_x2', { x: 1560, y: 240, ax: 0.5, ay: 0.5, op: clamp(x2 * 2), sc: x2 });
  show('b_tag', { x: 80, y: 64, op: 1 });
  const s = eo(7.5, 7.75, t); show('b_sum', { x: 960, y: 1010, ax: 0.5, ay: 0.5, op: s, dy: (1 - s) * 30 });
}
function secC(t) {   // 8-10 pivot
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.08); vignette(bg, 0.6);
  const a = eo(8.0, 8.3, t), b = eo(9.0, 9.3, t);
  show('c_1', { x: 160, y: 300, op: a, dx: (1 - a) * -80, blur: (1 - a) * 6 }); show('c_2', { x: 160, y: 470, op: b, dx: (1 - b) * -80, blur: (1 - b) * 6 });
  // abstract: bed line + a seat segment that lifts forward and tilts when line 2 lands
  const y = 860, u = eo(9.0, 9.6, t); fg.save(); fg.lineCap = 'round'; fg.strokeStyle = '#3A4656'; fg.lineWidth = 10; fg.beginPath(); fg.moveTo(160, y); fg.lineTo(1100, y); fg.stroke();
  const sx = 1120 + 120 * u, sy = y - 170 * u, ang = 0.26 * u; fg.translate(sx, sy); fg.rotate(ang); fg.strokeStyle = C.acc; fg.shadowColor = C.acc; fg.shadowBlur = 24; fg.lineWidth = 12; fg.beginPath(); fg.moveTo(0, 0); fg.lineTo(190, 0); fg.stroke(); fg.restore();
  if (u > 0) { fg.save(); fg.strokeStyle = 'rgba(25,211,240,.6)'; fg.lineWidth = 3; fg.setLineDash([10, 10]); fg.beginPath(); fg.moveTo(1215, y); fg.quadraticCurveTo(1240, y - 60, 1215 + 120 * u + 95, y - 170 * u + 24 * u); fg.stroke(); fg.restore(); }
}
function secD(t) {   // 10-12 title
  fillBG(C.ink); vignette(bg, 0.6);
  const fl = 1 - ss(10.0, 10.18, t); if (fl > 0) { bg.fillStyle = `rgba(255,255,255,${fl})`; bg.fillRect(0, 0, W, H); }
  const a = eo(10.0, 10.45, t), out = ss(11.6, 12.0, t);
  show('d_t', { x: 960, y: 470, ax: 0.5, ay: 0.5, op: a * (1 - out), ls: lerp(0.55, 0.06, a), sc: 1 + 0.6 * out, blur: out * 14 });
  TX.d_t.style.backgroundPosition = `${lerp(100, -60, ss(10.5, 11.3, t))}% 0`;
  const e = eo(10.25, 10.55, t); show('d_e', { x: 960, y: 640, ax: 0.5, ay: 0.5, op: e * (1 - out), ls: lerp(0.8, 0.32, e) });
  const g2 = eo(10.5, 10.8, t); show('d_g', { x: 960, y: 735, ax: 0.5, ay: 0.5, op: g2 * (1 - out) });
  // light streak
  const sx = lerp(-400, 2400, ss(10.0, 10.6, t)); const gr = bg.createLinearGradient(sx - 300, 0, sx + 300, 0); gr.addColorStop(0, 'rgba(25,211,240,0)'); gr.addColorStop(0.5, 'rgba(25,211,240,.25)'); gr.addColorStop(1, 'rgba(25,211,240,0)');
  bg.fillStyle = gr; bg.fillRect(0, 430, W, 120);
}
// hero assembly: groups land on beats 12.0 ... 15.5; shells at 16.0
const ASM = [
  { t: 12.0, codes: ['B1', 'B1a', 'B2', 'B2b', 'B7'], dir: [0, 0, -0.9], lab: 'B2', fr: [0.5, 0.2, 1] },
  { t: 12.5, codes: ['H1', 'L3'], dir: [0, 0.9, 0.3], lab: 'H1', fr: [0.25, 0.5, 0.7] },
  { t: 13.0, codes: ['D1', 'D2', 'D2a'], dir: [-0.5, 0, 1.0], lab: 'D1', fr: [0.5, 0.5, 0.5] },
  { t: 13.5, codes: ['D3', 'D4', 'D5', 'D6'], dir: [0.3, 0.2, 1.0], lab: 'D4', fr: [0.5, 0.5, 0.5] },
  { t: 14.0, grp: 'carriage', dir: [-0.6, 0, -0.8], lab: 'C1', fr: [0.5, 0.5, 0.5] },
  { t: 14.5, grp: 'link', dir: [0.9, -0.3, 0], lab: 'L1', fr: [0.5, 0.5, 0.5] },
  { t: 15.0, grp: 'seat', dir: [0, 0, 1.0], lab: 'S2', fr: [0.5, 0.2, 1] },
  { t: 15.5, codes: ['B4', 'B5'], dir: [0.9, 0, 0.2], lab: 'B4', fr: [0.5, 0.5, 0.75] },
];
function secE(t) {   // 12-18 hero
  fillBG(C.ink); const r = bg.createRadialGradient(760, 620, 50, 760, 620, 1100); r.addColorStop(0, '#162231'); r.addColorStop(1, C.ink); bg.fillStyle = r; bg.fillRect(0, 0, W, H); grid(bg, '#3A5A70', 60, 0.05);
  const over = {}; const off = {};
  for (const [i, a] of ASM.entries()) {
    const u = eback(a.t - 0.42, a.t, t), vis = t >= a.t - 0.42 ? 1 : 0, land = Math.exp(-Math.max(0, t - a.t) * 6) * (t >= a.t ? 1 : 0);
    const d = a.dir.map(v => v * (1 - u) * 1000);
    if (a.codes) for (const c of a.codes) { PG[c].position.set(d[0], d[1], d[2]); over[c] = { op: vis, emis: '#19D3F0', ei: land * 0.8, eop: 0.16 + 0.8 * land }; }
    else { off[a.grp] = d; for (const { code } of MATS.filter(m => D.mesh.parts.find(p => p.code === m.code).group === a.grp)) over[code] = { op: vis, emis: '#19D3F0', ei: land * 0.6, eop: 0.16 + 0.8 * land }; }
  }
  const sh = ss(16.0, 16.5, t);
  setLook('hero', over); for (const c of ['H2', 'H3', 'H4', 'H5']) { const m = PART[c].material; m.opacity = 0.14 * sh; m.visible = sh > 0.01; }
  EMATS.filter(e => ['H2', 'H3', 'H4', 'H5'].includes(e.code)).forEach(e => { e.m.opacity = 0.22 * sh; e.m.visible = sh > 0.01; });
  EMATS.filter(e => e.code === 'BED').forEach(e => { e.m.color.set('#8BEFFF'); e.m.opacity = 0.10 * ss(16.0, 16.6, t); e.m.visible = e.m.opacity > 0.003; });
  setMech(0, off); setSwitch(ss(15.9, 16.1, t) * (0.75 + 0.25 * Math.cos((t - 16) * Math.PI * 4))); sw.visible = t >= 15.5; swGlow.visible = t >= 15.5;
  disc.visible = true; const az = lerp(-1.22, -0.50, ss(12, 18.2, t)), el = lerp(0.30, 0.22, ss(12, 18, t)), dist = lerp(3.55, 3.0, eo(12, 18, t));
  const cam = heroView(az, el, dist, 300); renderGL(cam);
  // labels with leader lines (01..08), out at 16.0
  const lo = 1 - ss(15.95, 16.25, t);
  for (const [i, a] of ASM.entries()) {
    const u = eo(a.t, a.t + 0.22, t); if (u <= 0 || lo <= 0) continue;
    const ax = proj(partAnchor(a.lab, a.fr), cam), rx = 1350, ry = 190 + RANK[i] * 88;
    show('e_l' + i, { x: rx, y: ry, ay: 0.5, op: u * lo, dx: (1 - u) * 40 });
    fg.save(); fg.globalAlpha = u * lo * 0.85; fg.strokeStyle = C.acc; fg.lineWidth = 2; fg.beginPath(); fg.moveTo(ax[0], ax[1]); const mx = lerp(ax[0], rx - 30, 0.55);
    fg.lineTo(mx, ry); fg.lineTo(lerp(mx, rx - 24, u), ry); fg.stroke(); fg.fillStyle = C.acc; fg.beginPath(); fg.arc(ax[0], ax[1], 6, 0, 7); fg.fill();
    fg.globalAlpha = u * lo * 0.35; fg.beginPath(); fg.arc(ax[0], ax[1], 6 + 22 * (1 - Math.exp(-(t - a.t) * 3)), 0, 7); fg.stroke(); fg.restore();
  }
  show('e_tag', { x: 80, y: 64, op: 1 });
  const b = eo(16.1, 16.45, t); show('e_big', { x: 1180, y: 400, op: b, dy: (1 - b) * 50 }); const c = eo(16.5, 16.8, t); show('e_sub', { x: 1184, y: 640, op: c });
  vignette(fg, 0.25);
}
// side views shared by F, G, H
let RANK = null;
function heroRanks() {   // order the label rows by the anchors' screen height in the assembled view (t = 15)
  const save = ASM.map(() => 0); for (const c in PG) PG[c].position.set(0, 0, 0); setMech(0); const cam = heroView(lerp(-1.22, -0.50, ss(12, 18.2, 15)), lerp(0.30, 0.22, ss(12, 18, 15)), lerp(3.55, 3.0, eo(12, 18, 15)), 300);
  const ys = ASM.map((a, i) => [proj(partAnchor(a.lab, a.fr), cam)[1], i]).sort((p, q) => p[0] - q[0]); const r = []; ys.forEach(([y, i], k) => r[i] = k); return r;
}
const SEAT_POLY = [[-85, 0], [85, 0], [85, -60], [60, -92], [-40, -92], [-85, -50]];
function seatOutline(s) { const f = kinAt(s), ph = f[3] * Math.PI / 180, c = Math.cos(ph), sn = Math.sin(ph);
  return SEAT_POLY.map(([x, z]) => [(f[1] + x * c + z * sn) / 1000, (f[2] - x * sn + z * c) / 1000]); }
function pathTo(s) { const pts = []; for (const r of K) { if (r[0] > s) break; pts.push([r[1] / 1000, r[2] / 1000]); } const f = kinAt(s); pts.push([f[1] / 1000, f[2] / 1000]); return pts; }
function secF(t) {   // 18-24 motion (dark side view)
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.07);
  const hh = lerp(0.62, 0.95, ss(19.0, 22.0, t)), cx = lerp(0.20, 0.12, ss(19, 22, t)), cz = lerp(0.62, 0.86, ss(19.0, 22.0, t)); const V = sideView(cx, cz, hh);
  const kf = t < 19.0 ? -1 : t < 19.35 ? lerp(-1, 0, (t - 19.0) / 0.35) : lerp(0, FR.length - 1, ss(19.35, 22.6, t));
  const R = rise(kf); setLook('dark', { shell: { op: 0 } }); setMech(R.s); disc.visible = false;
  const sw = t >= 18.5 ? (R.released ? 0.25 : 1) * (0.8 + 0.2 * Math.cos((t - 18.5) * 4 * Math.PI)) : ss(18.4, 18.5, t); setSwitch(sw);
  floor2D(bg, V.map, '#2C3644'); drawBed2D(bg, V.map, V.sc, 0.42, false, -1.9);
  renderGL(V.cam);
  // trajectory + strobe ghosts of the seat on each beat
  const pts = pathTo(R.s); fg.save(); fg.lineCap = 'round'; fg.lineJoin = 'round';
  fg.strokeStyle = 'rgba(25,211,240,.25)'; fg.lineWidth = 16; fg.beginPath(); pts.forEach((p, i) => { const q = V.map(p); i ? fg.lineTo(...q) : fg.moveTo(...q); }); fg.stroke();
  fg.strokeStyle = C.acc; fg.lineWidth = 4; fg.stroke();
  for (let bt = 19.5; bt <= Math.min(t, 22.5); bt += BEAT) { const kb = bt < 19.35 ? lerp(-1, 0, (bt - 19.0) / 0.35) : lerp(0, FR.length - 1, ss(19.35, 22.6, bt)); const sb = rise(kb).s;
    const poly = seatOutline(sb); fg.globalAlpha = 0.55 * Math.exp(-(t - bt) * 0.6); fg.strokeStyle = C.acc; fg.lineWidth = 2.5; fg.beginPath(); poly.forEach((p, i) => { const q = V.map(p); i ? fg.lineTo(...q) : fg.moveTo(...q); }); fg.closePath(); fg.stroke(); }
  fg.restore();
  ghostFig(fg, joints(R.pose, HAND_BAR), V.map, V.sc, '#FFFFFF', 0.10, 5);
  // arrows: forward / up / tilt
  const q0 = kinAt(0), qr = kinAt(S_REL), A0 = [q0[1] / 1000, q0[2] / 1000], AR = [qr[1] / 1000, qr[2] / 1000];
  const arrow = (a, b, u, id, lab) => { if (u <= 0) return; const p = V.map(a), q = V.map(b), e = [lerp(p[0], q[0], u), lerp(p[1], q[1], u)]; fg.save(); fg.strokeStyle = C.acc; fg.fillStyle = C.acc; fg.lineWidth = 4; fg.beginPath(); fg.moveTo(...p); fg.lineTo(...e); fg.stroke();
    const an = Math.atan2(q[1] - p[1], q[0] - p[0]); fg.translate(...e); fg.rotate(an); fg.beginPath(); fg.moveTo(4, 0); fg.lineTo(-16, -10); fg.lineTo(-16, 10); fg.fill(); fg.restore();
    show(id, { x: lab[0], y: lab[1], ax: 0.5, ay: 0.5, op: u }); };
  const u1 = eo(20.0, 20.3, t), u2 = eo(20.5, 20.8, t), u3 = eo(21.0, 21.3, t), fa = 1 - ss(23.0, 23.3, t);
  const yb = A0[1] - 0.20; arrow([A0[0] - 0.02, yb], [AR[0] + 0.04, yb], u1 * fa, 'f_a0', V.map([(A0[0] + AR[0]) / 2, yb - 0.07]));
  const xr = AR[0] + 0.30; arrow([xr, A0[1]], [xr, AR[1] + 0.02], u2 * fa, 'f_a1', V.map([xr + 0.10, (A0[1] + AR[1]) / 2]));
  if (u3 * fa > 0) { const c = V.map([AR[0], AR[1]]), rr = 0.17 * V.sc; fg.save(); fg.strokeStyle = C.acc; fg.lineWidth = 4; fg.globalAlpha = u3 * fa; fg.beginPath(); fg.arc(c[0], c[1], rr, Math.PI - 0.30 * u3, Math.PI); fg.stroke(); fg.restore();
    show('f_a2', { x: c[0] - rr - 30, y: c[1] + 10, ax: 1, ay: 0.5, op: u3 * fa }); }
  show('f_tag', { x: 80, y: 64, op: 1 });
  const a = win(t, 18.0, 20.0, 0.25, 0.15), b = win(t, 20.0, 22.5, 0.25, 0.15), c = win(t, 22.6, 24.2, 0.25, 0.1);
  show('f_1', { x: 120, y: 130, op: a, dx: (1 - eo(18.0, 18.3, t)) * -60 }); show('f_2', { x: 120, y: 130, op: b, dx: (1 - eo(20.0, 20.3, t)) * -60 }); show('f_3', { x: 120, y: 130, op: c, dx: (1 - eo(22.6, 22.9, t)) * -60 });
}
function scootPose(u) {   // sitting on the bed edge -> on the seat, hands lap -> bar
  const P1 = sunk(F0, DZ0), Hp = lerpA([-0.24, 0.42 + 0.085 - 0.02], P1.Hp, eo(0, 1, u)); Hp[1] += 0.03 * Math.sin(Math.PI * u);
  const A = P1.A, tr = lerp(14, F0.tr, ss(0.2, 1, u)); return { Hp, K: kneeIK(Hp, A), A, tr };
}
function secG(t) {   // 24-30 how-to (light)
  fillBG(C.paper); grid(bg, '#0A0E14', 60, 0.045);
  const V = sideView(0.02, 0.80, 0.92); setLook('light', { shell: { op: 0 }, plate: { op: 0.6 } }); disc.visible = false;
  let pose, hands = HAND_BAR, s = 0, swv = 0;
  if (t < 25.5) { const u = ss(24.1, 25.2, t); pose = scootPose(u); const lap = joints(pose, null).Hd; hands = lerpA(lap, HAND_BAR, ss(24.6, 25.3, t)); hands[1] += 0.08 * Math.sin(Math.PI * ss(24.6, 25.3, t)); }
  else if (t < 27.0) { const R = rise(-1); pose = R.pose; swv = ss(25.9, 26.0, t) * (0.75 + 0.25 * Math.cos((t - 26) * 4 * Math.PI)); }
  else { const kf = t < 27.25 ? lerp(-1, 0, (t - 27.0) / 0.25) : lerp(0, FR.length - 1, ss(27.25, 28.45, t)); const R = rise(kf); pose = R.pose; s = R.s; swv = t < 28.5 ? 1 : 0;
    if (t >= 28.5) { const S = joints(pose, null).S, side = [S[0] + 0.03, S[1] - Lua - Lfa * 0.9]; hands = lerpA(HAND_BAR, side, eo(28.5, 28.85, t)); } }
  setMech(s); setSwitch(swv);
  floor2D(bg, V.map, '#0A0E14'); drawBed2D(bg, V.map, V.sc, 0.42, true, -1.9); renderGL(V.cam);
  drawFig(fg, joints(pose, hands), V.map, V.sc, C.ink, C.paper);
  if (t >= 25.5 && t < 28.5) {   // grip pulse rings on the beats
    const c = V.map(HAND_BAR); for (let bt = 26.0; bt <= t; bt += BEAT) { const k = t - bt; if (k > 0.5) continue; fg.save(); fg.strokeStyle = C.amb; fg.globalAlpha = 1 - k / 0.5; fg.lineWidth = 5; fg.beginPath(); fg.arc(c[0], c[1], 26 + 90 * k, 0, 7); fg.stroke(); fg.restore(); }
  }
  if (t >= 28.5) {   // seat locked: brackets around the seat
    const poly = seatOutline(s).map(V.map), xs = poly.map(p => p[0]), ys = poly.map(p => p[1]), x0 = Math.min(...xs) - 16, x1 = Math.max(...xs) + 16, y0 = Math.min(...ys) - 16, y1 = Math.max(...ys) + 16, L = 22;
    const u = eback(28.5, 28.7, t); fg.save(); fg.strokeStyle = C.red; fg.lineWidth = 5; fg.globalAlpha = clamp(u); fg.beginPath();
    for (const [x, y, dx, dy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x0, y1, 1, -1], [x1, y1, -1, -1]]) { fg.moveTo(x + dx * L, y); fg.lineTo(x, y); fg.lineTo(x, y + dy * L); } fg.stroke(); fg.restore();
    show('g_stop', { x: x0 - 20, y: y0 - 6, ay: 1, ax: 1, op: clamp(u), sc: u });
  }
  show('g_tag', { x: 80, y: 64, op: 1 });
  for (let i = 0; i < 4; i++) { const a = 24 + i * 1.5, o = win(t, a, a + 1.5, 0.12, 0.08), u = eo(a, a + 0.25, t);
    show('g_n' + i, { x: 110, y: 130, op: o, dy: (1 - u) * 40 }); show('g_a' + i, { x: 470, y: 160, op: o, dx: (1 - u) * 50 }); show('g_b' + i, { x: 474, y: 280, op: o * eo(a + 0.1, a + 0.35, t) }); }
  // progress ticks
  for (let i = 0; i < 4; i++) { const a = 24 + i * 1.5, f = clamp((t - a) / 1.5); bg.fillStyle = '#C9D0D9'; bg.fillRect(120 + i * 190, 1000, 170, 6); bg.fillStyle = C.ink; bg.fillRect(120 + i * 190, 1000, 170 * f, 6); }
}
function secH(t) {   // 30-33 sensing (dark)
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.07);
  const V = sideView(0.36, 0.78, 0.86); const kf = lerp(2, 9, ss(30, 33, t)), R = rise(kf); setLook('dark', { shell: { op: 0 } }); setMech(R.s); disc.visible = false; setSwitch(0.9);
  floor2D(bg, V.map, '#2C3644'); drawBed2D(bg, V.map, V.sc, 0.42, false, -1.9); renderGL(V.cam);
  ghostFig(fg, joints(R.pose, HAND_BAR), V.map, V.sc, '#FFFFFF', 0.08, 4);
  const f = kinAt(R.s), ph = f[3] * Math.PI / 180, seatPt = [(f[1] + 10 * Math.cos(ph) - 100 * Math.sin(ph)) / 1000, (f[2] - 10 * Math.sin(ph) - 100 * Math.cos(ph)) / 1000];
  const PTS = [seatPt, [0.70, 0.905], HAND_BAR, [0.40, 0.045]], LAB = [[-420, 40], [-440, -190], [110, -60], [260, -50]];
  for (let i = 0; i < 4; i++) {
    const bt = 30.0 + i * 0.5, u = eo(bt, bt + 0.2, t); if (u <= 0) continue; const c = V.map(PTS[i]), col = i === 2 ? C.amb : C.acc;
    fg.save(); fg.fillStyle = col; fg.shadowColor = col; fg.shadowBlur = 24; fg.beginPath(); fg.arc(c[0], c[1], 10 * u, 0, 7); fg.fill(); fg.shadowBlur = 0;
    for (let b2 = bt; b2 <= t; b2 += BEAT) { const k = t - b2; if (k > 0.6) continue; fg.strokeStyle = col; fg.globalAlpha = 1 - k / 0.6; fg.lineWidth = 3; fg.beginPath(); fg.arc(c[0], c[1], 14 + 80 * k, 0, 7); fg.stroke(); }
    fg.globalAlpha = u; fg.strokeStyle = col; fg.lineWidth = 2; const lx = c[0] + LAB[i][0], ly = c[1] + LAB[i][1]; fg.beginPath(); fg.moveTo(c[0], c[1]); fg.lineTo(lx + (LAB[i][0] < 0 ? 210 : -10), ly); fg.stroke(); fg.restore();
    show('h_s' + i, { x: lx, y: ly, ay: 0.5, op: u, dx: (1 - u) * 30 });
  }
  show('h_tag', { x: 80, y: 64, op: 1 }); const a = eo(30.0, 30.3, t) * (1 - ss(31.9, 32.05, t)); show('h_1', { x: 120, y: 130, op: a, dx: (1 - eo(30.0, 30.3, t)) * -60 });
  const b = eo(32.0, 32.25, t); show('h_2', { x: 120, y: 140, op: b, dx: (1 - b) * -60 });
}
function secI(t) {   // 33-36 end
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.07); vignette(bg, 0.7);
  drawECG(fg, { x0: 0, y0: 760, t0: 33, t, speed: 1100, amp: 120, col: 'rgba(25,211,240,1)', tail: 1400 });
  const a = eo(34.0, 34.35, t); show('i_t', { x: 960, y: 420, ax: 0.5, ay: 0.5, op: a, sc: lerp(1.15, 1, a), blur: (1 - a) * 10, ls: lerp(0.3, 0.05, a) });
  const b = eo(34.4, 34.7, t); show('i_s', { x: 960, y: 580, ax: 0.5, ay: 0.5, op: b });
  const c = eo(34.8, 35.1, t); show('i_g', { x: 960, y: 900, ax: 0.5, ay: 0.5, op: c });
  const fo = ss(35.6, 36, t); if (fo > 0) { fg.fillStyle = `rgba(0,0,0,${fo})`; fg.fillRect(0, 0, W, H); }
}
const SECS = [[0, 4, secA], [4, 8, secB], [8, 10, secC], [10, 12, secD], [12, 18, secE], [18, 24, secF], [24, 30, secG], [30, 33, secH], [33, 36.01, secI]];
window.renderAt = function (t) {
  resetFrame(); for (const c in PG) PG[c].position.set(0, 0, 0);
  for (const [a, b, f] of SECS) if (t >= a && t < b) { f(t); break; }
};
window.DUR = DUR;
// preload every glyph we use in every weight, then signal ready
(async () => {
  const all = Array.from(txt.querySelectorAll('.t')).map(e => e.textContent).join('') + '0123456789T+.s ';
  await Promise.all(['500', '700', '900'].flatMap(w => [document.fonts.load(`${w} 40px "Noto Sans SC"`, all), document.fonts.load(`${w} 40px "Inter Tight"`, all)]).concat([document.fonts.load('500 40px "JetBrains Mono"', all)]));
  await document.fonts.ready; RANK = heroRanks(); document.title = 'ready';
})();
