// usage: node render.js <outdir> <fps> <nframes> [list] [workerIndex workerCount]
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{const [out,fps,n]=[process.argv[2],+process.argv[3],+process.argv[4]];const list=process.argv[5]&&process.argv[5]!=='-'?process.argv[5].split(',').map(Number):null;
  const wi=+(process.argv[6]||0),wc=+(process.argv[7]||1);fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch({args:['--allow-file-access-from-files']});const p=await b.newPage({viewport:{width:1080,height:1920}});
  p.on('pageerror',e=>console.log('ERR',e.message));await p.goto('file://'+path.resolve(__dirname,'gfx.html'));await p.evaluate(()=>window.ready);
  const frames=(list||[...Array(n).keys()]).filter((f,i)=>i%wc===wi);
  for(const f of frames){const d=await p.evaluate(([t,l])=>{render(t,l);return document.getElementById('c').toDataURL('image/png')},[f/fps,process.env.LAYER||'front']);
    fs.writeFileSync(`${out}/${String(f).padStart(5,'0')}.png`,Buffer.from(d.split(',')[1],'base64'))}
  await b.close()})();
