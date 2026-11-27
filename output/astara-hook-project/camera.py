# Virtual camera: eased zoom keyframes + face tracking -> cam.json (per frame crop + face position on screen)
import json, numpy as np
FPS=30; tr=json.load(open('track.json')); N=len(tr)
# (time, zoom, face target y on screen) — all transitions cubic ease-in-out
K=[(0.00,1.12,900),(1.70,1.20,900),(2.05,1.10,930),(2.80,1.12,930),(3.35,1.16,1060),(3.85,1.22,1090),(4.87,1.27,1090)]
eio=lambda p:4*p**3 if p<.5 else 1-(-2*p+2)**3/2
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
