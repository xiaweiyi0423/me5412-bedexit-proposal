// "Pulse" cut of the bed-exit seat film: 36 s at 120 BPM (beat = 0.5 s). renderAt(t) draws the frame at time t; no clocks.
// Layers: #bg 2D canvas (backgrounds, bed, floor) -> three.js (CAD device, transparent clear) -> #fg 2D canvas (figure, lines) -> #txt DOM type.
// World: metres, x forward from the bed edge, y along the bed (+y = head side), z up.
const W = 1920, H = 1080, D = window.DATA, BEAT = 0.5, DUR = 44;
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
// problem
T('b_l1', '床低', { s: { ...big(200), color: C.ink } }); T('b_l2', '→ 站不起来', { s: { ...big(76, 700), color: C.ink } });
T('b_h1', '床高', { s: { ...big(200), color: C.ink } }); T('b_h2', '→ 脚踩不实', { s: { ...big(76, 700), color: C.ink } });
T('b_tag', 'PROBLEM / 问题', mono(24, '#5A6575')); T('b_x', '✕', { s: { ...big(120), color: C.red } }); T('b_x2', '✕', { s: { ...big(120), color: C.red } });
T('b_sum', '固定高度的床，两头难兼顾', { s: { ...big(54, 700), color: C.ink } });
// pivot + title
T('c_1', '平时，<span style="color:#19D3F0">和床一样低</span>。', { s: big(68) });
T('c_2', '起身时，<span style="color:#19D3F0">跟着你升起来</span>。', { s: big(68) });
T('d_t', '床边起身台', { s: { ...big(232), backgroundImage: 'linear-gradient(100deg,#fff 0%,#fff 40%,#9ff3ff 48%,#fff 56%,#fff 100%)', backgroundSize: '300% 100%', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } });
T('d_e', 'BED-EXIT SEAT', { cls: 'lat', s: { fontSize: '62px', fontWeight: 800, color: C.acc, letterSpacing: '.32em' } });
T('d_g', 'ME5412 ROBOTICS FOR HEALTHCARE · GROUP 16', mono(24));
// hero
const PARTS_LAB = ['底座 · 踏板', '导轨安装板 · 连杆支座', '斜导轨 + 滚珠丝杠', '电机 · 失电制动', '滑块', '倾角连杆', '座板 · 分区坐垫', 'L 形扶手 · 握把开关'];
T('e_tag', 'HARDWARE / 结构', mono(24));
PARTS_LAB.forEach((w, i) => T('e_l' + i, `<span class="mono" style="color:#19D3F0;font-size:24px;margin-right:18px">0${i + 1}</span>${w}`, { s: { fontSize: '36px', fontWeight: 700 } }));
T('e_big', '一个电机<br><span style="color:#19D3F0">一个自由度</span>', { s: big(96) });
[['斜导轨 + 滚珠丝杠', C.acc], ['电机 · 失电制动', C.acc], ['握把开关：握紧才升', C.amb]].forEach(([w, c], i) => T('e_k' + i, `<span class="mono" style="color:${c};font-size:24px;margin-right:18px">0${i + 1}</span>${w}`, { s: { fontSize: '40px', fontWeight: 700 } }));
T('e_sub', 'MOTOR → BELT → BALL SCREW → CARRIAGE', mono(26, '#A8B4C4'));
// mechanism
T('f_tag', 'MOTION / 运动', mono(24));
T('f_1', '座板不是直上直下', { s: big(84) });
T('f_2', '前移 · 上升 · 前倾<br><span style="font-size:52px;font-weight:700;color:#A8B4C4">跟着大腿一起走</span>', { s: big(84) });
T('f_3', '人站稳，<span style="color:#19D3F0">座板停住</span>', { s: big(84) });
['前移', '上升', '前倾'].forEach((w, i) => T('f_a' + i, w, { s: { ...big(40, 700), color: C.acc } }));
// how to
T('g_tag', 'HOW TO / 用法', mono(24, '#5A6575'));
const STEPS = [['挪上座板', '座板和床一样高，平移过去'], ['握紧开关', '握紧才升'], ['一起起身', '托住臀部和大腿，人不往前滑'], ['松手即停', '座板停在原位，坐回也接得住']];
STEPS.forEach(([a, b], i) => {
  T('g_n' + i, '0' + (i + 1), { cls: 'lat', s: { fontSize: '210px', fontWeight: 900, color: 'transparent', WebkitTextStroke: '3px #07090D', lineHeight: 1 } });
  T('g_a' + i, a, { s: { ...big(96), color: C.ink } });
  T('g_b' + i, b, { s: { ...big(40, 500), color: '#3A4554' } });
});
T('g_stop', 'STOP', { cls: 'lat', s: { fontSize: '44px', fontWeight: 900, color: '#fff', background: C.red, padding: '6px 18px', borderRadius: '8px', letterSpacing: '.08em' } });
// sensing
T('h_tag', 'SENSING / 传感', mono(24));
T('h_1', '起身全程，四处测力', { s: big(76) });
const SENS = [['座下测力', '坐稳了没有'], ['横杆测力', '手在不在'], ['握把开关', '握紧才升'], ['踏板测力', '脚踩实了没有']];
SENS.forEach(([a, b], i) => T('h_s' + i, `<div style="font-size:38px;font-weight:900">${a}</div><div style="font-size:28px;font-weight:500;color:#A8B4C4;margin-top:4px">${b}</div>`, { s: {} }));
T('h_2', '握紧才升 · 松手即停 · <span style="color:#19D3F0">失电制动</span>', { s: big(76) });
// end
T('i_t', '床边起身台', { s: big(120) });
T('i_s', '平时和床一样低 · 起身时跟着你升起来<br>松手就停', { s: { ...big(36, 500), color: '#C9D3DF', textAlign: 'center', lineHeight: 1.5 } });
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
function secB(t) {   // 4-8 problem, light (a dimmer cool grey, so the cut from the dark opening is not a flash)
  fillBG('#C3C9D1'); grid(bg, '#0A0E14', 60, 0.045);
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
  const fl = 1 - ss(10.0, 10.18, t); if (fl > 0) { bg.fillStyle = `rgba(140,225,250,${0.16 * fl})`; bg.fillRect(0, 0, W, H); }
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
  const lo = 0;
  for (const [i, a] of ASM.entries()) {
    const u = eo(a.t, a.t + 0.22, t); if (u <= 0 || lo <= 0) continue;
    const ax = proj(partAnchor(a.lab, a.fr), cam), rx = 1350, ry = 190 + RANK[i] * 88;
    show('e_l' + i, { x: rx, y: ry, ay: 0.5, op: u * lo, dx: (1 - u) * 40 });
    fg.save(); fg.globalAlpha = u * lo * 0.85; fg.strokeStyle = C.acc; fg.lineWidth = 2; fg.beginPath(); fg.moveTo(ax[0], ax[1]); const mx = lerp(ax[0], rx - 30, 0.55);
    fg.lineTo(mx, ry); fg.lineTo(lerp(mx, rx - 24, u), ry); fg.stroke(); fg.fillStyle = C.acc; fg.beginPath(); fg.arc(ax[0], ax[1], 6, 0, 7); fg.fill();
    fg.globalAlpha = u * lo * 0.35; fg.beginPath(); fg.arc(ax[0], ax[1], 6 + 22 * (1 - Math.exp(-(t - a.t) * 3)), 0, 7); fg.stroke(); fg.restore();
  }
  show('e_tag', { x: 80, y: 64, op: 1 });
  const b = eo(16.1, 16.45, t); show('e_big', { x: 1180, y: 200, op: b, dy: (1 - b) * 50 });
  const KEYS = [['D1', [0.5, 0.5, 0.6], 16.5], ['D4', [0.5, 0.5, 0.5], 17.0], [null, null, 17.5]];
  KEYS.forEach(([code, fr, kt], i) => { const u = eo(kt, kt + 0.2, t); if (u <= 0) return; const ax = code ? proj(partAnchor(code, fr), cam) : proj(SW.clone(), cam), rx = 1200, ry = 560 + i * 92;
    show('e_k' + i, { x: rx, y: ry, ay: 0.5, op: u, dx: (1 - u) * 40 });
    fg.save(); fg.globalAlpha = u * 0.9; fg.strokeStyle = i === 2 ? C.amb : C.acc; fg.fillStyle = fg.strokeStyle; fg.lineWidth = 2; fg.beginPath(); fg.moveTo(ax[0], ax[1]); const mx = lerp(ax[0], rx - 30, 0.55);
    fg.lineTo(mx, ry); fg.lineTo(lerp(mx, rx - 24, u), ry); fg.stroke(); fg.beginPath(); fg.arc(ax[0], ax[1], 7, 0, 7); fg.fill(); fg.globalAlpha = u * 0.4 * Math.exp(-(t - kt) * 2); fg.beginPath(); fg.arc(ax[0], ax[1], 7 + 30 * (1 - Math.exp(-(t - kt) * 3)), 0, 7); fg.stroke(); fg.restore(); });
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
const F25 = { az: 0.52, el: 0.16, dist: 4.2, hh: 1.32 };   // the 2.5D angle the motion shot starts from (hh: frame scale vs the flat view)
const figScene = new THREE.Scene(); figScene.add(new THREE.HemisphereLight(0xffffff, 0x8090a0, 1.1)); { const d = new THREE.DirectionalLight(0xffffff, 0.6); d.position.set(2, -3, 4); figScene.add(d); }
const FIGC = document.createElement('canvas'); FIGC.width = W; FIGC.height = H; const figg = FIGC.getContext('2d');
function figPass(cam) {   // render the tube figure alone, keep it as an image (no see-through overlaps when drawn translucent)
  const parent = tubeG.parent; figScene.add(tubeG); tubeG.visible = true; hipTube.forEach(h => h.visible = false); tubeM.transparent = false; tubeM.depthWrite = true; tubeM.opacity = 1;
  renderer.clear(); renderer.render(figScene, cam); figg.clearRect(0, 0, W, H); figg.drawImage(renderer.domElement, 0, 0); renderer.clear();
  parent.add(tubeG); tubeG.visible = false; hipTube.forEach(h => h.visible = true);
}
function secF(t) {   // 18-24 motion: 2.5D at first, turning to the flat side view as the seat rises
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.07 * (1 - 0)); 
  const hh = lerp(0.62, 0.95, ss(19.0, 22.0, t)), cx = lerp(0.20, 0.12, ss(19, 22, t)), cz = lerp(0.62, 0.86, ss(19.0, 22.0, t)); const V0 = sideView(cx, cz, hh);
  const q = 1 - ss(19.6, 21.0, t); let V = V0;
  if (q > 0.001) { const T = V3d(cx, 0, cz - 0.10 * q), az = -Math.PI / 2 + F25.az * q, el = F25.el * q, dist = Math.exp(lerp(Math.log(40), Math.log(F25.dist), q));
    pcam.fov = 2 * Math.atan(hh * lerp(1, F25.hh, q) / dist) * 180 / Math.PI; pcam.position.set(T.x + dist * Math.cos(el) * Math.cos(az), T.y + dist * Math.cos(el) * Math.sin(az), T.z + dist * Math.sin(el)); pcam.lookAt(T); pcam.clearViewOffset(); pcam.updateProjectionMatrix();
    V = { cam: pcam, sc: V0.sc, map: p => proj(V3d(p[0], 0, p[1]), pcam) }; }
  sketchG.visible = q > 0.01; SK.lines.forEach(l => { l.visible = true; l.material.opacity = (SK.jit.includes(l) ? 0.25 : 0.75) * q; l.position.set(0, 0, 0); });
  Object.values(SKB).forEach(m => { m.visible = q > 0.01 && m !== SKB.hb && m !== SKB.pl && m !== SKB.duv; m.children.forEach(l => l.geometry.setDrawRange(0, Infinity)); });
  const kf = t < 19.0 ? -1 : t < 19.35 ? lerp(-1, 0, (t - 19.0) / 0.35) : lerp(0, FR.length - 1, ss(19.35, 22.6, t));
  const R = rise(kf); setLook('dark', { shell: { op: 0 } }); setMech(R.s); disc.visible = false;
  const sw = t >= 18.5 ? (R.released ? 0.25 : 1) * (0.8 + 0.2 * Math.cos((t - 18.5) * 4 * Math.PI)) : ss(18.4, 18.5, t); setSwitch(sw);
  bg.save(); bg.globalAlpha = 1 - q; floor2D(bg, V0.map, '#2C3644'); drawBed2D(bg, V0.map, V0.sc, 0.42, false, -1.9); bg.restore();
  tubeG.visible = false; if (q > 0.01) { setTube(joints(R.pose, HAND_BAR)); figPass(V.cam); }
  renderGL(V.cam);
  if (q > 0.01) { fg.save(); fg.globalAlpha = 0.5 * q; fg.drawImage(FIGC, 0, 0); fg.restore(); }
  // trajectory + strobe ghosts of the seat on each beat
  const pts = pathTo(R.s); fg.save(); fg.lineCap = 'round'; fg.lineJoin = 'round';
  fg.strokeStyle = 'rgba(25,211,240,.25)'; fg.lineWidth = 16; fg.beginPath(); pts.forEach((p, i) => { const q = V.map(p); i ? fg.lineTo(...q) : fg.moveTo(...q); }); fg.stroke();
  fg.strokeStyle = C.acc; fg.lineWidth = 4; fg.stroke();
  for (let bt = 19.5; bt <= Math.min(t, 22.5); bt += BEAT) { const kb = bt < 19.35 ? lerp(-1, 0, (bt - 19.0) / 0.35) : lerp(0, FR.length - 1, ss(19.35, 22.6, bt)); const sb = rise(kb).s;
    const poly = seatOutline(sb); fg.globalAlpha = 0.55 * Math.exp(-(t - bt) * 0.6); fg.strokeStyle = C.acc; fg.lineWidth = 2.5; fg.beginPath(); poly.forEach((p, i) => { const q = V.map(p); i ? fg.lineTo(...q) : fg.moveTo(...q); }); fg.closePath(); fg.stroke(); }
  fg.restore();
  if (q < 0.99) { fg.save(); fg.globalAlpha = 1 - q; ghostFig(fg, joints(R.pose, HAND_BAR), V0.map, V0.sc, '#FFFFFF', 0.10 * (1 - q), 5); fg.restore(); }
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
    const bt = 30.0 + i * 0.5, u0 = eo(bt, bt + 0.2, t); if (u0 <= 0) continue; const c = V.map(PTS[i]), col = i === 2 ? C.amb : C.acc;
    const cur = Math.min(3, Math.floor((t - 30.0) / 0.5)), foc = t >= 32.0 ? 1 : i === cur ? 1 : lerp(1, 0.35, eo(bt + 0.5, bt + 0.7, t)), u = u0 * foc;
    fg.save(); fg.globalAlpha = foc; fg.fillStyle = col; fg.shadowColor = col; fg.shadowBlur = 24; fg.beginPath(); fg.arc(c[0], c[1], 10 * u, 0, 7); fg.fill(); fg.shadowBlur = 0;
    for (let b2 = bt; b2 <= t; b2 += BEAT) { const k = t - b2; if (k > 0.6 || (foc < 0.99)) continue; fg.strokeStyle = col; fg.globalAlpha = 1 - k / 0.6; fg.lineWidth = 3; fg.beginPath(); fg.arc(c[0], c[1], 14 + 80 * k, 0, 7); fg.stroke(); }
    fg.globalAlpha = u; fg.strokeStyle = col; fg.lineWidth = 2; const lx = c[0] + LAB[i][0], ly = c[1] + LAB[i][1]; fg.beginPath(); fg.moveTo(c[0], c[1]); fg.lineTo(lx + (LAB[i][0] < 0 ? 210 : -10), ly); fg.stroke(); fg.restore();
    show('h_s' + i, { x: lx, y: ly, ay: 0.5, op: u, dx: (1 - u0) * 30, sc: i === cur && t < 32 ? 1.08 : 1 });
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
// ------------------------------------------------------------------ points + lines: opening, design process, end
const DS = window.DS, XO = 10;     // sections after the design block run on the old clock (t - XO)
T('a_s', '每一次起身，都是一条<span style="color:#19D3F0">线</span>', { s: { ...big(60, 700), color: '#C9D3DF' } });
T('x_tag', 'TRAJECTORY / 轨迹', mono(24));
T('x_d1', '座板<span style="color:#19D3F0">跟着大腿走</span><br><span style="font-size:44px;font-weight:700;color:#A8B4C4">前移、上升、前倾，一路托着人</span>', { s: big(80) });
T('x_d2', '这条路线，按 <span style="color:#19D3F0">81 种身体</span>算出来<br><span style="font-size:44px;font-weight:700;color:#A8B4C4">身高 · 体型 · 起身习惯 · 脚的位置</span>', { s: big(80) });
T('x_d3', '一条导轨 + 一根连杆<br><span style="font-size:44px;font-weight:700;color:#A8B4C4">走出这条曲线</span>', { s: big(80) });
T('x_0', '线是怎么画的<br><span style="font-size:44px;font-weight:700;color:#A8B4C4">座板“粘”在大腿下面，跟着人起身</span>', { s: big(80) });
T('x_c', '座板中心走过的点，连成一条线', { s: { ...big(30, 700), color: '#fff' } });
T('x_0b', '换一个人，就是另一条线<br><span style="font-size:44px;font-weight:700;color:#A8B4C4">身高 × 体型 × 起身习惯 × 脚的位置 = 81 个人</span>', { s: big(80) });
T('x_1', '先画线<br><span style="font-size:44px;font-weight:700;color:#A8B4C4">81 个人，各自起身时座板该走的路</span>', { s: big(80) });
T('x_2', '挑一条<span style="color:#fff;text-shadow:0 0 24px #19D3F0">设计曲线</span><br><span style="font-size:44px;font-weight:700;color:#A8B4C4">每条都拿给 81 个人试，选最吃力的人也够用的那条</span>', { s: big(80) });
T('x_3', '再找点<br><span style="font-size:44px;font-weight:700;color:#A8B4C4">座板上每个点，都画出自己的轨迹</span>', { s: big(80) });
T('x_l1', '导轨', { s: { ...big(44, 900), color: C.acc } }); T('x_l2', '连杆', { s: { ...big(44, 900), color: '#8CF5A6' } });
T('x_B', 'B', { cls: 'lat', s: { fontSize: '40px', fontWeight: 800, color: '#8CF5A6' } });
T('x_4', '比过五种结构，它最贴合、最省力', { s: big(72) });
T('x_v', '不是直上直下，而是<span style="color:#19D3F0">一路贴着大腿</span>', { s: big(72) });
T('x_c0', '直上直下<br><span style="font-size:30px;font-weight:700;color:#8A96A6">座板很快离开大腿</span>', { s: { ...big(46, 900), color: '#C9D3DF', textAlign: 'center' } });
T('x_c1', '斜导轨 + 倾角连杆<br><span style="font-size:30px;font-weight:700;color:#C9D3DF">沿设计曲线，一路托着</span>', { s: { ...big(46, 900), color: C.acc, textAlign: 'center' } });
T('x_fb', '还比过三种四连杆：会碰小腿、回床挡腿，或受力太大', { s: { ...big(38, 700), color: '#C9D3DF' } });
['① 跟得上设计曲线', '② 床尾敞开，腿能转回床', '③ 受力小'].forEach((w, k) => T('x_g' + k, w, { s: big(38, 900) }));
const CANDN = ['竖直升降', '四连杆 · 中间', '四连杆 · 两侧', '四连杆 · 床头一侧', '斜导轨 + 倾角连杆'], CANDR = ['跟不上大腿', '会碰小腿', '回床时挡腿', '受力太大', '最贴合 · 最省力'];
CANDN.forEach((n, i) => { T('x_p' + i, n, { s: { ...big(32, 900), color: i === 4 ? C.acc : '#fff' } }); T('x_r' + i, CANDR[i], { s: { ...big(28, 700), color: i === 4 ? '#fff' : '#8A96A6' } }); });
T('x_ok', '四连杆的一根杆，换成一条<span style="color:#19D3F0">导轨</span>', { s: { ...big(40, 700), color: '#C9D3DF' } });
const LIME = '#8CF5A6';
const R2 = (Q, phi, c) => { const p = phi * Math.PI / 180, cs = Math.cos(p), sn = Math.sin(p); return [Q[0] + cs * c[0] + sn * c[1], Q[1] - sn * c[0] + cs * c[1]]; };
function pline(g, pts, map, col, lw, a = 1, glow = 0, dash) { if (pts.length < 2) return; g.save(); g.globalAlpha = a; g.strokeStyle = col; g.lineWidth = lw; g.lineCap = 'round'; g.lineJoin = 'round';
  if (dash) g.setLineDash(dash); if (glow) { g.shadowColor = col; g.shadowBlur = glow; } g.beginPath(); pts.forEach((p, i) => { const q = map(p); i ? g.lineTo(...q) : g.moveTo(...q); }); g.stroke(); g.restore(); }
function ppoly(g, pts, map, fill, stroke, lw = 2, a = 1) { g.save(); g.globalAlpha = a; g.beginPath(); pts.forEach((p, i) => { const q = map(p); i ? g.lineTo(...q) : g.moveTo(...q); }); g.closePath();
  if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.strokeStyle = stroke; g.lineWidth = lw; g.stroke(); } g.restore(); }
