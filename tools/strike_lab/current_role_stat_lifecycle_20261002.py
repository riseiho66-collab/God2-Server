"""Bounded real role-panel constructor/toggle and absolute2C lifecycle oracle.
Offline only: no gameplay process, DB, sockets or source/client modifications.
"""
import json,struct,hashlib,argparse,re
from pathlib import Path
import pefile,unicorn as uc
from tools.strike_lab.current_armor_equipped_attributes_20261002 import StatProbe,role_snapshot,LIVE,PIN,CONTRACT,ROOT,sha,require
from tools.strike_lab.current_armor_projection_20261002 import program_fixture
from tools.strike_lab.current_protocol_coverage import qualified_image
from tools.strike_lab.current_four_stat_ui_binding import SOURCES,parse_rom,decoded_source
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.current_weapon_attributes_native_20260926 import ACTOR
from tools.strike_lab.current_dialogue_mode4_native_20260926 import UI,RESOURCE,TABLE,PACKET,QUEUE,RETURN,SP
RENDER,SPRITES,BANKS,ASSETS,ROOT_ACTOR,ROOT_UI=0x70000000,0x70400000,0x70800000,0x71000000,0x63000000,0x64000000
API=0x72000000
INPUT=0x65000000
OUTPUT=ROOT/'artifacts/research/current-role-stat-lifecycle-20261002'

