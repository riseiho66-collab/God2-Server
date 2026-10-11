"""New bounded current x86 bank weapon/gem data transport proof, offline only.

All1259 source rows regenerate with original native ItemType binding. High
header fields are synthetic preservation controls, never original bind policy.
Queue/presentation adapters are inherited explicitly; no live UI acceptance.
"""
import argparse,json,struct
from pathlib import Path
from collections import Counter
import pefile,unicorn as uc
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EIP
from tools.strike_lab.current_bank_armor_transport_20261002 import ArmorBank,ROOT,LIVE,PIN,require,sha,itemmeta,growth,CAPTURE
from tools.strike_lab.current_deity_metadata import NativeDeityMetadata
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
from tools.strike_lab.current_party_20261002 import UI,BODY,STACK
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.import_native_weapons import validate_records

OUTPUT=ROOT/'artifacts/research/current-bank-weapon-gem-transport-20261003'
PREVIOUS=(ROOT/'tools/strike_lab/current_bank_armor_transport_20261002.py',ROOT/'artifacts/research/current-bank-armor-transport-20261002/run02/native.json',ROOT/'artifacts/research/current-bank-armor-transport-20261002/run02/contract.md')
SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED_SHA='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'

class Source(NativeDeityMetadata):
 ITEM_SECTIONS=('GOD','WPN','TWP','MIS02')
 CODE=NativeDeityMetadata.CODE+((0x9b5e0,0x9b662),)
 def section_selector(self,section):return self.lookup_section(section)[1]

