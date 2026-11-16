"""Realistic lightning v5 — light, not paint.
Layers per frame (all ADDITIVE, composite mode Add over V1):
  core   : tapered multi-scale jagged channels (+recursive branches), white-hot
  bloom  : tight lens/air glow around the core (occluded with the core)
  spill  : red light falling on surfaces = blurred energy x plate luminance (NOT occluded: it lights players too)
  refl   : soft glossy-ice reflection of core+bloom below the channel (ice pixels only)
Flicker every frame, comet-tail trail + fading channel afterglow, no discs.
usage: python3 lightning_v5.py OUTDIR [tl ...]   (no tl list = all 96..203)"""
import numpy as np, cv2, json, os, sys
D=os.path.dirname(os.path.abspath(__file__)); B=os.path.dirname(D); os.chdir(B)
W,H=1920,1080
T={int(k):np.array(v,float) for k,v in json.load(open("puck_track.json")).items()}
T.update({698:np.array([1038,469.]),699:np.array([1067,441.]),700:np.array([1105,419.]),701:np.array([1132,397.])})
CUM={int(k):np.array(v,float) for k,v in json.load(open("cam_shift_cum.json")).items()}
blade={687:(735,712),689:(830,708),691:(810,665),693:(840,607),694:(850,614),695:(846,618),696:(1043,500),697:(1055,505),698:(1090,478),699:(1110,457),700:(1125,450),701:(1135,445),702:(1140,440)}
hands={687:(1015,415),689:(1040,435),691:(1039,418),693:(1029,450),694:(1007,454),695:(993,464),696:(993,514),697:(1000,507),702:(1010,505)}
def interp(dct,f):
    ks=sorted(dct); a=max([k for k in ks if k<=f] or [ks[0]]); b=min([k for k in ks if k>=f] or [ks[-1]]); t=0 if a==b else (f-a)/(b-a)
    return np.array(dct[a],float)*(1-t)+np.array(dct[b],float)*t
def cum(f): return CUM[min(max(f,min(CUM)),max(CUM))]
REL=np.array((1045,500),float)
def rel(f): return REL+(cum(f)-cum(697))
# goal frame at src 740 (px), carried by the pan
G740={"LT":(1078,110),"LB":(1062,372),"RT":(1430,190),"RB":(1412,455)}
def goal(f): return {k:np.array(v,float)+(cum(f)-cum(740)) for k,v in G740.items()}
IMPACT740=np.array([1088,240.])
def impact(f): return IMPACT740+(cum(f)-cum(740))
def tl_of(src): return 96+(src-687) if src<=733 else 186+(src-734)
def dec(c):
    c=np.asarray(c,np.float32); cc=c*1023
    return np.where(cc>=171.2102946929,(10**((cc-420)/261.5))*0.19-0.01,(cc-95)*0.01125/(171.2102946929-95)).astype(np.float32)
def enc(l):
    l=np.asarray(l,np.float32)
    return np.clip(np.where(l>=0.01125,(420+np.log10(np.maximum(l+0.01,1e-6)/0.19)*261.5)/1023,(l*(171.2102946929-95)/0.01125+95)/1023),0,1)
RED=np.array([0.10,0.12,1.0],np.float32)       # BGR
PINK=np.array([0.55,0.50,1.0],np.float32)
HOT=np.array([0.93,0.90,1.0],np.float32)

def jag(p0,p1,rng,rough=0.18,depth=8,decay=0.58):
    """stepped leader: short kinked steps biased toward the target (rough ~ angular jitter)"""
    p0=np.array(p0,float); p1=np.array(p1,float); L=np.hypot(*(p1-p0))+1e-6
    step=float(np.clip(L/60,3.0,11.0)); jit=0.35+2.2*rough
    pts=[p0.copy()]; cur=p0.copy(); n=0
    while np.hypot(*(p1-cur))>step*1.5 and n<4000:
        d=p1-cur; ang=np.arctan2(d[1],d[0])+rng.normal(0,jit)
        if rng.random()<0.08: ang+=rng.choice([-1,1])*rng.uniform(0.6,1.1)     # sharp kink
        l=step*rng.uniform(0.5,1.5); cur=cur+l*np.array([np.cos(ang),np.sin(ang)]); pts.append(cur.copy()); n+=1
    pts.append(p1)
    P=np.array(pts)
    if len(P)>4: P[1:-1]=0.75*P[1:-1]+0.125*(P[:-2]+P[2:])                    # tiny smoothing (lens)
    return P
