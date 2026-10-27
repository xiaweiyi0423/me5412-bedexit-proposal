// cad/mechanism.html script: 3D assembly (three.js), 2D mechanism animation, balloons, load-path stepper, BOM filter, Q&A.
// D is injected by build_mech_page.py (mm, degrees; world x out from the bed, y toward the bed head, z up).
const F = D.frames, SMAX = F[F.length - 1][0], E = D.e, NF = D.nf;
const frameAt = s => { let i = 0; while (i < F.length - 2 && F[i + 1][0] < s) i++;
  const a = F[i], b = F[i + 1], t = Math.max(0, Math.min(1, (s - a[0]) / ((b[0] - a[0]) || 1))); return a.map((v, k) => v + t * (b[k] - v)); };
const add = (p, a, u, b, v) => [p[0] + a * u[0] + (b || 0) * (v ? v[0] : 0), p[1] + a * u[1] + (b || 0) * (v ? v[1] : 0)];
const Wt = (Q, phi, p) => { const a = phi * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [Q[0] + c * p[0] + s * p[1], Q[1] - s * p[0] + c * p[1]]; };
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const PINFO = {}; Object.entries(D.names).forEach(([c, n]) => { PINFO[c] = { name: n[0], material: n[1] }; });   // code -> {name, material}; manifest/mesh add more
const bomRows = [...document.querySelectorAll("#bom tbody tr")];
function markBom(codes) { bomRows.forEach(tr => tr.classList.toggle("on", codes.includes(tr.children[1].textContent.trim()))); }

// ------------------------------------------------------------------ tooltip for balloons and part codes
const tip = document.createElement("div"); tip.className = "tip"; tip.hidden = true; document.body.appendChild(tip);
function showTip(code, x, y) {
  const n = PINFO[code]; if (!n) return;
  tip.innerHTML = `<span class="code">${code}</span> <b></b><br><span class="m"></span>`; tip.querySelector("b").textContent = n.name; tip.querySelector(".m").textContent = n.material;
  tip.hidden = false; const r = tip.getBoundingClientRect();
  tip.style.left = Math.min(Math.max(8, x + 12), window.innerWidth - r.width - 8) + "px"; tip.style.top = Math.min(y + 12, window.innerHeight - r.height - 8) + "px";
}
document.addEventListener("click", ev => {
  const b = ev.target.closest(".bal"); document.querySelectorAll(".bal.on").forEach(x => x.classList.remove("on"));
  if (b) { b.classList.add("on"); showTip(b.dataset.code, ev.clientX, ev.clientY); markBom([b.dataset.code]); if (window.select3D) window.select3D([b.dataset.code], false); }
  else if (!ev.target.closest(".tip")) tip.hidden = true;
});
window.addEventListener("scroll", () => { tip.hidden = true; }, { passive: true });

