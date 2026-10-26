import sys, json, numpy as np; sys.path.insert(0,'/home/user/me5412-bedexit-proposal/model/calc_v13')
import seat_1dof_layout as LYm, seat_1dof_fourbar2 as FB2
from seat_trajectory import rot, Seat, body_points
import seat_trajectory as ST
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS, ukey, path_of, PAD_AMAX
from seat_relative_motion import track
from multiprocessing import Pool
from model import G
L=json.load(open('seat_1dof/layout.json')); x=np.array(L['x']); act=L['mech']['act']; A,B=x[:2],x[2:4]
s=[p[:5] for p in FB2.run(x,n=700)]
z=np.array([f[0][1] for f in s]); ph=np.array([f[1] for f in s])
Lact=np.array([np.hypot(*(LYm.act_parts(f,act,A,B)[2]-np.array(act['D']))) for f in s])
print('tilt along the path (seat centre z -> tilt, actuator length):')
for zz in (0.42,0.46,0.50,0.54,0.56,0.58,0.60,0.62,0.63,0.64,0.65,0.66):
    i=int(np.argmin(abs(z-zz))); print(f'  z {zz:.2f}  tilt {ph[i]:5.1f}  act L {Lact[i]*1000:5.0f} mm')
cv=with_prefix(np.array([f[0] for f in s]),ph); npre=len(cv[0])-len(s)
def job(u):
    ST.A_MAX=PAD_AMAX; sub,path=path_of(u); rows=track(sub,path,Seat(r_e=0.03),cv)
    good=[r for r in rows if r.get('contact') and r.get('ok')]; last=good[-1]; i=min(max(int(last['k'])-npre,0),len(s)-1)
    # 'shadow' mode: after release, the seat may only move up as far as it stays clear of the buttock; how far by the time the user stands?
    pz_end=path[-1]; pts,kind,aa=body_points(pz_end)
    j_ok=i
    for j in range(i,len(s)):
        Q,phi=s[j][0],s[j][1]; loc=(pts-Q)@rot(phi); seat=Seat(r_e=0.03)
        inside=(loc[:,0]>=-seat.h)&(loc[:,0]<=seat.h); gap=np.where(inside,loc[:,1]-seat.top(loc[:,0]),np.inf).min()
        if gap<0.01: break
        j_ok=j
    return ukey(u), dict(z_rel=round(float(z[i]),3), tilt_rel=round(float(ph[i]),1), z_shadow=round(float(z[j_ok]),3), tilt_shadow=round(float(ph[j_ok]),1),
                        dL_to_shadow_mm=round(1000*float(Lact[j_ok]-Lact[i]),0), dL_down_to_start_mm=round(1000*float(Lact[i]-Lact[0]),0))
with Pool() as p: R=dict(p.map(job,USERS))
tr=np.array([v['tilt_rel'] for v in R.values()]); ts=np.array([v['tilt_shadow'] for v in R.values()])
print('release tilt  med %.1f  max %.1f  n>20 %d' % (np.median(tr),tr.max(),(tr>20).sum()))
print('after shadowing to standing: tilt med %.1f max %.1f n>15 %d n>10 %d' % (np.median(ts),ts.max(),(ts>15).sum(),(ts>10).sum()))
dl=np.array([v['dL_to_shadow_mm'] for v in R.values()]); print('extra actuator travel to shadow pose mm: med %.0f max %.0f -> at 20 mm/s: med %.1f s max %.1f s'%(np.median(dl),dl.max(),np.median(dl)/20,dl.max()/20))
dd=np.array([v['dL_down_to_start_mm'] for v in R.values()]); print('collapse back to start, actuator shortening mm: med %.0f max %.0f'%(np.median(dd),dd.max()))
# generalized force when the actuator is released: does the seat go down under a vertical load at the seat, everywhere?
sign=[]
for i in range(1,len(s)-1,10):
    dz=(s[i+1][0][1]-s[i-1][0][1]); sign.append(dz>0)
print('seat centre rises monotonically along the path (so a released actuator lets the seat sink back):', all(sign))
# descent: tilt change while sinking from each release pose
worst_up=0
for v in R.values():
    i=int(np.argmin(abs(z-v['z_rel']))); worst_up=max(worst_up, ph[:i+1].max()-ph[i])
print('max tilt increase while sinking from a release pose:', round(worst_up,1),'deg')
json.dump(R,open('/home/user/me5412-bedexit-proposal/page/seat1dof/audit/checks/emergency.json','w'))
