"""Drama pass v2 over baked log lightning (gl_*.png -> fx_*.png, S-Log3 16-bit). No sparks.
charge: slow push-in on Horcoff + frost spreading over the ice from the blade path (world-anchored, melts after release)
release: zoom snap-back + shake + flash + colour fringe + wide anamorphic streak | flight: anamorphic streak at the puck (incl. frozen CG)
score: flash + shockwave ripple + heavy shake + wide streak."""
import numpy as np, cv2, os, sys, json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import lightning_v5 as LV
from lightning_v5 import dec, enc, T, cum, interp, blade, hands, impact, blob_occ
W,H=1920,1080; IN,OUT=sys.argv[1],sys.argv[2]; os.makedirs(OUT,exist_ok=True)
CGP={int(k):v for k,v in json.load(open("cg_puck_px.json")).items()}
def src_of(tl): return tl+591 if tl<=141 else (tl+548 if tl>=186 else None)
rng=np.random.default_rng(11)
# ---- frost texture: branching crystals ----
def frost_tex(S=520):
    t=np.zeros((S*4,S*4),np.float32); c=S/2
    def br(p,a,L,w,lvl):
        if L<6 or lvl>6: return
        pts=[p]; q=np.array(p,float)
        for _ in range(int(L/6)):
            a+=rng.normal(0,0.18); q=q+6*np.array([np.cos(a),np.sin(a)]); pts.append(q.copy())
        P=np.round(np.array(pts)*4).astype(np.int32).reshape(-1,1,2)
        cv2.polylines(t,[P],False,1.0/(1+0.35*lvl),max(1,int(w*4)),cv2.LINE_AA)
        for i in range(2,len(pts),max(2,int(4-lvl*0.4))):
            if rng.random()<0.55:
                for sgn in (-1,1):
                    if rng.random()<0.7: br(pts[i],a+sgn*rng.uniform(0.9,1.15),L*rng.uniform(0.25,0.45),w*0.7,lvl+1)
    for k in range(7):
        br((c,c),k*2*np.pi/7+rng.normal(0,0.2),S*0.5*rng.uniform(0.75,0.95),1.4,0)
    t=cv2.resize(t,(S,S),interpolation=cv2.INTER_AREA); return np.clip(t*1.4,0,1)
TEX=frost_tex()
SEEDS=[(s,interp(blade,s)-cum(s)) for s in range(687,697)]           # world-anchored blade path
def frost_layer(src):
    acc=np.zeros((H,W),np.float32); S=TEX.shape[0]
    melt=1.0 if src<=697 else float(np.exp(-(src-697)/5.0))
    if melt<0.03: return acc
    for s0,wp in SEEDS:
        if src<s0: continue
        g=1-np.exp(-(min(src,697)-s0+1)/2.5); r=int(30+150*g)                # radius px
        tex=cv2.resize(TEX,(2*r,max(2,int(2*r*0.5))),interpolation=cv2.INTER_AREA)   # ground perspective squash
        yy,xx=np.mgrid[0:tex.shape[0],0:tex.shape[1]]; ell=((xx-r)/r)**2+((yy-tex.shape[0]/2)/(tex.shape[0]/2))**2
        tex=tex*np.clip(1.3-ell,0,1)
        c=(wp+cum(src)).astype(int); x0,y0=c[0]-r,c[1]-tex.shape[0]//2
        X0,Y0=max(0,x0),max(0,y0); X1,Y1=min(W,x0+tex.shape[1]),min(H,y0+tex.shape[0])
        if X1<=X0 or Y1<=Y0: continue
        acc[Y0:Y1,X0:X1]=np.maximum(acc[Y0:Y1,X0:X1],tex[Y0-y0:Y1-y0,X0-x0:X1-x0])
    pm=LV.people(src)
    if pm is not None: acc*=1-cv2.GaussianBlur(pm,(0,0),1.5)
    return acc*melt
def streak(P,length,inten,thick=1.6):
    yy=np.arange(H,dtype=np.float32)[:,None]; xx=np.arange(W,dtype=np.float32)[None,:]
    v=np.exp(-((yy-P[1])/thick)**2)*np.exp(-np.abs(xx-P[0])/length)
    v+=0.35*np.exp(-((yy-P[1])/(thick*5))**2)*np.exp(-np.abs(xx-P[0])/(length*0.4))
    return v*inten
STREAKC=np.array([0.65,0.55,1.0],np.float32)
def warp(img,dx,dy,z,c):
    M=cv2.getRotationMatrix2D((float(c[0]),float(c[1])),0,z); M[:,2]+=(dx,dy)
    return cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
