# AI shots — prompts and takes (2D hand-drawn style)

Scope after the user's second change of direction: only S1, S2 and S10, in a 2D hand-drawn illustrated storybook style.
Keyframes: `gemini-3-pro-image` (generateContent, 16:9, 1376x768). Video: `gemini-omni-flash-preview` (interactions API), image-to-video; the input frame was the keyframe scaled to 1280x720 JPEG (`keyframes/vin/`).

## Character sheet → `keyframes/character_sheet_2d.png` (= `keyframes/character_2d.png`)
Model gemini-3-pro-image, text only. Chosen: candidate `char_gemini-3-pro-image_a` (other 3 candidates in `keyframes/candidates/`).
```
2D hand-drawn illustrated character model sheet for an animated short film, storybook look: flat soft colours with a subtle paper / gouache texture, clean thin ink-like outlines, simple appealing shapes. Nothing photorealistic, nothing 3D-rendered.

The character: a friendly, gentle Chinese grandmother, about 78 years old, slim and slightly stooped, short grey-white hair, kind lined face, wearing light-blue checked (gingham) long-sleeved cotton pajamas with long trousers and pale beige slippers.

Show the same character three times side by side on a plain warm off-white paper background: full body front view, full body side view (profile, facing right), and full body back view. Same proportions and colours in all three. No text, no labels, no letters, no numbers, no colour swatches.
```

## S2 keyframe → `keyframes/S2_start.png`
gemini-3-pro-image, refs: [character sheet]. (A first batch of 4 calls failed with HTTP 429 spend-rate errors; this was the retry.)
```
A single frame from a 2D hand-drawn illustrated animated short film, storybook look: flat soft colours with a subtle paper / gouache texture, clean thin ink-like outlines, simple shapes. Night palette of deep blues with warm amber lamp light. Nothing photorealistic, nothing 3D-rendered. 16:9.

The grandmother from image 1 (same face, short grey-white hair, light-blue checked pajamas, beige slippers — keep her design exactly).

A clean, simple SIDE VIEW (profile) of a modest Chinese bedroom at night: a plain LOW double bed with a white quilt and a pale pillow on the left half of the frame, seen exactly from the side; a small wooden nightstand at the head end with a little warm amber table lamp glowing; a window in the back wall with deep blue moonlight; plain wooden floor. No other furniture next to the bed.

She sits on the edge of the bed, facing RIGHT, in clean profile: her hands pressed on the mattress beside her hips, her slippers flat on the floor, knees bent, looking a little tired, about to try to stand up. Simple, uncluttered composition with empty floor space to the right of her. No text, no letters, no numbers.
```

## S1 keyframes → `keyframes/S1_start_a.png`, `keyframes/S1_start_b.png`
gemini-3-pro-image, refs: [character sheet, S2_start.png]. Two runs of the same prompt.
```
A single frame from a 2D hand-drawn illustrated animated short film, storybook look: flat soft colours with a subtle paper / gouache texture, clean thin ink-like outlines, simple shapes. Night palette of deep blues with warm amber accents. Nothing photorealistic, nothing 3D-rendered. 16:9.

The same modest Chinese bedroom as in image 2 (same bed, quilt, nightstand, lamp, window and colours), now dark: the table lamp is OFF, the room is lit only by cool deep-blue moonlight through the window. On the nightstand in the left foreground stands a small bedside digital alarm clock whose display glows soft amber and reads exactly "03:07". Behind it, in the low bed, the grandmother from image 1 (same face, short grey-white hair, light-blue checked pajamas) lies asleep on her back under the white quilt, head on the pillow. Quiet, still, calm. The only text in the image is the clock display "03:07"; no other letters or numbers.
```

