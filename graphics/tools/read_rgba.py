import OpenEXR, numpy as np
def read_rgba(p):
    f=OpenEXR.File(p); ch=f.channels()
    if "RGBA" in ch: a=np.asarray(ch["RGBA"].pixels,np.float32); return a[...,:3],a[...,3]
    if "RGB" in ch: return np.asarray(ch["RGB"].pixels,np.float32),np.ones(np.asarray(ch["RGB"].pixels).shape[:2],np.float32)
    k=lambda c:[x for x in ch if x.endswith(c)][0]
    rgb=np.dstack([np.asarray(ch[k(c)].pixels,np.float32) for c in ("R","G","B")]); A=np.asarray(ch[k("A")].pixels,np.float32) if any(x.endswith("A") for x in ch) else np.ones(rgb.shape[:2],np.float32)
    return rgb,A
