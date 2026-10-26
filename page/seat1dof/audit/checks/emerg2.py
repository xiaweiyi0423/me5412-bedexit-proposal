import sys, json, numpy as np; sys.path.insert(0,'/home/user/me5412-bedexit-proposal/model/calc_v13')
import seat_1dof_fourbar2 as FB2
from seat_trajectory import rot, Seat
import seat_trajectory as ST
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS, ukey, path_of, track_user, PAD_AMAX
from seat_relative_motion import rise, curve_fit, track
from multiprocessing import Pool
from model import G
L=json.load(open('seat_1dof/layout.json')); x=np.array(L['x'])
s=[p[:5] for p in FB2.run(x,n=700)]; cv=with_prefix(np.array([f[0] for f in s]),np.array([f[1] for f in s]))
# (B) passive tilt latch at the seat front: contact positions (seat frame x) during normal support, all users
def job(u):
    ST.A_MAX=PAD_AMAX; sub,path=path_of(u); rows=track(sub,path,Seat(r_e=0.03),cv)
    return [ (r['seat_x'], r['phi']) for r in rows if r.get('contact') and r.get('ok')]
with Pool() as p: XS=p.map(job,USERS)
xs=np.concatenate([[a for a,_ in v] for v in XS]); print('normal contact seat-x (m): min %.3f p5 %.3f med %.3f max %.3f'%(xs.min(),np.percentile(xs,5),np.median(xs),xs.max()))
for xp in (0.06,0.075,0.085):
    norm=0.6*100*G*max(0,xp-xs.min())           # worst normal: 100 kg user, 0.6 BW, most rearward contact
    sit=[0.8*45*G*(xp-xl) for xl in (-0.04,0.0,0.03)]   # weakest sit-back: 45 kg user landing at 0.8 BW
    print(f'pivot x {xp}: normal use max {norm:.0f} N·m ; sit-back (45 kg, 0.8 BW) at x -4/0/+3 cm: '+' / '.join(f'{v:.0f}' for v in sit)+' N·m')
# (C) design curve with a lower tilt cap: ideal curve (fitted to the same reference user), 81 users
ref=(1.50,0.33,0.6,0.09)
_,rp=rise(1.50,0.33,0.6,r_b=0.09)
def jobC(args):
    u,cap=args; c=curve_fit(rp,cap); return cap, track_user((u,c,PAD_AMAX,dict(r_e=0.03)))[1]
with Pool() as p: RC=p.map(jobC,[(u,c) for c in (12,15,20,30) for u in USERS])
ok=lambda q: bool(q.get('release_hz') and q['fwd_slip_max_cm']<=2 and q['min_catch_cm']>=0)
for cap in (12,15,20,30):
    rs=[q for c,q in RC if c==cap]
    print(f'tilt cap {cap}: ok {sum(ok(q) for q in rs)}/81  fwd max {max(q["fwd_slip_max_cm"] for q in rs)}  catch min {min(q["min_catch_cm"] for q in rs)}  E med {np.median([q["E0_release"] for q in rs]):.3f} max {max(q["E0_release"] for q in rs)}  phi@release max {max(q["phi_release"] for q in rs)}')
