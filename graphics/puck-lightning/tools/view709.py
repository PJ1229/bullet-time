"""quick S-Log3 -> display preview (not a grade): linear, +0.3 stop, filmic shoulder, Rec709 gamma"""
import numpy as np, cv2, sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from bake_lightning_log import dec
def view(code):
    x=np.maximum(dec(code),0)*0.55; t=(x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14); return np.clip(np.clip(t,0,1)**(1/2.2),0,1)
if __name__=="__main__":
    d=sys.argv[1]; name=sys.argv[2]; tls=[int(x) for x in sys.argv[3:]]; ims=[]
    for tl in tls:
        c=cv2.imread(os.path.join(d,"gl_%04d.png"%tl),-1).astype(np.float64)/65535
        im=cv2.resize((view(c)*255).astype(np.uint8),(640,360)); cv2.putText(im,str(tl),(6,24),0,.8,(0,255,255),2); ims.append(im)
    while len(ims)%3: ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(name,np.vstack([np.hstack(ims[r:r+3]) for r in range(0,len(ims),3)]))
