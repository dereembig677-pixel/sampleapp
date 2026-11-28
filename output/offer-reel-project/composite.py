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
BEATS=[0.0,1.62,3.20,4.88,6.02,99]   # framing changes happen inside the speaker's pauses (one continuous take)
def cam(t,i):
    # returns scale and the output y of the focus point; ht = where the top of the head lands (source head top is y~515),
    # chosen so the head covers only the bottom quarter of each keyword
    b=int(np.searchsorted(BEATS,t,side='right')-1); lt=t-BEATS[b]; d=min(BEATS[b+1],TOTAL)-BEATS[b]
    if b==0:   # hook: opens tight and pulls back fast, then a slow creep
        p=eOut(lin(lt,0,0.34)); s=1.46-0.22*p+0.03*lin(lt,0.34,d); ht=520
    elif b==1: s=1.04+0.03*lin(lt,0,d); ht=490
    elif b==2: s=1.30+0.03*lin(lt,0,d); ht=530
    elif b==3: s=1.12+0.025*lin(lt,0,d); ht=525
    else:
        p=eIO(lin(lt,0,d)); s=1.05+0.08*p; ht=525
    return s, ht+(FY-515)*s
def M(s,y): return np.float32([[s,0,540-FX*s],[0,s,y-FY*s]])
def warp(img,m,interp=cv2.INTER_CUBIC): return cv2.warpAffine(img,m,(W,H),flags=interp,borderMode=cv2.BORDER_REPLICATE)
def over(dst,png):
    png=cv2.GaussianBlur(png,(0,0),0.55)   # soften the vector graphics to the footage's sharpness
    a=png[...,3:4].astype(np.float32)/255; return dst*(1-a)+png[...,:3].astype(np.float32)*a
# ---- proof beat (1.62-3.20): full-screen split, the user's raw sample vs their edit of it
SPLIT=(1.62,3.20); CW,CH=400,711
def rounded(w,h,r):
    m=np.zeros((h*4,w*4),np.uint8); cv2.rectangle(m,(r*4,0),(w*4-r*4,h*4),255,-1); cv2.rectangle(m,(0,r*4),(w*4,h*4-r*4),255,-1)
    for cx,cy in [(r,r),(w-r,r),(r,h-r),(w-r,h-r)]: cv2.circle(m,(cx*4,cy*4),r*4,255,-1)
    return cv2.resize(m,(w,h),interpolation=cv2.INTER_AREA).astype(np.float32)/255   # anti-aliased
def make_card(img,stroke):
    # returns an RGBA card (video inside a white frame with a coloured outer stroke) plus its drop-shadow alpha
    pad=40; sw=6; fw=12; cw,ch=CW+2*fw+2*sw,CH+2*fw+2*sw
    outer=rounded(cw,ch,34); white=np.pad(rounded(cw-2*sw,ch-2*sw,30),sw); vid=np.pad(rounded(CW,CH,22),fw+sw)
    rgb=np.zeros((ch,cw,3),np.float32); rgb[:]=stroke
    rgb=rgb*(1-white[...,None])+255*white[...,None]
    big=np.zeros((ch,cw,3),np.float32); big[fw+sw:fw+sw+CH,fw+sw:fw+sw+CW]=img
    rgb=rgb*(1-vid[...,None])+big*vid[...,None]
    card=np.zeros((ch+2*pad,cw+2*pad,4),np.float32); card[pad:pad+ch,pad:pad+cw,:3]=rgb; card[pad:pad+ch,pad:pad+cw,3]=outer
    shadow=np.roll(cv2.GaussianBlur(np.pad(outer,pad),(0,0),16),14,0)*0.30
    return card,shadow
CARDS={}
def place(dst,cs,cx,cy,rot,mblur):
    card,shadow=cs; h,w=card.shape[:2]; M2=cv2.getRotationMatrix2D((w/2,h/2),rot,1.0); M2[0,2]+=cx-w/2; M2[1,2]+=cy-h/2
    c=cv2.warpAffine(card,M2,(W,H),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0)); sh=cv2.warpAffine(shadow,M2,(W,H),flags=cv2.INTER_LINEAR)
    if mblur>1: k=int(mblur)|1; c=cv2.blur(c,(k,1)); sh=cv2.blur(sh,(k,1))
    dst=dst*(1-sh[...,None])+np.array([40,20,70],np.float32)*sh[...,None]
    a=c[...,3:4]; return dst*(1-a)+c[...,:3]*a
def split_bg():
    yy=np.linspace(0,1,H)[:,None,None]; bg=np.ones((H,W,3),np.float32)*np.array([233,234,236],np.float32)-yy*np.array([14,14,13],np.float32)
    xx=np.linspace(-1,1,W)[None,:,None]; return bg-8*(xx**2)
SPLIT_BG=split_bg()
def split_frame(t):
    lt=t-SPLIT[0]; k=min(int(lt*30),50)
    b=cv2.imread(f'{WD}/before/{k:03d}.png'); a=cv2.imread(f'{WD}/after/{k:03d}.png')
    comp=SPLIT_BG.copy()
    for img,stroke,x1,t0,rot,frm in [(b,(90,86,92),260,0.0,-3,-1),(a,(43,38,227),700,0.07,3,1)]:
        p=lin(lt,t0,t0+0.34); e=eOut(p); x=x1+frm*(1-e)*760; v=frm*760*(10*2**(-10*p))*np.log(2)/0.34/30 if p<1 else 0
        comp=place(comp,make_card(img.astype(np.float32),stroke),x,1046,rot*e,abs(v)*0.5)
    return comp

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
    back=cv2.imread(f'{G}/back/{n:04d}.png',cv2.IMREAD_UNCHANGED); front=cv2.imread(f'{G}/front/{n:04d}.png',cv2.IMREAD_UNCHANGED)
    if SPLIT[0]<=t<SPLIT[1]:   # proof beat: no speaker on screen, his voice continues over it
        comp=over(over(split_frame(t),back),front)
    else:
        src=cv2.imread(f'{WD}/src/{si:04d}.png').astype(np.float32); a=cv2.imread(f'{WD}/mask/{si:04d}.png',0).astype(np.float32)/255
        base=warp(src,m); al=warp(a,m,cv2.INTER_LINEAR)[...,None]; pl=warp(plate,m)
        fg=np.clip((base-(1-al)*pl)/np.maximum(al,0.06),0,255)   # remove grey wall spill from hair edges
        comp=over(base,back); comp=comp*(1-al)+fg*al; comp=over(comp,front)
    # transitions
    zb=max(0,1-abs(t-1.62)/0.13)*0.08 + max(0,1-abs(t-3.20)/0.12)*0.06
    if zb>0.004: comp=zoomblur(comp,zb)
    if 5.84<=t<6.02:   # bloom to white into the last beat
        bl=eIn(lin(t,5.84,6.02)); glow=cv2.GaussianBlur(comp,(0,0),25); comp=comp*(1-bl)+(255*0.88+glow*0.12)*bl
    if 6.02<=t<6.32:
        wf=eIn(1-lin(t,6.02,6.32)); comp=comp*(1-wf)+255*wf
    # fine luma grain so graphics and footage sit in one image
    comp+=rng.normal(0,2.2,(H,W,1)).astype(np.float32)
    cv2.imwrite(f'{O}/{n:04d}.png',np.clip(comp,0,255).astype(np.uint8))
print('ok',K,N)