class Lifecycle(StatProbe):
 def __init__(self,pe,original,program):
  super().__init__(pe,original);self.entries=[];self.last=[];self.resource_requests=[];self.call_chain=[]
  self.vm.hook_add(uc.UC_HOOK_CODE,self.entry_trace)
  self.vm.mem_map(API,4096);self.write(0x5706e4,'I',API);self.write(0x5707bc,'I',API+16);self.write(0x5706c4,'I',API+32);self.write(0x5706c8,'I',API+48);self.api_calls=[]
  self.vm.mem_map(0,4096);self.vm.mem_map(ACTOR+4096,0x5000)
  for a,size in ((RENDER,0x300000),(SPRITES,0x100000),(BANKS,0x2a4000),(ASSETS,0x800000),(ROOT_ACTOR,0x6000),(ROOT_UI,0x60000),(INPUT,0x13000)):self.vm.mem_map(a,size)
  self.write(UI+0x8688c,'I',ROOT_ACTOR);self.write(UI+0x86884,'I',ROOT_UI);self.write(UI+0x232ebc,'I',ROOT_UI);self.write(ROOT_UI+0xdc,'I',UI)
  for off in range(0x232db0,0x232eb0,2):self.write(UI+off,'h',-1)
  self.write(UI+0x232e50,'h',-1);self.write(UI+0x232e52,'h',-1)
  program_fixture(self,program);self.assets();self.write(UI+0xe2174,'I',INPUT);self.invoke(0x507ca0,phase='widget_manager_ctor',this=UI+0xe2170)
 def code(self,v,a,size,ctx):
  if API<=a<API+64:return
  super().code(v,a,size,ctx)
 def trace(self,v,a,size,ctx):
  if a==0x546cf7:
   require(bytes(v.mem_read(a,size))==self.original[a-0x400000:a-0x400000+size],'CRT code pin');self.visited.add((a,size))
   sp=self.reg('ESP');ptr=self.read(sp+4,'I');fmt=self.cstring(self.read(sp+8,'I'));arg=self.read(sp+12,'I');out=bytearray();at=0
   for match in re.finditer(rb'%([-+ #0]*[0-9]*(?:\.[0-9]+)?)([sdfu%])',fmt):
    out+=fmt[at:match.start()];kind=match[2];spec=match.group().decode('ascii')
    if kind==b'%':value='%';text=b'%'
    elif kind==b'f':value=self.read(arg,'d');arg+=8;text=(spec%value).encode()
    elif kind==b's':value=self.cstring(self.read(arg,'I'));arg+=4;text=value
    else:value=self.read(arg,'i' if kind==b'd' else 'I');arg+=4;text=(spec%value).encode()
    out+=text;at=match.end()
   out+=fmt[at:];require(b'%' not in out,'Unsupported format');v.mem_write(ptr,bytes(out)+b'\0');self.setreg('EAX',len(out));self.setreg('EIP',self.read(sp,'I'));self.setreg('ESP',sp+4);return
  if not API<=a<API+64:return super().trace(v,a,size,ctx)
  sp=self.reg('ESP');self.api_calls.append({'phase':self.phase,'api':{API:'SetRect',API+16:'timeGetTime',API+32:'CopyRect',API+48:'OffsetRect'}[a]})
  if a==API:
   ptr=self.read(sp+4,'I');rect=bytes(v.mem_read(sp+8,16));v.mem_write(ptr,rect);value=1;pop=20
  elif a==API+16:value=123456;pop=0
  elif a==API+32:
   v.mem_write(self.read(sp+4,'I'),bytes(v.mem_read(self.read(sp+8,'I'),16)));value=1;pop=8
  else:
   ptr=self.read(sp+4,'I');x=self.read(sp+8,'i');y=self.read(sp+12,'i');left,top,right,bottom=struct.unpack('<4i',v.mem_read(ptr,16));v.mem_write(ptr,struct.pack('<4i',left+x,top+y,right+x,bottom+y));value=1;pop=12
  self.setreg('EAX',value);self.setreg('EIP',self.read(sp,'I'));self.setreg('ESP',sp+4+pop)
 def entry_trace(self,v,a,size,_):
  if bytes(v.mem_read(a,1))==b'\xe8':self.call_chain.append(hex(a));self.call_chain=self.call_chain[-30:]
  if a==0x41e710:self.resource_requests.append({'bank_ptr':hex(self.read(self.reg('ESP')+4,'I')),'action':self.read(self.reg('ESP')+8,'i'),'caller':hex(self.read(self.reg('ESP'),'I'))})
  self.last.append(a);self.last=self.last[-16:]
  if a in (0x4e7c80,0x4e8514,0x4e6710,0x4e6db0,0x4e6600,0x4e79a0,0x4e79e0,0x4e7b20,0x5046a0,0x507b20,0x507bb0):
   self.entries.append({'phase':self.phase,'address':hex(a)})
 def assets(self):
  top=ASSETS
  def store(data):
   nonlocal top
   ptr=top;top+=(len(data)+15)&~15;require(top<=ASSETS+0x800000,'GUI fixture budget');self.vm.mem_write(ptr,bytes(data));return ptr
  self.asset_pins=[]
  sources={34:SOURCES[34],33:('Data3/Flow/Cuse.romZ','a70489dbf53513f4f2b028020efbb246c64d10959de9088fcff61f687cf99358','dacb8b796578a772b561e1a83659304edf2670cca1fc7f524571c08ed0d0a531')}
  for ordinal,(path,rawsha,plainsha) in sources.items():
   raw,plain=decoded_source(LIVE.parent/path,rawsha,plainsha);rom=parse_rom(plain,name_encoding='cp950');bank=BANKS+ordinal*0x1514
   for i,p in enumerate(rom['palettes']):self.write(bank+8+4*i,'I',store(p['data']))
   for i,image in enumerate(rom['images']):self.write(bank+0x8c+4*i,'I',store(image['data']))
   self.write(bank+0x108c,'I',len(rom['actions']))
   for i,a in enumerate(rom['actions']):
    header=bytearray(max(0x640,0x630+4*len(a['pools'])));header[:48]=a['data']
    for j,step in enumerate(a['steps']):struct.pack_into('<I',header,0x30+4*j,store(step['data']))
    for j,pool in enumerate(a['pools']):struct.pack_into('<I',header,0x630+4*j,store(pool['data']))
    self.write(bank+0x1090+4*i,'I',store(header))
   self.asset_pins.append({'path':path,'raw':rawsha,'plain':plainsha,'bank':ordinal,'actions':len(rom['actions'])})
  self.write(RENDER+4,'II',SPRITES,0);self.write(RENDER+0xc,'I',BANKS)
  self.write(UI+0xcff60,'I',RENDER);self.write(UI+0xe2178,'I',RENDER)
 def invoke(self,address,*args,phase,this=UI):
  self.phase=phase;self.setup(*args);self.setreg('ECX',this)
  try:self.run(address,[RETURN,0x402c70])
  except Exception as e:raise RuntimeError(f'{phase} failed at {self.reg("EIP"):x} last={list(map(hex,self.last))} calls={self.call_chain}') from e
  require(self.reg('EIP')==RETURN,'Native assert '+phase+' last='+str(list(map(hex,self.last)))+' resources='+str(self.resource_requests[-4:])+' args='+str([hex(self.read(self.reg('ESP')+4+i*4,'I')) for i in range(3)]))
  require(self.reg('ESP')==SP+4+4*len(args),'Native stack '+phase)

def program_data():
 raw=(LIVE.parent/'Data2/Patch/Comm/message.csvZ').read_bytes();require(sha(raw)=='5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598','Message pin')
 out={};inside=False
 for row in decode_csvz(raw).splitlines():
  if row.startswith(b'ProgramMsg,'):inside=True;continue
  f=row.split(b',',1)
  if inside and len(f)==2 and f[0].isdigit():out[int(f[0])]=f[1]
 return out

