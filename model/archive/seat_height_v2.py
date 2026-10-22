"""Seat-height sweep v2 (after 2nd audit):
- modes: none, mattress (2 hands, cap 30%), handle in front at 0.80 m (2 hands) with hand cap 10% (balance only) and 30%
- report effort and per-leg hip+knee moment sum; sensitivity of the 0.42->0.60 reduction."""
import json, copy, numpy as np
from model import Subject, STSConfig, sts_effort, sts_geometry
def run(sub, h, mode, cap=0.30, shanks=range(5,31,5), hip_above=0.09):
    best=None
    for st in shanks:
        c=STSConfig(bed_h=h,shank_tilt_deg=st,trunk_grid=tuple(range(0,81,5)),hand_cap=cap,hip_above_seat=hip_above)
        try: g=sts_geometry(sub,c)
        except ValueError: continue
        if mode=="none": d=sts_effort(sub,c,None,return_detail=True)
        elif mode=="mattress": d=sts_effort(sub,c,np.array([g["Hp"][0]-0.05,h+0.02]),2,0.22,return_detail=True)
        else: d=sts_effort(sub,c,np.array([g["edge_x"]+0.42,0.80]),2,0.0,return_detail=True)
        if d and (best is None or d["effort"]<best["effort"]):
            ju=d["joint_use"]; best=dict(effort=float(d["effort"]),trunk=d["trunk_deg"],shank=st,
              knee=max(ju["knee"],0)*sub.knee_ext/sub.M, hip=max(ju["hip"],0)*sub.hip_ext/sub.M, hand=float(d["hand_load_pct_BW"]))
    return best
sub=Subject()
H=np.round(np.arange(0.40,0.661,0.02),3)
out={}
for key,mode,cap in [("none","none",0.3),("mattress","mattress",0.3),("handle10","handle",0.10),("handle30","handle",0.30)]:
    rows=[]
    for h in H:
        d=run(sub,h,mode,cap)
        rows.append(None if d is None else dict(h=float(h),effort=round(d["effort"],3),knee=round(d["knee"],3),hip=round(d["hip"],3),trunk=d["trunk"],shank=d["shank"],hand=round(d["hand"],1)))
    out[key]=rows; print(key,[r and r["effort"] for r in rows])
# sensitivity of sum reduction 0.42 -> 0.60 (no hands)
def sumred(**kw):
    s=kw.pop("sub",sub); a=run(s,0.42,"none",**kw); b=run(s,0.60,"none",**kw)
    return round((b["knee"]+b["hip"])/(a["knee"]+a["hip"])-1,3)
big=copy.deepcopy(sub); big.M=75; big.H=1.72
for k in ["knee_ext","knee_flex","hip_ext","hip_flex","sh_flex","sh_ext","el_flex","el_ext"]: setattr(big,k,getattr(sub,k)*75/60)
sens={"published(shank<=30)":sumred(),"shank fixed 15":sumred(shanks=[15]),"shank<=45":sumred(shanks=range(5,46,5)),
      "hip_above 0.06":sumred(hip_above=0.06),"hip_above 0.12":sumred(hip_above=0.12),"75kg 1.72m":sumred(sub=big)}
print(sens); out["sens_sum_reduction_042_060"]=sens
json.dump(out,open("seat_height_v2.json","w"),indent=1)
