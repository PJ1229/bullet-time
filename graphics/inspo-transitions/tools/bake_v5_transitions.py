"""v5 inspo transitions in 16-bit LOG: ink-matte wipes, drip wipes, pixel smear / glitch (hockey inspo 0:01, 0:07, 0:19-0:22).
Reads the v4 log base (master_v4/base16) and the v4 bake for frames it doesn't own. Writes bake_v5_log16/fx_tl_%04d.png.
usage: python3 bake_v5_transitions.py [tl ...]   (no args = all planned transitions)"""
import os, sys, cv2, numpy as np
G = os.path.expanduser("~/mnt/TOSHIBA EXT/um-athletics/hockey-edit/03_graphics")
BASE = G + "/master_v4/base16/b_%04d.png"; V4 = G + "/inspo-transitions/bake_v4_log16/fx_tl_%04d.png"
OUT = G + "/inspo-transitions/bake_v5_log16/fx_tl_%04d.png"; os.makedirs(os.path.dirname(OUT), exist_ok=True)
W, H = 1920, 1080
def rd(p): return cv2.imread(p, -1).astype(np.float32) / 65535
def base(t): return rd(BASE % t)
def under(t):                      # v19: stale v4 bake was cut for the old song length -> always use the real base
    return base(t)
def dec(c):
    cc = c * 1023; return np.where(cc >= 171.2102946929, (10 ** ((cc - 420) / 261.5)) * 0.19 - 0.01, (cc - 95) * 0.01125 / (171.2102946929 - 95))
def enc(l):
    return np.clip(np.where(l >= 0.01125, (420 + np.log10(np.maximum(l + 0.01, 1e-6) / 0.19) * 261.5) / 1023, (l * (171.2102946929 - 95) / 0.01125 + 95) / 1023), 0, 1)
BLACK = 95 / 1023.0                # S-Log3 code for scene black
RIM = np.array([0.05, 0.08, 1.0], np.float32)     # BGR hockey-red rim light (linear)
def zoom(im, s, c=(960, 540)):
    M = np.float32([[s, 0, c[0] - s * c[0]], [0, s, c[1] - s * c[1]]]); return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
