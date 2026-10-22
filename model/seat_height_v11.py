"""Seat-height sweep v10: feet limited by what is under the seat (heel >= hip + 0.08 m),
grip on a front bar whose position is optimised (0.35-0.70 m ahead of hip, 0.25-0.45 m above seat).
Series: none; bar with hand cap 25% (P1); bar with shoulder/elbow x0.5, cap 30% (P2)."""
import json, copy, numpy as np
from multiprocessing import Pool
from model import Subject, STSConfig, sts_effort, sts_geometry, sts_collides
SHANKS=list(range(-10,31,5)); XS=[0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70]; DZS=[0.25,0.30,0.35,0.40,0.45]
def subj(f=1.0,big=False):
    s=Subject()
    if big:
        s.M=75; s.H=1.72
        for k in ["knee_ext","knee_flex","hip_ext","hip_flex","sh_flex","sh_ext","el_flex","el_ext"]: setattr(s,k,getattr(Subject(),k)*75/60)
    for k in ["sh_flex","sh_ext","el_flex","el_ext"]: setattr(s,k,getattr(s,k)*f)
    return s
def run(args):
    h,mode,cap,f,heel_min,hip_above,big,shank_max=args; sub=subj(f,big); best=None
    for st in SHANKS:
        if st>shank_max: continue
        c=STSConfig(bed_h=h,shank_tilt_deg=st,trunk_grid=tuple(range(0,81,5)),hand_cap=cap,hip_above_seat=hip_above)
        try: g=sts_geometry(sub,c)
        except ValueError: continue
        if g["heel"]-g["Hp"][0]<heel_min: continue
        Ps=[None] if mode=="none" else [np.array([g["Hp"][0]+0.55,h+0.40])]
        for P in Ps:
            if P is not None and sts_collides(sub,c,P): continue
            d=sts_effort(sub,c,P,2,0.0,return_detail=True)
            if d and (best is None or d["effort"]<best["effort"]):
                ju=d["joint_use"]; best=dict(h=float(h),effort=round(float(d["effort"]),3),trunk=d["trunk_deg"],shank=st,
                  knee=round(max(ju["knee"],0)*sub.knee_ext/sub.M,3),hip=round(max(ju["hip"],0)*sub.hip_ext/sub.M,3),hand=round(float(d["hand_load_pct_BW"]),1))
    return best
if __name__=="__main__":
    H=[round(float(x),2) for x in np.arange(0.40,0.701,0.02)]
    series=[("none","none",0.3,1.0),("bar25","bar",0.25,1.0),("barweak","bar",0.30,0.5)]
    jobs=[(h,m,cap,f,0.08,0.09,False,30) for _,m,cap,f in series for h in H]
    with Pool() as pool: res=pool.map(run,jobs)
    out={}
    for i,(k,_,_,_) in enumerate(series):
        out[k]=res[i*len(H):(i+1)*len(H)]; print(k,[r and r["effort"] for r in out[k]])
    def sumred(heel=0.08,hip_above=0.09,big=False,shank_max=30):
        a=run((0.42,"none",0.3,1.0,heel,hip_above,big,shank_max)); b=run((0.66,"none",0.3,1.0,heel,hip_above,big,shank_max))
        if a is None or b is None: return dict(note="infeasible at 0.42" if a is None else "infeasible at 0.60", b=b and b["effort"])
        return dict(sum=round((b["knee"]+b["hip"])/(a["knee"]+a["hip"])-1,3),eff=round(b["effort"]/a["effort"]-1,3),ratio=round((a["knee"]+a["hip"])/(b["knee"]+b["hip"]),2))
    sens={"base":sumred(),"heel unconstrained":sumred(heel=-1),"feet not tucked (shank<=10)":sumred(heel=-1,shank_max=10),
          "hip_above 0.06":sumred(hip_above=0.06),"hip_above 0.12":sumred(hip_above=0.12),"75kg 1.72m":sumred(big=True)}
    print(sens); out["sens"]=sens
    json.dump(out,open("seat_height_v11.json","w"),indent=1)
