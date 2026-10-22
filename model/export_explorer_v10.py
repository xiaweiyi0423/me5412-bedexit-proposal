"""Explorer data for scheme A (bed 0.42 m), consistent with comparison numbers:
trunk 0-80 deg, shank 5-30 deg optimised, v10: strong = full arm strength, weak = shoulder/elbow strength x0.5; both with 30% hand cap."""
import json, numpy as np
from multiprocessing import Pool
from model import Subject, STSConfig, sts_effort, sts_geometry, sts_collides
sub=Subject(); BED=0.42; SHANKS=list(range(5,31,5))
def cfg(st,cap): return STSConfig(bed_h=BED,shank_tilt_deg=st,trunk_grid=tuple(range(0,81,5)),hand_cap=cap)
GEO={st:sts_geometry(sub,cfg(st,0.3)) for st in SHANKS}
r3=lambda v: round(float(v),3)
def pack(d,st):
    ju=d["joint_use"];g=GEO[st];e=g["edge_x"]
    return [r3(d["effort"]),int(d["trunk_deg"]),r3(d["elbow"][0]-e),r3(d["elbow"][1]),round(float(d["Fx"])),round(float(d["Fz"])),
            r3(ju["hip"]),r3(ju["knee"]),r3(ju["shoulder"]),r3(ju["elbow"]),st]
def subj(f):
    s=Subject()
    for k in ["sh_flex","sh_ext","el_flex","el_ext"]: setattr(s,k,getattr(Subject(),k)*f)
    return s
def cell(args):
    xr,z,cap,n,lat,f=args; best=None; sb=subj(f)
    for st in SHANKS:
        c=cfg(st,cap); P=np.array([GEO[st]["edge_x"]+xr,z])
        if n==2 and lat==0 and sts_collides(sub,c,P): continue
        d=sts_effort(sb,c,P,n,lat,return_detail=True)
        if d and (best is None or d["effort"]<best[0]): best=(d["effort"],pack(d,st))
    return None if best is None else best[1]
if __name__=="__main__":
    xs=np.round(np.arange(-0.30,0.901,0.05),3); zs=np.round(np.arange(0.40,1.301,0.05),3)
    hs=np.round(np.arange(0.55,1.201,0.025),3)
    out={"xs":xs.tolist(),"zs":zs.tolist(),"side_h":hs.tolist(),"BW":round(sub.M*9.81),
         "geo":{str(st):{k:(r3(v) if np.isscalar(v) else [r3(x) for x in v]) for k,v in GEO[st].items()} for st in SHANKS},
         "L":{"tr":r3(sub.L_trunk)}}
    with Pool() as pool:
        for cap,key,f in [(0.30,"strong",1.0),(0.30,"weak",0.5)]:
            jobs=[(float(x),float(z),cap,2,0.0,f) for z in zs for x in xs]
            res=pool.map(cell,jobs); out["front_"+key]=[res[i*len(xs):(i+1)*len(xs)] for i in range(len(zs))]
            for n in (1,2):
                out[f"side{n}_{key}"]=pool.map(cell,[(0.03,float(h),cap,n,0.22,f) for h in hs])
            print(key,"done",flush=True)
    c=json.load(open("compare_v10.json")); out["ref"]={"none_042":c["none"]["0.42"]["effort"],"strong":{"mattress_042":c["proxies"]["strong cap30"]["mattress_rigid"]["effort"]},"weak":{"mattress_042":c["proxies"]["P2 arm x0.5"]["mattress_rigid"]["effort"]}}
    json.dump(out,open("explorer_v10.json","w"),separators=(",",":"))
    print("bytes",len(json.dumps(out)))