function dot(g, q, r, col, a = 1, ring = 0) { g.save(); g.globalAlpha = a; g.fillStyle = col; g.shadowColor = col; g.shadowBlur = 18; g.beginPath(); g.arc(q[0], q[1], r, 0, 7); g.fill();
  if (ring) { g.shadowBlur = 0; g.strokeStyle = col; g.lineWidth = 2; g.globalAlpha = a * (1 - ring); g.beginPath(); g.arc(q[0], q[1], r + 26 * ring, 0, 7); g.stroke(); } g.restore(); }
function ground(g, q, col, s = 14) { g.save(); g.fillStyle = col; g.beginPath(); g.moveTo(q[0], q[1]); g.lineTo(q[0] - s * 0.7, q[1] + s); g.lineTo(q[0] + s * 0.7, q[1] + s); g.closePath(); g.fill(); g.restore(); }
const partial = (pts, u) => { if (u <= 0) return []; if (u >= 1) return pts; const n = (pts.length - 1) * u, i = Math.floor(n), f = n - i; return pts.slice(0, i + 1).concat([lerpA(pts[i], pts[i + 1], f)]); };
const DQ = DS.design.Q, DPHI = DS.design.phi;
function designPose(k) { k = clamp(k) * (DQ.length - 1); const i = Math.min(DQ.length - 2, Math.floor(k)), f = k - i; return { Q: lerpA(DQ[i], DQ[i + 1], f), phi: lerp(DPHI[i], DPHI[i + 1], f) }; }

function secA(t) {   // 0-4: joints pop in as points, bones join them as lines, the rise leaves a line behind the hip
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.10); vignette(bg, 0.7);
  const sc = 430, map = p => [1250 + p[0] * sc, 930 - p[1] * sc];
  const lu = eo(0.0, 0.8, t); pline(bg, [[-1.4, 0], [lerp(-1.4, 1.2, lu), 0]], map, '#2C3644', 3); pline(bg, [[-1.4, 0.42], [lerp(-1.4, 0, lu), 0.42]], map, '#3A4656', 3);
  const kf = lerp(0, FR.length - 1, ss(2.0, 3.55, t)), J = joints(poseAt(kf), null);
  const PTS = [J.A, J.K, J.H, J.S, J.hd, J.E, J.Hd, J.toe], BONES = [[0, 1], [1, 2], [2, 3], [3, 5], [5, 6], [0, 7], [3, 4]];
  BONES.forEach(([a, b], i) => { const u = eo(1.0 + i * 0.125, 1.35 + i * 0.125, t); if (u > 0) pline(fg, [PTS[a], lerpA(PTS[a], PTS[b], u)], map, '#FFFFFF', 4, 0.85); });
  // trails (head faint, hip bright) once the rise starts
  if (t > 2.0) { const tr = k => { const out = []; for (let x = 0; x <= k; x += 0.25) out.push(joints(poseAt(x), null)); out.push(joints(poseAt(k), null)); return out; }, TR = tr(kf);
    pline(fg, TR.map(j => j.hd), map, '#19D3F0', 2, 0.35, 0, [6, 8]); pline(fg, TR.map(j => j.K), map, '#19D3F0', 2, 0.25, 0, [6, 8]); pline(fg, TR.map(j => j.H), map, '#19D3F0', 5, 1, 22); }
  PTS.forEach((p, i) => { const u = eback(i * 0.125, i * 0.125 + 0.2, t); if (u <= 0) return; const q = map(p), hip = i === 2;
    dot(fg, q, (hip ? 13 : 9) * clamp(u, 0, 1.3), hip ? C.acc : '#FFFFFF', 1, clamp((t - i * 0.125) / 0.5)); });
  fg.save(); fg.fillStyle = '#fff'; fg.beginPath(); const hq = map(J.hd); fg.globalAlpha = eo(1.75, 1.95, t) * 0.0; fg.arc(hq[0], hq[1], 0.098 * sc, 0, 7); fg.fill(); fg.restore();
  if (eo(1.75, 2.0, t) > 0) { fg.save(); fg.strokeStyle = '#fff'; fg.lineWidth = 4; fg.globalAlpha = 0.85 * eo(1.75, 2.0, t); fg.beginPath(); fg.arc(hq[0], hq[1], 0.098 * sc * eo(1.75, 2.0, t), 0, 7); fg.stroke(); fg.restore(); }
  show('a_tagL', { x: 80, y: 64, op: ss(0.1, 0.4, t) }); show('a_tagR', { x: 1840, y: 64, ax: 1, op: ss(0.1, 0.4, t) });
  const h = eo(1.0, 1.3, t); show('a_h', { x: 120, y: 300, op: h, dx: (1 - h) * -60, blur: (1 - h) * 6 });
  const s2 = eo(2.5, 2.8, t); show('a_s', { x: 124, y: 440, op: s2, dx: (1 - s2) * -40 });
}
// design block 12-22
function xView(t) {     // camera for the design block: close on the paths, then wide enough for the rail and B
  const k = ss(16.0, 16.6, t); return { cx: lerp(0.135, 0.25, k), cz: lerp(0.545, 0.46, k), sc: lerp(2300, 1020, k), sx: lerp(1240, 1260, k), sy: lerp(560, 580, k) };
}
const CPTS = (() => { const c1 = DS.mech.c1, c2 = DS.mech.c2, pts = [];
  for (const x of [-0.10, -0.05, 0.0, 0.05, 0.10]) for (const z of [-0.02, -0.07, -0.13, -0.19]) pts.push([x, z]);
  const near = c => pts.reduce((b, p, i) => Math.hypot(p[0] - c[0], p[1] - c[1]) < Math.hypot(pts[b][0] - c[0], pts[b][1] - c[1]) ? i : b, 0);
  const i1 = near(c1); pts[i1] = c1; const i2 = near(c2); pts[i2] = c2; return { pts, i1, i2 }; })();
