"""Hold the 81-bodies frame 1 s longer and stretch the sensing shot to 4 s; the rain leads into the echo.
python3 music_v11.py music_v10_44.wav music.wav   (44 s in -> 46 s out)"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile
src = open("music.py").read(); exec(src[: src.index("beats = np.arange")])
rng4 = np.random.default_rng(41)
def seg(d): return np.zeros((2, int(d * SR)))
def add(buf, x, t, g=1.0, pan=0.0):
    i = int(t * SR); x = np.asarray(x) * g
    if x.ndim == 1: x = np.stack([np.sqrt(0.5 * (1 - pan)) * x, np.sqrt(0.5 * (1 + pan)) * x])
    n = min(x.shape[1], buf.shape[1] - i); buf[:, i:i + n] += x[:, :n]
def verb(buf, wet=0.3, dec=0.6):
    ir_t = tt(2.0); out = buf.copy()
    for c in range(2):
        ir = rng4.standard_normal(len(ir_t)) * np.exp(-ir_t / dec); ir = filt(ir, "lowpass", 6000); ir /= np.sqrt(np.sum(ir ** 2)); out[c] += wet * signal.fftconvolve(buf[c], ir)[: buf.shape[1]]
    return out
def groove(d, chords, light=False):
    X = seg(d); MB = seg(d)
    for b in np.arange(0, d, BEAT):
        add(X, kick(0.9), b); add(X, hat(), b + 0.25, 0.45, pan=-0.2)
        if int(round(b / BEAT)) % 2 == 1: add(X, clap(), b, 0.65)
        if not light: add(X, hat(), b + 0.125, 0.3, pan=0.35); add(X, hat(), b + 0.375, 0.3, pan=0.35)
    for t0, dd, c in chords:
        add(MB, pad(c, 0.10, 2000)[:, : int(dd * SR)], t0)
        for b in np.arange(t0, t0 + dd, 0.25): add(MB, bass_note(ROOT[c] + (12 if int(b * 4) % 4 in (1, 3) else 0), 0.22, 600), b, 0.9)
    pump = np.ones(X.shape[1])
    for b in np.arange(0, d, BEAT):
        i = int(b * SR); n = int(0.45 * SR); sgm = 1 - 0.65 * np.exp(-np.arange(n) / SR * 9); pump[i:i + n] = np.minimum(pump[i:i + n], sgm[: X.shape[1] - i])
    return X, MB * pump
# 1 s more under the 81 bodies (G, as the bar it sits in), a shimmer on the held curve
G1, M1 = groove(1.0, [(0.0, 1.0, 3)]); add(G1, ping(NOTE(91), 0.8), 0.0, 0.18); G1 = verb(G1 + M1)
# sensing, 4 s: one soft ping per sensor at 0, .75, 1.5, 2.25; the summary line at 3.0
H, MH = groove(4.0, [(0.0, 2.0, 0), (2.0, 2.0, 1)])
add(H, boom(1.0), 0.0, 0.5)
for k, b in enumerate((0.0, 0.75, 1.5, 2.25)): add(H, ping(NOTE([84, 88, 91, 96][k]), 0.7), b, 0.5, pan=[-0.5, 0.5, 0.3, -0.3][k])
for n in CH[0]: add(H, arp_note(n + 24, 0.4, 5000) * 2, 3.0, 0.8)
# the room comes back at the end: the groove thins out and the rain leads in under the window (J-cut into the echo)
fadeG = np.r_[np.ones(int(3.4 * SR)), np.linspace(1, 0.45, H.shape[1] - int(3.4 * SR))]; H *= fadeG[None, :]; MH *= fadeG[None, :]
rngr = np.random.default_rng(7)
def rain(d):
    x = filt(noise(d), "bandpass", [700, 7000]) * 0.06 + filt(noise(d), "lowpass", 220) * 0.03; y = np.stack([x, np.roll(x, 777)])
    for _ in range(int(d * 9)):
        t0 = rngr.random() * (d - 0.1); f = 2200 + 2200 * rngr.random(); add(y, np.sin(2 * np.pi * f * tt(0.04)) * np.exp(-tt(0.04) * 90) * 0.05, t0, 1.0, pan=rngr.random() * 2 - 1)
    return y
rn = rain(0.6) * np.linspace(0, 1, int(0.6 * SR))[None, :] ** 1.5; add(H, rn, 3.4, 2.0)
H = verb(H + MH, 0.35, 0.6); H[:, -int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
sr, core = wavfile.read(sys.argv[1]); core = core.astype(float).T / 32767
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
ref = rms(core[:, int(13 * SR):int(24 * SR)]); G1 *= 10 ** ((ref - rms(G1)) / 20); H *= 10 ** ((ref - rms(H)) / 20)
xf = int(0.012 * SR)
def join(a, b):
    a = a.copy(); b = b.copy(); a[:, -xf:] *= np.linspace(1, 0, xf); b[:, :xf] *= np.linspace(0, 1, xf); return np.concatenate([a, b], axis=1)
out = join(join(join(join(core[:, : 16 * SR], G1), core[:, 16 * SR: 35 * SR]), H), core[:, 38 * SR:])
wavfile.write(sys.argv[2], SR, (np.clip(out, -1, 1).T * 32767).astype(np.int16)); print("ok", out.shape[1] / SR, "s")
