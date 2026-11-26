# Refine coarse u2net masks with a colour-difference key against an inpainted clean plate.
import sys, os, cv2, numpy as np
W=sys.argv[1]; os.makedirs(W+'/mask',exist_ok=True)
files=sorted(os.listdir(W+'/mask_u'))
# clean plate: inpaint the dilated union of all masks on a median frame
union=None; stack=[]
for f in files[::10]:
    m=cv2.imread(W+'/mask_u/'+f,0); union=m if union is None else np.maximum(union,m)
    stack.append(cv2.imread(W+'/src/'+f))
med=np.median(np.stack(stack),0).astype(np.uint8)
hole=cv2.dilate((union>20).astype(np.uint8)*255,np.ones((41,41),np.uint8))
small=cv2.resize(med,None,fx=0.25,fy=0.25); hs=cv2.resize(hole,None,fx=0.25,fy=0.25)
plate=cv2.resize(cv2.inpaint(small,hs,15,cv2.INPAINT_TELEA),(med.shape[1],med.shape[0]))
plate=cv2.GaussianBlur(plate,(0,0),9); cv2.imwrite(W+'/plate.png',plate)
lab_p=cv2.cvtColor(plate,cv2.COLOR_BGR2LAB).astype(np.float32)
for f in files:
    im=cv2.imread(W+'/src/'+f); mu=cv2.imread(W+'/mask_u/'+f,0).astype(np.float32)/255
    lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)
    d=np.sqrt(((lab-lab_p)**2*np.array([1.0,2.0,2.0])).sum(2))
    key=np.clip((d-6)/(26-6),0,1)
    band=cv2.dilate((mu>0.1).astype(np.uint8),np.ones((25,25),np.uint8)).astype(np.float32)
    core=cv2.erode((mu>0.6).astype(np.uint8),np.ones((15,15),np.uint8)).astype(np.float32)
    a=np.maximum(core, key*band)
    a=cv2.GaussianBlur(a,(0,0),0.8)
    cv2.imwrite(W+'/mask/'+f,(np.clip(a,0,1)*255).astype(np.uint8))
print('ok',len(files))
