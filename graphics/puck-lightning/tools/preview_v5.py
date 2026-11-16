import cv2,numpy as np,sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
od=sys.argv[1]; tls=[int(x) for x in sys.argv[3:]]; name=sys.argv[2]
ims=[]
for tl in tls:
    if 142<=tl<=185: bg=cv2.imread("../hockey-puck-goal/render_bullettime_v10_slog3/bt_%04d.png"%(tl-141),-1).astype(np.float32)/65535
    else:
        src=tl+591 if tl<=141 else tl+548; bg=cv2.imread("src_frames/src_%04d.png"%src).astype(np.float32)/255
    ov=cv2.imread(os.path.join(od,"lt_%04d.png"%tl),-1).astype(np.float32)/65535
    c=np.clip(bg+ov,0,1)
    im=cv2.resize((c*255).astype(np.uint8),(640,360)); cv2.putText(im,str(tl),(6,24),0,.8,(0,255,255),2); ims.append(im)
while len(ims)%3: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(name,np.vstack([np.hstack(ims[r:r+3]) for r in range(0,len(ims),3)]))
