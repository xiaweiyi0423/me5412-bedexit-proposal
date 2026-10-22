"""v11: as-drawn geometry + raised-bed baselines (after audit 4).
Baselines: low bed 0.42 + mattress push; raised bed (risers) 0.55 / 0.58 + mattress push; raised bed + bed handle (best of
grips 0.35-0.70 ahead of hip, +0.25-0.45 above seat, same grid as before).
Station B: bar fixed relative to seat (dx ahead of hip, dz above seat) as it would be built; seat 0.60 / 0.64 / 0.66."""
import json, sys, numpy as np
from multiprocessing import Pool
from model import Subject, STSConfig, sts_effort, sts_geometry, sts_collides
SH=list(range(-10,31,5)); XS=[0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70]; DZS=[0.25,0.30,0.35,0.40,0.45]
PROX={"P1 cap25":(1.0,0.25),"P2 arm x0.5":(0.5,0.30),"P3 arm x0.35":(0.35,0.30),"strong cap30":(1.0,0.30)}
def subj(f):
    s=Subject()
    for k in ["sh_flex","sh_ext","el_flex","el_ext"]: setattr(s,k,getattr(Subject(),k)*f)
    return s
def best(a):
    f,cap,h,mode,heel,fixed=a; sub=subj(f); out=None
    for st in SH:
        try: g=sts_geometry(sub,STSConfig(bed_h=h,shank_tilt_deg=st))
        except ValueError: continue
        if g["heel"]-g["Hp"][0]<heel: continue
        c=STSConfig(bed_h=h,shank_tilt_deg=st,trunk_grid=tuple(range(0,81,5)),hand_cap=cap)
        if mode=="none": C=[(None,2,0.0)]
        elif mode=="mattress": C=[(np.array([g["Hp"][0]-0.05,h+0.02]),2,0.22)]
        elif mode=="fixed": C=[(np.array([g["Hp"][0]+fixed[0],h+fixed[1]]),2,0.0)]
        else: C=[(np.array([g["Hp"][0]+dx,h+dz]),2,0.0) for dx in XS for dz in DZS]
        for P,n,lat in C:
            if P is not None and mode!="mattress" and sts_collides(sub,c,P): continue
            d=sts_effort(sub,c,P,n,lat,return_detail=True)
            if d and (out is None or d["effort"]<out["effort"]):
                out=dict(effort=round(float(d["effort"]),3),shank=st,trunk=d["trunk_deg"],hand=round(float(d["hand_load_pct_BW"]),1))
    return out
if __name__=="__main__":
    designs={"bed042_mattress":(0.42,"mattress",0.10,None),"bed055_mattress":(0.55,"mattress",0.10,None),"bed058_mattress":(0.58,"mattress",0.10,None),
             "bed055_handle":(0.55,"handle",0.10,None),"bed058_handle":(0.58,"handle",0.10,None),"A042_drawn":(0.42,"fixed",0.10,(0.54,0.38))}
    for h in [0.60,0.64,0.66]:
        for dx in [0.50,0.55,0.60]:
            for dz in [0.35,0.40]:
                designs[f"B{int(h*100)}_x{int(dx*100)}_z{int(dz*100)}"]=(h,"fixed",0.08,(dx,dz))
    jobs=[];keys=[]
    for pn,(f,cap) in PROX.items():
        for dn,(h,m,heel,fx) in designs.items(): jobs.append((f,cap,h,m,heel,fx)); keys.append((pn,dn))
    for h in [0.42,0.55,0.58,0.60,0.64,0.66]:
        jobs.append((1.0,0.3,h,"none",0.10 if h<0.6 else 0.08,None)); keys.append(("none",f"none{int(h*100)}"))
    with Pool() as p: R=p.map(best,jobs)
    out={}
    for (pn,dn),r in zip(keys,R): out.setdefault(pn,{})[dn]=r
    json.dump(out,open("compare_v11.json","w"),indent=1)
    for pn in out:
        print(pn,{k:(v["effort"] if v else None) for k,v in out[pn].items()})
