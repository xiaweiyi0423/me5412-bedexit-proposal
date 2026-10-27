// cad/mechanism.html script: 3D assembly (three.js), 2D mechanism animation, balloons, load-path stepper, BOM filter, Q&A.
// D is injected by build_mech_page.py (mm, degrees; world x out from the bed, y toward the bed head, z up).
const F = D.frames, SMAX = F[F.length - 1][0], E = D.e, NF = D.nf;
const frameAt = s => { let i = 0; while (i < F.length - 2 && F[i + 1][0] < s) i++;
  const a = F[i], b = F[i + 1], t = Math.max(0, Math.min(1, (s - a[0]) / ((b[0] - a[0]) || 1))); return a.map((v, k) => v + t * (b[k] - v)); };
const add = (p, a, u, b, v) => [p[0] + a * u[0] + (b || 0) * (v ? v[0] : 0), p[1] + a * u[1] + (b || 0) * (v ? v[1] : 0)];
const Wt = (Q, phi, p) => { const a = phi * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [Q[0] + c * p[0] + s * p[1], Q[1] - s * p[0] + c * p[1]]; };
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const bomRows = [...document.querySelectorAll("#bom tbody tr")];
function markBom(codes) { bomRows.forEach(tr => tr.classList.toggle("on", codes.includes(tr.children[1].textContent.trim()))); }

// ------------------------------------------------------------------ tooltip for balloons and part codes
const tip = document.createElement("div"); tip.className = "tip"; tip.hidden = true; document.body.appendChild(tip);
function showTip(code, x, y) {
  const n = D.names[code]; if (!n) return;
  tip.innerHTML = `<span class="code">${code}</span> <b></b><br><span class="m"></span>`; tip.querySelector("b").textContent = n[0]; tip.querySelector(".m").textContent = n[1];
  tip.hidden = false; const r = tip.getBoundingClientRect();
  tip.style.left = Math.min(Math.max(8, x + 12), window.innerWidth - r.width - 8) + "px"; tip.style.top = Math.min(y + 12, window.innerHeight - r.height - 8) + "px";
}
document.addEventListener("click", ev => {
  const b = ev.target.closest(".bal"); document.querySelectorAll(".bal.on").forEach(x => x.classList.remove("on"));
  if (b) { b.classList.add("on"); showTip(b.dataset.code, ev.clientX, ev.clientY); markBom([b.dataset.code]); if (window.select3D) window.select3D([b.dataset.code], false); }
  else if (!ev.target.closest(".tip")) tip.hidden = true;
});
window.addEventListener("scroll", () => { tip.hidden = true; }, { passive: true });

