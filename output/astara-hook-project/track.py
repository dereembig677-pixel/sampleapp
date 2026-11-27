# Face tracking (OpenCV Haar, constrained to the matte's head region) -> smoothed track.json
import cv2, numpy as np, json, os
fc=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
N=len(os.listdir('w/src')); raw=[]
for i in range(N):
    im=cv2.imread(f'w/src/{i+1:05d}.png'); m=cv2.imread(f'w/matte/{i+1:05d}.png',0)
    ys,xs=np.where(m>128); top=ys.min(); bx=np.median(xs[ys<top+80]) if len(xs) else 540
    g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY); fs=fc.detectMultiScale(g,1.1,5,minSize=(60,60))
    best=None
    for (x,y,w,h) in fs:
        cx,cy=x+w/2,y+h/2
        if abs(cx-bx)<150 and top-40<y<top+250: best=(cx,cy,w)
    raw.append({'top':int(top),'bx':float(bx),'face':best,'bottom':int(ys.max())})
# fill gaps: face center from detections, fallback head-top + offset
fx=np.array([r['face'][0] if r['face'] else np.nan for r in raw]); fy=np.array([r['face'][1] if r['face'] else np.nan for r in raw]); fw=np.array([r['face'][2] if r['face'] else np.nan for r in raw])
print('detected',np.sum(~np.isnan(fx)),'/',N)
idx=np.arange(N)
def fill(a,fb):
    ok=~np.isnan(a)
    return np.interp(idx,idx[ok],a[ok]) if ok.sum()>3 else fb
fx=fill(fx,np.array([r['bx'] for r in raw])); fw=fill(fw,np.full(N,150.)); fy=fill(fy,np.array([r['top']+90. for r in raw]))
def smooth(a,s=6):
    k=np.exp(-0.5*(np.arange(-3*s,3*s+1)/s)**2);k/=k.sum();p=np.pad(a,3*s,mode='edge');return np.convolve(p,k,'valid')
out=[{'x':round(float(a),1),'y':round(float(b),1),'w':round(float(c),1),'top':r['top'],'bottom':r['bottom']} for a,b,c,r in zip(smooth(fx),smooth(fy),smooth(fw,8),raw)]
json.dump(out,open('track.json','w'))
for i in range(0,N,15):print(i,out[i])
