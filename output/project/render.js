// usage: node render.js <outdir> <fps> <nframes> [frame,frame,...]
const {chromium}=require('playwright'); const fs=require('fs'); const path=require('path');
(async()=>{
  const [out,fps,n,list]=[process.argv[2],+process.argv[3],+process.argv[4],process.argv[5]];
  fs.mkdirSync(out+'/back',{recursive:true});fs.mkdirSync(out+'/front',{recursive:true});
  const b=await chromium.launch({args:['--allow-file-access-from-files']});const p=await b.newPage({viewport:{width:1080,height:1920}});
  p.on('console',m=>console.log('page:',m.text()));p.on('pageerror',e=>console.log('ERR',e.message));
  await p.goto('file://'+path.resolve(__dirname,'gfx.html'));await p.evaluate(()=>window.ready);
  const frames=list?list.split(',').map(Number):[...Array(n).keys()];
  for(const f of frames){const t=f/fps;
    for(const L of ['back','front']){
      const d=await p.evaluate(([t,L])=>{render(t,L);return document.getElementById('c').toDataURL('image/png')},[t,L]);
      fs.writeFileSync(`${out}/${L}/${String(f).padStart(4,'0')}.png`,Buffer.from(d.split(',')[1],'base64'))}
    if(f%30===0)console.log('frame',f)}
  await b.close()})();
