"""Generate inline SVG figures for plan.html (role cards + overview).
Geometry follows the proposal page's side-view animation (drawB / POSE)."""
import math, json

W = 520
S = 300.0          # px per metre
X0 = 20 + 0.30 * S # x=-0.30 m at left edge
TOP = 1.36
Z0 = 14 + TOP * S

def X(x): return X0 + x * S
def Z(z): return Z0 - z * S
def pt(p): return f"{X(p[0]):.1f},{Z(p[1]):.1f}"
def pts(a): return " ".join(pt(p) for p in a)

POSE = {
 "Brise": dict(S=[0.37,1.149],H=[0.14,0.75],K=[0.42,0.44],A=[0.29,0.062],T=[0.46,0.02],E=[0.52,0.98],W=[0.69,1.06]),
 "Bready": dict(S=[0.28,0.94],H=[0.13,0.51],K=[0.46,0.40],A=[0.29,0.062],T=[0.46,0.02],E=[0.48,0.76],W=[0.69,0.82]),
}

def head(q):
    dx, dz = q["S"][0]-q["H"][0], q["S"][1]-q["H"][1]; n = math.hypot(dx, dz)
    return [q["S"][0]+dx/n*0.12, q["S"][1]+dz/n*0.12]

def person(q, cls="pk"):
    h = head(q)
    return (f'<polyline class="{cls}" stroke-width="6" points="{pts([q["S"],q["H"],q["K"],q["A"],q["T"]])}"/>'
            f'<circle class="{cls} hd" stroke-width="4" cx="{X(h[0]):.1f}" cy="{Z(h[1]):.1f}" r="{0.055*S:.1f}"/>'
            f'<polyline class="{cls}" stroke-width="4" points="{pts([q["S"],q["E"],q["W"]])}"/>')

def seat_poly(L, tilt):
    tn = math.tan(math.radians(tilt)); h0 = 0.42 + L; zr = h0 + 0.14*tn; t = 0.045
    return [[-0.03,zr],[0,zr],[0.13,h0+0.01*tn],[0.14,h0-0.012],[0.14,h0-t],[0,zr-t],[-0.03,zr-0.012]], h0

def anchor():
    """hook plate slid between mattress and bed frame, tying the station to the bed"""
    return (f'<rect class="hook" x="{X(-0.26):.1f}" y="{Z(0.276):.1f}" width="{0.26*S:.1f}" height="{0.012*S:.1f}" rx="1.5"/>'
            f'<rect class="hook" x="{X(-0.004):.1f}" y="{Z(0.30):.1f}" width="{0.012*S:.1f}" height="{0.036*S:.1f}"/>')

