"""NEW bounded original/current x86 complete-instance discard qualification.

Offline fixture memory only. No original server binding or live UI claim.
Frozen scalar27 and bank evidence are imported/read, never overwritten.
"""
import argparse,json,struct
from pathlib import Path
import pefile,unicorn as uc
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
from tools.strike_lab.current_bank_weapon_gem_transport_20261003 import Bank,Source,metadata,SOURCE_SHA,DECODED_SHA
from tools.strike_lab.current_bank_armor_transport_20261002 import defs,ROOT,LIVE,PIN,require,sha,itemmeta,growth,CAPTURE
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
from tools.strike_lab.current_party_20261002 import UI,BODY,STACK,STOP,ACTOR
from tools.strike_lab.omega_assets import decode_csvz

OUTPUT=ROOT/'artifacts/research/current-discard-instances-20261003'
FAMILIES=(('EQU',1201,2),('TEQ',20201,26),('WPN',1,1),('TWP',19001,25),('GEM',16055,8),('MED',3107,0))
PREVIOUS=('tools/strike_lab/current_discard_27_20261002.py','artifacts/research/native-discard-27-20261002.json','tools/strike_lab/current_bank_mixed_instances_20261003.py','artifacts/research/current-bank-mixed-instances-20261003/run02/native.json')
TESTED=(0x49a330,0x49b3f3,0x496720,0x4991e0,0x498dd0,0x4c9820,0x4c9b70,0x4c9ed0,0x4ca470,0x4c9bd0,0x4c9c00,0x4eaef0,0x4ea770,0x4eb620)

class Discard(Bank):
 def __init__(self,current,original,definitions):
  super().__init__(current,original,definitions)
  del self.helpers[0x4c9bd0] # Actual quantity lifecycle must execute, not inherited close adapter.
  self.helpers[0x5073e0]=8 # External renderer control hide.
  self.vm.mem_map(0x36000000,0x6000)
  self.put(0x32000000+0xb2c68,'<I',0x36000000);self.put(0x32000000+0xb2c6c,'<H',1200)
  for i in range(1200):self.put(0x36000000+i*4,'<I',0x36005000)
  self.vm.mem_write(0x36005000,b'EXPLICIT_PRESENTATION_FIXTURE\0')
  self.put(UI+0x232df4,'<h',9);self.flags(9,0x10)
  self.steps=[]
 def hook(self,v,a,size,data):
  if a in (0x507b20,0x507bb0):
   require(bytes(v.mem_read(a,size))==self.original[a-0x400000:a-0x400000+size],'Renderer boundary bytes differ');self.visited.add((a,size))
   esp=v.reg_read(UC_X86_REG_ESP);ret,widget=struct.unpack('<II',self.read(esp,8));widget&=0xffff
   require(widget in (6,7,8,9,10,11,12),'Unqualified renderer widget '+str(widget))
   old=self.read(UI+0xe2988+widget*0x2a08,1)[0];self.flags(widget,old|0x20 if a==0x507b20 else old&~0x28)
   self.calls.append((a,(widget,)));v.reg_write(UC_X86_REG_EIP,ret);v.reg_write(UC_X86_REG_ESP,esp+8);return
  self.steps.append(a)
  super().hook(v,a,size,data)
 def call(self,entry,*args,body=None):
  if body is not None:self.vm.mem_write(BODY,body)
  self.vm.mem_write(STACK,bytes([0xa5])*0xa000);sp=STACK+0x8000
  self.put(sp,'<'+'I'*(1+len(args)),STOP,*args);self.vm.reg_write(UC_X86_REG_ECX,UI);self.vm.reg_write(UC_X86_REG_ESP,sp)
  self.vm.emu_start(entry,STOP,count=100000)
  require(self.vm.reg_read(UC_X86_REG_EIP)==STOP,'Incomplete native call '+hex(entry)+' '+hex(self.vm.reg_read(UC_X86_REG_EIP)))
  require(self.vm.reg_read(UC_X86_REG_ESP)==sp+4+4*len(args),'Native callee stack differs '+hex(entry))
 def reset(self):
  super().reset();self.steps=[];self.flags(8,0x10);self.flags(9,0x10)
  self.put(UI+0x23d5e4,'<III',0,0,0);self.put(UI+0xafece,'<B',255);self.put(UI+0x866e4,'<I',0);self.put(ACTOR+0x449e,'<B',0)
 def fixture(self,key,kind,slot=5,count=1,flags=0,salt=3):
  self.reset();meta=metadata(key,kind,flags,salt,(0,15,240,255)[salt%4])
  if kind==8:meta=metadata(key,kind,flags|(3<<25),salt,meta[19])
  self.projection3b41(slot,meta)
  self.put(self.bag(slot),'<B',count);self.put(UI+0x855f0,'<h',slot)
  return meta,self.read(UI+0x8560c,50*24)

