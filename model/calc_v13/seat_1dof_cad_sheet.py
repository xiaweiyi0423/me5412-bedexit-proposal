"""v5.6: dimension sheet for the CAD model (role 3). Everything is read from the model, nothing typed by hand except the
assumed section sizes that the model never needed (marked "假设" in the sheet).

Frame (same as every model file): origin on the floor under the bed's long edge, at the seat's centre plane.
  x  out from the bed edge (bed at x < 0), y along the bed (+ = head side, where the housing is), z up.
Seat frame: origin Q = middle of the seat's top surface (cushion top), x forward along the seat, z normal to it; the seat is
tilted forward by phi (deg), world = Q + R(phi) (x_s, z_s) with R(phi) = [[cos, sin], [-sin, cos]].

Outputs: ../../cad/travel_table.csv (screw stroke every 10 mm), ../../cad/key_poses.csv, seat_1dof/cad_sheet.json
"""
import csv, json, os
import numpy as np
import seat_1dof_slider as SL
import seat_1dof_v5_checks as VC
from seat_trajectory import SEAT_X0, SEAT_X1, Z0, rot
import seat_1dof_v5 as V5

HERE = os.path.dirname(os.path.abspath(__file__)); CAD = os.path.join(HERE, "..", "..", "cad"); os.makedirs(CAD, exist_ok=True)
J = json.load(open(os.path.join(HERE, "seat_1dof", "slider.json"))); CK = json.load(open(os.path.join(HERE, "seat_1dof", "v5_checks.json")))
P = json.load(open(os.path.join(HERE, "seat_1dof", "page.json"))); REL = json.load(open(os.path.join(HERE, "seat_1dof", "release_z.json")))
r4 = lambda v: [round(float(a), 4) for a in v]

