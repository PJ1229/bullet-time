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

## 4. Transitions (final v22 — and the road there)
- Mentor: more **action** in the back half, and **no black frames**. Done: goal/save clips instead of standing shots, white flashes only, no ink holds on black.
- **Final set (`bake_v5_transitions.py` PLAN):**
  - **Pixel-sort drip** (`psort_tr`) — PJ's favourite ("heavy"). Column-stretch: below a per-column row y0 the column repeats its y0 pixel; y0 banded per ~12 px column group so it reads as sorted drips. Clip A drips into a full navy sorted frame on the beat, clip B bleeds out of the drips, maize strike lands 4 frames later. 48 drips **up** (`up=True`), 239 drips down, so they don't repeat.
  - **Depth orbit push** (`dpush_tr`): near and far layers move opposite ways around a mid-depth pivot + dolly, 28-sample motion blur. Blur the depth (σ≈28) and clamp parallax or near objects leave holes.
  - **Charge-up chain** (`dpush_tr2`) built from the push PJ loved at 0:16: 341→365→384→408 at 0.7/0.85/1.0/1.3× with maize crackle on the near subject growing each time, paying off at 431 (`payoff_tr`: 1.6× push + full strike).
- **Tried and dropped** (so we don't redo them): ink/drip wipes, organic mattes, big blocks, hard glitch, band slides, a 3D logo sting, LED-dot depth-map transitions (v13–v20: never got close enough to the Huntington reference — muddy melts, footage texture bleeding through, dots too big/too fine), the roto-cutout and window/square moves from PJ's IG reel (v21).
- **Lessons from the dot saga:**
  - Compare against the reference **frame by frame at matching phases** (in / hold / out) before iterating — it showed the ref hard-cuts into depth, holds pure high-contrast depth, and exits with a streak; we'd been melting.
  - When PJ likes one look (the Block M LED field), reuse that exact code path rather than re-deriving a similar one.
  - Tinting bright ice "navy→maize by luma" goes sepia. Keep navy dominant, maize only in highlights (luma > ~0.62).
  - Depth subject mattes: normalise, threshold, keep tall components, and never let the mask shrink frame-to-frame (a dropped mask = a black flash frame).
- **Ending:** fans push in → drop into the navy LED field on the downbeat (strike) → the official Block M (Printables STL) rises out of it → the bolt zaps it: it **freezes, goes flat 2D, solid maize #FFCB05 with a navy outline** → crackle → dots switch off.
- **Depth maps:** Depth Anything V2 ONNX on PJ's Mac (`~/Documents/claude-tools/depth-model`), run via Blender's Python (Popen, never blocking). Hugging Face is blocked from Claude's shells.

## 4b. The "weird cuts / timing glitches" bug
- The master stacks V4 lightning > goal FX > bake_v5 > bake_v4 > base. **bake_v4 was baked before the song was extended a bar** and never re-baked; wherever v5 didn't cover it, frames from the wrong moment showed (216–238 ~8f off, 312–334 ~7f off, old punch-zooms at 380/463–466 jumping into the next transition). The v5 baker was also sampling it.
- Found by correlating each v4 frame against base at offsets −8..+8 (downscaled gray, cached). < 0.75 at offset 0 = out of sync.
- Fix: `assemble.py` skips a `V4BAD` set; the baker reads base only.
- **Rule: after any re-time of the base, re-validate or delete every older bake layer.** Never let a lower layer silently fill gaps.

## 4c. Last-day tweaks (v23)
- **Charge on a held shot** (`charge_tr`, 0:16–0:17 on Horcoff 44): the goal grammar works anywhere — arcs crawl the person's silhouette and grow (intensity ∝ u^1.3) into the next cut. If a depth map is missing, a **maize-jersey HSV key** (H 14–38, S/V > 90 on the test-grade view) is a solid subject matte for Michigan footage.
- **3D logo has to show its sides to read as 3D.** A depth-only emission render looks flat in the LED field. Fix: animate a side swoosh with a big spin (~125° around vertical, ease-out, motion blur) that settles on the lock frame, and render a second channel = facing-light shade (Geometry Normal · light dir → G channel) so faces vs. returns separate. `m-logo/blockm_led_v02_swoosh.blend`.
- **Blender couldn't read `~/Documents`** this session (every read timed out — likely a pending macOS privacy prompt or iCloud eviction). Depth Anything lives there, so new depth maps couldn't be made. Fix next time: approve Blender's Documents access (System Settings → Privacy → Files & Folders) or move `claude-tools` off `~/Documents`.
- **ProRes encode on the device shell:** with Resolve/Blender busy, 8×66-frame parallel chunks no longer finish in one ~3-min call. Use 44-frame chunks, ≤5 per call, check every chunk's packet count before concat.

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
- **Deliverables (TOSHIBA `06_deliverables/`):** `hockey_prospect_v23_LOG_master_prores4444xq.mov` (FINAL, S-Log3), `hockey_prospect_v23_TESTGRADE_preview_small.mp4`, `stills_v22_LOG/` (17 × 16-bit S-Log3 TIFF for posting).
- **Notes:**
  - `notes/STORYBOARD_v3_PROSPECT.md` — the running changelog of every version
  - `notes/TRANSITIONS_v*.md`
