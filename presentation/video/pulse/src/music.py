"""120 BPM electronic track for the pulse cut, 45 s, synthesised (no samples). Every hit lands on the picture's beat grid.
python3 music.py out.wav"""
import sys
import numpy as np
from scipy import signal

SR = 48000; BEAT = 0.5; DUR = 45.0; XO = 10.0; RAW = False; N = int((DUR + 3) * SR)   # cues on the old 36 s clock move by XO after 12 s
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N); VERB = np.zeros((2, N)); MUS = np.zeros((2, N))   # MUS = bus that gets side-chained


def warp(t):   # old 36 s clock -> picture clock: design block inserted at 12-22, assembly (old 12-16) at double speed
    if RAW or t < 12: return t
    if t < 16: return 23 + (t - 12) / 2
    if t < 18: return 25 + (t - 16)
    return t + 9


def put(x, t, g=1.0, pan=0.0, bus="mix", verb=0.0):
    t = warp(t); i = int(round(t * SR)); x = np.asarray(x) * g
    if i >= N: return
    x = x[: N - i]; gl = np.sqrt(0.5 * (1 - pan)); gr = np.sqrt(0.5 * (1 + pan))
    tgt = (L, R) if bus == "mix" else (MUS[0], MUS[1])
    tgt[0][i:i + len(x)] += gl * x; tgt[1][i:i + len(x)] += gr * x
    if verb: VERB[0][i:i + len(x)] += verb * gl * x; VERB[1][i:i + len(x)] += verb * gr * x


def tt(d): return np.arange(int(d * SR)) / SR
def sos(kind, f, order=2): return signal.butter(order, f, kind, fs=SR, output="sos")
def filt(x, kind, f, order=2): return signal.sosfilt(sos(kind, f, order), x)
def noise(d): return rng.standard_normal(int(d * SR))


def saw(f, d, det=0.0):
    t = np.arange(int(d * SR * 4)) / (SR * 4); ph = (f * (1 + det) * t + rng.random()) % 1.0
    return signal.resample_poly(2 * ph - 1, 1, 4)


def env_adsr(d, a=0.005, dec=0.1, s=0.6, r=0.1):
    n = int(d * SR); e = np.ones(n) * s; na = max(1, int(a * SR)); nd = max(1, int(dec * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[na:na + nd] = np.linspace(1, s, len(e[na:na + nd])); e[-nr:] *= np.linspace(1, 0, nr); return e


def kick(g=1.0):
    t = tt(0.45); f = 48 + 110 * np.exp(-t * 28); ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 7.5); x[:150] += noise(150 / SR) * np.linspace(0.5, 0, 150); return np.tanh(1.6 * x) * g


def clap():
    x = np.zeros(int(0.3 * SR))
    for k, d in enumerate([0, 0.011, 0.022]):
        n = filt(noise(0.25), "bandpass", [900, 3200]) * np.exp(-tt(0.25) * (60 if k < 2 else 16)); i = int(d * SR); x[i:i + len(n)] += n[: len(x) - i]
    return x * 0.9


def hat(open_=False):
    d = 0.3 if open_ else 0.06; return filt(noise(d), "highpass", 7500, 4) * np.exp(-tt(d) * (11 if open_ else 70)) * 0.5


def blip(f=1000, d=0.07, g=0.5): t = tt(d); return np.sin(2 * np.pi * f * t) * np.minimum(1, (d - t) / 0.01) * np.minimum(1, t / 0.002) * g


def ping(f, d=0.6):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2.01 * f * t)) * np.exp(-t * 7) * 0.5


def boom(d=2.2):
    t = tt(d); f = 38 + 50 * np.exp(-t * 6); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    x += filt(noise(d), "lowpass", 900) * np.exp(-t * 9) * 0.6; return np.tanh(1.4 * x)


def crash(d=2.5): return filt(noise(d), "highpass", 4500) * np.exp(-tt(d) * 2.2) * 0.35


def riser(d, f0=400, f1=7000):
    x = noise(d); out = np.zeros_like(x); n = len(x); seg = 2048
    for i in range(0, n, seg):
        fc = f0 * (f1 / f0) ** (i / n); out[i:i + seg] = filt(x[i:i + seg], "bandpass", [fc * 0.7, min(fc * 1.4, SR / 2 - 100)])
    return out * np.linspace(0.05, 1, n) ** 2 * 0.5