## S10 keyframes → `keyframes/S10_start_a.png`, `keyframes/S10_start_b.png`
gemini-3-pro-image, refs: [character sheet, S2_start.png]. Two runs of the same prompt.
```
A single frame from a 2D hand-drawn illustrated animated short film, storybook look: flat soft colours with a subtle paper / gouache texture, clean thin ink-like outlines, simple shapes. Night palette of deep blues with warm amber light. Nothing photorealistic, nothing 3D-rendered. 16:9. Same art style and colours as image 2.

A dim, narrow hallway of a modest Chinese apartment at night, seen from behind the walker, looking down the hallway. Deep blue shadows on the walls and wooden floor. At the far end, low on the wall beside a half-open bathroom door, a small plug-in night light glows warm amber and casts a soft pool of light on the floor.

The grandmother from image 1 (same short grey-white hair, light-blue checked pajamas, beige slippers — keep her design exactly) is seen from behind, in the middle distance, walking slowly and steadily down the hallway toward the night light, upright and calm. No text, no letters, no numbers.
```

## Videos
| take | input frame(s) | prompt | result |
|---|---|---|---|
| **S1.mp4** (chosen) | S1_start_b | V-S1 | ok |
| variants/S1_alt_t1.mp4 | S1_start_a | V-S1 | ok, alternate |
| **S2.mp4** (chosen) | S2_start | V-S2-1img | ok |
| (none) | S2_start as first and last frame | V-S2-2img | failed: "upstream request failed" ×3 |
| **S10.mp4** (chosen) | S10_start_a | V-S10 | ok |
| (none) | S10_start_b | V-S10 | failed: project monthly spending cap reached |

V-S1:
```
5 second 2D hand-drawn animation in exactly the art style of the image: flat soft colours, paper/gouache texture, clean ink outlines, gentle limited animation, no 3D. Night, deep blue moonlight. The camera drifts slowly from the glowing bedside clock toward the bed. The grandmother opens her eyes, pauses, then slowly and carefully pushes herself up with her hands and sits up in bed. The clock keeps showing 03:07. Quiet night ambience only, no music, no speech, no added text.
```
V-S2-1img:
```
7 second 2D hand-drawn animation in exactly the art style of the images: flat soft colours, paper/gouache texture, clean ink outlines, gentle limited animation, no 3D. Static side-view camera. The grandmother sitting on the edge of the low bed presses both hands on the mattress and tries to stand up. She rises slowly to about halfway, her knees tremble, her legs wobble and she sways, then she drops heavily back down onto the bed edge, tired. It ends with her sitting on the bed edge in side view. Quiet room tone, a soft sigh, no music, no speech, no added text.
```
V-S2-2img (no output):
```
7 second 2D hand-drawn animation in exactly the art style of the images: flat soft colours, paper/gouache texture, clean ink outlines, gentle limited animation, no 3D. Static side-view camera. Image 1 is the first frame and image 2 is the last frame. The grandmother sitting on the edge of the low bed presses both hands on the mattress and tries to stand up. She rises slowly to about halfway, her knees tremble, her legs wobble and she sways, then she drops heavily back down onto the bed edge, tired. It ends with her sitting on the bed edge in side view, as in the last frame. Quiet room tone, a soft sigh, no music, no speech, no added text.
```
V-S10:
```
6 second 2D hand-drawn animation in exactly the art style of the image: flat soft colours, paper/gouache texture, clean ink outlines, gentle limited animation, no 3D. Static camera. The grandmother walks slowly and steadily away from the camera down the dim hallway toward the small warm night light, calm and upright, with gentle natural steps. Soft footsteps and quiet night ambience, no music, no speech, no added text.
```