def source_qualification(original,current):
 records,facts,info=defs(original,current)
 raw=(CAPTURE/'Data2/Patch/Comm/gamedata.csvZ').read_bytes();require(sha(raw)==SOURCE_SHA,'Original source pin');decoded=decode_csvz(raw);require(sha(decoded)==DECODED_SHA,'Decoded source pin')
 live=growth.parse_sections(decode_csvz((LIVE.parent/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()),('TWP',))
 old=itemmeta.CLIENT;itemmeta.CLIENT=CAPTURE
 try:n=Source()
 finally:itemmeta.CLIENT=old
 require([r['raw_record_hex'] for r in n.sections['TWP']['records']]==[r['raw_record_hex'] for r in live['TWP']['records']],'Current TWP source rows changed')
 matched=set()
 def hook(v,a,size,_):
  if n.active_code and a!=n.stop_address:require(bytes(v.mem_read(a,size))==current[a-0x400000:a-0x400000+size],'TWP source native mismatch');matched.add((a,size))
 n.vm.hook_add(uc.UC_HOOK_CODE,hook);require(n.lookup_section('TWP')==(35,25),'Native TWP binding');index=next(i for i,r in enumerate(n.sections['TWP']['records']) if int(growth.fields(r)[0])==19001);record=n.item_row('TWP',index)['record'];records[19001]=record
 cache=json.loads((ROOT/'artifacts/research/native-weapons-20260926/records.json').read_text('utf-8'));row=next(r for r in cache[1] if r[1]==19001);require(record==bytes.fromhex(row[8]),'TWP native source cache differs')
 facts.append({'key':19001,'source_family':'TWP','expected_instance_family':25,'source396_sha256':sha(record),'source_raw_sha256':sha(bytes.fromhex(n.sections['TWP']['records'][index]['raw_record_hex'])),'current_raw_rows_exact':True})
 return records,facts,info,matched

def execute(o,key,kind,slot,count,flags,salt,confirm=False,accept=True,chosen=None):
 meta,before=o.fixture(key,kind,slot,count,flags,salt);o.put(ACTOR+0x449e,'<B',0x10 if confirm else 0)
 o.call(0x49a330,56,0x20);opened_quantity=count in range(2,128)
 if opened_quantity:
  require(o.u32(UI+0x23d5e4)==4 and o.u32(UI+0x23d5ec)==count and o.visible(8),'Actual quantity mode4 did not open')
  require(not o.queued,'Quantity open prematurely queued')
  if chosen is not None:o.put(UI+0x23d5e8,'<I',chosen)
  o.call(0x4ca470,2,0x20) # Native quantity callback's actual OK control ->4C9ED0.
 if confirm:
  require(o.read(UI+0xafece,1)==b'\x05' and o.visible(9),'Actual confirmation5 did not open')
  require(o.read(UI+0xafecc,2)==struct.pack('<H',key) and o.u32(UI+0xafec8)==slot,'Confirmation identity/slot differs')
  require(not o.queued,'Confirmation open queued')
  o.call(0x4ea770,4 if accept else 3,1)
  require(o.read(UI+0xafece,1)==b'\xff' and not o.visible(9),'Confirmation mode not retired')
 amount=chosen if chosen is not None and opened_quantity else count
 physical_allowed=slot<30 or slot in (42,43)
 expected=[b'\x27'+struct.pack('<HBB',key,slot,amount)] if accept and physical_allowed else []
 if not physical_allowed:require(o.refusals==[820],'Equipped/native other physical discard guard changed')
 require(o.queued==expected,'Native discard wire differs '+str((key,kind,slot,count,flags,confirm,chosen,[q.hex() for q in o.queued])))
 require(o.read(UI+0x8560c,50*24)==before,'Native discard optimistically altered owned inventory')
 require(o.read(UI+0x855f0,2)==b'\xff\xff','Native selected source did not retire')
 beforecell=o.read(o.bag(slot),24);clear=struct.pack('<HBB',0,slot,0);o.call(0x4991e0,BODY,body=clear)
 after=o.read(o.bag(slot),24);require(after==b'\x00'+beforecell[1:4]+bytes(2)+beforecell[6:],'41 inactive upper18/reserved semantics differs')
 require(o.read(UI+0x8560c,slot*24)==before[:slot*24] and o.read(o.bag(slot)+24,(49-slot)*24)==before[(slot+1)*24:],'Clear touched another slot')
 return {'key':key,'instance_type':kind,'slot':slot,'count':count,'header_flags':hex(flags),'full20':meta.hex(),'confirmation':confirm,'accepted':accept,'chosen_direct_quantity_field':chosen,'quantity_mode4_native_opened':opened_quantity,'quantity_ok_callback':'004CA470/control2/event20' if opened_quantity else None,'native27':[q.hex() for q in o.queued],'refusal_program_labels':list(o.refusals),'source_unchanged_before_reply':True,'inactive_clear_upper18_retained':True,'physical_domain':'direct selected-slot fixture; not live UI/owned authority admission'}

def quantity_control(o,key,kind,value=None):
 meta,before=o.fixture(key,kind,count=7);o.call(0x49a330,56,0x20)
 require(o.u32(UI+0x23d5e4)==4 and o.visible(8),'Quantity prerequisite not opened')
 if value is None:
  o.call(0x4ca470,3,0x20);require(not o.queued and not o.visible(8) and o.u32(UI+0x23d5e4)==0 and o.u32(UI+0x23d5e8)==0,'Quantity cancel did not close/reset')
 else:
  o.put(UI+0x23d5e8,'<I',value);o.call(0x4ca470,2,0x20)
  expected=[] if value==0 else [b'\x27'+struct.pack('<HBB',key,5,value&255)]
  require(o.queued==expected,'Quantity direct-input boundary differs')
 require(o.read(UI+0x8560c,1200)==before,'Quantity control altered source')
 return {'key':key,'type':kind,'case':'native_quantity_cancel' if value is None else 'direct_quantity_boundary_NOT_edit_reachability','direct_quantity_value':value,'max_native_quantity':7,'wire':[q.hex() for q in o.queued],'unchanged_full20':True,'scope':'Native callback/completion only. Quantity edit/input clamping not proven.'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=OUTPUT/'run01');ap.add_argument('--smoke',action='store_true');args=ap.parse_args();require(not args.output_dir.exists(),'NEW evidence directory required')
 previous={p:sha((ROOT/p).read_bytes()) for p in PREVIOUS};raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current client pin');current=pefile.PE(data=raw).get_memory_mapped_image();original=qualified_image()
 records,facts,source,visits=source_qualification(original,current);print('Qualified native armor8 + WPN/TWP/GEM/MED source396',flush=True);o=Discard(current,original,records)
 cases=[]
 if args.smoke:
  cases.append(execute(o,1201,2,5,1,0,0));cases.append(execute(o,1201,2,5,1,0,0,True));cases.append(execute(o,3107,0,5,7,0,0,True,True,3))
 else:
  for family,key,kind in FAMILIES:
   for slot in (0,5,29):
    for flags in (0,0x00400000,0x00800000,0x01000000,0x40000000,0x80000000,0xffc00000):
     for salt in (0,1):cases.append(execute(o,key,kind,slot,1,flags,salt))
   for accept in (True,False):cases.append(execute(o,key,kind,5,1,0,3,True,accept))
   for slot in (30,31,32,33,34,42,43,49):cases.append(execute(o,key,kind,slot,1,0,4))
   for count in (0,2,7,127,128,255):cases.append(execute(o,key,kind,5,count,0,0))
   for confirm in (False,True):
    for qty in (1,3,7):cases.append(execute(o,key,kind,5,7,0,0,confirm,True,qty))
   for value in (None,0,8,128,256):cases.append(quantity_control(o,key,kind,value))
  # Precise transient-window/busy refusals: same complete-instance source remains owned.
  guards=[]
  for field,label in ((0x232dce,578),(0x232e08,578),(0x232dfe,1643)):
   meta,before=o.fixture(1201,2);o.put(UI+field,'<h',10);o.flags(10,0x30);o.call(0x49a330,56,0x20)
   require(not o.queued and o.refusals==[label] and o.read(UI+0x8560c,1200)==before,'Visible window guard differs');guards.append({'widget_field':hex(field),'native_program_label':label,'no_queue_no_source_mutation':True});o.put(UI+field,'<h',-1)
  for busy in (1,0xffffffff):
   meta,before=o.fixture(1201,2);o.put(UI+0x866e4,'<I',busy);o.call(0x49a330,56,0x20);require(not o.queued and o.read(UI+0x8560c,1200)==before,'Producer busy gate differs');guards.append({'producer_busy':busy,'no_queue_no_source_mutation':True})
  cases.extend(guards)
 require(all(sha((ROOT/p).read_bytes())==h for p,h in previous.items()),'Frozen evidence changed');require(sha(LIVE.read_bytes())==PIN,'Client changed')
 used={a for a,n in o.visited};require(not set(TESTED)&set(o.helpers),'Tested function stubbed');require(set(TESTED)<=used,'Required native branch not executed '+str([hex(a) for a in set(TESTED)-used]));require(NativeLengths(original).query(0x41)[0]==5,'Native41 width')
 result={'status':'PASS','cases':len(cases),'native_cases':cases,'source_samples':facts,'source_pin':SOURCE_SHA,'decoded_pin':DECODED_SHA,'source_qualification':source,'client_sha256':sha(raw),'original_mapped_sha256':sha(original),'tool_sha256':sha(Path(__file__).read_bytes()),'native_instruction_matches':len(o.visited),'TWP_source_instruction_matches':len(visits),'executed_instruction_span_sha256':sha(b''.join(struct.pack('<II',a,n)+original[a-0x400000:a-0x400000+n] for a,n in sorted(o.visited))),'executed_instructions':[{'va':hex(a),'bytes':original[a-0x400000:a-0x400000+n].hex()} for a,n in sorted(o.visited)],'executed_not_stubbed':[hex(a) for a in TESTED],'external_adapters':[hex(a) for a in sorted(o.helpers)],'preserved_previous':previous,'scope':'Offline matched original/current machine; no UI/server/custody/grants/DB/client/runtime changes','OPEN':['Original server discard binding/protection rules','Original granted equipment/reserved-slot state','Live actual drag/event reachability; direct selected-slot fixtures do not establish it','Chosen quantity field direct inputs do not prove keyboard/edit control clamping','27 does not carry metadata20; server must authenticate existing owned source with complete20']}
 args.output_dir.mkdir(parents=True,exist_ok=False);(args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8');(args.output_dir/'contract.md').write_text(CONTRACT,'utf-8');print('PASS',len(cases),'native discard cases',flush=True);print('TOOL',result['tool_sha256']);print('EVIDENCE',sha((args.output_dir/'native.json').read_bytes()))

CONTRACT='''# Complete-instance native discard qualification

Native C2S27 logical5: opcode27, itemWORD, sourceBYTE, quantityBYTE. Queue4132E0 receives raw4 from496720 at496739; busyUI866E4 suppresses it. Full20 is absent and must be checked from authoritative existing custody, not forged from this request.

Actual49A330 callback control56/event20 drag release reaches49B3F3 selected855F0/key85610/count8560C; event1 click alone does not discard. Signed quantity >1 opens4C9820 mode4;4C9B70 executes actual quantity state.4CA470 control2/event20 ->4C9ED0 and4CA07C calls496720. Quantity callback control3/event20 cancels and4C9BD0/4C9C00 retire state. Actor449E bit10 opens4EAEF0, storingAFECC key/AFEC8 source/AFECF quantity/AFECE5.4EA770 control4 queues through4EA81E;control3 cancels;both call4EB620 and retire modeFF. Test-fixture renderer widget visibility and external formatting are adapters, not live Windows UI evidence. Some quantity choices are direct emulator inputs explicitly identified in JSON; the completion path itself only tests signed amount>0 and serializes lowBYTE, so direct max7/value8 or128 queues and256 queues0. This does not prove edit control clamping or actual UI reachability of those quantities; server must validate authoritative positive count/domain.

Six source-qualified namespaces EQU2/TEQ26/WPN1/TWP25/gem8/MED comparison execute matched original149c/currentc5 instructions. Same-ID different20, high header flags and byte19 controls are synthetic preservation cases, not generated/granted instances or native bind semantics. Native49B086..49B09B permits source0..29 or42/43; equipped30..34/other49 refuse ProgramMsg820. Reserved42/43 and count0/128/255 remain direct native selected-slot fixtures only; transport exposure must not grant them. Window fields232DCE/232E08 visible refuse578,232DFE visible refuses1643; busy866E4 refuses before the producer.

27 does not optimistically modify any raw24 bag cell; supplied absolute41 clears quantity and low key while retaining reserved bytes1..3 and now-inactive upper18 metadata. A zero-key/count slot with stale tail is empty, not an owned full20 instance. Originalserver destruction/bind/protection and actual live drag/quantity-edit reachability remain OPEN. Accepted scalar27 and previous bank evidence stay frozen.
'''
if __name__=='__main__':main()
