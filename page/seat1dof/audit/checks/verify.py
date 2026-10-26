import sys, json, numpy as np; sys.path.insert(0,'/home/user/me5412-bedexit-proposal/model/calc_v13')
import seat_1dof_layout as LYm, seat_1dof_fourbar2 as FB2
from seat_trajectory import rot, effort, bar_at, Seat
import seat_trajectory as ST
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS, ukey, path_of, track_user, PAD_AMAX
from seat_relative_motion import curve_vertical, track
from multiprocessing import Pool
from model import G
L=json.load(open('seat_1dof/layout.json')); x=np.array(L['x']); act=L['mech']['act']
A,B,c1,c2=x[:2],x[2:4],x[4:6],x[6:8]
s=[p[:5] for p in FB2.run(x,n=700)]
cv=with_prefix(np.array([p[0] for p in s]),np.array([p[1] for p in s])); npre=len(cv[0])-len(s)
out={}
# (b) cross tube vs rocker A segment and post A, sagittal
dmin=9;where=None
for f in s:
    (D,H,rh),(H2,E,rr),Ept=LYm.act_parts(f,act,A,B)
    d=LYm.cap_d(np.atleast_2d(Ept),A,f[2],0)[0]-LYm.R_TUBE-LYm.R_ROCK
    if d<dmin:dmin,where=d,round(float(f[0][1]),3)
out['tube_vs_rockerA_cm']=(round(100*dmin,1),where)
# (c,d) actuator force and pin forces with load offsets; statics of coupler + rockers (two-force members except driven rocker B)
def statics(f,f_next,f_prev,Fs,xoff):
    Q,phi,P1,P2=f[0],f[1],f[2],f[3]; n_=rot(phi)@np.array([0,1.0]); Cpt=Q+rot(phi)@np.array([xoff,0]); F=-Fs*n_+np.array([0,-10*G])
    # virtual work incl. rotation: dW = F.dC  (C moves with seat: dC = dQ + dphi x r)
    Cn=f_next[0]+rot(f_next[1])@np.array([xoff,0]); Cp=f_prev[0]+rot(f_prev[1])@np.array([xoff,0])
    Ln=np.hypot(*(LYm.act_parts(f_next,act,A,B)[2]-np.array(act['D']))); Lp=np.hypot(*(LYm.act_parts(f_prev,act,A,B)[2]-np.array(act['D'])))
    Fa=-(F@(Cn-Cp))/(Ln-Lp)
    # pin forces: coupler (seat) equilibrium with rocker A two-force (along A->P1) and rocker B force R2 (2 comps) -> moments about P2
    uA=(P1-A)/np.hypot(*(P1-A)); m=lambda r,v: r[0]*v[1]-r[1]*v[0]
    fA=-m(Cpt-P2,F)/m(P1-P2,uA); R2=-(F+fA*uA)
    return Fa, abs(fA), float(np.hypot(*R2))
for xoff in (-0.06,0.0,0.06,0.085):
    res=[statics(s[i],s[i+1],s[i-1],1.5*100*G,xoff) for i in range(1,len(s)-1,5)]
    Fa=[r[0] for r in res]; out[f'hold100_xoff{xoff}']=dict(Fa_N=(round(min(Fa)),round(max(Fa))), pinP1_max=round(max(r[1] for r in res)), pinP2_max=round(max(r[2] for r in res)))
    res=[statics(s[i],s[i+1],s[i-1],0.5*60*G,xoff) for i in range(1,len(s)-1,5)]
    out[f'lift60_xoff{xoff}']=dict(Fa_N=(round(min(r[0] for r in res)),round(max(r[0] for r in res))))
# tilt at release / stop pose for 81 users
def job(u):
    ST.A_MAX=PAD_AMAX; sub,path=path_of(u); rows=track(sub,path,Seat(r_e=0.03),cv)
    good=[r for r in rows if r.get('contact') and r.get('ok')]
    sl=np.array([r['slip'] for r in good]); dd=np.maximum.accumulate(sl) if len(sl) else sl
    drawup=float(max([sl[j]-sl[:j+1].min() for j in range(len(sl))]+[0])); total=float(np.abs(np.diff(sl)).sum()) if len(sl)>1 else 0
    # supported-phase effort with actual contact
    worst=0
    for r,pz in list(zip(rows,path))[:len(good)][::3]:
        C=np.array(r['P']); kk=min(int(r['k']),len(cv[1])-1); n=rot(cv[2][kk])@np.array([0,1.0])
        e=effort(sub,pz,bar_at(pz['Hp'][1]),(C,n,r['pelvis']))
        worst=max(worst,e[0] if e else 9)
    # required actuator length change per hip rise
    ks=[int(r['k']) for r in good]; hz=[r['hz'] for r in good]
    Ls=[np.hypot(*(LYm.act_parts(s[min(max(k-npre,0),len(s)-1)],act,A,B)[2]-np.array(act['D']))) for k in ks]
    rate=max([abs(Ls[i+1]-Ls[i])/max(hz[i+1]-hz[i],1e-6) for i in range(len(Ls)-1)]+[0])
    return ukey(u), dict(phi_release=good[-1]['phi'] if good else None, drawup_cm=round(100*drawup,1), total_shear_cm=round(100*total,1), supported_effort_max=round(worst,3), dL_dhz_max=round(rate,2))
with Pool() as p: R=dict(p.map(job,USERS))
ph=[v['phi_release'] for v in R.values()]
out['phi_at_release']=dict(min=round(min(ph),1),med=round(float(np.median(ph)),1),max=round(max(ph),1),n_over_20=sum(p_>20 for p_ in ph),n_over_15=sum(p_>15 for p_ in ph))
out['slip_drawup_max_cm']=max(v['drawup_cm'] for v in R.values()); out['n_drawup_over2']=sum(v['drawup_cm']>2 for v in R.values())
out['total_shear_path_cm']=dict(med=float(np.median([v['total_shear_cm'] for v in R.values()])),max=max(v['total_shear_cm'] for v in R.values()))
out['supported_effort_max']=dict(med=float(np.median([v['supported_effort_max'] for v in R.values()])),max=max(v['supported_effort_max'] for v in R.values()))
out['dL_dhz_max']=max(v['dL_dhz_max'] for v in R.values())
# (e) fair vertical baseline: same pad tolerance 0.18 and r_e 0.03
with Pool() as p: RV=p.map(track_user,[(u,curve_vertical(),0.18,dict(r_e=0.03)) for u in USERS])
ok=lambda q: bool(q.get('release_hz') and q['fwd_slip_max_cm']<=2 and q['min_catch_cm']>=0)
out['vertical_fair']=dict(n_ok=sum(ok(q) for _,q,_ in RV), fwd_max=max(q['fwd_slip_max_cm'] for _,q,_ in RV), catch_min=min(q['min_catch_cm'] for _,q,_ in RV),
                          E_med=float(np.median([q['E0_release'] for _,q,_ in RV])), E_max=max(q['E0_release'] for _,q,_ in RV))
json.dump(dict(out=out,users=R),open('/home/user/me5412-bedexit-proposal/page/seat1dof/audit/checks/verify.json','w'),ensure_ascii=False,indent=1)
for k,v in out.items(): print(k,v)
