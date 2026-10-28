"""Insert the 3.5 s in-the-room shot (lines gather into the bed, a line climbs the rail to the switch) at 25.0 s.
python3 music_ctx.py music_v6_445.wav music.wav   (44.5 s in -> 47.5 s out; the motion shot now starts half a second later in its own clock)"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile
src = open("music.py").read(); exec(src[: src.index("beats = np.arange")])
rng2 = np.random.default_rng(23)
def seg(d): return np.zeros((2, int(d * SR)))
def add(buf, x, t, g=1.0, pan=0.0):
    i = int(t * SR); x = np.asarray(x) * g
    if x.ndim == 1: x = np.stack([np.sqrt(0.5 * (1 - pan)) * x, np.sqrt(0.5 * (1 + pan)) * x])
    n = min(x.shape[1], buf.shape[1] - i); buf[:, i:i + n] += x[:, :n]
def verb(buf, wet=0.3, dec=0.6):
    ir_t = tt(2.0); out = buf.copy()
    for c in range(2):
        ir = rng2.standard_normal(len(ir_t)) * np.exp(-ir_t / dec); ir = filt(ir, "lowpass", 6000); ir /= np.sqrt(np.sum(ir ** 2)); out[c] += wet * signal.fftconvolve(buf[c], ir)[: buf.shape[1]]
    return out
X = seg(3.5); MB = seg(3.5)
for b in np.arange(0, 3.5, BEAT):
    add(X, kick(0.9 if b >= 1.0 else 0.7), b)
    if int(round(b / BEAT)) % 2 == 1: add(X, clap(), b, 0.6)
    add(X, hat(), b + 0.25, 0.45, pan=-0.2)
    if b >= 1.0: add(X, hat(), b + 0.125, 0.3, pan=0.35); add(X, hat(), b + 0.375, 0.3, pan=0.35)
chords = [(0.0, 1.5, 0), (1.5, 1.0, 1), (2.5, 1.0, 3)]            # Am, F, G -> resolves to Am at the cut
for t0, d, c in chords:
    p = pad(c, 0.10, 2000)[:, : int(d * SR)]; add(MB, p, t0)
    for b in np.arange(t0, t0 + d, 0.25): add(MB, bass_note(ROOT[c] + (12 if int(b * 4) % 4 in (1, 3) else 0), 0.22, 600), b, 0.9)
for i in range(16):                                                 # lines flying in: short airy streaks
    t0 = 0.10 + 0.75 * ((i * 0.6180339) % 1); add(X, whoosh(0.22) * 0.5, t0, 1.0, pan=rng2.random() * 1.6 - 0.8)
for i, n in enumerate((76, 81, 84)): add(X, ping(NOTE(n), 0.8), 1.0 + i * 0.06, 0.28)   # the bed locks together
t_ = tt(0.85); add(X, filt(np.sin(2 * np.pi * np.cumsum(200 + 260 * (t_ / 0.85) ** 1.3) / SR), "lowpass", 1800) * np.hanning(len(t_)) * 0.16, 1.15)   # the line runs up the rail
add(X, ping(NOTE(88), 1.0), 2.0, 0.5); add(X, snap() * 0.5, 2.0)                       # it reaches the switch
add(X, ping(NOTE(91), 0.6), 2.05, 0.25); add(X, ping(NOTE(84), 0.6), 2.2, 0.25)
add(X, whoosh(0.5), 2.65, 0.7)
pump = np.ones(X.shape[1])
for b in np.arange(0, 3.5, BEAT):
    i = int(b * SR); n = int(0.45 * SR); sgm = 1 - 0.65 * np.exp(-np.arange(n) / SR * 9); pump[i:i + n] = np.minimum(pump[i:i + n], sgm[: X.shape[1] - i])
X = verb(X + MB * pump, 0.3, 0.6)
sr, core = wavfile.read(sys.argv[1]); core = core.astype(float).T / 32767
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
X *= 10 ** ((rms(core[:, int(13 * SR):int(24 * SR)]) - rms(X)) / 20)
xf = int(0.012 * SR)
def join(a, b):
    a = a.copy(); b = b.copy(); a[:, -xf:] *= np.linspace(1, 0, xf); b[:, :xf] *= np.linspace(0, 1, xf); return np.concatenate([a, b], axis=1)
out = join(join(core[:, : int(25.0 * SR)], X), core[:, int(25.5 * SR):])
out = np.clip(out, -1, 1)
wavfile.write(sys.argv[2], SR, (out.T * 32767).astype(np.int16)); print("ok", out.shape[1] / SR, "s")
