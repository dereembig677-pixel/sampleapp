import subprocess, sys
L='/root/.claude/skills/ghost-editor/library/sfx/'; X='../sfx/'; V=sys.argv[1]; MUS='/root/.claude/skills/ghost-editor/library/music/infinity.mp3'
# (time, file, gain dB, trim start, duration)
S=[(0.12,L+'tech-digital-whoosh.wav',-20,0,1.2),
 (17.98,L+'whoosh-2.wav',-15,0,0.9),(20.20,L+'pop-1.wav',-19,0,0.3),(21.56,L+'whoosh-1.wav',-18,0,0.9),
 (29.18,X+'speed_swoosh.mp3',-13,0,1.2),(29.50,X+'car_start.mp3',-20,0,1.8),(31.28,L+'whoosh-1.wav',-17,0,0.9),
 (35.70,L+'whoosh-cine.wav',-18,0,0.4),(41.12,L+'impact-2.wav',-19,0,0.8),
 (53.76,L+'impact-1.wav',-15,0,1.2),(55.28,L+'impact-1.wav',-15,0,1.2),(56.11,L+'cinematic-cine-hit.wav',-13,0,1.6),
 (61.18,X+'fire_swoosh.mp3',-14,0,1.6),(61.25,X+'fire_crackle.mp3',-19,0.2,2.7),
 (72.30,L+'whoosh-1.wav',-18,0,0.9),(72.85,L+'click-1.wav',-11,0,0.3),(72.98,L+'ding-1.wav',-17,0,1.0),
 (74.58,L+'click-1.wav',-11,0,0.3),(74.64,L+'pop-3.wav',-15,0,0.4),(80.42,L+'whoosh-2.wav',-17,0,0.9)]
D=81.32
args=['ffmpeg','-v','error','-y','-i',V,'-ss','4','-i',MUS]
fc=[]; mix=[]
for k,(t,f,g,ts,d) in enumerate(S):
    args+=['-i',f]; i=k+2; ms=int(t*1000)
    fc.append(f'[{i}:a]atrim={ts}:{ts+d},asetpts=N/SR/TB,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=out:st={max(0,d-0.08)}:d=0.08,volume={g}dB,adelay={ms}|{ms}[s{k}]'); mix.append(f'[s{k}]')
fc.append(f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=-7dB,highpass=f=75,lowpass=f=15000,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=4,alimiter=limit=0.89:attack=3:release=40,apad=whole_dur={D},afade=t=out:st=80.7:d=0.6,asplit=2[voice][sc]')
fc.append(f'[1:a]atrim=0:{D},asetpts=N/SR/TB,aformat=sample_rates=48000:channel_layouts=stereo,volume=-24dB,afade=t=in:d=0.6,afade=t=out:st=80.4:d=0.9[mus]')
fc.append('[mus][sc]sidechaincompress=threshold=0.04:ratio=5:attack=20:release=300[duck]')
fc.append('[voice][duck]'+''.join(mix)+f'amix=inputs={len(S)+2}:normalize=0,atrim=0:{D}[mix]')
args+=['-filter_complex',';'.join(fc),'-map','[mix]','-c:a','pcm_s16le','mix_raw.wav']
subprocess.run(args,check=True); print('sfx',len(S))
