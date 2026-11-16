"""Big-hit bullet-time comp: EXR (scene-linear) -> S-Log3 16-bit PNG, retimed 44->N frames,
real frame at the start/end, FG (posts/ropes/fan) layer near the ends, impact shake at contact."""
import os, sys, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from exr_to_slog3 import read_exr, slog3
H = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(H, "render_bighit_v01_log_exr"); OUT = os.path.join(H, "render_bighit_v01_slog3")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 23
os.makedirs(OUT, exist_ok=True)
frames = [slog3(read_exr(os.path.join(SRC, "bh_%04d.exr" % i))) for i in range(1, 45)]
orig = cv2.resize(cv2.imread(os.path.join(H, "src", "bighit_FREEZE_8.79.png")), (1920, 1080), interpolation=cv2.INTER_AREA)[..., ::-1].astype(np.float64) / 255
fg = cv2.resize(cv2.imread(os.path.join(H, "plates", "fg_rgba.png"), -1), (1920, 1080), interpolation=cv2.INTER_AREA).astype(np.float64) / 255
fgc, fga = fg[..., :3][..., ::-1], fg[..., 3:]
rng = np.random.default_rng(7)
for i in range(N):
    p = i * 43 / (N - 1); a = int(np.floor(p)); b = min(a + 1, 43); t = p - a
    img = frames[a] * (1 - t) + frames[b] * t
    # FG layer + exact real frame at the ends
    wfg = max(0.0, 1 - min(i, N - 1 - i) / 2.5)
    img = img * (1 - fga * wfg) + fgc * fga * wfg
    wfull = 1.0 if i == 0 else 0.0
    img = img * (1 - wfull) + orig * wfull
    # impact shake on contact (first 5 frames), slight zoom hides edges
    if 1 <= i <= 5:
        amp = 14 * (0.6 ** (i - 1)); dx, dy = rng.uniform(-1, 1, 2) * amp
        M = cv2.getRotationMatrix2D((960, 540), rng.uniform(-0.4, 0.4) * amp / 14, 1.04)
        M[:, 2] += (dx, dy); img = cv2.warpAffine(img, M, (1920, 1080), borderMode=cv2.BORDER_REFLECT)
    cv2.imwrite(os.path.join(OUT, "bh_%04d.png" % (i + 1)), (np.clip(img[..., ::-1], 0, 1) * 65535 + 0.5).astype(np.uint16))
print("wrote", N)