def scene(L=0.24, tilt=0, rail=True, column=True, bed=True, seat_cls="seat"):
    out = []
    out.append(f'<line class="fl" x1="0" y1="{Z(0):.1f}" x2="{W}" y2="{Z(0):.1f}"/>')
    if bed:
        out.append(f'<rect class="bed" x="{X(-0.5):.1f}" y="{Z(0.27):.1f}" width="{0.5*S:.1f}" height="{0.27*S:.1f}" rx="4"/>')
        out.append(f'<rect class="mat" x="{X(-0.5):.1f}" y="{Z(0.42):.1f}" width="{0.5*S:.1f}" height="{0.15*S:.1f}" rx="6"/>')
        out.append(f'<text class="tm" x="{X(-0.27):.1f}" y="{Z(0.13):.1f}">床</text>')
        out.append(anchor())
    out.append(f'<polygon class="dev" points="{pts([[0,0],[0.80,0],[0.77,0.013],[0,0.013]])}"/>')
    sp, h0 = seat_poly(L, tilt)
    if column:
        out.append(f'<rect class="dev" x="{X(0):.1f}" y="{Z(0.30):.1f}" width="{0.14*S:.1f}" height="{(0.30-0.013)*S:.1f}" rx="3"/>')
        top = h0 - 0.05
        if top > 0.30:
            out.append(f'<rect class="dev" x="{X(0.04):.1f}" y="{Z(top):.1f}" width="{0.06*S:.1f}" height="{(top-0.30)*S:.1f}"/>')
    out.append(f'<polygon class="{seat_cls}" points="{pts(sp)}"/>')
    if rail:
        zs, zb, BX = 0.64 + L, 0.82 + L, 0.69
        out.append(f'<line class="rl" stroke-width="8" opacity=".35" x1="{X(BX):.1f}" y1="{Z(0.02):.1f}" x2="{X(BX):.1f}" y2="{Z(0.55):.1f}"/>')
        out.append(f'<line class="rl" stroke-width="4" opacity=".6" x1="{X(BX):.1f}" y1="{Z(0.5):.1f}" x2="{X(BX):.1f}" y2="{Z(zb):.1f}"/>')
        out.append(f'<line class="rl" stroke-width="4" opacity=".5" stroke-linecap="round" x1="{X(0):.1f}" y1="{Z(zs):.1f}" x2="{X(BX):.1f}" y2="{Z(zs):.1f}"/>')
        out.append(f'<circle class="bar" cx="{X(BX):.1f}" cy="{Z(zb):.1f}" r="7"/>')
    return "".join(out)

def mark(x, z, label, cls="mk", dx=0, dy=0):
    cx, cy = X(x)+dx, Z(z)+dy
    return (f'<circle class="{cls}" cx="{cx:.1f}" cy="{cy:.1f}" r="11"/>'
            f'<text class="mkt" x="{cx:.1f}" y="{cy+4.5:.1f}">{label}</text>')

def leader(x1, z1, x2, z2, cls="ld"):
    return f'<line class="{cls}" x1="{X(x1):.1f}" y1="{Z(z1):.1f}" x2="{X(x2):.1f}" y2="{Z(z2):.1f}"/>'

def arrow(x1, y1, x2, y2, cls="ar", w=2.5):
    """pixel-space arrow with head at (x2,y2)"""
    a = math.atan2(y2-y1, x2-x1); h = 9
    p1 = (x2 - h*math.cos(a-0.4), y2 - h*math.sin(a-0.4)); p2 = (x2 - h*math.cos(a+0.4), y2 - h*math.sin(a+0.4))
    return (f'<line class="{cls}" stroke-width="{w}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
            f'<polygon class="{cls}f" points="{x2:.1f},{y2:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"/>')

def svg(body, h, w=W, label=""):
    return f'<svg viewBox="0 0 {w} {h:.0f}" role="img" aria-label="{label}">{body}</svg>'

H_SCENE = Z(0) + 16

# ---------- overview (primer): who owns which part ----------
def overview():
    q = POSE["Brise"]; b = []
    b.append(scene())
    b.append(person(q))
    # actuator hint inside column
    b.append(f'<rect class="act" x="{X(0.05):.1f}" y="{Z(0.28):.1f}" width="{0.04*S:.1f}" height="{0.22*S:.1f}" rx="3"/>')
    # role 2: joints
    for j in "HKA":
        b.append(f'<circle class="jt r2" cx="{X(q[j][0]):.1f}" cy="{Z(q[j][1]):.1f}" r="6"/>')
    b.append(leader(0.42, 0.44, 0.62, 0.36)); b.append(mark(0.62, 0.36, "2", "mk r2"))
    # role 3: seat + mechanism
    b.append(leader(0.02, 0.62, -0.16, 0.80)); b.append(mark(-0.16, 0.80, "3", "mk r3"))
    # role 4: actuator / base
    b.append(leader(0.07, 0.17, -0.16, 0.08)); b.append(mark(-0.16, 0.08, "4", "mk r4"))
    # role 5: sensors
    for p in ([0.07, 0.68], [0.69, 1.10], [0.42, 0.03]):
        b.append(f'<circle class="sn" cx="{X(p[0]):.1f}" cy="{Z(p[1]):.1f}" r="5.5"/>')
    b.append(leader(0.69, 1.10, 0.86, 1.22)); b.append(mark(0.86, 1.22, "5", "mk r5"))
    b.append(f'<text class="tm" x="{X(0.50):.1f}" y="{Z(0.05):.1f}">踏板</text>')
    b.append(f'<text class="t b" x="{X(-0.28):.1f}" y="30">升起后</text>')
    b.append(f'<text class="t" x="{X(-0.28):.1f}" y="50">座板 0.66 m · 保持水平</text>')
    return svg("".join(b), H_SCENE, label="起身台侧视图与各角色负责的部分")

