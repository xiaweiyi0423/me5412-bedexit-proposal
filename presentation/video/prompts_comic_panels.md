# Motion-comic panels: prompts

Model: `gemini-3-pro-image` (generateContent, responseModalities TEXT+IMAGE), aspect 16:9 (1376x768) unless noted (4:3 = 1200x896, 1:1 = 1024x1024).
Reference files: `character_2d.png` and `S2_start.png` are in `video/ai/keyframes/`. The text-free layouts and poses `layout_step1..5.png` and `pose_*.png`, made from `presentation/animations/seat_step*.png` and `seat_rise_mid.png`, are in `panels/candidates/_refs/`.
Method: C1 was made by editing a 16:9 text-free version of the seat_step1 schematic into a painted panel. This was the only approach that kept the device geometry; a text-only description or a layout passed as a passive reference both put the device in the wrong place. Each R frame is an edit of the previous frame plus the schematic for the next stage. R3 and R4 were edits of the schematic, with the previous frame as the scene reference, because edits of the previous frame barely moved the seat.

## C1  (candidate `C1E_a.png`)
Input images, in order: layout_step1.png (text-free 16:9 layout from seat_step1), character_2d.png, S2_start.png
```
Edit image 1: turn this flat side-view schematic into a finished hand-drawn comic panel. Keep the composition EXACTLY: same side-view camera, every object in the same place, same size, same angle. The figure faces RIGHT in strict profile.

Replace the stick figure with the grandmother from image 2 (short grey-white hair, light-blue checked pajamas, beige slippers), in exactly the stick figure's pose, seen from the side.
Turn the pale block on the left into a low bed with a white quilt; the orange block at its edge into a cream padded seat cushion level with the mattress; the pale grey slanted panel into a frosted semi-transparent housing with faint diagonal rails, standing behind her; the grey pole with the black knob into a slim steel post topped by a black grip bar; the grey floor strip into a low steel base with a dark rubber footplate.
Paint a night bedroom behind: deep-blue wall, a moonlit window, a small amber table lamp glowing at the far left, wooden floor.

Style: clean ink outlines, soft watercolour washes with paper grain, deep blue night palette with warm amber lamp light, like image 3. No text, no letters, no speech bubbles.
```

## C2  (candidate `C2_a.png`) — aspect 4:3
Input images, in order: C1.png (base_C1), character_2d.png
```
A close-up comic panel (4:3), side view, in exactly the hand-drawn ink-and-watercolour style and night colours of image 1 (deep blue night, warm amber lamp glow, paper grain, clean ink outlines). Close on the grandmother's hips and legs (light-blue checked pajamas, beige slippers, as in image 2): she slides her hips forward from the white mattress edge onto the cream padded seat cushion of the device, which sits right against the mattress edge at exactly the same height. Her slippers rest on the dark rubber footplate of the device's low steel base on the floor. The frosted housing of the device is behind her legs. Small motion lines suggest the slide. Leave a little calm empty space in the upper right. No text, no letters, no speech bubbles.
```

## C3  (candidate `C3_a.png`) — aspect 4:3
Input images, in order: C1.png (base_C1), character_2d.png
```
A close-up comic panel (4:3) in exactly the hand-drawn ink-and-watercolour style and night colours of image 1 (deep blue night, warm amber lamp glow from the left, paper grain, clean ink outlines). Both of the grandmother's elderly hands, with the light-blue checked pajama cuffs of image 2, close around a short black horizontal grip bar mounted on top of a slim grey steel post; the grip has a small round button on its top surface, not lit yet. Softly blurred background: the frosted housing of the device and the dark-blue bedroom wall. Natural hands with five fingers each, gentle and careful. Leave a little calm empty space in the upper right. No text, no letters, no speech bubbles.
```

## C4  (candidate `C4_b.png`) — aspect 1:1
Input images, in order: C1.png (base_C1)
```
An extreme close-up comic panel (square 1:1) in exactly the hand-drawn ink-and-watercolour style and night colours of image 1 (deep blue night, paper grain, clean ink outlines). An elderly thumb, with a light-blue checked pajama cuff at the edge of the frame, presses a round button set into the top of a black grip bar; the button glows warm amber, casting a soft amber glow onto the thumb and the grip. Dark blue softly blurred background. Natural anatomy. Leave a little calm empty space in one corner. No text, no letters, no speech bubbles.
```

## R1  (candidate `R1_c.png`)
Input images, in order: C1.png, layout_step2.png, character_2d.png
```
Edit image 1. This is one frame of a flipbook animation: keep the camera, framing, room, lamp, window, bed, the device's floor base, footplate, frosted housing and steel post with its grip bar EXACTLY the same and in exactly the same place. Change only the grandmother's pose and the position of the cream seat cushion, to match the side-view schematic in image 2 (same framing; the orange block is the seat cushion, the beige stick figure is her). Same character as image 3, same hand-drawn ink-and-watercolour style. No text, no letters.

Stage: she leans her torso forward and reaches out with both arms; both hands grip the black grip bar at the top of the post in front of her. The seat cushion has NOT moved yet: it is still flat and level with the mattress, under her buttocks.
```