// ------------------------------------------------------------------ 3D assembly: real CAD meshes (parts/mesh.json) when published with the page,
// otherwise a simplified primitive model drawn from the same numbers. Group frames as in cad/model/cadlib.py.
(function init3D() {
  const box = document.getElementById("v3"), info = document.getElementById("info"), legend = document.getElementById("legend"), hint = box.querySelector(".hint");
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
  let parts = {}, pickable = [], shellParts = [], model = null, poseFn = () => {}, sel = [];
  const put = (geo, m, code, parent, name) => { const me = new THREE.Mesh(geo, m); me.userData = { code, name }; (parent || model).add(me);
    if (code) { (parts[code] = parts[code] || []).push(me); pickable.push(me); } return me; };
  const rectEN = (c, ae, an) => [add(c, -ae, E, -an, NF), add(c, ae, E, -an, NF), add(c, ae, E, an, NF), add(c, -ae, E, an, NF)];

  function buildPrimitives() {
    model = new THREE.Group(); scene.add(model);
    put(boxG(-900, 0, -700, 800, 0, 420), mat("--bed", 0.55), null, null, "床"); put(boxG(-900, 1100, -800, 900, -4, 0), mat("--paper"), null, null, "地面");
    for (const g of [boxG(30, 780, -270, -210, 5, 35), boxG(30, 780, 320, 380, 5, 35), boxG(30, 90, -210, 320, 5, 35), boxG(720, 780, -210, 320, 5, 35), boxG(30, 780, 230, 260, 5, 35)]) put(g, mat("--steel"), "B1");
    put(boxG(200, 620, -220, 220, 35, 47), mat("--steel2"), "B2");
    put(boxG(670, 730, 270, 330, 35, 950), mat("--steel"), "B4"); put(cylY(700, 950, -50, 330, 19), mat("--ink2"), "B5");
    put(exXZ(D.housing, 336, 351), mat("--steel2"), "H1");
    shellParts = [put(exXZ(D.housing, 250, 253, [D.slot]), mat("--blue2", 0.28), "H2"), put(exXZ(D.housing, 356, 358), mat("--blue2", 0.12), "H4")];
    for (const r of [D.rail1, D.rail2]) put(exXZ([add(r[0], -7.5, NF), add(r[1], -7.5, NF), add(r[1], 7.5, NF), add(r[0], 7.5, NF)], 321, 336), mat("--ink"), "D1");
    const sv = [D.screw[1][0] - D.screw[0][0], 0, D.screw[1][1] - D.screw[0][1]], sl = Math.hypot(sv[0], sv[2]);
    const scr = put(new THREE.CylinderGeometry(8, 8, sl, 20), mat("--red"), "D2"); scr.position.set((D.screw[0][0] + D.screw[1][0]) / 2, 322, (D.screw[0][1] + D.screw[1][1]) / 2);
    scr.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(sv[0] / sl, 0, sv[2] / sl));
    put(exXZ(D.motor, 282, 350), mat("--ink2"), "D4");
    put(boxG(D.B[0] - 30, D.B[0] + 30, 260, 292, D.B[1] - 36, D.B[1] + 8), mat("--steel"), "L3");
    const G2 = new THREE.Group(); model.add(G2); const o = [0, 0], pl = D.plate, plOut = [add(o, pl.e[1], E, pl.nf[0], NF), add(o, pl.e[1], E, pl.nf[1], NF), add(o, pl.e[0], E, pl.nf[1], NF)];
    for (let k = 0; k <= 8; k++) { const a = (Math.PI / 2) * k / 8; plOut.push([-pl.rc * (Math.cos(a) * E[0] + Math.sin(a) * NF[0]), -pl.rc * (Math.cos(a) * E[1] + Math.sin(a) * NF[1])]); }
    put(exXZ(plOut, 288, 308), mat("--blue2"), "C1", G2);
    for (const on of [0, 150]) for (const se of [0, 150]) put(exXZ(rectEN(add(o, se, E, on, NF), 30.7, 17), 308, 330), mat("--blue"), "C2", G2);
    put(exXZ(rectEN(add(o, 75, E, 75, NF), 22, 14), 308, 336), mat("--ink2"), "C3", G2);
    put(cylY(0, 0, 229, 308, 37.5), mat("--red", 0.45), "J3", G2);
    put(cylY(0, 0, 229, 246, 27.5), mat("--ink"), "J2", G2); put(cylY(0, 0, 274, 291, 27.5), mat("--ink"), "J2", G2);
    const G3 = new THREE.Group(); model.add(G3); const S = D.seat;
    put(exXZ(S.foamr, -220, 220), mat("--foam"), "S1", G3); put(exXZ(S.foamf, -220, 220), mat("--foam2"), "S2", G3);
    put(exXZ(S.board, -220, 220), mat("--wood"), "S4", G3); put(exXZ(S.spacer, -220, 220), mat("--wood"), "S4", G3);
    put(exXZ(S.arm, 180, 200), mat("--steel"), "S6", G3); put(exXZ(S.arm, -200, -180), mat("--steel"), "S6", G3);
    put(exXZ(S.beam, -205, 212), mat("--steel"), "S7", G3);
    put(exXZ([[-30, -130], [45, -130], [45, -32], [-30, -32]], 204, 216), mat("--steel"), "S8", G3);
    const c1 = D.c1s, c2 = D.c2s; put(cylY(c1[0], c1[1], 216, 302, 15), mat("--ink2"), "J1", G3); put(cylY(c1[0], c1[1], 216, 226, 37.5), mat("--ink2"), "J1", G3);
    const ax = [c2[0] - c1[0], c2[1] - c1[1]], al = Math.hypot(ax[0], ax[1]), nx = [-ax[1] / al * 15, ax[0] / al * 15];
    put(exXZ([[c1[0] + nx[0], c1[1] + nx[1]], [c2[0] + nx[0], c2[1] + nx[1]], [c2[0] - nx[0], c2[1] - nx[1]], [c1[0] - nx[0], c1[1] - nx[1]]], 258, 270), mat("--steel"), "J4", G3);
    const link = put(new THREE.CylinderGeometry(10, 10, 1, 20), mat("--ink2"), "L1"), rodA = put(new THREE.SphereGeometry(14.5, 20, 14), mat("--ink"), "L2"), rodB = put(new THREE.SphereGeometry(14.5, 20, 14), mat("--ink"), "L2");
    rodB.position.set(D.B[0], 275, D.B[1]);
    const up = new THREE.Vector3(0, 1, 0);
    poseFn = s => {
      const f = frameAt(s), Q = [f[1], f[2]], phi = f[3], P1 = [f[4], f[5]], P2 = [f[6], f[7]];
      G2.position.set(P1[0], 0, P1[1]); G3.position.set(Q[0], 0, Q[1]); G3.rotation.set(0, phi * Math.PI / 180, 0);
      const a = new THREE.Vector3(P2[0], 275, P2[1]), b = new THREE.Vector3(D.B[0], 275, D.B[1]), d = b.clone().sub(a), L = d.length();
      link.position.copy(a.clone().add(b).multiplyScalar(0.5)); link.quaternion.setFromUnitVectors(up, d.normalize()); link.scale.set(1, L, 1); rodA.position.copy(a);
    };
  }
  const b64 = (s, T) => { const bin = atob(s), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return new T(u.buffer); };
  const SHELL = new Set(["H2", "H3", "H4", "H5"]);
  function buildMesh(M) {
    model = new THREE.Group(); scene.add(model); shellParts = [];
    const G = {}; for (const k of ["fixed", "ref", "seat", "carriage", "link"]) { G[k] = new THREE.Group(); model.add(G[k]); }
    const mcache = {};
    for (const p of M.parts) {
      if (!p.pos || !p.idx) continue;
      const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(b64(p.pos, Float32Array), 3));
      g.setIndex(new THREE.BufferAttribute(b64(p.idx, Uint32Array), 1)); g.computeVertexNormals();
      const isBed = p.group === "ref" || p.code === "BED", shell = SHELL.has(p.code), op = isBed ? 0.35 : shell ? 0.3 : 1;
      const key = (p.color || "#8c96a0") + op + (p.buy ? "b" : "");
      const m = mcache[key] || (mcache[key] = new THREE.MeshStandardMaterial({ color: new THREE.Color(p.color || "#8c96a0"), roughness: 0.6, metalness: p.buy ? 0.25 : 0.1, side: THREE.DoubleSide, transparent: op < 1, opacity: op, depthWrite: op >= 1 }));
      const me = put(g, m, isBed ? null : p.code, G[p.group] || G.fixed, p.name);
      if (shell) shellParts.push(me);
      if (!isBed) PINFO[p.code] = Object.assign({ name: p.name || p.code, material: "" }, PINFO[p.code] || {}, p.name ? { name: p.name } : {});
    }
    put(boxG(-900, 1100, -800, 900, -4, 0), mat("--paper"), null, model, "地面");
    const fr = M.frames || {}, rr = (fr.rail_rot_deg || 0) * Math.PI / 180, Bf = fr.B || D.B, ly = fr.link_y || 0;
    poseFn = s => {
      const f = frameAt(s), Q = [f[1], f[2]], phi = f[3], P1 = [f[4], f[5]], P2 = [f[6], f[7]];
      G.seat.position.set(Q[0], 0, Q[1]); G.seat.rotation.set(0, phi * Math.PI / 180, 0);
      G.carriage.position.set(P1[0], 0, P1[1]); G.carriage.rotation.set(0, rr, 0);
      G.link.position.set(Bf[0], ly, Bf[1]); G.link.rotation.set(0, -Math.atan2(P2[1] - Bf[1], P2[0] - Bf[0]), 0);
    };
  }
  function clearModel() {
    if (model) { scene.remove(model); model.traverse(o => { if (o.geometry) o.geometry.dispose(); }); }
    parts = {}; pickable = []; shellParts = []; sel = []; legend.innerHTML = "";
  }
  // selection
  const nameOf = c => (PINFO[c] && PINFO[c].name) || c, matOf = c => (PINFO[c] && PINFO[c].material) || "";
  function select(codes, fromPick) {
    for (const c of sel) for (const m of parts[c] || []) { m.material = m.userData.base; }
    sel = codes.filter(c => parts[c]);
    for (const c of sel) for (const m of parts[c]) { const h = m.userData.base.clone(); h.emissive = col("--hl"); h.emissiveIntensity = 0.55; m.material = h; }
    [...legend.children].forEach(x => x.classList.toggle("on", sel.includes(x.dataset.code)));
    if (sel.length === 1) { info.innerHTML = `<span class="code">${sel[0]}</span><br><b></b><br><span class="cap"></span>`; info.querySelector("b").textContent = nameOf(sel[0]); info.querySelector(".cap").textContent = matOf(sel[0]); }
    else if (sel.length > 1) { info.innerHTML = `<span class="code">${sel.join(" · ")}</span><br><b>已高亮 ${sel.length} 个零件</b><br><span class="cap"></span>`; info.querySelector(".cap").textContent = sel.map(nameOf).join("、"); }
    if (fromPick !== undefined) markBom(sel);
    render();
  }
  window.select3D = (codes, scroll) => {
    const want = []; for (const c of codes) { if (parts[c]) want.push(c); Object.keys(parts).forEach(k => { if (k !== c && k.startsWith(c) && /^[a-z]/.test(k.slice(c.length))) want.push(k); }); }
    select(want); if (scroll) document.getElementById("s1").scrollIntoView({ behavior: reduced ? "auto" : "smooth" });
  };
  const order = Object.keys(D.names), rank = c => { const i = order.indexOf(c.replace(/[a-z]+$/, "")); return (i < 0 ? 999 : i) * 10 + (c.length - c.replace(/[a-z]+$/, "").length); };
  function afterBuild() {
    for (const m of pickable) m.userData.base = m.material;
    Object.keys(parts).sort((a, b) => rank(a) - rank(b) || a.localeCompare(b)).forEach(c => {
      const bt = document.createElement("button"); bt.type = "button"; bt.className = "lg"; bt.dataset.code = c; bt.textContent = c; bt.title = nameOf(c);
      bt.onclick = () => select(sel.length === 1 && sel[0] === c ? [] : [c], true); legend.appendChild(bt); });
    poseFn(s); render();
  }
  const ray = new THREE.Raycaster(), ptr = new THREE.Vector2(); let down = null;
  renderer.domElement.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener("pointerup", e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return; const r = renderer.domElement.getBoundingClientRect();
    ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1); ray.setFromCamera(ptr, camera);
    const hit = ray.intersectObjects(pickable.filter(m => m.visible && m.parent && m.parent.visible !== false), false)[0]; select(hit ? [hit.object.userData.code] : [], true);
  });
  let w = 0, h = 0;
  function render() { renderer.render(scene, camera); }
  function size() { const r = box.getBoundingClientRect(); if (!r.width) return; if (r.width !== w || r.height !== h) { w = r.width; h = r.height; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); } render(); }
  new ResizeObserver(size).observe(box); controls.addEventListener("change", render);
  const r3 = document.getElementById("r3d"), p3 = document.getElementById("p3"); let s = 200, dir = 1, playing = false, last = 0, hold = 0;
  r3.value = s; buildPrimitives(); afterBuild(); size();
  r3.oninput = () => { s = +r3.value; poseFn(s); render(); if (playing) toggle(); };
  function tick(t) { if (!playing) return; const dt = last ? (t - last) / 1000 : 0; last = t;
    if (hold > 0) hold -= dt; else { s += dir * 60 * dt; if (s >= SMAX) { s = SMAX; dir = -1; hold = 1; } if (s <= 0) { s = 0; dir = 1; hold = 1; } }
    r3.value = s; poseFn(s); render(); requestAnimationFrame(tick); }
  function toggle() { playing = !playing; p3.textContent = playing ? "暂停" : "播放"; last = 0; if (playing) requestAnimationFrame(tick); }
  p3.onclick = toggle;
  const shellBtn = document.getElementById("shell"); let shellVis = true;
  shellBtn.onclick = () => { shellVis = !shellVis; shellParts.forEach(m => m.visible = shellVis); shellBtn.textContent = shellVis ? "隐藏机构箱外壳" : "显示机构箱外壳"; render(); };
  document.getElementById("reset3").onclick = () => { camera.position.set(...HOME.pos); controls.target.set(...HOME.tgt); controls.update(); render(); };
  fetch("parts/mesh.json").then(r => r.ok ? r.json() : Promise.reject(new Error(String(r.status)))).then(M => {
    if (!M || !Array.isArray(M.parts) || !M.parts.length) throw new Error("empty");
    const keep = sel.slice(); clearModel(); buildMesh(M); afterBuild(); if (keep.length) select(keep);
    shellParts.forEach(m => m.visible = shellVis);
    if (hint) hint.textContent = "CAD 模型（和 STEP 文件同一套几何）· 拖动旋转 · 滚轮缩放 · 点零件看名字";
  }).catch(() => { if (hint) hint.textContent = "简化示意模型 · 拖动旋转 · 滚轮缩放 · 点零件看名字"; });
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

