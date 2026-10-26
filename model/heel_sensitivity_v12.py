"""v12: sensitivity of the station result to the heel-clearance constraint.
compare_v11 lets the station place the heel 0.08 m ahead of the hip (short seat plate, slim column) but uses 0.10 m for beds.
Here the station is re-run with the bed's 0.10 m, so the comparison uses the same foot-space assumption on both sides."""
import json
from multiprocessing import Pool
from compare_v11 import best, PROX
if __name__=="__main__":
    d=json.load(open("compare_v11.json"))
    jobs=[(f,cap,0.66,"fixed",0.10,(0.55,0.40)) for pn,(f,cap) in PROX.items()]+[(1.0,0.3,0.66,"none",0.10,None)]
    with Pool() as p: R=p.map(best,jobs)
    out={"note":"station B66_x55_z40 with heel >= hip + 0.10 m (same as beds); compare_v11 used 0.08 m for the station"}
    for (pn,_),r in zip(PROX.items(),R):
        v=d[pn]; ra=min(v["bed058_mattress"]["effort"],v["bed058_handle"]["effort"]); lo=v["bed042_mattress"]["effort"]
        out[pn]=dict(B66_heel010=r,B66_heel008=v["B66_x55_z40"]["effort"],raised_bed=ra,low_bed=lo,
                     vs_raised_heel010=round(r["effort"]/ra-1,3),vs_raised_heel008=round(v["B66_x55_z40"]["effort"]/ra-1,3),
                     vs_low_heel010=round(r["effort"]/lo-1,3),vs_low_heel008=round(v["B66_x55_z40"]["effort"]/lo-1,3))
    n=d["none"]
    out["none"]=dict(none66_heel010=R[-1],none66_heel008=n["none66"]["effort"],none58=n["none57"]["effort"],
                     vs_058_heel010=round(R[-1]["effort"]/n["none57"]["effort"]-1,3),vs_058_heel008=round(n["none66"]["effort"]/n["none57"]["effort"]-1,3),
                     note="key none57 in compare_v11.json is the 0.58 m bed (int(0.58*100)=57)")
    json.dump(out,open("heel_sensitivity_v12.json","w"),indent=1)
    for k,v in out.items(): print(k,v)
