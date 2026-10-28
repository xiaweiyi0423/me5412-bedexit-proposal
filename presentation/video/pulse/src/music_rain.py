"""Splice the rain-night mood (8-11 s) and the echo ending (40-44.5 s) into the 42 s core score.
python3 music_rain.py music_core42.wav music.wav"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile
src = open("music.py").read(); exec(src[: src.index("beats = np.arange")])          # primitives: kick, pad, ping, riser, boom, crash, filt, noise, tt, NOTE, SR
rngr = np.random.default_rng(11)


def seg(d): return np.zeros((2, int(d * SR)))


def add(buf, x, t, g=1.0, pan=0.0):
    i = int(t * SR); x = np.asarray(x) * g
    if x.ndim == 1: x = np.stack([np.sqrt(0.5 * (1 - pan)) * x, np.sqrt(0.5 * (1 + pan)) * x])
    n = min(x.shape[1], buf.shape[1] - i); buf[:, i:i + n] += x[:, :n]


def verb(buf, wet=0.35, dec=0.7):
    ir_t = tt(2.5); out = np.zeros_like(buf)
    for c in range(2):
        ir = rngr.standard_normal(len(ir_t)) * np.exp(-ir_t / dec); ir = filt(ir, "lowpass", 5000); ir /= np.sqrt(np.sum(ir ** 2))
        out[c] = buf[c] + wet * signal.fftconvolve(buf[c], ir)[: buf.shape[1]]
    return out


def rain(d, g=1.0):
    n = noise(d); x = filt(n, "bandpass", [700, 7000]) * 0.06 + filt(noise(d), "lowpass", 220) * 0.03
    mod = 1 + 0.25 * np.sin(2 * np.pi * 0.7 * tt(d)) + 0.1 * np.sin(2 * np.pi * 2.3 * tt(d))
    y = np.stack([x * mod, np.roll(x, 777) * mod])
    for _ in range(int(d * 9)):     # drips
        t0 = rngr.random() * (d - 0.1); f = 2200 + 2200 * rngr.random(); dr = np.sin(2 * np.pi * f * tt(0.04)) * np.exp(-tt(0.04) * 90) * 0.05
        add(y, dr, t0, 1.0, pan=rngr.random() * 2 - 1)
    return y * g


def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


# ---- rain night, 3.0 s
R = seg(3.0)
add(R, rain(3.0), 0.0)
p = pad(0, 0.10, 900); p *= np.minimum(1, np.arange(p.shape[1]) / (0.4 * SR)); add(R, p, 0.0); add(R, pad(1, 0.08, 800)[:, : SR], 2.0)
for t0, n in ((0.15, 76), (0.7, 72), (1.35, 69)): add(R, ping(NOTE(n), 1.2), t0, 0.35)
t_ = tt(0.85); f_ = np.where(t_ < 0.5, 210 + 140 * t_ / 0.5, 350 - 170 * (t_ - 0.5) / 0.35)                       # the try: up, then a sigh down
add(R, filt(np.sin(2 * np.pi * np.cumsum(f_) / SR), "lowpass", 1200) * np.hanning(len(t_)) * 0.14, 0.45)
for t0 in (1.30, 1.36, 1.42, 1.5, 1.6):                                                                             # the line breaks into drops
    add(R, np.sin(2 * np.pi * (1800 + 900 * rngr.random()) * tt(0.05)) * np.exp(-tt(0.05) * 70) * 0.12, t0, 1.0, pan=rngr.random() - 0.5)
add(R, ping(NOTE(81), 0.8), 1.6, 0.25); add(R, ping(NOTE(84), 0.8), 2.2, 0.28)
add(R, riser(0.6, 600, 9000), 2.35, 0.7)
for i, b in enumerate(np.arange(2.5, 2.95, 0.0625)): add(R, arp_note([69, 72, 76][i % 3] + 12, 0.1, 2500 + 4000 * i / 8), b, 1.2)
R = verb(R, 0.45, 0.8); R[:, int(2.95 * SR):] = 0                                                                  # rain freezes on the title hit
R[:, int(2.9 * SR):int(2.95 * SR)] *= np.linspace(1, 0, int(0.05 * SR))
# ---- echo ending, 6.0 s (stand at 2.0, pull out into the sunlit room 2.3-4.9, title 3.6)
E = seg(6.0)
rn = rain(2.4) * np.r_[np.ones(int(1.0 * SR)), np.linspace(1, 0, int(1.4 * SR))][None, :]; add(E, rn, 0.0, 2.0)
add(E, pad(0, 0.14, 1000)[:, : 2 * SR], 0.0)
add(E, ping(NOTE(81), 0.9), 0.5, 0.4); add(E, snap() * 0.4, 0.5)
t_ = tt(1.4); add(E, filt(np.sin(2 * np.pi * np.cumsum(180 + 200 * (t_ / 1.4) ** 1.2) / SR), "lowpass", 1600) * np.minimum(1, t_ / 0.15) * np.minimum(1, (1.4 - t_) / 0.1) * 0.16, 0.6)
for i, b in enumerate(np.arange(0.85, 2.0, 0.125)): add(E, arp_note([69, 72, 76, 79][i % 4] + 12 + (12 if i >= 5 else 0), 0.11, 1500 + 3500 * i / 9), b, 1.1, pan=0.4 * np.sin(i))
for b in (1.0, 1.5): add(E, filt(kick(0.6), "lowpass", 400), b)
add(E, riser(0.7, 800, 10000), 1.3, 0.5)
add(E, boom(2.4) * 0.9, 2.0); add(E, crash(2.4), 2.0, 0.8)
hold = np.zeros((2, int(4.0 * SR)))
for n in (60, 64, 67, 72):                                                                                          # C major, open
    for det in (-0.006, 0.0, 0.006):
        s_ = saw(NOTE(n), 4.0, det); hold[0] += s_; hold[1] += np.roll(s_, 200)
open_ = np.concatenate([np.array([filt(c[i:i + 4800], "lowpass", 1400 + 3200 * min(1, i / (2.6 * SR))) for c in hold]) for i in range(0, hold.shape[1], 4800)], axis=1)   # filter opens as the sun comes in
hold = open_[:, : hold.shape[1]] * 0.024 * np.clip((4.0 - np.arange(hold.shape[1]) / SR) / 1.1, 0, 1) ** 1.5; add(E, hold, 2.0)   # full until the title has landed, then fades
for i, (n, t0) in enumerate(((88, 2.6), (91, 3.0), (96, 3.4), (100, 4.2))): add(E, ping(NOTE(n), 1.0), t0, 0.16, pan=[-0.4, 0.4, -0.2, 0.2][i])
for i, n in enumerate((84, 88, 91)): add(E, ping(NOTE(n), 1.4), 4.2 + i * 0.08, 0.25)
for b in np.arange(2.5, 5.5, 0.5):                                                                                  # the pulse comes back with the colour: kick on every ring
    add(E, kick(0.85), b); add(E, hat(), b + 0.25, 0.4, pan=-0.2)
    if int(round(b / 0.5)) % 2 == 1: add(E, clap(), b, 0.5)
for i, b in enumerate(np.arange(2.5, 5.4, 0.125)): add(E, arp_note([72, 76, 79, 84][i % 4] + (12 if (i // 4) % 2 else 0), 0.1, 5200), b, 0.9, pan=0.5 * np.sin(i * 0.7))
E = verb(E, 0.45, 0.9); E[:, -int(0.45 * SR):] *= np.linspace(1, 0, int(0.45 * SR)) ** 2
# ---- splice into the core score: old 0-8 | rain | old 10-39 | echo
sr, core = wavfile.read(sys.argv[1]); core = core.astype(float).T / 32767
lvl = rms_db(core[:, int(12 * SR):int(36 * SR)])
R *= 10 ** ((lvl - 7 - rms_db(R[:, : int(2.3 * SR)])) / 20); E *= 10 ** ((lvl - 2 - rms_db(E[:, int(2.0 * SR):int(3.5 * SR)])) / 20)
xf = int(0.012 * SR)
def join(a, b):
    a = a.copy(); b = b.copy(); a[:, -xf:] *= np.linspace(1, 0, xf); b[:, :xf] *= np.linspace(0, 1, xf); return np.concatenate([a, b], axis=1)
out = join(join(join(core[:, : int(8 * SR)], R), core[:, int(10 * SR):int(39 * SR)]), E)
out = np.tanh(out * 1.1) / np.tanh(1.1) * 10 ** (-1 / 20)
wavfile.write(sys.argv[2], SR, (out.T * 32767).astype(np.int16)); print("ok", out.shape[1] / SR, "s; core rms", round(lvl, 1))