def typed_role2c(*,constitution,strength,intelligence,speed,metal,wood,water,fire,earth,physical_defense,physical_attack,magic_defense,magic_attack):
 """Server-owned semantic values only. Never serialize client normalized RAM."""
 modifiers=(constitution,strength,intelligence,speed);elements=(metal,wood,water,fire,earth);combat=(physical_defense,physical_attack,magic_defense,magic_attack)
 require(all(type(v) is int and -32768<=v<=32767 for v in modifiers),'Signed modifier domain')
 require(all(type(v) is int and 0<=v<=0xffffffff for v in elements),'Raw element DWORD domain; display not claimed')
 require(all(type(v) is int and 0<=v<=0x7fffffff for v in combat),'Nonnegative signed-display combat domain')
 positive=sum(bit for v,bit in zip(modifiers,(2,4,1,8)) if v>0)
 negative=sum(bit for v,bit in zip(modifiers,(2,4,1,8)) if v<0)
 return b'\x2c'+struct.pack('<15I',*(tuple(abs(v) for v in modifiers)+elements+(positive,negative)+combat))

def typed_fixture(values):
 return typed_role2c(**dict(zip(('constitution','strength','intelligence','speed','metal','wood','water','fire','earth','physical_defense','physical_attack','magic_defense','magic_attack'),values+(101,102,103,104,105)+(201,202,203,204))))

def consume(n,logical,phase,expected):
 require(len(logical)==61 and logical[0]==0x2c,'Exact logical61 snapshot')
 n.vm.mem_write(PACKET,logical[1:]);n.invoke(0x4e6600,PACKET,phase=phase)
 require(role_snapshot(n)['modifier']==list(expected),'Fresh2C semantic signs differ')
 formats=[r for r in n.status_formats if r['phase']==phase and 18<=r['control']<=21]
 if n.read(UI+0x232dda,'h')>=0:
  require(len(formats)==4,'Missing native modifier formatter')
  for row,wanted in zip(formats,expected):
   fmt=bytes.fromhex(row['format_hex'])
   require(fmt== (b'+%d' if wanted>0 else b'%d' if wanted<0 else b''),'Modifier format polarity')
   if wanted:require(row['value_raw']==wanted&0xffffffff,'Signed native formatter argument')
 return {'phase':phase,'logical61_hex':logical.hex(),'snapshot':role_snapshot(n),'formats':formats}