## R2  (candidate `R2_c.png`)
Input images, in order: R1.png, layout_step3.png, character_2d.png
```
Edit image 1. This is one frame of a flipbook animation: keep the camera, framing, room, lamp, window, bed, the device's floor base, footplate, frosted housing and steel post with its grip bar EXACTLY the same and in exactly the same place. Change only the grandmother's pose and the position of the cream seat cushion, to match the side-view schematic in image 2 (same framing; the orange block is the seat cushion, the beige stick figure is her). Same character as image 3, same hand-drawn ink-and-watercolour style. No text, no letters.

Stage (only HALF of the way from image 1 toward the schematic): her buttocks are just starting to lift; the cream seat cushion has begun to move along the diagonal rails inside the housing — slightly FORWARD (to the right) and slightly UP, about a hand's width, and tilted forward a little (about 5 degrees). It stays pressed under her buttocks and thighs. She leans further forward over her feet, both hands still gripping the grip bar on top of the post. Feet stay on the footplate.
```

## R3  (candidate `R3L_a.png`)
Input images, in order: layout_step3.png (edited image), R2.png, character_2d.png
```
Edit image 1: turn this flat side-view schematic into the next frame of the comic flipbook shown in image 2. The finished frame must look exactly like image 2 — same camera, same room, lamp, moonlit window, bed, nightstand, same device (floor base with dark footplate, frosted housing, steel post with grip at its top), same grandmother, same ink-and-watercolour style — but with the woman's pose and the cream seat cushion's position and tilt taken EXACTLY from the schematic in image 1 (the orange block is the seat cushion, the beige stick figure is her, the pale block at left is the bed). Keep the schematic's positions, heights and angles precisely. No text, no letters.

Stage: rising. The seat cushion has moved forward (to the right, away from the bed edge) and up along the diagonal rails and is tilted forward about 9 degrees, still under her buttocks and thighs; a clear gap shows between the seat and the mattress. Her hips are higher, knees less bent, torso leaning forward, both hands gripping the grip on top of the post.
```

## R4  (candidate `R4fix_a.png`) — two steps: p_R4L.txt, then seat-tilt fix p_tiltfix.txt
Input images, in order: R4L_a.png (made from p_R4L.txt with inputs layout_step4.png + R3.png)
```
Edit image 1. Change ONLY the cream seat cushion under her: it is tilted too steeply. Make it much flatter — tilted only slightly, about 15 degrees from horizontal (front edge a little lower than the back edge), at the same height, still pressed under her buttocks and the backs of her thighs. Everything else (her pose, the room, the bed, the device, the framing, the style) stays exactly the same. No text.
```
First step prompt (`p_R4L.txt`):
```
Edit image 1: turn this flat side-view schematic into the next frame of the comic flipbook shown in image 2. The finished frame must look exactly like image 2 — same camera, same room, lamp, moonlit window, bed, nightstand, same device (floor base with dark footplate, frosted housing, steel post with grip at its top), same grandmother (keep her design exactly), same ink-and-watercolour style — but with the woman's pose and the cream seat cushion's position and tilt taken EXACTLY from the schematic in image 1 (the orange block is the seat cushion, the beige stick figure is her, the pale block at left is the bed). Keep the schematic's positions, heights and angles precisely. No text, no letters.

Stage: rising further than image 2. The seat cushion is higher and further forward along the diagonal rails than in image 2 and tilted forward about 15 degrees (front edge lower), still pressed under her buttocks and the backs of her thighs. Her hips are clearly higher than in image 2, knees only slightly bent, torso leaning well forward over her feet, both hands gripping the grip on top of the post.
```

## R5  (candidate `R5fix_a.png`) — two steps: p_R5.txt, then seat-tilt fix p_tiltfix.txt
Input images, in order: R5_a.png (made from p_R5.txt with inputs R4.png + pose_rise_mid.png + character_2d.png)
```
Edit image 1. Change ONLY the cream seat cushion under her: it is tilted too steeply. Make it much flatter — tilted only slightly, about 15 degrees from horizontal (front edge a little lower than the back edge), at the same height, still pressed under her buttocks and the backs of her thighs. Everything else (her pose, the room, the bed, the device, the framing, the style) stays exactly the same. No text.
```
First step prompt (`p_R5.txt`):
```
Edit image 1. This is one frame of a flipbook animation: keep the camera, framing, room, lamp, window, bed, the device's floor base, footplate, frosted housing and steel post with its grip EXACTLY the same and in the same place. Change only the grandmother's pose and the seat cushion, following the side-view pose sketch in image 2. Same character as image 3, same hand-drawn ink-and-watercolour style. No text, no letters.

Stage: she is nearly standing. Her legs are almost straight, her hips are clearly higher than in image 1, her torso is still leaning a little forward, both hands on the grip. The cream seat cushion has reached the top of its travel — a little higher and further forward than in image 1 — tilted forward about 15 degrees (no more), still touching the backs of her upper thighs just under her buttocks. Feet stay on the footplate.
```

## R6  (candidate `R6_a.png`)
Input images, in order: R5.png, layout_step5.png, character_2d.png
```
Edit image 1. This is the last frame of a flipbook animation: keep the camera, framing, room, lamp, window, bed, the device's floor base, footplate, frosted housing and steel post with its grip EXACTLY the same and in the same place. Change only the grandmother's pose and the seat cushion, following the side-view schematic in image 2 (same framing). Same character as image 3, same hand-drawn ink-and-watercolour style. No text, no letters.

Stage: she now STANDS fully upright on the footplate, steady and calm, one hand resting on the grip on top of the post, the other arm relaxed. The cream seat cushion stays at the top of its travel, where it was in image 1, tilted only slightly, just behind the backs of her thighs.
```

