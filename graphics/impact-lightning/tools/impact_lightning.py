"""Impact lightning for the hockey edit, built on lightning_v5's light model (additive scene-linear light on the
decoded S-Log3 plate, re-encoded to S-Log3 16-bit PNG).
usage: python3 impact_lightning.py SPOT OUTDIR      SPOT in {hit, phy, cele, lens}
Base frames: impact-lightning/base_log/b_%04d.png (ungraded log master); masks: seg_hit/f_%04d.png (rembg u2net_human_seg)."""
import os, sys, json, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(G, "puck-lightning", "tools"))
cwd = os.getcwd()
import lightning_v5 as L          # chdirs into puck-lightning
os.chdir(cwd)
IL = os.path.join(G, "impact-lightning")
W, H = 1920, 1080

def interp(d, f): return L.interp(d, f)
BAKE = os.path.join(G, "inspo-transitions", "bake_v4_log16", "fx_tl_%04d.png")
BASE = os.path.join(G, "master_v4", "base16", "b_%04d.png")
def base(t):
    """what the viewer sees under the lightning: V3 transition bake if there is one, else the v4 log base"""
    for p in (BAKE % t, BASE % t, os.path.join(IL, "base_log", "b_%04d.png" % t)):
        if os.path.exists(p): return cv2.imread(p, -1).astype(np.float32) / 65535
    raise FileNotFoundError(t)
def mask(t):
    p = os.path.join(IL, "seg_hit", "f_%04d.png" % t)
    if not os.path.exists(p): return None
    m = cv2.imread(p, -1)
    return (m[..., 3] > 110).astype(np.uint8) if m.ndim == 3 and m.shape[2] == 4 else None
def yellow(bg):
    v = (L.view(bg) * 255).clip(0, 255).astype(np.uint8) if hasattr(L, "view") else None
    return v
def comp_yellow(m, bg, pt, r=260):
    """component of the person mask with the most yellow-jersey pixels near pt (#17 = maize jersey)"""
    if m is None: return None
    import view709
    v = (view709.view(bg) * 255).clip(0, 255).astype(np.uint8); hsv = cv2.cvtColor(v, cv2.COLOR_BGR2HSV)
    yl = ((hsv[..., 0] > 18) & (hsv[..., 0] < 38) & (hsv[..., 1] > 90) & (hsv[..., 2] > 110)).astype(np.uint8)
    m2 = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, lab = cv2.connectedComponents(m2); yy, xx = np.ogrid[:H, :W]
    near = ((xx - pt[0]) ** 2 + (yy - pt[1]) ** 2) < r * r
    best, bs = None, 0
    for i in range(1, n):
        c = lab == i; sc = (c & near & (yl > 0)).sum()
        if sc > bs: best, bs = i, sc
    if best is None or bs < 150: return None
    body = (lab == best).astype(np.uint8)
    # keep only the yellow player's part if two players merged: restrict to yellow-dense region
    yd = cv2.dilate(yl & body, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45)))
    return (body & yd).astype(np.uint8)
def _hsv(bg):
    import view709
    v = (view709.view(bg) * 255).clip(0, 255).astype(np.uint8); return cv2.cvtColor(v, cv2.COLOR_BGR2HSV)
def _disc(c, r):
    yy, xx = np.ogrid[:H, :W]; return (((xx - c[0]) ** 2 + (yy - c[1]) ** 2) < r * r)
def keep_near(m, c, r=90):
    n, lab = cv2.connectedComponents(m); ids = [i for i in np.unique(lab[_disc(c, r) & (m > 0)]) if i > 0]
    return np.isin(lab, ids).astype(np.uint8) if ids else None