# ---------- role 2: forces at seat-off ----------
def role2():
    q = POSE["Brise"]; b = [scene(), person(q, "pk dim")]
    # joints and moment arcs
    for j, lab, dx in (("H", "M髋", -46), ("K", "M膝", 14), ("A", "M踝", -46)):
        cx, cy = X(q[j][0]), Z(q[j][1])
        b.append(f'<path class="mo" d="M{cx-14:.1f} {cy-10:.1f} A 17 17 0 1 1 {cx-14:.1f} {cy+10:.1f}"/>')
        b.append(f'<circle class="jt r2" cx="{cx:.1f}" cy="{cy:.1f}" r="6"/>')
        b.append(f'<text class="t b" x="{cx+dx:.1f}" y="{cy+5:.1f}">{lab}</text>')
    # hand force (bar pulls hand down/forward is the reaction on the person; draw the force on the person: up/back)
    wx, wz = X(q["W"][0]), Z(q["W"][1])
    b.append(arrow(wx, wz, wx-34, wz-26, "ar"))
    b.append(f'<text class="t" x="{wx-118:.1f}" y="{wz-30:.1f}">手上的力</text>')
    # floor reaction
    fx = X(0.36); fy = Z(0.0)
    b.append(arrow(fx, fy+2, fx-6, fy-62, "ar"))
    b.append(f'<text class="t" x="{fx+6:.1f}" y="{fy-44:.1f}">地面反力</text>')
    # seat force = 0
    b.append(f'<text class="t b" x="{X(-0.28):.1f}" y="30">离座瞬间</text>')
    b.append(f'<text class="t" x="{X(-0.28):.1f}" y="50">座板上的力 = 0</text>')
    # body weight
    gx, gz = X(0.27), Z(0.88)
    b.append(f'<circle class="cg" cx="{gx:.1f}" cy="{gz:.1f}" r="6"/>')
    b.append(arrow(gx, gz+6, gx, gz+58, "ar"))
    b.append(f'<text class="t" x="{gx+8:.1f}" y="{gz+44:.1f}">体重</text>')
    return svg("".join(b), H_SCENE, label="离座瞬间人体受力和关节力矩")

