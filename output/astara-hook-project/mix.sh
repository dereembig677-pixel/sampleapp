# Voice (Demucs stem) on top, the clip's music pulled down ~9 dB, restrained SFX on real moments; -14 LUFS, TP -1.5 dB
# needs: python3 -m demucs --two-stems=vocals -n htdemucs -o w/sep w/full.wav
V=w/sep/htdemucs/full/vocals.wav; M=w/sep/htdemucs/full/no_vocals.wav; S=/root/.claude/skills/ghost-editor/library/sfx
ffmpeg -v error -y -i $V -i $M -i $S/tech-digital-whoosh.wav -i $S/whoosh-2.wav -i $S/cc0-whoosh-reverse.wav -i $S/send-swoosh.wav -i $S/pop-1.wav -i $S/cinematic-cine-hit.wav -filter_complex \
"[0:a]highpass=f=70,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=120[v];\
[1:a]volume=-9dB,lowpass=f=9000[m];\
[2:a]volume=-60dB[s0];\
[5:a]adelay=1640|1640,volume=-18dB[s1];\
[4:a]adelay=2540|2540,volume=-20dB[s2];\
[5:a]adelay=3080|3080,volume=-18dB[s3];\
[6:a]adelay=3260|3260,volume=-16dB[s4];[6:a]adelay=1840|1840,volume=-16dB[s6];\
[7:a]adelay=3680|3680,volume=-22dB,afade=t=out:st=4.4:d=0.45[s5];\
[v][m][s0][s1][s2][s3][s4][s5][s6]amix=inputs=9:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000" -c:a pcm_s16le w/mix.wav
