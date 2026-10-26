import sys, json, numpy as np; sys.path.insert(0,'/home/user/me5412-bedexit-proposal/model/calc_v13')
import seat_1dof_layout as LYm, seat_1dof_fourbar2 as FB2
from seat_trajectory import rot
L=json.load(open('seat_1dof/layout.json')); x=np.array(L['x']); act=L['mech']['act']
A,B,c1,c2=x[:2],x[2:4],x[4:6],x[6:8]
s=[p[:5] for p in FB2.run(x,n=500)]
def segd(P,X,Y):
    d=Y-X; t=np.clip(((P-X)@d)/(d@d),0,1); return np.hypot(*(P-(X+t[:,None]*d)).T)
def seg2seg(X1,Y1,X2,Y2):
    P=LYm.seg_pts(X1,Y1,25); Q=LYm.seg_pts(X2,Y2,25)
    return min(segd(P,X2,Y2).min(), segd(Q,X1,Y1).min())
gaps={}
def upd(k,v,z):
    gaps.setdefault(k,[]).append((v,z))
for f in s:
    Q,phi,P1,P2=f[0],f[1],f[2],f[3]; plate,br=LYm.seat_polys(Q,phi,c1,c2)
    (D,H,rh),(H2,E,rr),Ept=LYm.act_parts(f,act,A,B)
    # cross tube vs seat underside (plate bottom edge), vs bracket polygon, vs posts, vs rails(floor plate z .04)
    pb=plate[2:4] if True else None
    upd('横管—座板底面', seg2seg(plate[2],plate[3],Ept,Ept+1e-6)-LYm.R_TUBE, Q[1])
    brp=LYm.poly_pts(br,0.005); upd('横管—座板支架', float(np.hypot(*(brp-Ept).T).min())-LYm.R_TUBE, Q[1])
    upd('横管—立柱A', seg2seg(np.array([A[0],0.04]),A,Ept,Ept+1e-6)-LYm.R_TUBE-LYm.R_POST, Q[1])
    upd('横管—立柱B', seg2seg(np.array([B[0],0.04]),B,Ept,Ept+1e-6)-LYm.R_TUBE-LYm.R_POST, Q[1])
    upd('横管—底座（z=4 cm）', Ept[1]-LYm.R_TUBE-0.04, Q[1])
    # seat plate bottom vs pivot posts tops / rockers (crush between descending seat and fixed parts)
    for nm,G0 in (('A',A),('B',B)):
        upd(f'座板底面/支架—立柱{nm}顶', min(segd(LYm.poly_pts(br,0.005),np.array([G0[0],0.04]),G0+np.array([0,0.02])).min(), segd(LYm.poly_pts(plate,0.005),np.array([G0[0],0.04]),G0).min())-LYm.R_POST, Q[1])
    # actuator vs rockers (mid-plane vs side plane: different planes, informative only)
    upd('推杆—后横梁/地面', min(D[1],H[1],E[1])-rh, Q[1])
    # seat front edge height vs footplate (feet under the seat front when lowering?)
    upd('座板前缘—脚踏板', Q[1]+ (rot(phi)@np.array([0.085,-0.045]))[1]-0.04, Q[1])
for k,v in gaps.items():
    vals=np.array([a for a,_ in v]); i=int(vals.argmin())
    print(f'{k:22s} min {100*vals.min():6.1f} cm at seat z {v[i][1]:.3f}  | start {100*vals[0]:6.1f}  top {100*vals[-1]:6.1f}')
# tipping: base support x 0.03..0.66, |y|<=0.27. device 35 kg at (0.30, z), user loads.
g=9.81
def cop(loads): # list of (Fz_down N, x)
    F=sum(a for a,_ in loads); return sum(a*b for a,b in loads)/F
dev=(35*g,0.30)
print('--- tipping (COP x must stay within 0.03..0.66) ---')
for name,loads in [('100 kg 猛坐在起始座板 1.5 BW，脚不着地',[dev,(1.5*100*g,0.055)]),
                   ('同上，坐在座板后缘 x=0.01',[dev,(1.5*100*g,0.01)]),
                   ('45 kg 轻用户猛坐后缘（器械重量占比小）',[dev,(1.5*45*g,0.01)]),
                   ('100 kg 全身挂在扶手上 x=0.69',[dev,(100*g,0.69)]),
                   ('100 kg 坐板在顶 0.5BW x=0.24 + 扶手 0.25BW + 脚 0.25BW x=0.25',[dev,(50*g,0.24),(25*g,0.69),(25*g,0.25)])]:
    c=cop(loads); print(f'{name:55s} COP x = {c:.3f}  margin rear {c-0.03:+.3f} front {0.66-c:+.3f}')
# lateral: bar push sideways at bar height ~1.06
for m in (60,100):
    W=(m+35)*g; print(f'lateral force to tip ({m} kg on device, bar 1.06 m): {W*0.27/1.06:.0f} N = {W*0.27/1.06/(m*g):.2f} BW')
