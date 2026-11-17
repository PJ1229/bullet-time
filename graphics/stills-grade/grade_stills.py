"""Bullet Time stills grade — PJ's December node order, in scene-linear.
CORRECT (per shot): cst in -> exposure/'hdr' -> wb (neutralise ice) -> curves
GRADE (shared):     split tone (navy shadows / golden-cream highs) -> midtones -> hue/lum vs sat (maize+navy protected)
                    -> soft clip -> halation -> grain -> cst out (Rec.709 g2.4)
usage: python3 grade_stills.py IN_DIR OUT_DIR [--lut out.cube]"""
import sys, os, glob, numpy as np, cv2
SG3C_TO_709 = np.array([[1.6269474, -0.5401385, -0.0868089], [-0.1785155, 1.4179409, -0.2394254], [0.0444361, -0.1959200, 1.2403040]], np.float32)
def slog3_dec(c):
    cc = c * 1023.0
    return np.where(cc >= 171.2102946929, 10 ** ((cc - 420.0) / 261.5) * (0.18 + 0.01) - 0.01, (cc - 95.0) * 0.01125000 / (171.2102946929 - 95.0)).astype(np.float32)
def luma(x): return x[..., 0] * 0.2126 + x[..., 1] * 0.7152 + x[..., 2] * 0.0722
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

# ---------------- CORRECT ----------------
def correct(lin):
    Y = luma(lin)
    # exposure: put the scene's mid (40th pct of luma, ice-heavy shots excluded via log median) near 0.16
    med = np.exp(np.median(np.log(np.clip(Y, 1e-4, None))))
    lin = lin * np.clip(0.16 / max(med, 1e-4), 0.55, 2.2)
    # "hdr" highlight: tame very hot ice/lights before the curve
    Y = luma(lin); k = np.where(Y > 1.0, (1.0 + np.log1p(Y - 1.0) * 0.6) / np.maximum(Y, 1e-6), 1.0)
    lin = lin * k[..., None]
    # wb: neutralise bright low-chroma pixels (ice / boards) 75%, keep a hair of warmth
    Y = luma(lin); ch = (lin.max(-1) - lin.min(-1)) / np.maximum(Y, 1e-4)
    hue_ok = (lin[..., 2] >= lin[..., 0] * 0.9)            # ice/boards: cyan-white, not maize/red
    m = (Y > np.quantile(Y, 0.55)) & (ch < 0.6) & hue_ok
    if m.sum() > 2000:
        g = np.median(lin[m], 0); g = g / g.mean()
        lin = lin / (1 + 0.9 * (g - 1))[None, None, :]
    Y = luma(lin); icef = float((Y > 0.7).mean())                 # ice-dominant frames: hold the ice down off clip
    if icef > 0.3: lin = lin * (1 - 0.35 * min(1.0, (icef - 0.3) / 0.4))
    return np.clip(lin, 0, None)

def filmic(x):            # 'curves': lifted toe, soft shoulder (display-referred 0..1)
    a, b, c, d, e = 2.2, 0.06, 2.0, 0.65, 0.12
    y = (x * (a * x + b)) / (x * (c * x + d) + e)
    return np.clip(y * 0.94 + 0.035, 0, 1)

