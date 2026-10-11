// CUSTOM: fixed-field native export; preserve choreography but remove the
// preview-only UI crop. Native UI overlays provide their own occlusion.
// BULLFX01 uses straight RGBA row spans. Ground is before native actors;
// foreground is after them. Browser additive drawing is flattened within each
// transparent layer; native playback must source-over, never add it again.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const {createCanvas,Image}=require('C:/Users/risei/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas');
const root=path.resolve(process.argv[2]||'C:/Users/risei/Desktop/封神OL技能模擬預覽');
const out=path.resolve(process.argv[3]||'artifacts/custom-skills/thousand-bulls/visualpack');
const W=1040,H=807,F=240,FPS=30;
fs.mkdirSync(out,{recursive:true});
const pins=new Map(),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function source(name){const b=fs.readFileSync(path.join(root,name));pins.set(name,sha(b));return b;}
const pendingImages=[];
class AssetImage extends Image{
  set src(v){super.src=source(v);pendingImages.push(this);}
  get complete(){return this.width>0;} get naturalWidth(){return this.width;} get naturalHeight(){return this.height;}
}
const stage={dataset:{}};
const sandbox={window:null,document:{getElementById:()=>stage,createElement:()=>createCanvas(1,1)},Image:AssetImage,console,Math,Map,Array};
sandbox.window=sandbox;const context=vm.createContext(sandbox);
for(const filename of ['data.js','bull-stampede-data.js','bull-stampede.js']){
 let code=source(filename).toString('utf8');
 if(filename==='bull-stampede.js'){
  const crop='ctx.rect(0,99,1040,660)';
  if(code.split(crop).length-1!==3)throw Error('Preview crop contract changed');
  code=code.replaceAll(crop,'ctx.rect(0,0,1040,807)');
 }
 vm.runInContext(code,context,{filename});
}
const effect=sandbox.BULL_STAMPEDE;
async function main(){
await Promise.all(pendingImages.map(image=>image.decode()));
if(pendingImages.some(image=>!image.naturalWidth))throw Error('Source sprite decode incomplete');
function spans(canvas){
  const rgba=canvas.getContext('2d').getImageData(0,0,W,H).data,parts=[];let count=0;
  for(let y=0;y<H;y++)for(let x=0;x<W;){
    while(x<W&&!rgba[(y*W+x)*4+3])x++;if(x===W)break;
    const start=x;while(x<W&&rgba[(y*W+x)*4+3])x++;
    const h=Buffer.alloc(8);h.writeUInt16LE(start,0);h.writeUInt16LE(y,2);h.writeUInt16LE(x-start,4);
    parts.push(h,Buffer.from(rgba.buffer,rgba.byteOffset+(y*W+start)*4,(x-start)*4));count++;
  }
  const h=Buffer.alloc(4);h.writeUInt32LE(count);return Buffer.concat([h,...parts]);
}
function writer(name){
  const fd=fs.openSync(path.join(out,name),'w'),header=Buffer.alloc(24+F*12);
  header.write('BULLFX01',0,'ascii');header.writeUInt32LE(W,8);header.writeUInt32LE(H,12);header.writeUInt32LE(F,16);header.writeUInt32LE(FPS,20);
  fs.writeSync(fd,header);let offset=header.length;
  return {frame(tick,canvas){const b=spans(canvas);header.writeBigUInt64LE(BigInt(offset),24+tick*12);header.writeUInt32LE(b.length,32+tick*12);fs.writeSync(fd,b);offset+=b.length;},
    close(){fs.writeSync(fd,header,0,header.length,0);fs.closeSync(fd);return {path:name,bytes:offset,sha256:sha(fs.readFileSync(path.join(out,name)))}}};
}
const metadata={format:'BULLFX01',skill_id:150,source_root:root,width:W,height:H,frames:F,fps:FPS,duration_seconds:8,
  clip:{x:0,y:0,width:W,height:H},native_clip_override:'Replace three preview-only(0,99,1040,660) clips with full canvas; source files untouched',herd_count:90,target_count_independent:true,layers:['ground','foreground'],
  alpha:'straight RGBA, source-over; additive particles already baked within transparent layer',
  limitation:'Flattened additive light over arbitrary underlying game pixels is an approximation; geometry, opacity and layer order preserve the accepted source.',
  damage_ticks:[70,110,150,190],damage_weights:[20,25,30,25],
  damage_timing_reason:'First contact tick63; continuous contact through tick214.3. Four impacts at70/110/150/190 span the dense stampede, never tied to target count.',
  shake:{amplitude:'2.3+(tick>=40&&tick<=155?2.2:0)+1.1*abs(sin(tick*1.7))',x:'round(sin(tick*5.37)*amplitude)',y:'round(cos(tick*4.11)*amplitude*.68)',scope:'battle viewport only'},
  files:[],audio:[],samples:[]};
const keys=[24,25,63,70,110,150,190,220,239],sheet=createCanvas(keys.length*260,2*224),sg=sheet.getContext('2d');
for(const [sideIndex,side] of ['player','enemy'].entries()){
  const ground=createCanvas(W,H),front=createCanvas(W,H),g=ground.getContext('2d'),f=front.getContext('2d');
  const gw=writer(side+'-ground.bfx'),fw=writer(side+'-foreground.bfx');
  for(let tick=0;tick<F;tick++){
    g.clearRect(0,0,W,H);f.clearRect(0,0,W,H);effect.drawGround(g,tick,[],side==='enemy');effect.draw(f,tick,[],side==='enemy');
    gw.frame(tick,ground);fw.frame(tick,front);
    if(keys.includes(tick)){
      const x=keys.indexOf(tick)*260,y=sideIndex*224;
      sg.fillStyle='#665e4e';sg.fillRect(x,y,260,202);sg.drawImage(ground,x,y,260,202);sg.drawImage(front,x,y,260,202);
      sg.fillStyle='#141414';sg.fillRect(x,y+202,260,22);sg.fillStyle='#ffffff';sg.font='14px sans-serif';sg.fillText(side+' '+tick+' / '+(tick/30).toFixed(2)+'s',x+6,y+218);
      const entities=effect.herdState(tick,side==='enemy').entities;
      metadata.samples.push({side,tick,active:entities.length,solid:entities.filter(e=>e.opacity>=1).length,friendly_max_alpha:Math.max(0,...entities.filter(e=>e.clearance<=0).map(e=>e.opacity))});
    }
    if(tick%60===0)console.log(side,tick);
  }
  metadata.files.push(gw.close(),fw.close());
}
fs.writeFileSync(path.join(out,'contact-sheet.png'),sheet.toBuffer('image/png'));
for(const name of ['niu_zhuan_xian_jie_ta_cast_whistle.wav','niu_zhuan_xian_jie_ta_herd_stomp.wav','bull-stampede-native-voice.wav']){
  const b=source('audio/'+name);fs.writeFileSync(path.join(out,name),b);metadata.audio.push({path:name,sha256:sha(b)});
}
metadata.source_pins=Object.fromEntries([...pins.entries()].sort());metadata.exporter_sha256=sha(fs.readFileSync(__filename));
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(metadata,null,2)+'\n');
console.log('complete',out,metadata.files.map(x=>[x.path,x.bytes]));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