# ---------- role 3: two positions + where mechanism goes ----------
def role3():
    b = []
    b.append(f'<line class="fl" x1="0" y1="{Z(0):.1f}" x2="{W}" y2="{Z(0):.1f}"/>')
    b.append(f'<rect class="bed" x="{X(-0.5):.1f}" y="{Z(0.27):.1f}" width="{0.5*S:.1f}" height="{0.27*S:.1f}" rx="4"/>')
    b.append(f'<rect class="mat" x="{X(-0.5):.1f}" y="{Z(0.42):.1f}" width="{0.5*S:.1f}" height="{0.15*S:.1f}" rx="6"/>')
    b.append(f'<text class="tm" x="{X(-0.27):.1f}" y="{Z(0.13):.1f}">床</text>')
    b.append(anchor())
    b.append(f'<text class="tm" x="{X(-0.27):.1f}" y="{Z(0.30)-2:.1f}">钩板</text>')
    b.append(f'<polygon class="dev" points="{pts([[0,0],[0.80,0],[0.77,0.013],[0,0.013]])}"/>')
    # foot keep-out zone
    b.append(f'<rect class="keep" x="{X(0.20):.1f}" y="{Z(0.20):.1f}" width="{0.55*S:.1f}" height="{(0.20-0.013)*S:.1f}"/>')
    b.append(f'<text class="t" x="{X(0.30):.1f}" y="{Z(0.10):.1f}">脚的空间，机构别放这里</text>')
    # mechanism envelope
    b.append(f'<rect class="env" x="{X(-0.01):.1f}" y="{Z(0.62):.1f}" width="{0.18*S:.1f}" height="{(0.62-0.013)*S:.1f}" rx="4"/>')
    b.append(f'<text class="t b" x="{X(0.19):.1f}" y="{Z(0.30):.1f}">机构区</text>')
    b.append(f'<text class="tm" x="{X(0.19):.1f}" y="{Z(0.30)+18:.1f}">（由你设计）</text>')
    # flush seat (ghost) and raised seat
    sp0, _ = seat_poly(0, 0); sp1, _ = seat_poly(0.24, 0)
    b.append(f'<polygon class="ghost" points="{pts(sp0)}"/>')
    b.append(f'<polygon class="seat" points="{pts(sp1)}"/>')
    b.append(arrow(X(0.07), Z(0.47), X(0.07), Z(0.60), "ar"))
    b.append(f'<text class="t" x="{X(0.20):.1f}" y="{Z(0.42)+5:.1f}">齐平 0.42 m（虚线）</text>')
    b.append(f'<text class="t" x="{X(0.20):.1f}" y="{Z(0.75):.1f}">竖直升到 0.66 m，保持水平</text>')
    # rail both positions
    BX = 0.69
    b.append(f'<line class="rl" stroke-width="8" opacity=".35" x1="{X(BX):.1f}" y1="{Z(0.02):.1f}" x2="{X(BX):.1f}" y2="{Z(0.55):.1f}"/>')
    b.append(f'<line class="ghostl" x1="{X(0):.1f}" y1="{Z(0.64):.1f}" x2="{X(BX):.1f}" y2="{Z(0.64):.1f}"/>')
    b.append(f'<line class="ghostl" x1="{X(BX):.1f}" y1="{Z(0.5):.1f}" x2="{X(BX):.1f}" y2="{Z(0.82):.1f}"/>')
    b.append(f'<line class="rl" stroke-width="4" opacity=".6" x1="{X(BX):.1f}" y1="{Z(0.5):.1f}" x2="{X(BX):.1f}" y2="{Z(1.06):.1f}"/>')
    b.append(f'<line class="rl" stroke-width="4" opacity=".5" x1="{X(0):.1f}" y1="{Z(0.88):.1f}" x2="{X(BX):.1f}" y2="{Z(0.88):.1f}"/>')
    b.append(f'<circle class="bar" cx="{X(BX):.1f}" cy="{Z(1.06):.1f}" r="7"/>')
    b.append(f'<text class="t" x="{X(0.28):.1f}" y="{Z(1.06)+5:.1f}">L 形扶手跟着升</text>')
    b.append(f'<text class="tm" x="{X(0.73):.1f}" y="{Z(0.30):.1f}">外套管</text>')
    return svg("".join(b), H_SCENE, label="座板两个位置和机构可以放的区域")

