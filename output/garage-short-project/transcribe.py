import sys, json
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[2],compute_type='int8',cpu_threads=4)
segs,info=m.transcribe(sys.argv[1],language='fa',word_timestamps=True,beam_size=5,vad_filter=False,condition_on_previous_text=True,initial_prompt='رفقا، تعمیرگاه، مهره پلوس، بکس ۳۵، دسته بکس سه‌چهارم، تورچ، داغ، دستکش، سرویس، ماشالله، سابسکرایب، تویوتا پرادو، چنل، بازسازی')
out=[]
for s in segs:
    out.append({'start':s.start,'end':s.end,'text':s.text,'words':[{'w':w.word,'s':w.start,'e':w.end,'p':w.probability} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}",flush=True)
json.dump(out,open(sys.argv[3],'w'),ensure_ascii=False,indent=1)