// ------------------------------------------------------------------ parts gallery: drawings, params, STEP downloads (parts/manifest.json)
// STEP is not on the downloads allowlist, so a STEP file is handed over inside a .zip built here (stored, no compression).
const CRC_T = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(u) { let c = 0xFFFFFFFF; for (let i = 0; i < u.length; i++) c = CRC_T[(c ^ u[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
function makeZip(files) {
  const enc = new TextEncoder(), chunks = [], central = []; let off = 0;
  for (const f of files) {
    const nm = enc.encode(f.name), d = f.data, c = crc32(d), lh = new DataView(new ArrayBuffer(30));
    lh.setUint32(0, 0x04034b50, true); lh.setUint16(4, 20, true); lh.setUint16(6, 0x0800, true); lh.setUint16(8, 0, true); lh.setUint16(10, 0, true); lh.setUint16(12, 0x21, true);
    lh.setUint32(14, c, true); lh.setUint32(18, d.length, true); lh.setUint32(22, d.length, true); lh.setUint16(26, nm.length, true); lh.setUint16(28, 0, true);
    chunks.push(new Uint8Array(lh.buffer), nm, d);
    const cd = new DataView(new ArrayBuffer(46));
    cd.setUint32(0, 0x02014b50, true); cd.setUint16(4, 20, true); cd.setUint16(6, 20, true); cd.setUint16(8, 0x0800, true); cd.setUint16(10, 0, true); cd.setUint16(12, 0, true); cd.setUint16(14, 0x21, true);
    cd.setUint32(16, c, true); cd.setUint32(20, d.length, true); cd.setUint32(24, d.length, true); cd.setUint16(28, nm.length, true); cd.setUint32(42, off, true);
    central.push(new Uint8Array(cd.buffer), nm); off += 30 + nm.length + d.length;
  }
  const cdSize = central.reduce((a, u) => a + u.length, 0), end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, files.length, true); end.setUint16(10, files.length, true); end.setUint32(12, cdSize, true); end.setUint32(16, off, true);
  return new Blob([...chunks, ...central, new Uint8Array(end.buffer)], { type: "application/zip" });
}
(function initGallery() {
  const list = document.getElementById("glist"), pane = document.getElementById("gpane"), gnote = document.getElementById("gnote");
  const lb = document.getElementById("lb"), lbImg = document.getElementById("lb-img"), lbStage = document.getElementById("lb-stage"), lbTitle = document.getElementById("lb-title");
  let dl = null, M = null, cur = null;
  const esc = t => String(t == null ? "" : t).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const GROUPS = [["S", "座板"], ["J", "铰点 1"], ["L", "连杆"], ["C", "滑块座"], ["D", "驱动"], ["H", "机构箱"], ["B", "底座和扶手"]];
  const groupOf = c => (GROUPS.find(g => c.startsWith(g[0])) || ["", "其他"])[1];
  const DLMSG = { declined: "", rate_limited: "已经有一个保存窗口开着，先处理它再点。", too_large: "文件太大，这个环境存不下。", rejected_extension: "这里不允许这种文件类型。",
    extension_not_enabled: "这里不允许这种文件类型。", unavailable: "这个页面在这里不能下载文件。" };
  function say(t) { const s = pane.querySelector(".gmsg"); if (s) s.textContent = t; }
  async function save(filename, makeData) {
    if (!dl) return; say("准备文件…");
    try { const data = await makeData(); await dl.save({ filename, data }); say(""); }
    catch (e) { say(e && e.code ? (DLMSG[e.code] ?? "保存失败，稍后再试。") : "文件没取到（可能没有随页面发布）。"); }
  }
  const getBytes = async path => { const r = await fetch("parts/" + path); if (!r.ok) throw new Error(String(r.status)); return new Uint8Array(await r.arrayBuffer()); };
  const base = p => p.split("/").pop();
  const zipOf = async paths => makeZip(await Promise.all(paths.map(async p => ({ name: base(p), data: await getBytes(p) }))));
  function openLb(src, title) {
    lbImg.src = src; lbTitle.textContent = title; lb.hidden = false; z = 1; tx = 0; ty = 0; apply(); document.getElementById("lb-close").focus();
  }
  let z = 1, tx = 0, ty = 0, drag = null;
  const apply = () => { lbImg.style.transform = `translate(${tx}px, ${ty}px) scale(${z})`; };
  const zoom = (k, cx, cy) => { const r = lbStage.getBoundingClientRect(), px = (cx ?? r.left + r.width / 2) - r.left - r.width / 2, py = (cy ?? r.top + r.height / 2) - r.top - r.height / 2;
    const nz = Math.min(8, Math.max(0.5, z * k)); tx = px - (px - tx) * nz / z; ty = py - (py - ty) * nz / z; z = nz; apply(); };
  lbStage.addEventListener("wheel", e => { e.preventDefault(); zoom(e.deltaY < 0 ? 1.2 : 1 / 1.2, e.clientX, e.clientY); }, { passive: false });
  lbStage.addEventListener("pointerdown", e => { drag = [e.clientX - tx, e.clientY - ty]; lbStage.setPointerCapture(e.pointerId); });
  lbStage.addEventListener("pointermove", e => { if (!drag) return; tx = e.clientX - drag[0]; ty = e.clientY - drag[1]; apply(); });
  lbStage.addEventListener("pointerup", () => { drag = null; });
  document.getElementById("lb-in").onclick = () => zoom(1.4); document.getElementById("lb-out").onclick = () => zoom(1 / 1.4);
  document.getElementById("lb-fit").onclick = () => { z = 1; tx = 0; ty = 0; apply(); };
  const closeLb = () => { lb.hidden = true; lbImg.removeAttribute("src"); };
  document.getElementById("lb-close").onclick = closeLb; lb.addEventListener("keydown", e => { if (e.key === "Escape") closeLb(); });
  lb.addEventListener("click", e => { if (e.target === lb) closeLb(); });

  function showAssembly() {
    cur = "ASM"; markList(); const A = M.assembly || {}, dr = (A.drawing || {}).flush, st = A.step || {};
    pane.innerHTML = `<div class="ghead"><span class="gcode">总装</span><h3>总装图（齐平位）</h3></div>
      <p class="cap">全部零件按 v5.7 模型装在一起，座板在齐平位（丝杠行程 0）。顶位的总装 STEP 也可以下载，用来做干涉检查。</p>
      ${dr ? `<button type="button" class="gimgbtn" aria-label="放大看总装图"><img src="parts/${esc(dr)}" alt="总装图三视图" loading="lazy"></button>` : '<p class="cap">总装图没有生成。</p>'}
      <div class="ctl gbtns">${st.flush ? '<button type="button" class="btn dl" data-k="af">下载总装 STEP · 齐平位</button>' : ""}${st.top ? '<button type="button" class="btn dl" data-k="at">下载总装 STEP · 顶位</button>' : ""}
      <button type="button" class="btn ghost dl" data-k="all">全部零件 STEP（一个 zip）</button>${dr ? '<button type="button" class="btn ghost dl" data-k="asvg">下载总装图 SVG</button>' : ""}</div><p class="cap gmsg" aria-live="polite"></p>`;
    wire({ af: () => save("总装_齐平位_STEP.zip", () => zipOf([st.flush])), at: () => save("总装_顶位_STEP.zip", () => zipOf([st.top])),
      all: () => save("全部零件_STEP.zip", () => zipOf(M.parts.filter(p => p.step).map(p => p.step))), asvg: () => save(base(dr), () => getBytes(dr)) }, dr, "总装图");
  }
  function showPart(code) {
    const p = M.parts.find(x => x.code === code); if (!p) return; cur = code; markList();
    const rows = (p.params || []).map(r => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td></tr>`).join("");
    pane.innerHTML = `<div class="ghead"><span class="gcode">${esc(p.code)}</span><h3>${esc(p.name)}</h3>${p.buy ? '<span class="pill buy">外购件</span>' : ""}</div>
      <p class="gmeta"><span>${esc(p.material)}</span><span>数量 ${esc(p.qty)}</span><span>${esc(groupOf(p.code))}</span></p>
      ${p.note ? `<p class="cap">${esc(p.note)}</p>` : ""}
      ${p.drawing ? `<button type="button" class="gimgbtn" aria-label="放大看 ${esc(p.code)} 的图纸"><img src="parts/${esc(p.drawing)}" alt="${esc(p.code)} ${esc(p.name)} 的三视图" loading="lazy"></button>`
        : `<p class="gnodraw">${p.buy ? "外购件：没有出图，按厂家样本选型；STEP 是按样本主要尺寸做的外形，用来装配和查干涉。" : "这个零件没有单独出图。"}</p>`}
      ${rows ? `<div class="tw"><table class="num gparams"><thead><tr><th>关键尺寸</th><th>值</th></tr></thead><tbody>${rows}</tbody></table></div>` : ""}
      <div class="ctl gbtns">${p.step ? '<button type="button" class="btn dl" data-k="step">下载 STEP（zip）</button>' : ""}${p.drawing ? '<button type="button" class="btn ghost dl" data-k="svg">下载图纸 SVG</button>' : ""}
      <button type="button" class="btn ghost" data-k="v3">在 3D 里看</button></div><p class="cap gmsg" aria-live="polite"></p>`;
    wire({ step: () => save(`${p.code}_STEP.zip`, () => zipOf([p.step])), svg: () => save(base(p.drawing), () => getBytes(p.drawing)),
      v3: () => { markBom([p.code]); if (window.select3D) window.select3D([p.code], true); } }, p.drawing, `${p.code} ${p.name}`);
  }
  function wire(acts, dr, title) {
    pane.querySelectorAll("[data-k]").forEach(b => { const f = acts[b.dataset.k]; if (f) b.onclick = f; if (b.classList.contains("dl")) b.hidden = !dl; });
    const ib = pane.querySelector(".gimgbtn"); if (ib) ib.onclick = () => openLb("parts/" + dr, title);
    if (!dl) say("下载要在 claude.ai 里打开这个页面才能用；图纸可以直接点开放大。");
  }
  function markList() { list.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.code === cur)); }
  function renderList() {
    const by = {}; M.parts.forEach(p => { (by[groupOf(p.code)] = by[groupOf(p.code)] || []).push(p); });
    let h = `<button type="button" class="gitem gasm" data-code="ASM"><span class="gc">总装</span><span>总装图和总装 STEP</span></button>`;
    for (const [, g] of [...GROUPS, ["", "其他"]]) { const ps = by[g]; if (!ps) continue;
      h += `<p class="gg">${esc(g)}</p>` + ps.map(p => `<button type="button" class="gitem" data-code="${esc(p.code)}"><span class="gc">${esc(p.code)}</span><span>${esc(p.name)}</span>${p.buy ? '<span class="pill buy">外购</span>' : ""}</button>`).join(""); }
    list.innerHTML = h; list.querySelectorAll("button").forEach(b => b.onclick = () => b.dataset.code === "ASM" ? showAssembly() : showPart(b.dataset.code));
  }
  if (window.claude && window.claude.use) window.claude.use("downloads").then(x => { dl = x; if (M) (cur === "ASM" ? showAssembly() : cur && showPart(cur)); }).catch(() => {});
  fetch("parts/manifest.json").then(r => r.ok ? r.json() : Promise.reject(new Error(String(r.status)))).then(m => {
    if (!m || !Array.isArray(m.parts)) throw new Error("bad");
    M = m; m.parts.forEach(p => { PINFO[p.code] = { name: p.name, material: p.material }; });
    gnote.textContent = `${m.parts.length} 个零件，${m.parts.filter(p => p.drawing).length} 张零件图（${m.version || ""}）。点左边的零件看图纸；图纸可以点开放大、拖动。`;
    renderList(); showAssembly();
  }).catch(() => { gnote.textContent = "零件文件没有随页面一起发布（或在本地直接打开），这里暂时看不到图纸和 STEP。仓库里 cad/out/ 下有同样的文件。"; list.innerHTML = ""; pane.innerHTML = ""; });
})();

// ------------------------------------------------------------------ Q&A window. Two routes:
//   "owner": comments.sendToClaude - posts the question as a page comment and the owner's watching Claude session answers in that
//            thread (owner's quota; editors of the artifact only; answer arrives in the comment panel, minutes later).
//   "self" : sample - answered here, live, on the asker's own Claude account.
// Default: owner route for a non-owner when it is available; otherwise self.
(function initQA() {
  const log = document.getElementById("qa-log"), box = document.getElementById("qa-in"), ask = document.getElementById("qa-ask"), stopB = document.getElementById("qa-stop"), note = document.getElementById("qa-note");
  const routeT = document.getElementById("qa-route-t"), routeB = document.getElementById("qa-switch");
  const sugg = [...document.querySelectorAll(".qs")]; let sample = null, comments = null, ownerOK = false, isOwner = false, route = "self", ctl = null, busy = false, ready = null; const turns = [];
  const RULES = "你是这个床边起身台项目的机械设计助教，回答 ME5412 小组里负责 SolidWorks 建模和有限元分析的同学。只根据下面的项目资料回答；资料里没有的就直说“资料里没有”，并说明需要什么数据或实验才能定。" +
    "区分已算出的数、假设值和需要厂家样本核对的值。先讲清楚“为什么”和受力/结构上的因果，再给具体做法（建模步骤、约束、载荷、网格、要看的结果）。提到零件时写出编号（如 J3、C1），数值带单位，坐标用资料里的坐标系。" +
    "用中文，简洁，必要时用短列表；不要用表格和标题。\n\n=== 项目资料 ===\n" + D.ctx;
  const canAsk = () => route === "owner" ? ownerOK : !!sample;
  const setBusy = b => { busy = b; ask.disabled = b || !canAsk(); stopB.hidden = !(b && route === "self"); sugg.forEach(x => x.disabled = b || !canAsk()); };
  const esc = t => t.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  function fmt(t) {
    let h = esc(t).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
    h = h.replace(/\b([SJLCDHB][1-8][a-z]?)\b/g, (m, c) => PINFO[c] ? `<button type="button" class="pc" data-code="${c}">${c}</button>` : m);
    return h.split(/\n{2,}/).map(p => { const ls = p.split("\n"); if (ls.every(l => /^\s*([-•*]|\d+[.)、])\s+/.test(l))) return "<ul>" + ls.map(l => "<li>" + l.replace(/^\s*([-•*]|\d+[.)、])\s+/, "") + "</li>").join("") + "</ul>"; return "<p>" + ls.join("<br>") + "</p>"; }).join("");
  }
  log.addEventListener("click", e => { const b = e.target.closest(".pc"); if (!b) return; const c = b.dataset.code; markBom([c]); showTip(c, e.clientX, e.clientY); if (window.select3D) window.select3D([c], false); });
  const COPY = { not_granted: "你没有允许这个页面使用 Claude，问答在这次打开里不可用。", sampling_disabled: "这个账号或组织没有开通 Claude，问答不可用。", rate_limited: "问得太快或额度用完了，过一会儿再问。",
    session_expired: "登录过期了，重新登录 claude.ai 后再问。", refused: "Claude 没有回答这个问题，换个问法试试。", empty_completion: "没有得到回答，把问题说得更具体一点再问。", prompt_too_large: "对话太长了，刷新页面重新开始。" };
  const OCOPY = { consent_required: "没有允许页面替你发评论，这次没发出。再点一次“提问”并在弹窗里允许，或者改用你自己的账号。",
    forbidden: "这里不能替你发评论，发给组长的 Claude 这条路关掉了。", claude_unavailable: "现在发不到组长的 Claude（可能没有在线的会话），这次没发出，什么也没贴出去。",
    rate_limited: "发得太快了，等一会儿再发。", invalid: "问题太长或含有不支持的字符，改短一点再发。", not_found: "那条评论找不到了，重新提问即可。" };
  const body = log.parentElement;
  function bubble(role, text) { const d = document.createElement("div"); d.className = "msg " + role; if (role === "you") d.textContent = text; else d.innerHTML = text; log.appendChild(d); body.scrollTop = body.scrollHeight; return d; }
  function showRoute() {
    if (route === "owner") { routeT.textContent = "回答用：组长的 Claude（发到页面评论，几分钟内在评论里回复）"; note.textContent = "Ctrl / ⌘ + Enter 发送。第一次会先请你允许页面替你发评论。"; }
    else if (sample) { routeT.textContent = "回答用：你自己的 Claude 账号（在这里即时回答）"; note.textContent = "第一次提问会先请你允许。Ctrl / ⌘ + Enter 发送。"; }
    else { routeT.textContent = "问答现在不可用"; note.textContent = "问答要在 claude.ai 里打开这个页面（登录 Claude 账号）才能用。"; }
    const both = ownerOK && !!sample; routeB.hidden = !both; routeB.textContent = route === "owner" ? "改用我自己的账号" : "改用组长的 Claude";
    setBusy(busy);
  }
  routeB.onclick = () => { route = route === "owner" ? "self" : "owner"; showRoute(); };
  async function checkOwner() {
    if (!comments || typeof comments.sendToClaude !== "function") { ownerOK = false; return; }
    try { ownerOK = (await comments.canSendToClaude()) === "available"; } catch (e) { ownerOK = false; }
  }
  function init() {
    if (ready) return ready;
    if (!window.claude || !window.claude.use) { ready = Promise.resolve(); showRoute(); return ready; }
    ready = Promise.all([window.claude.use("sample").catch(() => null), window.claude.use("comments").catch(() => null), window.claude.use("user").catch(() => null)]).then(async ([s, c, u]) => {
      sample = s; comments = c;
      try { isOwner = u ? !!(await u.isOwner()) : false; } catch (e) { isOwner = false; }
      await checkOwner(); route = ownerOK && !isOwner ? "owner" : (sample ? "self" : (ownerOK ? "owner" : "self")); showRoute();
    });
    return ready;
  }
  async function sendOwner(q) {
    const out = bubble("ai", '<p class="cap">正在发给组长的 Claude…（第一次会先请你允许页面替你发评论）</p>'); setBusy(true);
    try {
      const anchor = await comments.anchorFor(document.querySelector("h1"));
      await comments.sendToClaude({ anchor, text: ("【问答窗】" + q).slice(0, 3600) + "\n（请按“起身台机构与选型”页面的资料回答）" });
      out.innerHTML = "<p>已发出：回复会出现在页面的评论里（右上角评论按钮），通常几分钟内，由组长的 Claude 回答。</p>";
    } catch (e) {
      const code = e && e.code; out.innerHTML = `<p class="cap">${esc(OCOPY[code] || "发送失败，稍后再试。")}</p>`;
      if (["forbidden", "claude_unavailable", "not_granted", "capability_disabled", "capability_removed", "unavailable"].includes(code)) {
        ownerOK = false; if (sample) { route = "self"; out.insertAdjacentHTML("beforeend", '<p class="cap">已改用你自己的 Claude 账号，可以直接再问一次。</p>'); } showRoute(); }
    } finally { setBusy(false); }
  }
  async function sendSelf(q) {
    const out = bubble("ai", '<p class="cap">思考中…（第一次会先问你是否允许这个页面使用 Claude）</p>'); turns.push({ role: "user", content: q });
    const msgs = [{ role: "user", content: RULES }, ...turns.slice(-8)]; ctl = new AbortController(); setBusy(true);
    try {
      const { text, truncated } = await sample(msgs, { cache: false, signal: ctl.signal, onText: ({ text }) => { out.innerHTML = fmt(text); body.scrollTop = body.scrollHeight; } });
      out.innerHTML = fmt(text) + (truncated ? '<p class="cap">（回答太长被截断了，可以接着问“继续”。）</p>' : ""); turns.push({ role: "assistant", content: text });
    } catch (e) {
      out.innerHTML = e.text ? fmt(e.text) : ""; turns.pop();
      if (e.code === "cancelled") out.insertAdjacentHTML("beforeend", '<p class="cap">已停止。</p>');
      else { out.insertAdjacentHTML("beforeend", `<p class="cap">${esc(COPY[e.code] || "连接出了问题，稍后再问一次。")}</p>`);
        if (["not_granted", "sampling_disabled", "not_declared", "capability_disabled", "capability_removed"].includes(e.code)) { sample = null; if (ownerOK) route = "owner"; showRoute(); } }
    } finally { setBusy(false); }
  }
  async function send(q) {
    q = q.trim(); if (!q || busy) return; await init(); if (!canAsk()) return;
    box.value = ""; suggRow.hidden = true; bubble("you", q);
    if (route === "owner") await sendOwner(q); else await sendSelf(q);
  }
  ask.onclick = () => send(box.value); stopB.onclick = () => ctl && ctl.abort();
  box.addEventListener("keydown", e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(box.value); } });
  sugg.forEach(b => b.onclick = () => send(b.textContent));
  const fab = document.getElementById("qa-fab"), win = document.getElementById("qa-win"), suggRow = document.getElementById("qa-sugg");
  const openWin = open => { win.hidden = !open; fab.hidden = open; fab.setAttribute("aria-expanded", open);
    if (open) { box.focus(); init().then(async () => { const was = ownerOK; await checkOwner(); if (was !== ownerOK) { if (!ownerOK && route === "owner" && sample) route = "self"; showRoute(); } }); } else fab.focus(); };
  fab.onclick = () => openWin(true); document.getElementById("qa-min").onclick = () => openWin(false);
  win.addEventListener("keydown", e => { if (e.key === "Escape") openWin(false); });
  routeT.textContent = "正在连接 Claude…"; setBusy(false); init();
})();
