import numpy as np, cv2, json, sys, os
sys.path.insert(0,os.path.dirname(__file__)); from bolt import bolt, fractal, draw, glow_dot, compose, compose_rgba
W,H=1920,1080
T={int(k):np.array(v) for k,v in json.load(open("puck_track.json")).items()}
T.update({698:np.array([1038,469.]),699:np.array([1067,441.]),700:np.array([1105,419.]),701:np.array([1132,397.])})
CUM={int(k):np.array(v) for k,v in json.load(open("cam_shift_cum.json")).items()}
blade={687:(786,694),689:(777,689),691:(825,661),693:(840,640),695:(845,610),696:(960,560),697:(1045,500)}
def bl(f):
    if f in blade: return np.array(blade[f],float)
    ks=sorted(blade); a=max(k for k in ks if k<f); b=min(k for k in ks if k>f); t=(f-a)/(b-a); return np.array(blade[a])*(1-t)+np.array(blade[b])*t
hands={687:(990,400),691:(990,405),695:(975,445),697:(1000,470)}
def hd(f):
    ks=sorted(hands); a=max([k for k in ks if k<=f] or [ks[0]]); b=min([k for k in ks if k>=f] or [ks[-1]]); t=0 if a==b else (f-a)/(b-a); return np.array(hands[a])*(1-t)+np.array(hands[b])*t
REL=bl(697)
def rel(f): return REL+(CUM[f]-CUM[697])                 # release point, carried through the pan
NET740=np.array([1000,215.])
def net(f): return NET740+(CUM[f]-CUM[740])
def tl_of(src): return 96+(src-687) if src<=733 else 186+(src-734)
def occl(src):
    p="masks/occ_f%04d.png"%src
    return (cv2.imread(p,cv2.IMREAD_GRAYSCALE).astype(np.float32)/255) if os.path.exists(p) else None
def straight_bolt(a,b,rng,branches=3):
    main=fractal(a,b,rng,disp=0.10,depth=7); segs=[(main,1.0)]
    for _ in range(branches):
        i=rng.integers(len(main)//8,len(main)*7//8); s=main[i]; d=b-a; ang=np.arctan2(d[1],d[0])+rng.choice([-1,1])*rng.uniform(0.4,1.1)
        l=np.hypot(*d)*rng.uniform(0.05,0.14); segs.append((fractal(s,s+l*np.array([np.cos(ang),np.sin(ang)]),rng,0.3,5),0.5))
    return segs
for src in list(range(687,733))+list(range(734,748)):
    tl=tl_of(src); rng=np.random.default_rng(2000+src-(src%2))
    core=np.zeros((H,W),np.float32); glow=np.zeros((H,W),np.float32); extra=np.zeros((H,W),np.float32)
    if src<=696:
        k=(src-687)/9.0; b=bl(src); h=hd(src)
        for _ in range(2+int(5*k)):
            a=rng.uniform(0,2*np.pi); r=rng.uniform(25,60+110*k)
            draw(core,glow,bolt(b,b+r*np.array([np.cos(a),np.sin(a)]),rng,branches=1),width=1.6+1.2*k,gain=0.5+0.6*k)
        if k>0.3: draw(core,glow,bolt(h,b,rng,branches=2,disp=0.12),width=1.5,gain=0.4+0.5*k)
        glow_dot(extra,b,18+40*k,0.5+1.2*k)
    elif src==697:
        b=bl(697); glow_dot(extra,b,160,3.0); glow_dot(core,b,22,1.0)
        for _ in range(7):
            a=rng.uniform(0,2*np.pi); draw(core,glow,bolt(b,b+rng.uniform(80,260)*np.array([np.cos(a),np.sin(a)]),rng,2),width=2.6,gain=1.0)
        draw(core,glow,straight_bolt(b,T[698],rng,1),width=3.0,gain=1.2)
    else:
        R=rel(src); scored=src>=740
        p=net(src) if scored else T[min(src,739)]
        fade_tail=1.0 if not scored else max(0.0,1-(src-740)/5)
        draw(core,glow,straight_bolt(R,p,rng,3),width=2.6,gain=1.0*fade_tail)
        if not scored:
            glow_dot(extra,p,26,1.4); glow_dot(core,p,7,1.0)
            for _ in range(3):
                a=rng.uniform(0,2*np.pi); draw(core,glow,bolt(p,p+rng.uniform(20,55)*np.array([np.cos(a),np.sin(a)]),rng,0),width=1.4,gain=0.8)
        if src>=739:
            N=net(src); k=min(1,(src-738)/2); fade=max(0,1-(src-740)/4)
            glow_dot(extra,N,60+110*k,2.2*fade)
            for _ in range(int(7*fade)+1):
                a=rng.uniform(0,2*np.pi); draw(core,glow,bolt(N,N+rng.uniform(110,380)*fade*np.array([np.cos(a),np.sin(a)]),rng,3),width=3.0,gain=1.2*fade)
    img=compose_rgba(core,glow,extra).astype(np.float32)
    oc=occl(src)
    if oc is not None: img[...,3]*=(1-oc)
    cv2.imwrite("overlay_v4/lightning_tl_%04d.png"%tl, img.astype(np.uint8))
print("done", REL, rel(733), net(745))
