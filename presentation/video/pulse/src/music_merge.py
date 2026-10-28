"""Replace the separate motion (28.5-34) and how-to (34-40) audio with one 6.5 s block for the merged four-step shot.
python3 music_merge.py music_v9_49.wav music.wav   (49 s in -> 44 s out)"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile
src = open("music.py").read(); exec(src[: src.index("beats = np.arange")])
rng3 = np.random.default_rng(31)
def seg(d): return np.zeros((2, int(d * SR)))
def add(buf, x, t, g=1.0, pan=0.0):
    i = int(t * SR); x = np.asarray(x) * g
    if x.ndim == 1: x = np.stack([np.sqrt(0.5 * (1 - pan)) * x, np.sqrt(0.5 * (1 + pan)) * x])
    n = min(x.shape[1], buf.shape[1] - i); buf[:, i:i + n] += x[:, :n]
def verb(buf, wet=0.3, dec=0.6):
    ir_t = tt(2.0); out = buf.copy()
    for c in range(2):
        ir = rng3.standard_normal(len(ir_t)) * np.exp(-ir_t / dec); ir = filt(ir, "lowpass", 6000); ir /= np.sqrt(np.sum(ir ** 2)); out[c] += wet * signal.fftconvolve(buf[c], ir)[: buf.shape[1]]
    return out
D_, STOP = 6.5, 5.0
X = seg(D_); MB = seg(D_)
for b in np.arange(0, STOP, BEAT):
    add(X, kick(0.95), b); add(X, hat(True), b + 0.25, 0.45, pan=-0.2)
    if int(round(b / BEAT)) % 2 == 1: add(X, clap(), b, 0.7)
    for k in (0.125, 0.375): add(X, hat(), b + k, 0.35, pan=0.35)
for t0, d, c in ((0.0, 1.5, 0), (1.5, 1.0, 1), (2.5, 2.0, 2), (4.5, 0.5, 3)):     # Am F C G across the four steps
    add(MB, pad(c, 0.10, 2200)[:, : int(d * SR)], t0)
    for b in np.arange(t0, t0 + d, 0.25): add(MB, bass_note(ROOT[c] + (12 if int(b * 4) % 4 in (1, 3) else 0), 0.22, 650), b, 1.0)
for i, b in enumerate(np.arange(0, STOP, 0.125)):
    c = 0 if b < 1.5 else 1 if b < 2.5 else 2 if b < 4.5 else 3; n = CH[c][i % 3] + 12 + (12 if (i // 3) % 2 else 0)
    if b < 2.5 and i % 2: continue
    add(MB, arp_note(n, 0.11, 4200), b, 0.7, pan=0.5 * np.sin(i * 0.7))
for b in (0.0, 1.5, 2.5): add(X, thud(), b, 0.9); add(X, crash(0.6), b, 0.25)            # each step lands
for b in (2.0, 2.5): add(X, ping(NOTE(69), 0.5), b, 0.28)                                 # the grip, on the beats: a soft pluck, not a beep
t_ = tt(2.05); add(X, filt(np.sin(2 * np.pi * np.cumsum(140 + 90 * (t_ / 2.05) ** 0.8) / SR) + 0.3 * np.sign(np.sin(2 * np.pi * np.cumsum(2 * (140 + 90 * (t_ / 2.05) ** 0.8)) / SR)), "lowpass", 1200) * np.minimum(1, t_ / 0.2) * np.minimum(1, (2.05 - t_) / 0.3) * 0.18, 2.75)
for i, b in enumerate((3.25, 3.5, 3.75)): add(X, ping(NOTE([84, 88, 91][i]), 0.6), b, 0.35)   # forward / up / tilt arrows
pump = np.ones(X.shape[1])
for b in np.arange(0, STOP, BEAT):
    i = int(b * SR); n = int(0.45 * SR); sgm = 1 - 0.65 * np.exp(-np.arange(n) / SR * 9); pump[i:i + n] = np.minimum(pump[i:i + n], sgm[: X.shape[1] - i])
X = verb(X + MB * pump, 0.3, 0.6)
cut = int(STOP * SR) + int(0.01 * SR); X[:, cut:] = 0; X[:, cut - int(0.02 * SR):cut] *= np.linspace(1, 0, int(0.02 * SR))   # release: everything stops
def lock():   # electromagnetic brake engaging: a dry click, a latch, a deep thump - solid, not an alarm
    t = tt(0.8); x = np.sin(2 * np.pi * np.cumsum(52 + 45 * np.exp(-t * 28)) / SR) * np.exp(-t * 6.5) * 1.1 + np.sin(2 * np.pi * 108 * t) * np.exp(-t * 14) * 0.25
    c = filt(noise(0.03), "bandpass", [1400, 3800]) * np.exp(-tt(0.03) * 140) * 0.7; x[: len(c)] += c
    l = filt(noise(0.06), "bandpass", [500, 1600]) * np.exp(-tt(0.06) * 55) * 0.6; i = int(0.035 * SR); x[i:i + len(l)] += l
    return np.tanh(1.2 * x)
add(X, lock(), STOP, 1.1)
sr, core = wavfile.read(sys.argv[1]); core = core.astype(float).T / 32767
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
X *= 10 ** ((rms(core[:, int(13 * SR):int(24 * SR)]) - rms(X[:, : int(STOP * SR)])) / 20)
xf = int(0.012 * SR)
def join(a, b):
    a = a.copy(); b = b.copy(); a[:, -xf:] *= np.linspace(1, 0, xf); b[:, :xf] *= np.linspace(0, 1, xf); return np.concatenate([a, b], axis=1)
out = join(join(core[:, : int(28.5 * SR)], X), core[:, int(40.0 * SR):])
wavfile.write(sys.argv[2], SR, (np.clip(out, -1, 1).T * 32767).astype(np.int16)); print("ok", out.shape[1] / SR, "s")