def channel(p0,p1,rng,rough=0.16,branch=0.5,lvl=0,w0=3.0,i0=1.0,out=None):
    """returns list of (pts, width_start, width_end, intensity)"""
    out=[] if out is None else out
    pts=jag(p0,p1,rng,rough); out.append((pts,w0,w0*0.35,i0))
    if lvl<2:
        n=rng.poisson(branch*(2.2 if lvl==0 else 1.0))
        d=np.array(p1,float)-np.array(p0,float); L=np.hypot(*d); ang0=np.arctan2(d[1],d[0])
        for _ in range(n):
            i=rng.integers(len(pts)//10,max(len(pts)//10+1,len(pts)*8//10)); s=pts[i]
            ang=ang0+rng.choice([-1,1])*rng.uniform(0.3,0.75); l=min(L*rng.uniform(0.12,0.3),110.0/(lvl+1))
            channel(s,s+l*np.array([np.cos(ang),np.sin(ang)]),rng,rough*1.15,branch*0.6,lvl+1,w0*0.45,i0*rng.uniform(0.35,0.6),out)
    return out
def draw(core,segs,weight=None):
    for pts,wa,wb,inten in segs:
        n=len(pts)-1
        for j in range(n):
            u=j/max(n,1); w=wa+(wb-wa)*u; I=inten*(weight(pts[j]) if weight else 1.0)
            if I<0.01: continue
            a=np.round(pts[j]*16).astype(int); b=np.round(pts[j+1]*16).astype(int)
            cv2.line(core,tuple(a),tuple(b),float(I),max(1,int(round(w))),cv2.LINE_AA,4)
def lum(img):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
    return g
GAIN=dict(core=60.0,b1=28.0,b2=16.0,b3=8.0,spill=3.5,refl=10.0,flash=2.5)
REDL=np.array([0.02,0.035,1.0],np.float32); PINKL=np.array([0.25,0.22,1.0],np.float32); HOTL=np.array([0.95,0.93,1.0],np.float32)
def finish(core,albedo,occ,spill_gain=1.0,global_flash=0.0,refl_dy=70,refl_gain=0.16,ice=None,white_flash=0.0,bg_lin=None):
    """returns scene-linear light (BGR float) to ADD to the decoded S-Log3 plate"""
    core_o=core*(1-occ) if occ is not None else core
    b1=cv2.GaussianBlur(core_o,(0,0),2.2); b2=cv2.GaussianBlur(core_o,(0,0),7); b3=cv2.GaussianBlur(core_o,(0,0),22)
    e=cv2.GaussianBlur(core,(0,0),9); s1=cv2.GaussianBlur(e,(0,0),45); s2=cv2.GaussianBlur(e,(0,0),140)
    spill=(s1*14+s2*40)*spill_gain+global_flash
    alb=np.clip(bg_lin/0.9,0,1.5) if bg_lin is not None else albedo[...,None]
    L=cv2.GaussianBlur(core_o,(0,0),0.7)[...,None]*HOTL*GAIN["core"]
    L+=(b1*GAIN["b1"])[...,None]*PINKL+(b2*GAIN["b2"]+b3*GAIN["b3"])[...,None]*REDL
    L+=spill[...,None]*REDL*GAIN["spill"]*alb
    if refl_gain>0 and ice is not None:
        r=np.roll(core_o+b2*0.6,refl_dy,axis=0); r[:refl_dy]=0; r=cv2.GaussianBlur(r,(0,0),sigmaX=3,sigmaY=14)
        L+=(r*refl_gain*ice*GAIN["refl"])[...,None]*PINKL
    if white_flash>0: L+=white_flash*GAIN["flash"]*alb*HOTL
    return L
def occl(src):
    p="masks/occ_f%04d.png"%src
    return cv2.imread(p,0).astype(np.float32)/255 if os.path.exists(p) else None
def people(src):
    for s in (src,src-1,src-2,src-3,747):
        p="masks/peopleD_f%04d.png"%s
        if os.path.exists(p):
            m=cv2.imread(p,0).astype(np.float32)/255; sh=cum(src)-cum(s)
            return cv2.warpAffine(m,np.float32([[1,0,sh[0]],[0,1,sh[1]]]),(W,H))
    return None
def blob_occ(src,P,radius=130):
    """people silhouettes the puck is passing BEHIND: whole connected blob near the puck occludes"""
    p="masks/peopleD_f%04d.png"%src
    if not os.path.exists(p): return None
    m=(cv2.imread(p,0)>127).astype(np.uint8); n,lab=cv2.connectedComponents(m)
    yy,xx=np.ogrid[:H,:W]; near=((xx-P[0])**2+(yy-P[1])**2)<radius**2
    ids=[i for i in np.unique(lab[near & (m>0)]) if i>0]
    if not ids: return None
    o=np.isin(lab,ids).astype(np.float32); o=cv2.dilate(o,np.ones((5,5),np.uint8))
    return cv2.GaussianBlur(o,(0,0),1.5)
def shooter(src):
    p="masks/peopleD_f%04d.png"%src
    if not os.path.exists(p): return None
    m0=(cv2.imread(p,0)>127).astype(np.uint8)
    m=cv2.morphologyEx(m0,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))   # cut thin stick bridges
    n,lab=cv2.connectedComponents(m)
    h=interp(hands,src).astype(int); best=None
    for r in (0,15,35,60):
        win=lab[max(0,h[1]-r):h[1]+r+1,max(0,h[0]-r):h[0]+r+1]; ids=[i for i in np.unique(win) if i>0]
        if ids: best=max(ids,key=lambda i:(lab==i).sum()); break
    if best is None: return None
    body=cv2.dilate((lab==best).astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(17,17)))
    return (body&m0).astype(np.uint8)