// ------------------------------------------------------------------ 3D assembly
(function init3D() {
  const box = document.getElementById("v3"), info = document.getElementById("info"), legend = document.getElementById("legend");
  const fail = msg => { box.insertAdjacentHTML("beforeend", `<div class="fail">${msg}</div>`); document.getElementById("p3").disabled = true; };
  if (!window.THREE || !THREE.OrbitControls) { fail("3D 没能加载（网络或浏览器问题）。看第 3 节的三视图也能看懂。"); return; }
  let renderer; try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); } catch (e) { fail("这个浏览器不支持 WebGL。看第 3 节的三视图也能看懂。"); return; }
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1)); box.prepend(renderer.domElement);
  const css = getComputedStyle(document.documentElement), col = n => new THREE.Color(css.getPropertyValue(n).trim() || "#888");
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(30, 4 / 3, 10, 30000); camera.up.set(0, 0, 1);
  const HOME = { pos: [2100, -2150, 1500], tgt: [300, 80, 420] };
  camera.position.set(...HOME.pos); const controls = new THREE.OrbitControls(camera, renderer.domElement); controls.target.set(...HOME.tgt); controls.enableDamping = false; controls.update();
  const hemi = new THREE.HemisphereLight(0xffffff, 0x8a8f96, 0.85); hemi.position.set(0, 0, 1); scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xffffff, 0.65); sun.position.set(900, -1400, 1800); scene.add(sun);
  const mats = {};
  const mat = (token, op = 1) => { const k = token + op; if (!mats[k]) mats[k] = new THREE.MeshStandardMaterial({ color: col(token), roughness: 0.65, metalness: 0.08, side: THREE.DoubleSide, transparent: op < 1, opacity: op, depthWrite: op >= 1 }); return mats[k]; };
  const V2 = p => new THREE.Vector2(p[0], p[1]);
  const exXZ = (pts, y0, y1, holes) => { const sh = new THREE.Shape(pts.map(V2)); (holes || []).forEach(h => sh.holes.push(new THREE.Path(h.map(V2))));
    const g = new THREE.ExtrudeGeometry(sh, { depth: y1 - y0, bevelEnabled: false }); g.applyMatrix4(new THREE.Matrix4().set(1, 0, 0, 0, 0, 0, 1, y0, 0, 1, 0, 0, 0, 0, 0, 1)); return g; };
  const boxG = (x0, x1, y0, y1, z0, z1) => new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0).translate((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
  const cylY = (cx, cz, y0, y1, r) => new THREE.CylinderGeometry(r, r, y1 - y0, 40).translate(cx, (y0 + y1) / 2, cz);
  const parts = {}, pickable = [];
  const put = (geo, m, code, parent, name) => { const me = new THREE.Mesh(geo, m); me.userData = { code, name }; (parent || scene).add(me);
    if (code) { (parts[code] = parts[code] || []).push(me); pickable.push(me); } return me; };
  const rectEN = (c, ae, an) => [add(c, -ae, E, -an, NF), add(c, ae, E, -an, NF), add(c, ae, E, an, NF), add(c, -ae, E, an, NF)];
  // static: bed, floor, base, footplate, handrail, housing, rails, screw, motor, B bracket
  put(boxG(-900, 0, -700, 800, 0, 420), mat("--bed", 0.55), null, null, "床"); put(boxG(-900, 1100, -800, 900, -4, 0), mat("--paper"), null, null, "地面");
  for (const g of [boxG(30, 780, -270, -210, 5, 35), boxG(30, 780, 320, 380, 5, 35), boxG(30, 90, -210, 320, 5, 35), boxG(720, 780, -210, 320, 5, 35), boxG(30, 780, 230, 260, 5, 35)]) put(g, mat("--steel"), "B1");
  put(boxG(200, 620, -220, 220, 35, 47), mat("--steel2"), "B2");
  put(boxG(670, 730, 270, 330, 35, 950), mat("--steel"), "B4"); put(cylY(700, 950, -50, 330, 19), mat("--ink2"), "B5");
  put(exXZ(D.housing, 336, 351), mat("--steel2"), "H1");
  const shellParts = [put(exXZ(D.housing, 250, 253, [D.slot]), mat("--blue2", 0.28), "H2"), put(exXZ(D.housing, 356, 358), mat("--blue2", 0.12), "H4")];
  for (const r of [D.rail1, D.rail2]) put(exXZ([add(r[0], -7.5, NF), add(r[1], -7.5, NF), add(r[1], 7.5, NF), add(r[0], 7.5, NF)], 321, 336), mat("--ink"), "D1");
  const sv = [D.screw[1][0] - D.screw[0][0], 0, D.screw[1][1] - D.screw[0][1]], sl = Math.hypot(sv[0], sv[2]);
  const scr = put(new THREE.CylinderGeometry(8, 8, sl, 20), mat("--red"), "D2"); scr.position.set((D.screw[0][0] + D.screw[1][0]) / 2, 322, (D.screw[0][1] + D.screw[1][1]) / 2);
  scr.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(sv[0] / sl, 0, sv[2] / sl));
  put(exXZ(D.motor, 282, 350), mat("--ink2"), "D4");
  put(boxG(D.B[0] - 30, D.B[0] + 30, 260, 292, D.B[1] - 36, D.B[1] + 8), mat("--steel"), "L3");
  // carriage weldment group (moves with pin 1)
  const G2 = new THREE.Group(); scene.add(G2); const o = [0, 0], pl = D.plate, plOut = [add(o, pl.e[1], E, pl.nf[0], NF), add(o, pl.e[1], E, pl.nf[1], NF), add(o, pl.e[0], E, pl.nf[1], NF)];
  for (let k = 0; k <= 8; k++) { const a = (Math.PI / 2) * k / 8; plOut.push([-pl.rc * (Math.cos(a) * E[0] + Math.sin(a) * NF[0]), -pl.rc * (Math.cos(a) * E[1] + Math.sin(a) * NF[1])]); }
  put(exXZ(plOut, 288, 308), mat("--blue2"), "C1", G2);
  for (const on of [0, 150]) for (const se of [0, 150]) put(exXZ(rectEN(add(o, se, E, on, NF), 30.7, 17), 308, 330), mat("--blue"), "C2", G2);
  put(exXZ(rectEN(add(o, 75, E, 75, NF), 22, 14), 308, 336), mat("--ink2"), "C3", G2);
  put(cylY(0, 0, 229, 308, 37.5), mat("--red", 0.45), "J3", G2);
  put(cylY(0, 0, 229, 246, 27.5), mat("--ink"), "J2", G2); put(cylY(0, 0, 290, 307, 27.5), mat("--ink"), "J2", G2);
  // seat group (moves with Q, turns by phi about y)
  const G3 = new THREE.Group(); scene.add(G3); const S = D.seat;
  put(exXZ(S.foamr, -220, 220), mat("--foam"), "S1", G3); put(exXZ(S.foamf, -220, 220), mat("--foam2"), "S2", G3);
  put(exXZ(S.board, -220, 220), mat("--wood"), "S4", G3); put(exXZ(S.spacer, -220, 220), mat("--wood"), "S4", G3);
  put(exXZ(S.arm, 180, 200), mat("--steel"), "S6", G3); put(exXZ(S.arm, -200, -180), mat("--steel"), "S6", G3);
  put(exXZ(S.beam, -205, 212), mat("--steel"), "S7", G3);
  put(exXZ([[-30, -130], [45, -130], [45, -32], [-30, -32]], 212, 226), mat("--steel"), "S8", G3);
  const c1 = D.c1s, c2 = D.c2s; put(cylY(c1[0], c1[1], 212, 318, 15), mat("--ink2"), "J1", G3); put(cylY(c1[0], c1[1], 212, 224, 37.5), mat("--ink2"), "J1", G3);
  const ax = [c2[0] - c1[0], c2[1] - c1[1]], al = Math.hypot(ax[0], ax[1]), nx = [-ax[1] / al * 15, ax[0] / al * 15];
  put(exXZ([[c1[0] + nx[0], c1[1] + nx[1]], [c2[0] + nx[0], c2[1] + nx[1]], [c2[0] - nx[0], c2[1] - nx[1]], [c1[0] - nx[0], c1[1] - nx[1]]], 258, 270), mat("--steel"), "J4", G3);
  // link
  const link = put(new THREE.CylinderGeometry(10, 10, 1, 20), mat("--ink2"), "L1"), rodA = put(new THREE.SphereGeometry(14.5, 20, 14), mat("--ink"), "L2"), rodB = put(new THREE.SphereGeometry(14.5, 20, 14), mat("--ink"), "L2");
  rodB.position.set(D.B[0], 275, D.B[1]);
  const up = new THREE.Vector3(0, 1, 0);
  function pose(s) {
    const f = frameAt(s), Q = [f[1], f[2]], phi = f[3], P1 = [f[4], f[5]], P2 = [f[6], f[7]];
    G2.position.set(P1[0], 0, P1[1]); G3.position.set(Q[0], 0, Q[1]); G3.rotation.set(0, phi * Math.PI / 180, 0);
    const a = new THREE.Vector3(P2[0], 275, P2[1]), b = new THREE.Vector3(D.B[0], 275, D.B[1]), d = b.clone().sub(a), L = d.length();
    link.position.copy(a.clone().add(b).multiplyScalar(0.5)); link.quaternion.setFromUnitVectors(up, d.normalize()); link.scale.set(1, L, 1); rodA.position.copy(a);
  }
  // selection
  let sel = [];
  function select(codes, fromPick) {
    for (const c of sel) for (const m of parts[c] || []) { m.material = m.userData.base; }
    sel = codes.filter(c => parts[c]);
    for (const c of sel) for (const m of parts[c]) { m.userData.base = m.userData.base || m.material; const h = m.userData.base.clone(); h.emissive = col("--hl"); h.emissiveIntensity = 0.55; m.material = h; }
    [...legend.children].forEach(x => x.classList.toggle("on", sel.includes(x.dataset.code)));
    if (sel.length === 1) { const n = D.names[sel[0]] || ["", ""]; info.innerHTML = `<span class="code">${sel[0]}</span><br><b></b><br><span class="cap"></span>`; info.querySelector("b").textContent = n[0]; info.querySelector(".cap").textContent = n[1]; }
    else if (sel.length > 1) { info.innerHTML = `<span class="code">${sel.join(" · ")}</span><br><b>已高亮 ${sel.length} 个零件</b><br><span class="cap"></span>`; info.querySelector(".cap").textContent = sel.map(c => (D.names[c] || [c])[0]).join("、"); }
    if (fromPick !== undefined) markBom(sel);
    render();
  }
  for (const m of pickable) m.userData.base = m.material;
  window.select3D = (codes, scroll) => { select(codes); if (scroll) document.getElementById("s1").scrollIntoView({ behavior: reduced ? "auto" : "smooth" }); };
  Object.keys(D.names).filter(c => parts[c]).forEach(c => { const bt = document.createElement("button"); bt.type = "button"; bt.className = "lg"; bt.dataset.code = c; bt.textContent = c;
    bt.title = D.names[c][0]; bt.onclick = () => select(sel.length === 1 && sel[0] === c ? [] : [c], true); legend.appendChild(bt); });
  const ray = new THREE.Raycaster(), ptr = new THREE.Vector2(); let down = null;
  renderer.domElement.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener("pointerup", e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return; const r = renderer.domElement.getBoundingClientRect();
    ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1); ray.setFromCamera(ptr, camera);
    const hit = ray.intersectObjects(pickable.filter(m => m.visible), false)[0]; select(hit ? [hit.object.userData.code] : [], true);
  });
  // render, resize, controls
  let w = 0, h = 0;
  function render() { renderer.render(scene, camera); }
  function size() { const r = box.getBoundingClientRect(); if (!r.width) return; if (r.width !== w || r.height !== h) { w = r.width; h = r.height; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); } render(); }
  new ResizeObserver(size).observe(box); controls.addEventListener("change", render);
  const r3 = document.getElementById("r3d"), p3 = document.getElementById("p3"); let s = 200, dir = 1, playing = false, last = 0, hold = 0;
  r3.value = s; pose(s); size();
  r3.oninput = () => { s = +r3.value; pose(s); render(); if (playing) toggle(); };
  function tick(t) { if (!playing) return; const dt = last ? (t - last) / 1000 : 0; last = t;
    if (hold > 0) hold -= dt; else { s += dir * 60 * dt; if (s >= SMAX) { s = SMAX; dir = -1; hold = 1; } if (s <= 0) { s = 0; dir = 1; hold = 1; } }
    r3.value = s; pose(s); render(); requestAnimationFrame(tick); }
  function toggle() { playing = !playing; p3.textContent = playing ? "暂停" : "播放"; last = 0; if (playing) requestAnimationFrame(tick); }
  p3.onclick = toggle;
  const shellBtn = document.getElementById("shell"); shellBtn.onclick = () => { const vis = !shellParts[0].visible; shellParts.forEach(m => m.visible = vis); shellBtn.textContent = vis ? "隐藏机构箱外壳" : "显示机构箱外壳"; render(); };
  document.getElementById("reset3").onclick = () => { camera.position.set(...HOME.pos); controls.target.set(...HOME.tgt); controls.update(); render(); };
})();
document.querySelectorAll(".show3d").forEach(b => b.onclick = () => { const codes = b.dataset.hl.split(" "); markBom(codes); if (window.select3D) window.select3D(codes, true); });

