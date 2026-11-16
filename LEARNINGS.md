# Bullet Time (Michigan hockey × "Prospect") — what we learned (Nov 15–16, 2026)

A personal 16:9, 23.976 Michigan hockey hype edit, cut to "Prospect" (ft. Lil Baby).
- Claude drove DaVinci Resolve, Blender and Python.
- PJ directed and grades.
- Media stays on the TOSHIBA (`um-athletics/hockey-edit/`); this folder holds the code and docs.

## 1. Pipeline rules that held up
- **Everything in S-Log3, PJ grades at the end.** CG, lightning and transitions are all built as decode log → edit in scene-linear → re-encode log (16-bit PNG / ProRes 4444 XQ). Only the previews get a throwaway test grade (`view709.py`). No B&W, no "tasteful" grade from Claude.
- **Once PJ starts grading V1, a Resolve render is no longer log.** Build the deliverable from the ungraded log base plus log patches:
  - `master_v4/assemble.py`: top layer per frame wins;
  - then encode ProRes 4444 XQ in parallel 66-frame chunks and concat with `-c copy`;
  - take the audio from a Resolve render.
- **Version everything** (timelines `prospect_v3_cut`, `v4`, `v5`; render folders `_vNN`). Never overwrite.
- **Previews for chat:** H.264 yuv420p faststart, ≤ ~15 MB (720p crf 23). `mp4v` shows as a frozen frame.

## 2. Lightning (the look PJ loves = the first goal shot)
- **Reference for every future bolt:** `puck-lightning/tools/lightning_v5.py`.
- **Light model:** additive scene-linear layers:
  - white-hot core;
  - pink, then red, bloom at three radii;
  - spill = energy × plate albedo;
  - optional ice reflection and white flash.
- **Path:** stepped-leader random walk with branching. Geometry holds for 2 frames; flicker is per frame.
- **Grammar:**
  1. Charge builds **on the person** (arcs on their silhouette).
  2. One strike at the moment of impact.
  3. The same channel holds, with restrikes.
  4. Crackle decays.

  Arcs that trace every outline read as neon, so use them sparingly.
- **Masking:** depth and person occlusion; netting via a black-hat filter.
  - rembg fails through glass and netting; colour keys work better (maize jersey + navy).
  - Arcs only where depth jumps sharply: filter contour points by depth gradient, and never along the frame border or a floor depth band.
- **Rejected:**
  - sparks;
  - lightning on every play (kept: goal + big hit + transition strikes);
  - red discs;
  - pink full-frame flashes.

## 3. Blender in log
- **Footage textures:** Non-Color → `SLog3ToLinear` → Emission. Render EXR, then `exr_to_slog3.py`.
- **Camera solve** from goal posts; the real freeze frame is projected onto the 3D arena.
- **Fixes that mattered:**
  - a fine-mesh net;
  - crowd and ad textures from real frames;
  - DOF and motion blur keyed sharp at the joins;
  - grain matched to the footage;
  - quaternion sign-flip fix (one frame smeared through a 360° spin);
  - hard CG→plate switch hidden under a lightning restrike (no ghost dissolve).
- **Downloaded models need cleanup:** two goals, emissive faceoff dots (find them by ray-casting from the camera through the bad pixel).
- **Long renders:** start with `bpy.app.timers.register(... INVOKE_DEFAULT ...)` and poll the output folder.

## 4. Transitions (mentor + PJ feedback)
- Mentor: more **action** in the back half, and **no black frames**. Done:
  - goal and save clips swapped in for standing shots;
  - white flashes only;
  - no ink holds on black.
- **What PJ liked (the hockey inspo reel grammar):**
  - **LED depth map** (`led_tr`): the depth map seen through a 6 px round-dot LED matrix, **navy**, with a rolling wave and a parallax wiggle. Cells sweep in far-first and out near-first. A **maize** lightning strike lands on the snap.
    - **Give it time:** ~31 frames (5 in, ~1 s hold, 5 out). Shorter and you can't see the lightning.
    - **Normalise depth per frame**, or mostly-far shots (a tunnel) go black.
    - **Re-form the bolt channel every 3-frame restrike**; a channel held for 15 frames looks frozen.
  - **Depth orbit push** (`dpush_tr`): near and far layers move opposite ways around a mid-depth pivot, plus a dolly, with 28-sample motion blur. Blur the depth (σ≈28) and clamp the parallax, or near objects leave white holes.