const DM = window.DEMO, DCOL = ['#19D3F0', '#8CF5A6', '#FFB020', '#C9A7FF', '#FF8A7A'], CHOSEN = DM.keys.indexOf(DM.chosen);
function demoState(u, k) {   // user u at progress k in [0,1]: joints + seat pose (thigh-carried)
  const F = u.fr, x = clamp(k) * (F.length - 1), i = Math.min(F.length - 2, Math.floor(x)), f = x - i, a = F[i], b = F[i + 1], sc = u.H / 1.60;
  const Hp = lerpA(a.Hp, b.Hp, f), K = lerpA(a.K, b.K, f), A = lerpA(a.A, b.A, f), pf = lerp(a.f, b.f, f);
  const tr = pf < 0.35 ? lerp(22, 52, ss(0, 0.35, pf)) : lerp(52, 0, ss(0.35, 1, pf)), t2 = tr * Math.PI / 180, ut = [Math.sin(t2), Math.cos(t2)], S = [Hp[0] + Ltr * sc * ut[0], Hp[1] + Ltr * sc * ut[1]];
  const up = [ut[0] * 0.45, ut[1] * 0.45 + 0.55], n = Math.hypot(...up), hd = [S[0] + 0.165 * sc * up[0] / n, S[1] + 0.165 * sc * up[1] / n];
  const Hd = [lerp(Hp[0], K[0], 0.66), lerp(Hp[1], K[1], 0.66) + 0.07], E = elbowIK(S, Hd), fz = Math.max(0.025, A[1] - 0.04);
  const on = (b.on ? f : 0) + (a.on ? 1 - f : 0) > 0.5, last = F.filter(r => r.on).slice(-1)[0];
  const Q = on ? lerpA(a.Q, b.Q, f) : last.Q, phi = on ? lerp(a.phi, b.phi, f) : last.phi;
  return { J: { H: Hp, K, A, S, hd, E, Hd, toe: [A[0] + 0.72 * FOOT * sc, fz], heel: [A[0] - 0.2 * FOOT * sc, fz] }, Q, phi, on };
}
function demoTrail(u, k) { const F = u.fr, x = clamp(k) * (F.length - 1), out = []; for (let i = 0; i <= Math.floor(x) && i < F.length; i++) if (F[i].on) out.push(F[i].Q); const s = demoState(u, k); if (s.on) out.push(s.Q); return out; }
function prettyPaths(g, map, t, a = 1, hl = -1, t0 = null) {   // 81 lines as faint glowing strands with points flowing along them; t0: draw in from t0
  g.save(); g.globalCompositeOperation = 'lighter';
  DS.env.forEach((P2full, i) => { if (i === hl) return; const P2 = t0 === null ? P2full : partial(P2full, eo(t0 + (i % 9) * 0.1, t0 + (i % 9) * 0.1 + 0.35, t)); if (P2.length < 2) return; const gr = g.createLinearGradient(...map(P2[0]), ...map(P2[P2.length - 1])); gr.addColorStop(0, 'rgba(25,211,240,0)'); gr.addColorStop(0.35, `rgba(25,211,240,${0.16 * a})`); gr.addColorStop(1, `rgba(200,240,255,${0.30 * a})`);
    g.strokeStyle = gr; g.lineWidth = 1.6; g.lineCap = 'round'; g.beginPath(); P2.forEach((p, j) => { const q = map(p); j ? g.lineTo(...q) : g.moveTo(...q); }); g.stroke();
    const u = ((t * 0.55 + i * 0.6180339) % 1), pp = partial(P2, u), q = map(pp[pp.length - 1]); g.fillStyle = `rgba(220,250,255,${0.85 * a * Math.sin(Math.PI * u)})`; g.beginPath(); g.arc(q[0], q[1], 2.6, 0, 7); g.fill(); });
  g.restore();
}
function secX(t) {   // 12-20 product voice: the seat follows the thigh; its path is built for 81 bodies; a rail + a link make it; picked from five
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.08); vignette(bg, 0.5); show('x_tag', { x: 80, y: 64, op: 1 });
  if (t >= 17.5) { cmp2(t); return; }
  const k0 = ss(13.6, 14.3, t), k2 = ss(15.0, 15.45, t);
  const v = { cx: lerp(lerp(0.32, 0.14, k0), 0.25, k2), cz: lerp(lerp(0.83, 0.55, k0), 0.46, k2), sc: lerp(lerp(620, 1900, k0), 1020, k2), sx: lerp(1250, 1260, k2), sy: lerp(560, 580, k2) };
  const map = p => [v.sx + (p[0] - v.cx) * v.sc, v.sy - (p[1] - v.cz) * v.sc];
  ppoly(bg, [[-1.5, 0], [0, 0], [0, DS.Z0], [-1.5, DS.Z0]], map, '#141A22', '#2C3644', 2); pline(bg, [[-1.5, 0], [1.5, 0]], map, '#2C3644', 3);
  if (t < 15.0) {
    const u = DM.users[0], k = ss(12.3, 13.8, t), st = demoState(u, k), fa = 1 - ss(13.9, 14.3, t);
    if (fa > 0) { drawFig(fg, st.J, map, v.sc, '#55657A', '#55657A', fa, 4, true); drawFig(fg, st.J, map, v.sc, '#222B37', '#222B37', fa, 0, true); }
    if (t >= 13.95) prettyPaths(fg, map, t, lerp(1, 0.6, ss(14.6, 14.95, t)), -1, 13.95);
    pline(fg, demoTrail(u, k), map, C.acc, 4, lerp(1, 0.0, ss(14.4, 14.8, t)), 16);
    ppoly(fg, DS.mech.plate.map(c => R2(st.Q, st.phi, c)), map, 'rgba(255,255,255,.92)', null, 2, 1 - ss(13.6, 13.9, t));
    const du = eo(14.45, 14.95, t); if (du > 0) pline(fg, partial(DQ, du), map, '#FFFFFF', 5, 1, 24);
  } else {
    prettyPaths(fg, map, t, 0.22); pline(fg, DQ, map, '#FFFFFF', 3, 0.55, 10);
    const up = ss(15.3, 16.2, t), dn = ss(16.5, 17.3, t), k = up * (1 - dn), dp = designPose(k), ku = up;   // up, then back down
    const tr = (c, kk) => { const out = []; for (let x = 0; x <= kk + 1e-9; x += 0.02) { const d = designPose(Math.min(x, kk)); out.push(R2(d.Q, d.phi, c)); } return out; };
    const lo = DS.mech.rail_lo, hi = DS.mech.rail_hi, ur = eo(15.9, 16.25, t), mid = lerpA(lo, hi, 0.5);
    if (ur > 0) { pline(fg, [lerpA(mid, lo, ur), lerpA(mid, hi, ur)], map, C.acc, 16, 0.32); const q = map(lerpA(lo, hi, 0.88)); show('x_l1', { x: q[0] - 30, y: q[1] - 10, ax: 1, ay: 0.5, op: ur }); }
    const B = DS.mech.B, cp = R2(dp.Q, dp.phi, DS.mech.c2), ul = eo(16.2, 16.5, t);
    if (ul > 0) { pline(fg, [B, lerpA(B, cp, ul)], map, LIME, 7, 0.95); ground(fg, map(B), LIME, 18); dot(fg, map(B), 7, LIME); const lq = map(lerpA(B, cp, 0.5)); show('x_l2', { x: lq[0] + 30, y: lq[1] + 24, ay: 0.5, op: ul }); }
    pline(fg, tr(DS.mech.c1, ku), map, C.acc, 4, 0.9, 14); pline(fg, tr(DS.mech.c2, ku), map, LIME, 4, 0.9, 14);
    ppoly(fg, DS.mech.br.map(c => R2(dp.Q, dp.phi, c)), map, 'rgba(255,255,255,.06)', 'rgba(255,255,255,.4)', 2);
    ppoly(fg, DS.mech.plate.map(c => R2(dp.Q, dp.phi, c)), map, 'rgba(255,255,255,.9)', null);
    const p1 = map(R2(dp.Q, dp.phi, DS.mech.c1)); fg.fillStyle = C.acc; fg.fillRect(p1[0] - 9, p1[1] - 9, 18, 18); dot(fg, map(cp), 7, LIME);
  }
  const o1 = win(t, 12.0, 13.9, 0.25, 0.12), o2 = win(t, 13.9, 15.0, 0.2, 0.12), o3 = win(t, 15.0, 17.5, 0.2, 0.1);
  show('x_d1', { x: 120, y: 150, op: o1, dx: (1 - eo(12, 12.3, t)) * -60 }); show('x_d2', { x: 120, y: 150, op: o2, dx: (1 - eo(13.9, 14.2, t)) * -60 });
  show('x_d3', { x: 120, y: 150, op: o3, dx: (1 - eo(15.0, 15.3, t)) * -60 });
}
function cmp2(t) {   // 17.5-20: straight-up lift vs ours, side by side, both looping
  const loop = 0.5 - 0.5 * Math.cos(2 * Math.PI * (t - 17.5) / 2.0); show('x_v', { x: 120, y: 120, op: eo(17.5, 17.8, t), dx: (1 - eo(17.5, 17.8, t)) * -60 });
  [[0, 560], [1, 1360]].forEach(([k, pcx]) => {
    const ap = eback(17.55 + k * 0.25, 17.8 + k * 0.25, t); if (ap <= 0) return; const sc = 720 * clamp(ap, 0, 1.1), base = 950, map = p => [pcx + (p[0] - 0.22) * sc, base - p[1] * sc];
    ppoly(fg, [[-0.35, 0], [0, 0], [0, DS.Z0], [-0.35, DS.Z0]], map, '#1A212B', '#2C3644', 2); pline(fg, [[-0.35, 0], [0.6, 0]], map, '#3A4656', 2);
    pline(fg, DQ, map, '#FFFFFF', 3, 0.55, 0, [8, 8]);
    if (k === 0) { const z = lerp(DS.Z0, 0.66, loop), Q = [0.055, z]; pline(fg, [[0.055, 0], [0.055, z - 0.05]], map, '#5A6575', 14);
      pline(fg, [[0.055, DS.Z0], [0.055, 0.66]], map, '#8A96A6', 3, 0.8); ppoly(fg, DS.mech.plate.map(c => R2(Q, 0, c)), map, '#C9D3DF', null); }
    else { const M2 = DS.mech, F = M2.frames, f = F[Math.round(loop * (F.length - 1))]; pline(fg, [M2.rail_lo, M2.rail_hi], map, C.acc, 14, 0.5);
      pline(fg, F.map(x => x.Q), map, C.acc, 4, 1, 18); ppoly(fg, M2.br.map(p => R2(f.Q, f.phi, p)), map, 'rgba(160,170,182,.6)', null); ppoly(fg, M2.plate.map(p => R2(f.Q, f.phi, p)), map, '#FFFFFF', null);
      const q1 = map(f.P1); fg.fillStyle = C.acc; fg.fillRect(q1[0] - 11, q1[1] - 11, 22, 22); pline(fg, [M2.B, f.P2], map, LIME, 7); dot(fg, map(f.P2), 7, '#fff'); ground(fg, map(M2.B), LIME, 16); }
    show('x_c' + k, { x: pcx, y: 300, ax: 0.5, ay: 0.5, op: clamp(ap) });
  });
  const n = eo(17.9, 18.2, t); show('x_fb', { x: 960, y: 1030, ax: 0.5, ay: 0.5, op: n * 0.9 });
}
function cand2(t) {   // 17.5-20: five structures flash in, four step back together, the rail + link stays lit
  show('x_4', { x: 120, y: 120, op: eo(17.5, 17.8, t), dx: (1 - eo(17.5, 17.8, t)) * -60 });
  const loop = 0.5 - 0.5 * Math.cos(2 * Math.PI * (t - 17.5) / 2.0), fade = eo(18.6, 18.9, t), win5 = eback(18.7, 18.95, t);
  for (let i = 0; i < 5; i++) {
    const ap = eback(17.5 + i * 0.15, 17.75 + i * 0.15, t); if (ap <= 0) continue;
    const f5 = i < 4 ? fade : 0, pcx = 210 + i * 375, sc = 520 * clamp(ap, 0, 1.15), base = 880, map = p => [pcx + (p[0] - 0.22) * sc, base - p[1] * sc], dim = lerp(1, 0.22, f5);
    fg.save(); fg.globalAlpha = dim;
    ppoly(fg, [[-0.12, 0], [0, 0], [0, DS.Z0], [-0.12, DS.Z0]], map, '#1A212B', null); pline(fg, [[-0.12, 0], [0.62, 0]], map, '#3A4656', 2);
    pline(fg, DQ, map, '#FFFFFF', 2, 0.45, 0, [5, 6]);
    if (i === 0) { const z = lerp(DS.Z0, 0.69, loop), Q = [0.055, z]; pline(fg, [[0.055, 0], [0.055, z - 0.05]], map, '#5A6575', 10);
      ppoly(fg, DS.mech.plate.map(c => R2(Q, 0, c)), map, '#E9EDF2', null); pline(fg, [[0.055, DS.Z0], [0.055, 0.69]], map, C.acc, 2, 0.7); }
    else if (i < 4) { const c = DS.cands[i - 1], F = c.frames, f = F[Math.round(loop * (F.length - 1))];
      pline(fg, F.map(x => x.Q), map, C.acc, 2, 0.7); ppoly(fg, c.br.map(p => R2(f.Q, f.phi, p)), map, 'rgba(160,170,182,.6)', null); ppoly(fg, c.plate.map(p => R2(f.Q, f.phi, p)), map, '#E9EDF2', null);
      pline(fg, [c.A, f.P1], map, '#C9D3DF', 5); pline(fg, [c.B, f.P2], map, '#C9D3DF', 5); [f.P1, f.P2].forEach(p => dot(fg, map(p), 5, '#fff')); ground(fg, map(c.A), '#C9D3DF', 12); ground(fg, map(c.B), '#C9D3DF', 12); }
    else { const M2 = DS.mech, F = M2.frames, f = F[Math.round(loop * (F.length - 1))]; pline(fg, [M2.rail_lo, M2.rail_hi], map, C.acc, 10, 0.55);
      pline(fg, F.map(x => x.Q), map, C.acc, 2 + 2 * win5, 0.8, win5 ? 16 : 0); ppoly(fg, M2.br.map(p => R2(f.Q, f.phi, p)), map, 'rgba(160,170,182,.6)', null); ppoly(fg, M2.plate.map(p => R2(f.Q, f.phi, p)), map, '#E9EDF2', null);
      const q1 = map(f.P1); fg.fillStyle = C.acc; fg.fillRect(q1[0] - 9, q1[1] - 9, 18, 18); pline(fg, [M2.B, f.P2], map, LIME, 5); dot(fg, map(f.P2), 5, '#fff'); ground(fg, map(M2.B), LIME, 12); }
    fg.restore();
    show('x_p' + i, { x: pcx, y: 360, ax: 0.5, ay: 0.5, op: clamp(ap) * lerp(1, 0.35, f5), col: i === 4 ? C.acc : f5 > 0.5 ? '#6B7684' : '#fff' });
    if (f5 > 0) show('x_r' + i, { x: pcx, y: 950, ax: 0.5, ay: 0.5, op: f5 * 0.9 });
    if (win5 > 0 && i === 4) { fg.save(); fg.strokeStyle = C.acc; fg.lineWidth = 4; fg.globalAlpha = clamp(win5); fg.shadowColor = C.acc; fg.shadowBlur = 24; fg.beginPath(); fg.roundRect(pcx - 182, 320, 364, 660, 18); fg.stroke(); fg.restore();
      show('x_r' + i, { x: pcx, y: 950, ax: 0.5, ay: 0.5, op: clamp(win5) }); }
  }
  const okT = eo(19.0, 19.3, t); show('x_ok', { x: 960, y: 1035, ax: 0.5, ay: 0.5, op: okT, dy: (1 - okT) * 20 });
}
function candX(t) {   // five candidates on the old clock (18.5-22)
  // five candidates filtered by three conditions: a candidate that fails steps back and greys out (no crosses)
  show('x_4', { x: 120, y: 120, op: eo(18.5, 18.8, t), dx: (1 - eo(18.5, 18.8, t)) * -60 });
  const loop = 0.5 - 0.5 * Math.cos(2 * Math.PI * (t - 18.5) / 2.0), GATE = [19.5, 20.0, 20.5], FAIL = [0, 0, 1, 2, -1];
  for (let k = 0; k < 3; k++) { const on = eo(GATE[k], GATE[k] + 0.2, t), act = on * (1 - 0.55 * ss(GATE[k] + 0.45, GATE[k] + 0.6, t)), ap = eo(18.9 + k * 0.1, 19.2 + k * 0.1, t);
    show('x_g' + k, { x: 960 + (k - 1) * 560, y: 262, ax: 0.5, ay: 0.5, op: ap * lerp(0.35, 1, on), col: act > 0.5 ? C.acc : '#C9D3DF', sc: 1 + 0.06 * act });
    if (on > 0) { fg.save(); fg.strokeStyle = C.acc; fg.globalAlpha = 0.9 * on; fg.lineWidth = 4; fg.beginPath(); fg.moveTo(960 + (k - 1) * 560 - 200 * on, 298); fg.lineTo(960 + (k - 1) * 560 + 200 * on, 298); fg.stroke(); fg.restore(); } }
  const pathEmph = 1 + 1.5 * win(t, 19.4, 20.0, 0.1, 0.15);
  for (let i = 0; i < 5; i++) {
    const ap = eback(18.5 + i * 0.25, 18.75 + i * 0.25, t); if (ap <= 0) continue;
    const ft = FAIL[i] >= 0 ? GATE[FAIL[i]] : null, fade = ft ? eo(ft + 0.1, ft + 0.4, t) : 0, win5 = i === 4 ? eback(21.0, 21.25, t) : 0;
    const pcx = 210 + i * 375, sc = 520 * clamp(ap, 0, 1.15), base = 880, map = p => [pcx + (p[0] - 0.22) * sc, base - p[1] * sc], dim = lerp(1, 0.22, fade);
    fg.save(); fg.globalAlpha = dim;
    ppoly(fg, [[-0.12, 0], [0, 0], [0, DS.Z0], [-0.12, DS.Z0]], map, '#1A212B', null); pline(fg, [[-0.12, 0], [0.62, 0]], map, '#3A4656', 2);
    pline(fg, DQ, map, '#FFFFFF', 2, 0.45, 0, [5, 6]);
    if (i === 0) { const z = lerp(DS.Z0, 0.69, loop), Q = [0.055, z]; pline(fg, [[0.055, 0], [0.055, z - 0.05]], map, '#5A6575', 10);
      ppoly(fg, DS.mech.plate.map(c => R2(Q, 0, c)), map, '#E9EDF2', null); pline(fg, [[0.055, DS.Z0], [0.055, 0.69]], map, C.acc, 2 * pathEmph, 0.7); }
    else if (i < 4) { const c = DS.cands[i - 1], F = c.frames, f = F[Math.round(loop * (F.length - 1))];
      pline(fg, F.map(x => x.Q), map, C.acc, 2 * pathEmph, 0.7); ppoly(fg, c.br.map(p => R2(f.Q, f.phi, p)), map, 'rgba(160,170,182,.6)', null); ppoly(fg, c.plate.map(p => R2(f.Q, f.phi, p)), map, '#E9EDF2', null);
      pline(fg, [c.A, f.P1], map, '#C9D3DF', 5); pline(fg, [c.B, f.P2], map, '#C9D3DF', 5); [f.P1, f.P2].forEach(p => dot(fg, map(p), 5, '#fff')); ground(fg, map(c.A), '#C9D3DF', 12); ground(fg, map(c.B), '#C9D3DF', 12); }
    else { const M2 = DS.mech, F = M2.frames, f = F[Math.round(loop * (F.length - 1))]; pline(fg, [M2.rail_lo, M2.rail_hi], map, C.acc, 10, 0.55);
      pline(fg, F.map(x => x.Q), map, C.acc, 2 * pathEmph + 2 * win5, 0.8, win5 ? 16 : 0); ppoly(fg, M2.br.map(p => R2(f.Q, f.phi, p)), map, 'rgba(160,170,182,.6)', null); ppoly(fg, M2.plate.map(p => R2(f.Q, f.phi, p)), map, '#E9EDF2', null);
      const q1 = map(f.P1); fg.fillStyle = C.acc; fg.fillRect(q1[0] - 9, q1[1] - 9, 18, 18); pline(fg, [M2.B, f.P2], map, LIME, 5); dot(fg, map(f.P2), 5, '#fff'); ground(fg, map(M2.B), LIME, 12); }
    fg.restore();
    show('x_p' + i, { x: pcx, y: 360, ax: 0.5, ay: 0.5, op: clamp(ap) * lerp(1, 0.35, fade), col: i === 4 ? C.acc : fade > 0.5 ? '#6B7684' : '#fff' });
    if (fade > 0) show('x_r' + i, { x: pcx, y: 950, ax: 0.5, ay: 0.5, op: fade * 0.9 });
    if (win5 > 0) { fg.save(); fg.strokeStyle = C.acc; fg.lineWidth = 4; fg.globalAlpha = clamp(win5); fg.shadowColor = C.acc; fg.shadowBlur = 24; fg.beginPath(); fg.roundRect(pcx - 182, 320, 364, 660, 18); fg.stroke(); fg.restore();
      show('x_r' + i, { x: pcx, y: 950, ax: 0.5, ay: 0.5, op: clamp(win5) }); }
  }
  const okT = eo(21.3, 21.6, t); show('x_ok', { x: 960, y: 1035, ax: 0.5, ay: 0.5, op: okT, dy: (1 - okT) * 20 });
}
function secI2(t) {   // end on the old clock 33-36: the 81 lines and the design curve under the title, a point riding the curve
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.07); vignette(bg, 0.7);
  const sc = 1000, map = p => [960 + (p[0] - 0.135) * sc, 980 - (p[1] - 0.40) * sc];
  DS.env.forEach((P2, i) => { const u = eo(33.0 + i * 0.006, 33.5 + i * 0.006, t); if (u > 0) pline(fg, partial(P2, u), map, '#B9C6D6', 1.2, 0.22); });
  const du = eo(33.4, 34.0, t); if (du > 0) pline(fg, partial(DQ, du), map, C.acc, 5, 1, 22);
  if (t >= 34.0) { const k = ((t - 34.0) / 1.0) % 1, dp = designPose(ss(0, 1, k)); dot(fg, map(dp.Q), 9, '#fff', 1, k); }
  const a = eo(34.0, 34.35, t); show('i_t', { x: 960, y: 330, ax: 0.5, ay: 0.5, op: a, sc: lerp(1.15, 1, a), blur: (1 - a) * 10, ls: lerp(0.3, 0.05, a) });
  const b = eo(34.4, 34.7, t); show('i_s', { x: 960, y: 480, ax: 0.5, ay: 0.5, op: b });
  const c = eo(34.8, 35.1, t); show('i_g', { x: 960, y: 1030, ax: 0.5, ay: 0.5, op: c });
  const fo = ss(35.6, 36, t); if (fo > 0) { fg.fillStyle = `rgba(0,0,0,${fo})`; fg.fillRect(0, 0, W, H); }
}

