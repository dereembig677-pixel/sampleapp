# usage: matte.py <workdir> <cuts.json> <worker> <nworkers>   (BiRefNet-portrait masks for the frames that survive the cuts)
import sys, os, json, time, onnxruntime as ort
from rembg import new_session, remove
from PIL import Image
W,C,k,n=sys.argv[1],json.load(open(sys.argv[2])),int(sys.argv[3]),int(sys.argv[4])
os.makedirs(W+'/mask',exist_ok=True)
fr=sorted({i for a,b in C['segments'] for i in range(int(a*24)-1,int(b*24)+2)})[k::n]
so=ort.SessionOptions(); so.intra_op_num_threads=4; so.enable_cpu_mem_arena=False; so.enable_mem_pattern=False; s=new_session('birefnet-portrait',sess_opts=so); t0=time.time()
for j,i in enumerate(fr):
    out=f'{W}/mask/{i:04d}.png'
    if os.path.exists(out): continue
    remove(Image.open(f'{W}/src/{i:04d}.png'),session=s,only_mask=True).save(out)
    if j%10==0: print(k,j,len(fr),round(time.time()-t0),flush=True)
print('done',k,round(time.time()-t0))