def whoosh(d=0.45): x = riser(d, 300, 5000); return x * np.hanning(len(x)) * 2.2


def snap():   # metallic part landing
    t = tt(0.25); x = filt(noise(0.25), "highpass", 2500) * np.exp(-t * 55) * 0.8
    x += (np.sin(2 * np.pi * 3150 * t) + 0.6 * np.sin(2 * np.pi * 4870 * t)) * np.exp(-t * 26) * 0.35
    x += np.sin(2 * np.pi * (180 + 200 * np.exp(-t * 40)) * t) * np.exp(-t * 30) * 0.6; return x


def thud(): t = tt(0.4); return np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 25)) * t) * np.exp(-t * 9) + filt(noise(0.4), "lowpass", 500) * np.exp(-t * 20) * 0.4


def brake():  # STOP: solenoid clunk
    t = tt(0.5); x = thud() * 0.0; x = np.zeros(len(t)); y = filt(noise(0.06), "bandpass", [600, 2500]) * np.exp(-tt(0.06) * 60); x[: len(y)] += y * 1.2
    x += np.sin(2 * np.pi * 95 * t) * np.exp(-t * 14) * 0.9; return x


NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)
CH = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]       # Am F C G (one bar each)
ROOT = [33, 29, 36, 31]


def pad(bar, g=0.12, cutoff=1800):
    notes = CH[bar % 4]; d = 2.0; x = np.zeros((2, int(d * SR)))
    for n in notes:
        for k, det in enumerate([-0.011, -0.004, 0.0, 0.005, 0.012]):
            s = saw(NOTE(n), d, det); x[k % 2] += s; x[(k + 1) % 2] += 0.4 * s
    e = env_adsr(d, 0.08, 0.3, 0.8, 0.25); x = np.array([filt(c, "lowpass", cutoff) for c in x]) * e * g / 5
    return x


def bass_note(n, d=0.22, cut=520):
    x = 0.6 * saw(NOTE(n), d) + 0.4 * np.sign(np.sin(2 * np.pi * NOTE(n) * tt(d))); x = filt(x, "lowpass", cut, 2); return np.tanh(1.5 * x * env_adsr(d, 0.003, 0.12, 0.5, 0.05)) * 0.45


def arp_note(n, d=0.12, cut=3500): x = saw(NOTE(n), d); x = filt(x, "lowpass", cut) * np.exp(-tt(d) * 22); return x * 0.18


def put2(x2, t, g=1.0, bus="mus", verb=0.0):
    t = warp(t); i = int(t * SR); n = min(x2.shape[1], N - i)
    tgt = MUS if bus == "mus" else np.array([L, R])
    if bus == "mus": MUS[:, i:i + n] += g * x2[:, :n]
    else: L[i:i + n] += g * x2[0, :n]; R[i:i + n] += g * x2[1, :n]
    if verb: VERB[:, i:i + n] += verb * g * x2[:, :n]


beats = np.arange(0, 36.0, BEAT)
STOP0, STOP1 = 28.5, 30.0      # release -> silence until the sensing section


def live(t): return not (STOP0 <= t < STOP1)


# ---- intro 0-4: soft pulse, one ping per joint point, shimmer while the lines join, sweep while the figure rises
for b in beats[beats < 4.0]: put(filt(kick(0.55), "lowpass", 380), b)
for i, n in enumerate([81, 84, 86, 88, 91, 93, 96, 98]): put(ping(NOTE(n), 0.5), i * 0.125, 0.32, pan=0.6 * np.sin(i), verb=0.45)
put(riser(1.0, 2000, 9000) * np.hanning(48000), 1.0, 0.35, verb=0.3)
t_ = tt(1.6); f_ = 180 + 160 * (t_ / 1.6) ** 1.2
put(filt(np.sin(2 * np.pi * np.cumsum(f_) / SR), "lowpass", 1500) * np.minimum(1, t_ / 0.15) * np.minimum(1, (1.6 - t_) / 0.2) * 0.12, 2.0, verb=0.3)
put(whoosh(0.4), 3.7, 0.8)
for bar in (0, 1): put2(pad(bar, 0.07, 700), bar * 2.0, verb=0.4)
# ---- problem 4-8: lighter groove, error thuds on the X marks, whoosh at the whip
for b in beats[(beats >= 4) & (beats < 8)]:
    put(kick(0.8), b); put(hat(), b + 0.25, 0.8, pan=0.3)
