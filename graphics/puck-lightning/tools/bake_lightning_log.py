"""Bake v5 lightning (additive light layers) into the S-Log3 frames: decode -> + light (scene-linear) -> encode.
usage: python3 bake_lightning_log.py OVERLAY_DIR OUT_DIR [K] [tl...]"""
import numpy as np, cv2, os, sys
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(B)
def dec(c):
    c=np.asarray(c,np.float64); cc=c*1023
    return np.where(cc>=171.2102946929,(10**((cc-420)/261.5))*0.19-0.01,(cc-95)*0.01125/(171.2102946929-95))
def enc(l):
    l=np.asarray(l,np.float64)
    return np.clip(np.where(l>=0.01125,(420+np.log10(np.maximum(l+0.01,1e-6)/0.19)*261.5)/1023,(l*(171.2102946929-95)/0.01125+95)/1023),0,1)
def bg_code(tl):
    if 142<=tl<=185: return cv2.imread("../hockey-puck-goal/render_bullettime_v10_slog3/bt_%04d.png"%(tl-141),-1).astype(np.float64)/65535
    src=tl+591 if tl<=141 else tl+548
    return cv2.imread("src_frames/src_%04d.png"%src).astype(np.float64)/255
def bake(tl,ovd,outd,K):
    bg=bg_code(tl); ovp=os.path.join(ovd,"lt_%04d.png"%tl)
    ov=cv2.imread(ovp,-1).astype(np.float64)/65535 if os.path.exists(ovp) else np.zeros_like(bg)
    out=enc(dec(bg)+K*ov**2.2)
    cv2.imwrite(os.path.join(outd,"gl_%04d.png"%tl),(out*65535+0.5).astype(np.uint16))
if __name__=="__main__":
    ovd,outd=sys.argv[1],sys.argv[2]; K=float(sys.argv[3]) if len(sys.argv)>3 else 8.0
    os.makedirs(outd,exist_ok=True); tls=[int(x) for x in sys.argv[4:]] or list(range(96,204))
    for t in tls: bake(t,ovd,outd,K)
    print("baked",len(tls))
