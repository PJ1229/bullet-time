import numpy as np, cv2, json, sys, os
sys.path.insert(0,os.path.dirname(__file__)); from bolt import bolt, draw, glow_dot, compose
W,H=1920,1080; SS=16  # bolt.draw uses 4-bit subpixel shift
T={int(k):np.array(v) for k,v in json.load(open("puck_track.json")).items()}
T.update({698:np.array([1038,469.]),699:np.array([1067,441.]),700:np.array([1105,419.]),701:np.array([1132,397.])})
blade={687:(786,694),689:(777,689),691:(825,661),693:(840,640),695:(845,610),696:(960,560),697:(1045,500)}
def bl(f):
    ks=sorted(blade); 
    if f in blade: return np.array(blade[f],float)
    a=max(k for k in ks if k<f); b=min(k for k in ks if k>f); t=(f-a)/(b-a); return np.array(blade[a])*(1-t)+np.array(blade[b])*t
hands={687:(990,400),691:(990,405),695:(975,445),697:(1000,470)}
def hd(f):
    ks=sorted(hands); a=max([k for k in ks if k<=f] or [ks[0]]); b=min([k for k in ks if k>=f] or [ks[-1]])
    t=0 if a==b else (f-a)/(b-a); return np.array(hands[a])*(1-t)+np.array(hands[b])*t
def tl_of(src): return 96+(src-687) if src<=733 else 186+(src-734)
NET=np.array([1000,215.])
TR3=json.load(open('trail3d_proj.json')); TRP=np.array(TR3['trail3d_px1920']); TRP_end=TRP[-1]
for src in list(range(687,733))+list(range(734,748)):
    tl=tl_of(src); seed=src - (src%2)          # on 2s
    rng=np.random.default_rng(1000+seed)
    core=np.zeros((H,W),np.float32); glow=np.zeros((H,W),np.float32); extra=np.zeros((H,W),np.float32)
    if src<=696:                                   # CHARGE-UP on the blade + up the shaft
        k=(src-687)/9.0; b=bl(src); h=hd(src)
        for _ in range(2+int(5*k)):
            a=rng.uniform(0,2*np.pi); r=rng.uniform(25,60+110*k)
            draw(core,glow,bolt(b,b+r*np.array([np.cos(a),np.sin(a)]),rng,branches=1),width=1.6+1.2*k,gain=0.5+0.6*k)
        if k>0.3: draw(core,glow,bolt(h,b,rng,branches=2,disp=0.12),width=1.5,gain=0.4+0.5*k)
        glow_dot(extra,b,18+40*k,0.5+1.2*k)
    elif src==697:                                 # RELEASE: transfer flash
        b=bl(697); p=T[698]
        glow_dot(extra,b,160,3.0); glow_dot(core,b,22,1.0)
        for _ in range(7):
            a=rng.uniform(0,2*np.pi); draw(core,glow,bolt(b,b+rng.uniform(80,260)*np.array([np.cos(a),np.sin(a)]),rng,2),width=2.6,gain=1.0)
        draw(core,glow,bolt(b,p,rng,1,0.15),width=3.0,gain=1.2)
    else:                                          # TRAIL following the puck
        p=T[min(src,739)]
        hist=[T[s] for s in range(max(698,src-9),min(src,739)+1) if s in T]
        if src<=705: hist=[bl(697)]+hist           # still tethered to the blade right after release
        w3=0.0
        if 726<=src<=733: w3=min(1.0,(src-725)/6.0)
        if 734<=src<=737: w3=max(0.0,1.0-(src-734)/4.0)
        if len(hist)>=2 and w3<1:
            for a,b2 in zip(hist[:-1],hist[1:]):
                if np.hypot(*(b2-a))<2: continue
                draw(core,glow,bolt(a,b2,rng,branches=1,disp=0.28),width=2.4,gain=1.0-w3)
        if w3>0:
            shp=TRP-TRP_end+p
            for a,b2 in zip(shp[:-1],shp[1:]): draw(core,glow,bolt(a,b2,rng,branches=1,disp=0.30),width=2.4,gain=w3)
        glow_dot(extra,p,26,1.4); glow_dot(core,p,7,1.0)
        for _ in range(3):
            a=rng.uniform(0,2*np.pi); draw(core,glow,bolt(p,p+rng.uniform(20,55)*np.array([np.cos(a),np.sin(a)]),rng,0),width=1.4,gain=0.8)
        if src>=739:                               # IMPACT burst into the net (tl ~191-192 = DROP)
            k=min(1,(src-738)/2); fade=max(0,1-(src-740)/4)
            glow_dot(extra,NET,60+110*k,2.2*fade)
            for _ in range(int(7*fade)+1):
                a=rng.uniform(0,2*np.pi); draw(core,glow,bolt(NET,NET+rng.uniform(110,380)*fade*np.array([np.cos(a),np.sin(a)]),rng,3),width=3.0,gain=1.2*fade)
    cv2.imwrite("overlay_v1/lightning_tl_%04d.png"%tl, compose(core,glow,extra))
print("done")