# ---------------- GRADE (shared look) ----------------
NAVY_SH = np.array([0.90, 0.97, 1.10], np.float32)   # RGB multipliers in shadows
CREAM_HI = np.array([1.06, 1.01, 0.90], np.float32)  # golden-cream highlights (ref video)
def rgb2hsv_f(x): return cv2.cvtColor(np.clip(x, 0, 1).astype(np.float32), cv2.COLOR_RGB2HSV)
def hsv2rgb_f(x): return cv2.cvtColor(x.astype(np.float32), cv2.COLOR_HSV2RGB)
# reference ("Video 40953") measured colour by luma band: (centre, r/g, b/g)
REF_BANDS = [(0.05, 1.155, 1.201), (0.17, 1.31, 0.97), (0.35, 1.18, 0.89), (0.55, 1.14, 0.82), (0.75, 1.19, 0.76), (0.93, 1.07, 0.72)]
def ref_tint(L, k=0.72):
    c = np.array([b[0] for b in REF_BANDS], np.float32)
    rg = np.interp(L, c, [b[1] for b in REF_BANDS]) ** k; bg = np.interp(L, c, [b[2] for b in REF_BANDS]) ** k
    m = np.stack([rg, np.ones_like(rg), bg], -1)
    return m / (m @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
def grade(d):
    hsv0 = rgb2hsv_f(d); H0, S0 = hsv0[..., 0], hsv0[..., 1]
    w_navy0 = np.exp(-((H0 - 222) / 22) ** 2) * ss(S0 / 0.35)
    L = luma(d)
    tint = ref_tint(L)
    keep = (0.55 * w_navy0)[..., None]                          # navy jerseys keep their blue
    d = d * (tint * (1 - keep) + keep)
    # midtones: soft contrast, highlights held under ~0.88 like the ref
    d = np.clip(0.40 + (d - 0.40) * 1.05, 0, 1)
    hsv = rgb2hsv_f(d); H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    w_maize = np.exp(-((H - 47) / 12) ** 2); w_navy = np.exp(-((H - 222) / 20) ** 2)
    w_red = np.exp(-((np.minimum(np.abs(H - 0), np.abs(H - 360)) / 18) ** 2)); w_grn = np.exp(-((H - 110) / 35) ** 2)
    w_teal = np.exp(-((H - 180) / 18) ** 2)
    sat = 0.78 + 0.32 * w_maize + 0.22 * w_navy + 0.05 * w_red - 0.25 * w_grn + 0.05 * w_teal
    sat = sat * (0.6 + 0.4 * ss(V / 0.22)) * (1 - 0.35 * (1 - w_maize) * ss((V - 0.8) / 0.2))
    H = np.where(w_maize > 0.3, H - 3.0 * w_maize, H)          # maize -> gold
    H = np.where(w_grn > 0.3, H - 18 * w_grn, H)                # greens -> olive (ref foliage)
    S = np.clip(S * sat, 0, 1)
    d = hsv2rgb_f(np.dstack([H % 360, S, V]))
    d = np.where(d > 0.84, 0.84 + (1 - np.exp(-(d - 0.84) / 0.12)) * 0.12, d)   # creamy roll-off
    return np.clip(d, 0, 1)
def finish(d, seed=0):
    h, w = d.shape[:2]
    # halation: warm red-orange bloom off the brightest bits (lightning, lights, ice glints)
    hl = np.clip((luma(d) - 0.76) / 0.2, 0, 1)
    hal = cv2.GaussianBlur(hl, (0, 0), w / 320) * 0.6 + cv2.GaussianBlur(hl, (0, 0), w / 90) * 0.4
    d = d + hal[..., None] * np.array([0.12, 0.05, 0.005], np.float32)
    # grain: luma-weighted, fine
    rng = np.random.default_rng(seed)
    g = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 0.7)
    L = luma(d); amp = 0.018 * (0.4 + 0.6 * (1 - np.abs(L - 0.45) / 0.55))
    d = d + (g * amp)[..., None]
    return np.clip(d, 0, 1)

def to709(lin_disp):     # display transform: values already display-referred 0..1 -> Rec709 g2.4 encode
    return np.clip(lin_disp, 0, 1) ** (1 / 1.0)   # filmic() already outputs display code values

def process(path):
    a = cv2.imread(path, -1)[..., ::-1].astype(np.float32) / 65535.0     # RGB S-Log3 code
    lin = slog3_dec(a) @ SG3C_TO_709.T
    lin = np.clip(lin, 0, None)
    lin = correct(lin)
    d = filmic(lin)
    d = grade(d)
    d = finish(d, seed=hash(os.path.basename(path)) % 2**31)
    return d
def write_lut(path, n=33):
    """global look only (cst in -> curves -> grade), no per-shot correction / spatial fx. S-Log3/SGamut3.Cine in -> Rec709 out"""
    r = np.linspace(0, 1, n, dtype=np.float32)
    B, G, R = np.meshgrid(r, r, r, indexing='ij')
    rgb = np.stack([R, G, B], -1).reshape(n * n, n, 3)
    lin = np.clip(slog3_dec(rgb) @ SG3C_TO_709.T, 0, None)
    lin = lin * (0.16 / 0.18)
    out = grade(filmic(lin)).reshape(-1, 3)
    with open(path, 'w') as f:
        f.write('TITLE "Bullet Time look (S-Log3 SGamut3.Cine -> Rec709)"\nLUT_3D_SIZE %d\n' % n)
        for v in out: f.write('%.6f %.6f %.6f\n' % tuple(v))
if __name__ == "__main__":
    ind, outd = sys.argv[1], sys.argv[2]; os.makedirs(outd, exist_ok=True)
    if '--lut' in sys.argv: write_lut(sys.argv[sys.argv.index('--lut') + 1])
    only = [a for a in sys.argv[3:] if a.isdigit()]
    for p in sorted(glob.glob(os.path.join(ind, '*_SLog3.tif'))):
        if only and not any('_%04d_' % int(o) in p for o in only): continue
        d = process(p)
        name = os.path.basename(p).replace('_SLog3.tif', '')
        cv2.imwrite(os.path.join(outd, name + '.tif'), (d[..., ::-1] * 65535 + 0.5).astype(np.uint16))
        cv2.imwrite(os.path.join(outd, name + '.jpg'), (d[..., ::-1] * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
        print('ok', name)
