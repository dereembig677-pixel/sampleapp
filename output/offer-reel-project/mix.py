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
ru=C.get('raw_voice_until')
if ru:   # RAW opening: thin phone-mic sound with a little room echo and hiss, switching to the clean voice at the snap
    n=int((ru+0.05)*SR); seg=voice[:n].copy(); F=np.fft.rfft(seg,axis=0); f=np.fft.rfftfreq(n,1/SR)
    g=np.clip((f-250)/150,0,1)*np.clip((3800-f)/800,0,1); g=g*(1+0.6*np.exp(-((f-1500)/500)**2)); seg=np.fft.irfft(F*g[:,None],n,axis=0)
    for d,a_ in [(0.031,0.35),(0.067,0.22),(0.113,0.12)]:
        k=int(d*SR); seg[k:]+=seg[:-k]*a_
    seg+=np.random.default_rng(3).normal(0,0.0016,seg.shape); seg*=0.75
    x=np.ones((n,1)); cf=int(0.03*SR); x[n-cf-int(0.05*SR):n-int(0.05*SR)]=np.linspace(1,0,cf)[:,None]; x[n-int(0.05*SR):]=0
    voice[:n]=seg*x+voice[:n]*(1-x)
mus=load(MUS,0,T+0.1)[:N]; mus=np.pad(mus,((0,N-len(mus)),(0,0)))
env=np.abs(voice).mean(1); k=int(0.15*SR); env=np.convolve(env,np.ones(k)/k,'same')
duck=1-0.37*np.clip(env/0.02,0,1)                  # about -4 dB more under speech
k2=int(0.25*SR); duck=np.convolve(np.pad(duck,(k2,k2),'edge'),np.ones(k2)/k2,'same')[k2:-k2]
fade=np.ones(N); fo=int(0.8*SR); fade[-fo:]=np.linspace(1,0,fo)**1.5; fi=int(0.25*SR); fade[:fi]=np.linspace(0,1,fi)
tt=np.arange(N)/SR; bump=np.ones(N)
for tc in C.get('music_swells',[]): bump+=0.55*np.exp(-((tt-tc)/0.28)**2)   # music lifts ~+4 dB around each transition
for a0,a1,gdb in C.get('music_lift',[]):   # music carries the moments with no voice (the before/after)
    w=np.clip((tt-a0)/0.25,0,1)*np.clip((a1-tt)/0.25,0,1); bump*=1+(10**(gdb/20)-1)*w
mix=voice + mus*(10**(-22/20))*(duck*fade*bump)[:,None]
SFXL=C.get('sfx',[])
def st_rms(x,win=int(0.1*SR)):   # loudest 100 ms RMS - a short-term loudness estimate, used to match effects by how loud they feel
    m=x.mean(1)**2; c=np.convolve(m,np.ones(win)/win,'valid'); return np.sqrt(c.max()+1e-12)
VREF=st_rms(voice)
sduck=1-0.5*np.clip(env/0.02,0,1)                 # effects dip ~6 dB while the speaker talks
k3=int(0.06*SR); sduck=np.convolve(np.pad(sduck,(k3,k3),'edge'),np.ones(k3)/k3,'same')[k3:-k3]
bus=np.zeros_like(mix)
for e in SFXL:   # [file, peak time in video, peak offset inside the (trimmed) clip, level dB relative to the voice's loudest moment, start in file, length]
    name,peak_at,peak_off,rel=e[:4]; ss=e[4] if len(e)>4 else 0; du=e[5] if len(e)>5 else None
    s=load(f'{SFX}/{name}' if '.' in name else f'{SFX}/{name}.wav',ss if ss else None,du)
    if du: f=min(len(s),int(0.08*SR)); s[-f:]*=np.linspace(1,0,f)[:,None]
    f=min(len(s),int(0.004*SR)); s[:f]*=np.linspace(0,1,f)[:,None]
    s=s*(VREF*10**(rel/20)/st_rms(s)); i=int((peak_at-peak_off)*SR)
    if i<0: s=s[-i:]; i=0
    j=min(N,i+len(s)); bus[i:j]+=s[:j-i]
mix+=bus*sduck[:,None]
mix=np.tanh(mix*0.98)/0.98 if np.abs(mix).max()>0.98 else mix
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-','-c:a','pcm_s16le',OUT],input=mix.astype(np.float32).tobytes(),check=True)
print('ok',round(T,3))
