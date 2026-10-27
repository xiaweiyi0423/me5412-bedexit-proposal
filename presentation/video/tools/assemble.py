"""Assemble the concept video from scene clips, narration and music.
Usage: python3 assemble.py edit.json out.mp4
edit.json: {"fade": 0.5, "scenes": [{"id": "S1", "file": "...", "start": 0.0, "dur": 5.0, "tag": "AI 生成概念画面",
            "narr": "audio/N1.wav" | null, "narr_at": 0.4, "sub": "...", "speed": 1.0}], "music": "audio/music.wav",
            "music_db": -14, "duck": true}
Each scene: cut [start, start + dur*speed] from its file, retime by 1/speed, scale to 1920x1080 @30 fps, pad the end by
cloning the last frame if the clip is short, tag in the bottom-right corner. Scenes join with crossfades; narration is
placed at scene start + narr_at; subtitles are burned from an ASS file; music is ducked under the voice.
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "WenQuanYi Zen Hei"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print(" ".join(cmd)); print(r.stderr[-3000:]); sys.exit(1)
    return r.stdout


def dur_of(f):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).strip())


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def main(cfg_path, out):
    C = json.load(open(cfg_path)); T = C.get("fade", 0.5); tmp = os.path.join(HERE, "build"); os.makedirs(tmp, exist_ok=True)
    seg = []
    for i, s in enumerate(C["scenes"]):
        src = os.path.join(HERE, s["file"]); sp = s.get("speed", 1.0); d = s["dur"]; st = s.get("start", 0.0)
        avail = (dur_of(src) - st) / sp; pad = max(0.0, d - avail + 0.05)
        tag = s.get("tag")
        vf = [f"trim=start={st}:duration={d * sp + 0.2}", "setpts=PTS-STARTPTS", f"setpts=PTS/{sp}" if sp != 1 else "null",
              "scale=1920:1080:flags=lanczos", "setsar=1", "fps=30"]
        if pad > 0: vf.append(f"tpad=stop_mode=clone:stop_duration={pad:.2f}")
        vf.append(f"trim=duration={d}")
        if s.get("grade"): vf.append(s["grade"])
        if tag:
            vf.append(f"drawtext=font='{FONT}':text='{tag}':fontsize=26:fontcolor=white@0.78:box=1:boxcolor=black@0.35:boxborderw=10:x=w-tw-44:y=h-th-40")
        vf.append("format=yuv420p")
        o = os.path.join(tmp, f"{i:02d}_{s['id']}.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", "30", o])
        seg.append((o, d))
    # crossfade chain; scene i starts at t_i
    starts = [0.0]
    for k in range(1, len(seg)): starts.append(starts[-1] + seg[k - 1][1] - T)
    total = starts[-1] + seg[-1][1]
    inputs = sum((["-i", o] for o, _ in seg), [])
    fc = []; last = "[0:v]"
    for k in range(1, len(seg)):
        tr = C["scenes"][k].get("transition", "fade")
        fc.append(f"{last}[{k}:v]xfade=transition={tr}:duration={T}:offset={starts[k]:.3f}[v{k}]"); last = f"[v{k}]"
    # subtitles
    ass = os.path.join(tmp, "subs.ass")
    with open(ass, "w") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n[V4+ Styles]\n"
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                f"Style: Sub,{FONT},50,&H00FFFFFF,&H00FFFFFF,&H64000000,&H78000000,0,0,0,0,100,100,1,0,1,2.2,1.2,2,120,120,64,1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for s, t0 in zip(C["scenes"], starts):
            for k in ("", "2"):
                if not s.get("sub" + k): continue
                a = t0 + s.get(f"narr{k}_at", 0.4); nd = dur_of(os.path.join(HERE, s["narr" + k])) if s.get("narr" + k) else 2.5
                f.write(f"Dialogue: 0,{ts(a)},{ts(a + nd + 0.35)},Sub,,0,0,0,,{{\\fad(150,200)}}{s['sub' + k]}\n")
    fc.append(f"{last}ass={ass}[vout]")
    # audio: narration lines + ducked music
    ain = []; amix = []; n_in = len(seg)
    for s, t0 in zip(C["scenes"], starts):
        for k in ("", "2"):
            if s.get("narr" + k):
                ain += ["-i", os.path.join(HERE, s["narr" + k])]; ms = int((t0 + s.get(f"narr{k}_at", 0.4)) * 1000)
                fc.append(f"[{n_in}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[n{n_in}]"); amix.append(f"[n{n_in}]"); n_in += 1
    fc.append(f"{''.join(amix)}amix=inputs={len(amix)}:normalize=0,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[voice]")
    # sound effects (scene-relative times), mixed under the voice but not ducked
    sfx = []
    for s, t0 in zip(C["scenes"], starts):
        for e in s.get("sfx", []):
            ain += ["-i", os.path.join(HERE, e["file"])]; ms = int((t0 + e["at"]) * 1000); d_ = e.get("dur")
            tr = f"atrim=0:{d_},afade=t=out:st={max(0, d_ - 0.4)}:d=0.4," if d_ else ""
            fc.append(f"[{n_in}:a]aformat=sample_rates=48000:channel_layouts=stereo,{tr}volume={e.get('db', -12)}dB,adelay={ms}|{ms}[x{n_in}]"); sfx.append(f"[x{n_in}]"); n_in += 1
    if sfx:
        fc.append(f"{''.join(sfx)}amix=inputs={len(sfx)}:normalize=0,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[sfxbus]")
    if C.get("music"):
        ain += ["-i", os.path.join(HERE, C["music"])]; mi = n_in; n_in += 1
        fc.append(f"[{mi}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{total:.3f},apad=whole_dur={total:.3f},"
                  f"afade=t=in:d=1.5,afade=t=out:st={total - 3:.3f}:d=3,volume={C.get('music_db', -14)}dB[mus]")
        if C.get("duck", True):
            fc.append("[voice]asplit[vo1][vo2]")
            fc.append("[mus][vo2]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600[mduck]")
            fc.append(f"[vo1][mduck]{'[sfxbus]' if sfx else ''}amix=inputs={3 if sfx else 2}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
        else:
            fc.append("[voice][mus]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    else:
        fc.append("[voice]loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, *ain, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", out])
    print(f"wrote {out}: {total:.1f} s; scene starts:", ", ".join(f"{s['id']} {t:.1f}" for s, t in zip(C["scenes"], starts)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