## Earlier, discarded photorealistic pass (in `variants/old/`)
Before the style changes I made photoreal bible frames (room + device from `3d_a_shell.png`, grandmother, a side view of her sitting on the seat holding the bar, a standing frame with the seat raised, and a close-up of the hands on the bar). I also ran two video tests:
- `test_photoreal_i2v_1img.mp4`: one start frame; prompt "A 4 second video: the woman slowly looks up. Static camera."
- `test_photoreal_i2v_2img.mp4`: start frame `S7_start` and end frame `S10_start`; prompt "A 6 second video. The first image is the first frame and the second image is the last frame. The woman slowly stands up. Static camera." This one shows that start and end frame conditioning works.
The long photoreal S7 rise prompt (~900 characters, about the seat moving forward, up and tilting under her buttocks and thighs) returned "upstream request failed" every time, with one image and with two. I deleted the photoreal prompt text files during cleanup, so only this summary remains.

## Retake round (coordinator request: S10 walk forward and centred; S2 ending in strict profile)
Keyframes (gemini-3-pro-image):
- `keyframes/S2_profile_end.png`: an edit of S2_start.png (candidate k3_s2end_a; b is in candidates/). Prompt:
```
Edit image 1. Keep the same room, camera, art style, colours and the same grandmother exactly. Change only her pose: she sits on the bed edge in a STRICT side profile facing right (shoulders, hips and face exactly side-on to the camera), slumped and tired after a failed attempt to stand: back slightly rounded, head bowed, both hands resting on her knees, slippers flat on the floor. No text.
```
- `keyframes/S10c_start.png`: refs [character_2d.png, S2_start.png] (candidate k3_s10a_d). With S10_start_a.png as the ref (k3_s10a_a/b) the model copied the old off-centre framing, so I rejected those. Prompt:
```
A single frame from a 2D hand-drawn illustrated animated short film, in exactly the art style and colours of image 2: flat soft colours, subtle paper / gouache texture, clean thin ink-like outlines, deep-blue night palette with warm amber light. Nothing photorealistic, nothing 3D. 16:9.

Symmetrical one-point-perspective view straight down a long, dim, narrow hallway of a modest Chinese apartment at night, the vanishing point in the centre of the frame. Walls on both sides fill only the edges of the frame. At the far end of the hallway, about 5 metres away, a small plug-in night light low on the wall beside a half-open bathroom door glows warm amber and casts a soft pool of light on the wooden floor.

The grandmother from image 1 (same short grey-white hair, light-blue checked pajamas, beige slippers — keep her design exactly) is seen from behind, CENTRED in the frame and in the FOREGROUND near the camera (her figure about half the frame height), starting to walk down the hallway toward the night light. No text, no letters, no numbers.
```
- `keyframes/S10c_end.png`: an edit of S10c_start.png (candidate k3_s10end_b; I rejected a because the framing changed). Prompt:
```
Edit image 1. Keep the same hallway, camera, art style, colours, lighting and the same grandmother exactly. Change only her position: she has walked far down the hallway and is now near its far end, a few steps from the glowing night light, seen from behind, small in the frame, still upright and calm, mid-step. No text.
```
Video prompts. Nothing was produced: all 5 calls failed on the daily 20-request quota.
- S10 two-image (S10c_start → S10c_end), two takes planned: `6 second 2D hand-drawn animation, same art style as the images, no 3D. Static camera. Image 1 is the first frame, image 2 is the last frame. The grandmother walks steadily and calmly down the hallway, away from the camera, toward the warm night light. Quiet footsteps, no music, no speech, no text.`
- S10 one-image (S10c_start), one take planned: `6 second 2D hand-drawn animation, same art style as the image, no 3D. Static camera. The grandmother walks steadily and calmly all the way down the hallway, away from the camera, and reaches the warm night light at the far end. Quiet footsteps, no music, no speech, no text.`
- S2_profile two-image (S2_start → S2_profile_end), two takes planned: `7 second 2D hand-drawn animation, same art style as the images, no 3D. Static side camera. Image 1 is the first frame, image 2 is the last frame. She pushes on the mattress and rises halfway, her knees tremble and wobble, then she drops back down onto the bed edge and slumps, tired, in side profile. Quiet room tone, a soft sigh, no music, no text.`