// ------------------------------------------------------------------ 2D mechanism animation
(function init2D() {
  const XA = -160, XB = 830, ZB = 1000, ZA = -30, NS = "http://www.w3.org/2000/svg";
  const X = x => x - XA, Y = z => ZB - z, svg = document.getElementById("mech"); svg.setAttribute("viewBox", `0 0 ${XB - XA} ${ZB - ZA}`);
  const el = (tag, at, par) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); (par || svg).appendChild(e); return e; };
  const pts = a => a.map(p => `${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join(" ");
  const txt = (par, x, y, t, cls, anchor) => { const e = el("text", { x, y, class: cls || "lab", "text-anchor": anchor || "start" }, par); e.textContent = t; return e; };
  const gS = el("g", {}), gP = el("g", {}), gK = el("g", {}), gT = el("g", {});
  el("rect", { x: X(-160), y: Y(D.bed), width: 160, height: D.bed, class: "bed" }, gS); txt(gS, X(-150), Y(220), "床", "lab muted"); txt(gS, X(-150), Y(D.bed) - 8, "床垫面 420", "lab muted");
  el("rect", { x: X(-160), y: Y(0), width: XB - XA, height: 14, fill: "url(#hat)" }, gS); el("line", { x1: X(-160), y1: Y(0), x2: X(XB), y2: Y(0), class: "floor" }, gS);
  el("polygon", { points: pts(D.housing), class: "house" }, gP);
  el("rect", { x: X(D.base.x[0]), y: Y(D.base.h), width: D.base.x[1] - D.base.x[0], height: D.base.h, class: "base" }, gP);
  el("rect", { x: X(D.foot.x[0]), y: Y(D.foot.z[1]), width: D.foot.x[1] - D.foot.x[0], height: D.foot.z[1] - D.foot.z[0], class: "base" }, gP);
  for (const r of [D.rail1, D.rail2]) el("line", { x1: X(r[0][0]), y1: Y(r[0][1]), x2: X(r[1][0]), y2: Y(r[1][1]), class: "rail" }, gP);
  el("line", { x1: X(D.screw[0][0]), y1: Y(D.screw[0][1]), x2: X(D.screw[1][0]), y2: Y(D.screw[1][1]), class: "screw" }, gP);
  el("polygon", { points: pts(D.motor), class: "motor" }, gP);
  el("line", { x1: X(D.post.x), y1: Y(D.base.h), x2: X(D.post.x), y2: Y(D.post.top), class: "post" }, gP); el("circle", { cx: X(D.post.x), cy: Y(D.post.top), r: 19, class: "barc" }, gP);
  txt(gP, X(D.post.x) - 26, Y(D.post.top) - 24, "B5 横杆（垂直纸面）", "lab", "end"); txt(gP, X(530), Y(430), "H1 机构箱", "kcode");
  txt(gP, X(D.rail2[1][0]) + 14, Y(D.rail2[1][1]) + 6, "D1 导轨", "kcode"); txt(gP, X(D.motor[1][0]) + 12, Y(D.motor[1][1]) - 4, "D4 电机 D5 制动", "kcode");
  const r1 = D.rail1; el("polygon", { points: pts([r1[0], r1[1], add(r1[1], 14, NF), add(r1[0], 14, NF)]), fill: "url(#hat)" }, gK);
  el("line", { x1: X(r1[0][0]), y1: Y(r1[0][1]), x2: X(r1[1][0]), y2: Y(r1[1][1]), class: "kline" }, gK);
  const B = D.B; el("polygon", { points: pts([B, [B[0] - 26, B[1] - 36], [B[0] + 26, B[1] - 36]]), class: "kg" }, gK);
  el("rect", { x: X(B[0] - 36), y: Y(B[1] - 36), width: 72, height: 11, fill: "url(#hat)" }, gK);
  el("line", { x1: X(D.screw[0][0]), y1: Y(D.screw[0][1]), x2: X(D.screw[1][0]), y2: Y(D.screw[1][1]), class: "screw" }, gK);
  const mc = add(D.screw[1], 40, E); el("circle", { cx: X(mc[0]), cy: Y(mc[1]), r: 18, class: "kg" }, gK); txt(gK, X(mc[0]), Y(mc[1]) + 6, "M", "kl", "middle");
  txt(gK, X(mc[0]) + 26, Y(mc[1]) - 4, "电机 + 制动 + 限速"); txt(gK, X(r1[1][0]) + 14, Y(r1[1][1]) + 4, "P 导轨", "kl2"); txt(gK, X(B[0]) + 30, Y(B[1]) + 6, "S3（B）", "kl2");
  txt(gK, X(560), Y(60), "① 机架", "kl"); txt(gK, X(560), Y(60) + 22, "机构箱 + 底座 + 导轨，和床固定", "lab muted");
  el("polyline", { points: pts(F.map(f => [f[1], f[2]])), class: "trace" }, gT);
  const P = {};
  P.plate = el("polygon", { class: "plate" }, gP); P.carr = [0, 1, 2, 3].map(() => el("polygon", { class: "carr" }, gP)); P.nut = el("polygon", { class: "nut" }, gP);
  P.link = el("line", { class: "linkp" }, gP); P.armc2 = el("line", { class: "armc2" }, gP); P.seat = {};
  for (const k of ["beam", "arm", "board", "spacer", "foamf", "foamr"]) P.seat[k] = el("polygon", { class: k === "spacer" ? "board" : k }, gP);
  P.cart = el("circle", { r: D.cart, class: "cartc" }, gP); P.rodA = el("circle", { r: D.rod, class: "rodp" }, gP); el("circle", { r: D.rod, class: "rodp", cx: X(B[0]), cy: Y(B[1]) }, gP);
  P.cJ3 = txt(gP, 0, 0, "J3 轴承座筒", "kcode", "end"); P.cC1 = txt(gP, 0, 0, "C1 滑块板", "kcode"); P.cL1 = txt(gP, 0, 0, "L1 连杆", "kcode"); P.cS7 = txt(gP, 0, 0, "S7 横梁", "kcode", "end");
  P.kslider = el("polygon", { class: "kslider" }, gK); P.kseat = el("polygon", { class: "kseat" }, gK); P.kplate = el("line", { class: "kplate" }, gK); P.klink = el("line", { class: "klink" }, gK);
  P.j1 = el("circle", { r: 9, class: "kj" }, gK); P.j2 = el("circle", { r: 9, class: "kj" }, gK); el("circle", { r: 9, class: "kj", cx: X(B[0]), cy: Y(B[1]) }, gK);
  P.t2 = txt(gK, 0, 0, "② 滑块座", "kl"); P.t3 = txt(gK, 0, 0, "③ 座板", "kl"); P.t4 = txt(gK, 0, 0, "④ 连杆", "kl");
  P.tR = txt(gK, 0, 0, "R1 铰点 1", "kl2", "end"); P.tS = txt(gK, 0, 0, "S2 铰点 2", "kl2", "end");
  P.load = el("line", { class: "kload", "marker-end": "url(#fa)" }, gT); P.q = el("circle", { r: 7, class: "qdot" }, gT);
  const setL = (l, a, b) => { l.setAttribute("x1", X(a[0])); l.setAttribute("y1", Y(a[1])); l.setAttribute("x2", X(b[0])); l.setAttribute("y2", Y(b[1])); };
  const setC = (c, p) => { c.setAttribute("cx", X(p[0])); c.setAttribute("cy", Y(p[1])); };
  const setT = (t, p, dx, dy) => { t.setAttribute("x", X(p[0]) + dx); t.setAttribute("y", Y(p[1]) + dy); };
  const sp = document.getElementById("spark"), spEl = (tag, a) => el(tag, a, sp), sx = s => 34 + 258 * s / SMAX;
  const y1 = z => 10 + 52 * (700 - z) / 300, y2 = p => 88 + 46 * (16 - p) / 16;
  for (const [yy, t] of [[y1(400), "400"], [y1(700), "700"], [y2(0), "0°"], [y2(16), "16°"]]) { spEl("line", { x1: 34, y1: yy, x2: 292, y2: yy, class: "grid" }); txt(sp, 30, yy + 3, t, "tick", "end"); }
  spEl("polyline", { points: F.map(f => `${sx(f[0]).toFixed(1)},${y1(f[2]).toFixed(1)}`).join(" "), class: "sline s1" });
  spEl("polyline", { points: F.map(f => `${sx(f[0]).toFixed(1)},${y2(f[3]).toFixed(1)}`).join(" "), class: "sline s2" });
  txt(sp, 38, 24, "座面高度 mm"); txt(sp, 38, 102, "前倾"); txt(sp, 292, 148, `丝杠行程 0–${SMAX.toFixed(0)} mm`, "tick", "end");
  const cur = spEl("line", { y1: 6, y2: 136, class: "cur" }), d1 = spEl("circle", { r: 3.5, class: "sdot" }), d2 = spEl("circle", { r: 3.5, class: "sdot" });
  function draw(s) {
    const f = frameAt(s), Q = [f[1], f[2]], phi = f[3], P1 = [f[4], f[5]], P2 = [f[6], f[7]], pl = D.plate;
    const cr = [add(P1, pl.e[1], E, pl.nf[0], NF), add(P1, pl.e[1], E, pl.nf[1], NF), add(P1, pl.e[0], E, pl.nf[1], NF)];
    for (let k = 0; k <= 6; k++) { const a = (Math.PI / 2) * k / 6; cr.push([P1[0] - pl.rc * (Math.cos(a) * E[0] + Math.sin(a) * NF[0]), P1[1] - pl.rc * (Math.cos(a) * E[1] + Math.sin(a) * NF[1])]); }
    P.plate.setAttribute("points", pts(cr)); let n = 0;
    for (const on of [0, 150]) for (const se of [0, 150]) { const c = add(P1, se, E, on, NF); P.carr[n++].setAttribute("points", pts([add(c, -30.7, E, -17, NF), add(c, 30.7, E, -17, NF), add(c, 30.7, E, 17, NF), add(c, -30.7, E, 17, NF)])); }
    const nc = add(P1, 75, E, 75, NF); P.nut.setAttribute("points", pts([add(nc, -22, E, -14, NF), add(nc, 22, E, -14, NF), add(nc, 22, E, 14, NF), add(nc, -22, E, 14, NF)]));
    setL(P.link, B, P2); setL(P.armc2, P1, P2); setC(P.cart, P1); setC(P.rodA, P2);
    for (const k in P.seat) P.seat[k].setAttribute("points", pts(D.seat[k].map(p => Wt(Q, phi, p))));
    setT(P.cJ3, P1, -44, 4); setT(P.cC1, add(P1, 120, E, 175, NF), 6, 0); setT(P.cL1, [(B[0] + P2[0]) / 2, (B[1] + P2[1]) / 2], 6, 30); setT(P.cS7, Wt(Q, phi, [-85, -120]), -6, 4);
    P.kslider.setAttribute("points", pts([add(P1, -35, E, -18, NF), add(P1, 185, E, -18, NF), add(P1, 185, E, 6, NF), add(P1, -35, E, 6, NF)]));
    const ra = Wt(Q, phi, [-D.half, 0]), rb = Wt(Q, phi, [D.half, 0]);
    P.kseat.setAttribute("points", pts([ra, rb, P1, P2])); setL(P.kplate, ra, rb); setL(P.klink, B, P2); setC(P.j1, P1); setC(P.j2, P2);
    setT(P.t2, add(P1, 200, E), 16, 0); setT(P.t3, rb, 12, -12); setT(P.t4, [(B[0] + P2[0]) / 2, (B[1] + P2[1]) / 2], 8, 30); setT(P.tR, P1, -16, 5); setT(P.tS, P2, -16, 8);
    setL(P.load, [Q[0], Q[1] + 150], [Q[0], Q[1] + 14]); setC(P.q, Q);
    document.getElementById("r-s").textContent = `${s.toFixed(0)} mm`; document.getElementById("r-z").textContent = `${Q[1].toFixed(0)} mm`;
    document.getElementById("r-x").textContent = `${(Q[0] - F[0][1]).toFixed(0)} mm`; document.getElementById("r-p").textContent = `${phi.toFixed(1)}°`;
    const x = sx(s); cur.setAttribute("x1", x); cur.setAttribute("x2", x); d1.setAttribute("cx", x); d1.setAttribute("cy", y1(Q[1])); d2.setAttribute("cx", x); d2.setAttribute("cy", y2(phi));
  }
  const rangeEl = document.getElementById("s"), playBtn = document.getElementById("play"); let s = 0, dir = 1, playing = false, last = 0, hold = 0;
  const setMode = kin => { gK.style.display = kin ? "" : "none"; gP.style.display = kin ? "none" : ""; document.getElementById("m-kin").setAttribute("aria-pressed", kin);
    document.getElementById("m-part").setAttribute("aria-pressed", !kin); try { localStorage.setItem("mech-mode", kin ? "kin" : "part"); } catch (e) {} };
  document.getElementById("m-kin").onclick = () => setMode(true); document.getElementById("m-part").onclick = () => setMode(false);
  let saved = null; try { saved = localStorage.getItem("mech-mode"); } catch (e) {} setMode(saved !== "part");
  rangeEl.oninput = () => { s = +rangeEl.value; draw(s); if (playing) toggle(); };
  function tick(t) { if (!playing) return; const dt = last ? (t - last) / 1000 : 0; last = t;
    if (hold > 0) hold -= dt; else { s += dir * 60 * dt; if (s >= SMAX) { s = SMAX; dir = -1; hold = 1; } if (s <= 0) { s = 0; dir = 1; hold = 1; } }
    rangeEl.value = s; draw(s); requestAnimationFrame(tick); }
  function toggle() { playing = !playing; playBtn.textContent = playing ? "暂停" : "播放"; last = 0; if (playing) requestAnimationFrame(tick); }
  playBtn.onclick = toggle; draw(0); if (!reduced) toggle();
})();

// ------------------------------------------------------------------ load-path stepper
(function initSteps() {
  const sec = document.getElementById("sec"), btns = [...document.querySelectorAll(".step")], pb = document.getElementById("path-play"); let timer = null;
  function show(i) { btns.forEach((b, k) => b.setAttribute("aria-pressed", k === i)); sec.classList.toggle("focus", i >= 0);
    const ps = i >= 0 ? btns[i].dataset.parts.split(" ") : []; sec.querySelectorAll("[data-part]").forEach(n => n.classList.toggle("hl", ps.includes(n.dataset.part))); }
  const stop = () => { if (timer) { clearInterval(timer); timer = null; pb.textContent = "逐步播放"; } };
  btns.forEach((b, i) => b.onclick = () => { stop(); show(b.getAttribute("aria-pressed") === "true" ? -1 : i); });
  pb.onclick = () => { if (timer) { stop(); return; } let i = 0; show(0); pb.textContent = "停止"; timer = setInterval(() => { i++; if (i >= btns.length) { stop(); show(-1); return; } show(i); }, 1800); };
  document.getElementById("path-all").onclick = () => { stop(); show(-1); };
})();

// ------------------------------------------------------------------ BOM filter
(function initBom() {
  const chips = [...document.querySelectorAll(".chip")];
  chips.forEach(c => c.onclick = () => { chips.forEach(x => x.classList.toggle("on", x === c)); bomRows.forEach(tr => tr.hidden = !(c.dataset.g === "*" || tr.dataset.g === c.dataset.g)); });
})();

// ------------------------------------------------------------------ Q&A with Claude (sample capability, viewer's own account)
(function initQA() {
  const log = document.getElementById("qa-log"), box = document.getElementById("qa-in"), ask = document.getElementById("qa-ask"), stopB = document.getElementById("qa-stop"), note = document.getElementById("qa-note");
  const sugg = [...document.querySelectorAll(".qs")]; let sample = null, ctl = null, busy = false; const turns = [];
  const RULES = "你是这个床边起身台项目的机械设计助教，回答 ME5412 小组里负责 SolidWorks 建模和有限元分析的同学。只根据下面的项目资料回答；资料里没有的就直说“资料里没有”，并说明需要什么数据或实验才能定。" +
    "区分已算出的数、假设值和需要厂家样本核对的值。先讲清楚“为什么”和受力/结构上的因果，再给具体做法（建模步骤、约束、载荷、网格、要看的结果）。提到零件时写出编号（如 J3、C1），数值带单位，坐标用资料里的坐标系。" +
    "用中文，简洁，必要时用短列表；不要用表格和标题。\n\n=== 项目资料 ===\n" + D.ctx;
  const setBusy = b => { busy = b; ask.disabled = b || !sample; stopB.hidden = !b; sugg.forEach(x => x.disabled = b || !sample); };
  const esc = t => t.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  function fmt(t) {
    let h = esc(t).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
    h = h.replace(/\b([SJLCDHB][1-8])\b/g, (m, c) => D.names[c] ? `<button type="button" class="pc" data-code="${c}">${c}</button>` : m);
    return h.split(/\n{2,}/).map(p => { const ls = p.split("\n"); if (ls.every(l => /^\s*([-•*]|\d+[.)、])\s+/.test(l))) return "<ul>" + ls.map(l => "<li>" + l.replace(/^\s*([-•*]|\d+[.)、])\s+/, "") + "</li>").join("") + "</ul>"; return "<p>" + ls.join("<br>") + "</p>"; }).join("");
  }
  log.addEventListener("click", e => { const b = e.target.closest(".pc"); if (!b) return; const c = b.dataset.code; markBom([c]); showTip(c, e.clientX, e.clientY); if (window.select3D) window.select3D([c], false); });
  const COPY = { not_granted: "你没有允许这个页面使用 Claude，问答在这次打开里不可用。", sampling_disabled: "这个账号或组织没有开通 Claude，问答不可用。", rate_limited: "问得太快或额度用完了，过一会儿再问。",
    session_expired: "登录过期了，重新登录 claude.ai 后再问。", refused: "Claude 没有回答这个问题，换个问法试试。", empty_completion: "没有得到回答，把问题说得更具体一点再问。", prompt_too_large: "对话太长了，刷新页面重新开始。" };
  function bubble(role, text) { const d = document.createElement("div"); d.className = "msg " + role; if (role === "you") d.textContent = text; else d.innerHTML = text; log.appendChild(d); log.scrollTop = log.scrollHeight; return d; }
  async function send(q) {
    q = q.trim(); if (!q || busy || !sample) return; box.value = ""; bubble("you", q);
    const out = bubble("ai", '<p class="cap">思考中…（第一次会先问你是否允许这个页面使用 Claude）</p>'); turns.push({ role: "user", content: q });
    const msgs = [{ role: "user", content: RULES }, ...turns.slice(-8)]; ctl = new AbortController(); setBusy(true);
    try {
      const { text, truncated } = await sample(msgs, { cache: false, signal: ctl.signal, onText: ({ text }) => { out.innerHTML = fmt(text); log.scrollTop = log.scrollHeight; } });
      out.innerHTML = fmt(text) + (truncated ? '<p class="cap">（回答太长被截断了，可以接着问“继续”。）</p>' : ""); turns.push({ role: "assistant", content: text });
    } catch (e) {
      out.innerHTML = e.text ? fmt(e.text) : ""; turns.pop();
      if (e.code === "cancelled") out.insertAdjacentHTML("beforeend", '<p class="cap">已停止。</p>');
      else { out.insertAdjacentHTML("beforeend", `<p class="cap">${esc(COPY[e.code] || "连接出了问题，稍后再问一次。")}</p>`);
        if (["not_granted", "sampling_disabled", "not_declared", "capability_disabled", "capability_removed"].includes(e.code)) { sample = null; note.textContent = COPY[e.code] || "问答不可用。"; } }
    } finally { setBusy(false); }
  }
  ask.onclick = () => send(box.value); stopB.onclick = () => ctl && ctl.abort();
  box.addEventListener("keydown", e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(box.value); } });
  sugg.forEach(b => b.onclick = () => send(b.textContent));
  setBusy(false); note.textContent = "正在连接 Claude…";
  if (!window.claude || !window.claude.use) { note.textContent = "问答要在 claude.ai 里打开这个页面（登录 Claude 账号）才能用。"; return; }
  window.claude.use("sample").then(s => { sample = s; setBusy(false);
    note.textContent = s ? "回答用的是提问人自己的 Claude 账号额度；第一次提问会先请你允许。Ctrl / ⌘ + Enter 发送。" : "问答要在 claude.ai 里打开这个页面（登录 Claude 账号）才能用。"; });
})();
