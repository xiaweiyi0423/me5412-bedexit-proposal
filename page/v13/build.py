"""Build the v13 proposal page: inject model and simulation results into template.html -> ../bedexit_proposal_v13.html"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
ss = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_support.json")))
cs = json.load(open(os.path.join(ROOT, "model/calc_v13/controller_v13.json")))
hs = sorted(ss["start"]["P1 cap25"]["heel08"], key=float)
eff = dict(h=[float(h) for h in hs], seatoff={}, start50={}, startcaps={}, minseat={}, cgrid=None,
           raised={"P1": 0.291, "P2": 0.303}, low={"P1": 0.389, "P2": 0.357})
for key, arm in (("P1", "P1 cap25"), ("P2", "P2 arm x0.5")):
    st = ss["start"][arm]["heel08"]
    eff["seatoff"][key] = [st[h]["0.0"]["effort"] for h in hs]
    eff["start50"][key] = [st[h]["0.5"]["effort"] for h in hs]
    eff["startcaps"][key] = {c: st["0.42"][c]["effort"] for c in ("0.3", "0.4", "0.5", "0.6")}
    ms = ss["min_seat"][arm]; cg = sorted(ms["0.42"], key=float); eff["cgrid"] = [float(c) for c in cg]
    eff["minseat"][key] = [[(ms[h][c]["Fs_BW"] if ms[h][c] else 1.0) for c in cg] for h in hs]
SN = ["IDLE", "SEATED", "LIFTING", "STOPPED", "STANDING_HOLD", "LOWERING", "EMPTY_HOLD", "EMPTY_MOVE", "RESET_EMPTY", "LOCKED"]
sims = []
for s in cs["scenarios"]:
    se = s["series"]
    sims.append(dict(key=s["key"], name=s["name"], rules=s["rules"], final=s["final_state"], fh=s["final_height"],
                     so=s["seat_off_height"], t=se["t"], h=se["h"], seat=se["seat"], st=[SN.index(x) for x in se["state"]]))
data = dict(eff=eff, sims=sims, states=SN)
tpl = open(os.path.join(HERE, "template.html")).read()
out = tpl.replace("/*__DATA__*/{}", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
open(os.path.join(ROOT, "page/bedexit_proposal_v13.html"), "w").write(out)
print(len(out), "bytes")
