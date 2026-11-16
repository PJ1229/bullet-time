import numpy as np, cv2, json
T={int(k):np.array(v) for k,v in json.load(open("puck_track.json")).items()}
T.update({698:np.array([1038,469.]),699:np.array([1067,441.]),700:np.array([1105,419.]),701:np.array([1132,397.])})
CUM={int(k):np.array(v) for k,v in json.load(open("cam_shift_cum.json")).items()}
REL=np.array([1045,500.]); NET740=np.array([1000,215.])
def rel(f): return REL+(CUM[f]-CUM[697])
def net(f): return NET740+(CUM[f]-CUM[740])
yy,xx=np.mgrid[0:540,0:960].astype(np.float32)
for f in range(698,748):
    if f==733+100: pass
    D=np.load("masks/depth_f%04d.npy"%f).astype(np.float32); M=cv2.imread("masks/peopleD_f%04d.png"%f,cv2.IMREAD_GRAYSCALE)
    M=cv2.resize(M,(960,540),interpolation=cv2.INTER_NEAREST)>127
    R=rel(f)/2; P=(net(f) if f>=740 else T[min(f,739)])/2
    def samp(p):
        x,y=int(np.clip(p[0],0,959)),int(np.clip(p[1],0,539)); return float(np.median(D[max(0,y-6):y+7,max(0,x-6):x+7]))
    dR=samp(R) if (0<=R[0]<960 and 0<=R[1]<540) else 0.95
    dP=samp(P+np.array([0,10]))
    d=P-R; L2=(d**2).sum()+1e-6; t=np.clip(((xx-R[0])*d[0]+(yy-R[1])*d[1])/L2,0,1)
    boltD=dR+(dP-dR)*t
    occ=(M & (D>boltD+0.05)).astype(np.uint8)
    if f<=706: cv2.circle(occ,(int(R[0]),int(R[1])),55,0,-1)       # keep the release at the blade visible
    occ=cv2.dilate(occ,np.ones((3,3),np.uint8)); occ=cv2.resize(occ.astype(np.float32),(1920,1080)); occ=cv2.GaussianBlur(occ,(0,0),1.5)
    cv2.imwrite("masks/occ_f%04d.png"%f,(np.clip(occ,0,1)*255).astype(np.uint8))
print("occ done")