def jersey17(bg, p, r=250):
    """maize jersey + navy pants/helmet key around #17's track -> silhouette blob for the charge to crawl on"""
    h = _hsv(bg)
    yl = (h[..., 0] > 16) & (h[..., 0] < 40) & (h[..., 1] > 80) & (h[..., 2] > 100)
    nv = (h[..., 0] > 95) & (h[..., 0] < 135) & (h[..., 1] > 60) & (h[..., 2] < 140)
    core = cv2.dilate((yl & _disc(p, r)).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
    m = ((yl | (nv & (core > 0))) & _disc(p, r)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19)))
    k = keep_near(m, p, 200)
    if k is None or k.sum() < 600: return None
    n, lab = cv2.connectedComponents(k); sizes = [(lab == i).sum() for i in range(1, n)]
    return (lab == 1 + int(np.argmax(sizes))).astype(np.uint8)
def bodies(bg, c, r=210):
    """both players at the contact (maize + dark jerseys) for occlusion"""
    h = _hsv(bg)
    yl = (h[..., 0] > 16) & (h[..., 0] < 40) & (h[..., 1] > 80) & (h[..., 2] > 100)
    dk = (h[..., 2] < 70)
    m = ((yl | dk) & _disc(c, r)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    return keep_near(m, c, 120)
_BX = {}
def crop_mask(name, t):
    """full-frame mask from a rembg run on a crop (seg_<name>/f_%04d.png + boxes.json)"""
    d = os.path.join(IL, "seg_" + name)
    if name not in _BX:
        p = os.path.join(d, "boxes.json"); _BX[name] = json.load(open(p)) if os.path.exists(p) else {}
    b = _BX[name].get(str(t)); p = os.path.join(d, "f_%04d.png" % t)
    if b is None or not os.path.exists(p): return None
    x0, y0, cw, ch = b; f = cv2.imread(p, -1)
    if f is None or f.ndim < 3 or f.shape[2] < 4: return None
    m = np.zeros((H, W), np.uint8); m[y0:y0 + ch, x0:x0 + cw] = (f[..., 3] > 110).astype(np.uint8)
    return m
def comp_near(m, pt, rmax=140):
    if m is None: return None
    m2 = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    n, lab = cv2.connectedComponents(m2); x, y = int(pt[0]), int(pt[1])
    for r in (0, 25, 60, rmax):
        win = lab[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1]; ids = [i for i in np.unique(win) if i > 0]
        if ids: return (lab == max(ids, key=lambda i: (lab == i).sum())).astype(np.uint8)
    return None
def write(out, t, bg, Lin):
    o = L.enc(np.maximum(L.dec(bg), -0.01) + Lin)
    cv2.imwrite(os.path.join(out, "il_%04d.png" % t), (o * 65535 + 0.5).astype(np.uint16))
def net_mask(bg):
    """thin dark netting/stanchions in FRONT of the glass (black-hat on luma) -> occluder for bolts behind them"""
    import view709
    g = cv2.cvtColor((view709.view(bg) * 255).clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(np.float32)
    return np.clip((bh - 12) / 30, 0, 1)
def glass_burst(core, c, rng, n, rmin, rmax, inten, w, slope=-0.16):
    """real strike on glass: a few heavy channels fanning UP/ACROSS the glass + 2 crawling along the boards' top"""
    for k in range(n):
        ang = rng.uniform(-np.pi * 0.95, -np.pi * 0.05)
        l = rng.uniform(rmin, rmax); p1 = c + l * np.array([np.cos(ang), np.sin(ang)])
        L.draw(core, L.channel(c, p1, rng, rough=0.17, branch=1.5, w0=w * rng.uniform(0.8, 1.25), i0=inten * rng.uniform(0.75, 1.0)))
    d = np.array([1.0, slope]); d /= np.linalg.norm(d)
    for sgn in (-1, 1):
        p0 = c + np.array([0, 55.0]); p1 = p0 + sgn * d * rng.uniform(rmin * 1.3, rmax * 1.2)
        L.draw(core, L.channel(p0, p1, rng, rough=0.12, branch=0.8, w0=w * 0.7, i0=inten * 0.8))
def below_boards(c, slope=-0.16, off=95):
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    top = c[1] + off + slope * (xx - c[0])
    keep = 1.0 - np.clip((yy - top) / 25.0, 0, 1)
    near = np.clip(1 - np.hypot(xx - c[0], yy - c[1]) / 70.0, 0, 1)
    return np.maximum(keep, near)
def burst(core, c, rng, n, rmin, rmax, up=True, inten=1.0, w=3.0):
    for k in range(n):
        if up: ang = rng.uniform(-np.pi * 0.98, -np.pi * 0.02) if rng.random() < 0.75 else rng.choice([0.0, np.pi]) + rng.normal(0, 0.25)
        else: ang = rng.uniform(-np.pi, np.pi)
        l = rng.uniform(rmin, rmax); p1 = c + l * np.array([np.cos(ang), np.sin(ang)])
        L.draw(core, L.channel(c, p1, rng, rough=0.2, branch=0.9, w0=w, i0=inten * rng.uniform(0.6, 1.0)))
def _contour(m):
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(cs, key=len)[:, 0, :].astype(float) if cs else None
def arcs_out(core, m, rng, n, inten, width, reach=(16, 75), valid=None, leap_only=False):
    """real discharge: short jagged arcs LEAPING off the body (outward normal), plus bridges between nearby edge
    points; a faint crawl only where it hugs the surface. valid(pts)->bool mask restricts usable edge points."""
    if m is None or m.sum() < 400: return
    c = _contour(m)
    if c is None or len(c) < 60: return
    N = len(c); ok = np.ones(N, bool) if valid is None else valid(c)
    idx = np.where(ok)[0]
    if len(idx) < 20: return
    M = cv2.moments(m.astype(np.uint8)); cen = np.array([M["m10"] / (M["m00"] + 1e-6), M["m01"] / (M["m00"] + 1e-6)])
    d = np.gradient(c, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6
    flip = np.sum(nrm * (c - cen), 1) < 0; nrm[flip] *= -1          # point outward
    for _ in range(n):
        i = rng.choice(idx); s0 = c[i]; r = 0.0 if leap_only else rng.random()
        if r < 0.55:                                                   # leap outward
            ang = np.arctan2(nrm[i, 1], nrm[i, 0]) + rng.normal(0, 0.55); l = rng.uniform(*reach)
            L.draw(core, L.channel(s0, s0 + l * np.array([np.cos(ang), np.sin(ang)]), rng, rough=0.3, branch=0.7, w0=width, i0=inten * rng.uniform(0.6, 1.0)))
        elif r < 0.85:                                                 # bridge to another edge point a little away
            j = idx[np.argmin(np.abs(np.hypot(*(c[idx] - s0).T) - rng.uniform(50, 140)))]
            mid = (s0 + c[j]) / 2 + nrm[i] * rng.uniform(8, 30)
            pts = L.jag(s0, mid, rng, 0.3); pts2 = L.jag(mid, c[j], rng, 0.3)
            L.draw(core, [(np.vstack([pts, pts2[1:]]), width * 0.9, width * 0.5, inten * rng.uniform(0.5, 0.9))])
        else:                                                          # short crawl hugging the surface
            ids = (i + np.arange(0, int(rng.uniform(25, 70)), 4)) % N
            pts = c[ids] + nrm[ids] * rng.uniform(1, 4) + rng.normal(0, 1.8, (len(ids), 2))
            L.draw(core, [(pts, width * 0.7, width * 0.3, inten * 0.45)])
def aura(core, sm, rng, n, inten, width):
    arcs_out(core, sm, rng, n, inten, width)
PREV = {}
REDW = np.array([0.55, 0.6, 1.0], np.float32)   # BGR warm-red ambient bounce
def final(out, t, bg, bg_lin, core, occ, spill, wflash=0.0, fx=None):
    """afterglow + bolt-lit ambient + lens FX, all in scene-linear, then encode S-Log3"""
    fx = fx or {}
    raw = core.copy(); pg = PREV.get(t - 1)
    if pg is not None: core = core + 0.32 * cv2.GaussianBlur(pg, (0, 0), 1.2)       # channel afterglow (persistence)
    PREV.clear(); PREV[t] = raw
    alb = L.lum((L.enc(bg_lin) * 255).astype(np.uint8))
    Lin = L.finish(core, alb, occ, spill, 0.0, refl_gain=0.0, white_flash=wflash, bg_lin=bg_lin)
    E = float(cv2.GaussianBlur(raw, (0, 0), 4).sum()) / (W * H)                   # how much bolt is on screen
    Lin += min(0.9, 9.0 * E) * np.clip(bg_lin, 0, 2) * REDW * 0.35               # scene lit by the bolt
    o = np.maximum(L.dec(bg), -0.01) + Lin
    if "streak" in fx:                                                          # anamorphic lens streak
        x, y = fx["streak"]; hot = np.zeros((H, W), np.float32); cv2.circle(hot, (int(x), int(y)), 18, 1.0, -1)
        st = cv2.GaussianBlur(hot, (0, 0), sigmaX=260, sigmaY=2.2) * fx.get("streak_gain", 6.0)
        o += st[..., None] * np.array([0.7, 0.55, 1.0], np.float32)
    if fx.get("ca", 0) > 0:                                                     # chromatic fringe on impact
        k = fx["ca"]; o[..., 0] = np.roll(o[..., 0], -k, axis=1); o[..., 2] = np.roll(o[..., 2], k, axis=1)
    if "shake" in fx:
        dx, dy = fx["shake"]; Mt = np.float32([[1, 0, dx], [0, 1, dy]])
        o = cv2.warpAffine(o, Mt, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    enc = L.enc(o)
    cv2.imwrite(os.path.join(out, "il_%04d.png" % t), (enc * 65535 + 0.5).astype(np.uint16))

# ---------------- BIG HIT (#17 pins WMU on the glass) ----------------
P17 = {257: (1880, 440), 259: (1705, 432), 261: (1590, 470), 263: (1365, 430), 265: (1267, 330), 266: (1264, 320),
       268: (1143, 346), 271: (965, 260), 275: (960, 400), 280: (1057, 446), 286: (1080, 450)}
CON = {263: (1290, 420), 264: (1230, 370), 265: (1190, 330), 266: (1180, 330), 268: (1050, 330), 271: (915, 290),
       275: (930, 390), 280: (960, 450), 286: (980, 460)}
def strike_geom(c, seed, top=None):
    """one strike, goal-style: stepped leader from above the frame down to c, few branches. Held geometry (seeded)."""
    rng = np.random.default_rng(seed)
    top = np.array(top if top is not None else (c[0] + rng.uniform(-260, 260), -40.0))
    return L.channel(top, c, rng, rough=0.17, branch=0.9, w0=5.5, i0=1.0)
def ground_runs(c, seed, slope=-0.16):
    rng = np.random.default_rng(seed); d = np.array([1.0, slope]); d /= np.linalg.norm(d); segs = []
    for sgn in (-1, 1):
        p0 = c + np.array([0, 40.0]); segs += L.channel(p0, p0 + sgn * d * rng.uniform(220, 420), rng, rough=0.12, branch=0.5, w0=2.4, i0=0.7)
    return segs
def scale_segs(segs, k): return [(p, wa, wb, i * k) for p, wa, wb, i in segs]
def hit(t, out):
    rng = np.random.default_rng(4100 + t // 2); rf = np.random.default_rng(9100 + t)
    flick = float(np.clip(rf.normal(1.0, 0.18), 0.65, 1.3))
    bg = base(t); bg_lin = L.dec(bg); core = np.zeros((H, W), np.float32)
    c = interp(CON, t); p17 = interp(P17, t)
    me = jersey17(bg, p17) if t != 264 else None
    m = bodies(bg, c) if t != 264 else None
    occ = None; spill = 0.2; wflash = 0.0
    if 257 <= t <= 263:                                      # charge builds on #17 (same look as the goal charge-up)
        u = (t - 257) / 6.0
        if me is not None: L.contour_arcs(core, me, rng, int(3 + 9 * u), 0.35 + 0.55 * u, 1.4 + 0.8 * u)
        spill = 0.08 + 0.3 * u
    elif t == 264:                                           # THE strike: one bolt drops onto the contact point
        L.draw(core, strike_geom(c, 777)); L.draw(core, ground_runs(c, 778)); spill = 1.1; wflash = 0.3
    elif 265 <= t <= 270:                                    # same channel holds and decays, restrikes on 266/268
        k = t - 265; e = (1.0, 0.55, 0.85, 0.35, 0.6, 0.2)[k]
        L.draw(core, scale_segs(strike_geom(c, 777), e)); L.draw(core, scale_segs(ground_runs(c, 778), e * 0.8))
        if me is not None: L.contour_arcs(core, me, rng, 5, 0.55 * e + 0.15, 1.6)
        occ = 0.7 * net_mask(bg)
        if m is not None:
            o2 = cv2.GaussianBlur(cv2.dilate(m, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.5)
            yy, xx = np.ogrid[:H, :W]; o2 *= np.clip((np.hypot(xx - c[0], yy - c[1]) - 40) / 50, 0, 1)
            occ = np.maximum(occ, o2)
        spill = 0.6 * e + 0.08
    elif 271 <= t <= 280:                                    # residual charge crawling off #17
        k = t - 271; e = 0.78 ** k
        if me is not None: L.contour_arcs(core, me, rng, int(4 * e) + 1, 0.4 * e + 0.08, 1.3)
        spill = 0.15 * e
    else:
        write(out, t, bg, np.zeros((H, W, 3), np.float32)); return
    core *= flick
    fx = {}
    if t in (264, 265): fx = {"shake": (6, -4) if t == 264 else (-4, 3), "ca": 3 if t == 264 else 1, "streak": c, "streak_gain": 5.0 if t == 264 else 2.0}
    final(out, t, bg, bg_lin, core, occ, spill * flick, wflash, fx)


# ---------------- #44 faceoff scrum (341-346): crackle in the scrum -> jumps to Horcoff ----------------
SCRUM = np.array([1250.0, 330.0]); H44 = np.array([920.0, 700.0])
def maize_near(bg, p, r, keep_r=160, open_k=15):
    h = _hsv(bg)
    yl = ((h[..., 0] > 16) & (h[..., 0] < 40) & (h[..., 1] > 80) & (h[..., 2] > 100) & _disc(p, r)).astype(np.uint8)
    yl = cv2.morphologyEx(yl, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    yl = cv2.morphologyEx(yl, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k)))
    k = keep_near(yl, p, keep_r)
    if k is None: return None
    n, lab = cv2.connectedComponents(k); sizes = [(lab == i).sum() for i in range(1, n)]
    return (lab == 1 + int(np.argmax(sizes))).astype(np.uint8)
def phy(t, out):
    rng = np.random.default_rng(5100 + t // 2); rf = np.random.default_rng(9500 + t)
    flick = float(np.clip(rf.normal(1.0, 0.2), 0.6, 1.35))
    bg = base(t); bg_lin = L.dec(bg); core = np.zeros((H, W), np.float32); spill = 0.3
    if t < 341: write(out, t, bg, np.zeros((H, W, 3), np.float32)); return
    k = t - 341
    nsc = 4 if k <= 2 else 2
    for _ in range(nsc):
        a = SCRUM + rng.normal(0, [150, 95]); b = SCRUM + rng.normal(0, [150, 95])
        L.draw(core, L.channel(a, b, rng, rough=0.24, branch=0.6, w0=2.2, i0=(0.55 + 0.2 * k if k <= 2 else 0.45)))
    if k == 2:                                                 # arc leaps to Horcoff
        L.draw(core, L.channel(SCRUM + (-120, 120), H44 + (20, -60), rng, rough=0.2, branch=0.8, w0=3.2, i0=1.0)); spill = 0.9
    if k >= 2:
        m44 = maize_near(bg, H44, 260)
        aura(core, m44, rng, 10 if k <= 3 else 7, 0.85 if k <= 3 else 0.6, 2.0)
    core *= flick
    fx = {"shake": (5, -3), "streak": SCRUM + (-120, 120), "streak_gain": 3.0} if k == 2 else ({"shake": (-2, 1)} if k == 3 else {})
    final(out, t, bg, bg_lin, core, None, spill * flick, 0.0, fx)

def silhouette(bg, p, r):
    """maize jersey + navy numbers/trim near p, holes filled -> one body blob"""
    h = _hsv(bg)
    yl = (h[..., 0] > 16) & (h[..., 0] < 40) & (h[..., 1] > 80) & (h[..., 2] > 100)
    nv = (h[..., 0] > 95) & (h[..., 0] < 135) & (h[..., 1] > 50) & (h[..., 2] < 150)
    d = _disc(p, r)
    m = ((yl | nv) & d).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
    k = keep_near(m, p, 120)
    if k is None: return None
    cs, _ = cv2.findContours(k, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    f = np.zeros_like(k); cv2.drawContours(f, [max(cs, key=cv2.contourArea)], -1, 1, -1)
    return f
def aura_edge(core, m, p, r, rng, n, inten, width):
    """contour arcs only on real outline (not on the search-circle cut)"""
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs: return
    c = max(cs, key=len)[:, 0, :].astype(float); N = len(c)
    ok = np.hypot(c[:, 0] - p[0], c[:, 1] - p[1]) < r - 12
    ok &= c[:, 1] < H - 6
    ok &= np.abs(c[:, 0] - p[0]) < 300
    if ok.sum() < 60: return
    idx_ok = np.where(ok)[0]
    for _ in range(n):
        i = rng.choice(idx_ok); Ln = int(rng.uniform(40, 150)); ids = (i + np.arange(0, Ln, 5)) % N
        ids = ids[: np.argmin(ok[ids]) if not ok[ids].all() else len(ids)]
        if len(ids) < 4: continue
        pts = c[ids]; d = np.gradient(pts, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6
        pts = pts + nrm * rng.uniform(1, 5) + rng.normal(0, 2.2, pts.shape)
        L.draw(core, [(pts, width, width * 0.4, inten)])

# ---------------- Horcoff celebration (388-402): the charge is still on him ----------------
C44 = np.array([950.0, 480.0])
def cele(t, out):
    rng = np.random.default_rng(6100 + t // 2); rf = np.random.default_rng(9700 + t)
    bg = base(t); bg_lin = L.dec(bg)
    if not (388 <= t <= 402): write(out, t, bg, np.zeros((H, W, 3), np.float32)); return
    u = (t - 388) / 14.0; env = np.sin(np.pi * min(1.0, u * 1.15)) ** 0.7       # swell then fade
    flick = float(np.clip(rf.normal(1.0, 0.25), 0.5, 1.4))
    core = np.zeros((H, W), np.float32)
    m = silhouette(bg, C44, 480)
    if m is not None:
        val = lambda c: (np.hypot(c[:, 0] - C44[0], c[:, 1] - C44[1]) < 468) & (c[:, 1] < H - 6) & (np.abs(c[:, 0] - C44[0]) < 300)
        arcs_out(core, m, rng, int(7 + 12 * env), 0.45 + 0.6 * env, 1.8 + 0.9 * env, reach=(14, 60), valid=val)
    if rf.random() < 0.2 * env:                          # occasional arc off his shoulders into the air
        p0 = C44 + rng.normal(0, [140, 60]) + (0, -120); ang = rng.uniform(-2.6, -0.5); l = rng.uniform(120, 260)
        L.draw(core, L.channel(p0, p0 + l * np.array([np.cos(ang), np.sin(ang)]), rng, rough=0.22, branch=0.7, w0=2.0, i0=0.7 * env))
    core *= flick
    final(out, t, bg, bg_lin, core, None, 0.35 * env * flick, 0.0, {})


# ---------------- puck -> lens ending (467-477): puck carries the bolt into the lens ----------------
PK = {467: (1044, 592, 4), 468: (1065, 615, 8), 469: (1116, 651, 12), 470: (1155, 684, 18), 471: (1230, 729, 28),
      472: (1305, 750, 45), 473: (1365, 810, 65), 474: (1395, 840, 110), 475: (1500, 700, 200), 476: (1380, 690, 330), 477: (1000, 560, 650)}
ORIGIN = np.array([1000.0, 560.0])
def rim(core, c, r, rng, n, inten, w):
    m = np.zeros((H, W), np.uint8); cv2.ellipse(m, (int(c[0]), int(c[1])), (max(3, int(r)), max(2, int(r * 0.55))), 0, 0, 360, 1, -1)
    arcs_out(core, m, rng, n + 2, inten, w, reach=(max(10, r * 0.25), max(30, r * 0.9)), leap_only=True)
def _rim_old(core, c, r, rng, n, inten, w):
    for _ in range(n):
        a0 = rng.uniform(0, 2 * np.pi); da = rng.uniform(0.5, 1.6); a = np.linspace(a0, a0 + da, max(6, int(r * da / 6)))
        rr = r * (1.05 + 0.08 * rng.random()) + rng.normal(0, max(1.0, r * 0.02), len(a))
        pts = np.stack([c[0] + rr * np.cos(a), c[1] + rr * 0.55 * np.sin(a)], 1)
        L.draw(core, [(pts, w, w * 0.4, inten)])
def lens(t, out):
    rng = np.random.default_rng(7100 + t // 2); rf = np.random.default_rng(9900 + t)
    bg = base(t); bg_lin = L.dec(bg); core = np.zeros((H, W), np.float32)
    if t not in PK: write(out, t, bg, np.zeros((H, W, 3), np.float32)); return
    x, y, r = PK[t]; c = np.array([x, y], float); flick = float(np.clip(rf.normal(1.0, 0.18), 0.65, 1.3))
    spill = 0.15 + 0.35 * min(1, r / 200); wflash = 0.0
    if t <= 475:                                             # comet: the bolt rides with the puck (goal grammar)
        prev = [np.array(PK[k][:2], float) for k in range(max(467, t - 3), t)] or [c + (-30, -18)]
        tail = prev[0]
        L.draw(core, L.channel(tail, c, rng, rough=0.2, branch=0.4, w0=1.4 + r / 70, i0=0.85))
        if r > 20: L.contour_arcs(core, cv2.ellipse(np.zeros((H, W), np.uint8), (int(x), int(y)), (int(r), int(r * 0.55)), 0, 0, 360, 1, -1), rng, 2 + int(r / 60), 0.6, 1.2 + r / 120)
    else:                                                    # impact on the lens: one strike into the puck, then white-out
        L.draw(core, strike_geom(c, 999, top=(c[0] - 500, -60))); L.draw(core, strike_geom(c, 1001, top=(c[0] + 620, -60)))
        spill = 1.2; wflash = 0.25 if t == 476 else 0.7
    core *= flick
    fx = {}
    if t >= 476: fx = {"shake": ((10, -6) if t == 476 else (-6, 4)), "ca": 3, "streak": c, "streak_gain": 5.0}
    final(out, t, bg, bg_lin, core, None, spill * flick, wflash, fx)

SPOTS = {"hit": (hit, range(256, 281)), "phy": (phy, range(341, 347)), "cele": (cele, range(388, 403)), "lens": (lens, range(467, 478))}
if __name__ == "__main__":
    spot, out = sys.argv[1], os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
    fn, rr = SPOTS[spot]
    frames = [int(x) for x in sys.argv[3:]] or list(rr)
    for t in frames: fn(t, out)
    print("ok", spot, len(frames))
