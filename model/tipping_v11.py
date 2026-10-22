"""v11 tipping: one design load (177 N = 30% BW of 60 kg) in both axes.
Station COM x 0.25; footplate 0.80 long; base half-width 0.33; bar 1.06 m when raised; side rail 0.64 m when flush."""
import json
g=9.81; F=177; xc=0.25
def m_fwd(L,h): return F*h/(g*(L-xc))
def m_lat(hw,h): return F*h/(g*hw)
out={"design_load_N":F,
 "mass_needed_forward_kg(plate0.80,bar1.06)":round(m_fwd(0.80,1.06),1),
 "mass_needed_lateral_kg(halfw0.33,rail0.64)":round(m_lat(0.33,0.64),1),
 "mass_needed_lateral_kg(halfw0.33,rail0.88 raised)":round(m_lat(0.33,0.88),1),
 "chosen_mass_kg":35,
 "capacity_forward_N(35kg)":round(35*g*(0.80-xc)/1.06),
 "capacity_lateral_N(35kg,rail0.64)":round(35*g*0.33/0.64)}
print(out); json.dump(out,open("tipping_v11.json","w"),indent=1)
