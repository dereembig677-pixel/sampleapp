# usage: make_assets.py <workdir> <assetdir> — stills of the speaker for the "reel" cards, graded differently each
import sys, cv2, numpy as np
W,A=sys.argv[1],sys.argv[2]
def grab(i,x,y,w,h,grade):
    im=cv2.imread(f'{W}/src/{i:04d}.png')[y:y+h,x:x+w].astype(np.float32)
    im=grade(im); cv2.imwrite(f'{A}/'+name,np.clip(im,0,255).astype(np.uint8))
warm=lambda im: im*np.array([0.88,0.98,1.10])+np.array([0,4,12])
cool=lambda im: (im-128)*1.12+128+np.array([10,2,-8])
mono=lambda im: np.repeat(cv2.cvtColor(np.clip(im,0,255).astype(np.uint8),cv2.COLOR_BGR2GRAY)[...,None],3,2).astype(np.float32)*1.02
for name,i,box,g in [('r1.png',30,(260,380,560,760),mono),('r2.png',120,(220,420,640,900),warm),('r3.png',150,(300,330,480,620),cool),('r4.png',190,(240,400,600,820),warm)]:
    grab(i,*box,g)
print('ok')
