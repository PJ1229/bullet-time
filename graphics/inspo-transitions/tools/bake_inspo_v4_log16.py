# Bakes inspo-style transitions (zoom punches, pushes, whip/motion blur, radial speed blur, shake, white/black flash frames)
# from the clean LOG (ungraded, colour) timeline render, 16-bit in/out. Output = opaque frames that sit on V3 over V1. Never touches tl 96-203.
import cv2, numpy as np, os, sys
SRC=os.path.expanduser("~/mnt/TOSHIBA EXT/um-athletics/hockey-edit/03_graphics/master_v4/base16/b_%04d.png")   # index = tl (v4 base, new action clips)
OUT=os.path.expanduser("~/mnt/TOSHIBA EXT/um-athletics/hockey-edit/03_graphics/inspo-transitions/bake_v4_log16/fx_tl_%04d.png")
W,H=1920,1080; C=np.array([960.,540.])
def eo(x): x=min(max(x,0),1); return 1-(1-x)**3
def ei(x): x=min(max(x,0),1); return x**3
def zoom(im,s,anchor=C,k=1.0,off=(0,0)):
    a=np.array(anchor,float); c=C+(a-C)*k
    half=np.array([W,H])/(2*s); c=np.clip(c,half,np.array([W,H])-half)   # keep crop inside frame
    M=np.float32([[s,0,960-s*c[0]+off[0]],[0,s,540-s*c[1]+off[1]]])
    return cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
def dblur(im,length,angle=0):
    L=int(length)
    if L<2: return im
    k=np.zeros((L*2+1,L*2+1),np.float32); a=np.deg2rad(angle)
    for t in np.linspace(-L,L,4*L): k[int(round(L+t*np.sin(a))),int(round(L+t*np.cos(a)))]=1
    return cv2.filter2D(im,-1,k/k.sum())
def radial(im,amt,n=9):
    if amt<=0: return im
    acc=np.zeros_like(im,np.float32)
    for i in range(n): acc+=zoom(im,1+amt*i/(n-1)).astype(np.float32)
    return (acc/n).astype(np.float32)
def flash(im,a,white=True):
    if a<=0: return im
    t=65535.0 if white else 0.0
    return np.clip(im.astype(np.float32)*(1-a)+t*a,0,65535).astype(np.float32)
rng=np.random.default_rng(44)
SH={264:(26,-18),265:(-20,14),266:(14,10),267:(-9,-7),268:(5,4),269:(-2,2),270:(0,0)}
FC=[335,341,347,353,359,365,371]                # flash-cut run (377 handled as the push into 384)  v4: WHITE flashes only (no black frames)
def fx(f):
    if not os.path.exists(SRC%f): return None
    im=cv2.imread(SRC%f,cv2.IMREAD_UNCHANGED).astype(np.float32)
    if f<=2: return flash(im,[0.85,0.55,0.25][f],False)                          # fade up from black
    if 24<=f<=47:                                                                 # A1 slow push into the M, whip out
        im=zoom(im,1+0.06*ei((f-24)/23),(700,420),1.0)
        if f>=46: im=dblur(im,[28,64][f-46],0)
        return im
    if f in (48,49): return flash(dblur(im,[46,16][f-48],0),[0.45,0][f-48])      # whip lands + 1f white pop
    if 88<=f<=95:                                                                 # #71 push + upward whip (eyeline into the tilt)
        im=zoom(im,1+0.05*ei((f-88)/7),(960,420))
        if f>=93: im=dblur(im,[12,30,58][f-93],90)
        return im
    if 204<=f<=214: return dblur(im,8+62*np.sin(np.pi*(f-203)/12),0)            # speed-ramp motion blur, peak mid-ramp
    if 215<=f<=238:                                                               # zoom punch on #44, hold & track
        s=1+0.4*eo((f-215)/4) if f<=219 else 1.4+0.02*(f-219)/19
        anc=(890+120*(f-215)/23,420); im=zoom(im,s,anc,1.0)
        if f<=216: im=radial(im,[0.06,0.025][f-215])
        if f==215: im=flash(im,0.5)
        if f>=237: im=dblur(im,[30,72][f-237],0)                                  # whip out into the push
        return im
    if 239<=f<=241: return radial(zoom(im,[1.08,1.04,1.01][f-239]),[0.09,0.05,0.02][f-239])  # USC speed-blur push-in
    if 264<=f<=270:                                                               # contact shake + white hit
        dx,dy=SH[f]; im=zoom(im,1.05,C,1,(dx,dy))
        if f<=265: im=dblur(im,[10,5][f-264],np.rad2deg(np.arctan2(dy,dx)))
        return flash(im,0.4 if f==264 else 0)
    if 287<=f<=289: return flash(zoom(im,[1.07,1.035,1.01][f-287]),0.25 if f==287 else 0)     # match-cut punch-out
    if 311<=f<=334:                                                               # punch into the crease scramble
        s=1+0.15*eo((f-311)/3) if f<=314 else 1.15+0.02*(f-314)/20
        return flash(zoom(im,s,(850,640)),0.3 if f==311 else 0)
    for i,c in enumerate(FC):                                                     # flash-cut run: punch-out + alternating white/black frame
        if c<=f<=c+5:
            if f-c<3: im=zoom(im,[1.06,1.03,1.01][f-c])
            if f==c: im=flash(im,0.35 if i%2==0 else 0.22,True)
            return im
    if 377<=f<=383:                                                               # push into the "9" -> cut to the giant "44"
        im=zoom(im,1+0.25*ei((f-377)/6),(1010,450))
        if f>=381: im=radial(im,[0.02,0.05,0.09][f-381])
        return flash(im,0.3 if f==377 else 0)
    if 384<=f<=386: return flash(radial(zoom(im,[1.10,1.05,1.015][f-384]),[0.08,0.04,0.015][f-384]),0.4 if f==384 else 0)
    if 408<=f<=410: return flash(zoom(im,[1.07,1.035,1.01][f-408]),0.3 if f==408 else 0)   # v4: cele -> RHEAUME-MULLEN rush (punch-out + white)
    if 429<=f<=430: return dblur(im,[40,85][f-429],0)                             # whip pan rush -> crease scramble
    if 431<=f<=432: return dblur(im,[70,28][f-431],0)                             # whip lands on the #72 scramble
    if 455<=f<=466:                                                               # fans: punch-out + white, push accelerating into the puck->lens
        s=[1.06,1.03,1.01][f-455] if f<=457 else 1.0+0.15*ei((f-457)/9)
        im=zoom(im,s,(900,480))
        return flash(im,0.25 if f==455 else 0)
    return None
lo,hi=int(sys.argv[1]),int(sys.argv[2]); done=[]
for f in range(lo,hi+1):
    if 96<=f<=203: continue
    o=fx(f)
    if o is not None: cv2.imwrite(OUT%f,np.clip(o,0,65535).astype(np.uint16)); done.append(f)
print(len(done),done[:3],done[-3:])