## S9a  (candidate `S9a_a.png`)
Input images, in order: R3.png
```
Edit image 1. Keep the camera, framing, room, lamp, bed, the whole device and the seat cushion's position EXACTLY the same, and keep her mid-rise body pose. Change only: she closes her eyes and frowns slightly, dizzy, her head tipping a little, and one hand is loosening and slipping off the grip (fingers opening). Same character, same hand-drawn ink-and-watercolour style. No text, no letters.
```

## S9b  (candidate `S9b_a.png`)
Input images, in order: S9a.png
```
Edit image 1. Keep the camera, framing, room, lamp, bed and the whole device EXACTLY the same — the cream seat cushion stays at exactly the same raised, slightly tilted position (it has stopped and has not moved). Change only her: she has sat back down onto the raised seat cushion, which holds her safely under her buttocks; her knees are bent, her body upright and relaxed; her eyes are open and she looks relieved, a small calm smile; both hands rest lightly on the grip on top of the post. Same character, same hand-drawn ink-and-watercolour style. No text, no letters.
```

## C5  (candidate `C5_b.png`)
Input images, in order: R6.png
```
Edit image 1. Keep the camera, framing, room, lamp, bed and the whole device EXACTLY the same — the cream seat cushion stays raised at the top of its travel where it is now. Change only her: she has let go of the grip and is stepping forward off the dark footplate onto the wooden floor to the right, one slipper already on the floor, steady, upright and calm, seen from the side facing right. Same character, same hand-drawn ink-and-watercolour style. No text, no letters.
```

## H3  (candidate `H3_b.png`)
Input images, in order: R3.png
```
Edit image 1. Keep the real scene EXACTLY as it is: her pose, the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the back wall, cast by the warm bedside lamp at the left: her silhouette, enlarged, falls on the blue wall to the right and above her, together with the shadow of the device under her. In this frame the device's shadow under her shadow begins to curve upward at its front edge, like the tips of gentle fingers starting to form. Warm and comforting, not spooky: soft blurry edges, the wall around the shadows washed in warm amber lamplight. No text, no letters.
```

## H4  (candidate `H4_b.png`)
Input images, in order: R4.png
```
Edit image 1. Keep the real scene EXACTLY as it is: her pose, the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the back wall, cast by the warm bedside lamp at the left: her silhouette, enlarged, falls on the blue wall to the right and above her, together with the shadow of the device under her. In this frame the device's shadow under her shadow has become unmistakably a big, soft, open human hand, palm up, its fingers gently curved, cradling her shadow from below and holding it up. Warm and comforting, not spooky: soft blurry edges, the wall around the shadows washed in warm amber lamplight. No text, no letters.
```

## H5  (candidate `H5_b.png`)
Input images, in order: R5.png
```
Edit image 1. Keep the real scene EXACTLY as it is: her pose, the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the back wall, cast by the warm bedside lamp at the left: her silhouette, enlarged, falls on the blue wall to the right and above her, together with the shadow of the device under her. In this frame the shadow is a big, soft, open human hand, palm up, fingers gently curved around her shadow, lifting her shadow up the wall as she nearly stands. Warm and comforting, not spooky: soft blurry edges, the wall around the shadows washed in warm amber lamplight. No text, no letters.
```

## S9h  (candidate `S9h_a.png`)
Input images, in order: S9b.png
```
Edit image 1. Keep the real scene EXACTLY as it is: her pose (sitting back on the raised seat, relieved), the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the back wall, cast by the warm bedside lamp at the left: her enlarged sitting silhouette falls on the blue wall to the right and above her, and beneath it the device's shadow is a big, soft, open human hand, palm up, cupping her shadow, so that her shadow rests safely in the palm. Warm and comforting, not spooky: soft blurry edges, the wall around the shadows washed in warm amber lamplight. The hand exists ONLY as a shadow on the wall, not as a real object. No text, no letters.
```

## G2  (candidate `G2_a.png`)
Input images, in order: S2_start.png
```
Edit image 1 into an expressive, slightly surreal comic exaggeration of how hard it feels to stand up, keeping the same grandmother (side view, sitting on the bed edge facing right, hands pressed on the mattress), the same hand-drawn ink-and-watercolour style and night colours. Exaggerate: the bed edge she sits on stretches out like the edge of a cliff; the floor below her slippers drops away into a deep, dark-blue gap far below, as if standing up meant climbing out of a canyon; the room tilts slightly; the bedroom door on the right is tiny and very far away across the floor. She looks small and uncertain, but the mood stays gentle, like a storybook, not scary. No text, no letters.
```

## E1  (candidate `E1_a.png`)
Input images, in order: C1.png (base_C1)
```
Edit image 1. Same bedroom, same framing, same hand-drawn ink-and-watercolour style, but now it is DAWN: soft early-morning light, pale gold and pale blue, coming through the window; the table lamp is off; the moon is gone and the sky outside is pale gold with a small bird sitting on the windowsill outside. The grandmother lies peacefully asleep in the bed under the white quilt, head on the pillow, a faint smile. Next to the bed, the device stands quietly and empty, its cream seat cushion back down level with the mattress, exactly as drawn. Calm, gentle. No text, no letters.
```

