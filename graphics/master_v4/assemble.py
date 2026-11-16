"""v4 LOG master frame resolver: for each tl frame pick the top-most layer (V4 lightning > V1 goal fx > V3 bake > v4 base).
usage: python3 assemble.py LINKDIR [v4 lightning version suffix]"""
import os, sys
G = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
link = os.path.expanduser(sys.argv[1]); os.makedirs(link, exist_ok=True)
LV = sys.argv[2] if len(sys.argv) > 2 else "v9"
GOAL = sys.argv[3] if len(sys.argv) > 3 else "goal_fx_log_v5"
L4 = [(256, 280, "hit")]   # v11: scrum + cele lightning cut (PJ)
src = {}
for t in range(0, 527):
    p = None
    for a, b, n in L4:
        if a <= t <= b: p = f"{G}/impact-lightning/out_{n}_{LV}/il_{t:04d}.png"
    if p is None and 96 <= t <= 203: p = f"{G}/puck-lightning/{GOAL}/fx_{t:04d}.png"
    if p is None and os.path.exists(f"{G}/inspo-transitions/bake_v5_log16/fx_tl_{t:04d}.png"): p = f"{G}/inspo-transitions/bake_v5_log16/fx_tl_{t:04d}.png"
    if p is None and os.path.exists(f"{G}/inspo-transitions/bake_v4_log16/fx_tl_{t:04d}.png"): p = f"{G}/inspo-transitions/bake_v4_log16/fx_tl_{t:04d}.png"
    if p is None: p = f"{G}/master_v4/base16/b_{t:04d}.png"
    assert os.path.exists(p), p
    d = os.path.join(link, f"m_{t:04d}.png")
    if os.path.lexists(d): os.remove(d)
    os.symlink(p, d); src[t] = p.replace(G + "/", "")
import json; json.dump(src, open(os.path.join(G, "master_v4", f"sources_{LV}.json"), "w"), indent=0)
print("linked", len(src))
