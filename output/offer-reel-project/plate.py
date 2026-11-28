# usage: plate.py <workdir> — clean background plate (speaker inpainted out), used to unmix wall colour from hair edges
import sys, os, cv2, numpy as np
W=sys.argv[1]; fs=sorted(os.listdir(W+'/mask'))
union=None; stack=[]
for f in fs[::3]:
    m=cv2.imread(W+'/mask/'+f,0); union=m if union is None else np.maximum(union,m); stack.append(cv2.imread(W+'/src/'+f))
med=np.median(np.stack(stack),0).astype(np.uint8)
hole=cv2.dilate((union>10).astype(np.uint8)*255,np.ones((51,51),np.uint8))
small=cv2.resize(med,None,fx=0.25,fy=0.25); hs=cv2.resize(hole,None,fx=0.25,fy=0.25)
plate=cv2.resize(cv2.inpaint(small,hs,20,cv2.INPAINT_TELEA),(med.shape[1],med.shape[0]),interpolation=cv2.INTER_CUBIC)
cv2.imwrite(W+'/plate.png',cv2.GaussianBlur(plate,(0,0),12)); print('ok',len(stack))
