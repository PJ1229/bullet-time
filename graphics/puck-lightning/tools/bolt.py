"""Hockey lightning look: white-hot core + hockey-red glow, additive. Reusable for trail + transitions."""
import numpy as np, cv2
RED=np.array([8,6,195],np.float32)/255     # BGR hockey red
WHITE=np.array([1,1,1],np.float32)
def fractal(p0,p1,rng,disp=0.22,depth=6):
    pts=[np.array(p0,float),np.array(p1,float)]
    for _ in range(depth):
        out=[pts[0]]
        for a,b in zip(pts[:-1],pts[1:]):
            m=(a+b)/2; d=b-a; L=np.hypot(*d)+1e-6; n=np.array([-d[1],d[0]])/L
            out+= [m+n*rng.normal(0,disp*L*0.5), b]
        pts=out
    return np.array(pts)
def bolt(p0,p1,rng,branches=3,disp=0.22):
    main=fractal(p0,p1,rng,disp); segs=[(main,1.0)]
    for _ in range(branches):
        i=rng.integers(len(main)//6,max(len(main)//6+1,len(main)*5//6)); a=main[i]
        d=np.array(p1,float)-np.array(p0,float); L=np.hypot(*d)
        ang=np.arctan2(d[1],d[0])+rng.normal(0,0.9); l=L*rng.uniform(0.15,0.4)
        segs.append((fractal(a,a+l*np.array([np.cos(ang),np.sin(ang)]),rng,disp*1.2,5),0.55))
    return segs
def draw(canvas_core, canvas_glow, segs, width=2.2, gain=1.0):
    for pts,w in segs:
        P=np.round(pts*16).astype(np.int32).reshape(-1,1,2)
        cv2.polylines(canvas_core,[P],False,float(gain*w),max(1,int(round(width*w))),cv2.LINE_AA,4)
        cv2.polylines(canvas_glow,[P],False,float(gain*w),max(2,int(round(width*w*4))),cv2.LINE_AA,4)
def glow_dot(canvas,c,r,gain):
    cv2.circle(canvas,(int(c[0]),int(c[1])),int(r),float(gain),-1,cv2.LINE_AA)
def compose(core,glow,extra_glow=None):
    """core/glow: float32 HxW intensity. returns BGR uint8 (black bg, use ADD composite)."""
    g1=cv2.GaussianBlur(glow,(0,0),6); g2=cv2.GaussianBlur(glow,(0,0),22); g3=cv2.GaussianBlur(glow,(0,0),60)
    if extra_glow is not None: g2=g2+cv2.GaussianBlur(extra_glow,(0,0),30); g3=g3+cv2.GaussianBlur(extra_glow,(0,0),90)
    red=(g1*0.9+g2*1.6+g3*1.2)[...,None]*RED*1.6
    hot=(cv2.GaussianBlur(core,(0,0),1.2)*1.0+g1*0.35)[...,None]*WHITE
    out=1-np.exp(-(red+hot)*1.4)        # soft clip
    return (np.clip(out,0,1)*255).astype(np.uint8)

def compose_rgba(core,glow,extra_glow=None,red_gain=1.0):
    """Normal-blend version (keeps true red on bright/white backgrounds). Returns BGRA uint8."""
    g1=cv2.GaussianBlur(glow,(0,0),5); g2=cv2.GaussianBlur(glow,(0,0),18); g3=cv2.GaussianBlur(glow,(0,0),48)
    if extra_glow is not None: g2=g2+cv2.GaussianBlur(extra_glow,(0,0),24); g3=g3+cv2.GaussianBlur(extra_glow,(0,0),70)
    ar=1-np.exp(-(g1*1.4+g2*1.9+g3*1.1)*1.6*red_gain)          # red glow coverage
    ac=np.clip(cv2.GaussianBlur(core,(0,0),1.0)*1.6+g1*0.25,0,1)  # white-hot core
    red=np.array([10,8,200],np.float32)/255; white=np.array([1,1,1],np.float32)
    a=ac+ar*(1-ac)
    rgb=(white*ac[...,None]+red*(ar*(1-ac))[...,None])/np.maximum(a,1e-4)[...,None]
    return np.dstack([(np.clip(rgb,0,1)*255).astype(np.uint8),(np.clip(a,0,1)*255).astype(np.uint8)])
