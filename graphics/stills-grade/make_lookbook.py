"""Look-book final slide (1920x1080): stills in timeline order.
usage: python3 make_lookbook.py STILLS_DIR OUT_DIR
 - titled: 8x7 grid, 40px margin, 6px gutter, title strip (Inter)  -> BulletTime_lookbook_1920x1080.png
 - full-bleed: 8x8 grid of 240x135 tiles                            -> BulletTime_lookbook_fullbleed_1920x1080.png"""
import sys, glob, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
IN, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
F = [f for f in sorted(glob.glob(IN + '/bullet_time_*.jpg')) if os.path.basename(f)[12:16] not in ('0204', '0211', '0005')]
F = [F[i] for i in np.round(np.linspace(0, len(F) - 1, 64)).astype(int)]
tiles = [Image.open(f).convert('RGB').resize((480, 270), Image.LANCZOS) for f in F]
W, H = 1920, 1080
B = Image.new('RGB', (W, H))
for i, t in enumerate(tiles): r, c = divmod(i, 8); B.paste(t.resize((240, 135), Image.LANCZOS), (c * 240, r * 135))
B.save(OUT + '/BulletTime_lookbook_fullbleed_1920x1080.png')
A = Image.new('RGB', (W, H), (12, 11, 10)); d = ImageDraw.Draw(A)
m, g, cols, rows = 40, 6, 8, 7
tw = (W - 2 * m - (cols - 1) * g) / cols; th = tw * 9 / 16
for k, i in enumerate(np.round(np.linspace(0, 63, cols * rows)).astype(int)):
    r, c = divmod(k, cols); A.paste(tiles[i].resize((round(tw), round(th)), Image.LANCZOS), (round(m + c * (tw + g)), round(m + r * (th + g))))
gy = round(m + rows * (th + g) - g); cy = (gy + H) // 2
FD = '/usr/share/fonts/opentype/inter/'
big = ImageFont.truetype(FD + 'Inter-SemiBold.otf', 46); sm = ImageFont.truetype(FD + 'Inter-Medium.otf', 17); tiny = ImageFont.truetype(FD + 'Inter-Regular.otf', 15)
def spaced(x, y, s, font, fill, track, right=False):
    w = sum(d.textlength(ch, font=font) + track for ch in s) - track
    if right: x -= w
    for ch in s: d.text((x, y), ch, font=font, fill=fill, anchor='lm'); x += d.textlength(ch, font=font) + track
spaced(m, cy, 'BULLET TIME', big, (255, 203, 5), 6)
spaced(W - m, cy - 12, 'MICHIGAN HOCKEY  ×  PROSPECT', sm, (236, 228, 214), 3, True)
spaced(W - m, cy + 14, 'EDIT · VFX · COLOR  —  PJ KIM', tiny, (150, 142, 130), 3, True)
d.line([(m, gy + 14), (W - m, gy + 14)], fill=(40, 37, 34), width=1)
A.save(OUT + '/BulletTime_lookbook_1920x1080.png')
