import sys,os,cv2,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import grade_stills as g
IN=sys.argv[1]; OUT=sys.argv[2]; frames=sys.argv[3].split(',')
import glob
paths=[glob.glob(f"{IN}/bullet_time_{int(f):04d}_*_SLog3.tif")[0] for f in frames]
pre={}
for p in paths:
    a=cv2.imread(p,-1)[...,::-1].astype(np.float32)/65535; a=cv2.resize(a,(960,540),interpolation=cv2.INTER_AREA)
    lin=np.clip(g.slog3_dec(a)@g.SG3C_TO_709.T,0,None); pre[p]=g.filmic(g.correct(lin))
rows=[]
for name,L in g.LOOKS.items():
    g.LOOK.update(L); r=[]
    for p in paths:
        d=g.finish(g.grade(pre[p].copy()),0); im=(d[...,::-1]*255).astype(np.uint8); im=cv2.resize(im,(480,270))
        r.append(im)
    row=np.hstack(r); cv2.putText(row,name,(8,26),0,.8,(255,255,255),2); rows.append(row)
cv2.imwrite(OUT,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,88])