if __name__ == "__main__":
    sim, g = SL.simulate(J["x"], 2000)
    s0 = sim[0][4]; c1, c2 = np.array(J["x"][:2]), np.array(J["x"][2:4]); B = np.array(g["B"]); e = np.array(g["d"]) / np.hypot(*g["d"])
    rows = []
    for Q, phi, P1, P2, s in sim:
        rows.append(dict(stroke_mm=1000 * (s - s0), Q=Q, phi=phi, P1=P1, P2=P2, link_deg=np.degrees(np.arctan2(P2[1] - B[1], P2[0] - B[0]))))
    stroke = rows[-1]["stroke_mm"]
    pick = lambda mm: min(rows, key=lambda r: abs(r["stroke_mm"] - mm))
    with open(os.path.join(CAD, "travel_table.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["screw_stroke_mm", "seat_Qx_mm", "seat_Qz_mm", "seat_tilt_deg", "pin1_x_mm", "pin1_z_mm", "pin2_x_mm", "pin2_z_mm", "link_angle_deg"])
        for mm in list(range(0, int(stroke), 10)) + [stroke]:
            r = pick(mm); w.writerow([round(r["stroke_mm"], 1)] + [round(1000 * v, 1) for v in r["Q"]] + [round(r["phi"], 2)] +
                                    [round(1000 * v, 1) for v in (*r["P1"], *r["P2"])] + [round(r["link_deg"], 2)])
    z_rel = np.array([v["seat_z"] for v in REL.values()])
    def at_height(z): return min(rows, key=lambda r: abs(r["Q"][1] - z))
    keys = [("齐平（起点）", rows[0]), ("回床高度 0.50 m", at_height(0.50)), ("离座中位", at_height(float(np.median(z_rel)))),
            ("前倾最大", max(rows, key=lambda r: r["phi"])), ("离座最高", at_height(float(z_rel.max()))), ("顶（终点）", rows[-1])]
    with open(os.path.join(CAD, "key_poses.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["pose", "screw_stroke_mm", "seat_Qx_mm", "seat_Qz_mm", "seat_tilt_deg", "pin1_x_mm", "pin1_z_mm", "pin2_x_mm", "pin2_z_mm", "link_angle_deg"])
        for n, r in keys: w.writerow([n, round(r["stroke_mm"], 1)] + [round(1000 * v, 1) for v in r["Q"]] + [round(r["phi"], 2)] +
                                     [round(1000 * v, 1) for v in (*r["P1"], *r["P2"])] + [round(r["link_deg"], 2)])
    (lo, hi), (lo2, hi2) = VC.rails(); E = CK["emergency"]; Fo = CK["forces"]
    out = dict(note=__doc__,
               frame="x 离床方向（床沿 x=0，床在 x<0），y 沿床长（+ 为床头一侧），z 向上（地面 z=0）；y=0 是座板中面",
               bed=dict(top_z=Z0, note="床垫面 0.42 m；床沿在 x = 0"),
               seat=dict(x_world_at_flush=[SEAT_X0, SEAT_X1], half_len=round((SEAT_X1 - SEAT_X0) / 2, 4), width_y=[-VC.Y["seat"], VC.Y["seat"]],
                         lip=V5.LIP, foam_board_t=VC.SEAT_T, split_x_s=VC.SEAT_T["split"], pins_seat_frame=dict(c1=r4(c1), c2=r4(c2), spacing=round(float(np.hypot(*(c1 - c2))), 4))),
               rail1=dict(lo=r4(lo), hi=r4(hi), length=round(float(np.hypot(*(hi - lo))), 4), angle_from_vertical_deg=round(float(np.degrees(np.arctan2(e[0], e[1]))), 2), y=VC.Y["rail"]),
               rail2=dict(lo=r4(lo2), hi=r4(hi2), offset=VC.RAIL_GAP, y=VC.Y["rail"]),
               carriages=dict(per_rail=2, span_along_rail=VC.CARR_SPAN, assumed_len=VC.CARR_LEN, block_from_pin=[-0.03, VC.CARR_SPAN + VC.CARR_LEN / 2]),
               screw=dict(stroke=round(stroke / 1000, 4), lead_mm=E["lead_mm"], axis="两根导轨之间、与导轨平行，螺母经浮动接头连滑块板"),
               link=dict(ground_pivot_B=r4(B), length=round(float(g["R"]), 4), y=VC.Y["link"]),
               housing=dict(outline_xz=CK["rail"]["housing"], y=[VC.Y["wall_in"], VC.Y["wall_out"]], wall=VC.WALL, motor_xz=CK["rail"]["motor"]),
               base=dict(x=[0.03, 0.78], y=[VC.Y["base_open"], VC.Y["base_head"]], tube_h=0.035),
               handrail=dict(post=dict(x=P["consts"]["handrail"]["x"], y=0.30, top_z=P["consts"]["handrail"]["z"]), bar=dict(z=P["consts"]["handrail"]["z"], y=[-0.05, 0.30])),
               footplate=dict(x=[0.20, 0.62], y=[-0.22, 0.22], z=[0.035, 0.047]),
               loads=dict(screw_hold100_N=J["mech"]["screw_force_hold100_N"], link_hold100_N=J["mech"]["forces_hold100_N"]["link"],
                          seat_normal_hold100_N=J["mech"]["forces_hold100_N"]["normal"], offset10cm=Fo["载荷偏向敞开一侧 10 cm"], centre=Fo["载荷在座板中线"],
                          anchor_N=P["layout"]["tipping"]["固定件拉力（ADA 609 扶手设计载荷 1112 N，安全系数 1.5）"]["anchor_N"], brake_torque_Nm=E["brake_torque_Nm"]),
               clearances=dict(bed_floor_cm=CK["bed_floor_cm"], pinch_cm=CK["pinch_cm"], legs_cm=CK["bracket_vs_legs_cm"]),
               key_poses={n: dict(stroke_mm=round(r["stroke_mm"], 1), Q=r4(r["Q"]), phi=round(r["phi"], 2), P1=r4(r["P1"]), P2=r4(r["P2"])) for n, r in keys})
    C3 = json.load(open(os.path.join(HERE, "seat_1dof", "cantilever3d.json")))
    nf = np.array([e[1], -e[0]]); nf = nf if (lo2 - lo) @ nf > 0 else -nf
    out["rail_dirs"] = dict(e=r4(e), nf_rail1_to_rail2=r4(nf))
    out["screw"].update(axis_lo=r4(lo + 0.5 * VC.RAIL_GAP * nf + 0.03 * e), axis_hi=r4(hi + 0.5 * VC.RAIL_GAP * nf - 0.06 * e), y=round(VC.Y["rail"] - 0.029, 4))
    out["carriage_plate"] = dict(along_rail_from_pin1=[-0.04, VC.CARR_SPAN + 0.04], across_from_rail1=[-0.02, VC.RAIL_GAP + 0.02], y=[VC.Y["rail"] - 0.03, VC.Y["rail"] - 0.015], note="假设尺寸")
    out["seat_arm"] = dict(seat_frame_x=[-out["seat"]["half_len"] + 0.05, out["seat"]["half_len"] - 0.03], seat_frame_z=[-0.092, -0.062], y=[-VC.Y["seat"] + 0.03, VC.Y["wall_in"]], note="座板下的悬臂托架（假设截面），从座板下伸进竖槽")
    out["joints"] = dict(
        c1=dict(type="转动副（绕 y）", must_carry=dict(moment_Nm=C3["c1_moment_Nm"]["value"], force_N=C3["c1_force_N"]["value"]),
                options=["A 薄型交叉滚子轴承贴装在滑块板侧面（厚约 2 cm，外径 12–15 cm）", f"B 短轴穿过竖槽，两个轴承相距约 14 cm（每个约 {C3['c1_bearing_radial_N_s140']['value']} N）"],
                bearing_radial_N={k.replace("c1_bearing_radial_N_", ""): C3[k]["value"] for k in C3 if k.startswith("c1_bearing_radial_N_s")}),
        c2=dict(type="球铰（杆端关节轴承）", link_axial_N=C3["link_axial_N"]["value"]),
        B=dict(type="球铰（杆端关节轴承），固定在机构箱底部"),
        nut=dict(type="浮动接头，只传轴向", axial_N=C3["nut_axial_N"]["value"]),
        carriages=dict(radial_N=C3["carriage_radial_y_N"]["value"], lateral_N=C3["carriage_lateral_inplane_N"]["value"], resultant_N=C3["carriage_resultant_N"]["value"],
                       note="假设滑块板刚性、4 个滑块一样硬；离铰点 1 最近的那个实际更大，选型乘 1.3–1.5"))
    out["lever"] = "应急拉索拨杆：横杆与立柱拐角下方，带翻盖；坐着伸手够得到，不在握把正下方（位置待 CAD 和真人核对）"
    out["fea"] = dict(deflection_target_mm=5, cases=["100 kg × 1.5 偏向敞开一侧 10 cm，方向：法向 / 竖直 / 法向 ± 0.3 沿座面", "猛坐座板 + 同时拉横杆 0.25 倍体重", "固定件 2282 N（ADA 1112 N × 1.5）"])
    json.dump(out, open(os.path.join(HERE, "seat_1dof", "cad_sheet.json"), "w"), ensure_ascii=False, indent=1)
    print("stroke", round(stroke, 1), "mm; rail1", out["rail1"]); print("keys", {n: out["key_poses"][n]["stroke_mm"] for n in out["key_poses"]})
