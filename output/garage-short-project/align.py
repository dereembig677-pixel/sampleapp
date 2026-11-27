# CTC forced alignment of corrected Persian transcript (wav2vec2 Persian), outputs words.json
import json, wave, numpy as np, torch, sys
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
M='jonatasgrosman/wav2vec2-large-xlsr-53-persian'
proc=Wav2Vec2Processor.from_pretrained(M); model=Wav2Vec2ForCTC.from_pretrained(M).eval()
w=wave.open(sys.argv[1]); audio=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; SR=16000
vocab=proc.tokenizer.get_vocab(); blank=proc.tokenizer.pad_token_id; SEP=vocab['|']
# word entries: "display=align" (display '-' hidden). align text may contain spaces (several spoken words)
SEGS=[(0.0,11.9,"رفقا متاسفانه یه دونه ابزار از دست دادیم! کله‌ش=کلش پرید و باید -=یه سرشو حالتی بکنیم که کار بهمون بده ولی نداد!"),
 (12.2,15.5,"رفتیم یه دونه بچه‌تورچ=بچه+تورچ گرفتیم باز جواب نداد!"),
 (15.8,25.9,"الان رفتیم یه دونه بکس ۳۵=سی+و+پنج فشارقوی=فشار+قوی سه‌چهارم=سه+چهارم با دسته‌بکسش=دسته+بکسش فراهم کردیم"),
 (25.8,31.0,"با تورچ می‌خوایم=میخوایم این پلوس‌رو=پلوس+رو باز کنیم"),
 (32.2,37.0,"امیدوارم که بتونیم بازش کنیم و دهنمون‌رو=دهنمون+رو سرویس نکنه! بریم تو کارش"),
 (36.85,41.30,"خب رفقا بالاخره حس می‌کنم=میکنم که باز شده... اما -=از -=منظورت باز شده؟ نه!"),
 (41.25,43.2,"فکر نکنم"),
 (47.3,51.6,"-=اوستا نه... -=دارم -=میبرم امیدوارم در حال باز شدن هم باشه"),
 (53.3,57.1,"ماشالله! ماشالله! ماشالله!"),
 (57.2,63.9,"بیاید اینجا رفقا بالاخره بازش کردیم! داغه داغه دستم داره می‌سوزه!=میسوزه با دستکش حتی!"),
 (64.8,67.3,"خیلی سخت بود"),
 (71.4,80.56,"بیاید -=که سابسکرایب کنید برای دیدن بازسازی کامل این تویوتا لندکروزر=پرادو -=هم بیاید داخل چنل")]
def norm(s):
    s=s.replace('‌','').replace('ي','ی').replace('ك','ک')
    return ''.join(ch for ch in s if ch in vocab or ch==' ')
out=[]
for a,b,text in SEGS:
    seg=audio[int(a*SR):int(b*SR)]
    inp=proc(seg,sampling_rate=SR,return_tensors='pt').input_values
    with torch.no_grad(): lp=torch.log_softmax(model(inp).logits[0],-1).numpy()
    T=lp.shape[0]; fdur=(len(seg)/SR)/T
    entries=[]
    for tok in text.split(' '):
        disp,al=(tok.split('=',1) if '=' in tok else (tok,tok))
        al=norm(al.replace('+',' ').replace('!','').replace('؟','').replace('.','').replace('۳۵',''))
        entries.append((disp,al.split()))
    # token sequence with word index per char
    toks=[];widx=[]
    for i,(d,parts) in enumerate(entries):
        for j,p in enumerate(parts):
            if toks: toks.append(SEP);widx.append(-1)
            for ch in p: toks.append(vocab[ch]);widx.append(i)
    # CTC viterbi
    L=len(toks); S=2*L+1; ext=[blank if s%2==0 else toks[s//2] for s in range(S)]
    NEG=-1e9; dp=np.full((T,S),NEG); bp=np.zeros((T,S),np.int32)
    dp[0,0]=lp[0,ext[0]]; dp[0,1]=lp[0,ext[1]]
    for t in range(1,T):
        for s in range(S):
            c=[(dp[t-1,s],s)]
            if s>0: c.append((dp[t-1,s-1],s-1))
            if s>1 and ext[s]!=blank and ext[s]!=ext[s-2]: c.append((dp[t-1,s-2],s-2))
            v,k=max(c); dp[t,s]=v+lp[t,ext[s]]; bp[t,s]=k
    s=S-1 if dp[T-1,S-1]>dp[T-1,S-2] else S-2; path=[0]*T
    for t in range(T-1,-1,-1): path[t]=s; s=bp[t,s]
    first={};last={}
    for t,s in enumerate(path):
        if s%2==1:
            wi=widx[s//2]
            if wi>=0: first.setdefault(wi,t); last[wi]=t
    for i,(d,parts) in enumerate(entries):
        if i in first: out.append({'w':d,'s':round(a+first[i]*fdur,3),'e':round(a+(last[i]+1)*fdur,3),'seg':len([x for x in SEGS if x[0]<=a])-1})
    print(f'seg {a}-{b}: '+' | '.join(f"{x['w']} {x['s']:.2f}" for x in out if x['seg']==len([x for x in SEGS if x[0]<=a])-1),flush=True)
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