def fringe(img,amt,c):
    out=img.copy()
    for ch,s in ((2,1+amt),(0,1-amt)):
        M=cv2.getRotationMatrix2D((float(c[0]),float(c[1])),0,s); out[...,ch]=cv2.warpAffine(img[...,ch],M,(W,H),borderMode=cv2.BORDER_REFLECT)
    return out
def shockwave(img,c,r,amp,width=28):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32); dx=xx-c[0]; dy=yy-c[1]; d=np.sqrt(dx*dx+dy*dy)+1e-3
    g=np.exp(-((d-r)/width)**2)*np.sin((d-r)/width*np.pi)*amp
    return cv2.remap(img,(xx-dx/d*g).astype(np.float32),(yy-dy/d*g).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT), np.exp(-((d-r)/(width*0.8))**2)*abs(amp)/20
def push(tl):                      # slow push-in during charge, snap back on release
    if 96<=tl<=105: x=(tl-96)/9.0; return 1+0.065*x*x*(3-2*x)
    return {106:1.045,107:1.02,108:1.008}.get(tl,1.0)
SHAKE={106:(13,-9),107:(-8,6),108:(4,-3),191:(22,-15),192:(-17,11),193:(10,-7),194:(-5,4),195:(2,-2)}
ZPUNCH={191:1.05,192:1.04,193:1.028,194:1.016,195:1.008}
FLASH={106:(1.7,0.30),107:(1.18,0.06),191:(1.9,0.40),192:(1.25,0.10)}
for tl in range(96,204):
    code=cv2.imread(os.path.join(IN,"gl_%04d.png"%tl),-1).astype(np.float32)/65535; lin=dec(code); s=src_of(tl)
    fl=float(np.clip(rng.normal(1.0,0.18),0.6,1.3))
    if s is not None and s<=715:                           # frost
        fr=frost_layer(s)
        if fr.any():
            soft=cv2.GaussianBlur(fr,(0,0),1.2); halo=cv2.GaussianBlur(fr,(0,0),9)
            lin=lin*(1-soft[...,None]*np.array([0.24,0.55,0.70],np.float32))*(1-0.10*halo[...,None])
            glint=np.clip(fr-0.75,0,1)*4*(rng.random((H,W)).astype(np.float32)>0.985)
            lin=lin+cv2.GaussianBlur(glint,(0,0),0.8)[...,None]*np.array([1.4,1.25,1.1],np.float32)*3
    if s is not None and 698<=s<=739:                      # streak at puck
        P=T[min(s,739)]; st=streak(P,170,1.6*fl)
        if 712<=s<=726:
            bo=blob_occ(s,P)
            if bo is not None: st*=1-bo
        lin=lin+st[...,None]*STREAKC
    if 142<=tl<=185:                                       # frozen CG: steady streak at the frozen puck
        x,y,z=CGP[tl-141]
        if z>0 and 0<=x<W and 0<=y<H: lin=lin+streak((x,y),150+80*np.sin((tl-142)/43*np.pi),1.3*(0.92+0.08*fl))[...,None]*STREAKC
    if tl==106: lin=lin+streak(interp(blade,697),900,4.0,2.4)[...,None]*STREAKC
    if s is not None and 739<=s<=742: lin=lin+streak(impact(s),1200*np.exp(-(s-739)/1.5),5.0*np.exp(-(s-739)/1.3),2.6)[...,None]*STREAKC
    if tl in FLASH: m,a=FLASH[tl]; lin=lin*m+a
    out=enc(lin).astype(np.float32)
    if tl in (106,107): out=fringe(out,0.006 if tl==106 else 0.003,interp(blade,697))
    if 191<=tl<=197 and s is not None:
        k=tl-191; r=40+90*k**1.15+30*k; amp=14*np.exp(-k/2.2)
        out,ring=shockwave(out,impact(s),r,amp); out=enc(dec(out)+ring[...,None]*np.array([0.5,0.5,1.0],np.float32)*0.6).astype(np.float32)
    z=push(tl)*ZPUNCH.get(tl,1.0); dx,dy=SHAKE.get(tl,(0,0))
    if z!=1.0 or dx or dy:
        c=(interp(hands,min(s,697))+interp(blade,min(s,697)))/2 if (s is not None and s<=699) else np.array([960.,540.])
        out=warp(out,dx,dy,z,c)
    cv2.imwrite(os.path.join(OUT,"fx_%04d.png"%tl),(np.clip(out,0,1)*65535+0.5).astype(np.uint16))
print("fx v2 done")
