"""Drama pass over the baked log lightning frames (gl_*.png -> fx_*.png, S-Log3 16-bit).
release: shake + zoom punch + white flash + colour fringe | flight: sparks & ice chips off the puck (world-anchored, gravity)
score: heavy shake + white flash + shockwave ripple from the net + spark bursts off the posts/crossbar."""
import numpy as np, cv2, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import lightning_v5 as LV
from lightning_v5 import dec, enc, T, cum, interp, blade, goal, impact, blob_occ
W,H=1920,1080
IN,OUT=sys.argv[1],sys.argv[2]; os.makedirs(OUT,exist_ok=True)
def src_of(tl): return tl+591 if tl<=141 else (tl+548 if tl>=186 else None)
rng=np.random.default_rng(77)
# ---------- particle sim (screen space, pan-compensated) ----------
parts=[]   # dict: p,v,life,age,kind
SPARK=np.array([0.30,0.62,1.0],np.float32); CHIP=np.array([1.0,0.97,0.93],np.float32)
def spawn(p,n,speed,kind,spread=np.pi,base=None,life=(6,12)):
    for _ in range(n):
        a=(base if base is not None else rng.uniform(0,2*np.pi))+rng.uniform(-spread,spread)
        s=rng.uniform(*speed); parts.append(dict(p=np.array(p,float),v=s*np.array([np.cos(a),np.sin(a)]),life=rng.integers(*life),age=0,kind=kind,b=rng.uniform(0.6,1.4)))
def step(shift):
    for q in parts:
        q["prev"]=q["p"].copy(); q["p"]=q["p"]+q["v"]+shift; q["v"]=q["v"]*0.9+np.array([0,1.1 if q["kind"]=="chip" else 1.6]); q["age"]+=1
    parts[:]=[q for q in parts if q["age"]<=q["life"]]
def render_parts():
    c_s=np.zeros((H,W),np.float32); c_c=np.zeros((H,W),np.float32); c_p=np.zeros((H,W),np.float32)
    for q in parts:
        f=1-q["age"]/(q["life"]+1); a=np.round(q.get("prev",q["p"])*16).astype(int); b=np.round(q["p"]*16).astype(int)
        cv={"spark":c_s,"chip":c_c,"post":c_p}[q["kind"]]
        cv2.line(cv,tuple(a),tuple(b),float(f*q["b"]),3 if q["kind"]=="chip" else 2,cv2.LINE_AA,4)
    return c_s,c_c,c_p
def warp_shift(img,dx,dy,z,cx=960,cy=540):
    M=cv2.getRotationMatrix2D((cx,cy),0,z); M[:,2]+=(dx,dy)
    return cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
def fringe(img,amt,c):
    out=img.copy(); 
    for ch,s in ((2,1+amt),(0,1-amt)):
        M=cv2.getRotationMatrix2D(tuple(map(float,c)),0,s); out[...,ch]=cv2.warpAffine(img[...,ch],M,(W,H),borderMode=cv2.BORDER_REFLECT)
    return out
def shockwave(img,c,r,amp,width=28):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32); dx=xx-c[0]; dy=yy-c[1]; d=np.sqrt(dx*dx+dy*dy)+1e-3
    g=np.exp(-((d-r)/width)**2)*np.sin((d-r)/width*np.pi)*amp
    mx=(xx-dx/d*g).astype(np.float32); my=(yy-dy/d*g).astype(np.float32)
    return cv2.remap(img,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT), np.exp(-((d-r)/(width*0.8))**2)*abs(amp)/20
SHAKE={106:(13,-9,1.035),107:(-8,6,1.022),108:(4,-3,1.01),
       191:(22,-15,1.05),192:(-17,11,1.04),193:(10,-7,1.028),194:(-5,4,1.016),195:(2,-2,1.008)}
FLASH={106:(1.7,0.30),107:(1.18,0.06),191:(1.9,0.40),192:(1.25,0.10)}
prev_src=None
for tl in range(96,204):
    code=cv2.imread(os.path.join(IN,"gl_%04d.png"%tl),-1).astype(np.float32)/65535
    lin=dec(code); s=src_of(tl)
    if s is not None:
        if prev_src is not None and s>prev_src: step(cum(s)-cum(prev_src))
        prev_src=s
        if 698<=s<=738:                                    # flight: shed sparks & ice chips off the puck
            P=T[min(s,739)]; dirv=T[min(s+1,739)]-T[max(s-1,698)]; back=np.arctan2(-dirv[1],-dirv[0])
            spawn(P,8,(6,18),"spark",0.8,back,(5,11)); spawn(P,3,(3,9),"chip",1.1,back,(6,12))
        if s==697: spawn(interp(blade,697),26,(6,20),"spark",np.pi,None,(5,10))
        if s==739:                                         # score: bursts off posts + crossbar + impact
            g=goal(s); I=impact(s)
            spawn(I,45,(8,26),"spark",np.pi,None,(7,14)); spawn(I,18,(4,12),"chip",np.pi,None,(8,14))
            for k in ("LT","RT"): spawn(g[k],18,(6,18),"post",np.pi,None,(6,12))
            for t in np.linspace(0,1,6): spawn(g["LT"]+(g["RT"]-g["LT"])*t,4,(4,12),"post",np.pi,None,(5,10))
        if s in (740,741): spawn(impact(s),12,(5,15),"spark",np.pi,None,(5,10))
        cs,cc,cp=render_parts()
        if cp.any():
            pm=LV.people(s)
            if pm is not None: cp*=1-cv2.GaussianBlur(pm,(0,0),1.5)
            cs=cs+cp
        if 712<=s<=726:
            bo=blob_occ(s,T[min(s,739)])
            if bo is not None: cs*=1-bo; cc*=1-bo
        light=cv2.GaussianBlur(cs,(0,0),0.6)[...,None]*SPARK*24+cv2.GaussianBlur(cs,(0,0),4)[...,None]*SPARK*7+cv2.GaussianBlur(cc,(0,0),0.7)[...,None]*CHIP*1.6
        lin=lin+light
    if tl in FLASH: m,a=FLASH[tl]; lin=lin*m+a
    out=enc(lin).astype(np.float32)
    if tl in (106,107): out=fringe(out,0.006 if tl==106 else 0.003,interp(blade,697))
    if 191<=tl<=197 and s is not None:
        k=tl-191; r=40+90*k**1.15+30*k; amp=14*np.exp(-k/2.2)
        out,ring=shockwave(out,impact(s),r,amp)
        lr=dec(out)+ring[...,None]*np.array([0.5,0.5,1.0],np.float32)*0.6; out=enc(lr).astype(np.float32)
    if tl in SHAKE:
        dx,dy,z=SHAKE[tl]; out=warp_shift(out,dx,dy,z)
    cv2.imwrite(os.path.join(OUT,"fx_%04d.png"%tl),(np.clip(out,0,1)*65535+0.5).astype(np.uint16))
print("fx done")