def role3_options():
    """three candidate mechanisms, schematic"""
    b = []; w = 160
    def frame(ox, title):
        return (f'<rect class="box" x="{ox+4}" y="4" width="{w-8}" height="168" rx="8"/>'
                f'<text class="t b c" x="{ox+w/2}" y="160">{title}</text>')
    # twin columns
    ox = 10; b.append(frame(ox, "两根同步立柱"))
    b.append(f'<line class="fl" x1="{ox+24}" y1="132" x2="{ox+136}" y2="132"/>')
    for cx in (ox+46, ox+114):
        b.append(f'<rect class="dev" x="{cx-9}" y="80" width="18" height="52" rx="2"/><rect class="dev" x="{cx-6}" y="56" width="12" height="28"/>')
    b.append(f'<rect class="seat" x="{ox+32}" y="48" width="96" height="9" rx="2"/>')
    b.append(f'<line class="lk" x1="{ox+46}" y1="70" x2="{ox+114}" y2="70"/>')
    b.append(f'<line class="actl" x1="{ox+80}" y1="128" x2="{ox+80}" y2="72"/>')
    # scissor
    ox = 180; b.append(frame(ox, "剪叉"))
    b.append(f'<line class="fl" x1="{ox+24}" y1="132" x2="{ox+136}" y2="132"/>')
    b.append(f'<rect class="dev" x="{ox+34}" y="124" width="92" height="8"/>')
    b.append(f'<rect class="seat" x="{ox+34}" y="52" width="92" height="9" rx="2"/>')
    b.append(f'<line class="lk" x1="{ox+40}" y1="124" x2="{ox+120}" y2="62"/><line class="lk" x1="{ox+120}" y1="124" x2="{ox+40}" y2="62"/>')
    b.append(f'<line class="actl" x1="{ox+44}" y1="118" x2="{ox+92}" y2="96"/>')
    b.append(f'<circle class="pin" cx="{ox+80}" cy="{92}" r="4"/>')
    # column
    ox = 350; b.append(frame(ox, "单立柱直接顶升"))
    b.append(f'<line class="fl" x1="{ox+24}" y1="132" x2="{ox+136}" y2="132"/>')
    b.append(f'<rect class="dev" x="{ox+58}" y="76" width="44" height="56" rx="3"/>')
    b.append(f'<rect class="dev" x="{ox+66}" y="56" width="28" height="24"/>')
    b.append(f'<line class="actl" x1="{ox+80}" y1="128" x2="{ox+80}" y2="62"/>')
    b.append(f'<rect class="seat" x="{ox+40}" y="47" width="80" height="9" rx="2"/>')
    return svg("".join(b), 178, label="三种可能的升降机构示意")

# ---------- role 4: actuator, tipping, check points ----------
def actuator():
    b = []; y = 70
    # motor + gearbox (side-mounted below housing)
    b.append(f'<rect class="act" x="80" y="{y+14}" width="74" height="34" rx="6"/>')
    b.append(f'<text class="t c" x="117" y="{y+72}">电机 + 减速箱</text>')
    # housing tube
    b.append(f'<rect class="tube" x="30" y="{y-14}" width="230" height="28" rx="6"/>')
    # lead screw (inside, dashed)
    b.append(f'<line class="screw" x1="44" y1="{y}" x2="250" y2="{y}"/>')
    # rod
    b.append(f'<rect class="rod" x="260" y="{y-7}" width="120" height="14" rx="3"/>')
    # eyes
    b.append(f'<circle class="pin" cx="22" cy="{y}" r="9"/><circle class="pin" cx="392" cy="{y}" r="9"/>')
    # labels
    b.append(f'<text class="t c" x="150" y="{y-24}">外管（里面是丝杠，虚线）</text>')
    b.append(f'<text class="t c" x="320" y="{y-16}">推杆：伸出 / 缩回</text>')
    b.append(f'<text class="tm c" x="22" y="{y+30}">铰接孔</text><text class="tm c" x="392" y="{y+30}">铰接孔</text>')
    # stroke dimension
    b.append(f'<line class="dim" x1="260" y1="{y+40}" x2="380" y2="{y+40}"/>')
    b.append(f'<line class="dim" x1="260" y1="{y+34}" x2="260" y2="{y+46}"/><line class="dim" x1="380" y1="{y+34}" x2="380" y2="{y+46}"/>')
    b.append(f'<text class="t c" x="320" y="{y+60}">行程（伸出的长度）</text>')
    # force arrow
    b.append(arrow(404, y, 448, y, "ar"))
    b.append(f'<text class="t b" x="410" y="{y-14}">推力 F</text>')
    return svg("".join(b), 150, w=460, label="电动推杆（执行器）结构示意")

