# Composite: virtual camera (tracked punch-ins) + Astara B-roll behind the speaker (matte) + text layers -> frames on stdout
import cv2, numpy as np, json, os, sys
FPS=30; cam=json.load(open('cam.json')); N=len(cam); W,H=1080,1920
clamp=lambda x,a=0,b=1:max(a,min(b,x)); lin=lambda t,a,b:clamp((t-a)/(b-a))
eio=lambda p:4*p**3 if p<.5 else 1-(-2*p+2)**3/2
# Astara photo: cover 1920 high, crop window chosen so the tower and the sign sit around the speaker
A=cv2.imread('astara.png'); sc=H/A.shape[0]; A=cv2.resize(A,None,fx=sc,fy=sc,interpolation=cv2.INTER_LANCZOS4)
AX0=int(470*sc)
yy=np.linspace(0,1,H)[:,None,None]; GRAD=1-0.16*np.clip(1-yy/0.45,0,1)**1.5     # darken the top (text area) of the background only
IN0,IN1,OUT0,OUT1=1.70,2.30,2.62,3.02                                                  # B-roll reveal / exit
def rgba(p):
    if not os.path.exists(p):return None
    im=cv2.imread(p,cv2.IMREAD_UNCHANGED).astype(np.float32)/255;return im[...,:3],im[...,3:]
def person(m,fx,fy):
    _,lab=cv2.connectedComponents((m>0.5).astype(np.uint8));k=lab[int(fy),int(fx)]
    if k==0:return m
    keep=(lab==k).astype(np.uint8);keep=cv2.dilate(keep,np.ones((7,7),np.uint8))
    return m*keep
out=sys.stdout.buffer
for f in range(N):
    t=f/FPS;c=cam[f];s=c['s']
    M=np.float32([[s,0,540-s*c['cx']],[0,s,960-s*c['cy']]])
    src=cv2.imread(f'w/src/{f+1:05d}.png').astype(np.float32)/255
    fr=cv2.warpAffine(src,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
    mp=f'w/matte2/{f+1:05d}.png';m=cv2.imread(mp if os.path.exists(mp) else f'w/matte/{f+1:05d}.png',0).astype(np.float32)/255
    m=cv2.warpAffine(m,M,(W,H),flags=cv2.INTER_LINEAR)
    m=person(m,c['fx'],c['fy']+c['fw']*1.5);m=cv2.GaussianBlur(m,(0,0),1.6)[...,None]
    bg=fr*GRAD
    # B-roll
    pin=eio(lin(t,IN0,IN1));pout=eio(lin(t,OUT0,OUT1));k=pin*(1-pout)
    if k>0.002:
        z=1.0+0.10*(1-eio(lin(t,IN0,OUT1)))                      # slow push-out while shown, push-through on exit
        Mi=np.float32([[z,0,540-z*(AX0+540)],[0,z,960-z*960]])
        img=cv2.warpAffine(A,Mi,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT).astype(np.float32)/255
        bl=3.0+18*(1-pin)+10*pout                                          # 3 px base = soft depth of field behind him
        if bl>0.5:img=cv2.GaussianBlur(img,(0,0),bl)
        # radial reveal growing out from behind the speaker, feathered edge
        Y,X=np.ogrid[:H,:W];d=np.sqrt((X-c['fx'])**2+(Y-c['fy'])**2)
        R=2300*pin*(1-pout);mask=np.clip((R-d)/300+0.5,0,1)*min(1,pin*3)      # circle opens from behind him, closes back into him
        bg=bg*(1-mask[...,None])+img*GRAD*mask[...,None]
    b=rgba(f'w/back/{f:05d}.png')
    if b:bg=bg*(1-b[1])+b[0]*b[1]
    comp=bg*(1-m)+fr*m
    fl=rgba(f'w/front/{f:05d}.png')
    if fl:comp=comp*(1-fl[1])+fl[0]*fl[1]
    out.write((np.clip(comp,0,1)*255+0.5).astype(np.uint8).tobytes())
    print(f,file=sys.stderr) if f%30==0 else None
