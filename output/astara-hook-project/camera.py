# Virtual camera: eased zoom keyframes + face tracking -> cam.json (per frame crop + face position on screen)
import json, numpy as np
FPS=30; tr=json.load(open('track.json')); N=len(tr)
# (time, zoom, face target y on screen) — all transitions cubic ease-in-out
K=[(0.00,1.04,900),(1.65,1.16,900),(2.25,1.03,930),(2.95,1.08,930),(3.55,1.25,1010),(4.87,1.30,1010)]   # push in / ease out to reveal Astara / slow push / punch-in under the card
eio=lambda p:16*p**5 if p<.5 else 1-(-2*p+2)**5/2
def key(t,i):
    for a,b in zip(K,K[1:]):
        if t<=b[0]:p=eio(min(1,max(0,(t-a[0])/(b[0]-a[0]))));return a[i]+(b[i]-a[i])*p
    return K[-1][i]
out=[]
for f in range(N):
    t=f/FPS; s=key(t,1); ty=key(t,2); fx,fy,fw=tr[f]['x'],tr[f]['y'],tr[f]['w']
    cx=540+(fx-540)*0.85            # follow the face horizontally (85 %), keeps a little natural sway
    cy=fy-(ty-960)/s
    cx=min(max(cx,540/s),1080-540/s); cy=min(max(cy,960/s),1920-960/s)
    sx=(fx-cx)*s+540; sy=(fy-cy)*s+960
    out.append({'t':t,'s':s,'cx':cx,'cy':cy,'fx':sx,'fy':sy,'fw':fw*s,'head':sy-fw*s*0.95})
json.dump(out,open('cam.json','w'))
for o in out[::20]:print({k:round(v,1) for k,v in o.items()})