// ------------------------------------------------------------------ rain night (mood) and its echo at the end: same window, same bed, same camera
const RV = () => sideView(0.55, 0.85, 0.95);                    // shared framing; the window hangs on the wall above the bed
const WIN = { x0: -1.05, x1: -0.35, z0: 0.95, z1: 1.60 };
const RAIN = Array.from({ length: 150 }, (_, i) => { const r = k => ((Math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1 + 1) % 1; return { x: r(1), ph: r(2), sp: 0.9 + 0.6 * r(3), len: 0.04 + 0.05 * r(4), a: 0.25 + 0.5 * r(5) }; });
const DROPS = Array.from({ length: 46 }, (_, i) => { const r = k => ((Math.sin(i * 91.17 + k * 17.31) * 24634.6345) % 1 + 1) % 1; return { x: r(1), z: r(2), r: 1.5 + 2.5 * r(3), slide: r(4) < 0.3 }; });
function drawRoom(V, t, rain, dawn) {   // rain: 0..1 strength; dawn: 0..1 light behind the glass
  const g = bg; const top = V.map([0, 3])[1];
  const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, lerpC('#0A0F17', '#141821', dawn)); gr.addColorStop(1, lerpC('#0C121B', '#17171C', dawn)); g.fillStyle = gr; g.fillRect(0, 0, W, H);
  const a = V.map([WIN.x0, WIN.z1]), b = V.map([WIN.x1, WIN.z0]), w = b[0] - a[0], h = b[1] - a[1];
  // glass: night blue, warming toward dawn from the bottom edge
  const gl = g.createLinearGradient(0, a[1], 0, b[1]); gl.addColorStop(0, lerpC('#101C2C', '#2A3550', dawn)); gl.addColorStop(1, lerpC('#16263A', '#E39A5C', dawn * 0.85)); g.fillStyle = gl; g.fillRect(a[0], a[1], w, h);
  // light cast on the bed and floor through the window
  g.save(); g.globalAlpha = 0.10 + 0.14 * dawn; g.fillStyle = lerpC('#7FA8D8', '#FFC27A', dawn); const p1 = V.map([WIN.x0 + 0.55, 0.42]), p2 = V.map([WIN.x1 + 0.75, 0.42]);
  g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], a[1]); g.lineTo(p2[0], p2[1]); g.lineTo(p1[0], p1[1]); g.closePath(); g.fill(); g.restore();
  g.save(); g.beginPath(); g.rect(a[0], a[1], w, h); g.clip();
  if (rain > 0) { g.lineCap = 'round'; for (const d of RAIN) { const y = ((d.ph + t * d.sp * 1.6) % 1.2 - 0.1), x = a[0] + d.x * w + (y * h) * 0.12, yy = a[1] + y * h, L = d.len * V.sc;
      g.strokeStyle = `rgba(170,200,235,${d.a * rain})`; g.lineWidth = 1.6; g.beginPath(); g.moveTo(x, yy); g.lineTo(x - L * 0.12, yy + L); g.stroke(); } }
  for (const d of DROPS) { const zz = d.slide ? ((d.z + t * 0.05 * rain) % 1) : d.z, q = [a[0] + d.x * w, a[1] + zz * h]; g.fillStyle = `rgba(${dawn > 0.3 ? '255,220,180' : '200,220,245'},${0.35 + 0.4 * dawn})`; g.beginPath(); g.arc(q[0], q[1], d.r, 0, 7); g.fill(); }
  g.restore();
  g.strokeStyle = '#3A4656'; g.lineWidth = 6; g.strokeRect(a[0], a[1], w, h); g.lineWidth = 4; g.beginPath(); g.moveTo(a[0] + w / 2, a[1]); g.lineTo(a[0] + w / 2, b[1]); g.moveTo(a[0], a[1] + h / 2); g.lineTo(b[0], a[1] + h / 2); g.stroke();
  g.fillStyle = '#2A3442'; g.fillRect(a[0] - 14, b[1], w + 28, 10);
}
function lerpC(c1, c2, k) { const p = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)), A = p(c1), B = p(c2); return '#' + A.map((v, i) => Math.round(lerp(v, B[i], clamp(k))).toString(16).padStart(2, '0')).join(''); }
function secRain(t) {   // 8-11: after the failed rises, rain; the hip's line climbs a little, sags, and breaks into drops
  const V = RV(); drawRoom(V, t, 1, 0); floor2D(bg, V.map, '#243041'); drawBed2D(bg, V.map, V.sc, 0.40, false, -1.9);
  const bump = u => Math.max(0, Math.sin(Math.PI * clamp(u))), b = bump((t - 8.35) / 0.95), slump = ss(9.3, 9.9, t);
  const Hp = [-0.08 + 0.05 * b, 0.40 + 0.085 + 0.03 * b], A = [0.30, 0.062], tr = 26 + 26 * b + 6 * slump + 1.2 * Math.sin(t * 2.4);
  const J = joints({ Hp, K: kneeIK(Hp, A), A, tr }, null); const fwd = [Math.sin((tr + 40 * slump) * Math.PI / 180), Math.cos((tr + 40 * slump) * Math.PI / 180)];
  J.hd = [J.S[0] + 0.15 * fwd[0], J.S[1] + 0.15 * fwd[1]];                     // head bows
  // the self it pictures: a faint standing outline and the dashed way there, gone when the try fails
  const wish = eo(8.25, 8.55, t) * (1 - ss(9.3, 9.7, t)); if (wish > 0) { const Pst = poseAt(FR.length - 1), Js = joints(Object.assign({}, Pst, { A: [0.30, 0.062] }), null);
    fg.save(); fg.globalAlpha = 0.55 * wish; ghostFig(fg, Js, V.map, V.sc, '#BFD6EE', 0.04, 3); fg.restore();
    const dash = []; for (let k = 0; k <= 24; k++) { const u = k / 24, P0 = [-0.06, 0.49], P1 = [0.05, 0.86], P2 = [0.29, 0.834]; dash.push([(1 - u) ** 2 * P0[0] + 2 * u * (1 - u) * P1[0] + u * u * P2[0], (1 - u) ** 2 * P0[1] + 2 * u * (1 - u) * P1[1] + u * u * P2[1]]); }
    pline(fg, dash, V.map, '#BFD6EE', 2.5, 0.6 * wish, 0, [8, 10]); dot(fg, V.map(dash[24]), 6, '#BFD6EE', 0.7 * wish); }
  drawFig(fg, J, V.map, V.sc, '#8C9AAD', '#0B1018', 1);
  // the line it wanted: from the hip toward standing; it gets about half way, sags under its own weight, then breaks into drops
  const reach = 0.45 * eo(8.45, 8.95, t), sag = ss(8.95, 9.3, t), tr0 = [];
  for (let k = 0; k <= 24; k++) { const u = reach * k / 24, P0 = [-0.06, 0.49], P1 = [0.05, 0.86], P2 = [0.29, 0.834], q = [(1 - u) ** 2 * P0[0] + 2 * u * (1 - u) * P1[0] + u * u * P2[0], (1 - u) ** 2 * P0[1] + 2 * u * (1 - u) * P1[1] + u * u * P2[1]];
    q[1] -= sag * 0.28 * (k / 24) ** 1.6; tr0.push(q); }
  if (t < 9.3) { if (reach > 0.01) { pline(fg, tr0, V.map, lerpC('#19D3F0', '#5A6B80', sag), 7, 1, 20); dot(fg, V.map(tr0[tr0.length - 1]), 8, lerpC('#FFFFFF', '#5A6B80', sag)); } }
  else tr0.forEach((p, i) => { const dt = t - 9.3 - i * 0.012; if (dt < 0) { dot(fg, V.map(p), 3, '#5A6B80', 0.8); return; } const z = p[1] - 1.6 * dt * dt, q = V.map([p[0] + 0.02 * dt, z]);
    if (z < 0.42) return; fg.save(); fg.globalAlpha = 0.8 * (1 - clamp(dt / 0.9)); fg.strokeStyle = '#9DB8D8'; fg.lineWidth = 2; fg.beginPath(); fg.moveTo(q[0], q[1] - 10 * dt * 6); fg.lineTo(q[0], q[1]); fg.stroke(); fg.restore(); });
  vignette(fg, 0.55);
  const a1 = eo(9.6, 9.95, t), a2 = eo(10.2, 10.55, t), fr = 1 - ss(10.85, 11.0, t);
  show('c_1', { x: 1130, y: 420, op: a1 * fr, dy: (1 - a1) * 30 }); show('c_2', { x: 1130, y: 540, op: a2 * fr, dy: (1 - a2) * 30 });
}
function secEcho(t) {   // 40-46: same window, same bed, now with the seat: rise all the way, the rain stops, dawn; then pull out into the 3D room, sun through the window
  const V = RV(), kf = t < 40.6 ? -1 : t < 40.85 ? lerp(-1, 0, (t - 40.6) / 0.25) : lerp(0, FR.length - 1, ss(40.85, 42.2, t)), R = rise(kf);
  const rain = 1 - ss(41.0, 42.0, t), dawn = ss(41.3, 43.0, t), x2d = 1 - ss(42.3, 42.65, t);
  setLook('dark', { shell: { op: 0 } }); for (const c of ['H2', 'H3', 'H4', 'H5']) { const m = PART[c].material; m.opacity = 0.2; m.visible = true; }
  setMech(R.s); disc.visible = false; setSwitch(t >= 40.5 && !R.released ? 1 : ss(40.4, 40.5, t) * 0.4);
  const P3 = echoPull(t, R, dawn);
  if (P3) { fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.08); const k = ss(42.4, 43.4, t), sp = bg.createRadialGradient(W * 0.62, -80, 40, W * 0.62, 260, 900); sp.addColorStop(0, `rgba(210,235,255,${0.22 * k})`); sp.addColorStop(1, 'rgba(210,235,255,0)'); bg.fillStyle = sp; bg.fillRect(0, 0, W, H); vignette(bg, 0.5);
    setLook('hero', { shell: { op: 0 } }); key.position.set(0.4, 0.2, 6); key.intensity = 1.5; rim.intensity = 1.4; for (const c of ['H2', 'H3', 'H4', 'H5']) { const m = PART[c].material; m.opacity = 0.35; m.visible = true; } }
  if (x2d > 0) { bg.save(); bg.globalAlpha = x2d; drawRoom(V, t, rain, dawn); floor2D(bg, V.map, '#243041'); drawBed2D(bg, V.map, V.sc, 0.42, false, -1.9); bg.restore(); }
  renderGL(P3 ? P3.cam : V.cam); if (P3) { pcam.clearViewOffset(); key.position.set(3, -4, 5); }
  const hips = []; if (kf >= 0) for (let x = 0; x <= kf; x += 0.25) hips.push(poseAt(x).Hp); if (kf >= 0) hips.push(R.pose.Hp);
  if (x2d > 0) { fg.save(); fg.globalAlpha = x2d; drawFig(fg, joints(R.pose, HAND_BAR), V.map, V.sc, '#DDE5EE', '#DDE5EE', 0.9, 0, true); pline(fg, hips, V.map, C.acc, 6, 1, 24);
    if (hips.length) dot(fg, V.map(hips[hips.length - 1]), 9, '#FFFFFF', 1, ((t - 40.85) % 0.5) / 0.5); fg.restore(); }
  vignette(fg, 0.45 - 0.2 * dawn);
  const a = eo(44.2, 44.55, t); show('i_t', { x: 420, y: 250, ax: 0.5, ay: 0.5, op: a, sc: lerp(1.12, 1, a), blur: (1 - a) * 8, ls: lerp(0.3, 0.05, a) });
  const b = eo(44.5, 44.8, t); show('i_s', { x: 420, y: 400, ax: 0.5, ay: 0.5, op: b });
  const c = eo(44.8, 45.1, t); show('i_g', { x: 1500, y: 1030, ax: 0.5, ay: 0.5, op: c });
  const fo = ss(45.55, 46.0, t); if (fo > 0) { fg.fillStyle = `rgba(0,0,0,${fo})`; fg.fillRect(0, 0, W, H); }
}

