# usage: mix.py <source.mp4> <cuts.json> <sfx dir> <music file> <out.wav>
# Voice: one continuous take with natural pauses; breaths/clicks inside pauses are replaced by room tone.
# Music: the user's track from its start, kept low (~16 dB under the voice) and dipped a little more under speech.
# SFX: a few soft transition sounds only.
import sys, json, subprocess, numpy as np
SRC,C,SFX,MUS,OUT=sys.argv[1],json.load(open(sys.argv[2])),sys.argv[3],sys.argv[4],sys.argv[5]
SR=48000
def load(path,ss=None,t=None):
    cmd=['ffmpeg','-v','error']+(['-ss',str(ss)] if ss is not None else [])+(['-t',str(t)] if t else [])+['-i',path,'-ac','2','-ar',str(SR),'-f','f32le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True,check=True).stdout,np.float32).reshape(-1,2).copy()
src=load(SRC)
rt=src[int(C['roomtone'][0]*SR):int(C['roomtone'][1]*SR)]
for a,b in C.get('patches',[]):
    i,j=int(a*SR),int(b*SR); n=j-i; tone=np.resize(rt,(n,2)); f=int(0.012*SR); r=np.linspace(0,1,f)[:,None]
    w=np.ones((n,1)); w[:f]=r; w[-f:]=r[::-1]
    src[i:j]=src[i:j]*(1-w)+tone*w
parts=[]
for a,b in C['segments']:
    seg=src[int(round(a*SR)):int(round(b*SR))].copy(); f=int(0.01*SR); r=np.linspace(0,1,f)[:,None]
    seg[:f]*=r; seg[-f:]*=r[::-1]; parts.append(seg)
voice=np.concatenate(parts); N=len(voice); T=N/SR
mus=load(MUS,0,T+0.1)[:N]; mus=np.pad(mus,((0,N-len(mus)),(0,0)))
env=np.abs(voice).mean(1); k=int(0.15*SR); env=np.convolve(env,np.ones(k)/k,'same')
duck=1-0.37*np.clip(env/0.02,0,1)                  # about -4 dB more under speech
k2=int(0.25*SR); duck=np.convolve(np.pad(duck,(k2,k2),'edge'),np.ones(k2)/k2,'same')[k2:-k2]
fade=np.ones(N); fo=int(0.8*SR); fade[-fo:]=np.linspace(1,0,fo)**1.5; fi=int(0.25*SR); fade[:fi]=np.linspace(0,1,fi)
mix=voice + mus*(10**(-23/20))*(duck*fade)[:,None]
SFXL=C.get('sfx',[])
for name,peak_at,peak_off,gain in SFXL:
    s=load(f'{SFX}/{name}.wav')*10**(gain/20); i=int((peak_at-peak_off)*SR); j=min(N,i+len(s)); mix[i:j]+=s[:j-i]
mix=np.tanh(mix*0.98)/0.98 if np.abs(mix).max()>0.98 else mix
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-','-c:a','pcm_s16le',OUT],input=mix.astype(np.float32).tobytes(),check=True)
print('ok',round(T,3))
