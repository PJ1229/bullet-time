import os, sys, cv2, numpy as np
from multiprocessing import Pool
G = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, G + "/puck-lightning/tools")
LINK, OUT = os.path.expanduser(sys.argv[1]), os.path.expanduser(sys.argv[2]); a, b = int(sys.argv[3]), int(sys.argv[4])
os.makedirs(OUT, exist_ok=True)
def job(t):
    import view709
    x = cv2.imread(f"{LINK}/m_{t:04d}.png", -1).astype(np.float32) / 65535
    im = (view709.view(x) * 255).clip(0, 255).astype(np.uint8)
    cv2.imwrite(f"{OUT}/p_{t:04d}.jpg", cv2.resize(im, (1280, 720), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 93])
if __name__ == "__main__":
    with Pool(6) as p: p.map(job, range(a, b + 1))
    print("ok", a, b)
