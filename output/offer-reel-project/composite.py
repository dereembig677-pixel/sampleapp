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
BEATS=[0.0,0.75,1.45,3.40,4.88,6.02,8.30,99]   # framing changes happen inside the speaker's pauses (one continuous take)
def cam(t,i):
    # returns scale and the output y of the focus point; ht = where the top of the head lands (source head top is y~515),
    # chosen so the head covers only the bottom quarter of each keyword
    b=int(np.searchsorted(BEATS,t,side='right')-1); lt=t-BEATS[b]; d=min(BEATS[b+1],TOTAL)-BEATS[b]
    if b==0:   s=1.1513; ht=441.7               # RAW wide frame, pre-scaled by the source's own slow zoom (measured 1.151x by frame 220) so the last frame loops into the first
    elif b==1:   # snap into the edit on "views": tight, fast pull-back
        p=eOut(lin(lt,0,0.30)); s=1.42-0.18*p+0.02*lin(lt,0.3,d); ht=520
    elif b==2: s=1.04; ht=490                   # proof beat (speaker not on screen)
    elif b==3: s=1.30+0.03*lin(lt,0,d); ht=530
    elif b==4: s=1.12+0.025*lin(lt,0,d); ht=525
    elif b==5: p=eIO(lin(lt,0,d)); s=1.05+0.08*p; ht=525
    else:      p=eIO(lin(lt,0,0.30)); s=1.13-0.13*p; ht=525-10*p   # loop: back to the RAW framing of frame 0
    return s, ht+(FY-515)*s
def M(s,y): return np.float32([[s,0,540-FX*s],[0,s,y-FY*s]])
def warp(img,m,interp=cv2.INTER_CUBIC): return cv2.warpAffine(img,m,(W,H),flags=interp,borderMode=cv2.BORDER_REPLICATE)
def over(dst,png):
    png=cv2.GaussianBlur(png,(0,0),0.55)   # soften the vector graphics to the footage's sharpness
    a=png[...,3:4].astype(np.float32)/255; return dst*(1-a)+png[...,:3].astype(np.float32)*a
# ---- proof beat (1.45-3.40): full screen, the editor's raw sample wipes into their edit of it
PROOF=(1.45,3.40)
def proof_frame(t):
    lt=t-PROOF[0]; k=min(int(lt*30),62)
    b=cv2.imread(f'{WD}/beforeF/{k:03d}.png').astype(np.float32); a=cv2.imread(f'{WD}/afterF/{k:03d}.png').astype(np.float32)
    wx=W*eIO(lin(t,1.90,2.40)); xs=np.arange(W,dtype=np.float32)[None,:,None]
    m=np.clip((wx-xs)/6+0.5,0,1)   # left of the wipe edge shows the edit
    comp=b*(1-m)+a*m
    if 0<wx<W:   # glowing red edge
        g=np.exp(-((xs-wx)/14)**2); c=np.exp(-((xs-wx)/3)**2)
        comp=comp*(1-0.85*g)+np.array([40,30,225],np.float32)*0.85*g; comp=comp*(1-c)+255*c
    z=1+0.05*lin(t,PROOF[0],PROOF[1]); M2=np.float32([[z,0,540-540*z],[0,z,960-960*z]])
    return cv2.warpAffine(comp,M2,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
def raw_grade(img,k):   # flat, slightly desaturated "camera original" look
    if k<=0: return img
    g=img.mean(2,keepdims=True); r=(img*0.68+g*0.32)*0.88+20
    return img*(1-k)+r*k

def zoomblur(img,amt,k=8,c=(540,800)):
    acc=np.zeros_like(img)
    for j in range(k):
        s=1+amt*j/(k-1); m=np.float32([[s,0,c[0]-c[0]*s],[0,s,c[1]-c[1]*s]]); acc+=cv2.warpAffine(img,m,(W,H),borderMode=cv2.BORDER_REPLICATE)
    return acc/k

plate=cv2.imread(WD+'/plate.png').astype(np.float32)
rng=np.random.default_rng(7)
for n in ([int(x) for x in sys.argv[7].split(',')] if len(sys.argv)>7 else range(K,N,NW)):
    t=n/FPS; i,si=src_index(t); s,y=cam(t,i); m=M(s,y)
    if t<0.75: m[0,2]+=12.8   # horizontal part of the measured drift
    if os.path.exists(f'{O}/{n:04d}.png') or not os.path.exists(f'{WD}/mask/{si:04d}.png'): continue   # resumable; waits for the matte
    back=cv2.imread(f'{G}/back/{n:04d}.png',cv2.IMREAD_UNCHANGED); front=cv2.imread(f'{G}/front/{n:04d}.png',cv2.IMREAD_UNCHANGED)
    if PROOF[0]<=t<PROOF[1]:   # proof beat: no speaker on screen, his voice continues over it
        comp=over(over(proof_frame(t),back),front)
    else:
        src=cv2.imread(f'{WD}/src/{si:04d}.png').astype(np.float32); a=cv2.imread(f'{WD}/mask/{si:04d}.png',0).astype(np.float32)/255
        base=warp(src,m); al=warp(a,m,cv2.INTER_LINEAR)[...,None]; pl=warp(plate,m)
        fg=np.clip((base-(1-al)*pl)/np.maximum(al,0.06),0,255)   # remove grey wall spill from hair edges
        rk=1.0 if t<0.75 else lin(t,8.32,8.56)
        base=raw_grade(base,rk); fg=raw_grade(fg,rk)
        comp=over(base,back); comp=comp*(1-al)+fg*al; comp=over(comp,front)
    # transitions
    zb=max(0,1-abs(t-0.75)/0.10)*0.07 + max(0,1-abs(t-1.45)/0.13)*0.08 + max(0,1-abs(t-3.40)/0.12)*0.06
    if zb>0.004: comp=zoomblur(comp,zb)
    if 5.84<=t<6.02:   # bloom to white into the last beat
        bl=eIn(lin(t,5.84,6.02)); glow=cv2.GaussianBlur(comp,(0,0),25); comp=comp*(1-bl)+(255*0.88+glow*0.12)*bl
    if 6.02<=t<6.32:
        wf=eIn(1-lin(t,6.02,6.32)); comp=comp*(1-wf)+255*wf
    if 0.75<=t<0.85: comp=comp*(1-0.55*(1-lin(t,0.75,0.85)))+255*0.55*(1-lin(t,0.75,0.85))   # snap flash
    # fine luma grain so graphics and footage sit in one image
    comp+=rng.normal(0,2.2,(H,W,1)).astype(np.float32)
    cv2.imwrite(f'{O}/{n:04d}.png',np.clip(comp,0,255).astype(np.uint8))
print('ok',K,N)
