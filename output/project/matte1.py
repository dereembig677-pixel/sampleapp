import sys, os, time, numpy as np, onnxruntime as ort
from rembg import new_session, remove
from PIL import Image
W,model,outd,n=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]); os.makedirs(W+'/'+outd,exist_ok=True)
so=ort.SessionOptions(); so.enable_cpu_mem_arena=False; so.enable_mem_pattern=False
s=new_session(model,sess_opts=so)
files=sorted(os.listdir(W+'/src'))[:n]; t0=time.time()
for i,f in enumerate(files):
    out=W+'/'+outd+'/'+f
    if os.path.exists(out): continue
    remove(Image.open(W+'/src/'+f),session=s,only_mask=True).save(out)
    if i%10==0: print(model,i,round(time.time()-t0),flush=True)
print('done',model,round(time.time()-t0))