for bar in (2, 3): put2(pad(bar, 0.08, 1100), bar * 2.0, verb=0.4)
for b in np.arange(4.0, 8.0, 0.25):
    bar = int(b // 2); put(bass_note(ROOT[bar % 4] + (12 if int(b * 4) % 4 == 2 else 0), 0.2, 380), b, 0.8, bus="mus")
put(thud(), 5.5, 1.1); put(thud(), 7.0, 1.1); put(whoosh(0.4), 5.82, 0.9)
# ---- pivot 8-10: breakdown, arp opening, snare roll + riser
put2(pad(4, 0.24, 1900), 8.0, verb=0.5)
for i, b in enumerate(np.arange(8.0, 10.0, 0.125)):
    notes = CH[0]; n = notes[i % 3] + 12 + (12 if i % 6 >= 3 else 0); put(arp_note(n, 0.12, 1200 + 2600 * (b - 8) / 2), b, 1.5, pan=0.4 * np.sin(i), bus="mus", verb=0.25)
for b in np.arange(9.0, 10.0, 0.125 if True else 0.25): put(clap() * (0.25 + 0.6 * (b - 9.0)), b, 0.7, verb=0.2)
put(riser(1.5, 500, 9000), 8.5, 0.8)
# ---- title 10-12: impact, sparse, roll into the drop, gap 11.75-12
put(boom(), 10.0, 1.0, verb=0.4); put(crash(), 10.0, 0.8, verb=0.4); put2(pad(5, 0.12, 2400), 10.0, verb=0.6)
put(kick(), 11.0, 0.9)
for b in np.arange(11.0, 11.75, 0.0625): put(clap() * (0.3 + 0.9 * (b - 11.0)), b, 0.6)
put(riser(1.0, 800, 12000), 10.75, 0.9)
# ---- design block 12-23 (raw clock): one line drawn, more people, 81 strands, design curve, points, rail, link, five candidates
RAW = True
for b in np.arange(12.0, 23.0, BEAT):
    put(kick(0.95 if b >= 14.5 else 0.7), b)
    if int(round(b / BEAT)) % 2 == 1 and b >= 14.5: put(clap(), b, 0.7, verb=0.25)
    put(hat(), b + 0.25, 0.5, pan=-0.2)
    if b >= 16: put(hat(), b + 0.125, 0.35, pan=0.35); put(hat(), b + 0.375, 0.35, pan=0.35)
for b in np.arange(12.0, 23.0, 0.25):
    bar = int(b // 2); n = ROOT[bar % 4] + (12 if int(b * 4) % 4 in (1, 3) else 0); put(bass_note(n, 0.22, 480 if b < 14.5 else 560), b, 0.9, bus="mus")
for t0 in (12.0, 14.0, 16.0, 18.0, 20.0): put2(pad(int(t0 // 2), 0.09, 1800), t0, verb=0.45)
put2(pad(11, 0.09, 1800)[:, : SR], 22.0, verb=0.45)
put(crash(1.2), 12.0, 0.35, verb=0.3)
for j, b in enumerate(np.arange(12.75, 14.2, 0.125)): put(ping(NOTE([81, 84, 86, 88, 91, 93][j % 6] + (12 if j >= 6 else 0)), 0.25), b, 0.16, pan=0.3 * np.sin(j), verb=0.3)   # the dots of the first line
t_ = tt(1.6); put(filt(np.sin(2 * np.pi * np.cumsum(170 + 140 * (t_ / 1.6) ** 1.2) / SR), "lowpass", 1400) * np.hanning(len(t_)) * 0.1, 12.6, verb=0.3)
put(whoosh(0.45), 14.3, 0.7)
for j in range(4): put(ping(NOTE([84, 88, 91, 96][j]), 0.5), 14.55 + j * 0.15, 0.25, pan=[-0.5, 0.5, -0.3, 0.3][j], verb=0.4)
put(riser(0.7, 1500, 10000) * np.hanning(int(0.7 * SR)), 15.3, 0.45, verb=0.4); put(whoosh(0.45), 15.85, 0.7)
put(ping(NOTE(88), 0.9), 16.5, 0.4, verb=0.5); put(ping(NOTE(93), 1.0), 16.9, 0.45, verb=0.5)
put(whoosh(0.4), 17.4, 0.6)
for i in range(5): put(ping(NOTE([84, 86, 88, 91, 93][i]), 0.35), 17.8 + i * 0.03, 0.2, pan=0.5 * np.sin(i * 2), verb=0.3)
t_ = tt(0.65); put(filt(np.sin(2 * np.pi * np.cumsum(220 + 160 * t_) / SR), "lowpass", 1400) * np.hanning(len(t_)) * 0.12, 17.95, verb=0.3)
put(snap(), 18.65, 0.9); put(ping(NOTE(91), 0.8), 18.65, 0.4, verb=0.5); put(snap(), 19.0, 0.9); put(ping(NOTE(86), 0.8), 19.0, 0.4, verb=0.5)
for i in range(5): put(ping(NOTE([81, 84, 88, 91, 93][i]), 0.4), 19.5 + i * 0.25, 0.28, verb=0.3)
for j, b in enumerate((20.5, 21.0, 21.5)):          # each condition: a soft two-note step down as candidates fall back (no buzzers)
    put(ping(NOTE(88 - 2 * j), 0.5), b, 0.3, verb=0.4); put(ping(NOTE(81 - 2 * j), 0.6), b + 0.12, 0.22, verb=0.4)
put(ping(NOTE(93), 1.4), 22.0, 0.6, verb=0.6); put(ping(NOTE(100), 1.4), 22.0, 0.35, verb=0.6)
for b in np.arange(22.5, 22.875, 0.0625): put(clap() * (0.4 + (b - 22.5)), b, 0.5)
put(riser(0.7, 800, 11000), 22.2, 0.6); put(crash(1.5), 23.0, 0.6, verb=0.4)
RAW = False
# ---- main groove 12-36 (cut during the STOP)
RAW = True
LIVE = lambda t: not (37.5 <= t < 39.0)
for b in np.arange(23.0, 43.0, BEAT):
    if not LIVE(b): continue
    put(kick(), b)
    if int(round(b / BEAT)) % 2 == 1: put(clap(), b, 0.8, verb=0.25)
    put(hat(True), b + 0.25, 0.55, pan=-0.2)
    for k in (0.125, 0.375): put(hat(), b + k, 0.45, pan=0.35)
for b in np.arange(23.0, 43.0, 0.25):
    if not LIVE(b): continue
    bar = int(b // 2); n = ROOT[bar % 4] + (12 if int(b * 4) % 4 in (1, 3) else 0); put(bass_note(n, 0.22, 650), b, 1.0, bus="mus")
for bar in range(11, 21):
    t0 = bar * 2.0 + 1.0
    if 37.5 <= t0 < 39.0: continue
    p = pad(bar, 0.10, 2200)
    if t0 < 37.5 < t0 + 2: p[:, int((37.5 - t0) * SR):] = 0
    put2(p, t0, verb=0.45)
for i, b in enumerate(np.arange(23.0, 43.0, 0.125)):
    if not LIVE(b) or (33.0 <= b < 37.5 and i % 2): continue
    bar = int(b // 2); notes = CH[bar % 4]; n = notes[i % 3] + 12 + (12 if (i // 3) % 2 else 0)
    put(arp_note(n, 0.11, 4200), b, 0.75, pan=0.5 * np.sin(i * 0.7), bus="mus", verb=0.2)
RAW = False
# assembly snaps 12.0-15.5, button chime at 16
for b in np.arange(12.0, 16.0, 0.5): put(snap(), b, 0.9, pan=0.3 * np.sin(b * 3), verb=0.15)
put(ping(NOTE(88), 1.2), 16.0, 0.7, verb=0.5); put(ping(NOTE(93), 1.2), 16.0, 0.4, verb=0.5)
# motion 18-24: whoosh in, servo sweep while the seat rises, lock at release
put(whoosh(0.5), 17.6, 1.0)
t = tt(3.2); f = 140 + 90 * np.clip(t / 3.2, 0, 1) ** 0.8
serv = filt(np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sign(np.sin(2 * np.pi * np.cumsum(2 * f) / SR)), "lowpass", 1200) * np.minimum(1, t / 0.2) * np.minimum(1, (3.2 - t) / 0.3) * 0.18
put(serv, 19.35, 1.0)
put(snap(), 22.6, 0.8)
# how-to 24-30: step stamps, grip pulses, STOP brake + silence, heartbeat back in
for b in (24.0, 25.5, 27.0): put(thud(), b, 0.9); put(crash(0.6), b, 0.25)
for b in np.arange(26.0, 28.5, 0.5): put(blip(NOTE(81), 0.08, 0.25), b, verb=0.3)
EXTRA = [(brake() * 1.2, warp(28.5)), (blip(1000, 0.06, 0.25), warp(29.5))]
# sensing 30-33: rising pings per sensor, chord stab at 32
for k, b in enumerate((30.0, 30.5, 31.0, 31.5)): put(ping(NOTE([84, 88, 91, 96][k]), 0.7), b, 0.55, pan=[-0.5, 0.5, 0.3, -0.3][k], verb=0.4)
put(boom(1.0), 30.0, 0.6)
for n in CH[0]: put(arp_note(n + 24, 0.4, 5000) * 2, 32.0, 0.8, verb=0.4)
# end 33-36: riser, final impact, held chord, monitor blips
put(riser(1.0, 600, 10000), 33.0, 0.8)
for b in np.arange(33.5, 34.0, 0.0625): put(clap() * 0.6, b, 0.5)
put(boom(2.5), 34.0, 1.1, verb=0.5); put(crash(2.5), 34.0, 0.9, verb=0.5)
end = pad(0, 0.15, 2600); end2 = pad(0, 0.15, 2600); hold = np.concatenate([end, end2[:, :]], axis=1) * np.linspace(1, 0, end.shape[1] * 2) ** 1.5
put2(hold, 34.0, bus="mix", verb=0.6)
for i, b in enumerate(np.arange(34.5, 36.0, 0.5)): put(ping(NOTE([93, 96, 100][i]), 0.6), b, 0.18, verb=0.5)

# ---- side-chain pump on the music bus (kick on every live beat from 4 s)
pump = np.ones(N); tn = np.arange(N) / SR
KT = [b for b in beats if 4 <= b < 12] + list(np.arange(12.0, 23.0, BEAT)) + [b for b in np.arange(23.0, 45.0, BEAT) if not (37.5 <= b < 39.0)]
for b in KT:
    i = int(b * SR); n = int(0.45 * SR); seg = 1 - 0.65 * np.exp(-np.arange(n) / SR * 9); pump[i:i + n] = np.minimum(pump[i:i + n], seg[: N - i])
L += MUS[0] * pump; R += MUS[1] * pump
# reverb
ir_t = tt(2.4)
for c, tgt in ((0, L), (1, R)):
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.55); ir = filt(ir, "lowpass", 6000); ir /= np.sqrt(np.sum(ir ** 2))
    tgt += signal.fftconvolve(VERB[c], ir)[:N] * 0.35
# master: gentle glue, hard stop for the STOP gap, trim to 36 s
mix = np.stack([L, R])[:, : int(DUR * SR)]
tn = np.arange(mix.shape[1]) / SR
S0, S1 = warp(STOP0), warp(STOP1); gate = 1 - np.clip((tn - (S0 + 0.01)) / 0.03, 0, 1) * np.clip(((S1 - 0.02) - tn) / 0.02, 0, 1)
pk = np.max(np.abs(mix)) + 1e-9; mix = mix * gate / pk
for x, t0 in EXTRA:
    i = int(t0 * SR); mix[:, i:i + len(x)] += 0.55 * x[: mix.shape[1] - i]
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= 10 ** (-1 / 20)
from scipy.io import wavfile
wavfile.write(sys.argv[1] if len(sys.argv) > 1 else "music.wav", SR, (mix.T * 32767).astype(np.int16))
print("ok", mix.shape[1] / SR, "s")