- **Rejected:**
  - drip wipes;
  - organic noise mattes;
  - big blocks;
  - hard glitch blocks and pixel smears ("too in your face");
  - band-slide "kinetic" slices (no depth);
  - a cheesy 3D logo sting.
- **Ending:**
  1. Fans push in.
  2. They drop into the LED field on the downbeat (strike).
  3. The official Block M (an STL from Printables) rises out of the depth field.
  4. The bolt zaps it: it **freezes, goes flat 2D and turns solid maize (#FFCB05) with a navy outline**.
  5. Crackle.
  6. The LED dots switch off.
- **Depth maps:** Depth Anything V2 ONNX on PJ's Mac (`~/Documents/claude-tools/depth-model`), run through Blender's Python. Hugging Face is blocked from Claude's shells.

## 5. Resolve API gotchas
- **Image sequences:** place with `startFrame=a, endFrame=b+1` (sequence numbers), not 0..N. It "succeeds" with a negative offset and shows nothing. Verify by diffing exported frames.
- **New clips without touching audio:** `AppendToTimeline` with `mediaType: 1` on a spare track.
- **`DeleteClips(items)`** works (don't pass the flag). **`SetProperty("AudioVolume", dB)`** for levels.
- **Bake files on a track** must not include stale frames from an older version of a transition; move them aside.

## 6. Infra
- **Device shell:** ~3 min per command, and background jobs die when the command ends. Split work into parallel chunks inside one call.
- **ffmpeg seeks** can land one frame off; check where the cuts land before trusting a decode.
- **Patch scripts on the drive directly** (Python read-modify-write + `md5sum`). The cloud→device upload once pushed a stale cached copy.
- **Keep the Mac awake:** `caffeinate -dimsu -t N` started from Blender's Python.

## Files
- **Code:**
  - `graphics/puck-lightning/tools/` — goal lightning and FX
  - `graphics/impact-lightning/tools/` — big hit
  - `graphics/inspo-transitions/tools/bake_v5_transitions.py` — all depth transitions and the ending
  - `graphics/master_v4/` — log master assembly
  - `graphics/tools/` — EXR→S-Log3, viewers
- **Notes:**
  - `notes/STORYBOARD_v3_PROSPECT.md` — the running changelog of every version
  - `notes/TRANSITIONS_v*.md`

## v17 → v18: match the reference's *structure*, not just its texture
- Comparing frame by frame with the Huntington ref: it **hard-cuts** into the depth look on the beat (or whip smear → 1 blue glitch frame → depth). Slow depth-ordered melts made muddy half-states — dropped.
- Depth sections are **pure depth** (no footage luma bleeding through), high-contrast: far crushes toward black, people glow saturated, only the nearest parts approach white. Cap the value (~0.86) so near subjects stay blue, not pale gray.
- Dot grid must have **dark gaps** to read (5px cell, dot radius 0.40, sharp edge) — 4px soft dots vanished.
- Hold one depth scene per clip; on the cut, hard-switch depth A → depth B under the maize strike. Exit with a horizontal row streak (ref f176), then clean footage with a decelerating whip.
- Always build a REF-vs-ours strip at matching phases (in / hold / out) before iterating.

## v19: the "weird cuts / timing glitches" were a stale layer, not the transitions
- The master stacks V4 lightning > goal FX > bake_v5 > bake_v4 > base. bake_v4 was baked BEFORE the song was extended a bar and never re-baked, so wherever v5 didn't cover it, old frames from the wrong clip moment showed through (216–238 ~8f off, 312–334 ~7f off, plus old punch-zooms at 380 / 463–466 that jumped into the next transition).
- Found it by correlating every v4 frame against base at offsets −8..+8 (downscaled gray, cached base). Anything < 0.75 at offset 0 = out of sync.
- Fix: `assemble.py` skips a V4BAD set; `under(t)` in the v5 baker now always reads the real base (the whip-in frames were sampling the stale layer too).
- Rule: after ANY re-time of the base, re-validate or delete every older bake layer — never let a lower layer silently fill gaps.
- Look: transitions now reuse the Block-M ending's LED field (`led_img` + `navy_led`, 6px dots, wave + parallax wiggle) — PJ's favourite — via `ledM()`; ref structure kept (whip → smear frame → hard-cut depth hold → maize strike on the cut → streak out → clean footage).