def contour_arcs(core,sm,rng,n,inten,width):
    cs,_=cv2.findContours(sm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    if not cs: return
    c=max(cs,key=len)[:,0,:].astype(float); N=len(c)
    if N<50: return
    for _ in range(n):
        i=rng.integers(0,N); L=int(rng.uniform(40,150)); idx=(i+np.arange(0,L,5))%N
        pts=c[idx]; d=np.gradient(pts,axis=0); nrm=np.stack([-d[:,1],d[:,0]],1); nrm/=np.linalg.norm(nrm,axis=1,keepdims=True)+1e-6
        pts=pts+nrm*rng.uniform(1,5)+rng.normal(0,2.2,pts.shape)
        draw(core,[(pts,width,width*0.4,inten)])
def frame_src(src):
    p="src_frames/src_%04d.png"%src; return cv2.imread(p)
def ice_mask(img):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV); l=hsv[...,2].astype(np.float32)/255; s=hsv[...,1].astype(np.float32)/255
    m=((l>0.55)&(s<0.22)).astype(np.float32); return cv2.GaussianBlur(m,(0,0),3)

def live(src,rng,flick):
    rng=np.random.default_rng(5000+src//2)
    img=frame_src(src); alb=lum(img); ice=ice_mask(img); core=np.zeros((H,W),np.float32); occ=occl(src)
    bgc=img.astype(np.float32)/255; bg_lin=dec(bgc)
    gflash=0.0; spill=1.0; refl=0.16; wflash=0.0
    if src<=696:                                   # CHARGE-UP: energy builds ON the player, flows down the stick
        k=(src-687)/9.0; b=interp(blade,src); h=interp(hands,src); sh=b-h; Ls=np.hypot(*sh)
        sm=shooter(src)
        if sm is not None: contour_arcs(core,sm,rng,2+int(9*k),0.45+0.75*k,1.3+1.0*k)
        stick=np.zeros((H,W),np.float32); n=np.array([-sh[1],sh[0]])/(Ls+1e-6)
        for _ in range(2+int(4*k)):
            t1=rng.uniform(0.0,0.7); t2=min(1.0,t1+rng.uniform(0.2,0.5))
            draw(stick,channel(h+sh*t1+n*rng.normal(0,3),h+sh*t2+n*rng.normal(0,3),rng,0.18,0.3,1,1.6+1.4*k,0.6+0.8*k))
        if sm is not None: stick*=1-cv2.GaussianBlur(cv2.erode(sm,np.ones((7,7),np.uint8)).astype(np.float32),(0,0),2)
        core=np.maximum(core,stick)
        for _ in range(1+int(3*k)):
            a=rng.uniform(np.radians(20),np.radians(160)); r=rng.uniform(18,40+70*k)
            draw(core,channel(b,b+r*np.array([np.cos(a),np.sin(a)*0.55]),rng,0.3,0.6,1,1.8+1.6*k,0.8+0.9*k))
        cv2.circle(core,tuple(np.round(b*16).astype(int)),int(16*(2+3*k)),0.35+0.6*k,-1,cv2.LINE_AA,4)
        spill=0.45+1.1*k; refl=0.10
    elif src==697:                                 # RELEASE: white flash, burst at blade, strike toward puck
        b=interp(blade,697); sm=shooter(697)
        if sm is not None: contour_arcs(core,sm,rng,8,1.0,2.2)
        for _ in range(6):
            a=rng.uniform(0,2*np.pi); draw(core,channel(b,b+rng.uniform(60,190)*np.array([np.cos(a),np.sin(a)*0.6]),rng,0.24,0.8,0,2.6,0.9))
        draw(core,channel(b,T[698]+(T[698]-b)*0.4,rng,0.12,0.9,0,4.5,1.3))
        gflash=0.0; spill=1.4; wflash=0.10
    else:                                          # FLIGHT / SCORE
        R=rel(src); scored=src>=739
        P=T[min(src,739)] if src<=739 else impact(src)
        age=src-697; d=P-R; L=np.hypot(*d)+1e-6
        if 698<=src<=703:
            tf=1-(src-698)/6.0; bb=interp(blade,min(src,702)); draw(core,channel(bb,R+(P-R)*0.08,rng,0.22,0.5,0,2.4,1.1*tf))
            sm=shooter(src)
            if sm is not None: contour_arcs(core,sm,rng,int(1+5*tf),0.8*tf,1.6)
        if 712<=src<=726:
            bo=blob_occ(src,P)
            if bo is not None: occ=bo if occ is None else np.maximum(occ,bo)
        if src<=741:
            head=320.0
            def wfun(p,R=R,d=d,L=L,age=age,head=head):
                u=np.clip(np.dot(p-R,d)/(L*L),0,1); dist=(1-u)*L
                return max(np.exp(-dist/head), 0.32*np.exp(-age/16))
            fade=1.0 if src<=739 else (0.55 if src==740 else 0.25)
            draw(core,[(pts,wa,wb,i*fade) for pts,wa,wb,i in channel(R,P,rng,0.12,0.7,0,3.6,1.6)],wfun)
            if not scored:
                for _ in range(2):
                    a=rng.uniform(0,2*np.pi); draw(core,channel(P,P+rng.uniform(14,40)*np.array([np.cos(a),np.sin(a)]),rng,0.3,0.3,1,1.4,0.7))
                cv2.circle(core,tuple(np.round(P*16).astype(int)),16*5,1.2,-1,cv2.LINE_AA,4)
        if src>=739:                               # SCORE: arcs crawl the goal frame + into the mesh, then die
            g=goal(src); dk=np.exp(-(src-739)/3.2); I=impact(src)
            net=np.zeros((H,W),np.float32)
            frame_path=[g["LB"],g["LT"],g["RT"],g["RB"]]
            nar=int(2+7*dk)
            for _ in range(nar):
                seg=rng.integers(0,3); a,b_=frame_path[seg],frame_path[seg+1]; t1,t2=sorted(rng.uniform(0,1,2))
                p0=a+(b_-a)*t1; p1=a+(b_-a)*min(1,t2+0.15)
                draw(net,channel(p0,p1,rng,0.06,0.4,1,2.8,1.2*dk))
            for _ in range(int(1+6*dk)):            # from impact into the mesh / along to the frame
                tgt=g["LT"]+(g["RB"]-g["LT"])*rng.uniform(0.1,0.9)+rng.normal(0,25,2)
                draw(net,channel(I,tgt,rng,0.2,0.7,0,3.4,1.4*dk))
            if src==739: draw(net,channel(I,I+np.array([0,140.]),rng,0.25,0.8,0,3.0,1.2))
            pm=people(src)
            if pm is not None: net*=(1-cv2.GaussianBlur(pm,(0,0),1.5))
            core=np.maximum(core,net)
            spill=0.9*dk+0.1; wflash=0.12 if src==739 else (0.05 if src==740 else 0.0)
    core*=flick
    return bgc,finish(core,alb,occ,spill*flick,gflash,refl_gain=refl,ice=ice,white_flash=wflash,bg_lin=bg_lin)

def cg(tl,rng,flick):
    fr=tl-141
    m=cv2.imread("cg_bolt_mask_v4/mask_%04d.png"%fr,-1).astype(np.float32)/255
    core=(m[...,:3].max(-1)*(m[...,3] if m.shape[2]==4 else 1))
    core=cv2.erode(core,np.ones((3,3),np.uint8))**1.6*0.9
    bg=cv2.imread(os.environ.get("CGDIR","../hockey-puck-goal/render_bullettime_v10_slog3")+"/bt_%04d.png"%fr,-1)
    bg8=(bg/257).astype(np.uint8); alb=lum(bg8); ice=ice_mask(bg8); bgc=bg.astype(np.float32)/65535
    if os.environ.get("CGGRAIN","1")=="1":   # match footage: slight softness + log-domain grain (~1.5 cv10)
        bgc=cv2.GaussianBlur(bgc,(0,0),0.55)
        g=np.random.default_rng(777+fr)
        amt=(1.0 if fr in (1,44) else 1.35)/1023.0
        lumn=cv2.GaussianBlur(g.normal(0,1,bgc.shape[:2]).astype(np.float32),(0,0),0.6)*1.6
        chn=cv2.GaussianBlur(g.normal(0,1,bgc.shape).astype(np.float32),(0,0),0.9)*0.5
        bgc=np.clip(bgc+amt*(lumn[...,None]+chn),0,1)
    bg_lin=dec(bgc)
    occ=None
    Wt={1:1,2:.85,3:.6,4:.3,41:.3,42:.6,43:.85,44:1}
    if fr in Wt:
        o=cv2.imread("masks/occ_f0733.png",0).astype(np.float32)/255; occ=Wt[fr]*o
    rs={42:0.55,43:0.18}.get(fr,0.0)                       # restrike flash hides the CG->plate switch (v16)
    if rs: core=np.maximum(core,cv2.dilate(core,np.ones((5,5),np.uint8))*1.4)
    return bgc,finish(core*flick,alb,occ,(0.22+1.2*rs)*flick,0.0,refl_gain=0.0,ice=ice,white_flash=rs,bg_lin=bg_lin)

def render(tl,outdir):
    rng=np.random.default_rng(9000+tl)
    flick=float(np.clip(rng.normal(1.0,0.22),0.55,1.35))
    if rng.random()<0.12: flick*=1.35                       # restrike
    if 142<=tl<=185:
        flick=float(np.clip(1.0+0.08*rng.normal(),0.85,1.15))   # time is frozen: shimmer only
        bgc,L=cg(tl,rng,flick)
    else:
        src=tl+591 if tl<=141 else tl+548
        if src>751: return
        bgc,L=live(src,rng,flick)
    out=enc(np.maximum(dec(bgc),-0.01)+L)
    cv2.imwrite(os.path.join(outdir,"gl_%04d.png"%tl),(out*65535+0.5).astype(np.uint16))
if __name__=="__main__":
    out=sys.argv[1]; os.makedirs(out,exist_ok=True)
    tls=[int(x) for x in sys.argv[2:]] or list(range(96,204))
    for t in tls: render(t,out)
    print("ok",len(tls))
