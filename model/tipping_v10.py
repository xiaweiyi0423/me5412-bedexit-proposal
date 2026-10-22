"""Tipping of the v10 bedside station (side view x forward from the bed edge, z up).
Station: footplate x 0..0.78, base width 0.56 (y +-0.28), estimated self-mass 30 kg with COM at x 0.25.
Front bar at x 0.62, z 0.95 (lifted); side rail z 0.64 (flush). Backward (toward bed) is blocked by the bed."""
import json
g=9.81; m=30; xc=0.25; xf=0.78; half_w=0.28
out={}
# 1) user standing on the plate: hand forces are internal to (user + station); overturning needs the
#    combined COM to leave the base polygon -> no tipping from hand forces alone.
out["on_plate"]="hand forces internal; stable while combined COM is over the base"
# 2) user stepped off the plate, pulls bar forward (toward self) horizontally at z 0.95
out["off_plate_forward_pull_N"]=round(m*g*(xf-xc)/0.95)
# 3) sitting on the bed edge, pulls side rail sideways at z 0.64 (lateral tipping about base side edge)
out["sit_up_lateral_pull_N"]=round(m*g*half_w/0.64)
# 4) same with the old v9 free-standing layout for reference (base 0.03-0.48, rail 0.72, mass needed for 177 N)
out["v9_mass_needed_177N_kg"]=round(177*0.72/(g*(0.48-0.255)))
print(out); json.dump(out,open("tipping_v10.json","w"),indent=1)