// ------------------------------------------------------------------ context shot: the seat beside a real bed in 3/4, then swing to the side view
const bedG = new THREE.Group(); bedG.visible = false; scene.add(bedG);
const bedMat = c => new THREE.MeshStandardMaterial({ color: new THREE.Color(c), roughness: 0.85, metalness: 0.05 });
const bedEdge = (geo, parent, op = 0.18) => { const l = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), new THREE.LineBasicMaterial({ color: 0x8BEFFF, transparent: true, opacity: op })); parent.add(l); return l; };
function bbox(w, d, h, x, y, z, col, op) { const g = new THREE.BoxGeometry(w, d, h); const m = new THREE.Mesh(g, bedMat(col)); m.position.set(x, y, z); bedG.add(m); const e = bedEdge(g, m, op); return m; }
const BEDP = {};
bbox(1.62, 2.10, 0.14, -0.81, -0.22, 0.20, '#0B0F15', 0.10);            // frame
bbox(1.58, 2.05, 0.15, -0.80, -0.22, 0.345, '#0F141C', 0.18);           // mattress (top at 0.42, flush with the seat)
BEDP.hb = bbox(1.66, 0.07, 0.86, -0.81, 0.86, 0.55, '#0A0D13', 0.10);             // headboard (head side = +y)
BEDP.pl = bbox(0.50, 0.32, 0.12, -0.95, 0.62, 0.48, '#161D28', 0.10);             // pillow
for (const [x, y] of [[-1.55, -1.2], [-0.07, -1.2], [-1.55, 0.76], [-0.07, 0.76]]) bbox(0.06, 0.06, 0.14, x, y, 0.07, '#141A22', 0.0);
const floorGrid = new THREE.Group(); floorGrid.visible = false; scene.add(floorGrid);
{ const pts = []; for (let v = -3; v <= 3.0001; v += 0.25) { pts.push(v, -3, 0, v, 3, 0, -3, v, 0, 3, v, 0); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); floorGrid.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x3A5A70, transparent: true, opacity: 0.25 }))); }
// the open foot-side zone on the floor (legs swing back onto the bed through here)
const openZone = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.62), new THREE.MeshBasicMaterial({ color: 0x19D3F0, transparent: true, opacity: 0, depthWrite: false })); openZone.position.set(0.30, -0.66, 0.004); scene.add(openZone);
const ozEdge = new THREE.LineSegments(new THREE.EdgesGeometry(openZone.geometry), new THREE.LineBasicMaterial({ color: 0x19D3F0, transparent: true, opacity: 0 })); openZone.add(ozEdge);
T('k_1', '机构全在<span style="color:#19D3F0">床头一侧</span>', { s: { ...big(40, 900) } });
T('k_2', '床尾一侧<span style="color:#19D3F0">敞开</span><br><span style="font-size:28px;font-weight:700;color:#A8B4C4">回床时，腿能转过去</span>', { s: { ...big(40, 900) } });
T('k_tag', 'IN THE ROOM / 床边', mono(24));
// ------------------------------------------------------------------ context shot v2: hand-drawn room (boiling ink lines on dark paper), the seat fills in from line art
const SK = { lines: [], jit: [] };   // bed/room line objects and their jitter copies
const INKC = new THREE.Color('#DCE6F2');
function skLines(geo, parent, op = 0.75, thr = 25) {
  const eg = new THREE.EdgesGeometry(geo, thr), out = [];
  for (let k = 0; k < 3; k++) { const l = new THREE.LineSegments(eg, new THREE.LineBasicMaterial({ color: INKC.clone(), transparent: true, opacity: k ? op * 0.35 : op })); parent.add(l); out.push(l); if (k) SK.jit.push(l); SK.lines.push(l); }
  return out;
}
const sketchG = new THREE.Group(); sketchG.visible = false; scene.add(sketchG);
function skBox(w, d, h, x, y, z, op) { const g = new THREE.BoxGeometry(w, d, h); const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: new THREE.Color().setRGB(0.0042, 0.0075, 0.0135) })); m.position.set(x, y, z); sketchG.add(m); skLines(g, m, op); return m; }   // linear values: shows as about #0E141D
const SKB = {
  frame: skBox(1.62, 2.10, 0.14, -0.81, -0.22, 0.20, 0.55), matt: skBox(1.58, 2.05, 0.15, -0.80, -0.22, 0.345, 0.85),
  hb: skBox(1.66, 0.07, 0.86, -0.81, 0.86, 0.55, 0.6), pl: skBox(0.50, 0.32, 0.12, -0.95, 0.62, 0.48, 0.6),
  duv: skBox(1.30, 1.40, 0.04, -0.95, -0.45, 0.44, 0.45),
};
for (const [x, y] of [[-1.55, -1.2], [-0.07, -1.2], [-1.55, 0.76], [-0.07, 0.76]]) skBox(0.06, 0.06, 0.14, x, y, 0.07, 0.5);
{ // floor: a few long strokes, and hatching for the open foot-side zone
  const pts = []; for (let v = -2.5; v <= 2.5001; v += 0.5) { pts.push(v, -2.5, 0, v, 2.5, 0, -2.5, v, 0, 2.5, v, 0); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); sketchG.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x3A5A70, transparent: true, opacity: 0.35 })));
}
const hatch = (() => { const pts = [], x0 = -0.02, x1 = 0.62, y0 = -0.98, y1 = -0.36;
  for (let s = -0.7; s <= 0.7; s += 0.035) { const a = [x0, y0 + (s + 0.35)], b = [x0 + 0.62, y0 + (s + 0.35) - 0.62]; // 45° strokes clipped to the box
    const seg = []; for (let k = 0; k <= 40; k++) { const p = lerpA(a, b, k / 40); if (p[0] >= x0 && p[0] <= x1 && p[1] >= y0 && p[1] <= y1) seg.push(p); }
    if (seg.length > 1) { const p = seg[0], q = seg[seg.length - 1]; pts.push(p[0], p[1], 0.005, q[0], q[1], 0.005); } }
  pts.push(x0, y0, .005, x1, y0, .005, x1, y0, .005, x1, y1, .005, x1, y1, .005, x0, y1, .005, x0, y1, .005, x0, y0, .005);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x19D3F0, transparent: true, opacity: 0 })); scene.add(l); return l; })();
