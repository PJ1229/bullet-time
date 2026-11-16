# Hockey × Prospect — Transitions v2 (inspo-driven, B&W)

Timeline `prospect_v3_cut` · 1920×1080 · 23.976 · beat ≈ 12f · bars at tl 0/48/96/142/192(DROP)/239/287/335/384/431/479.
Check render: `06_deliverables/checks/check_full_v5_transitions.mp4` (H264 + audio). Frame sheet: `checks/v5_inspo_sheet.jpg`.

**Scope (PJ):** lightning lives ONLY on the Horcoff goal, tl 96–204 (V1 locked + V2 `lightning_tl_[0096-0199]`, owned by the main thread).
Every other cut uses the inspo grammar from `hockey_inspo_95283.mp4` + `usc_football_hype_2024.mp4`: whips, white/black flash frames,
speed-ramp blur, zoom punches, pushes, speed-blur push-ins, shake on hits, match cuts. All B&W, no cartoon/comic/halftone. Clips play forward, each used once.

## How it's built
- Resolve scripting can't keyframe Zoom/Position, add OFX blurs or shake. So the FX are **baked**: clean B&W timeline render
  (`checks/clean_v5_base2.mov`, ProRes 422 HQ, V3 empty) → `03_graphics/inspo-transitions/tools/bake_inspo.py` → opaque frames
  `03_graphics/inspo-transitions/bake_v1/fx_tl_%04d.png` → **V3 "FX_inspo"**, 8 clips, Normal composite, CDL sat 0.
- ⚠️ Baked frames carry the current V1 grade. If V1 grade/trim changes in 0–95 or 204–466: re-render the clean base, rerun
  `bake_inspo.py 0 250` and `bake_inspo.py 251 478` into a NEW folder (bake_v2), re-import on V3. V3 never touches tl 96–203.
- SFX from the existing `02_audio/sfx` library. Whoosh slices are taken from measured events in the 20-whoosh compilation so each peaks on its cut.
  New tracks: A8 `INSPO_whoosh`, A9 `INSPO_clicks`. Electric SFX (A5–A7) kept only inside the goal.

## Per cut
| tl (peak) | OUT → IN | Visual (V3 baked) | Audio cue |
|---|---|---|---|
| 0 | black → A1 tunnel | 3f fade up from black (0–2) | Low Boom (A2, existing) |
| 48 | A1 → A2 #71 | slow push 1.00→1.06 into the M (24–47), 2f horizontal whip-blur out (46–47), whip lands + 45% white pop (48–49) | whoosh evt@141 (A8 42–54) + Shutter Click moved to 43 so its peak hits 48 (A9) |
| 96 | A2 #71 → goal | push 1.00→1.05 on #71 (88–95) + 3f **upward** whip blur (93–95) into the faceoff tilt | whoosh evt@355 (A8 90–97) → electric charge-up 96 (A6) |
| 96–204 | **GOAL — lightning (locked, main thread)** | — | charge-up 96–106 (A6, −9), zap 106 (A5, −10), crackle bed 106–142 (A6, −14), big strike 191 (A7, −8) + existing riser/flash/sub drop/impact |
| 204 | goal → speed ramp | motion blur ramping 8→70px→8 across the ramp (204–214) | Short Swoosh re-placed src 6–21 (A3 204–219, peak ≈213; old slice cut off before its peak) |
| 215 | ramp → B1c #44 | **zoom punch** 1.0→1.4 in 4f on #44 + radial blur + 50% white frame on 215, hold/track #44 to 238 | Shutter Click peak 215 (A9 210) under the ringing Cinematic Impact |
| 239 | B1c → B2 big hit | 2f whip blur out of B1c (237–238), **USC speed-blur push-in** 1.08→1.0 with radial blur (239–241) | whoosh evt@659 (A8 232–246) |
| 264 | (in B2) contact | **shake** 7f decaying (264–270, 1.05 overscan, directional blur on first 2f) + 40% white hit frame | Cinematic Impact 264 (A2, existing) |
| 287 | B2 → B3 | **match cut** on the BELFOR board line + 3f punch-out 1.07→1.0 + 25% white | Shutter Click peak 287 (A9 282) |
| 311 | (in B3) | zoom punch 1.0→1.15 into the crease scramble, held to 334 + 30% white (replaces the old colour switch — edit is B&W) | Shutter, Satisfying 311 (A3, existing) |
| 335–371 | flash-cut run (6f each) | each cut: 3f punch-out 1.06→1.0; first frame alternates **white 35% / black 50%** flash frame | Fast Clicks 335–362 (existing) + 2nd Fast Clicks slice 362–384 (A3) |
| 384 | F8 → B5 HORCOFF 44 | push 1.0→1.25 into the "9" on F8 (377–383) with radial blur building, cut to giant "44" with radial blur decaying (384–386) + 40% white | whoosh evt@885 (A8 378–390) + Shutter Click peak 384 (A9 379) |
| 431 | B5 → B6 fans | **whip pan** R→L: blur 40→85 out (429–430), 70→28 in (431–432); reverse cut players→fans | whoosh evt@1098 (A8 426–438) |
| 431–466 | B6 fans | slow push 1.00→1.05, accelerating to 1.15 (458–466) into the puck→lens | whoosh 455–467 (A3, existing) |
| 467 | B6 → CG puck→lens | V1 467–479 empty — main thread's CG | Low Boom 467 (A2, existing) |

## API notes
- `Timeline.DeleteClips(items, False)` silently returns None and deletes nothing in Resolve 21.2; call `DeleteClips(items)`.
- Audio volume property is `AudioVolume` (dB), not `Volume`.
- Image-seq placement: startFrame=a, endFrame=b+1 (sequence numbering).

## Eyeball list for PJ
1. 215 punch: 1.4× on #44 is soft-ish from the 1080 render; if it reads soft, bake from source 4K instead.
2. Whip strengths at 238 and 430–431 are heavy (inspo-level); dial down in `bake_inspo.py` if too much.
3. White/black flash-frame alternation in the 335–371 run.
4. 384: "9"→"44" number match (F8 has no #44 in frame).
