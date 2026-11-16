"""Encode scene-linear (S-Gamut3.Cine) EXR renders to S-Log3 16-bit PNG, matching Sony FX3/FX6 footage.
usage: python3 exr_to_slog3.py in.exr out.png   |   python3 exr_to_slog3.py in_dir out_dir"""
import sys, os, numpy as np, OpenEXR, cv2
def read_exr(p):
    f=OpenEXR.File(p); ch=f.channels()
    if "RGB" in ch: a=np.asarray(ch["RGB"].pixels,np.float32)
    else: a=np.dstack([np.asarray(ch[c].pixels,np.float32) for c in ("R","G","B")])
    return a
def slog3(lin):
    lin=lin.astype(np.float64)
    hi=(420+np.log10(np.maximum(lin+0.01,1e-6)/0.19)*261.5)/1023; lo=(lin*(171.2102946929-95)/0.01125+95)/1023
    return np.clip(np.where(lin>=0.01125,hi,lo),0,1)
def conv(a,b):
    code=slog3(read_exr(a)); cv2.imwrite(b,(code[...,::-1]*65535+0.5).astype(np.uint16))
if __name__=="__main__":
    a,b=sys.argv[1],sys.argv[2]
    if os.path.isdir(a):
        os.makedirs(b,exist_ok=True)
        for n in sorted(os.listdir(a)):
            if n.endswith(".exr"):
                o=os.path.join(b,n[:-4]+".png")
                if not os.path.exists(o): conv(os.path.join(a,n),o)
    else: conv(a,b)