const PAPER = (() => { const c = document.createElement('canvas'); c.width = 960; c.height = 540; const g = c.getContext('2d'); const im = g.createImageData(960, 540); let s = 7;
  const rnd = () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
  for (let i = 0; i < im.data.length; i += 4) { const n = 10 + rnd() * 9; im.data[i] = n; im.data[i + 1] = n + 5; im.data[i + 2] = n + 12; im.data[i + 3] = 255; } g.putImageData(im, 0, 0);
  g.globalAlpha = 0.05; g.strokeStyle = '#8FB0D0'; for (let k = 0; k < 900; k++) { g.beginPath(); const x = rnd() * 960, y = rnd() * 540; g.moveTo(x, y); g.lineTo(x + rnd() * 24 - 12, y + rnd() * 3 - 1.5); g.stroke(); } return c; })();
function rnd3(seed) { const r = k => ((Math.sin(seed * 12.9898 + k * 78.233) * 43758.5453) % 1 + 1) % 1; return [r(1) - 0.5, r(2) - 0.5, r(3) - 0.5]; }
function wobblyLine(g, pts, col, lw, a, seed) { g.save(); g.globalAlpha = a; g.strokeStyle = col; g.lineWidth = lw; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath();
  pts.forEach((q, i) => { const j = rnd3(seed + i); const x = q[0] + j[0] * 2.2, y = q[1] + j[1] * 2.2; i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.stroke(); g.restore(); }
// ------------------------------------------------------------------ context shot v3: one line draws the bed, the camera follows it up the rail and turns out the device
const V3d = (x, y, z) => new THREE.Vector3(x, y, z);
const RL = D.mech ? null : null;
const TRACE = (() => {   // the path the line travels (world, m)
  const lo = DS.mech.rail_lo, hi = DS.mech.rail_hi, Y = 0.322;
  const P = [V3d(-0.6, -0.9, 0.42), V3d(-0.01, -0.9, 0.42), V3d(-0.01, -0.05, 0.42), V3d(0.06, 0.0, 0.42), V3d(lo[0], Y, lo[1]), V3d(hi[0], Y, hi[1]), V3d(0.70, 0.30, 0.97), V3d(0.70, 0.06, 0.975)];
  const L = [0]; for (let i = 1; i < P.length; i++) L.push(L[i - 1] + P[i].distanceTo(P[i - 1]));
  return { P, L, tot: L[L.length - 1], mark: { dev: L[3], rail0: L[4], top: L[5] } };
})();
function traceAt(s) { s = clamp(s, 0, TRACE.tot); let i = 1; while (i < TRACE.L.length - 1 && TRACE.L[i] < s) i++; const a = TRACE.L[i - 1], b = TRACE.L[i]; return TRACE.P[i - 1].clone().lerp(TRACE.P[i], (s - a) / ((b - a) || 1)); }
function tracePts(s0, s1, n = 80) { const out = []; for (let k = 0; k <= n; k++) out.push(traceAt(lerp(s0, s1, k / n))); return out; }
// arc length along the path vs time: fast on the floor, steady round the bed, slower up the rail
function sOf(u) { const M = TRACE.mark; if (u < 1.15) return 0; if (u < 1.45) return lerp(0, M.rail0, ss(1.15, 1.45, u)); return lerp(M.rail0, TRACE.tot, ss(1.45, 2.0, u)); }
// bed edges in world space, each flies in from far away and lands on its place (the lines gather into the bed)
const BED_EDGES = (() => { const out = []; let i = 0; sketchG.updateMatrixWorld(true);
  for (const m of Object.values(SKB)) { const pos = m.children[0].geometry.attributes.position; for (let k = 0; k < pos.count; k += 2) {
    const a = V3d(pos.getX(k), pos.getY(k), pos.getZ(k)).applyMatrix4(m.matrixWorld), b = V3d(pos.getX(k + 1), pos.getY(k + 1), pos.getZ(k + 1)).applyMatrix4(m.matrixWorld);
    const j = rnd3(i * 3.7 + 1), dir = V3d(j[0] * 2, j[1] * 2, 0.4 + Math.abs(j[2]) * 1.5).normalize().multiplyScalar(1.8 + Math.abs(j[0]) * 2.2);
    out.push({ a, b, dir, t0: 0.10 + 0.75 * ((i * 0.6180339) % 1), key: m === SKB.hb || m === SKB.pl || m === SKB.duv ? 1 : 0 }); i++; } }
  return out; })();
const CAMK = [   // u, azimuth, elevation, distance, target blend toward the line head (0..1), fixed target
  [0.00, -2.05, 0.50, 4.6, 0.0, V3d(-0.75, -0.25, 0.30)], [1.15, -1.75, 0.44, 4.1, 0.0, V3d(-0.6, -0.2, 0.35)], [1.50, -1.25, 0.40, 3.5, 0.25, V3d(-0.05, -0.1, 0.45)],
  [2.05, -0.86, 0.42, 3.5, 0.12, V3d(0.18, -0.12, 0.36)], [2.70, -0.80, 0.40, 3.4, 0.0, V3d(0.18, -0.12, 0.36)]];
function camAt(u, head) { let i = 0; while (i < CAMK.length - 2 && CAMK[i + 1][0] < u) i++; const a = CAMK[i], b = CAMK[i + 1], k = ss(a[0], b[0], u);
  const az = lerp(a[1], b[1], k), el = lerp(a[2], b[2], k), dist = lerp(a[3], b[3], k), bl = lerp(a[4], b[4], k), T = a[5].clone().lerp(b[5], k).lerp(head, bl); return { az, el, dist, T }; }
function secCtx(u) {   // u: 0..3.5 s
  bg.drawImage(PAPER, 0, 0, W, H); const r = bg.createRadialGradient(980, 560, 100, 980, 560, 1250); r.addColorStop(0, 'rgba(25,45,70,.35)'); r.addColorStop(1, 'rgba(0,0,0,.55)'); bg.fillStyle = r; bg.fillRect(0, 0, W, H);
  sketchG.visible = true; disc.visible = false;
  const step = Math.floor(u * 12), s = sOf(u), head = traceAt(s), M = TRACE.mark;
  const bedDraw = ss(1.0, 1.25, u), devDraw = ss(1.2, 1.5, u), swg = ss(2.7, 3.5, u);
  SK.jit.forEach((l, i) => { const j = rnd3(step * 31 + i); l.position.set(j[0] * 0.006, j[1] * 0.006, j[2] * 0.006); });
  SK.lines.forEach(l => { l.material.opacity = (SK.jit.includes(l) ? 0.25 : 0.75) * bedDraw; l.visible = bedDraw > 0.01; }); Object.values(SKB).forEach(m => m.visible = bedDraw > 0.01 || u > 1.0);
  for (const k of ['hb', 'pl', 'duv']) { const m = SKB[k], a = 1 - ss(2.8, 3.25, u); m.visible = a > 0.01; m.children.forEach(l => l.material.opacity = (l === m.children[0] ? 0.6 : 0.2) * a); }
  // device: line art when the line reaches it, filled up to the line head as it climbs the rail
  setLook('dark', { shell: { op: 1 } }); key.intensity = 1.25; rim.intensity = 1.1;
  const band = u < 1.45 ? -0.2 : (u < 2.0 ? head.z + 0.05 : lerp(head.z + 0.05, 1.2, ss(2.0, 2.2, u)));
  const pzOf = code => { const b = PART[code].geometry.boundingBox; return (b.min.z + b.max.z) / 2000 + (PART[code].parent.parent === G.fixed ? 0 : 0.35); };
  for (const { m, k, code } of MATS) { if (k === 'bed') { m.visible = false; continue; } const pz = pzOf(code), f = ss(pz - 0.05, pz + 0.05, band);
    if (k === 'shell') { m.opacity = lerp(0, lerp(0.55, 0.0, swg), f); m.visible = m.opacity > 0.01; } else { m.opacity = f; m.visible = f > 0.01; }
    m.emissive.set('#19D3F0'); m.emissiveIntensity = 0.9 * Math.max(0, 1 - Math.abs(pz - band) / 0.08) * (u < 2.1 ? 1 : 0); }
  for (const { m, k, code } of EMATS) { if (k === 'bed') { m.visible = false; continue; } const pz = pzOf(code), f = ss(pz - 0.05, pz + 0.05, band);
    m.color.set(f < 0.5 ? '#DCE6F2' : '#8BEFFF'); m.opacity = lerp(0.75, k === 'shell' ? 0.25 * (1 - swg) : 0.18, f) * devDraw; m.visible = m.opacity > 0.01; }
  for (const c in PG) { const el = PG[c].children[1]; if (!el) continue; const j = rnd3(step * 7 + c.charCodeAt(0) + (c.charCodeAt(1) || 0)); el.position.set(j[0] * 3, j[1] * 3, j[2] * 3); }
  setMech(0); setSwitch(ss(1.95, 2.05, u) * (0.75 + 0.25 * Math.cos((u - 2.0) * 4 * Math.PI))); sw.visible = u > 1.2; swGlow.visible = u > 1.2;
  // camera follows the head, then dolly-zooms to the orthographic side view used next
  const ca = camAt(u, head), T0 = ca.T.clone().lerp(V3d(0.20, 0.0, 0.60), swg), az = lerp(ca.az, -Math.PI / 2 + F25.az, swg), el = lerp(ca.el, F25.el, swg);
  const halfH = lerp(ca.dist * Math.tan(13 * Math.PI / 180), 0.74 * F25.hh, swg), dist = lerp(ca.dist, F25.dist, swg);
  pcam.fov = 2 * Math.atan(halfH / dist) * 180 / Math.PI; pcam.position.set(T0.x + dist * Math.cos(el) * Math.cos(az), T0.y + dist * Math.cos(el) * Math.sin(az), T0.z + dist * Math.sin(el)); pcam.lookAt(T0); pcam.clearViewOffset(); pcam.updateProjectionMatrix();
  const gb = win(u, 2.15, 2.85, 0.15, 0.2); if (gb > 0) {   // back to bed: sit, turn toward the foot end, legs up (rendered before the main pass)
    const k = ss(2.3, 2.8, u), P0 = sunk(F0, DZ0), Hp = [P0.Hp[0] - 0.10 * k, P0.Hp[1] + 0.02 * k], K = lerpA(P0.K, [Hp[0] + 0.38, Hp[1] + 0.04], k), A = lerpA(P0.A, [Hp[0] + 0.76, Hp[1] + 0.0], k);
    const Jb = joints({ Hp, K, A, tr: lerp(F0.tr, -12, k), toe: [A[0] + 0.15, A[1] + 0.05], heel: [A[0] - 0.04, A[1] - 0.02] }, null), yaw = -1.35 * k, c = V3d(Hp[0], 0, 0);
    setTube(Jb); tubeG.rotation.set(0, 0, yaw); const cs = Math.cos(yaw), sn = Math.sin(yaw); tubeG.position.set(c.x - (cs * c.x - sn * c.y), c.y - (sn * c.x + cs * c.y), 0);
    figPass(pcam); tubeG.rotation.set(0, 0, 0); tubeG.position.set(0, 0, 0); }
  const oz = win(u, 2.2, 2.85, 0.2, 0.2); hatch.material.opacity = 0.75 * oz;
  renderGL(pcam);
  // the line itself: a bright head and a trail that cools to a thin ink line
  // flying bed edges (before the 3D sketch takes over)
  if (u < 1.3) { fg.save(); fg.lineCap = 'round';
    for (const e of BED_EDGES) { const k = eo(e.t0, e.t0 + 0.35, u); if (k <= 0) continue; const off = e.dir.clone().multiplyScalar(1 - k), off2 = e.dir.clone().multiplyScalar(Math.min(1, 1 - k + 0.12));
      const a = proj(e.a.clone().add(off), pcam), b = proj(e.b.clone().add(off), pcam), a2 = proj(e.a.clone().add(off2), pcam), b2 = proj(e.b.clone().add(off2), pcam), al = (1 - bedDraw) * (e.key ? 0.6 : 0.85);
      fg.globalAlpha = al * 0.25 * (1 - k); fg.strokeStyle = '#19D3F0'; fg.lineWidth = 6; fg.beginPath(); fg.moveTo(...a2); fg.lineTo(...a); fg.moveTo(...b2); fg.lineTo(...b); fg.stroke();
      fg.globalAlpha = al; fg.strokeStyle = k < 1 ? '#BFF4FF' : '#DCE6F2'; fg.lineWidth = k < 1 ? 2.2 : 1.6; fg.beginPath(); fg.moveTo(...a); fg.lineTo(...b); fg.stroke(); } fg.restore(); }
  const fadeL = 1 - ss(2.6, 3.0, u), trail = tracePts(Math.max(0, s - 1.2), s, 60).map(p => proj(p, pcam)), old = tracePts(0, Math.max(0, s - 1.2), 60).map(p => proj(p, pcam));
  if (fadeL > 0 && u >= 1.15) { wobblyLine(fg, old, '#DCE6F2', 1.6, 0.5 * fadeL, 70 + step);
    fg.save(); fg.globalAlpha = fadeL; fg.lineCap = 'round'; fg.lineJoin = 'round'; fg.shadowColor = C.acc; fg.shadowBlur = 18;
    for (let i = 1; i < trail.length; i++) { const k = i / trail.length; fg.strokeStyle = `rgba(25,211,240,${0.15 + 0.85 * k})`; fg.lineWidth = 1.5 + 4 * k; fg.beginPath(); fg.moveTo(...trail[i - 1]); fg.lineTo(...trail[i]); fg.stroke(); }
    fg.restore(); if (u < 2.05) dot(fg, proj(head, pcam), 8, '#FFFFFF', fadeL, (u * 2) % 1); }
  const lab = (id, p, dx, dy, a, seed) => { if (a <= 0) return; const q = proj(p, pcam), pts = []; for (let k = 0; k <= 12; k++) pts.push([q[0] + dx * k / 12, q[1] + dy * k / 12]);
    wobblyLine(fg, pts.slice(0, 1 + Math.round(12 * eo(0, 1, a))), '#DCE6F2', 2.2, a, seed + step); dot(fg, q, 5, '#DCE6F2', a);
    show(id, { x: q[0] + dx + (dx > 0 ? 14 : -14), y: q[1] + dy, ax: dx > 0 ? 0 : 1, ay: 0.5, op: a }); };
  lab('k_1', V3d(0.30, 0.36, 0.75), 170, -110, win(u, 2.05, 2.8, 0.2, 0.2), 3);
  if (oz > 0) { const arc = []; for (let k = 0; k <= 30; k++) { const a = lerp(-0.15, -1.45, k / 30 * eo(2.2, 2.55, u)); arc.push(proj(V3d(0.05 + 0.55 * Math.cos(a), -0.2 + 0.55 * Math.sin(a), 0.01), pcam)); }
    wobblyLine(fg, arc, C.acc, 4, oz, 50 + step); const q1 = arc[arc.length - 1], q0 = arc[arc.length - 3], an = Math.atan2(q1[1] - q0[1], q1[0] - q0[0]);
    fg.save(); fg.globalAlpha = oz; fg.strokeStyle = C.acc; fg.lineWidth = 4; fg.lineCap = 'round'; fg.translate(...q1); fg.rotate(an); fg.beginPath(); fg.moveTo(-16, -10); fg.lineTo(2, 0); fg.lineTo(-16, 10); fg.stroke(); fg.restore(); }
  lab('k_2', V3d(0.18, -0.80, 0.01), -150, -150, oz, 9);
  if (gb > 0) { fg.save(); fg.globalAlpha = 0.5 * gb; fg.drawImage(FIGC, 0, 0); fg.restore(); }
  show('k_tag', { x: 80, y: 64, op: 1 - swg }); vignette(fg, 0.3);
  pcam.fov = 26;
}

// ------------------------------------------------------------------ echo pull-out: the same room in 3D (ink-line bed, wall, sunlit window), tube figure, the hip line kept in space
const lin = (r, g, b) => new THREE.Color().setRGB(r, g, b);          // linear colour (the renderer encodes to sRGB)
const roomG = new THREE.Group(); roomG.visible = false; scene.add(roomG);
const WALL_Y = 0.93, WX = [-1.05, -0.35], WZ = [0.95, 1.60];
{ const wall = new THREE.Mesh(new THREE.PlaneGeometry(7, 3.2), new THREE.MeshBasicMaterial({ color: lin(0.006, 0.009, 0.016) })); wall.rotation.x = Math.PI / 2; wall.position.set(-0.4, WALL_Y + 0.01, 1.6); roomG.add(wall);
  const gl = new THREE.Mesh(new THREE.PlaneGeometry(WX[1] - WX[0], WZ[1] - WZ[0]), new THREE.MeshBasicMaterial({ color: lin(1, 0.62, 0.30) })); gl.rotation.x = Math.PI / 2; gl.position.set((WX[0] + WX[1]) / 2, WALL_Y, (WZ[0] + WZ[1]) / 2); roomG.add(gl); roomG.userData.glass = gl;
  const fr = []; const y = WALL_Y - 0.01, xm = (WX[0] + WX[1]) / 2, zm = (WZ[0] + WZ[1]) / 2;
  fr.push(WX[0], y, WZ[0], WX[1], y, WZ[0], WX[1], y, WZ[0], WX[1], y, WZ[1], WX[1], y, WZ[1], WX[0], y, WZ[1], WX[0], y, WZ[1], WX[0], y, WZ[0], xm, y, WZ[0], xm, y, WZ[1], WX[0], y, zm, WX[1], y, zm);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(fr, 3)); roomG.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x3A4656 }))); }
