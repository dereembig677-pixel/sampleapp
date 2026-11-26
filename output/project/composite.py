# usage: composite.py <raw dir> <gfx dir> <out dir> <fps> <nframes> [list]
import sys, os, cv2, numpy as np
R,G,O,FPS,N=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5])
frames=[int(x) for x in sys.argv[6].split(',')] if len(sys.argv)>6 else range(N)
os.makedirs(O,exist_ok=True); W,H=1080,1920; AX,AY=540,1215
plate=cv2.imread(R+'/plate.png').astype(np.float32)
clamp=lambda x,a=0,b=1:max(a,min(b,x)); lin=lambda t,a,b:clamp((t-a)/(b-a))
eOut=lambda p:1-(1-p)**3; eIO=lambda p:4*p**3 if p<.5 else 1-(-2*p+2)**3/2; eIn=lambda p:p**3
# camera keyframes: (time, scale, target Y of subject anchor)
K=[(0.0,1.0,1215),(0.14,1.30,1044),(1.15,1.30,1044),(1.45,1.12,1180),(2.95,1.12,1180),(3.15,1.27,1060),(4.90,1.31,1040),
   (7.36,1.30,1044),(8.42,1.30,1044),(8.72,1.16,1150),(9.5,1.17,1145)]
def cam(t):
    for (t0,s0,y0),(t1,s1,y1) in zip(K,K[1:]):
        if t0<=t<=t1:
            p=eIO((t-t0)/(t1-t0)) if t1-t0<0.5 else (t-t0)/(t1-t0)
            return s0+(s1-s0)*p, y0+(y1-y0)*p
    return K[-1][1],K[-1][2]
def warp(img,s,Y,interp=cv2.INTER_LINEAR):
    M=np.float32([[s,0,AX-AX*s+0],[0,s,Y-AY*s]]); M[0,2]=540-AX*s
    return cv2.warpAffine(img,M,(W,H),flags=interp,borderMode=cv2.BORDER_REPLICATE)
def over(dst,png):
    a=png[...,3:4].astype(np.float32)/255; return dst*(1-a)+png[...,:3].astype(np.float32)*a
def zoomblur(img,amt,k=7,c=(540,1000)):
    acc=np.zeros_like(img)
    for i in range(k):
        s=1+amt*i/(k-1); M=np.float32([[s,0,c[0]-c[0]*s],[0,s,c[1]-c[1]*s]]); acc+=cv2.warpAffine(img,M,(W,H),borderMode=cv2.BORDER_REPLICATE)
    return acc/k
for n in frames:
    t=n/FPS; si=min(int(t*24+1e-6),229); f='%04d.png'%(si+1)
    s,Y=cam(t)
    src=cv2.imread(R+'/src/'+f).astype(np.float32); m=cv2.imread(R+'/mask/'+f,0).astype(np.float32)/255
    base=warp(src,s,Y); a=warp(m,s,Y)[...,None]; pl=warp(plate,s,Y)
    # colour decontamination of the subject edge
    fg=np.clip((base-(1-a)*pl)/np.maximum(a,0.08),0,255)
    back=cv2.imread(f'{G}/back/{n:04d}.png',cv2.IMREAD_UNCHANGED); front=cv2.imread(f'{G}/front/{n:04d}.png',cv2.IMREAD_UNCHANGED)
    comp=over(base,back)
    comp=comp*(1-a)+fg*a
    comp=over(comp,front)
    # post effects
    zb=max(0,1-abs(t-3.04)/0.12)*0.10 + max(0,1-abs(t-1.28)/0.14)*0.05
    if zb>0.004: comp=zoomblur(comp,zb)
    bl=eIn(lin(t,4.62,4.89)) if t<4.90 else 0
    if bl>0: glow=cv2.GaussianBlur(comp,(0,0),25); comp=comp*(1-bl)+(255*0.85+glow*0.15)*bl
    g=max(lin(t,7.20,7.30)*8 if 7.20<=t<7.37 else 0, (1-lin(t,7.37,7.50))*8 if t>=7.37 else 0, (1-lin(t,0,0.12))*6)
    if g>0.3: comp=cv2.GaussianBlur(comp,(0,0),g)
    if 7.29<=t<7.37:
        inv=255-cv2.GaussianBlur(comp,(0,0),12); comp=inv*0.55; comp[...,0]*=1.25
    cv2.imwrite(f'{O}/{n:04d}.png',np.clip(comp,0,255).astype(np.uint8))
print('ok')