class Bank(ArmorBank):
 def __init__(self,current,original,definitions):
  super().__init__(current,original,{})
  self.vm.mem_map(STACK+0x1000,0x9000) # Actual tooltip frame locals extend beyond the small inherited caller stack.
  capacity=((len(definitions)*0x200+4095)//4096)*4096
  if capacity>0x2000:self.vm.mem_map(0x33002000,capacity-0x2000)
  for i,(key,record) in enumerate(definitions.items()):
   ptr=0x33000000+i*0x200;self.vm.mem_write(ptr,record);self.put(0x32000000+0xb2d40+key*4,'<I',ptr)
 def reset(self,page=0):
  self.queued.clear();self.refusals.clear();self.vm.mem_write(UI+0x8560c,bytes(50*24));self.vm.mem_write(UI+0x839cc,bytes(300*24));self.put(UI+0x839a4,'<I',page);self.put(UI+0x83994,'<h',-1)

def source(current):
 raw=(CAPTURE/'Data2/Patch/Comm/gamedata.csvZ').read_bytes();require(sha(raw)==SOURCE_SHA,'Original source pin');decoded=decode_csvz(raw);require(sha(decoded)==DECODED_SHA,'Original decoded pin')
 live=decode_csvz((LIVE.parent/'Data2/Patch/Comm/gamedata.csvZ').read_bytes());current_sections=growth.parse_sections(live,('WPN','TWP','MIS02'))
 old=itemmeta.CLIENT;itemmeta.CLIENT=CAPTURE
 try:n=Source()
 finally:itemmeta.CLIENT=old
 matched=set()
 def match(v,a,size,_):
  if n.active_code and a!=n.stop_address:require(bytes(v.mem_read(a,size))==current[a-0x400000:a-0x400000+size],'Current source instruction differs');matched.add((a,size))
 n.vm.hook_add(uc.UC_HOOK_CODE,match)
 cached=json.loads((ROOT/'artifacts/research/native-weapons-20260926/records.json').read_text('utf-8'))
 normalized=[[[bytes.fromhex(v) if gi==1 and i in (6,8) else v for i,v in enumerate(row)] for row in group] for gi,group in enumerate(cached)]
 validate_records(normalized);lookup={row[1]:row for row in cached[1]}
 definitions={};facts=[];bindings={}
 for family,count,expected in (('WPN',630,(0,1)),('TWP',629,(35,25)),('MIS02',2226,(33,24))):
  rows=n.sections[family]['records'];require(len(rows)==count,'Source denominator');require([r['raw_record_hex'] for r in rows]==[r['raw_record_hex'] for r in current_sections[family]['records']],'Current source rows changed')
  actual=n.lookup_section(family);require(actual==expected,'Original namespace binding differs');bindings[family]={'ordinal':actual[0],'loader_selector':actual[1],'raw_row_count':count,'current_raw_rows_exact':True}
  for i,row in enumerate(rows):
   key=int(growth.fields(row)[0])
   if family=='MIS02' and key!=16055:continue
   parsed=n.item_row(family,i);record=parsed['record'];definitions[key]=record
   if family!='MIS02':require(lookup[key][0]==family and record==bytes.fromhex(lookup[key][8]) and bytes.fromhex(lookup[key][6])==bytes.fromhex(row['raw_record_hex']).rstrip(b'\r\n'),'All1259 native/source cache equality failed')
   facts.append({'key':key,'family':family,'source_index':i,'source_line':row['source_line'],'instance_type':1 if family=='WPN' else 25 if family=='TWP' else 8,'source_flags11A':record[0x11a],'source_flags11B':record[0x11b],'source_stack':bool(record[0x11b]&1),'source396_sha256':sha(record),'raw_row_sha256':sha(bytes.fromhex(row['raw_record_hex']))})
 require(len(definitions)==1260,'Source+gem total');return definitions,facts,bindings,matched

def metadata(key,kind,header_extra,salt,byte19):
 b=bytearray(((salt+i*29)&255 for i in range(20)));struct.pack_into('<I',b,0,key|(kind<<16)|header_extra);b[19]=byte19;return bytes(b)

def roundtrip(o,key,kind,extra,salt,byte19,tag):
 page=salt%3;bank_slot=2+(salt//3)%48;o.reset(page);left=metadata(key,kind,extra,salt,byte19)
 projection=o.projection3b41(5,left);bag=o.read(o.bag(5),24);require(bag[0]==1 and bag[4:]==left,'3B41 full metadata lost')
 o.put(UI+0x855f0,'<h',5);o.call(0x4723a0,bank_slot,1);deposit=b'\x63'+struct.pack('<HBBBB',3793,page,5,bank_slot,1)
 require(o.queued==[deposit] and o.read(o.bag(5),24)==bag,'Native63 fields/local mutation differs')
 o.snapshot48(page,bank_slot,1,left);o.call(0x4991e0,BODY,body=struct.pack('<HBB',0,5,0));saved=o.read(o.cell(page,bank_slot),24);require(saved[4:]==left,'48 lost full20')
 o.queued.clear();o.put(UI+0x83994,'<h',bank_slot);o.call(0x49f010,0x17,7,1);withdraw=b'\x64'+struct.pack('<HBBBB',3793,page,bank_slot,7,1)
 require(o.queued==[withdraw] and o.read(o.cell(page,bank_slot),24)==saved,'64 fields/local mutation differs')
 o.projection3b41(7,left);require(o.read(o.bag(7),24)[4:]==left,'Restored bag altered full20')
 # Same ID, intentionally distinct full20; native65 swaps the complete cells.
 target=49 if bank_slot!=49 else 2;right=metadata(key,kind,extra,salt+1,byte19^255);o.snapshot48(page,target,1,right)
 o.vm.mem_write(o.cell(page,bank_slot)+2,b'\x12\x34');o.vm.mem_write(o.cell(page,target)+2,b'\x56\x78');before=(o.read(o.cell(page,bank_slot),24),o.read(o.cell(page,target),24))
 o.queued.clear();o.put(UI+0x83994,'<h',bank_slot);o.call(0x4719b0,target,1);move=b'\x65'+struct.pack('<HBBBB',3793,page,bank_slot,target,1)
 require(o.queued==[move] and o.read(o.cell(page,bank_slot),24)==before[1] and o.read(o.cell(page,target),24)==before[0],'65 same-ID complete raw24 swap differs')
 o.snapshot48(page,bank_slot,1,right);o.snapshot48(page,target,1,left);require(o.read(o.cell(page,bank_slot),24)[1]==bank_slot and o.read(o.cell(page,target),24)[1]==target and o.read(o.cell(page,target),24)[4:]==left,'48 canonical reconstruction differs')
 o.snapshot48(page,bank_slot,0,bytes(20));o.snapshot48(page,target,0,bytes(20));require(o.read(o.cell(page,bank_slot),24)[4:]==bytes(20) and o.read(o.cell(page,target),24)[4:]==bytes(20),'48 explicit clear differs')
 return {'case':tag,'key':key,'instance_type':kind,'header_extra':hex(extra),'byte19':byte19,'page':page,'source_bank_slot':bank_slot,'target_bank_slot':target,'metadata20_hex':left.hex(),'same_id_other20_hex':right.hex(),'native_C2S63':deposit.hex(),'native_C2S64':withdraw.hex(),'native_C2S65':move.hex(),'full20_roundtrip_same_id_swap_clear_canonical_PASS':True,'reply_scope':'Explicit fixture-owned snapshot sequence; no original server causality'}

def dispatch(o,value):
 expected_type=(value>>16)&63;idx=o.original[0xbc1d0+expected_type-1];target=struct.unpack_from('<I',o.original,0xbc188+idx*4)[0]
 o.vm.reg_write(UC_X86_REG_EAX,value);o.vm.reg_write(UC_X86_REG_EBP,UI);o.vm.reg_write(UC_X86_REG_ESP,STACK+0x8000);o.vm.emu_start(0x4b6424,target,count=100)
 require(o.vm.reg_read(UC_X86_REG_EIP)==target,'Native type dispatch did not reach expected target');return {'type':expected_type,'target':hex(target),'native_dispatch_executed':True}

def gem_display(o,value):
 sp=STACK+0x8000;o.vm.mem_write(sp-0x80,bytes(0x1800));o.put(sp+0x11a4,'<I',16055);o.vm.reg_write(UC_X86_REG_EAX,value);o.vm.reg_write(UC_X86_REG_EBP,UI);o.vm.reg_write(UC_X86_REG_ESP,sp)
 stops={0x4b887a,0x4bbbce};hook=o.vm.hook_add(uc.UC_HOOK_CODE,lambda v,a,n,d:v.emu_stop() if a in stops else None)
 try:o.vm.emu_start(0x4b6424,0,count=1000)
 finally:o.vm.hook_del(hook)
 count=value>>25;pc=o.vm.reg_read(UC_X86_REG_EIP);shown=1<=count<=10;require(pc==(0x4b887a if shown else 0x4bbbce),'Original charge display gate')
 if shown:
  args=struct.unpack('<5I',o.vm.mem_read(o.vm.reg_read(UC_X86_REG_ESP),20));require(args[1:]==(0x5927f4,0x36002000,count,0x36002100),'Actual charge format args differ')
 return {'count_bits25_31':count,'displayed':shown,'actual_formatter_count':count if shown else None,'stop_before_external_sprintf':hex(pc)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=OUTPUT);args=ap.parse_args();require(not args.output_dir.exists(),'New evidence directory required')
 previous={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in PREVIOUS};raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current client changed');current=pefile.PE(data=raw).get_memory_mapped_image();original=qualified_image()
 definitions,facts,bindings,parsed_visits=source(current);print('Qualified native1259 source rows + gem16055',flush=True);o=Bank(current,original,definitions)
 o.vm.mem_map(0x36000000,0x4000);o.put(0x32000000+0xb2c68,'<I',0x36000000);o.put(0x32000000+0xb2c6c,'<H',1080)
 for ident,address in ((890,0x36002000),(891,0x36002100)):o.put(0x36000000+(ident-1)*4,'<I',address);o.vm.mem_write(address,b'EXPLICIT_FORMAT_BOUNDARY\0')
 cases=[];weapon_facts=[row for row in facts if row['family']!='MIS02'];source_flags=Counter((r['family'],r['source_flags11A'],r['source_flags11B']) for r in weapon_facts)
 for i,row in enumerate(weapon_facts):cases.append(roundtrip(o,row['key'],row['instance_type'],((i%1024)<<22),i,(0,15,240,255)[i%4],'all1259_original_source_rows'))
 print('Passed1259 per-item bank roundtrips',flush=True)
 # Exhaust all ten non-type header bits for both source namespaces, not a
 # speculative bind interpretation. The original bank checks only type bits.
 for family,key,kind in (('WPN',1,1),('TWP',19001,25)):
  for flags in range(1024):cases.append(roundtrip(o,key,kind,flags<<22,flags,(0,15,240,255)[flags%4],'all1024_high_header_'+family))
 print('Passed2048 exhaustive weapon high-header cases',flush=True)
 gem=[]
 for charge in range(1,11):
  for flags in range(8):
   for byte19 in (0,15,240,255):
    extra=(charge<<25)|(flags<<22);n=len(gem);result=roundtrip(o,16055,8,extra,n,byte19,'gem_all_valid_charges_flags_byte19');result['charge_display']=gem_display(o,16055|(8<<16)|extra);gem.append(result)
 invalid=[gem_display(o,16055|(8<<16)|(count<<25)) for count in (0,11,127)]
 dispatches=[dispatch(o,key|(kind<<16)) for key,kind in ((1,1),(19001,25),(16055,8))]
 domains=[]
 for key,kind,extra in ((1,1,0),(19001,25,0),(16055,8,10<<25)):
  for source_slot in (0,29,30,34,42,43):
   for dest in (0,1,2,49):
    o.reset(2);data=metadata(key,kind,extra,3,255);o.vm.mem_write(o.bag(source_slot),bytes([1,0,0,0])+data);o.put(UI+0x855f0,'<h',source_slot);o.call(0x4723a0,dest,1)
    allowed=source_slot in (0,29) and dest>=2;require(bool(o.queued)==allowed,'63 measured physical/type domain changed');domains.append({'producer':'63','key':key,'type':kind,'source':source_slot,'dest':dest,'queued':[v.hex() for v in o.queued],'refusal_program_labels':list(o.refusals),'not_server_authority':True})
  for source_slot in (0,1,2,49):
   for dest in (0,29,30,34,42,43):
    o.reset(2);o.snapshot48(2,source_slot,1,metadata(key,kind,extra,3,255));o.put(UI+0x83994,'<h',source_slot);o.call(0x49f010,0x17,dest,1);allowed=dest in (0,29,42,43);require(bool(o.queued)==allowed,'64 measured physical domain changed');domains.append({'producer':'64','key':key,'type':kind,'source':source_slot,'dest':dest,'queued':[v.hex() for v in o.queued],'not_server_authority':True})
  for source_slot,dest in ((0,2),(1,2),(2,0),(2,1),(2,49)):
   o.reset(2);o.snapshot48(2,source_slot,1,metadata(key,kind,extra,3,255));o.snapshot48(2,dest,1,metadata(key,kind,extra,4,0));before=(o.read(o.cell(2,source_slot),24),o.read(o.cell(2,dest),24));o.put(UI+0x83994,'<h',source_slot);o.call(0x4719b0,dest,1);allowed=dest>=2;require(bool(o.queued)==allowed,'65 special destination guard changed');require((o.read(o.cell(2,source_slot),24),o.read(o.cell(2,dest),24))==(before[::-1] if allowed else before),'65 special-domain raw24 mutation changed');domains.append({'producer':'65','key':key,'type':kind,'source':source_slot,'dest':dest,'queued':[v.hex() for v in o.queued],'refusal_program_labels':list(o.refusals),'whole24_swap_if_queued':allowed,'not_server_authority':True})
 require(all(sha((ROOT/p).read_bytes())==h for p,h in previous.items()),'Previous accepted279 evidence/tool changed');require(sha(LIVE.read_bytes())==PIN,'Client changed after oracle')
 tested=(0x471e50,0x498dd0,0x4991e0,0x4723a0,0x4722b0,0x471d40,0x49f010,0x497510,0x4975f0,0x4977b0,0x459a60,0x49b850,0x4b6424,0x4ba6f4)
 require(not set(tested).intersection(o.helpers) and set(tested).issubset({a for a,n in o.visited}),'Consumer/producer unexpectedly stubbed or not executed')
 result={'status':'PASS','scope':'Original/current x86 transport and raw source qualification only; no live UI, server bind/ownership/shared bank/transfer policy','cases':len(cases)+len(gem)+len(invalid)+len(dispatches)+len(domains),'weapon_cases':cases,'gem_cases':gem,'invalid_charge_display_controls':invalid,'native_instance_type_dispatch':dispatches,'domain_cases':domains,'source_rows':facts,'source_binding':bindings,'source_flag_classes':[{'family':f,'flags11A':a,'flags11B':b,'rows':count} for (f,a,b),count in sorted(source_flags.items())],'client_sha256':sha(raw),'native_image_sha256':sha(original),'source_sha256':SOURCE_SHA,'decoded_sha256':DECODED_SHA,'source_native_instruction_matches':len(parsed_visits),'consumer_native_instruction_matches':len(o.visited),'native_widths_S2C':{hex(x):NativeLengths(original).query(x)[0] for x in (0x48,0x3b,0x41)},'executed_not_stubbed':[hex(x) for x in tested],'presentation_queue_adapters':[hex(x) for x in sorted(o.helpers)],'previous_279_evidence_and_tool_preserved':previous,'tool_sha256':sha(Path(__file__).read_bytes()),'OPEN':['No original bank binding/tradability/charge debit/shared account/ownership/access policy','No server source-row to firstDWORD instance generation rule','Physical native42/43/special0/1 transport cases do not admit inventory slots or grant items','WPN1/TWP25 original tooltip dispatch paths do not prove any stats/appearance generation','No UI/pixels/process/network/DB/client/runtime changes']}
 args.output_dir.mkdir(parents=True,exist_ok=False);(args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8');(args.output_dir/'contract.md').write_text(CONTRACT,'utf-8');print('PASS',result['cases'],'new native weapon/gem bank cases');print('Tool',result['tool_sha256']);print('Evidence',sha((args.output_dir/'native.json').read_bytes()))

CONTRACT="""# WPN / TWP / gem bank transport, new evidence

Current c5d8 and original149c instructions match at every executed source loader, data consumer and native producer. All original630 WPN +629 TWP source rows regenerate396 and exactly equal accepted original cached records; current source rows remain exact. ItemType original59380 gives WPN ordinal0 selector1, TWP ordinal35 selector25, MIS02 ordinal33 selector24. The gem instance still has type8; source selector24 is not instance type24. Source396 firstDWORDs are source operands, not an instance header generator.

S2C48 logical29: pageBYTE@1, opaque3@2..4, quantityBYTE@5, slotBYTE@6, opaque2@7..8, full20@9. Bank cells raw24 = quantity, stored-slot, local-reserved2, full20. Exact load/overwrite/clear, same-ID distinct20, raw24 whole65 swap and canonical48 reconstruction execute. All1259 weapon rows, both namespaces' all1024 header flags bits22..31, gem charges1..10 and all8 noncharge flag combinations bits22..24 with byte19 00/0F/F0/FF are preservation controls. Instance operands are synthetic controls, not original generated/granted weapons.

3B logical25 copies all20; clear41 then3B thenabsolute41 supplies count1 without stacking ambiguity. Empty41 preserves now-inactive upper18 bytes, so it is not an owned live instance. Zero20 explicit48 clears vault metadata. Native63/64 count1 leave source data unchanged until supplied authoritative fixture replies. 65 queues tail1 while swapping complete raw24, not a quantity-one stack action.

C2S63/64/65 each logical7: opcode, targetWORD@1, pageBYTE@3, sourceBYTE@4, destinationBYTE@5, quantity/tailBYTE@6. 63 native WPN1/TWP25/gem8 target bank2..49, not0/1; measured ordinary bag0/29 permit, equipped30/34 reject ProgramMsg869, special42/43 reject647. 64 exposes selected-bank0/1 as well as2/49 with destination ordinary0/29/42/43 (30/34 reject). This mechanical exposure never establishes that weapon/gem instances can originally occupy bank0/1 or special inventory42/43. 65 category guard checks the destination: source0/1 to ordinary2 queues and raw24 swaps, while source2 to destination0/1 rejects841. The prior279 accepted oracle did not test63 source42/43 or65 special sources; it remains preserved. Server support must keep explicit ordinary-bank/bag authority bounds rather than infer permissions from the native sender.

Gem16055 original type8 consumer4B6424 ->4BA6F4 extracts header>>25, displays only1..10, preserves bits22..24 and byte19. 0/11/127 omit the charge display; they are not valid usable-instance grants. A source qualifier can use complete original-source NativeWeaponCatalog record/key + WPN/TWP namespace + source equipment bit, separately retain full20 and explicit owned count1; exact type1/25 matching is an explicit authority admission policy consistent with native dispatch, not an original server-generation rule. Gem qualifier requires key16055/type8/known1..10 charge display domain plus complete owned full20. No bank transfer should debit charges based on these transport observations.

Original bind/transfer rules, shared bank scope, access, generation, granted ownership, and live-client acceptance remain OPEN. This tool does not enable a formal route or modify any earlier accepted evidence.
"""
if __name__=='__main__':main()
