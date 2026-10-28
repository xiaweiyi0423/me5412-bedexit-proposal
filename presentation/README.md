# Presentation draft (Chinese)

**10/28, deck v6 (15-minute version):** 19 main slides (cover, 46 s film, agenda, 15 content pages, team) at about 15 min by the talk guide's estimate; concept, cantilever, speed, fall_exit and nextsteps moved to the appendix; problem + users and sensing + speed merged; prior-art and comparison pages carry side-view pictograms (`assets_v6/`); the motion and sensing pages loop clips from the film. Published deck: https://claude.ai/artifact/FkeDBuTMtDLJvWpUHrZL4p · talk guide: https://claude.ai/artifact/7Qmsv5uJLjYDeoM6FvR7qh

- `deck.json` + `slides/*.html`: 21-slide class-presentation structure (19 main slides, appendix index, consultation-only questions slide). Unfinished parts are marked "待补" on the slides. Speaker notes are in each slide's `<aside>`.
- `animations/`: stick-figure demo GIFs (`use_sequence.gif`, `safety_sitback.gif`) and the script that draws them (`make_gifs.py`). They are schematics, not CAD.
- `tools/talk_guide.html`: interactive speaker guide (to-do list, pick slides, time estimate, per-slide script and Q&A), built by `build_guide2.py`.

Images in the slides reference uploaded blobs (`/_blob/<id>`); the calculation figures come from `model/calc_v12/` and the schematic drawings from `plan/figs.py`.