def toggle(n,action,expected_open):
 before=len(n.entries);start=n.read(QUEUE+0x36c4,'I');n.invoke(0x4e79a0,phase=action)
 intermediate=n.read(UI+0xe2988,'H');flags=[intermediate]
 for step in range(100):
  for field in (4,10):
   group=n.read(UI+0xe2988+field,'H')
   if group<0x1000 and n.read(RENDER+0x10+group*0x290,'B')==2:n.invoke(0x41c360,RENDER+0x10+group*0x290,phase=action+'_animation',this=RENDER)
  n.invoke(0x504620,TABLE,TABLE+4,phase=action+'_widget_update',this=UI+0xe2170)
  flag=n.read(UI+0xe2988,'H');flags.append(flag)
  if flag&0x30:break
 require(flag== (0x23 if expected_open else 0x13),'Real widget transition failed')
 calls=n.entries[before:];require(not any(r['address'] in ('0x4e6710','0x4e6db0') for r in calls),'Ordinary toggle unexpectedly renormalized role')
 finish=n.read(QUEUE+0x36c4,'I');delta=bytes(n.vm.mem_read(QUEUE+0x36c8+start,finish-start)).hex()
 return {'phase':action,'widget_flags':list(map(hex,flags)),'frames':step+1,'native_calls':calls,'outgoing_queue_delta_hex':delta,'modifier':role_snapshot(n)['modifier']}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=OUTPUT);args=ap.parse_args();require(not args.output_dir.exists(),'New evidence directory required')
 raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current EXE pin');pe=pefile.PE(data=raw);original=qualified_image();program=program_data()
 guards=json.loads(CONTRACT.read_text('utf-8'))['source_sha256'];require(all(sha((ROOT/f).read_bytes())==h for f,h in guards.items()),'Frozen runtime20 changed before research')
 prior=ROOT/'artifacts/research/current-armor-equipped-attributes-20261002'
 prior_files={str(f.relative_to(ROOT)):sha(f.read_bytes()) for f in (prior/'native.json',prior/'contract.md',ROOT/'tools/strike_lab/current_armor_equipped_attributes_20261002.py')}
 require(prior_files[str((prior/'native.json').relative_to(ROOT))]=='1298f8cad1f780708ed8955df4b74ff840aed9e37778810b090335def94402e3','Prior45 evidence changed')
 require(json.loads((prior/'native.json').read_text('utf-8'))['tooltip_cases'][0]['labels']==['物防','魔防','力','體','智','速'],'Correction source labels differ')
 lifecycle=[];ordering=[];visits=set()
 vectors=((0,0,0,0),(-1,-13,-32767,-32768),(32767,-32768,1,-1),(111,-222,333,-444))
 for edition in (0,1):
  for values in vectors:
   n=Lifecycle(pe,original,program);n.write(QUEUE+0x4200,'B',edition);n.write(ACTOR+0x78,'4I',111,222,333,444)
   n.invoke(0x4e7c80,ACTOR,phase='constructor');require(n.read(UI+0x232dda,'h')==0,'Native role allocation');events=[]
   logical=typed_fixture(values);events.append(consume(n,logical,'fresh_closed',values))
   events.append(toggle(n,'open',True));require(role_snapshot(n)['modifier']==list(values),'Open changed signs')
   events.append(consume(n,logical,'fresh_open',values));events.append(consume(n,logical,'repeat_fresh_open',values))
   events.append(toggle(n,'close',False));require(role_snapshot(n)['modifier']==list(values),'Close changed signs')
   events.append(consume(n,logical,'fresh_closed_again',values));events.append(toggle(n,'reopen',True));require(role_snapshot(n)['modifier']==list(values),'Reopen changed signs')
   events.append(consume(n,logical,'fresh_reopen',values));events.append(toggle(n,'close_again',False));require(role_snapshot(n)['modifier']==list(values),'Final close changed signs')
   require([r['address'] for r in n.entries].count('0x4e6710')==6,'Unexpected role normalization lifecycle')
   require(not n.inventory_accesses,'Role lifecycle read equipment unexpectedly')
   visits.update(n.visited);lifecycle.append({'edition_byte':edition,'semantic_modifiers':values,'events':events,'entries':n.entries,'external_api_counts':{name:sum(r['api']==name for r in n.api_calls) for name in ('SetRect','timeGetTime','CopyRect','OffsetRect')},'equipment_reads':0,'full_constructor_return':True})
  for values in ((-1,-13,-32767,-32768),(111,-222,333,-444)):
   n=Lifecycle(pe,original,program);n.write(QUEUE+0x4200,'B',edition);logical=typed_fixture(values)
   first=consume(n,logical,'pre_constructor2C',values);n.invoke(0x4e7c80,ACTOR,phase='constructor_after2C');after=role_snapshot(n)['modifier']
   flipped=[-v if v<0 and v!=-32768 else v for v in values];require(after==flipped,'Constructor ordering signs differ')
   opened=toggle(n,'open_after_prior2C',True);require(role_snapshot(n)['modifier']==flipped,'Ordinary opener renormalized')
   corrected=consume(n,logical,'fresh_after_constructor',values);closed=toggle(n,'close_after_correction',False);reopened=toggle(n,'reopen_after_correction',True)
   require(role_snapshot(n)['modifier']==list(values),'Fresh correction failed lifecycle')
   visits.update(n.visited);ordering.append({'edition_byte':edition,'semantic_modifiers':values,'pre_constructor':first,'after_full_constructor_modifier':after,'opened':opened,'fresh_absolute_correction':corrected,'close':closed,'reopen':reopened,'qualification':'reachable machine ordering control; actual live startup packet order not tested'})
 require(all(sha((ROOT/f).read_bytes())==h for f,h in guards.items()),'Frozen runtime20 changed after research')
 require(all(sha((ROOT/f).read_bytes())==h for f,h in prior_files.items()),'Prior45 deliverable changed')
 result={'status':'PASS','scope':'Offline actual x86 full4E7C80 ctor/4E79A0 toggles/real widget animation/fresh2C; synthetic owned role and device/input backing; not live startup, rendered UI or stat formula acceptance','cases':len(lifecycle)+len(ordering),'current_client_sha256':sha(raw),'original_mapped_sha256':sha(original),'tool_sha256':sha(Path(__file__).read_bytes()),'assets':n.asset_pins,'lifecycle_cases':lifecycle,'constructor_ordering_cases':ordering,'executed_matched_instruction_count':len(visits),'runtime20_preserved':True,'prior45_sha256_preserved':prior_files,'external_adapters':['CRT sprintf547AF7 inherited','CRT vsprintf546CF7','USER32 SetRect/CopyRect/OffsetRect','WinMM timeGetTime'],'no_game_callee_stubs':True,'finding':'Ordinary open/close/reopen never renormalizes. Constructor calls4E6710 once and flips existing negative-only normalized WORD. A new absolute2C recovers canonical signs. Actual startup order and constructor reuse require separate live proof.','correction':'Prior45 prose mislabeled armor centers. Native labels74,73,72,75 are force/constitution/intelligence/speed: instance bytes8/9 are Strength/Constitution;2C logical1/5 are Constitution/Strength. Prior evidence remains unchanged.'}
 args.output_dir.mkdir(parents=True,exist_ok=False);(args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
 (args.output_dir/'contract.md').write_text(CONTRACT_TEXT,'utf-8')
 print('PASS',result['cases'],'bounded real role lifecycle cases',args.output_dir);print('Matched instructions',len(visits));print('Tool SHA256',result['tool_sha256']);print('Evidence SHA256',sha((args.output_dir/'native.json').read_bytes()))

CONTRACT_TEXT="""# Role panel lifecycle and corrected typed fields

This NEW evidence supersedes only the semantic ordering prose and untested caller-lifetime caveat of the earlier 45-case report. Earlier native.json, contract.md, and tool are preserved byte for byte.

## Actual executed native lifecycle

Full constructor 4E7C80 -> true caller4E8514 ->4E6710 executes once. Original FS2_GUI bank34 and Cuse bank33 chunks supply native action/control resources, including edition0/1 branches. Native widget manager507CA0 initializes registry; 4E79A0 chooses4E79E0 open or4E7B20 close;41C360 advances original animation,504620 updates flags. The sequence is13 closed ->0B opening ->23 open ->07 closing ->13 closed ->0B reopening ->23 open. No gameplay callee is stubbed. External formatting and four Win32 APIs are modeled; ROM loader and display-device blit are not tested.

Ordinary open and reopen send native1F requests but NEVER call4E6710 or4E6DB0. Negative modifiers remain unchanged on close/reopen. Each fresh2C fully overwrites raw operands and sign masks, then normalizes once; repeated fresh snapshots are stable whether the widget is closed or open. This is machine evidence, not live screen or formal server acceptance.

If a negative-only2C has already normalized actor RAM before full4E7C80 constructor, the actual constructor changes negative values to positive (except -32768, invariant in16bits). Ordinary opener does not fix that state; a fresh absolute2C fixes it. The machine ordering control does not prove current live startup has this ordering. Server producer should respond to each valid1F with fresh authoritative absolute values; do not copy normalized client RAM back into wire.

## Correction: armor and role fields use different orders

Actual earlier native.json labels are [物防,魔防,力,體,智,速], not Con/Str. Armor instance byte8 plus byte19 bit0 is Strength/Force; byte9 plus bit1 is Constitution; byte10/11 plus bit2/3 are Intelligence/Speed. Centers range0..511; physical/magic defense range0..1023. Source class fields, tooltip operands, and2C positions must not be treated as the same order.

## Server-owned typed logical61 builder

Opcode2C; four DWORD cells at logical1/5/9/13 represent Constitution/Strength/Intelligence/Speed, with only lowWORD consumed. Encode semantic int16 -32768..32767 as abs(value), highWORD0. Positive mask DWORD logical37 and negative mask DWORD41 use con2,str4,int1,speed8; only lowWORD is consumed. Set exactly one sign bit for nonzero values; zero has neither. -32768 magnitude32768 with negative bit is representable. Never serialize an already-negated RAMWORD with old negative mask.

Metal/Wood/Water/Fire/Earth at logical17/21/25/29/33 are raw DWORDs, actorA4/A8/AC/B0/B4. Storage domain0..FFFFFFFF is proven; this tool does not prove their user-visible formatter domain.

PhysicalDefense/PhysicalAttack/MagicDefense/MagicAttack DWORDs logical45/49/53/57 go to actor98/94/A0/9C. Native formatter uses signed%d; mechanically INT32_MIN..INT32_MAX can be displayed. Typed nonnegative role combat totals here require0..INT32_MAX to avoid wrapped negative text. This is an encoding policy, not recovered original balance formula.

Native controls14..17 separately show base22 Con/Str/Int/Speed;18..21 show signed2C modifiers (+%d positive,%d negative,empty forzero). They do not add base and modifier, nor read equipped metadata. No proof of original instance generation, four-part sum, set/enhancement/buff or final combat formula was added. Any sum or cap remains CUSTOM and needs its own authority/live/balance acceptance.
"""
if __name__=='__main__':main()