// sun shafts: thin additive sheets running from the window into the room, fading with distance
const SUN_D = new THREE.Vector3(0.30, -1.0, -0.62).normalize();
const shaftTex = (() => { const c = document.createElement('canvas'); c.width = 256; c.height = 4; const g = c.getContext('2d'); const r = g.createLinearGradient(0, 0, 256, 0); r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(0.6, 'rgba(255,255,255,.35)'); r.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = r; g.fillRect(0, 0, 256, 4); return new THREE.CanvasTexture(c); })();
const SHAFTS = [];
function shaft(a, b, len, op) {   // sheet spanned by segment a-b (on the window) and the sun direction
  const pts = [a, b, b.clone().addScaledVector(SUN_D, len), a.clone().addScaledVector(SUN_D, len)], g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pts.flatMap(p => [p.x, p.y, p.z]), 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 0, 1, 1, 1, 1, 0], 2)); g.setIndex([0, 1, 2, 0, 2, 3]);
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: shaftTex, color: lin(1, 0.66, 0.36), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  roomG.add(m); SHAFTS.push({ m, op }); }
for (let k = 0; k < 6; k++) { const z = lerp(WZ[0] + 0.05, WZ[1] - 0.05, k / 5); shaft(new THREE.Vector3(WX[0], WALL_Y - 0.02, z), new THREE.Vector3(WX[1], WALL_Y - 0.02, z), 2.3, 0.10); }
for (let k = 0; k < 4; k++) { const x = lerp(WX[0] + 0.05, WX[1] - 0.05, k / 3); shaft(new THREE.Vector3(x, WALL_Y - 0.02, WZ[0]), new THREE.Vector3(x, WALL_Y - 0.02, WZ[1]), 2.3, 0.10); }
{ // the window's patch of light on the bed (window corners carried along the sun direction to the mattress top)
  const hit = p => { const k = (0.425 - p.z) / SUN_D.z; return p.clone().addScaledVector(SUN_D, k); };
  const c = [V3d(WX[0], WALL_Y, WZ[0]), V3d(WX[1], WALL_Y, WZ[0]), V3d(WX[1], WALL_Y, WZ[1]), V3d(WX[0], WALL_Y, WZ[1])].map(hit), g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(c.flatMap(p => [p.x, p.y, p.z]), 3)); g.setIndex([0, 1, 2, 0, 2, 3]);
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: lin(1, 0.62, 0.32), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide })); roomG.add(m); roomG.userData.patch = m; }
const sunLight = new THREE.DirectionalLight(0xffc38a, 0); sunLight.position.copy(SUN_D.clone().multiplyScalar(-5)); scene.add(sunLight);
// tube figure (same proportions as the flat pictogram) and the hip line as a tube
const tubeG = new THREE.Group(); tubeG.visible = false; scene.add(tubeG);
const tubeM = new THREE.MeshStandardMaterial({ color: '#DDE5EE', roughness: 0.95, metalness: 0, emissive: new THREE.Color('#4A5562') });
const CYL = new THREE.CylinderGeometry(1, 1, 1, 20), SPH = new THREE.SphereGeometry(1, 24, 16), TB = {};
['torso', 'head', 'pelvis', 'thL', 'thR', 'shL', 'shR', 'ftL', 'ftR', 'uaL', 'uaR', 'faL', 'faR', 'kL', 'kR', 'aL', 'aR', 'eL', 'eR', 'sL', 'sR', 'hL', 'hR'].forEach(k => { TB[k] = new THREE.Mesh(k.length === 2 && 'kaesh'.includes(k[0]) || k === 'head' || k === 'pelvis' ? SPH : CYL, tubeM); tubeG.add(TB[k]); });
const _up = new THREE.Vector3(0, 1, 0);
function tseg(m, p, q, rx, rz = rx) { const d = q.clone().sub(p), L = d.length(); m.position.copy(p).add(q).multiplyScalar(0.5); m.quaternion.setFromUnitVectors(_up, d.normalize()); m.scale.set(rx, L, rz); }
function tball(m, p, r, sx = 1, sy = 1, sz = 1) { m.position.copy(p); m.quaternion.identity(); m.scale.set(r * sx, r * sy, r * sz); }
function setTube(J) {
  const P = (p, y) => V3d(p[0], y, p[1]);
  tseg(TB.torso, P(J.H, 0), P(J.S, 0), 0.062, 0.115); tball(TB.pelvis, P(J.H, 0), 0.07, 1, 1.5, 1); tball(TB.head, P(J.hd, 0), 0.098);
  for (const [s, y] of [['L', -0.085], ['R', 0.085]]) { tseg(TB['th' + s], P(J.H, y), P(J.K, y), 0.044); tseg(TB['sh' + s], P(J.K, y), P(J.A, y), 0.044); tball(TB['k' + s], P(J.K, y), 0.044); tball(TB['a' + s], P(J.A, y), 0.044);
    tseg(TB['ft' + s], P(J.heel, y), P(J.toe, y), 0.028); }
  for (const [s, ys, yh] of [['L', -0.15, -0.02], ['R', 0.15, 0.14]]) { const S = P(J.S, ys), Hd = V3d(J.Hd[0], yh, J.Hd[1]), E = P(J.E, (ys + yh) / 2);
    tseg(TB['ua' + s], S, E, 0.034); tseg(TB['fa' + s], E, Hd, 0.034); tball(TB['s' + s], S, 0.036); tball(TB['e' + s], E, 0.034); tball(TB['h' + s], Hd, 0.036); }
}
const hipTube = (() => { const pts = []; for (let x = 0; x <= FR.length - 1; x += 0.5) { const h = poseAt(x).Hp; pts.push(V3d(h[0], -0.12, h[1])); }
  const curve = new THREE.CatmullRomCurve3(pts), g1 = new THREE.TubeGeometry(curve, 80, 0.009, 10), g2 = new THREE.TubeGeometry(curve, 80, 0.03, 10);
  const a = new THREE.Mesh(g1, new THREE.MeshBasicMaterial({ color: lin(0.1, 0.75, 0.95), transparent: true, opacity: 0 })), b = new THREE.Mesh(g2, new THREE.MeshBasicMaterial({ color: lin(0.1, 0.6, 0.9), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
  tubeG.add(a, b); return [a, b]; })();
const POP = ['#19D3F0', '#19D3F0', '#19D3F0', '#FFB020', '#19D3F0', '#19D3F0'];
const RINGS = Array.from({ length: 6 }, () => { const m = new THREE.Mesh(new THREE.RingGeometry(0.97, 1.0, 96), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  m.position.set(0.40, 0.05, 0.003); scene.add(m); return m; });
const BLOBS = Array.from({ length: 7 }, (_, i) => ({ c: POP[i % 6], x: 0.15 + 0.7 * ((i * 0.618) % 1), y: 0.2 + 0.6 * ((i * 0.381 + 0.2) % 1), r: 420 + 160 * ((i * 0.77) % 1), sp: 0.12 + 0.05 * i }));
function aurora(g, t, a) {   // soft moving colour fields on near-black
  if (a <= 0) return; g.save(); g.globalAlpha = a; g.fillStyle = '#0B0A14'; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'lighter';
  for (const b of BLOBS) { const x = (b.x + 0.06 * Math.sin(t * b.sp * 6 + b.y * 9)) * W, y = (b.y + 0.05 * Math.cos(t * b.sp * 5 + b.x * 7)) * H, r = b.r * (1 + 0.08 * Math.sin(t * 2 * Math.PI + b.x * 6));
    const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, b.c + 'B0'); gr.addColorStop(0.55, b.c + '30'); gr.addColorStop(1, b.c + '00'); g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); }
  g.globalCompositeOperation = 'source-over'; const v = g.createRadialGradient(W * 0.6, H * 0.65, 200, W * 0.6, H * 0.65, 900); v.addColorStop(0, 'rgba(8,8,16,.45)'); v.addColorStop(1, 'rgba(8,8,16,0)'); g.fillStyle = v; g.fillRect(0, 0, W, H); g.restore(); }
function pulseRings(t, a) {   // one ring per beat from the seat's base, cycling through the colours
  RINGS.forEach((m, i) => { const b0 = Math.floor(t / BEAT) - i, age = t - b0 * BEAT, k = age / 3.0; if (k < 0 || k > 1 || a <= 0) { m.material.opacity = 0; return; }
    m.scale.setScalar(0.35 + 2.6 * Math.pow(k, 0.7)); m.material.color.set(POP[((b0 % 6) + 6) % 6]); m.material.opacity = a * 0.55 * (1 - k); }); }
function echoPull(t, R, dawn) {   // t: echo clock; the person and the room fade, the seat alone turns in a pulsing colour field
  const p = ss(42.3, 44.9, t); if (p <= 0) return null;
  hipTube[0].material.opacity = 0.9 * (1 - ss(44.6, 45.3, t)); hipTube[1].material.opacity = 0.3 * (1 - ss(44.6, 45.3, t)); tubeG.visible = true;
  Object.values(TB).forEach(m => m.visible = false);
  const spin = 0.10 * ss(44.4, 46.0, t) * (t - 44.4);
  const T0 = V3d(0.55, 0, 0.85), T1 = V3d(0.38, 0.05, 0.55), T = T0.clone().lerp(T1, p), az = lerp(-Math.PI / 2, -0.95, p) + spin, el = lerp(0, 0.30, p);
  const dist = Math.exp(lerp(Math.log(40), Math.log(4.4), p)), halfH = lerp(0.95, 4.4 * Math.tan(13 * Math.PI / 180), p);
  pcam.fov = 2 * Math.atan(halfH / dist) * 180 / Math.PI; pcam.position.set(T.x + dist * Math.cos(el) * Math.cos(az), T.y + dist * Math.cos(el) * Math.sin(az), T.z + dist * Math.sin(el)); pcam.lookAt(T);
  pcam.setViewOffset(W, H, -260 * p, 0, W, H); pcam.updateProjectionMatrix();
  pulseRings(t, ss(42.6, 43.2, t));
  return { cam: pcam, p };
}

// ------------------------------------------------------------------ merged "how it moves": the four steps, 2.5D turning to the flat side view, the path and arrows inside step 03
const MSTEPS = [['挪上座板', '座板和床一样高，平移过去'], ['握紧开关', '握紧才升'], ['一起起身', '托住臀部和大腿，人不往前滑'], ['松手即停', '座板停在原位，坐回也接得住']];
T('m_tag', 'HOW IT MOVES / 起身', mono(24));
MSTEPS.forEach(([a, b], i) => {
  T('m_n' + i, '0' + (i + 1), { cls: 'lat', s: { fontSize: '170px', fontWeight: 900, color: 'transparent', WebkitTextStroke: '3px #FFFFFF', lineHeight: 1 } });
  T('m_a' + i, a, { s: { ...big(84), color: '#fff' } }); T('m_b' + i, b, { s: { ...big(38, 500), color: '#A8B4C4' } });
});
const MT = [0, 1.5, 2.5, 5.0, 6.5];   // step starts (local)
function secM(u) {   // u: 0..6.5
  fillBG(C.ink); grid(bg, '#3A5A70', 60, 0.07);
  const rk = ss(2.6, 4.6, u), hh = lerp(0.74, 0.95, rk), cx = lerp(0.20, 0.12, rk), cz = lerp(0.70, 0.86, rk), V0 = sideView(cx, cz, hh);
  const q = 1 - ss(1.4, 2.6, u); let V = V0;
  if (q > 0.001) { const Tt = V3d(cx, 0, cz - 0.10 * q), az = -Math.PI / 2 + F25.az * q, el = F25.el * q, dist = Math.exp(lerp(Math.log(40), Math.log(F25.dist), q));
    pcam.fov = 2 * Math.atan(hh * lerp(1, F25.hh, q) / dist) * 180 / Math.PI; pcam.position.set(Tt.x + dist * Math.cos(el) * Math.cos(az), Tt.y + dist * Math.cos(el) * Math.sin(az), Tt.z + dist * Math.sin(el)); pcam.lookAt(Tt); pcam.clearViewOffset(); pcam.updateProjectionMatrix();
    V = { cam: pcam, sc: V0.sc, map: p => proj(V3d(p[0], 0, p[1]), pcam) }; }
  sketchG.visible = q > 0.01; SK.lines.forEach(l => { l.visible = true; l.material.opacity = (SK.jit.includes(l) ? 0.25 : 0.75) * q; l.position.set(0, 0, 0); });
  Object.values(SKB).forEach(m => { m.visible = q > 0.01 && m !== SKB.hb && m !== SKB.pl && m !== SKB.duv; m.children.forEach(l => l.geometry.setDrawRange(0, Infinity)); });
  // pose: scoot (01), hold (02), rise (03), release (04)
  let pose, hands = HAND_BAR, s = 0, swv = 0, rel = 0;
  if (u < 1.5) { const k = ss(0.1, 1.2, u); pose = scootPose(k); const lap = joints(pose, null).Hd; const hk = ss(0.6, 1.35, u); hands = lerpA(lap, HAND_BAR, hk); hands[1] += 0.08 * Math.sin(Math.PI * hk); }
  else if (u < 2.5) { pose = rise(-1).pose; swv = ss(1.95, 2.05, u) * (0.75 + 0.25 * Math.cos((u - 2.0) * 4 * Math.PI)); }
  else { const kf = u < 2.75 ? lerp(-1, 0, (u - 2.5) / 0.25) : lerp(0, FR.length - 1, ss(2.75, 4.8, u)), R = rise(kf); pose = R.pose; s = R.s; swv = u < 5.0 ? 1 : 0;
    if (u >= 5.0) { rel = eo(5.0, 5.35, u); const S = joints(pose, null).S; hands = lerpA(HAND_BAR, [S[0] + 0.03, S[1] - Lua - Lfa * 0.9], rel); } }
  setLook('dark', { shell: { op: 0 } }); setMech(s); disc.visible = false; setSwitch(swv);
  bg.save(); bg.globalAlpha = 1 - q; floor2D(bg, V0.map, '#2C3644'); drawBed2D(bg, V0.map, V0.sc, 0.42, false, -1.9); bg.restore();
  const J = joints(pose, hands);
  tubeG.visible = false; if (q > 0.01) { setTube(J); figPass(V.cam); }
  renderGL(V.cam);
  if (q > 0.01) { fg.save(); fg.globalAlpha = 0.5 * q; fg.drawImage(FIGC, 0, 0); fg.restore(); }
  // step 03: the seat's path, a ghost of the seat on each beat, arrows
  if (u >= 2.5) { const pts = pathTo(s), fa = 1 - ss(6.0, 6.4, u); fg.save(); fg.globalAlpha = fa; fg.lineCap = 'round'; fg.lineJoin = 'round';
    fg.strokeStyle = 'rgba(25,211,240,.25)'; fg.lineWidth = 16; fg.beginPath(); pts.forEach((p, i) => { const qq = V.map(p); i ? fg.lineTo(...qq) : fg.moveTo(...qq); }); fg.stroke(); fg.strokeStyle = C.acc; fg.lineWidth = 4; fg.stroke();
    for (let bt = 3.0; bt <= Math.min(u, 4.75); bt += BEAT) { const kb = lerp(0, FR.length - 1, ss(2.75, 4.8, bt)), sb = rise(kb).s, poly = seatOutline(sb); fg.globalAlpha = fa * 0.55 * Math.exp(-(u - bt) * 0.6); fg.strokeStyle = C.acc; fg.lineWidth = 2.5; fg.beginPath(); poly.forEach((p, i) => { const qq = V.map(p); i ? fg.lineTo(...qq) : fg.moveTo(...qq); }); fg.closePath(); fg.stroke(); }
    fg.restore(); }
  if (q < 0.99) { fg.save(); fg.globalAlpha = 1 - q; ghostFig(fg, J, V0.map, V0.sc, '#FFFFFF', 0.10 * (1 - q), 5); fg.restore(); }
  const q0 = kinAt(0), qr = kinAt(S_REL), A0 = [q0[1] / 1000, q0[2] / 1000], AR = [qr[1] / 1000, qr[2] / 1000];
  const arrow = (a, b, k, id, lab) => { if (k <= 0) return; const p = V.map(a), qq = V.map(b), e = [lerp(p[0], qq[0], k), lerp(p[1], qq[1], k)]; fg.save(); fg.strokeStyle = C.acc; fg.fillStyle = C.acc; fg.lineWidth = 4; fg.beginPath(); fg.moveTo(...p); fg.lineTo(...e); fg.stroke();
    const an = Math.atan2(qq[1] - p[1], qq[0] - p[0]); fg.translate(...e); fg.rotate(an); fg.beginPath(); fg.moveTo(4, 0); fg.lineTo(-16, -10); fg.lineTo(-16, 10); fg.fill(); fg.restore(); show(id, { x: lab[0], y: lab[1], ax: 0.5, ay: 0.5, op: k }); };
  const fa = 1 - ss(4.9, 5.1, u), u1 = eo(3.25, 3.5, u) * fa, u2 = eo(3.5, 3.75, u) * fa, u3 = eo(3.75, 4.0, u) * fa;
  const yb = A0[1] - 0.20; arrow([A0[0] - 0.02, yb], [AR[0] + 0.04, yb], u1, 'f_a0', V0.map([(A0[0] + AR[0]) / 2, yb - 0.07]));
  const xr = AR[0] + 0.30; arrow([xr, A0[1]], [xr, AR[1] + 0.02], u2, 'f_a1', V0.map([xr + 0.10, (A0[1] + AR[1]) / 2]));
  if (u3 > 0) { const c = V0.map([AR[0], AR[1]]), rr = 0.17 * V0.sc; fg.save(); fg.strokeStyle = C.acc; fg.lineWidth = 4; fg.globalAlpha = u3; fg.beginPath(); fg.arc(c[0], c[1], rr, Math.PI - 0.30 * u3, Math.PI); fg.stroke(); fg.restore(); show('f_a2', { x: c[0] - rr - 30, y: c[1] + 10, ax: 1, ay: 0.5, op: u3 }); }
  // step 02: grip pulses on the beats
  if (u >= 1.5 && u < 2.75) { const c = V.map(HAND_BAR); for (let bt = 2.0; bt <= u; bt += BEAT) { const k = u - bt; if (k > 0.5) continue; fg.save(); fg.strokeStyle = C.amb; fg.globalAlpha = 1 - k / 0.5; fg.lineWidth = 5; fg.beginPath(); fg.arc(c[0], c[1], 26 + 90 * k, 0, 7); fg.stroke(); fg.restore(); } }
  // step 04: seat held, STOP
  if (u >= 5.0) { const poly = seatOutline(s).map(V0.map), xs = poly.map(p => p[0]), ys = poly.map(p => p[1]), x0 = Math.min(...xs) - 16, x1 = Math.max(...xs) + 16, y0 = Math.min(...ys) - 16, y1 = Math.max(...ys) + 16, L = 22;
    const k = eback(5.0, 5.2, u); fg.save(); fg.strokeStyle = C.red; fg.lineWidth = 5; fg.globalAlpha = clamp(k); fg.beginPath();
    for (const [x, y, dx, dy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x0, y1, 1, -1], [x1, y1, -1, -1]]) { fg.moveTo(x + dx * L, y); fg.lineTo(x, y); fg.lineTo(x, y + dy * L); } fg.stroke(); fg.restore();
    show('g_stop', { x: x0 - 20, y: y0 - 6, ay: 1, ax: 1, op: clamp(k), sc: k }); }
  show('m_tag', { x: 80, y: 64, op: 1 });
  for (let i = 0; i < 4; i++) { const a = MT[i], b = MT[i + 1], o = win(u, a, b, 0.12, 0.08), k = eo(a, a + 0.25, u);
    show('m_n' + i, { x: 110, y: 120, op: o, dy: (1 - k) * 40 }); show('m_a' + i, { x: 420, y: 140, op: o, dx: (1 - k) * 50 }); show('m_b' + i, { x: 424, y: 250, op: o * eo(a + 0.1, a + 0.35, u) }); }
  for (let i = 0; i < 4; i++) { const f = clamp((u - MT[i]) / (MT[i + 1] - MT[i])); bg.fillStyle = '#2A3442'; bg.fillRect(120 + i * 190, 1010, 170, 6); bg.fillStyle = C.acc; bg.fillRect(120 + i * 190, 1010, 170 * f, 6); }
}

const SH = f => t => f(t - 10), EC = t => secE(t < 23 ? 12 + 2 * (t - 21) : 16 + (t - 23)), S1 = f => t => f(t - 1);   // assembly at double speed (parts land on 16ths), then normal
const SECS = [[0, 4, secA], [4, 8, secB], [8, 11, secRain], [11, 13, S1(secD)], [13, 21, S1(secX)], [21, 25, EC], [25, 28.5, t => secCtx(t - 25)], [28.5, 35, t => secM(t - 28.5)], [35, 38, t => secH(t - 5)], [38, 44.01, t => secEcho(t + 2)]];
window.renderAt = function (t) {
  resetFrame(); for (const c in PG) PG[c].position.set(0, 0, 0);
  bedG.visible = false; floorGrid.visible = false; openZone.material.opacity = 0; ozEdge.material.opacity = 0; pcam.fov = 26;
  sketchG.visible = false; hatch.material.opacity = 0; roomG.visible = false; tubeG.visible = false; sunLight.intensity = 0; RINGS.forEach(m => m.material.opacity = 0); Object.values(TB).forEach(m => m.visible = true); for (const c in PG) { const el = PG[c].children[1]; if (el) el.position.set(0, 0, 0); }
  if (window.CTX !== undefined) { secCtx(window.CTX); return; }
  for (const [a, b, f] of SECS) if (t >= a && t < b) { f(t); break; }
};
window.DUR = DUR;
// preload every glyph we use in every weight, then signal ready
(async () => {
  const all = Array.from(txt.querySelectorAll('.t')).map(e => e.textContent).join('') + '0123456789T+.s ';
  await Promise.all(['500', '700', '900'].flatMap(w => [document.fonts.load(`${w} 40px "Noto Sans SC"`, all), document.fonts.load(`${w} 40px "Inter Tight"`, all)]).concat([document.fonts.load('500 40px "JetBrains Mono"', all)]));
  await document.fonts.ready; RANK = heroRanks(); document.title = 'ready';
})();
