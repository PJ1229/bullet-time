# Hockey × Prospect: Transitions v1 (16:9, 23.976)

Timeline `prospect_v3_cut` (project `hockey-sunflower-personal`). Visual board: `TRANSITIONS_v1_board.jpg`, which shows the OUT shot's last frame next to the IN shot's first frame for each cut.
Frame pairs were taken from the real source at the exact frames the timeline uses; the review sheets are in `contact_sheets/review/pairs_0.jpg`, `pairs_1.jpg` and `transition_candidates.jpg`.
Rules followed: clips play forward only, each clip is used once as one continuous piece, every transition or zoom gets a visual cue plus an SFX cue, and transitions peak on the beat.
Palette: black, white and red, with red only for hockey reds. Maize appears only as the payoff, from the drop through B1c and on B5.
Beat grid: about 12 frames per beat. Bars start at tl 0, 48, 96, 142 (beat 192, where the music cuts out), 192 (DROP), 239, 287, 335, 384, 431 and 479.

## Per-cut plan

| tl | OUT → IN | Transition | Dir | Frames | Peak vs beat | Visual cue | SFX cue (02_audio/sfx) | Build |
|---|---|---|---|---|---|---|---|---|
| 0 | black → A1 tunnel | Fade up from black | — | 3 | finishes on beat 1 | crushed-black B&W lift | `Low Boom` (already placed) | Cross dissolve from black, 3f |
| 48 | A1 tunnel → A2 #71 | **Hard cut**, led by a 5% push-in on A1 | push toward the centre M | push over A1's last 24f | cut on the downbeat | A1 navy/dark B&W cuts to A2's maize-on-navy depth silhouette (same dark field, so the cut feels designed) | `[27] Shutter Click` (placed) | A1: Inspector Zoom 1.00→1.05, ease-in, over the last 24f. A2: depth-silhouette grade |
| 96 | A2 #71 → A3 faceoff | **Eyeline cut** | #71's head lifts (the last A2 frames look up), then the camera tilts up | 0 | on the downbeat | — | `20 FREE CINEMATIC WHOOSH` slice on the tilt, tl ~108–119 (placed) | Plain cut. A2's 50% speed makes the head lift read |
| 119 | A3 Yost lights → A4a Horcoff | **Upward light whip + 2f white flash** | vertical, upward (continues A3's tilt) | blur on A3's last 3f + 2f white (tl 118–120) | white peaks exactly on 119 (beat 190) | A3 must end on the blown-out roof lights (see FIX 1). Directional blur up, then white, then A4a | `[21] Vintage Flash` (placed at 119) + `[8] Ringing Riser` ending at 119 (placed) | V2: solid white generator 118–121, opacity 0→100→0 (keys 118/119/121). A3: Directional Blur OFX (angle 90°, ramps 0→high on the last 3f). A4a: B&W with light posterize |
| 142 | A4a → CG bullet-time | **LOCKED.** Freeze lands on beat 192 as the music cuts out | — | — | on the beat | the world turns into comic over CG f2–8 | `[46] Sub Drop` 144→ (placed), orbit whoosh 142–186 (placed) | Done. Copy PJ's WMU grade onto the CG clip exactly |
| 186 | CG → live resume | **LOCKED.** Invisible join | — | — | puck crosses the line at about tl 191–192 = DROP | — | — | Done |
| 192 | DROP (inside B1a) | **2f white impact flash + 3f stutter** | — | 2 + 3 | flash on 192 | punch the brightness on the net-ripple frame | `[15] Cinematic Impact` (placed) + WMU crowd roar from the clip's own audio | V2 white solid 192–194 at 60%→0. Stutter: duplicate frame 192 for 2 extra frames via a retime freeze, or skip if it fights the bullet-time |
| 204 | B1a → speed ramp | **Speed ramp** (continuous clip) | camera pans with the play | 11 | the ramp starts on the beat | directional blur during the fast portion | `[12] Short Swoosh` (placed) | Retime curve: ease into ~1000% and back out (now a flat 1009%). Motion blur on. **FIX 4: 1-frame repeat** |
| 215 | ramp → B1c #44 arms up | **Punch-in 100→140% on #44 + 1f flash** | zoom in toward #44 | 4f zoom + 1f flash | lands on the beat at 215 | #44 is tiny in the wide shot; the 4K source supports a clean 2× in 1080. **Maize payoff starts here** (PJ colour) | `[27] Shutter Click` + short whoosh | Inspector Zoom keyframes 215→219, 1.0→1.4, position on #44 (about x+0.05, y−0.1). V2 white 1f at 60% |
| 239 | B1c → B2 big hit | **Speed-blur push-in** (USC style) | push forward into B2 | 3f radial blur on B2's head | cut on the bar downbeat | B2 opens through the students' heads in the foreground, so the push "enters" the crowd | `[12] Short Swoosh` peaking at 239 | B2's first 3f: Radial/Zoom Blur OFX 40→0 + Zoom 1.08→1.0. B2 is harsh B&W |
| ~264 | (inside B2) contact | **Impact accent** | — | 6 | contact on the beat | 40% retime for 6f on contact, 2f camera shake | `[15] Cinematic Impact` (placed 264) + glass bang from clip audio | Retime 40% over the contact frames, Fusion Shake 2f |
| 287 | B2 hit → B3 scramble | **Match cut on screen position** | both have the action in the left third against the same BELFOR boards | 0 | downbeat | continuous board line and action spot, so it reads as one beat | `[27] Shutter Click` | Plain cut. Both B&W up to the 311 colour switch |
| 311 | (inside B3) | COLOR SWITCH (placed) | — | — | beat 3 | B&W → PJ colour | `[20] Shutter, Satisfying` (placed) | Grade keyframe |
| 335 | B3 → flash run | **Hard cut into 8 × 6f flashes** | — | 6f each (half-beat) | every cut on a half-beat | alternate B&W / colour / depth silhouette and tight / wide (F1 tight, F2 wide, F3 med, F4 tight, F5 med, **F6 tight (swap)**, F7 tight crowd, F8 med). F3 is Denver in red, so keep it **B&W** (red rule) | `Fast Clicks` slice under 335–384, one click per cut (placed, pick exact clicks) | Plain cuts. Optional: 1f white on the first flash only |
| 384 | F8 (#96/#44 at the glass) → B5 HORCOFF 44 | **Zoom-through "44" match** | push into #44 in F8, then cut to the 44 nameplate | push over F8's last 6f (1.0→1.25) | cut on the downbeat | #44 is in F8, so cut from the small 44 to the giant 44. B5 is PJ colour (maize hero) | short whoosh peaking at 384 + `[27] Shutter Click` | F8 Zoom keys 377→383 toward #44 (right of centre). Motion blur on |
| 431 | B5 → B6 fans | **Reverse cut, players → fans** | the players face the stands, the fans face the ice | 0 | downbeat | B6 = students erupting (see FIX 3) | crowd swell from B6's clip audio + `[12] Short Swoosh` | Plain cut. Optional 3% push on B6 |
| 467 | B6 → CG puck→lens | **Object → lens wipe** (USC football move) | the puck flies at the camera and fills the frame | 12 | the puck fills the frame on beat 219 (tl ~467); black on 479 | ends on hard black at 479 | whoosh rising into `Low Boom` on 479 (placed) | Main thread builds the 12f CG. Place it on V1 467–479 |

## Shot fixes (exact source)

1. **A3 in-point.** The current A3 (`0134` src f506–563, 8.44–9.39 s) ends on dim roof girders, so the white flash at 119 has nothing bright to come out of. The tilt hits the brightest Yost lights at **9.45–9.57 s**. **New A3 = `26IHM_07_0134_#11_FACEOFF_TILTDOWN_!` src 8.61–9.57 s (f516–574 at 59.94), 23 tl frames.** It still opens on the wide faceoff, tilts up, and ends on the blown lights at the cut.
2. **F6 swap.** `26_IHM_7_683_#72_SAVE` @14.5 is wide and nearly empty (the goalie is tiny, nothing is moving), and it breaks the tight/wide rhythm. **New F6 = `26_IHM_2_232_#72.MXF` src 1.00–1.25 s (f24–30).** It's an IVANKOVIC #72 close-up skating across the lens, sharp, and works as a natural mini lens wipe. 683 isn't used anywhere else.
3. **B6 swap.** `26IHM_07_0237_FANS_STUDENTSECTION_!!` is shot through the glass: hazy, a stanchion cuts the frame, and the eruption is small in 16:9. **New B6 = `26IHM_07_0234_FANS_CHEERING.MP4` (59.94) src 2.30–3.80 s (f138–228), 36 tl frames.** It's a sharp close-up of students going off, and it pairs as a clean reverse shot with the B5 close-up. 0237 moves to the alt pool.
4. **1-frame repeats around the ramp.** The ramp starts on src f751, the same frame that ends B1a, and B1c starts on f862, the frame the ramp ends on. **Set the ramp to f752 and B1c to f863** (B1c then runs f863–886).
5. **B1c framing.** It's too wide in 16:9 for a hero beat; the 140% punch-in above is the fix, with no swap needed.
6. **Optional F4.** The Perron-vs-Denver Horcoff hug @61.0 is slightly soft through the glass. It's fine for 6 frames, but a sharper frame might exist about ±0.5 s.

Alt pool checked: `26_IHM_7_512_#09` (goalie stance seen through the net, a good flash), `26IHM_07_0178_FANS_LETSGOBLUE` (weak, someone's back), `26_IHM_7_567_FANS` (wide maize crowd, sharp), `26_IHM_7_673_#72_SAVE` (wide crease scramble, small).

## PJ's call
- **B6:** the sharp student close-up (0234, recommended) or the wide eruption through the glass (0237)?
- **DROP stutter:** add a 3f stutter on the puck-in, or let the bullet-time carry it and use only the white impact flash? I lean toward flash only.
- **White flashes:** pure white, or a white tinted a touch toward the grade? Pure white matches the USC grammar.
- **F3:** Denver's red jerseys stay B&W (hockey-red rule)? Recommended yes.
