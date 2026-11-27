# CTC forced alignment of the corrected Persian transcript (wav2vec2 Persian) -> words.json
import json, wave, numpy as np, torch, sys
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
M='jonatasgrosman/wav2vec2-large-xlsr-53-persian'
proc=Wav2Vec2Processor.from_pretrained(M); model=Wav2Vec2ForCTC.from_pretrained(M).eval()
w=wave.open(sys.argv[1]); audio=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; SR=16000
vocab=proc.tokenizer.get_vocab(); blank=proc.tokenizer.pad_token_id; SEP=vocab['|']
words="امروز اومدیم شهر زیبای آستارا واسه افتتاح شرکت ویهان بتن".split()
norm=lambda s:''.join(c for c in s.replace('‌','') if c in vocab)
inp=proc(audio,sampling_rate=SR,return_tensors='pt').input_values
with torch.no_grad(): lp=torch.log_softmax(model(inp).logits[0],-1).numpy()
T=lp.shape[0]; fd=(len(audio)/SR)/T
toks=[];widx=[]
for i,wd in enumerate(words):
    if toks: toks.append(SEP);widx.append(-1)
    for ch in norm(wd): toks.append(vocab[ch]);widx.append(i)
S=2*len(toks)+1; ext=[blank if s%2==0 else toks[s//2] for s in range(S)]
dp=np.full((T,S),-1e9); bp=np.zeros((T,S),np.int32); dp[0,0]=lp[0,ext[0]]; dp[0,1]=lp[0,ext[1]]
for t in range(1,T):
    for s in range(S):
        c=[(dp[t-1,s],s)]
        if s>0:c.append((dp[t-1,s-1],s-1))
        if s>1 and ext[s]!=blank and ext[s]!=ext[s-2]:c.append((dp[t-1,s-2],s-2))
        v,k=max(c);dp[t,s]=v+lp[t,ext[s]];bp[t,s]=k
s=S-1 if dp[T-1,S-1]>dp[T-1,S-2] else S-2;path=[0]*T
for t in range(T-1,-1,-1):path[t]=s;s=bp[t,s]
f={};l={}
for t,s in enumerate(path):
    if s%2:
        wi=widx[s//2]
        if wi>=0:f.setdefault(wi,t);l[wi]=t
out=[{'w':wd,'s':round(f[i]*fd,3),'e':round((l[i]+1)*fd,3)} for i,wd in enumerate(words)]
for o in out:print(o)
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