def tipping():
    Sx = 260.0; cx = 230; gy = 260
    def px(y): return cx + y*Sx
    def pz(z): return gy - z*Sx
    b = [f'<line class="fl" x1="0" y1="{gy}" x2="460" y2="{gy}"/>']
    hw = 0.33
    b.append(f'<rect class="dev" x="{px(-hw):.1f}" y="{pz(0.04):.1f}" width="{2*hw*Sx:.1f}" height="{0.04*Sx:.1f}" rx="3"/>')
    b.append(f'<rect class="dev" x="{px(-0.05):.1f}" y="{pz(0.62):.1f}" width="{0.10*Sx:.1f}" height="{0.58*Sx:.1f}"/>')
    b.append(f'<rect class="seat" x="{px(-0.21):.1f}" y="{pz(0.66):.1f}" width="{0.42*Sx:.1f}" height="{0.04*Sx:.1f}" rx="3"/>')
    # side rail post (one side) up to 0.88
    b.append(f'<line class="rl" stroke-width="5" x1="{px(0.24):.1f}" y1="{pz(0.62):.1f}" x2="{px(0.24):.1f}" y2="{pz(0.88):.1f}"/>')
    b.append(f'<line class="rl" stroke-width="5" x1="{px(0.18):.1f}" y1="{pz(0.88):.1f}" x2="{px(0.30):.1f}" y2="{pz(0.88):.1f}"/>')
    # pull force
    b.append(arrow(px(0.30)+2, pz(0.88), px(0.30)+62, pz(0.88), "ar"))
    b.append(f'<text class="t b" x="{px(0.30)+4:.1f}" y="{pz(0.88)-12:.1f}">F（手拉扶手）</text>')
    # height dimension
    hx = px(0.42)
    b.append(f'<line class="dim" x1="{hx:.1f}" y1="{gy}" x2="{hx:.1f}" y2="{pz(0.88):.1f}"/>')
    b.append(f'<text class="t" x="{hx+6:.1f}" y="{pz(0.45):.1f}">h</text>')
    # COM + weight
    b.append(f'<circle class="cg" cx="{px(0):.1f}" cy="{pz(0.25):.1f}" r="6"/>')
    b.append(arrow(px(0), pz(0.25)+6, px(0), pz(0.25)+50, "ar"))
    b.append(f'<text class="t" x="{px(0)-112:.1f}" y="{pz(0.25)+30:.1f}">台架重量 W</text>')
    # tipping edge
    b.append(f'<polygon class="edge" points="{px(hw):.1f},{gy} {px(hw)-7:.1f},{gy+12} {px(hw)+7:.1f},{gy+12}"/>')
    b.append(f'<text class="t" x="{px(hw)+12:.1f}" y="{gy+14}">翻倒时绕这条边转</text>')
    # b dimension
    b.append(f'<line class="dim" x1="{px(0):.1f}" y1="{gy+24}" x2="{px(hw):.1f}" y2="{gy+24}"/>')
    b.append(f'<text class="t c" x="{px(hw/2):.1f}" y="{gy+42}">b = 底座半宽</text>')
    b.append(f'<text class="tm" x="12" y="24">正视图（从床尾方向看）</text>')
    return svg("".join(b), 312, w=460, label="侧向倾翻受力示意")

