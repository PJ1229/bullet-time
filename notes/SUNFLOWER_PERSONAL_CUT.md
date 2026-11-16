# Hockey x Sunflower — personal / portfolio cut (v2 dev)

Started 2026-11-15. Notion: "hockey edit" → Storyboard v2. PERSONAL ONLY — copyrighted song,
no posting without Gabe's OK (Michigan Athletics footage rule). Official cut stays on Epidemic Sound (v1).

## Spec
- Song: Sunflower (Post Malone, Swae Lee). Section 1:10.867–1:32.230 = 8 bars, 21.36 s, 90.67 BPM, bar 2.670 s.
  Audio: ../02_audio/sunflower.mp3 (2:38.145, copied from Downloads 2026-11-15).
  **This file runs +0.023 s vs the Notion grid** (beat-tracked; ~mp3 encoder padding, about half a frame).
  → In THIS file the section is **1:10.890 – 1:32.253**. Set the timeline audio in-point to 70.890 s.
  Cut times in the table are unchanged (relative to the in-point); add 0.023 to every "Song in" value.
- Timeline: 23.976 fps (all MXF are 23.976; only the 7 `26IHM_07_*` MP4s are 59.94).
- Source: 78 clips, all 3840x2160 h264, flat log. Specs: clip_index.csv.

## Bar grid (cut time = song time − 70.867)
| Bar | Cut in | Song in | Lyric |
|---|---|---|---|
| 1 | 0:00.00 | 1:10.867 | Then you're left in the dust (orbit 0:00–0:02.00) |
| 2 | 0:02.67 | 1:13.538 | Unless I stuck by ya |
| 3 | 0:05.33 | 1:16.196 | You're the sunflower |
| 4 | 0:07.99 | 1:18.855 | I think your love would be too much |
| 5 | 0:10.67 | 1:21.537 | Or you'll be left in the dust |
| 6 | 0:13.33 | 1:24.196 | Unless I stuck by ya |
| 7 | 0:16.00 | 1:26.866 | You're the sunflower |
| 8 | 0:18.66 | 1:29.525 | You're the sunflower (out 0:21.36) |

## Hero clip — `2026 1023 GOAL 1 HORCOFF VS WMU.MXF` (Horcoff = #44)
Contact sheets: contact_sheets/GOAL_HORCOFF_WMU*.jpg
- 0:25.0–0:29.5  #44 carries in, dangles past a sprawling WMU defender (best live action beat)
- ~0:30.0        camera WHIPS to the net — puck entering is NOT visible (it happens inside the whip)
- 0:30.25–0:33   goalie down in the splits, net, WMU players turning
- 0:36–0:42      #44 arms up
- 0:42–1:25      glass celly under the "THE CHILDREN OF YOST!" banner — big pile, faces at ~0:45–0:50
- 1:39–2:06      bench fist-bump line

### Orbit decision (changed from Notion)
No readable puck-on-the-line frame + follow cam at 23.976 → a matchmoved 360° puck orbit won't work on this clip.
New plan for bar 1: **fully CG, stylized puck-into-net orbit** built from ../03_graphics/hockey-puck-goal/puck_goal_starter.blend
(restyle: on 2s, Line Art, halftone, maize/blue), bracketed by live footage:
- IN  (0:00.00, ~6–10 fr): live #44 dangle, freeze ~0:29.25, maize/white impact flash → CG
- ORBIT (to 0:02.00): CG puck orbits 360° and crosses the line — the "goal we never saw"
- OUT (0:02.00): flash/whip into live goalie-in-splits 0:30.5–0:31.5 on "dust", then bar 2 celly
No camera solve needed. Blender shot = 48 frames at 23.976 (2.00 s) for the orbit.

## Selects by bar (★ = seen on a contact sheet; others picked by filename, still need a look)
1. ★ WMU goal 0:25–0:29.5 (in), CG orbit, ★ 0:30.5–0:31.5 (out)
2. ★ WMU goal celly 0:42–0:50 (#44 leap into the pile, banner behind)
3. STYLIZED identity: ★ banner frames WMU 0:51–1:00 → halftone; `26IHM_07_0237_FANS_STUDENTSECTION_!!` (60p)
4. Rush/hit: `26IHM_07_0172_#17_BIGHIT_!` (60p), `26_IHM_7_826_#44_PHY_HIT`
5. Save (B&W + maize isolation, panel split): `26_IHM_7_673/683/698_#72_SAVE`
6. Flash montage: `26IHM_07_0134_#11_FACEOFF_TILTDOWN_!` (60p), `26IHM_07_0231_#71_ISO_FACEOFF` (60p),
   `26_IHM_4_715_TEAM_TUNNEL`, ★ Perron/Schifsky vs Denver, `26_IHM_7_833_TEAM_CELE`
7. Hero portrait: `26IHM_07_0238_POST_#44_ISO_CELE` (60p, Horcoff again = through-line); crowd alt `26IHM_07_0178_FANS_LETSGOBLUE`
8. End: `26_IHM_7_848_TEAM_SPEECH_SONG_DANCE_CELE` or `26_IHM_7_830_SCENIC`

The `869_*` clips (13) have no description in their filenames and still need a look.

## Autolog (found 2026-11-15)
Labels live on the Mac: ~/Documents/autolog/hockey-ihm-1113.nosync/out/ (index.json, overlay-viewer/descriptions/).
Copy here: hockey_labels_autolog.csv. Caveats:
- `seconds` column = processing time, NOT a moment in the clip.
- GOAL event times come from the filename tag and sit mid-clip (WMU goal logged at 74.0 s). The real WMU goal is ~0:29–0:30 (contact sheet). Trust the sheets for timing.
- All 13 `869_*` = machine-guessed "scenic"/"interview" — unverified.
- Tags agree with the filename picks above; no changes to the bar map.

## Next
1. ✅ Resolve project `hockey-sunflower-personal` (1080x1920, 23.976): bins 01_audio + 02_raw_footage (78), timeline `sunflower_v01_grid` = song from 70.904 s (frame 1700), 512 fr, bar markers.
2. Restyle the puck_goal_starter.blend → 48-frame stylized orbit.
3. Rough-cut the live bars from the selects above; then stylize passes (see Notion v2 order).