## Prompts for rejected attempts
Text-only C1 (device geometry came out wrong, candidates C1_a/b/c):
```
Style: a single comic panel from a gentle illustrated motion comic, in exactly the hand-drawn look and colours of image 2: clean ink outlines, soft watercolour washes with paper grain, flat soft colours, night palette of deep blue with a warm amber table-lamp glow. Nothing photorealistic, nothing 3D-rendered. Absolutely NO text, letters, numbers, speech bubbles, captions or sound-effect lettering anywhere in the image.
The grandmother is exactly the character in image 1 (and image 2): Chinese, about 78, slim, short grey-white hair, light-blue checked cotton pajamas, beige slippers.

The bedside sit-to-stand device, drawn simply but accurately as in the side-view line drawing (image 3): it stands ON THE FLOOR right against the side of the bed. A low grey steel base frame with a dark rubber footplate lies on the floor in front of the bed edge. A tall, frosted semi-transparent pale-grey housing with a slanted top stands on the base just behind her (on the far side, toward the head of the bed); faint diagonal rails are visible inside it. A small cream padded seat cushion sits on a carriage on those rails, right against the mattress edge, its top exactly level with the mattress top. A slim grey steel post rises from the front end of the base, and at its top a short black horizontal grip bar sticks out toward her, at about her chest height when she sits.

Panel C1, wide 16:9, a clean SIDE VIEW (like image 2 and the pose sketch in image 4): the same night bedroom as image 2 — the low bed with white quilt on the left, the nightstand with the glowing amber lamp at the far left, the moonlit blue window in the back wall, wooden floor. The device stands at the bed edge in the middle of the frame. The grandmother sits on the edge of the mattress, right next to the seat cushion, facing RIGHT in profile, hands resting on her knees, slippers on the dark footplate, calm and a little tired. Calm empty wall space in the upper right of the panel.
```
Layout passed as a passive reference (she was drawn facing the camera, candidates C1L_a/b):
```
Style: a single panel of a gentle illustrated motion comic, in exactly the hand-drawn look and colours of image 3: clean ink outlines, soft watercolour washes with paper grain, flat soft colours, night palette of deep blue with a warm amber table-lamp glow. Nothing photorealistic, nothing 3D-rendered. Absolutely NO text, letters, numbers, speech bubbles, captions or sound-effect lettering.
The woman is exactly the grandmother in image 2 and image 3: Chinese, about 78, slim, short grey-white hair, light-blue checked cotton pajamas, beige slippers.

Image 1 is a flat schematic LAYOUT in side view. Redraw it as the comic panel, keeping the exact position, size, angle and proportion of every element and the same camera:
- the pale block on the left = a low bed with a white quilt (mattress top at the same height);
- the small orange/cream block at the bed edge = a cream padded seat cushion, top level with the mattress, right against the mattress edge;
- the pale grey slanted panel with diagonal lines = a tall frosted, semi-transparent housing with a slanted top and faint diagonal rails inside, standing BEHIND her body (we see it through and around her);
- the thin grey pole with the black knob on top = a slim grey steel post with a short black grip bar at its top, in front of her;
- the flat grey strip on the floor = a low grey steel base with a dark rubber footplate under her feet;
- the beige stick figure = the grandmother, in exactly that pose.
Add the night bedroom around it, as in image 3: a nightstand with a glowing amber lamp at the far left behind the bed, a moonlit blue window in the back wall, wooden floor.

Panel C1 (wide, 16:9): she has just sat down at the bed edge next to the device, hands resting on her knees, calm, looking ahead. Leave calm empty wall space in the upper right.
```
C1 with her moved back onto the mattress (she stayed on the seat, candidates C1M_a/b):
```
Edit image 1. Keep the camera, framing, room, lamp, window, bed and the whole device exactly the same. Change only the grandmother's position: she sits about 15 cm further BACK, on the white mattress edge, so the front of the cream seat cushion in front of her hips is visible and empty. Hands on her knees, slippers resting on the dark footplate, calm. Same character as image 2, same hand-drawn ink-and-watercolour style. No text, no letters.
```
R3 made by editing the previous frame (too little seat motion, candidates R3_a/b/c):
```
Edit image 1. This is one frame of a flipbook animation: keep the camera, framing, room, lamp, window, bed, the device's floor base, footplate, frosted housing and steel post with its grip bar EXACTLY the same and in exactly the same place. Change only the grandmother's pose and the position of the cream seat cushion, to match the side-view schematic in image 2 (same framing; the orange block is the seat cushion, the beige stick figure is her). Same character as image 3, same hand-drawn ink-and-watercolour style. No text, no letters.

Stage (match the schematic): she is rising. The cream seat cushion has moved clearly FORWARD (to the right, away from the bed) and UP along the diagonal rails inside the housing, and is tilted forward about 9 degrees (front edge lower). It is still pressed under her buttocks and the backs of her thighs, carrying her. Her hips are noticeably higher than in image 1, her knees less bent, her torso leans forward over her feet, both hands gripping the grip bar on top of the post. There is now a visible gap between the seat and the mattress edge. Feet stay on the footplate.
```

