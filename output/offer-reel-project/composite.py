# usage: composite.py <workdir> <gfx dir> <out dir> <cuts.json> <worker> <nworkers> [frame,frame,...]
# workdir holds src/NNNN.png (1080x1920 upscaled source frames, 24 fps) and mask/NNNN.png (BiRefNet mattes).
import sys, os, json, cv2, numpy as np
WD,G,O,C,K,NW=sys.argv[1],sys.argv[2],sys.argv[3],json.load(open(sys.argv[4])),int(sys.argv[5]),int(sys.argv[6])
os.makedirs(O,exist_ok=True); W,H=1080,1920; FPS=30
SEG=C['segments']; starts=np.cumsum([0]+[b-a for a,b in SEG]); TOTAL=starts[-1]; N=int(round(TOTAL*FPS))
FX,FY=540,600   # focus point in the source (the speaker's face)
clamp=lambda x,a=0,b=1:max(a,min(b,x)); lin=lambda t,a,b:clamp((t-a)/(b-a))
eOut=lambda p:1-2**(-10*p) if p<1 else 1; eIO=lambda p:4*p**3 if p<.5 else 1-(-2*p+2)**3/2; eIn=lambda p:p**3

def src_index(t):
    i=int(np.searchsorted(starts,t,side='right')-1); i=min(i,len(SEG)-1)
    st=SEG[i][0]+(t-starts[i]); return i,min(int(round(st*24)),239)

# camera per segment: scale and where the face lands vertically; alternate tight/wide so the jump cuts read as intentional punch-ins
def cam(t,i):
    # returns scale and the output y of the focus point; ht = where the top of the head lands (source head top is y~515),
    # chosen so the head covers only the bottom quarter of each keyword, as in the reference
    lt=t-starts[i]; d=starts[i+1]-starts[i]
    if i==0:   # opening punch-in from wide, then a slow creep
        p=eOut(lin(lt,0,0.30)); s=1.04+0.20*p+0.03*lin(lt,0.3,d); ht=575-55*p
    elif i==1: s=1.04+0.03*lin(lt,0,d); ht=490
    elif i==2: s=1.30+0.03*lin(lt,0,d); ht=510
    elif i==3: s=1.12+0.025*lin(lt,0,d); ht=525
    else:
        p=eIO(lin(lt,0,d)); s=1.05+0.08*p; ht=505
    return s, ht+(FY-515)*s
def M(s,y): return np.float32([[s,0,540-FX*s],[0,s,y-FY*s]])
def warp(img,m,interp=cv2.INTER_CUBIC): return cv2.warpAffine(img,m,(W,H),flags=interp,borderMode=cv2.BORDER_REPLICATE)
def over(dst,png):
    png=cv2.GaussianBlur(png,(0,0),0.55)   # soften the vector graphics to the footage's sharpness
    a=png[...,3:4].astype(np.float32)/255; return dst*(1-a)+png[...,:3].astype(np.float32)*a
def zoomblur(img,amt,k=8,c=(540,800)):
    acc=np.zeros_like(img)
    for j in range(k):
        s=1+amt*j/(k-1); m=np.float32([[s,0,c[0]-c[0]*s],[0,s,c[1]-c[1]*s]]); acc+=cv2.warpAffine(img,m,(W,H),borderMode=cv2.BORDER_REPLICATE)
    return acc/k

plate=cv2.imread(WD+'/plate.png').astype(np.float32)
rng=np.random.default_rng(7)
for n in ([int(x) for x in sys.argv[7].split(',')] if len(sys.argv)>7 else range(K,N,NW)):
    t=n/FPS; i,si=src_index(t); s,y=cam(t,i); m=M(s,y)
    if os.path.exists(f'{O}/{n:04d}.png') or not os.path.exists(f'{WD}/mask/{si:04d}.png'): continue   # resumable; waits for the matte
    src=cv2.imread(f'{WD}/src/{si:04d}.png').astype(np.float32); a=cv2.imread(f'{WD}/mask/{si:04d}.png',0).astype(np.float32)/255
    base=warp(src,m); al=warp(a,m,cv2.INTER_LINEAR)[...,None]; pl=warp(plate,m)
    fg=np.clip((base-(1-al)*pl)/np.maximum(al,0.06),0,255)   # remove grey wall spill from hair edges
    back=cv2.imread(f'{G}/back/{n:04d}.png',cv2.IMREAD_UNCHANGED); front=cv2.imread(f'{G}/front/{n:04d}.png',cv2.IMREAD_UNCHANGED)
    comp=over(base,back); comp=comp*(1-al)+fg*al; comp=over(comp,front)
    # transitions
    zb=max(0,1-abs(t-1.40)/0.13)*0.09 + max(0,1-abs(t-2.58)/0.12)*0.07
    if zb>0.004: comp=zoomblur(comp,zb)
    if 4.66<=t<4.86:   # bloom to white into the last beat
        bl=eIn(lin(t,4.66,4.86)); glow=cv2.GaussianBlur(comp,(0,0),25); comp=comp*(1-bl)+(255*0.88+glow*0.12)*bl
    if 4.86<=t<5.16:
        wf=eIn(1-lin(t,4.86,5.16)); comp=comp*(1-wf)+255*wf
    g=(1-lin(t,0,0.13))*6
    if g>0.3: comp=cv2.GaussianBlur(comp,(0,0),g)
    if 3.98<=t<4.04:   # two-frame inverted glitch on the hard cut
        inv=255-cv2.GaussianBlur(comp,(0,0),10); comp=comp*0.35+inv*0.65*np.array([1.0,0.92,1.15])
    # fine luma grain so graphics and footage sit in one image
    comp+=rng.normal(0,2.2,(H,W,1)).astype(np.float32)
    cv2.imwrite(f'{O}/{n:04d}.png',np.clip(comp,0,255).astype(np.uint8))
print('ok',K,N)
