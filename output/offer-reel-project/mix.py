# usage: mix.py <source.mp4> <cuts.json> <sfx dir> <music file> <out.wav>
# Voice: the kept segments joined with short fades (breaths and dead air are in the removed gaps).
# Music: ducked bed, kicks lined up with the cuts. SFX: one per transition.
import sys, json, subprocess, numpy as np
SRC,C,SFX,MUS,OUT=sys.argv[1],json.load(open(sys.argv[2])),sys.argv[3],sys.argv[4],sys.argv[5]
SR=48000
def load(path,ss=None,t=None):
    cmd=['ffmpeg','-v','error']+(['-ss',str(ss)] if ss is not None else [])+(['-t',str(t)] if t else [])+['-i',path,'-ac','2','-ar',str(SR),'-f','f32le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True,check=True).stdout,np.float32).reshape(-1,2).copy()
src=load(SRC)
parts=[]
for a,b in C['segments']:
    seg=src[int(round(a*SR)):int(round(b*SR))].copy(); f=int(0.008*SR); r=np.linspace(0,1,f)[:,None]
    seg[:f]*=r; seg[-f:]*=r[::-1]; parts.append(seg)
voice=np.concatenate(parts); N=len(voice); T=N/SR
# music: start at 30.02 s so the track's kicks fall near the cuts at 1.40 and 2.58
mus=load(MUS,30.02,T+0.1)[:N]; mus=np.pad(mus,((0,N-len(mus)),(0,0)))
env=np.abs(voice).mean(1); k=int(0.12*SR); env=np.convolve(env,np.ones(k)/k,'same')
duck=1-0.45*np.clip(env/0.02,0,1)                  # about -5 dB under speech
k2=int(0.08*SR); duck=np.convolve(duck,np.ones(k2)/k2,'same')
fade=np.ones(N); fo=int(0.5*SR); fade[-fo:]=np.linspace(1,0,fo)**1.5; fi=int(0.06*SR); fade[:fi]=np.linspace(0,1,fi)
mix=voice*1.0 + mus*(10**(-19/20))*(duck*fade)[:,None]
for name,peak_at,peak_off,gain in [('whoosh-cine',0.70,0.17,-14),('whoosh-3',1.40,0.76,-13),('cinematic-deep-boom',1.40,0.19,-14),
                                   ('tech-digital-whoosh',2.58,0.66,-6),('tech-glitch-2',3.98,0.01,-17),('cinematic-film-flash',4.84,0.64,-14),
                                   ('tech-notification-2',5.48,0.06,-13)]:
    s=load(f'{SFX}/{name}.wav')*10**(gain/20); i=int((peak_at-peak_off)*SR); j=min(N,i+len(s)); mix[i:j]+=s[:j-i]
mix=np.tanh(mix*0.98)/0.98 if np.abs(mix).max()>0.98 else mix
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-','-c:a','pcm_s16le',OUT],input=mix.astype(np.float32).tobytes(),check=True)
print('ok',round(T,3))
