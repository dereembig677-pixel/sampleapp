# BiRefNet-portrait matte for the frames where the speaker is cut out over the B-roll (cleaner than u2net there)
import sys,os,numpy as np, onnxruntime as ort
from rembg import new_session, remove
from PIL import Image
a,b,wi,wc=map(int,sys.argv[1:5]);os.makedirs('w/matte2',exist_ok=True);so=ort.SessionOptions();so.enable_cpu_mem_arena=False;so.enable_mem_pattern=False;s=new_session('birefnet-portrait',sess_opts=so)
for f in range(a,b+1):
    if (f-a)%wc!=wi or os.path.exists(f'w/matte2/{f:05d}.png'):continue
    remove(Image.open(f'w/src/{f:05d}.png'),session=s,only_mask=True).save(f'w/matte2/{f:05d}.png');print(f,flush=True)
