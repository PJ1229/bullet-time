# Bullet Time

PJ Kim's Michigan hockey hype edit, cut to "Prospect" (ft. Lil Baby): 16:9, 23.976 fps, 527 frames (~22 s).

- **Built agentically:** Claude drove DaVinci Resolve Studio, Blender and Python.
- **PJ directed and grades.**
- **This repo holds the pipeline code and notes.** Footage, renders and .blend files stay on the TOSHIBA EXT drive under `um-athletics/hockey-edit/`.

## What's in the edit
- **Horcoff goal (tl 96–204):**
  - lightning charge-up on the shooter;
  - the bolt leaves the blade;
  - a Blender bullet-time orbit around the goalie, inside the real arena model;
  - a restrike back to the plate and the score hit.
- **Big hit (256–280):** charge on #17, then one strike at contact, held with restrikes.
- **Transitions:**
  - an LED dot-matrix depth map (Depth Anything V2) with a wave and a wiggle, and a lightning strike on the snap;
  - a depth-parallax orbit push.
- **Ending:**
  1. Fans drop into the LED depth field.
  2. The official Block M rises out of it.
  3. Lightning strikes it, and it freezes, goes flat and turns maize with a navy outline.
- **Everything is delivered in S-Log3 / S-Gamut3.Cine** so PJ grades it all at the end.

## Layout
| Path | What |
|---|---|
| `graphics/puck-lightning/tools/lightning_v5.py` | The reference lightning model (core, bloom, spill, reflection), added in scene-linear to the log plate |
| `graphics/puck-lightning/tools/fx_v2.py` | Goal FX: push-in, frost, anamorphic streaks, shake, shockwave |
| `graphics/impact-lightning/tools/impact_lightning.py` | Big-hit lightning |
| `graphics/inspo-transitions/tools/bake_v5_transitions.py` | Depth transitions + the ending (current) |
| `graphics/master_v4/assemble.py`, `preview.py` | Build the log master (top layer per frame) and the test-grade preview |
| `graphics/tools/` | EXR → S-Log3, EXR viewers |
| `notes/STORYBOARD_v3_PROSPECT.md` | The running changelog of every version |
| `LEARNINGS.md` | What worked, what PJ rejected, Resolve/Blender gotchas |

## Rebuild
1. Run the effect scripts; each writes 16-bit S-Log3 PNG sequences next to the media on the drive.
2. Run `python3 graphics/master_v4/assemble.py ~/links v13 goal_fx_log_v7`.
3. Encode ProRes 4444 XQ in parallel chunks and concat with `-c copy`. Take the audio from a Resolve render of the current timeline (`prospect_v5_cut`).
