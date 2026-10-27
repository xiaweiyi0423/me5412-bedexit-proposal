"""Fall-prevention step 2: can the sensors the design already has tell a fall from a normal exit when the user leaves the
footplate? Synthetic Monte Carlo feasibility / kill test - it can rule the idea out or keep it alive, it cannot prove it works.

Sensors (already in the design): seat load cells x4 (seat force; here only used to see "sitting back"), footplate load cells
x4 (foot force F_f and centre of pressure COP x, y), handrail bar force F_b. 100 Hz. Forces in body weights (BW).
Noise: 1.5 % BW per force channel, COP 1 cm (variant 2 cm); COP is undefined when F_f < 0.05 BW.
Geometry as the design: footplate x 0.20-0.62, y +-0.22; feet centred at y +-0.06 H, foot width 0.055 H, length 0.152 H.

Classes
  N normal exit (>= 400): stand 1-4 s after the seat releases, bar released early / abruptly / held while stepping; weight
    shift onto the stance foot, swing (platform still carries ~BW, COP at the stance-foot centre), first foot lands on the
    floor, weight transfer 0.15-1.0 s (platform force falls smoothly, COP stays inside the stance foot), second foot leaves.
    Shuffle variant (two partial transfers with a plateau), sideways or forward steps. Plus "sit back down" (seat force
    rises again: no exit at all).
  F fall starting on the platform (>= 400): (a) lateral topple about the outer edge of a foot: loss of balance (COP runs to
    the edge), then an inverted pendulum, point mass at l = 0.55 H, theta'' = (g/l) sin(theta), vertical GRF
    F/W = 1 - (l/g)(theta'' sin + theta'^2 cos) until the foot unloads; COP pinned at the edge; bar grab sometimes
    (0.2-0.6 BW for 0.1-0.4 s, slows the fall); 20 % land partly on the footplate (small impact). (b) forward topple about
    the toes, bar grab 70 %. (c) knees give way: fast partial unload, then knees/hip hit the footplate (1.5-3 BW, 30-80 ms),
    then lying partly on it. (d) one foot slips sideways (COP jumps), then (a)- or (c)-like.
  O fall after both feet have left the platform: nothing reaches these sensors - out of scope by construction.
  Backward falls onto the seat are caught by the seat and already handled by the controller (not simulated here).
Event: the summed force (seat + feet + bar, 5-sample mean) drops below 0.1 BW after being above 0.8; if there is no exit but a
footplate spike >= 1.3 BW, the spike is the event.
Features: unloading time 0.9 -> 0.1, shape (share of that time spent above 0.5), COP edge index at the 0.5 crossing (0 = foot
centre, 1 = outer edge / toe), max COP speed in the last 1 s, bar peak (-1 .. +0.3 s), stance dwell (longest still COP with
F_f > 0.5 in the last 1 s), footplate peak after the drop.
Detectors: a 3-line rule (thresholds tuned on the training half) and a logistic regression (numpy). Variants for
sensitivity. Output: seat_1dof/exit_detect.json, seat_1dof/exit_detect.png
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "seat_1dof")
DT, TT, G = 0.01, 9.0, 9.81
N_EACH = 500
ss = lambda s: np.clip(s, 0, 1) ** 2 * (3 - 2 * np.clip(s, 0, 1))          # smoothstep

def base_body(rng):
    H = rng.uniform(1.45, 1.85); return dict(H=H, fc=0.06 * H, fw=0.055 * H, fl=0.152 * H, ax=rng.uniform(0.28, 0.40))

def empty(n): return dict(Ff=np.zeros(n), cx=np.zeros(n), cy=np.zeros(n), Fs=np.zeros(n), Fb=np.zeros(n))

def standing(rng, b, t, sig, t_end):
    """seat releasing over the first 0.5 s, then standing with small sway; returns bar level used."""
    n = len(t); m = t < t_end; xc = b["ax"] + 0.25 * b["fl"]
    sway_y = np.cumsum(rng.normal(0, 0.0015, n)); sway_y -= np.linspace(0, sway_y[-1], n); sway_y = np.clip(sway_y, -0.015, 0.015)
    sway_x = np.cumsum(rng.normal(0, 0.0015, n)); sway_x -= np.linspace(0, sway_x[-1], n); sway_x = np.clip(sway_x, -0.02, 0.02)
    sig["Fs"] = np.where(t < 0.5, 0.3 * (1 - t / 0.5), 0.0)
    sig["cx"][:] = xc + sway_x; sig["cy"][:] = sway_y
    return xc

def normal(rng, v):
    b = base_body(rng); t = np.arange(0, TT, DT); s = empty(len(t)); xc = standing(rng, b, t, s, TT)
    t1 = 0.5 + rng.uniform(1, 4); bar0 = rng.uniform(0, 0.25); mode = rng.choice(["early", "abrupt", "hold"], p=[0.45, 0.2, 0.35])
    side = rng.random() < 0.6; sgn = 1.0 if (side or rng.random() < 0.5) else -1.0
    t2 = t1 + rng.uniform(0.3, 0.8); t3 = t2 + rng.uniform(0.3, 0.9)
    shuffle = rng.random() < 0.3; tf = v["step_T"]
    yst = sgn * b["fc"] + rng.uniform(-0.012, 0.012) + sgn * v["normal_edge"] * rng.uniform(0, 1) * b["fw"] / 2
    load = np.ones(len(t))
    s["cy"] = np.where(t < t1, s["cy"], s["cy"] + (yst - s["cy"]) * ss((t - t1) / (t2 - t1)))
    swing = (t >= t2) & (t < t3); load[swing] += 0.08 * np.sin(np.pi * (t[swing] - t2) / (t3 - t2)) * rng.choice([-1, 1])
    tc = t3
    if shuffle:
        lvl = rng.uniform(0.3, 0.7); d1 = rng.uniform(0.2, 0.5); pl = rng.uniform(0.4, 1.5)
        m = t >= tc; load[m] = 1 - (1 - lvl) * ss((t[m] - tc) / d1); tc = tc + d1 + pl; start = lvl
    else: start = 1.0
    Tt = rng.uniform(*tf); m = t >= tc; load[m] = start * (1 - ss((t[m] - tc) / Tt))
    if not side: s["cx"] = np.where(t >= tc, s["cx"] + rng.uniform(0.1, 0.4) * b["fl"] * ss((t - tc) / Tt), s["cx"])     # push-off: COP to the forefoot
    s["cy"] = np.where(t >= tc, s["cy"] + rng.uniform(-0.015, 0.015) * ss((t - tc) / Tt), s["cy"])
    if mode == "early": Fb = bar0 * (1 - ss((t - (t1 - 0.8)) / rng.uniform(0.3, 1.0)))
    elif mode == "abrupt": tr = rng.uniform(t1 - 0.5, t3); Fb = np.where(t < tr, bar0, 0.0)
    else: tr = tc + Tt + rng.uniform(0.1, 0.5); Fb = np.where(t < tr, bar0, 0.0) * (1 - ss((t - tr + 0.15) / 0.15))
    Fb = np.where(t < 0.5, bar0, Fb)
    s["Fb"] = Fb; s["Ff"] = np.clip(load * (1 - s["Fs"]) - Fb * (load > 0.02), 0, None)
    return s, b, "step_side" if side else "step_forward"

def sitback(rng, v):
    b = base_body(rng); t = np.arange(0, TT, DT); s = empty(len(t)); standing(rng, b, t, s, TT)
    t1 = 0.5 + rng.uniform(1, 4); d = rng.uniform(0.5, 1.5); lvl = rng.uniform(0.6, 0.9)
    s["Fs"] = np.maximum(s["Fs"], lvl * ss((t - t1) / d)); s["Fb"] = rng.uniform(0, 0.2) * np.ones(len(t))
    s["Ff"] = np.clip(1 - s["Fs"] - s["Fb"], 0, None); return s, b, "sit_back"

def pendulum(theta0, om0, l, slow, grab, rng):
    """returns arrays (time, F/W of the feet, bar force) until the foot unloads."""
    th, om, out, tt = theta0, om0, [], 0.0; w2 = G / l
    tg0 = rng.uniform(0.0, 0.4) if grab else 9; tg1 = tg0 + (rng.uniform(0.1, 0.4) if grab else 0); fg = rng.uniform(0.2, 0.6) if grab else 0
    while tt < 4.0:
        fb = fg if tg0 <= tt < tg1 else 0.0
        acc = w2 * np.sin(th) * (1 - slow * fb)
        F = 1 - (l / G) * (acc * np.sin(th) + om * om * np.cos(th)) - fb
        if F <= 0 or th > np.radians(80): break
        out.append((tt, F, fb)); om += acc * DT; th += om * DT; tt += DT
    return np.array(out)

def fall(rng, v):
    b = base_body(rng); t = np.arange(0, TT, DT); s = empty(len(t)); xc = standing(rng, b, t, s, TT)
    t1 = 0.5 + rng.uniform(1, 4); bar0 = rng.uniform(0, 0.2) if rng.random() < 0.5 else 0.0
    kind = rng.choice(["lateral", "forward", "knees", "slip", "rescue_step"], p=[0.35, 0.15, 0.2, 0.15, 0.15]); sgn = rng.choice([-1.0, 1.0])
    s["Fb"] = np.where(t < t1, bar0, 0.0); Ff = 1 - s["Fs"] - s["Fb"]
    l = 0.55 * b["H"]
    def topple(t_start, axis, edge_pos, grab_p):
        nonlocal Ff
        pre = rng.uniform(*v["pre"]); m = (t >= t_start) & (t < t_start + pre)
        key = "cy" if axis == "y" else "cx"; c0 = s[key][np.searchsorted(t, t_start)]
        s[key] = np.where(m, c0 + (edge_pos - c0) * ((t - t_start) / pre) ** 2, s[key])
        tp = t_start + pre; P = pendulum(np.radians(rng.uniform(*v["theta0"])), rng.uniform(0, 0.4), l, v["slow"], rng.random() < grab_p, rng)
        i0 = np.searchsorted(t, tp); k = min(len(P), len(t) - i0)
        Ff[i0:i0 + k] = P[:k, 1]; s["Fb"][i0:i0 + k] = np.maximum(s["Fb"][i0:i0 + k], P[:k, 2]); s[key][i0:] = edge_pos + rng.normal(0, 0.002)
        toff = tp + k * DT; Ff[i0 + k:] = 0.0
        return toff
    edge_f = lambda: rng.uniform(0.6, 1.0)                   # where the COP sits when tipping over a foot edge (1 = sole edge)
    if kind in ("lateral", "slip"):
        ts = t1
        if kind == "slip":                      # one foot slides: COP jumps toward the other foot, brief dip
            d = rng.uniform(0.1, 0.2); m = (t >= t1) & (t < t1 + d)
            s["cy"] = np.where(m, s["cy"] + sgn * b["fc"] * (t - t1) / d, s["cy"]); Ff = np.where(m, Ff - rng.uniform(0.1, 0.4) * np.sin(np.pi * (t - t1) / d), Ff)
            s["cy"] = np.where(t >= t1 + d, sgn * b["fc"], s["cy"]); ts = t1 + d
            if rng.random() < 0.4: kind = "slip_knees"
        if kind != "slip_knees":
            toff = topple(ts, "y", sgn * (b["fc"] + edge_f() * b["fw"] / 2), 0.35)
            if rng.random() < 0.2:
                tl = toff + rng.uniform(0.2, 0.4); m = (t >= tl) & (t < tl + rng.uniform(0.05, 0.15)); Ff = np.where(m, rng.uniform(0.3, 1.0), Ff)
                Ff = np.where(t >= tl + 0.15, rng.uniform(0, 0.3), Ff)
        else: t1 = ts
    if kind == "forward":
        topple(t1, "x", b["ax"] + 0.25 * b["fl"] + edge_f() * 0.5 * b["fl"], 0.7)
    if kind in ("knees", "slip_knees"):
        d = rng.uniform(0.08, 0.2); r = rng.uniform(0.1, 0.5); m = (t >= t1) & (t < t1 + d)
        Ff = np.where(m, 1 - (1 - r) * ss((t - t1) / d), Ff); Ff = np.where(t >= t1 + d, r, Ff)
        ti = t1 + d + rng.uniform(0.25, 0.45); dur = rng.uniform(0.03, 0.08); m = (t >= ti) & (t < ti + dur)
        Ff = np.where(m, rng.uniform(1.5, 3.0) * np.sin(np.pi * (t - ti) / dur) + r, Ff)
        Ff = np.where(t >= ti + dur, rng.uniform(0.3, 0.9) if rng.random() > 0.3 else 0.0, Ff)
        s["cy"] = np.where(t >= t1, s["cy"] + rng.normal(0, 0.02), s["cy"])
    if kind == "rescue_step":                  # COP runs toward an edge, the free foot steps off fast, weight leaves the platform fast
        pre = rng.uniform(0.2, 0.6); m = (t >= t1) & (t < t1 + pre); yt = sgn * (b["fc"] + rng.uniform(0.3, 1.0) * b["fw"] / 2)
        s["cy"] = np.where(m, s["cy"] + (yt - s["cy"]) * ((t - t1) / pre) ** 2, s["cy"]); s["cy"] = np.where(t >= t1 + pre, yt, s["cy"])
        sw = rng.uniform(0.15, 0.35); tc = t1 + pre + sw; Tt = rng.uniform(0.08, 0.3)
        Ff = np.where(t >= tc, (1 - ss((t - tc) / Tt)), Ff)
        if rng.random() < 0.4:
            tg = tc - rng.uniform(0, 0.2); s["Fb"] = np.where((t >= tg) & (t < tg + rng.uniform(0.1, 0.3)), rng.uniform(0.2, 0.5), s["Fb"])
    s["Ff"] = np.clip(Ff, 0, None); return s, b, kind

def noisy(s, rng, v):
    o = {k: s[k] + rng.normal(0, 0.015, len(s[k])) for k in ("Ff", "Fs", "Fb")}
    for k in ("cx", "cy"):
        sig = v["cop_noise"] * np.maximum(1.0, 0.5 / np.maximum(s["Ff"], 0.05))      # COP error grows as the plate unloads
        c = s[k] + rng.normal(0, 1, len(s[k])) * sig; o[k] = np.where(s["Ff"] > 0.05, c, np.nan)
    return o

def features(o, b):
    tot = np.convolve(o["Ff"] + o["Fs"] + o["Fb"], np.ones(5) / 5, "same"); ff = np.convolve(o["Ff"], np.ones(3) / 3, "same")
    hi = np.where(tot > 0.8)[0]; ie = None
    if len(hi):
        lo = np.where((tot < 0.1) & (np.arange(len(tot)) > hi[0]))[0]
        if len(lo): ie = int(lo[0])
    spike_i = int(np.argmax(ff)); spike = float(ff[spike_i])
    if ie is None:
        if spike < 1.3: return None
        ie = spike_i
    j9 = np.where(tot[:ie] >= 0.9)[0]; i9 = int(j9[-1]) if len(j9) else max(0, ie - 50)
    j5 = np.where(tot[:ie] >= 0.5)[0]; i5 = int(j5[-1]) if len(j5) else ie
    tun = (ie - i9) * DT; shape = (i5 - i9) / max(ie - i9, 1)
    xc = b["ax"] + 0.25 * b["fl"]; k = i5
    while k > i9 and np.isnan(o["cy"][k]): k -= 1
    ey = (abs(o["cy"][k]) - b["fc"]) / (b["fw"] / 2) if not np.isnan(o["cy"][k]) else 0.0
    ex = (o["cx"][k] - xc) / (b["fl"] / 2) if not np.isnan(o["cx"][k]) else 0.0
    edge = float(max(ey, ex))
    w0 = max(0, ie - 100); cy, cx = o["cy"][w0:ie], o["cx"][w0:ie]
    def lp(c):
        c = np.asarray(c, float); good = ~np.isnan(c); c = np.where(good, c, np.interp(np.arange(len(c)), np.where(good)[0], c[good]) if good.any() else 0.0)
        c = np.pad(c, 12, mode="edge"); return np.convolve(c, np.ones(25) / 25, "valid")      # edge-padded, no zero-padding artefact
    def speed(cy_, cx_):                         # 0.25 s moving average, speed over 0.1 s
        a, b_ = lp(cy_), lp(cx_); return np.hypot(a[10:] - a[:-10], b_[10:] - b_[:-10]) / 0.1
    v = speed(cy, cx) if len(cy) > 30 else np.zeros(1); okm = (o["Ff"][w0 + 10:ie] > 0.2)[: len(v)] if len(cy) > 30 else np.zeros(1, bool)
    copv = float(np.percentile(v[okm], 95)) if okm.sum() > 3 else 0.0
    barp = float(np.max(o["Fb"][max(0, ie - 100):ie + 30])) if ie > 0 else 0.0
    w2 = max(0, ie - 100); vv = speed(o["cy"][w2:ie], o["cx"][w2:ie]) if ie - w2 > 30 else np.zeros(0); still = (o["Ff"][w2 + 10:ie] > 0.5)[: len(vv)]
    run = best = 0
    for a, q in zip(still[1:], vv < 0.05):
        run = run + 1 if (a and q) else 0; best = max(best, run)
    dwell = best * DT
    post = float(np.max(ff[max(0, ie - 50):ie + 250])) if spike >= 1.3 else float(np.max(ff[ie:ie + 250])) if ie < len(ff) else 0.0
    return dict(t_unload=tun, shape=shape, edge=edge, cop_speed=copv, bar_peak=barp, dwell=dwell, impact=max(post, 0.0))

FEATS = ["t_unload", "shape", "edge", "cop_speed", "bar_peak", "dwell", "impact"]

def dataset(v, seed):
    rng = np.random.default_rng(seed); rows = []
    for _ in range(N_EACH):
        s, b, k = normal(rng, v); rows.append((0, k, features(noisy(s, rng, v), b)))
    for _ in range(N_EACH // 5):
        s, b, k = sitback(rng, v); rows.append((0, k, features(noisy(s, rng, v), b)))
    for _ in range(N_EACH):
        s, b, k = fall(rng, v); rows.append((1, k, features(noisy(s, rng, v), b)))
    return rows

def logreg(X, y, l2=1e-2, it=4000, lr=0.3):
    w = np.zeros(X.shape[1]); c = 0.0
    for _ in range(it):
        p = 1 / (1 + np.exp(-(X @ w + c))); g = X.T @ (p - y) / len(y) + l2 * w; w -= lr * g; c -= lr * float(np.mean(p - y))
    return w, c

def roc(score, y):
    o = np.argsort(-score); ys = y[o]; tp = np.cumsum(ys) / max(ys.sum(), 1); fp = np.cumsum(1 - ys) / max((1 - ys).sum(), 1)
    auc = float(np.trapezoid(np.r_[0, tp], np.r_[0, fp])); return fp, tp, auc

def tpr_at(fp, tp, f): return float(tp[np.searchsorted(fp, f, side="right") - 1]) if np.any(fp <= f) else 0.0

def rule(F, th):
    return (F["impact"] >= 1.3) | ((F["edge"] >= th["edge"]) & (F["dwell"] < th["dwell"])) | ((F["bar_peak"] >= th["bar"]) & (F["t_unload"] < th["tun"]))

def evaluate(v, seed=1):
    rows = dataset(v, seed); ev = [(y, k, f) for y, k, f in rows if f is not None]
    no_event = {"normal": sum(1 for y, k, f in rows if f is None and y == 0), "fall": sum(1 for y, k, f in rows if f is None and y == 1)}
    y = np.array([e[0] for e in ev], float); kinds = np.array([e[1] for e in ev]); X = np.array([[e[2][k] for k in FEATS] for e in ev])
    rng = np.random.default_rng(seed + 7); idx = rng.permutation(len(y)); tr, te = idx[: len(y) // 2], idx[len(y) // 2:]
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9; Z = (X - mu) / sd
    w, c = logreg(Z[tr], y[tr]); sc = Z @ w + c
    fp, tp, auc = roc(sc[te], y[te])
    Ft = {k: X[:, i] for i, k in enumerate(FEATS)}; best = None
    n_norm_tr = (y[tr] == 0).sum()
    for e_ in (0.4, 0.5, 0.6, 0.7, 0.8):
        for d_ in (0.15, 0.3, 0.5):
            for b_ in (0.15, 0.25, 0.35):
                for t_ in (0.3, 0.5, 0.8):
                    th = dict(edge=e_, dwell=d_, bar=b_, tun=t_); a = rule({k: v_[tr] for k, v_ in Ft.items()}, th)
                    fa = a[y[tr] == 0].sum() / n_norm_tr; det = a[y[tr] == 1].mean()
                    if fa <= 0.05 and (best is None or det > best[0]): best = (det, th)
    if best is None: best = (0, dict(edge=0.8, dwell=0.15, bar=0.35, tun=0.3))
    th = best[1]; a = rule({k: v_[te] for k, v_ in Ft.items()}, th)
    det_rule = float(a[y[te] == 1].mean()); fa_rule = float(a[y[te] == 0].mean())
    # per subtype at the logistic threshold giving <= 5 false alarms per 100 exits on the test half
    thr = np.sort(sc[te][y[te] == 0])[::-1][max(0, int(0.05 * (y[te] == 0).sum()) - 1)]
    by = {k: round(float((sc[te][(kinds[te] == k)] > thr).mean()), 3) for k in sorted(set(kinds[te])) if (kinds[te] == k).sum()}
    # single-feature AUCs (how much each one carries alone)
    single = {k: round(max(roc(X[te, i], y[te])[2], roc(-X[te, i], y[te])[2]), 3) for i, k in enumerate(FEATS)}
    out = dict(n_events=int(len(y)), no_event=no_event, auc=round(auc, 3), tpr_at_fa_per100={str(f): round(tpr_at(fp, tp, f / 100), 3) for f in (1, 5, 10)},
               rule=dict(thresholds=th, detection=round(det_rule, 3), false_alarms_per100=round(100 * fa_rule, 1)),
               coef_std=dict(zip(FEATS, np.round(w, 2).tolist())), single_feature_auc=single, detect_by_kind_at_5fa=by,
               medians={g: {k: round(float(np.median(X[(y == (1 if g == "fall" else 0)), i])), 3) for i, k in enumerate(FEATS)} for g in ("normal", "fall")})
    return out, (fp, tp), (X, y, kinds)

BASE = dict(cop_noise=0.01, step_T=(0.15, 1.0), normal_edge=0.3, pre=(0.3, 1.0), theta0=(1, 6), slow=1.0)
VARS = {"base": {}, "cop_noise_2cm": dict(cop_noise=0.02), "fast_steps_edgy_stance": dict(step_T=(0.08, 0.35), normal_edge=0.7),
        "slow_falls": dict(pre=(0.8, 2.0), theta0=(0.5, 2), slow=2.0), "worst": dict(cop_noise=0.02, step_T=(0.08, 0.35), normal_edge=0.7, pre=(0.8, 2.0), theta0=(0.5, 2), slow=2.0)}

def example_traces():
    rng = np.random.default_rng(3); v = BASE; ex = {}
    for name, fn in (("正常：侧向迈下", normal), ("正常：拖步两次", normal), ("跌倒：侧向倾倒", fall), ("跌倒：膝软坐到踏板上", fall)):
        for _ in range(200):
            s, b, k = fn(rng, v)
            want = {"正常：侧向迈下": "step_side", "跌倒：侧向倾倒": "lateral", "跌倒：膝软坐到踏板上": "knees"}.get(name)
            if name == "正常：拖步两次":
                if k == "step_side" and np.any((s["Ff"] > 0.3) & (s["Ff"] < 0.7) & (np.gradient(s["Ff"]) == 0)): ex[name] = (s, b); break
                continue
            if k == want: ex[name] = (s, b); break
        if name not in ex: ex[name] = (s, b)
    return ex

if __name__ == "__main__":
    res = {}; curves = {}; data = None
    for nm, dv in VARS.items():
        v = dict(BASE, **dv); r, cv, d = evaluate(v); res[nm] = r; curves[nm] = cv
        if nm == "base": data = d
        print(nm, "AUC", r["auc"], "TPR@1/5/10 FA per100", r["tpr_at_fa_per100"], "rule", r["rule"]["detection"], r["rule"]["false_alarms_per100"], "noevent", r["no_event"])
    print("base by kind", res["base"]["detect_by_kind_at_5fa"]); print("single AUC", res["base"]["single_feature_auc"]); print("coef", res["base"]["coef_std"])
    print("medians", res["base"]["medians"])
    exits_per_day = 6; fa = res["base"]["rule"]["false_alarms_per100"]
    out = dict(note=__doc__, assumptions=BASE, variants=VARS, results=res,
               false_alarm_cost=dict(exits_per_day=exits_per_day, rule_false_prompts_per_week=round(fa / 100 * exits_per_day * 7, 1),
                                     note="每次误报只是一次语音询问（按握把按钮即取消）；30 秒没回应才呼叫家属，所以呼叫家属的误报还要乘上“没听到/没按”的概率"),
               out_of_scope=dict(class_O="离开踏板以后的跌倒（去厕所路上）：踏板、座板、横杆都没有任何信号，检出率 0，需要另外的设备（床边毫米波雷达或可穿戴报警）",
                                 backward_onto_seat="往后倒到座板上：座板接住，控制器已有处理（停住、提醒、呼叫），本检验不含"))
    json.dump(out, open(os.path.join(OUT, "exit_detect.json"), "w"), ensure_ascii=False, indent=1, default=float)
    # figure
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR); plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]; plt.rcParams["axes.unicode_minus"] = False
    fig = plt.figure(figsize=(14, 8.5)); ex = example_traces(); t = np.arange(0, TT, DT)
    for i, (nm, (s, b)) in enumerate(ex.items()):
        ax = fig.add_subplot(3, 4, i + 1); ax.plot(t, s["Ff"], label="踏板力", color="#1E5AA8"); ax.plot(t, s["Fb"], label="横杆力", color="#9A5408")
        ax.plot(t, s["Ff"] + s["Fs"] + s["Fb"], ":", label="三处之和", color="#333"); ax.set_title(nm, fontsize=11); ax.set_ylim(-0.1, 2.6); ax.set_xlabel("s")
        ax2 = fig.add_subplot(3, 4, i + 5); ax2.plot(t, np.where(s["Ff"] > 0.05, (np.abs(s["cy"]) - b["fc"]) / (b["fw"] / 2), np.nan), color="#B3261E")
        ax2.axhline(1, color="#999", lw=0.8, ls="--"); ax2.axhline(0, color="#999", lw=0.8); ax2.set_ylim(-3, 2); ax2.set_ylabel("COP 横向\n0=脚中 1=外缘"); ax2.set_xlabel("s")
        if i == 0: ax.legend(fontsize=8, loc="upper right")
    X, y, kinds = data; ax = fig.add_subplot(3, 4, 9)
    for lab, col, nm in ((0, "#1E5AA8", "正常离开"), (1, "#B3261E", "跌倒")):
        m = y == lab; ax.scatter(X[m, 0], X[m, 2], s=5, alpha=0.4, color=col, label=nm)
    ax.set_xlabel("卸载时间 0.9→0.1 (s)"); ax.set_ylabel("COP 贴边程度"); ax.set_xlim(0, 2); ax.set_ylim(-2, 2.5); ax.legend(fontsize=8)
    ax = fig.add_subplot(3, 4, 10)
    for i, (lab, col) in enumerate(((0, "#1E5AA8"), (1, "#B3261E"))):
        m = y == lab; ax.hist(np.clip(X[m, 6], 0, 3.5), bins=30, alpha=0.5, color=col)
    ax.set_xlabel("离开时踏板峰值 (BW)"); ax.set_yscale("log")
    ax = fig.add_subplot(3, 4, (11, 12))
    for nm, (fp, tp) in curves.items(): ax.plot(100 * fp, tp, label=f'{nm}  AUC {res[nm]["auc"]}')
    ax.set_xlim(0, 30); ax.set_xlabel("误报：每 100 次正常离开"); ax.set_ylabel("跌倒检出率"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.suptitle("离开踏板时的跌倒检测：合成数据可行性检验（只能否定或保留这个想法，不能证明有效）", fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "exit_detect.png"), dpi=110)