def checks():
    b = [scene(rail=True, column=True)]
    # actuator inside column + its pins
    b.append(f'<rect class="act" x="{X(0.05):.1f}" y="{Z(0.28):.1f}" width="{0.04*S:.1f}" height="{0.22*S:.1f}" rx="3"/>')
    # loads
    sx, sz = X(0.10), Z(0.70)
    b.append(arrow(sx, sz-48, sx, sz-4, "ar"))
    b.append(f'<text class="t" x="{sx+10:.1f}" y="{sz-22:.1f}">人压在座板上</text>')
    bx, bz = X(0.69), Z(1.06)
    b.append(arrow(bx-60, bz-34, bx-8, bz-4, "ar"))
    b.append(f'<text class="t" x="{bx-150:.1f}" y="{bz-38:.1f}">手压 / 拉横杆</text>')
    # check marks
    for (x, z, n) in ((0.14, 0.62, "1"), (0.69, 0.55, "2"), (0.07, 0.30, "3"), (0.0, 0.88, "4"), (-0.13, 0.27, "5")):
        b.append(mark(x, z, n, "mk r4", dx=16 if n not in "45" else 0, dy=0 if n not in "45" else (-18 if n == "4" else 22)))
    b.append(f'<text class="tm" x="{X(0.50):.1f}" y="{Z(0.05):.1f}">踏板</text>')
    return svg("".join(b), H_SCENE, label="需要校核强度的位置")

# ---------- role 5: sensors ----------
def role5():
    q = POSE["Bready"]; b = [scene(L=0, tilt=0), person(q, "pk dim")]
    L = 0
    pos = {"1": (0.07, 0.43), "2": (0.69, 0.82), "3": (0.69, 0.82), "4": (0.40, 0.013)}
    b.append(f'<circle class="sn" cx="{X(0.07):.1f}" cy="{Z(0.40):.1f}" r="6"/>')
    b.append(f'<circle class="sn" cx="{X(0.69):.1f}" cy="{Z(0.82):.1f}" r="6"/>')
    b.append(f'<rect class="btn" x="{X(0.69)+6:.1f}" y="{Z(0.82)-16:.1f}" width="14" height="10" rx="2"/>')
    b.append(f'<circle class="sn" cx="{X(0.33):.1f}" cy="{Z(0.006):.1f}" r="6"/>')
    b.append(leader(0.07, 0.40, -0.12, 0.62)); b.append(mark(-0.12, 0.62, "1", "mk r5"))
    b.append(leader(0.69, 0.82, 0.86, 0.66)); b.append(mark(0.86, 0.66, "2", "mk r5"))
    b.append(leader(0.73, 0.86, 0.86, 1.00)); b.append(mark(0.86, 1.00, "3", "mk r5"))
    b.append(leader(0.33, 0.006, 0.12, 0.18)); b.append(mark(0.12, 0.18, "4", "mk r5"))
    b.append(f'<text class="tm" x="{X(0.50):.1f}" y="{Z(0.05):.1f}">踏板</text>')
    b.append(f'<text class="t" x="{X(-0.28):.1f}" y="30">坐在座板上、握住握把，准备握紧“起”开关</text>')
    return svg("".join(b), H_SCENE, label="传感器和开关的位置")

comp = json.load(open('../model/compare_v11.json'))
c = comp["P1 cap25"]
bars = [("低床 0.42 m，撑床垫", c["bed042_mattress"]["effort"], "m"),
        ("抬高床 0.58 m + 扶手", min(c["bed058_mattress"]["effort"], c["bed058_handle"]["effort"]), "m"),
        ("方案甲（动态扶手）", c["A042_drawn"]["effort"], "m"),
        ("起身台 0.66 m", c["B66_x55_z40"]["effort"], "c")]

FIGS = {
 "overview": overview(),
 "r2": role2(),
 "r3": role3(), "r3opt": role3_options(),
 "act": actuator(), "tip": tipping(), "chk": checks(),
 "r5": role5(),
 "bars": bars,
}
json.dump(FIGS, open('figs.json', 'w'), ensure_ascii=False)
print({k: len(v) if isinstance(v, str) else v for k, v in FIGS.items()})