# Correction and new-motif round
H3–H5 and S9h (shadow-hand motif) were replaced and kept in candidates/ as *_old_shadowhand.png. The old R5, R6, C5, E1 and C4 are kept as candidates/*_old.png.

## R5 (seat tilt fix, candidate fix/R5fix_a)
Input images: guide_R5.png (old R5 with a red 15° outline; in candidates/)
```
Edit image 1. The thin RED outline marks exactly where the cream padded seat cushion must be. Repaint the cream seat cushion (with its small bracket underneath that connects it to the diagonal rail of the frosted housing) so that it sits exactly inside the red outline: nearly flat, tilted only slightly, its front (right) edge a little lower than its back edge. Completely erase the old, steeply tilted cushion, repainting whatever was behind it (the woman's pajamas, the frosted housing, the bed, the wall) where it used to be. Then remove the red outline entirely. Keep everything else exactly unchanged: the woman, her pose, the room, the lamp, the bed, the rest of the device, the framing and the hand-drawn ink-and-watercolour style. No red lines and no text in the result.
```

## R6 (candidate fix/R6prof_a)
Input images: step 1: guide_R6.png with fix/p_seatfix.txt → R6fix_b; step 2: R6fix_b.png — step-2 prompt below; turned her to strict profile
```
Edit image 1. Keep everything exactly the same (room, lamp, bed, the whole device including the seat cushion position, framing, style), but turn the grandmother so she stands in a STRICT side profile facing RIGHT, upright and steady on the footplate, her right hand resting on the grip on top of the post, looking ahead to the right with a calm small smile. Same character. No text, no letters.
```

## C5 (candidate fix/C5fix_b)
Input images: guide_C5.png (red seat box + red post line)
```
Edit image 1. The thin RED outlines mark two corrections:
1) the small red box marks exactly where the cream padded seat cushion must be. Repaint the cream seat cushion (with its small bracket underneath that connects it to the diagonal rail of the frosted housing) so it sits exactly inside the box: nearly flat, tilted only slightly, its front (right) edge a little lower. Completely erase the old, steeply tilted cushion and repaint what was behind it.
2) the red vertical line with the small circle on top marks the slim grey steel post of the device, rising from the right end of the dark footplate, with a short black grip knob on top. Paint it there (it stands just behind her front leg).
Then remove all red lines. Keep everything else exactly unchanged: the woman stepping off the footplate, the room, lamp, bed, the rest of the device, the framing and the hand-drawn ink-and-watercolour style. No red lines and no text in the result.
```

## E1 step 1 (candidate fix/E1c_c)
Input images: E1_collage.png (old E1 with the R1 device region pasted in, brightened), R1.png — an earlier direct attempt, fix/p_E1fix.txt, failed (E1fix_*)
```
Edit image 1, a rough collage: the dark-blue rectangle in the middle was pasted in from a night scene of the same room (image 2 is that night scene). Repaint it into one seamless calm DAWN illustration in the hand-drawn ink-and-watercolour style:
- Remove the extra seated woman in the pasted area completely (the grandmother is the one asleep in the bed, keep her as she is).
- Keep the device from the pasted area exactly in shape and place: low grey steel base with dark rubber footplate on the floor, frosted semi-transparent pale-grey housing with slanted top and faint diagonal rails at the bed edge, cream padded seat cushion on its bracket, flat and level with the mattress top against the mattress edge, slim grey steel post at the front end of the base with the black grip knob on top. The seat is empty.
- Behind the device, continue the pale morning wall, the bed and quilt and the wooden floor naturally; repaint everything in soft pale-gold and pale-blue dawn light, no dark blue patch.
Keep the window with the bird, the lamp, the sleeping grandmother and the framing. No text, no letters.
```

## E1 step 2 = final (candidate E1p_a)
Input images: E1c_c.png, young_2d.png
```
Edit image 1. Keep everything exactly the same (dawn light, the sleeping smiling grandmother, the bed, the device, the window with the bird, the lamp, framing, style). Add only one detail: on the nightstand, next to the lamp, a small framed old sepia photograph of the young woman in image 2 (about 25, long single braid over one shoulder, smiling), and a single warm ray of morning sun from the window falling across the photo so it glows softly. No text, no letters.
```

## young_2d (candidate young_a)
Input images: character_2d.png
```
2D hand-drawn illustrated character model sheet, in exactly the same art style as image 1 (clean ink outlines, soft watercolour, paper texture). The character: the SAME woman as the grandmother in image 1, but about 50 years younger — around 25 years old, in the 1970s. Same face shape, same eyes, nose and gentle smile, so she clearly reads as the same person when young. Slim and upright, long black hair in a single braid worn over one shoulder, a simple 1970s light-coloured cotton blouse with a small collar, dark trousers, cloth shoes. Show her three times side by side on a plain warm off-white paper background: full body front view, full body side view (profile facing right, braid visible), and a head-and-shoulders portrait smiling. No text, no labels, no letters.
```

## D1 (candidate D1_b)
Input images: young_2d.png, S2_start.png
```
A close-up comic panel (16:9) in exactly the hand-drawn ink-and-watercolour style and night colours of image 2 (clean ink outlines, soft watercolour, paper grain, deep blue moonlight). The top of a small wooden nightstand at night, lit by cool moonlight from a window and a faint amber glow from a small bedside digital clock whose display reads exactly "03:07". On the nightstand: folded reading glasses, a glass of water, a small pill box, and a small framed old sepia photograph standing upright, showing the young woman from image 1 (about 25, long single braid over one shoulder, 1970s blouse) smiling, head and shoulders. The table lamp is off. Quiet, intimate, still. The only text anywhere is the clock display "03:07"; no other letters or numbers.
```

## D2 (candidate D2_a)
Input images: S2_start.png
```
A close-up comic panel (16:9) in exactly the hand-drawn ink-and-watercolour style and night colours of image 1 (clean ink outlines, soft watercolour, paper grain, deep blue night). Low angle on the wooden floor beside a low bed at night: a pair of beige cloth slippers placed neatly side by side, a stripe of pale moonlight from the window falling across them and the floorboards, the edge of a white duvet hanging down from the bed above. Quiet and still. No people. No text, no letters.
```

## Y3 step 1: young shadow (candidate Y3_a)
Input images: R3.png, young_2d.png
```
Edit image 1. Keep the real scene EXACTLY as it is: the old grandmother, her pose, the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the blue back wall behind her, cast by the warm bedside lamp at the left. The shadow is NOT her current old shape: it is the silhouette of her YOUNGER self from image 2 — a slim young woman of about 25 with a long single braid over one shoulder — rising from sitting, half up, leaning forward, hands reaching to a bar, upright and supple. The young silhouette moves with the same action as the real old woman, but looks light and effortless. It is clearly a shadow (flat, soft, dark, warm-tinted, no face details), the wall around it washed in warm amber lamplight; warm and tender, not spooky. No text, no letters.
```

## Y3 step 2 = final: add crane shadow (candidate Yc3_a)
Input images: Y3_a.png
```
Edit image 1. Keep EVERYTHING exactly as it is: the real old grandmother, the real device, the seat, the bed, the lamp, the room, the framing, the style, and the young braided shadow of her on the wall. Add only one more shadow on the wall, in the same soft shadow-play (piying) style, next to and slightly behind the young shadow: the shadow of the device has become an elegant red-crowned CRANE silhouette — its long slender neck follows the slanted rail of the device, one thin leg follows the diagonal link. In this frame the crane's head is still low, neck bent forward and down near the young woman's hips, as if beginning to lift her. Flat, soft-edged, warm-tinted shadow, poetic and tender, like a shadow-puppet duet; not spooky. No text, no letters.
```

## Y4 step 1: young shadow (candidate Y4_b)
Input images: R4.png, young_2d.png
```
Edit image 1. Keep the real scene EXACTLY as it is: the old grandmother, her pose, the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the blue back wall behind her, cast by the warm bedside lamp at the left. The shadow is NOT her current old shape: it is the silhouette of her YOUNGER self from image 2 — a slim young woman of about 25 with a long single braid over one shoulder — rising, more than half up, hips high, leaning forward lightly, hands on a bar, graceful and strong. The young silhouette moves with the same action as the real old woman, but looks light and effortless. It is clearly a shadow (flat, soft, dark, warm-tinted, no face details), the wall around it washed in warm amber lamplight; warm and tender, not spooky. No text, no letters.
```

## Y4 step 2 = final: add crane shadow (candidate Yc4_b)
Input images: Y4_b.png
```
Edit image 1. Keep EVERYTHING exactly as it is: the real old grandmother, the real device, the seat, the bed, the lamp, the room, the framing, the style, and the young braided shadow of her on the wall. Add only one more shadow on the wall, in the same soft shadow-play (piying) style, next to and slightly behind the young shadow: the shadow of the device has become an elegant red-crowned CRANE silhouette — its long slender neck follows the slanted rail of the device, one thin leg follows the diagonal link. In this frame the crane's neck is rising forward and up, its head lifting under the young woman's shadow, supporting her. Flat, soft-edged, warm-tinted shadow, poetic and tender, like a shadow-puppet duet; not spooky. No text, no letters.
```

## Y5 step 1: young shadow (candidate Y5_b)
Input images: R5 (fixed).png, young_2d.png
```
Edit image 1. Keep the real scene EXACTLY as it is: the old grandmother, her pose, the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the blue back wall behind her, cast by the warm bedside lamp at the left. The shadow is NOT her current old shape: it is the silhouette of her YOUNGER self from image 2 — a slim young woman of about 25 with a long single braid over one shoulder — nearly standing, legs straight, body almost upright, light as a dancer, one hand on a bar, the braid starting to swing. The young silhouette moves with the same action as the real old woman, but looks light and effortless. It is clearly a shadow (flat, soft, dark, warm-tinted, no face details), the wall around it washed in warm amber lamplight; warm and tender, not spooky. No text, no letters.
```

## Y5 step 2 = final: add crane shadow (candidate Yc5_b)
Input images: Y5_b.png
```
Edit image 1. Keep EVERYTHING exactly as it is: the real old grandmother, the real device, the seat, the bed, the lamp, the room, the framing, the style, and the young braided shadow of her on the wall. Add only one more shadow on the wall, in the same soft shadow-play (piying) style, next to and slightly behind the young shadow: the shadow of the device has become an elegant red-crowned CRANE silhouette — its long slender neck follows the slanted rail of the device, one thin leg follows the diagonal link. In this frame the crane's neck is raised high and forward, its head near the young woman's waist, both rising together gracefully. Flat, soft-edged, warm-tinted shadow, poetic and tender, like a shadow-puppet duet; not spooky. No text, no letters.
```

## Y6 step 1: young shadow (candidate Y6_a)
Input images: R6 (fixed).png, young_2d.png
```
Edit image 1. Keep the real scene EXACTLY as it is: the old grandmother, her pose, the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the blue back wall behind her, cast by the warm bedside lamp at the left. The shadow is NOT her current old shape: it is the silhouette of her YOUNGER self from image 2 — a slim young woman of about 25 with a long single braid over one shoulder — standing tall and perfectly straight, chin up, one hand lightly on a bar, the braid swinging behind her shoulder, full of life. The young silhouette moves with the same action as the real old woman, but looks light and effortless. It is clearly a shadow (flat, soft, dark, warm-tinted, no face details), the wall around it washed in warm amber lamplight; warm and tender, not spooky. No text, no letters.
```

## Y6 step 2 = final: add crane shadow (candidate Yc6_b)
Input images: Y6_a.png
```
Edit image 1. Keep EVERYTHING exactly as it is: the real old grandmother, the real device, the seat, the bed, the lamp, the room, the framing, the style, and the young braided shadow of her on the wall. Add only one more shadow on the wall, in the same soft shadow-play (piying) style, next to and slightly behind the young shadow: the shadow of the device has become an elegant red-crowned CRANE silhouette — its long slender neck follows the slanted rail of the device, one thin leg follows the diagonal link. In this frame the crane stands tall with its neck raised fully upright, head high, beside the standing young woman, both proud and serene. Flat, soft-edged, warm-tinted shadow, poetic and tender, like a shadow-puppet duet; not spooky. No text, no letters.
```

## Y9 step 1: young shadow (candidate Y9_a)
Input images: S9b.png, young_2d.png
```
Edit image 1. Keep the real scene EXACTLY as it is: the old grandmother, her pose, the device, the seat cushion position, the bed, the lamp, the room, the framing and the hand-drawn ink-and-watercolour style. Add only a large, soft-edged shadow on the blue back wall behind her, cast by the warm bedside lamp at the left. The shadow is NOT her current old shape: it is the silhouette of her YOUNGER self from image 2 — a slim young woman of about 25 with a long single braid over one shoulder — sitting down calmly on a seat, back straight, chin up, hands resting lightly on a bar, patient and serene, as if saying 'take your time'. The young silhouette moves with the same action as the real old woman, but looks light and effortless. It is clearly a shadow (flat, soft, dark, warm-tinted, no face details), the wall around it washed in warm amber lamplight; warm and tender, not spooky. No text, no letters.
```

## Y9 step 2 = final: add crane shadow (candidate Yc9_b)
Input images: Y9_a.png
```
Edit image 1. Keep EVERYTHING exactly as it is: the real old grandmother, the real device, the seat, the bed, the lamp, the room, the framing, the style, and the young braided shadow of her on the wall. Add only one more shadow on the wall, in the same soft shadow-play (piying) style, next to and slightly behind the young shadow: the shadow of the device has become an elegant red-crowned CRANE silhouette — its long slender neck follows the slanted rail of the device, one thin leg follows the diagonal link. In this frame the crane stands calmly beside the seated young woman's shadow, neck gently curved, quietly keeping her company. Flat, soft-edged, warm-tinted shadow, poetic and tender, like a shadow-puppet duet; not spooky. No text, no letters.
```

## F_worry (candidate F_worry_b; 4:3; light paper border auto-cropped)
Input images: character_2d.png, R1.png
```
A close-up comic panel (4:3) in exactly the hand-drawn ink-and-watercolour style of image 2 (clean ink outlines, soft watercolour, paper grain). The grandmother from image 1 (Chinese, about 78, short grey-white hair, light-blue checked pajamas) — keep her face exactly on-model, warm and gentle, natural, not uncanny. Night, deep blue moonlight: she lies in bed, head on the pillow, eyes open, glancing sideways with a quiet worried look toward a faint amber clock glow at the edge of the frame. No text, no letters, no numbers.
```

## F_struggle (candidate F_struggle_b; 4:3; light paper border auto-cropped)
Input images: character_2d.png, R1.png
```
A close-up comic panel (4:3) in exactly the hand-drawn ink-and-watercolour style of image 2 (clean ink outlines, soft watercolour, paper grain). The grandmother from image 1 (Chinese, about 78, short grey-white hair, light-blue checked pajamas) — keep her face exactly on-model, warm and gentle, natural, not uncanny. Night, warm amber lamp light from the left: sitting on the bed edge, she presses her lips together, eyebrows tense with effort; her hand pressed on the white mattress is trembling (tiny motion lines). No text, no letters.
```

## F_curious (candidate F_curious_b; 4:3; light paper border auto-cropped)
Input images: character_2d.png, R1.png
```
A close-up comic panel (4:3) in exactly the hand-drawn ink-and-watercolour style of image 2 (clean ink outlines, soft watercolour, paper grain). The grandmother from image 1 (Chinese, about 78, short grey-white hair, light-blue checked pajamas) — keep her face exactly on-model, warm and gentle, natural, not uncanny. Night, warm lamp light: she looks at something new beside her bed for the first time — the softly blurred frosted housing and cream seat cushion of the device at the edge of the frame — with a curious, slightly surprised, open look, head tilted a little. No text, no letters.
```

## F_press (candidate F_press_a; 4:3; light paper border auto-cropped)
Input images: character_2d.png, R1.png
```
A close-up comic panel (4:3) in exactly the hand-drawn ink-and-watercolour style of image 2 (clean ink outlines, soft watercolour, paper grain). The grandmother from image 1 (Chinese, about 78, short grey-white hair, light-blue checked pajamas) — keep her face exactly on-model, warm and gentle, natural, not uncanny. Night: a determined look, lips together, eyes lowered to her thumb pressing a round button on a black grip bar in the foreground; the button glows warm amber, lighting her face softly from below. No text, no letters.
```

## F_rise (candidate F_rise_a; 4:3; light paper border auto-cropped)
Input images: character_2d.png, R1.png
```
A close-up comic panel (4:3) in exactly the hand-drawn ink-and-watercolour style of image 2 (clean ink outlines, soft watercolour, paper grain). The grandmother from image 1 (Chinese, about 78, short grey-white hair, light-blue checked pajamas) — keep her face exactly on-model, warm and gentle, natural, not uncanny. Night, warm lamp light: rising from sitting, both hands on a black grip bar, she breaks into a small surprised smile, eyes widening a little, as if 'oh — this is easy'. No text, no letters.
```

## F_proud (candidate F_proud_a; 4:3; light paper border auto-cropped)
Input images: character_2d.png, R1.png
```
A close-up comic panel (4:3) in exactly the hand-drawn ink-and-watercolour style of image 2 (clean ink outlines, soft watercolour, paper grain). The grandmother from image 1 (Chinese, about 78, short grey-white hair, light-blue checked pajamas) — keep her face exactly on-model, warm and gentle, natural, not uncanny. Night, warm lamp light: standing upright, a quiet small proud smile, chin slightly up, eyes calm and bright. No text, no letters.
```

## F_sleep (candidate F_sleep_b; 4:3; light paper border auto-cropped)
Input images: character_2d.png, R1.png
```
A close-up comic panel (4:3) in exactly the hand-drawn ink-and-watercolour style of image 2 (clean ink outlines, soft watercolour, paper grain). The grandmother from image 1 (Chinese, about 78, short grey-white hair, light-blue checked pajamas) — keep her face exactly on-model, warm and gentle, natural, not uncanny. Dawn, soft pale-gold morning light: she sleeps peacefully on the pillow under the white quilt, eyes closed, a gentle smile. No text, no letters.
```

## M2m (candidate M2m_a; 1:1)
Input images: mech_refs/M2.png
```
Edit image 1, a precise side-view drawing of a seat-lifting mechanism (pale block at left = bed edge; the slanted rail; the cream seat on a carriage; a thin diagonal link down to a floor pivot; a pale housing behind; floor strip). Keep every line exactly where it is, same framing, same warm paper. Turn it gently toward Chinese ink-wash painting: add only a few loose, expressive black ink brush strokes that echo the rail and the link (a soft dry-brush stroke along the rail, a light wash shadow under the seat), a little ink bleed on the paper. It must still clearly be the mechanism. No text, no letters, no seals with characters.
```

## M3m (candidate M3m_a)
Input images: mech_refs/M3.png, M2m
```
Edit image 1, a precise side-view drawing of the seat-lifting mechanism in its next position (pale block at left = bed edge; slanted rail; cream seat on its carriage; thin diagonal link down to a floor pivot; pale housing; floor strip). Keep the framing and the positions of the rail, seat, link and pivot exactly as in image 1. Paint it in the same ink-wash style as image 2 (the previous frame of this morph), continuing the transformation one step further: soft ink-wash feathers start to grow along the slanted rail, and the thin link is brushed like a slender bird's leg with a delicate joint. It is still mostly a mechanism. Warm paper, no text, no letters.
```

## M4m (candidate M4m_b)
Input images: mech_refs/M4.png, M3m
```
Edit image 1, a precise side-view drawing of the seat-lifting mechanism in its next position (pale block at left = bed edge; slanted rail; cream seat on its carriage; thin diagonal link down to a floor pivot; pale housing; floor strip). Keep the framing and the positions of the rail, seat, link and pivot exactly as in image 1. Paint it in the same ink-wash style as image 2 (the previous frame of this morph), continuing the transformation one step further: now it is half mechanism, half crane: the slanted rail is clearly a long feathered neck, and a crane's head with a long beak is forming at its top, near the seat; the link is a thin crane leg; some mechanical lines still show through faintly. Warm paper, no text, no letters.
```

## M5m (candidate M5m_b)
Input images: mech_refs/M5.png, M4m
```
Edit image 1, a precise side-view drawing of the seat-lifting mechanism in its next position (pale block at left = bed edge; slanted rail; cream seat on its carriage; thin diagonal link down to a floor pivot; pale housing; floor strip). Keep the framing and the positions of the rail, seat, link and pivot exactly as in image 1. Paint it in the same ink-wash style as image 2 (the previous frame of this morph), continuing the transformation one step further: the transformation is complete: a full, elegant Chinese ink-wash red-crowned crane stands posed along the same lines — its long neck raised along the direction of the rail, its head high near where the seat was, one slender leg along the line of the link down to the floor pivot point, wings folded, a small red crown on its head. Only faint ghost lines of the mechanism remain. Same warm paper, same framing. No text, no letters, no seals.
```

C4: the old C4 with its paper border cropped off by script (no new generation).