def noise_field(seed, scales=((260, 1.0), (90, 0.45), (28, 0.18))):
    r = np.random.default_rng(seed); f = np.zeros((H, W), np.float32)
    for s, a in scales:
        n = r.random((H // s + 3, W // s + 3)).astype(np.float32)
        f += a * cv2.resize(n, (W + 3 * s, H + 3 * s), interpolation=cv2.INTER_CUBIC)[:H, :W]
    f -= f.min(); return f / f.max()
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
# ---------- ink matte (organic blobs eat A -> recede to reveal B) ----------
def _reveal(A, B, M, bandw, rim):
    """A outside, B inside the matte; a thin dark ink band + red rim at the boundary (no black frames)"""
    Ms = cv2.GaussianBlur(M, (0, 0), 1.0)
    out = A * (1 - Ms[..., None]) + B * Ms[..., None]
    d = cv2.distanceTransform((1 - M).astype(np.uint8), cv2.DIST_L2, 3) + cv2.distanceTransform(M.astype(np.uint8), cv2.DIST_L2, 3)
    band = np.clip(1 - d / bandw, 0, 1)
    out = out * (1 - band[..., None]) + BLACK * band[..., None]
    rimm = cv2.GaussianBlur(np.clip(1 - np.abs(d - bandw) / 3.0, 0, 1).astype(np.float32), (0, 0), 1.5)
    return enc(dec(out) + (rimm * 0.7 * rim)[..., None] * RIM)
def ink(A, B, u, seed, rim=1.0):
    F = noise_field(seed); thr = ss(u) * 1.06
    M = (F < thr).astype(np.float32)
    bandw = 4 + 18 * np.sin(np.pi * min(1, u))            # ink edge thickest mid-wipe
    return _reveal(A, B, M, bandw, rim) if 0 < thr < 1.05 else (enc(dec(B)) if thr >= 1.05 else A)
def drips(seed):
    r = np.random.default_rng(seed); x = np.arange(W, dtype=np.float32); d = np.zeros(W, np.float32)
    for _ in range(26):
        c = r.uniform(0, W); w = r.uniform(10, 45); a = r.uniform(0.15, 0.6)
        d += a * np.exp(-0.5 * ((x - c) / w) ** 2)
    d += 0.04 * cv2.resize(r.random((1, 40)).astype(np.float32), (W, 1), interpolation=cv2.INTER_CUBIC)[0]
    return d
def drip(A, B, u, seed):
    d = drips(seed); yy = np.arange(H, dtype=np.float32)[:, None] / H
    k = ss(u); bottom = -0.45 + k * 1.9 + d[None, :] * (0.6 + 0.3 * k)
    M = (yy < bottom).astype(np.float32)
    if M.mean() > 0.995: return B
    return _reveal(A, B, M, 7 + 10 * np.sin(np.pi * u), 1.0)
# ---------- pixel smear / glitch ----------
def smear(im, seed, amt=1.0, vertical=True, up=False):
    r = np.random.default_rng(seed); o = im.copy()
    if vertical:
        rr = (0.25 + 0.5 * cv2.resize(r.random((1, 30)).astype(np.float32), (W, 1), interpolation=cv2.INTER_CUBIC)[0]) * H
        rr = rr + (1 - amt) * H
        Y = np.arange(H)[:, None].repeat(W, 1); R = rr.astype(int)[None, :].clip(0, H - 1)
        sel = (Y > R) if not up else (Y < (H - R))
        o[sel] = im[R.repeat(H, 0)[sel], np.arange(W)[None, :].repeat(H, 0)[sel]]
    else:
        cc = ((0.3 + 0.4 * cv2.resize(r.random((30, 1)).astype(np.float32), (1, H), interpolation=cv2.INTER_CUBIC)[:, 0]) * W + (1 - amt) * W).astype(int).clip(0, W - 1)
        X = np.arange(W)[None, :].repeat(H, 0); sel = X > cc[:, None]
        o[sel] = im[np.arange(H)[:, None].repeat(W, 1)[sel], cc[:, None].repeat(W, 1)[sel]]
    return o
def glitch(im, seed, n=14, blow=0.35):
    r = np.random.default_rng(seed); o = im.copy(); lin = dec(o)
    for _ in range(n):
        h = int(r.uniform(12, 140)); y = int(r.uniform(0, H - h)); dx = int(r.choice([-1, 1]) * r.uniform(40, 260))
        o[y:y + h] = np.roll(o[y:y + h], dx, axis=1)
    k = int(r.uniform(6, 14)); o[..., 2] = np.roll(o[..., 2], k, axis=1); o[..., 0] = np.roll(o[..., 0], -k, axis=1)
    lin = dec(o)
    for _ in range(int(n * blow)):                                   # blown-out blocks (inspo 0:21)
        h = int(r.uniform(60, 260)); w = int(r.uniform(200, 900)); y = int(r.uniform(0, H - h)); x = int(r.uniform(0, W - w))
        lin[y:y + h, x:x + w] = lin[y:y + h, x:x + w] * 1.35 + 0.02
    return enc(lin)

# ---------- DEPTH-driven ink / drip (inspo 0:01 + 0:07): matte follows scene depth, background goes first ----------
DEP = G + "/inspo-transitions/depth_in/depth_%04d.png"
def depth(t):
    p = DEP % t
    if not os.path.exists(p): return None
    d = cv2.imread(p, -1).astype(np.float32) / 65535          # Depth Anything: 1 = near
    return cv2.bilateralFilter(d, 9, 0.08, 7)
def _dcomp(A, B, inkA, revB):
    """A outside the ink; inside the ink B shows wherever it has been revealed; black only in the overlap gap"""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    inkA = cv2.morphologyEx(inkA.astype(np.float32), cv2.MORPH_OPEN, k); revB = cv2.morphologyEx(revB.astype(np.float32), cv2.MORPH_OPEN, k)
    a = 1 - cv2.GaussianBlur(inkA, (0, 0), 1.0); bm = cv2.GaussianBlur(revB, (0, 0), 1.0) * (1 - a)
    out = A * a[..., None] + B * bm[..., None] + BLACK * (1 - a - bm)[..., None]
    ink = inkA * (1 - revB)
    d = cv2.distanceTransform((1 - ink).astype(np.uint8), cv2.DIST_L2, 3)
    rimm = cv2.GaussianBlur(np.clip(1 - np.abs(d - 2.5) / 2.5, 0, 1).astype(np.float32), (0, 0), 1.2) * (0.002 < ink.mean() < 0.995)
    return enc(dec(out) + (rimm * 0.75)[..., None] * RIM)
def _q(key, frac):
    """mask of the top `frac` of key values"""
    if frac <= 0.001: return np.zeros_like(key, bool)
    if frac >= 0.999: return np.ones_like(key, bool)
    return key >= np.quantile(key, 1 - frac)
def depth_ink(A, B, dA, dB, u, seed):
    F = noise_field(seed, ((180, 1.0), (60, 0.5), (18, 0.25)))
    fa = ss(u / 0.6); fb = ss((u - 0.12) / 0.75)
    inkA = _q((1 - dA) * 0.82 + 0.18 * F, fa)       # far of A inked first
    revB = _q(dB * 0.82 + 0.18 * F, fb)             # near of B revealed first
    return _dcomp(A, B, inkA, revB)
def depth_drip(A, B, dA, dB, u, seed):
    dr = drips(seed); yy = np.arange(H, dtype=np.float32)[:, None] / H
    fa = ss(u / 0.6); fb = ss((u - 0.12) / 0.75)
    keyA = (1 - dA) * 0.5 + (1 - yy) * 0.5 + dr[None, :] * 0.35   # top + far first, drippy edge
    inkA = _q(keyA, fa)
    revB = _q(dB * 0.85 + dr[None, :] * 0.15, fb)
    return _dcomp(A, B, inkA, revB)
def dink_tr(cut, n_out=4, n_in=4, seed=1, fn=None):
    fn = fn or depth_ink; n = n_out + n_in
    for i, t in enumerate(range(cut - n_out, cut + n_in)):
        u = (i + 0.5) / n
        a = under(min(t, cut - 1)); b = base(max(t, cut))
        da = depth(min(t, cut - 1)); db = depth(max(t, cut))
        if da is None or db is None: raise SystemExit("missing depth for %d" % t)
        yield t, fn(a, b, da, db, u, seed)
def ddrip_tr(cut, seed=2): return dink_tr(cut, 3, 4, seed, depth_drip)


# ---------- DEPTH HEATMAP (inspo 0:05 green, 0:08 fire, 0:27 blue): shot becomes a colourised, pixelated depth map ----------
PAL = {   # BGR scene-linear stops, far -> near
 "fire": [(0.0, (0.0, 0.0, 0.0)), (0.25, (0.0, 0.0, 0.18)), (0.5, (0.0, 0.02, 0.75)), (0.72, (0.0, 0.22, 1.6)), (0.88, (0.05, 0.7, 2.4)), (1.0, (0.6, 1.8, 3.2))],
 "ice":  [(0.0, (0.0, 0.0, 0.0)), (0.3, (0.16, 0.02, 0.0)), (0.55, (0.9, 0.18, 0.0)), (0.78, (2.0, 0.7, 0.1)), (1.0, (3.2, 2.2, 1.4))],
 "maize":[(0.0, (0.0, 0.0, 0.0)), (0.3, (0.12, 0.02, 0.0)), (0.55, (0.3, 0.12, 0.05)), (0.78, (0.05, 0.75, 1.3)), (1.0, (0.35, 2.0, 2.8))],
}
def heat(d, pal, gamma=1.0):
    x = np.clip(d, 0, 1) ** gamma; stops = PAL[pal]; out = np.zeros(d.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        m = (x >= a) & (x <= b); w = ((x - a) / (b - a + 1e-6))[..., None]
        out[m] = (np.array(ca) * (1 - w) + np.array(cb) * w)[m]
    return out
def pix(img, b):
    if b <= 1: return img
    s = cv2.resize(img, (max(1, W // b), max(1, H // b)), interpolation=cv2.INTER_AREA)
    return cv2.resize(s, (W, H), interpolation=cv2.INTER_NEAREST)
def heat_frame(t, pal, block, mix, near_first=True, seed=0):
    """mix 0 = footage, 1 = full heatmap; heat takes over FAR-first (or reveals footage NEAR-first on the way out)"""
    src = under(t); d = depth(t)
    if d is None: raise SystemExit("missing depth %d" % t)
    r = np.random.default_rng(seed + t)
    dd = d + 0.015 * r.normal(size=d.shape).astype(np.float32)            # slight sensor-ish shimmer
    hm = heat(pix(dd, block), pal, 1.1)
    if mix >= 0.999: lin = hm
    else:
        key = (1 - d) if near_first else d
        m = (key >= np.quantile(key, 1 - mix)).astype(np.float32) if mix > 0.001 else np.zeros_like(d)
        m = pix(cv2.GaussianBlur(m, (0, 0), 1.0), max(1, block))
        lin = dec(src) * (1 - m[..., None]) + hm * m[..., None]
    return enc(lin)
def heat_tr(cut, pal="fire", seed=0):
    """A: heat floods in far-first (3f) -> full pixel heat (2f, blocks grow) || B: full heat (2f, blocks shrink) -> footage returns near-first (3f)"""
    seq = [(cut - 5, 0.3, 1), (cut - 4, 0.65, 2), (cut - 3, 1.0, 6), (cut - 2, 1.0, 14), (cut - 1, 1.0, 30),
           (cut, 1.0, 24), (cut + 1, 1.0, 10), (cut + 2, 0.7, 4), (cut + 3, 0.35, 2), (cut + 4, 0.1, 1)]
    for t, mix, b in seq:
        yield t, heat_frame(t, pal, b, mix, near_first=(t < cut), seed=seed)


# ---------- v5b: BLOCKY pixel heat (grid steps, not organic) ----------
def block_order(d, cell, seed, far_first=True, rnd=0.3):
    """per-cell order key: cell-average depth (far first) + a little random so cells pop in stepped clusters"""
    hc, wc = H // cell + 1, W // cell + 1
    small = cv2.resize(d, (wc, hc), interpolation=cv2.INTER_AREA)
    r = np.random.default_rng(seed).random((hc, wc)).astype(np.float32)
    k = ((1 - small) if far_first else small) * (1 - rnd) + r * rnd
    return cv2.resize(k, (wc * cell, hc * cell), interpolation=cv2.INTER_NEAREST)[:H, :W]
def heat_frame_b(t, pal, block, frac, far_first, seed):
    src = under(t) if t < 9999 else None; d = depth(t)
    if d is None: raise SystemExit("missing depth %d" % t)
    q = max(1, block)
    dq = np.round(pix(d, q) * 16) / 16                                  # posterised depth = chunky pixel levels
    hm = heat(dq, pal, 1.1)
    if frac >= 0.999: return enc(hm)
    if frac <= 0.001: return enc(dec(src))
    key = block_order(d, 16, seed, far_first)
    m = (key >= np.quantile(key, 1 - frac)).astype(np.float32)
    return enc(dec(src) * (1 - m[..., None]) + hm * m[..., None])
def heat_tr(cut, pal="fire", seed=0):
    seq = [(cut - 5, 0.18, 6, True), (cut - 4, 0.45, 6, True), (cut - 3, 0.8, 8, True), (cut - 2, 1.0, 10, True), (cut - 1, 1.0, 14, True),
           (cut, 1.0, 14, False), (cut + 1, 1.0, 10, False), (cut + 2, 0.75, 8, False), (cut + 3, 0.4, 6, False), (cut + 4, 0.12, 6, False)]
    for t, frac, b, ff in seq:
        if t < cut: yield t, heat_frame_b(t, pal, b, frac, True, seed)
        else:
            src = base(t); d = depth(t); dq = np.round(pix(d, b) * 16) / 16; hm = heat(dq, pal, 1.1)
            if frac >= 0.999: yield t, enc(hm); continue
            key = block_order(d, 16, seed + 7, far_first=False)        # footage comes back near-first, in blocks
            m = (key >= np.quantile(key, frac)).astype(np.float32)       # m = revealed footage
            yield t, enc(dec(src) * m[..., None] + hm * (1 - m[..., None]))
# ---------- v5b: KINETIC SLICE (smooth eased band slides, motion blur, light RGB split) ----------
def ease_io(x): x = np.clip(x, 0, 1); return 0.5 - 0.5 * np.cos(np.pi * x)
def bands(seed, n=7):
    r = np.random.default_rng(seed); cuts = np.sort(r.uniform(0.08, 0.92, n - 1)); edges = np.r_[0, cuts, 1] * H
    return [(int(edges[i]), int(edges[i + 1]), r.uniform(0.7, 1.3) * (1 if i % 2 == 0 else -1)) for i in range(n)]
def slide(img, bnds, off, blur):
    out = img.copy()
    for y0, y1, sp in bnds:
        dx = off * sp; band = img[y0:y1]
        M = np.float32([[1, 0, dx], [0, 1, 0]]); sh = cv2.warpAffine(band, M, (W, y1 - y0), borderMode=cv2.BORDER_WRAP)
        L = int(abs(blur * sp))
        if L > 2: k = np.zeros((1, 2 * L + 1), np.float32); k[0, L:] = 1 if dx > 0 else 0; k[0, :L + 1] += 0 if dx > 0 else 1; sh = cv2.filter2D(sh, -1, k / k.sum())
        out[y0:y1] = sh
    return out
def rgb(img, k):
    if k < 1: return img
    o = img.copy(); o[..., 2] = np.roll(img[..., 2], k, 1); o[..., 0] = np.roll(img[..., 0], -k, 1); return o
def slice_tr(cut, seed=3, vertical=False):
    """A's bands slide out with ease-in, B's bands slide in with ease-out: 3f out, 3f in"""
    b = bands(seed)
    for i, t in enumerate(range(cut - 3, cut + 3)):
        if t < cut:
            u = (i + 1) / 3.0; off = ease_io(u) ** 2 * W * 0.55; im = slide(under(t), b, off, off * 0.35)
            yield t, rgb(im, int(2 + 6 * u))
        else:
            u = (t - cut) / 3.0; off = -(1 - ease_io(u + 0.34)) ** 2 * W * 0.55; im = slide(base(t), b, off, abs(off) * 0.35)
            yield t, rgb(im, int(6 * (1 - u)))


# ---------- v5d: depth-pixel heat with WIGGLE (wigglegram parallax) + tile depth ----------
def _grid_edges(b, off):
    yy, xx = np.mgrid[:H, :W]
    gx = (xx + off[0]) % b; gy = (yy + off[1]) % b
    hi = ((gx == 0) | (gy == 0)).astype(np.float32); lo = ((gx == b - 1) | (gy == b - 1)).astype(np.float32)
    return hi, lo
def heat_img(t, d, pal, b, seed=0):
    """near pixels sway more (parallax wiggle on ~6f period), near blocks 2x bigger, bevelled tiles"""
    ph = 2 * np.pi * (t % 6) / 6.0
    ax, ay = 16.0 * np.sin(ph), 6.0 * np.cos(ph)
    xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    d = d.astype(np.float32); dw = cv2.remap(d, (xx - ax * (d - 0.35)).astype(np.float32), (yy - ay * (d - 0.35)).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    r = np.random.default_rng(seed * 31 + t)
    jit = (int(r.integers(0, b)), int(r.integers(0, b)))            # grid crawls a little each frame
    def pixo(img, bb, off):
        im = np.roll(np.roll(img, off[1], 0), off[0], 1); p = pix(im, bb); return np.roll(np.roll(p, -off[1], 0), -off[0], 1)
    pf = pixo(dw, b, jit); pn = pixo(dw, b * 2, jit)
    near = (pn > 0.55).astype(np.float32)
    dq = np.round((pf * (1 - near) + pn * near) * 16) / 16
    hm = heat(dq, pal, 1.1)
    hf, lf = _grid_edges(b, jit); hn, ln = _grid_edges(b * 2, jit)
    hi = hf * (1 - near) + hn * near; lo = lf * (1 - near) + ln * near
    shade = 1 + 0.22 * hi - 0.35 * lo
    return hm * shade[..., None]
def heat_tr(cut, pal="fire", seed=0):
    seq = [(cut - 5, 0.18, 6), (cut - 4, 0.45, 6), (cut - 3, 0.8, 8), (cut - 2, 1.0, 8), (cut - 1, 1.0, 10),
           (cut, 1.0, 10), (cut + 1, 1.0, 8), (cut + 2, 0.75, 8), (cut + 3, 0.4, 6), (cut + 4, 0.12, 6)]
    for t, frac, b in seq:
        d = depth(t)
        if d is None: raise SystemExit("missing depth %d" % t)
        hm = heat_img(t, d, pal, b, seed)
        if t < cut:
            src = under(t)
            if frac >= 0.999: yield t, enc(hm); continue
            key = block_order(d, 16, seed, True); m = (key >= np.quantile(key, 1 - frac)).astype(np.float32)
            yield t, enc(dec(src) * (1 - m[..., None]) + hm * m[..., None])
        else:
            src = base(t)
            if frac >= 0.999: yield t, enc(hm); continue
            key = block_order(d, 16, seed + 7, far_first=False); m = (key >= np.quantile(key, frac)).astype(np.float32)
            yield t, enc(dec(src) * m[..., None] + hm * (1 - m[..., None]))


# ---------- v5e: LED dot-matrix depth (inspo 0:05 / 0:27), wavy + wiggle ----------
PAL.update({
 "navy_led": [(0.0, (0.010, 0.002, 0.0)), (0.3, (0.035, 0.008, 0.001)), (0.55, (0.08, 0.02, 0.003)), (0.75, (0.35, 0.10, 0.02)), (0.9, (1.1, 0.55, 0.25)), (1.0, (2.4, 1.8, 1.4))],
 "gray_led": [(0.0, (0.0, 0.0, 0.0)), (0.3, (0.012, 0.012, 0.012)), (0.55, (0.12, 0.12, 0.12)), (0.78, (0.65, 0.65, 0.65)), (0.92, (1.8, 1.8, 1.8)), (1.0, (2.8, 2.8, 2.8))],
 "maize_led": [(0.0, (0.0, 0.0, 0.0)), (0.22, (0.01, 0.006, 0.0)), (0.45, (0.0, 0.10, 0.22)), (0.7, (0.02, 0.55, 0.95)), (0.88, (0.25, 1.5, 2.2)), (1.0, (1.6, 2.6, 3.0))],
 "blue_led":  [(0.0, (0.0, 0.0, 0.0)), (0.25, (0.06, 0.005, 0.0)), (0.5, (0.45, 0.06, 0.0)), (0.75, (1.6, 0.45, 0.02)), (0.9, (2.6, 1.4, 0.4)), (1.0, (3.0, 2.6, 2.0))],
})
CELL = 6
_yy, _xx = np.mgrid[:H, :W].astype(np.float32)
_cx = ((_xx % CELL) - (CELL - 1) / 2) / CELL; _cy = ((_yy % CELL) - (CELL - 1) / 2) / CELL
DOT = np.clip((0.44 - np.sqrt(_cx ** 2 + _cy ** 2)) / 0.08, 0, 1).astype(np.float32)        # round LED dots
def led_depth(t, d, seed=0):
    """wavy + wiggling depth, resampled on the LED grid"""
    ph = 2 * np.pi * t / 7.0
    dx = 9.0 * np.sin(2 * np.pi * _yy / 260.0 + ph) + 14.0 * np.sin(ph * 0.9) * (d - 0.3)      # rolling wave + parallax wiggle
    dy = 6.0 * np.sin(2 * np.pi * _xx / 340.0 - ph * 1.3) + 5.0 * np.cos(ph * 0.9) * (d - 0.3)
    dw = cv2.remap(d.astype(np.float32), (_xx - dx).astype(np.float32), (_yy - dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    sm = cv2.resize(dw, (W // CELL, H // CELL), interpolation=cv2.INTER_AREA)
    sm = sm + 0.012 * np.random.default_rng(seed * 13 + t).normal(size=sm.shape).astype(np.float32)   # LED shimmer
    return cv2.resize(sm, (W // CELL * CELL, H // CELL * CELL), interpolation=cv2.INTER_NEAREST)[:H, :W] if W % CELL == 0 and H % CELL == 0 else cv2.resize(sm, (W, H), interpolation=cv2.INTER_NEAREST)
def led_img(t, d, pal, seed=0):
    lo, hi = np.percentile(d, 2), np.percentile(d, 99.5)              # per-frame depth normalise: no shot goes black
    d = (np.clip((d - lo) / max(hi - lo, 1e-3), 0, 1) * 0.92 + 0.04).astype(np.float32)
    dl = led_depth(t, d, seed)
    hm = heat(dl, pal, 1.15)
    glow = cv2.GaussianBlur(hm, (0, 0), 3.0)
    return hm * DOT[..., None] + glow * 0.18
_DG = {}
def edge_arcs(L, core, m, rng, n, inten, width, pad=14, d=None):
    """contour arcs only on real object silhouettes: not on the frame border, and only where depth jumps (not floor bands)"""
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs: return
    c = max(cs, key=len)[:, 0, :].astype(float); N = len(c)
    ok = (c[:, 0] > pad) & (c[:, 0] < W - pad) & (c[:, 1] > pad) & (c[:, 1] < H - pad)
    if d is not None:
        g = cv2.GaussianBlur(np.hypot(cv2.Sobel(d, cv2.CV_32F, 1, 0, ksize=5), cv2.Sobel(d, cv2.CV_32F, 0, 1, ksize=5)), (0, 0), 3)
        gv = g[c[:, 1].astype(int).clip(0, H - 1), c[:, 0].astype(int).clip(0, W - 1)]
        ok &= gv > np.quantile(g, 0.9)
    idx = np.where(ok)[0]
    if len(idx) < 40: return
    for _ in range(n):
        i = rng.choice(idx); Ln = int(rng.uniform(40, 150)); ids = (i + np.arange(0, Ln, 5)) % N
        bad = np.where(~ok[ids])[0]; ids = ids[: bad[0]] if len(bad) else ids
        if len(ids) < 4: continue
        p = c[ids]; d = np.gradient(p, axis=0); nr = np.stack([-d[:, 1], d[:, 0]], 1); nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-6
        p = p + nr * rng.uniform(1, 5) + rng.normal(0, 2.2, p.shape)
        L.draw(core, [(p, width, width * 0.4, inten)])
def near_mask(d, q=0.86):
    m = (cv2.GaussianBlur(d, (0, 0), 3) > np.quantile(d, q)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for i in range(1, n):                                     # drop thin edge slivers (tunnel wall etc.)
        x, y, w, h, a = st[i]
        if a > 4000 and w > 150 and h > 150: keep[lab == i] = 1
    return keep
def strike_on(lin, d, t, cut, seed, L):
    """goal-grammar lightning on the LED snap: charge arcs (cut-1), strike into the nearest object (cut), held restrike + crackle (cut+1..+3)"""
    k = t - cut
    if k < -6 or k > 15: return lin
    rng = np.random.default_rng(seed * 7 + t // 2); core = np.zeros((H, W), np.float32)
    nm = near_mask(d); spill = 0.25; wfl = 0.0
    ys, xs = np.nonzero(nm); c = np.array([np.median(xs), ys.min() + 6.0]) if len(xs) else np.array([960.0, 420.0])
    gs = seed * 101 + max(0, k) // 3                                  # channel re-forms every restrike (3f)
    geo = L.channel(np.array([c[0] + np.random.default_rng(gs).uniform(-300, 300), -40.0]), c, np.random.default_rng(gs + 1), rough=0.17, branch=1.2, w0=9.0, i0=1.0)
    if k < 0: u = (k + 7) / 6.0; edge_arcs(L, core, nm, rng, int(3 + 9 * u), 0.25 + 0.5 * u, 1.6 + 0.6 * u, d=d)
    elif k == 0: L.draw(core, geo); edge_arcs(L, core, nm, rng, 8, 0.8, 2.4, d=d); spill = 1.1; wfl = 0.3
    else:
        e = (0.55, 0.9, 0.45, 0.75, 0.3, 0.6, 0.25, 0.85, 0.4, 0.2, 0.5, 0.15, 0.3, 0.1, 0.05)[k - 1]; L.draw(core, [(p, a, b, i * e) for p, a, b, i in geo]); edge_arcs(L, core, nm, rng, 4, 0.35 + 0.4 * e, 1.8, d=d); spill = 0.5 * e
    core *= float(np.clip(np.random.default_rng(900 + t).normal(1, 0.2), 0.65, 1.3))
    alb = L.lum((enc(lin) * 255).clip(0, 255).astype(np.uint8))
    return lin + L.finish(core, alb, None, spill, 0.0, refl_gain=0.0, white_flash=wfl, bg_lin=lin)
def led_tr(cut, pal="maize_led", seed=0, bolt=True):
    """footage dissolves into LED depth cell-by-cell (far first), LED holds + waves, snaps to B's LED (lightning strike), B returns near-first"""
    L = _L() if bolt else None
    ramp_in = [0.06, 0.18, 0.38, 0.62, 0.85]                    # cut-14 .. cut-10
    ramp_out = [0.85, 0.62, 0.38, 0.18, 0.06]                   # cut+12 .. cut+16
    seq = [(cut - 14 + i, f) for i, f in enumerate(ramp_in)] + [(t, 1.0) for t in range(cut - 9, cut + 12)] + [(cut + 12 + i, f) for i, f in enumerate(ramp_out)]
    for t, frac in seq:
        d = depth(t)
        if d is None: raise SystemExit("missing depth %d" % t)
        d = np.minimum(d, cv2.dilate(cv2.erode(d, np.ones((1, 181), np.float32), borderType=cv2.BORDER_CONSTANT, borderValue=0), np.ones((1, 181), np.float32), borderType=cv2.BORDER_REFLECT) + 0.08)
        hm = led_img(t, d, pal, seed)
        src = under(t) if t < cut else base(t)
        if frac >= 0.999: lin = hm
        else:
            key = block_order(cv2.GaussianBlur(d, (0, 0), 6), CELL, seed + (0 if t < cut else 7), far_first=(t < cut), rnd=0.08)
            m = (key >= np.quantile(key, 1 - frac)).astype(np.float32)
            lin = dec(src) * (1 - m[..., None]) + hm * m[..., None]
        if bolt: lin = strike_on(lin, d, t, cut, seed, L)
        yield t, enc(lin)
# ---------- v5e: DEPTH-PARALLAX PUSH (near layers move faster than far; motion-blurred) ----------
def dpush(img, d, amt, dirv, zoom, n=8):
    """virtual camera orbit + dolly: near and far layers move OPPOSITE ways around a pivot at mid-depth"""
    acc = np.zeros_like(img)
    dd = cv2.GaussianBlur(np.clip(d, 0, 1).astype(np.float32), (0, 0), 28); piv = float(np.median(dd))
    par = np.clip((dd - piv) * 1.1, -0.35, 0.35)                                   # signed parallax (near +, far -)
    wz = 0.2 + 0.8 * dd ** 1.4                               # dolly weight (near grows faster)
    for i in range(n):
        k = amt * (i + 1) / n
        mx = _xx - dirv[0] * k * W * par - (_xx - W / 2) * zoom * k * wz
        my = _yy - dirv[1] * k * H * par - (_yy - H / 2) * zoom * k * wz
        acc += cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return acc / n
def dpush_tr(cut, seed=3, dirv=(1.0, 0.0)):
    dv = np.array(dirv, np.float32)
    for t, u in ((cut - 3, 0.025), (cut - 2, 0.08), (cut - 1, 0.2)):
        d = depth(t); yield t, enc(dpush(dec(under(t)), d, u, dv * 0.9, 0.45, 28))
    for t, u in ((cut, 0.18), (cut + 1, 0.07), (cut + 2, 0.02)):
        d = depth(t); yield t, enc(dpush(dec(base(t)), d, -u, dv * 0.9, 0.45, 28))


# ---------- v5e ENDING: fans -> maize LED depth on the downbeat (lightning restrike) -> LED holds/waves -> dots switch off ----------
def _L():
    import importlib; cwd = os.getcwd(); sys.path.insert(0, G + "/puck-lightning/tools"); L = importlib.import_module("lightning_v5"); os.chdir(cwd)
    L.HOTL = np.array([0.78, 0.97, 1.0], np.float32); L.PINKL = np.array([0.08, 0.78, 1.0], np.float32); L.REDL = np.array([0.0, 0.45, 1.0], np.float32)   # MAIZE lightning in transitions
    return L
BM = G + "/m-logo/blockm_depth_exr/bm_%04d.exr"
def m_depth(t, drop=479):
    """Block M depth (near=1) + alpha for tl t (render f1 = drop)"""
    f = min(t - drop + 1, 13)                                   # freezes on the strike (f13 = lock)
    if f < 1 or not os.path.exists(BM % f): return None, None
    sys.path.insert(0, G + "/tools"); from read_rgba import read_rgba
    rgb, A = read_rgba(BM % f); z = rgb[..., 0]
    return np.clip(0.55 + (z - 0.33) * 1.1, 0, 1).astype(np.float32) * (A > 0.02), A.astype(np.float32)
def end_tr(drop=479, lock=491, off=515, last=526, pal="navy_led", seed=5):
    L = _L()
    for t in range(467, drop):                                   # slow depth push-in on the fans (near grows faster)
        d = depth(t); u = (t - 467) / (drop - 467)
        yield t, enc(dpush(dec(base(t)), d, 0.02 + 0.06 * u * u, np.array([0.0, 0.0], np.float32), 0.9, 16))
    for t in range(drop, last + 1):
        d = depth(t); md, A = m_depth(t, drop)
        dd = d * 0.72
        hm = led_img(t, dd, pal, seed)                               # crowd field waves + wiggles
        if md is not None:                                         # Block M: crisp (no wave), same LED dots, lit by depth
            yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
            mz = np.clip(md * (0.92 + 0.08 * (1 - yy)), 0, 1)
            sm = cv2.resize(mz, (W // CELL, H // CELL), interpolation=cv2.INTER_AREA)
            mq = cv2.resize(sm, (W, H), interpolation=cv2.INTER_NEAREST)
            mh = heat(mq, pal, 1.15); mh = mh * DOT[..., None] + cv2.GaussianBlur(mh, (0, 0), 3.0) * 0.18
            a = cv2.GaussianBlur(A, (0, 0), 1.0)[..., None]
            cz = {lock: 1.0}.get(t, 1.0 if t > lock else 0.0)      # zapped -> Michigan maize + navy
            if cz > 0:
                MAIZE = np.array([0.0015, 0.47, 1.0], np.float32) * 1.7         # #FFCB05 (BGR, linear)
                NAVY = np.array([0.072, 0.020, 0.0], np.float32) * 2.2           # #00274C
                mc = MAIZE * np.ones_like(mq)[..., None]                       # flat 2D logo: no depth shading
                mc = mc * DOT[..., None] + cv2.GaussianBlur(mc, (0, 0), 3.0) * 0.22
                mh = mh * (1 - cz) + mc * cz
                ring = np.clip(cv2.dilate((A > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))).astype(np.float32) - (A > 0.5), 0, 1)
                ring = cv2.GaussianBlur(ring, (0, 0), 1.0)[..., None] * cz
                hm = hm * (1 - ring) + (NAVY[None, None, :] * np.ones((H, W, 1), np.float32)) * ring
            if t >= lock:                                                    # 2D: crisp solid fill, no LED dots on the M
                mh = MAIZE[None, None, :] * np.ones((H, W, 1), np.float32)
            hm = hm * (1 - a) + mh * a
            dd = np.maximum(dd, md * (A > 0.5))
        rng = np.random.default_rng(700 + t // 2); core = np.zeros((H, W), np.float32); spill = 0.0; wfl = 0.0
        mm = (A > 0.5).astype(np.uint8) if A is not None else None
        if t == drop:                                            # drop: strike into the crowd as it turns to LED
            nm = near_mask(d); ys, xs = np.nonzero(nm); c = np.array([np.median(xs), ys.min() + 5.0])
            L.draw(core, L.channel(np.array([c[0] + 220, -40.0]), c, np.random.default_rng(91), rough=0.17, branch=1.0, w0=6.0, i0=1.0)); spill = 1.0; wfl = 0.3
        if mm is not None and mm.sum() > 2000:
            k = t - lock
            ys, xs = np.nonzero(mm); top = np.array([xs.mean(), ys.min() + 4.0])
            if -3 <= k < 0: edge_arcs(L, core, mm, rng, 4 + 3 * (k + 3), 0.4 + 0.15 * (k + 3), 1.6)
            elif k == 0:
                geo = L.channel(np.array([top[0] - 260, -40.0]), top, np.random.default_rng(1491), rough=0.17, branch=1.1, w0=7.0, i0=1.0)
                L.draw(core, geo); edge_arcs(L, core, mm, rng, 26, 1.0, 2.8); spill = 1.2; wfl = 0.35
            elif 0 < k <= 22:
                e = 0.88 ** k
                if k in (1, 3, 9):
                    geo = L.channel(np.array([top[0] - 260, -40.0]), top, np.random.default_rng(1491), rough=0.17, branch=1.1, w0=6.0, i0=0.8 * e + 0.2)
                    L.draw(core, geo)
                edge_arcs(L, core, mm, rng, int(5 + 14 * e), 0.3 + 0.6 * e, 1.5 + e); spill = 0.5 * e
        lin = hm
        if core.max() > 0:
            core *= float(np.clip(np.random.default_rng(900 + t).normal(1, 0.2), 0.65, 1.3))
            alb = L.lum((enc(lin) * 255).clip(0, 255).astype(np.uint8))
            lin = lin + L.finish(core, alb, None, spill, 0.0, refl_gain=0.0, white_flash=wfl, bg_lin=lin)
        if t >= off:
            frac = ss((t - off + 1) / (last - off + 1)) ** 0.8
            key = block_order(cv2.GaussianBlur(dd, (0, 0), 6), CELL, seed + 3, far_first=True, rnd=0.15)
            m = (key >= np.quantile(key, 1 - frac)).astype(np.float32) if frac < 0.999 else np.ones_like(d)
            lin = lin * (1 - m[..., None]) + (-0.003) * m[..., None]
        yield t, enc(lin)


# ---------- v17: fine LED depth (4px), people pop, smooth melts + depth morph across the cut ----------
CELL2 = 4
_cx2 = ((_xx % CELL2) - (CELL2 - 1) / 2) / CELL2; _cy2 = ((_yy % CELL2) - (CELL2 - 1) / 2) / CELL2
DOT2 = np.clip((0.46 - np.sqrt(_cx2 ** 2 + _cy2 ** 2)) / 0.10, 0, 1).astype(np.float32)
PAL["navy2"] = [(0.0, (0.006, 0.0015, 0.0)), (0.25, (0.045, 0.012, 0.002)), (0.45, (0.2, 0.06, 0.01)), (0.62, (0.55, 0.2, 0.05)),
                (0.78, (0.95, 0.45, 0.16)), (0.9, (1.8, 1.1, 0.6)), (1.0, (2.8, 2.3, 1.9))]
def ndepth(d):
    d = np.minimum(d, cv2.dilate(cv2.erode(d.astype(np.float32), np.ones((1, 181), np.float32), borderType=cv2.BORDER_CONSTANT, borderValue=0), np.ones((1, 181), np.float32)) + 0.10)   # kill thin edge slivers (tunnel wall)
    lo, hi = np.percentile(d, 1), np.percentile(d, 99.7)
    return np.clip((d - lo) / max(hi - lo, 1e-3), 0, 1).astype(np.float32)
def led2(t, d, src, pal="navy2"):
    """fine LED depth: gentle wave + parallax wiggle, rim on silhouettes, a touch of footage luma for detail"""
    d = ndepth(d)
    ph = 2 * np.pi * t / 8.0
    dx = 5.0 * np.sin(2 * np.pi * _yy / 300.0 + ph) + 9.0 * np.sin(ph * 0.9) * (d - 0.4)
    dy = 3.0 * np.sin(2 * np.pi * _xx / 420.0 - ph * 1.2) + 3.0 * np.cos(ph * 0.9) * (d - 0.4)
    mx, my = (_xx - dx).astype(np.float32), (_yy - dy).astype(np.float32)
    dw = cv2.remap(d, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    lum = cv2.cvtColor(np.clip(src, 0, 1).astype(np.float32), cv2.COLOR_BGR2GRAY)
    lum = cv2.remap(lum, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    lum = (lum - lum.mean()) / (lum.std() + 1e-3)
    g = cv2.GaussianBlur(np.hypot(cv2.Sobel(dw, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(dw, cv2.CV_32F, 0, 1, ksize=3)), (0, 0), 1.5)
    rim = np.clip(g / (np.quantile(g, 0.985) + 1e-4), 0, 1) * np.clip(dw * 1.5 - 0.2, 0, 1)
    loc = dw - cv2.GaussianBlur(dw, (0, 0), 45)                            # how much each object stands out from its surroundings
    loc = np.clip(loc / (np.quantile(np.abs(loc), 0.995) + 1e-4), -1, 1)
    v = np.clip(0.18 + 0.42 * dw + 0.55 * np.maximum(loc, 0) - 0.15 * np.maximum(-loc, 0) + 0.05 * lum + 0.12 * rim, 0, 1)
    sm = cv2.resize(v, (W // CELL2, H // CELL2), interpolation=cv2.INTER_AREA)
    q = cv2.resize(sm, (W, H), interpolation=cv2.INTER_NEAREST)
    hm = heat(q, pal, 1.0)
    return hm * DOT2[..., None] + cv2.GaussianBlur(hm, (0, 0), 2.0) * 0.22
def melt(foot, led, d, u, far_first=True):
    """smooth depth-ordered dissolve: u 0 -> footage, 1 -> LED; soft band, no blocks"""
    d = ndepth(cv2.GaussianBlur(d, (0, 0), 4)); key = (1 - d) if far_first else d
    key = cv2.GaussianBlur(key, (0, 0), 25)
    a = np.clip((u - 0.3 * (1 - key)) / 0.7, 0, 1); a = a * a * (3 - 2 * a)
    return foot * (1 - a[..., None]) + led * a[..., None]
def led_tr2(cut, seed=0, pal="navy2", n_in=6, hold_a=6, morph=4, hold_b=8, n_out=7, bolt=True):
    L = _L() if bolt else None
    t0 = cut - hold_a - n_in - morph // 2
    for t in range(t0, cut + morph // 2 + hold_b + n_out):
        d = depth(t)
        if d is None: raise SystemExit("missing depth %d" % t)
        src_lin = dec(under(t) if t < cut else base(t))
        if cut - morph // 2 <= t < cut + morph // 2:            # morph: A's LED depth -> B's LED depth (cross-dissolve of fields)
            ta, tb = cut - morph // 2 - 1, cut + morph // 2
            u = (t - (cut - morph // 2) + 1) / (morph + 1); u = u * u * (3 - 2 * u)
            la = led2(t, depth(min(t, cut - 1)), dec(under(min(t, cut - 1))), pal); lb = led2(t, depth(max(t, cut)), dec(base(max(t, cut))), pal)
            lin = la * (1 - u) + lb * u
        else:
            led = led2(t, d, src_lin, pal)
            if t < cut:
                u = (t - t0 + 1) / n_in
                lin = led if u >= 1 else melt(src_lin, led, d, u, True)
            else:
                k = t - (cut + morph // 2 + hold_b)
                u = 1 - (k + 1) / n_out if k >= 0 else 1.0
                lin = led if u >= 1 else melt(src_lin, led, d, u, True)
        if bolt: lin = strike_on(lin, d, t, cut, seed, L)
        yield t, enc(lin)


# ---------- v18: reference structure — hard cut in, clean high-contrast depth hold, streak out ----------
CELL3 = 5
_cy3, _cx3 = np.mgrid[0:H, 0:W]; _cy3 = (_cy3 % CELL3 + 0.5) / CELL3 - 0.5; _cx3 = (_cx3 % CELL3 + 0.5) / CELL3 - 0.5
DOT3 = np.clip((0.40 - np.sqrt(_cx3 ** 2 + _cy3 ** 2)) / 0.07, 0, 1).astype(np.float32)   # crisp dots, dark gaps
PAL["navy3"] = [(0.0, (0.004, 0.001, 0.0)), (0.22, (0.03, 0.008, 0.001)), (0.4, (0.16, 0.04, 0.006)), (0.58, (0.5, 0.15, 0.025)),
                 (0.74, (1.0, 0.38, 0.08)), (0.87, (1.6, 0.85, 0.35)), (1.0, (2.6, 2.1, 1.6))]
def led3(t, d, pal="navy3"):
    """pure depth (no footage texture): far -> black, people glow, nearest clips toward white; slow subtle wobble"""
    d = ndepth(d)
    ph = 2 * np.pi * t / 16.0
    dx = 2.5 * np.sin(2 * np.pi * _yy / 360.0 + ph) + 4.0 * np.sin(ph * 0.7) * (d - 0.4)
    dy = 1.5 * np.sin(2 * np.pi * _xx / 500.0 - ph) + 2.0 * np.cos(ph * 0.7) * (d - 0.4)
    dw = cv2.remap(d, (_xx - dx).astype(np.float32), (_yy - dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    loc = dw - cv2.GaussianBlur(dw, (0, 0), 60)
    loc = np.clip(loc / (np.quantile(np.abs(loc), 0.995) + 1e-4), -1, 1)
    v = 0.08 + 0.58 * ss(dw / 0.9) ** 0.7 + 0.30 * np.maximum(loc, 0) - 0.08 * np.maximum(-loc, 0)
    v = np.clip(v, 0, 0.86)
    sm = cv2.resize(v, (W // CELL3, H // CELL3), interpolation=cv2.INTER_AREA)
    q = cv2.resize(sm, (W, H), interpolation=cv2.INTER_NEAREST)
    hm = heat(q, pal, 1.0)
    return hm * DOT3[..., None] + cv2.GaussianBlur(hm, (0, 0), 3.0) * 0.12
def whip(img, amt, dirv=(1.0, 0.0), n=14):
    """directional motion smear of length amt px"""
    if amt < 1: return img
    acc = np.zeros_like(img)
    for i in range(n):
        o = (i / (n - 1) - 0.5) * amt
        M = np.float32([[1, 0, o * dirv[0]], [0, 1, o * dirv[1]]])
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return acc / n
def glitch3(foot, led, seed):
    """one transitional frame like the ref: blue-tinted smeared footage + coarse depth blocks"""
    rng = np.random.default_rng(seed)
    a = whip(foot, 260)
    lum = cv2.cvtColor(np.clip(a, 0, 1), cv2.COLOR_BGR2GRAY)[..., None]
    tint = lum * np.array([1.0, 0.45, 0.12], np.float32) * 1.3
    blk = pix(led, 24)
    out = tint * 0.30 + blk * 0.55
    for _ in range(9):                                  # a few horizontal slabs offset
        y = int(rng.integers(0, H - 60)); h = int(rng.integers(12, 70)); o = int(rng.integers(-180, 180))
        out[y:y + h] = np.roll(out[y:y + h], o, axis=1)
    return out
def streak(led, amt, seed):
    """exit: rows smear sideways (ref 176) + fade"""
    rng = np.random.default_rng(seed)
    out = whip(led, amt, (-1.0, 0.0), 18)
    rows = cv2.resize(rng.random((H // 6, 1)).astype(np.float32), (1, H), interpolation=cv2.INTER_NEAREST)
    sh = whip(led, amt * 2.2, (-1.0, 0.0), 18)
    m = (rows > 0.55).astype(np.float32)[:, :, None] * np.ones((1, W, 1), np.float32)
    return out * (1 - m) + sh * m
def led_tr3(cut, seed=0, pal="navy3", bolt=True):
    L = _L() if bolt else None
    for t in range(cut - 14, cut + 17):
        k = t - cut
        d = depth(t)
        if d is None: raise SystemExit("missing depth %d" % t)
        if k <= -13:                                          # whip build on clip A
            foot = dec(under(t)); lin = whip(foot, (90, 220)[k + 14], (1, 0)); yield t, enc(lin); continue
        if k == -12:
            lin = glitch3(dec(under(t)), led3(t, d, pal), seed); yield t, enc(lin); continue
        if k <= 11:                                           # depth hold A (hard), hard cut on the beat to depth B
            lin = led3(t, d, pal)
            if k <= -10: lin = lin * (1.0 + 0.6 * (-9 - k))          # 2f exposure kick on entry
        elif k <= 13:                                          # streak out
            lin = streak(led3(t, d, pal), (140, 420)[k - 12], seed + k) * (0.85, 0.5)[k - 12]
        else:                                                  # clean footage B, decelerating whip
            foot = dec(base(t)); lin = whip(foot, (160, 50, 0)[k - 14], (-1, 0)); yield t, enc(lin); continue
        if bolt and k >= -6: lin = strike_on(lin, d, t, cut, seed, L)
        yield t, enc(lin)


# ---------- v19: transitions use the exact Block-M ending LED field (led_img + navy_led) ----------
def ledM(t, d, seed=0):
    return led_img(t, ndepth(d) * 0.85, "navy_led", seed)
def smear_in(foot, led):
    return whip(foot, 300) * 0.45 + whip(led, 120) * 0.65
def led_tr4(cut, seed=0, bolt=True):
    L = _L() if bolt else None
    for t in range(cut - 14, cut + 17):
        k = t - cut
        d = depth(t)
        if d is None: raise SystemExit("missing depth %d" % t)
        if k <= -13:
            lin = whip(dec(under(t)), (90, 220)[k + 14], (1, 0)); yield t, enc(lin); continue
        if k == -12:
            lin = smear_in(dec(under(t)), ledM(t, d, seed))
        elif k <= 11:
            lin = ledM(t, d, seed)
        elif k <= 13:
            lin = streak(ledM(t, d, seed), (140, 420)[k - 12], seed + k) * (0.85, 0.5)[k - 12]
        else:
            lin = whip(dec(base(t)), (160, 50, 0)[k - 14], (-1, 0)); yield t, enc(lin); continue
        if bolt and k >= -6: lin = strike_on(lin, d, t, cut, seed, L)
        yield t, enc(lin)


# ---------- v20: LED covers ONE clip (the incoming one), people pop; dpush charge-up chain -> LED reveal ----------
def ledP(t, d, seed=0):
    """Block-M LED field, but people lifted: local depth contrast added before the LED quantise"""
    dn = ndepth(d)
    loc = dn - cv2.GaussianBlur(dn, (0, 0), 70); loc = np.clip(loc / (np.quantile(np.abs(loc), 0.995) + 1e-4), -1, 1)
    dp = np.clip(0.62 * dn + 0.42 * np.maximum(loc, 0) - 0.06 * np.maximum(-loc, 0) + 0.04, 0, 1)
    return led_img(t, dp, "navy_led", seed)
def led_tr5(cut, seed=0, hold=10, bolt=True):
    L = _L() if bolt else None
    for t in range(cut - 14, cut + 17):
        k = t - cut
        if k < 0:                                              # clip A plays clean; last 2f whip; lightning charges on A's subject
            foot = dec(base(t))
            lin = whip(foot, {-2: 70, -1: 200}.get(k, 0), (1, 0))
            if bolt and k >= -6: lin = strike_on(lin, depth(t), t, cut, seed, L)
            yield t, enc(lin); continue
        d = depth(t)
        if d is None: raise SystemExit("missing depth %d" % t)
        if k < hold:                                           # hard cut on the beat into clip B as LED depth, strike lands
            lin = ledP(t, d, seed) * (1.0 + 0.5 * max(0, 1 - k))
            if bolt: lin = strike_on(lin, d, t, cut, seed, L)
        elif k < hold + 2:                                     # streak out
            lin = streak(ledP(t, d, seed), (140, 420)[k - hold], seed + k) * (0.85, 0.5)[k - hold]
            if bolt: lin = strike_on(lin, d, t, cut, seed, L)
        else:                                                  # reveal clip B footage, decelerating whip
            lin = whip(dec(base(t)), {hold + 2: 160, hold + 3: 50}.get(k, 0), (-1, 0))
        yield t, enc(lin)
CHARGE = {341: 0.7, 365: 0.85, 384: 1.0, 408: 1.3}             # escalating pushes into the 431 LED reveal
def dpush_tr2(cut, seed=3, dirv=(1.0, 0.0)):
    g = CHARGE.get(cut, 1.0); stage = sorted(CHARGE).index(cut) if cut in CHARGE else -1
    L = _L(); dv = np.array(dirv, np.float32)
    seq = [(cut - 3, 0.025, False), (cut - 2, 0.08, False), (cut - 1, 0.2, False), (cut, -0.18, True), (cut + 1, -0.07, True), (cut + 2, -0.02, True)]
    for t, u, post in seq:
        d = depth(t); src = dec(base(t))
        lin = dpush(src, d, u * g, dv * 0.9, 0.45, 28)
        if stage >= 0:                                         # crackle grows each push: the edit is charging
            k = t - cut; e = (0.35, 0.55, 0.75, 1.0)[stage] * (1.0 if k in (-1, 0) else 0.5)
            nm = near_mask(d); rng = np.random.default_rng(seed * 11 + t); core = np.zeros((H, W), np.float32)
            edge_arcs(L, core, nm, rng, int(3 + 7 * e), 0.3 + 0.6 * e, 1.4 + 1.2 * e, d=d)
            if core.max() > 0:
                alb = L.lum((enc(lin) * 255).clip(0, 255).astype(np.uint8))
                lin = lin + L.finish(core, alb, None, 0.35 * e, 0.0, refl_gain=0.0, white_flash=0.12 * e if k == 0 else 0.0, bg_lin=lin)
        yield t, enc(lin)


# ---------- v21: reel-intro grammar (PJ ref "Instagram Reels Downloader.mp4"), Michigan colours ----------
MZ = np.array([0.0015, 0.47, 1.0], np.float32) * 1.7      # maize (linear BGR)
NV = np.array([0.072, 0.020, 0.0], np.float32) * 2.2       # navy
BLK = np.float32(0.0012)
def _shift(a, s, axis):
    out = np.empty_like(a)
    if axis == 0: out[s:] = a[:-s]; out[:s] = a[:1]
    else: out[:, s:] = a[:, :-s]; out[:, :s] = a[:, :1]
    return out
def sparkles(seed, t, n=70):
    rng = np.random.default_rng(seed); m = np.zeros((H, W), np.float32)
    xs = rng.integers(0, W, n); ys = rng.integers(0, H, n); ph = rng.uniform(0, 6.28, n)
    for x, y, p in zip(xs, ys, ph): m[y, x] = 0.5 + 0.5 * np.sin(p + t * 0.9)
    return cv2.GaussianBlur(m, (0, 0), 1.6) * 60 + cv2.GaussianBlur(m, (0, 0), 6) * 25
def shard_mask(seed, frac, t):
    """torn cut-out pieces of the next scene (upper/side areas), more as frac grows"""
    nf = noise_field(seed + 7, ((180, 1.0), (60, 0.5), (18, 0.25)))
    nf = (nf - nf.min()) / (np.ptp(nf) + 1e-6)
    yy = np.linspace(1, 0, H, dtype=np.float32)[:, None]
    key = nf * 0.75 + yy * 0.25
    th = np.quantile(key, 1 - 0.07 - 0.38 * frac)
    m = (key > th).astype(np.float32)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    return m
def subj(d, th=0.55):
    dn = ndepth(cv2.GaussianBlur(d.astype(np.float32), (0, 0), 2))
    m = (dn > th).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m); keep = np.zeros_like(m)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a > 6000 and w > 60 and h > 120 and w < W * 0.9: keep[lab == i] = 1
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.2)
def cutout_tr(cut, seed=0):
    """48: subject isolated on black + sparkles -> shards of clip B behind -> maize block glitch on the beat -> mosaic resolve -> strike"""
    L = _L()
    for t in range(cut - 14, cut + 17):
        k = t - cut
        if k < -7 or k > 4:
            lin = dec(base(t))
            if k > 4: lin = strike_on(lin, depth(t), t, cut + 5, seed, L)
            yield t, enc(lin); continue
        if k < 0:
            A = dec(base(t)); ma = subj(depth(t))
            for o in (1, 2, 3):                                    # subject mask must not shrink/flicker: take the fullest nearby
                if t + o < cut:
                    mm = subj(depth(t + o))
                    if mm.mean() > ma.mean() * 1.4: ma = mm
            if ma.mean() < 0.03:                                   # mask dropout -> reuse a neighbour's (no black flash frames)
                for o in (1, -1, 2, -2, 3):
                    mm = subj(depth(t + o))
                    if mm.mean() >= 0.03: ma = mm; break
            ma = ma[..., None]
            bg = np.full_like(A, BLK) + sparkles(seed, t)[..., None] * 0.09 * np.array([1.0, 0.9, 0.7], np.float32)
            if k >= -4:
                Bf = dec(base(cut + 1)); mb = cv2.GaussianBlur(cv2.dilate(near_mask(depth(cut + 1)).astype(np.float32), np.ones((15, 15), np.uint8)), (0, 0), 2)
                tear = shard_mask(seed, 0.25 + 0.75 * (k + 5) / 4.0, t)
                sm = (mb * cv2.dilate(tear, np.ones((25, 25), np.uint8)))[..., None] * (0.55 + 0.45 * (k + 5) / 4.0)
                bg = bg * (1 - sm) + Bf * sm
            yield t, enc(bg * (1 - ma) + A * ma); continue
        Bf = dec(base(t))
        if k == 0:                                                     # maize bar + block glitch
            A = dec(base(cut - 1)); ma = subj(depth(cut - 1))[..., None]; sm = cv2.dilate(near_mask(depth(cut + 1)).astype(np.float32), np.ones((15, 15), np.uint8))[..., None]
            img = (np.full_like(A, BLK) * (1 - sm) + Bf * sm) * (1 - ma) + A * ma
            rng = np.random.default_rng(seed + 3)
            img[:int(H * 0.17)] = MZ
            for _ in range(10):
                x = int(rng.integers(0, W - 200)); y = int(rng.integers(0, H - 120)); w = int(rng.integers(60, 260)); h = int(rng.integers(30, 120))
                img[y:y + h, x:x + w] = pix(Bf, 40)[y:y + h, x:x + w]
            yield t, enc(img); continue
        lin = pix(Bf, (48, 24, 10, 4)[k - 1])                         # mosaic resolve
        if k >= 3: lin = strike_on(lin, depth(t), t, cut + 5, seed, L)
        yield t, enc(lin)
def psort(img, amt, seed):
    """column-stretch drip (pixel-sort look): below a per-column row y0 the column repeats its y0 pixel -> streaks"""
    rng = np.random.default_rng(seed)
    nb = W // 12
    r = rng.random(nb).astype(np.float32); r = cv2.resize(r[None, :], (W, 1), interpolation=cv2.INTER_NEAREST)[0]
    r = r * 0.7 + 0.3 * cv2.resize(rng.random(W // 3).astype(np.float32)[None, :], (W, 1), interpolation=cv2.INTER_NEAREST)[0]
    y0 = (H - 1) * (1 - amt * (0.25 + 0.75 * r))
    rows = np.minimum(np.arange(H, dtype=np.float32)[:, None], y0[None, :])
    out = cv2.remap(img, np.broadcast_to(_xx[0][None, :], (H, W)).astype(np.float32), rows.astype(np.float32), cv2.INTER_NEAREST)
    return out
def tint(img, a):
    l = cv2.cvtColor(np.clip(enc(img), 0, 1), cv2.COLOR_BGR2GRAY)[..., None]
    t = NV * (0.5 + 1.2 * l) + MZ * np.clip((l - 0.62) * 3.0, 0, 1) ** 1.5 * 1.1
    return img * (1 - a) + t * a
def psort_tr(cut, seed=0):
    """239: footage drips into a navy/maize sorted frame, clip B bleeds out of it, strike lands"""
    L = _L()
    for t in range(cut - 14, cut + 17):
        k = t - cut
        if k < -6 or k > 5:
            lin = dec(base(t))
            if k > 5: lin = strike_on(lin, depth(t), t, cut + 4, seed, L)
            yield t, enc(lin); continue
        if k < 0:
            u = (k + 7) / 6.0
            lin = tint(psort(dec(base(t)), u ** 1.4, seed), 0.25 + 0.65 * u * u)
        elif k <= 1:
            lin = tint(psort(dec(base(cut - 1)), 1.0, seed + k), 1.0) * (1.25 if k == 0 else 0.8)
        else:
            u = (k - 1) / 4.0
            lin = tint(psort(dec(base(t)), 1 - u, seed + 9), 1 - u)
            lin = strike_on(lin, depth(t), t, cut + 4, seed, L)
        yield t, enc(lin)
def window_tr(cut, seed=0):
    """431: maize rectangle hit on the cut -> clip B inside a window on navy-black -> window opens to full -> strike"""
    L = _L()
    for t in range(cut - 14, cut + 17):
        k = t - cut
        if k < -2 or k > 9:
            lin = dec(base(t))
            if k > 9: lin = strike_on(lin, depth(t), t, cut + 8, seed, L)
            yield t, enc(lin); continue
        if k < 0:
            yield t, enc(whip(dec(base(t)), (80, 220)[k + 2], (1, 0))); continue
        if k == 0:
            img = dec(base(cut - 1)) * 0.35; img[int(H * 0.30):int(H * 0.72), int(W * 0.38):int(W * 0.62)] = MZ
            yield t, enc(img); continue
        Bf = dec(base(t))
        s = 0.44 + 0.02 * (k - 1) if k <= 5 else 0.52 + 0.48 * ss((k - 5) / 4.0)
        w, h = int(W * s), int(H * s); x0, y0 = (W - w) // 2, int((H - h) * 0.55)
        img = np.full_like(Bf, BLK) + NV * 0.08
        img[y0:y0 + h, x0:x0 + w] = cv2.resize(zoom(Bf, 1.0 + 0.04 * (1 - s)), (w, h), interpolation=cv2.INTER_AREA) if s < 0.999 else Bf
        if k >= 6: img = strike_on(img, depth(t), t, cut + 8, seed, L) if k >= 2 else img
        yield t, enc(img)

# ---------- plan (tl cut -> transition) ----------
def ink_tr(cut, n_out=4, n_in=4, seed=1):
    A = under(cut - 1)
    for i, t in enumerate(range(cut - n_out, cut + n_in)):
        u = (i + 0.5) / (n_out + n_in)
        a = under(t) if t < cut else zoom(A, 1.0 + 0.01 * (t - cut + 1))
        b = under(t) if t >= cut else under(cut)
        yield t, ink(a if u < 0.5 else a, b, u, seed)
def drip_tr(cut, n_out=3, n_in=4, seed=2):
    for i, t in enumerate(range(cut - n_out, cut + n_in)):
        u = (i + 0.5) / (n_out + n_in)
        a = under(min(t, cut - 1)); b = under(max(t, cut))
        yield t, drip(a, b, u, seed)
def smear_tr(cut, seed=3, vertical=True):
    a1, a2 = under(cut - 2), under(cut - 1); b1, b2, b3 = under(cut), under(cut + 1), under(cut + 2)
    yield cut - 2, smear(a1, seed, 0.45, vertical)
    yield cut - 1, glitch(smear(a2, seed + 1, 0.85, vertical), seed + 2, 6, 0.1)
    yield cut, smear(b1, seed + 3, 0.55, vertical, up=True)
    yield cut + 1, glitch(b2, seed + 5, 4, 0.0)
    yield cut + 2, smear(b3, seed + 6, 0.2, vertical, up=True)
def glitch_cut(cut, seed=5):
    yield cut, glitch(under(cut), seed, 7, 0.15)
PLAN = [(cutout_tr, 48, dict(seed=11)), (psort_tr, 239, dict(seed=21)), (dpush_tr, 287, dict(seed=31, dirv=(1, 0))),
        (dpush_tr2, 341, dict(seed=41, dirv=(-1, 0.15))), (dpush_tr2, 365, dict(seed=61, dirv=(1, -0.1))), (dpush_tr2, 384, dict(seed=71, dirv=(0.0, -1.0))),
        (dpush_tr2, 408, dict(seed=81, dirv=(-1, 0))), (window_tr, 431, dict(seed=91)), (dpush_tr, 455, dict(seed=101, dirv=(0.6, 0.4))), (lambda c, **k: end_tr(), 467, {})]
if __name__ == "__main__":
    want = set(int(x) for x in sys.argv[1:])
    done = []
    for fn, cut, kw in PLAN:
        if want and cut not in want: continue
        for t, im in fn(cut, **kw):
            cv2.imwrite(OUT % t, (np.clip(im, 0, 1) * 65535 + 0.5).astype(np.uint16)); done.append(t)
    print("baked", len(done), sorted(done)[:4], sorted(done)[-4:])
