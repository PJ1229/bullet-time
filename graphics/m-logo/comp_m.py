"""M finale comp (LOG): M render (scene-linear RGBA EXR) over a dark arena haze, lightning around the M (goal grammar),
ink-out at the end. tl = 466 + f. usage: python3 comp_m.py OUTDIR [f...]"""
import os, sys, cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(HERE)
sys.path.insert(0, G + "/tools"); sys.path.insert(0, G + "/puck-lightning/tools")
from read_rgba import read_rgba
cwd = os.getcwd(); import lightning_v5 as L; os.chdir(cwd)
W, H = 1920, 1080
RND = HERE + "/render_v01_exr/m_%04d.exr"
bgsrc = cv2.imread(G + "/master_v4/base16/b_0466.png", -1).astype(np.float32) / 65535
BG = cv2.GaussianBlur(L.dec(bgsrc), (0, 0), 45) * 0.10 + np.array([0.004, 0.0015, 0.0005], np.float32)  # dim crowd haze, navy
yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; BG = BG * (0.55 + 0.6 * (1 - np.abs(yy - 0.45) * 1.6).clip(0, 1))
LOCK = 13
def comp(f, out):
    rgb, A = read_rgba(RND % f); rgb = rgb[..., ::-1].copy()        # -> BGR
    lin = rgb + BG * (1 - A[..., None])
    rng = np.random.default_rng(500 + f // 2); rf = np.random.default_rng(900 + f)
    core = np.zeros((H, W), np.float32); m = (A > 0.5).astype(np.uint8)
    flick = float(np.clip(rf.normal(1.0, 0.2), 0.6, 1.35)); spill = 0.0; wfl = 0.0
    if 8 <= f < LOCK and m.sum() > 500:                              # charge builds as it swings in
        u = (f - 8) / (LOCK - 8); L.contour_arcs(core, m, rng, int(3 + 8 * u), 0.4 + 0.5 * u, 1.4 + 0.8 * u); spill = 0.15 + 0.3 * u
    elif f == LOCK:                                                  # lock = strike into the M + ring of arcs
        ys, xs = np.nonzero(m); c = np.array([xs.mean(), ys.min() + 10.0])
        L.draw(core, L.channel(np.array([c[0] + 180, -40.0]), c, np.random.default_rng(77), rough=0.17, branch=0.9, w0=5.5, i0=1.0))
        L.contour_arcs(core, m, rng, 22, 1.0, 2.6); spill = 1.2; wfl = 0.35
    elif LOCK < f <= 52 and m.sum() > 500:                           # crackle orbits the M, decaying, restrikes
        k = f - LOCK; e = 0.93 ** k
        if f in (19, 31): e = 0.9; ys, xs = np.nonzero(m); c = np.array([xs.mean() + rng.uniform(-200, 200), ys.min() + 10.0]); L.draw(core, L.channel(np.array([c[0] - 150, -40.0]), c, rng, rough=0.17, branch=0.8, w0=4.0, i0=0.85))
        L.contour_arcs(core, m, rng, int(6 + 12 * e), 0.35 + 0.6 * e, 1.6 + 0.8 * e); spill = 0.15 + 0.5 * e
    core *= flick
    if core.max() > 0:
        alb = L.lum((L.enc(lin) * 255).clip(0, 255).astype(np.uint8))
        lin = lin + L.finish(core, alb, None, spill * flick, 0.0, refl_gain=0.0, white_flash=wfl, bg_lin=lin)
    if f >= 53:                                                      # ink out to black (end card)
        u = (f - 52) / 8.0; F = cv2.resize(np.random.default_rng(5).random((24, 43)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        msk = cv2.GaussianBlur((F < u * 1.15).astype(np.float32), (0, 0), 1.2); lin = lin * (1 - msk[..., None]) - 0.01 * msk[..., None]
    o = L.enc(np.maximum(lin, -0.01))
    cv2.imwrite(os.path.join(out, "mf_%04d.png" % (466 + f)), (o * 65535 + 0.5).astype(np.uint16))
if __name__ == "__main__":
    out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
    fr = [int(x) for x in sys.argv[2:]] or list(range(1, 61))
    for f in fr: comp(f, out)
    print("ok", len(fr))
