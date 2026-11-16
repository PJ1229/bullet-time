"""quick test-grade view of EXR renders: python3 qview.py out.jpg a.exr b.exr ..."""
import sys,os,cv2,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","puck-lightning","tools"))
from exr_to_slog3 import read_exr, slog3
from view709 import view
ims=[]
for p in sys.argv[2:]:
    c=slog3(read_exr(p))[...,::-1]; im=cv2.resize((view(c)*255).astype(np.uint8),(960,540)); cv2.putText(im,os.path.basename(p),(6,24),0,.7,(0,255,255),2); ims.append(im)
while len(ims)%2: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(sys.argv[1],np.vstack([np.hstack(ims[i:i+2]) for i in range(0,len(ims),2)]))
