import subprocess, sys
L='/root/.claude/skills/ghost-editor/library/sfx/'; X='../sfx/'; V=sys.argv[1]; MUS='/root/.claude/skills/ghost-editor/library/music/infinity.mp3'
# (time, file, gain dB, trim start, duration)
S=[(0.08,L+'tech-digital-whoosh.wav',-17,0,1.2),
 (3.40,L+'impact-2.wav',-13,0,1.0),(3.42,L+'cc0-glass-break.wav',-22,0,0.8),
 (14.94,L+'cc0-error-beep.wav',-18,0,0.8),
 (18.12,L+'whoosh-2.wav',-13,0,0.9),(18.75,X+'strong_punch.mp3',-11,0,0.52),(19.55,X+'strong_punch.mp3',-12,0,0.52),(20.35,X+'body_punches.mp3',-14,0,1.38),
 (21.28,L+'cc0-vinyl-scratch.wav',-15,0,0.7),(22.45,L+'pop-1.wav',-17,0,0.3),(22.70,L+'pop-2.wav',-15,0,0.2),
 (29.10,X+'speed_swoosh.mp3',-12,0,1.2),(29.45,X+'car_start.mp3',-17,0,2.0),(31.30,L+'whoosh-1.wav',-17,0,0.9),
 (35.13,L+'whoosh-cine.wav',-14,0,0.4),
 (39.45,L+'tick-1.wav',-19,0,0.3),(41.04,L+'cc0-vinyl-scratch.wav',-13,0,0.7),
 (43.00,L+'riser-1.wav',-23,0,1.7),(45.60,L+'riser-1.wav',-21,0,1.7),(48.20,L+'tech-ui-error.wav',-18,0,0.8),
 (53.58,L+'impact-1.wav',-13,0,1.2),(55.05,L+'impact-1.wav',-12,0,1.2),(55.72,L+'cinematic-cine-hit.wav',-12,0,1.6),
 (60.80,L+'reaction-ding-ding.wav',-15,0,1.2),
 (61.25,X+'fire_swoosh.mp3',-13,0,1.6),(61.30,X+'fire_crackle.mp3',-18,0.2,2.6),
 (67.50,L+'whoosh-reverse.wav' if False else L+'cc0-whoosh-reverse.wav',-22,0,1.0),
 (72.30,L+'whoosh-1.wav',-17,0,0.9),(72.94,L+'click-1.wav',-10,0,0.3),(73.02,L+'ding-1.wav',-16,0,1.0),
 (74.68,L+'click-1.wav',-10,0,0.3),(74.74,L+'pop-3.wav',-13,0,0.4),(80.50,L+'whoosh-2.wav',-15,0,0.9)]
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
