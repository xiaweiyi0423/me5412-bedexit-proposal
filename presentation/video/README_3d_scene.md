# 3D shot S4 (device reveal, sketch -> 3D -> sketch), 1920x1080, 30 fps, 5.0 s

Output: S4.mp4 (150 frames, H.264 yuv420p, no audio). Contact sheet S4_tile.png, last frame S4_last.png.

Timing:
- 0.0-0.3 s: ink sketch on warm paper, exact side view (bed + device + L handrail).
- 0.3-2.3 s: camera swings (dolly-zoom from near-orthographic side view to 3/4 perspective). Materials warm up into the lit night bedroom from 0.6 s; fully lit at 2.3 s.
- 2.3-3.8 s: lit hold, slow drift. Seat flush with the mattress, lamp key light, moonlit window.
- 3.8-4.8 s: flatten back to the ink-sketch-on-paper look, staying in the 3/4 view.
- 4.3-4.9 s: thin black comic-panel border fades in (inset 44/40 px, 9 px).
- 4.8-5.0 s: hold on the final frame: 3/4 ink sketch of the bed outline and device on paper, inside the panel border.

Re-render:
1. `python3 prep.py`: packs cad/out/mesh.json, mechanism kinematics and page.json into data.js.
2. `node render.js S4 0.2 2.5 4.9` (previews into prev/), or `node render.js S4 --video [from to]` (frames into frames/S4, resumable).
3. `ffmpeg -framerate 30 -i frames/S4/f%04d.png -c:v libx264 -crf 16 -pix_fmt yuv420p S4.mp4`

`scene.js` also still contains the dropped mannequin scenes (S5–S10a), unused. Frames rendered for them are in dropped/.
