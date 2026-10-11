"""NEW armor bank full20/producer oracle. Offline only, never server authority.
Uses current c5d8 instructions and original70a source definitions. Actual data
consumers/producers execute; inherited presentation/queue boundaries are named.
"""
import argparse,hashlib,json,struct
from pathlib import Path
import pefile
from unicorn.x86_const import UC_X86_REG_EIP,UC_X86_REG_ESP
from tools.strike_lab.current_bank_items_20261002 import ItemsOracle
from tools.strike_lab.current_party_20261002 import UI,BODY,STOP
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
from tools.strike_lab.current_armor_20261002 import qualify_source,CAPTURE,ArmorMetadata
from tools.strike_lab import current_item_metadata as itemmeta,recover_companion_growth as growth
from tools.strike_lab.current_armor_equipped_attributes_20261002 import CONTRACT,LIVE,PIN,ROOT,require,sha
OUTPUT=ROOT/'artifacts/research/current-bank-armor-transport-20261002'
KEYS=(1201,1001,1501,1601,20201,20001,20501,20601)
PARTS=(30,31,32,33,30,31,32,33)
CATALOG,RECORDS=0x32000000,0x33000000

class BankSourceMetadata(ArmorMetadata):
 ITEM_SECTIONS=ArmorMetadata.ITEM_SECTIONS+('MIS02',)

class ArmorBank(ItemsOracle):
 def __init__(self,current,original,definitions):
  self.original=original;self.current=current;self.visited=set();self.refusals=[]
  super().__init__(current)
  del self.helpers[0x402c70] # Assertions fail; they are never presentation adapters.
  self.vm.mem_map(CATALOG+0xc0000,0x10000);self.vm.mem_map(RECORDS+0x1000,0x1000)
  companion=0x35000000;self.vm.mem_map(companion,0x22000)
  self.put(UI+0x232ebc,'<I',companion);self.put(companion+0x21236,'<B',255)
  for index,(key,record) in enumerate(definitions.items()):
   ptr=RECORDS+index*0x200;self.vm.mem_write(ptr,record);self.put(CATALOG+0xb2d40+key*4,'<I',ptr)
  self.put(UI+0x85abd,'<B',255)
 def hook(self,v,a,size,ctx):
  if a not in (STOP,STOP+16):
   require(0x400000<=a<0x400000+len(self.current),'Execution escaped executable')
   require(bytes(v.mem_read(a,size))==self.original[a-0x400000:a-0x400000+size],'Current/original instruction mismatch '+hex(a));self.visited.add((a,size))
  if a==0x402c70:raise RuntimeError('Native assertion '+hex(self.vm.reg_read(UC_X86_REG_EIP)))
  if a==0x475d60:self.refusals.append(self.u32(self.vm.reg_read(UC_X86_REG_ESP)+4))
  super().hook(v,a,size,ctx)
 def bag(self,slot):return UI+0x8560c+slot*24
 def snapshot48(self,page,slot,quantity,meta):
  body=bytes([page,0xa1,0xa2,0xa3,quantity,slot,0xb1,0xb2])+meta
  self.call(0x471e50,BODY,body=body);return b'\x48'+body
 def projection3b41(self,slot,meta):
  key=int.from_bytes(meta[:2],'little')
  packets=(b'\x41'+struct.pack('<HBB',0,slot,0),b'\x3b'+bytes([1,slot,0xa1,0xa2])+meta,b'\x41'+struct.pack('<HBB',key,slot,1))
  for wire in packets:self.call(0x498dd0 if wire[0]==0x3b else 0x4991e0,BODY,body=wire[1:])
  return [b.hex() for b in packets]

def instance(key,flags=0,salt=0):
 family=2 if key<19000 else 26
 data=bytearray(((salt+i*17)&255 for i in range(20)))
 struct.pack_into('<I',data,0,key|(family<<16)|flags)
 data[19]=(0,15,240,255)[salt%4]
 return bytes(data)

def defs(original,current):
 decoded,sections,declarations,source=qualify_source()
 cached=json.loads((ROOT/'artifacts/research/native-armor-20261002/records.json').read_text('utf-8'))
 rows={r[1]:r for r in cached[1]};out={};facts=[]
 old=itemmeta.CLIENT;itemmeta.CLIENT=CAPTURE
 try:n=BankSourceMetadata()
 finally:itemmeta.CLIENT=old
 import unicorn as uc
 def match(v,a,size,_):
  if n.active_code and a!=n.stop_address:require(bytes(v.mem_read(a,size))==current[a-0x400000:a-0x400000+size],'Definition current native differs')
 n.vm.hook_add(uc.UC_HOOK_CODE,match)
 for key,part in zip(KEYS,PARTS):
  row=rows[key];family=row[0];index=next(i for i,r in enumerate(n.sections[family]['records']) if int(growth.fields(r)[0])==key)
  record=n.item_row(family,index)['record'];require(record==bytes.fromhex(row[8]),'Regenerated source396 differs')
  require(bytes.fromhex(row[6])==bytes.fromhex(n.sections[family]['records'][index]['raw_record_hex']).rstrip(b'\r\n'),'Raw original row differs beyond terminal CRLF')
  out[key]=record;facts.append({'key':key,'source_family':family,'expected_instance_family':2 if family=='EQU' else 26,'physical_part':part,'source396_sha256':sha(record),'source_stack_flag':record[0x11b]&1,'source_raw_sha256':sha(bytes.fromhex(row[6]))})
 for family,key in (('MED02',3107),('WPN',1),('MIS02',16055)):
  index=next(i for i,r in enumerate(n.sections[family]['records']) if int(growth.fields(r)[0])==key)
  record=n.item_row(family,index)['record'];out[key]=record
  facts.append({'key':key,'source_family':family,'source396_sha256':sha(record),'source_stack_flag':record[0x11b]&1,'scope':'comparison source only; no authority or grants'})
 return out,facts,source

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=OUTPUT);args=ap.parse_args();require(not args.output_dir.exists(),'New evidence directory required')
 raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current client pin');current=pefile.PE(data=raw).get_memory_mapped_image();original=qualified_image()
 guards=json.loads(CONTRACT.read_text('utf-8'))['source_sha256'];require(all(sha((ROOT/f).read_bytes())==h for f,h in guards.items()),'Frozen runtime20 differs')
 previous=(ROOT/'tools/strike_lab/current_bank_items_20261002.py',ROOT/'artifacts/research/native-bank-items-20261002/oracle.json',ROOT/'tools/strike_lab/current_bank_20261002.py')
 previous_hash={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in previous}
 definitions,source_rows,source=defs(original,current)
 load=[];roundtrips=[];swaps=[];domains=[];visits=set()
 flags=(0,0x00400000,0x00800000,0x01000000,0x40000000,0x80000000,0xc0400000)
 # Armor-only full48 matrix: every ordinary bank cell2..49 on exposed pages0..2.
 for page in range(3):
  for slot in range(2,50):
   key=KEYS[(slot-2)%8];f=flags[(slot+page)%len(flags)];meta=instance(key,f,slot+page);other=instance(key,f,slot+page+1)
   o=ArmorBank(current,original,definitions);o.put(UI+0x839a4,'<I',page);at=o.cell(page,slot);o.vm.mem_write(at-1,b'\x5a'+bytes([0xcc])*24+b'\x6b')
   first=o.snapshot48(page,slot,1,meta);require(o.read(at,24)==bytes([1,slot,0xcc,0xcc])+meta,'48 armor full20 load differs')
   second=o.snapshot48(page,slot,1,other);require(meta!=other and o.read(at,24)==bytes([1,slot,0xcc,0xcc])+other,'Same-ID full20 replacement failed')
   clear=o.snapshot48(page,slot,0,bytes(20));require(o.read(at,24)==bytes([0,slot,0xcc,0xcc])+bytes(20),'48 literal full20 clear failed')
   require(o.read(at-1,1)==b'\x5a' and o.read(at+24,1)==b'\x6b','48 touched neighbor')
   require(o.u32(UI+0x839a8+page*4)==1,'48 cache qualification missing')
   load.append({'page':page,'slot':slot,'key':key,'instance_family':meta[2]&63,'flags':hex(f),'first_logical29':first.hex(),'same_id_different20':second.hex(),'clear_logical29':clear.hex(),'reserved2_3_unchanged':True,'neighbors_unchanged':True});visits.update(o.visited)
 # Consumers are supplied explicit server-owned fixture metadata; no grant claim.
 for index,key in enumerate(KEYS):
  page=index%3;slot=2 if index%2==0 else 49;meta=instance(key,flags[index%len(flags)],index+3)
  o=ArmorBank(current,original,definitions);o.put(UI+0x839a4,'<I',page)
  projection=o.projection3b41(5,meta);bag=o.read(o.bag(5),24);require(bag[0]==1 and bag[4:]==meta,'Bag full3B41 armor differs')
  o.put(UI+0x855f0,'<h',5);o.call(0x4723a0,slot,1);deposit=b'\x63'+struct.pack('<HBBBB',3793,page,5,slot,1)
  require(o.queued==[deposit] and o.read(o.bag(5),24)==bag,'Native63 direction or optimistic mutation differs')
  o.snapshot48(page,slot,1,meta);o.call(0x4991e0,BODY,body=struct.pack('<HBB',0,5,0));clearedbag=o.read(o.bag(5),24)
  require(clearedbag[0]==0 and clearedbag[4:6]==bytes(2) and clearedbag[6:]==meta[2:],'41 inactive metadata behavior differs')
  vault=o.read(o.cell(page,slot),24);o.queued.clear();o.put(UI+0x83994,'<h',slot);o.call(0x49f010,0x17,7,1);withdraw=b'\x64'+struct.pack('<HBBBB',3793,page,slot,7,1)
  require(o.queued==[withdraw] and o.read(o.cell(page,slot),24)==vault,'Native64 direction or optimistic vault mutation differs')
  restored=o.projection3b41(7,meta);o.snapshot48(page,slot,0,bytes(20))
  require(o.read(o.bag(7),24)[0]==1 and o.read(o.bag(7),24)[4:]==meta,'Restored bag lost20bytes')
  require(o.read(o.cell(page,slot),24)[4:]==bytes(20),'Vault clear metadata retained')
  roundtrips.append({'key':key,'part':PARTS[index],'page':page,'bank_slot':slot,'metadata20_hex':meta.hex(),'bag_projection':projection,'C2S63':deposit.hex(),'C2S64':withdraw.hex(),'restored_bag_projection':restored,'restored_metadata_exact':True,'inactive_source_bag_upper18_retained':True,'server_replies':'explicit fixture sequence, not recovered original transaction rule'});visits.update(o.visited)
 for index,key in enumerate(KEYS):
  page=index%3;left=instance(key,flags[index%len(flags)],index);right=instance(key,flags[(index+1)%len(flags)],index+1)
  o=ArmorBank(current,original,definitions);o.put(UI+0x839a4,'<I',page);o.snapshot48(page,2,1,left);o.snapshot48(page,49,1,right)
  o.vm.mem_write(o.cell(page,2)+2,b'\x12\x34');o.vm.mem_write(o.cell(page,49)+2,b'\x56\x78');before=(o.read(o.cell(page,2),24),o.read(o.cell(page,49),24))
  o.put(UI+0x83994,'<h',2);o.call(0x4719b0,49,1);wire=b'\x65'+struct.pack('<HBBBB',3793,page,2,49,1)
  require(o.queued==[wire] and o.read(o.cell(page,2),24)==before[1] and o.read(o.cell(page,49),24)==before[0],'65 did not swap whole distinct same-ID cells')
  o.snapshot48(page,2,1,right);o.snapshot48(page,49,1,left)
  require(o.read(o.cell(page,2),24)[1]==2 and o.read(o.cell(page,49),24)[1]==49,'Authoritative48 did not canonicalize cell index')
  swaps.append({'key':key,'page':page,'C2S65':wire.hex(),'before_raw24':[b.hex() for b in before],'whole24_swap_exact':True,'native_local_slot_byte_swapped_not_reindexed':True,'authoritative48_canonical_slot_corrected':True});visits.update(o.visited)
 comparison=((1201,2),(20201,26),(3107,0),(1,1),(16055,8))
 for key,family in comparison:
  canonical_high=0x04000000 if key==16055 else 0
  for high in ((0,0x80000000,canonical_high) if canonical_high else (0,0x80000000)):
   for source_slot in (5,30):
    for dest in (0,1,2,49):
     o=ArmorBank(current,original,definitions);o.put(UI+0x839a4,'<I',2);o.put(UI+0x855f0,'<h',source_slot);meta=struct.pack('<I',key|(family<<16)|high)+bytes(range(4,20));o.vm.mem_write(o.bag(source_slot),bytes([1,0,0,0])+meta)
     o.call(0x4723a0,dest,1);allowed=source_slot==5 and dest>=2;require(bool(o.queued)==allowed,'Native63 family/physical domain differs')
     if allowed:require(o.queued==[b'\x63'+struct.pack('<HBBBB',3793,2,source_slot,dest,1)],'Native63 raw fields differ')
     domains.append({'producer':'63','key':key,'family':family,'header_flags':hex(high),'bit31':bool(high&0x80000000),'source_slot':source_slot,'bank_dest':dest,'queued':[b.hex() for b in o.queued],'refusal_program_labels':o.refusals});visits.update(o.visited)
  for dest in (0,29,30,42,43):
   o=ArmorBank(current,original,definitions);o.put(UI+0x839a4,'<I',2);meta=struct.pack('<I',key|(family<<16)|canonical_high)+bytes(range(4,20));o.snapshot48(2,2,1,meta);o.put(UI+0x83994,'<h',2);o.call(0x49f010,0x17,dest,1)
   require(bool(o.queued)==(dest in (0,29,42,43)),'Native64 physical destination domain differs')
   domains.append({'producer':'64','key':key,'family':family,'bag_dest':dest,'queued':[b.hex() for b in o.queued],'qualification':'42/43 are native caller transport destinations, not armor owner admission'});visits.update(o.visited)
  o=ArmorBank(current,original,definitions);o.put(UI+0x839a4,'<I',2);meta=struct.pack('<I',key|(family<<16)|canonical_high)+bytes(range(4,20));o.snapshot48(2,2,1,meta);o.snapshot48(2,49,1,instance(1201,0,10));o.put(UI+0x83994,'<h',2);o.call(0x4719b0,49,1)
  require(o.queued==[b'\x65'+struct.pack('<HBBBB',3793,2,2,49,1)] and o.read(o.cell(2,49),24)[4:]==meta,'Native65 domain differs')
  domains.append({'producer':'65','key':key,'family':family,'destination_family':2,'queued':[b.hex() for b in o.queued],'whole_cell_moved':True});visits.update(o.visited)
 o=ArmorBank(current,original,definitions);stale=bytes(2)+bytes([0xa5])*18;o.snapshot48(2,49,0,stale);require(o.read(o.cell(2,49),24)[4:]==stale,'48 falsely assumed auto-zero on quantity0');visits.update(o.visited)
 require(all(sha((ROOT/f).read_bytes())==h for f,h in guards.items()),'Frozen runtime20 changed after oracle');require(all(sha((ROOT/f).read_bytes())==h for f,h in previous_hash.items()),'Previous bank tool/evidence changed')
 tested=(0x471e50,0x498dd0,0x4991e0,0x4723a0,0x4722b0,0x471d40,0x49f010,0x497510,0x4975f0,0x4977b0)
 require(not any(a in o.helpers for a in tested),'Tested gameplay helper was stubbed')
 require(set(tested+(0x49b850,0x459a60)).issubset({a for a,n in visits}),'Expected data/definition function was not executed')
 result={'status':'PASS','scope':'Offline x86 copied-metadata/caller proof, queue/presentation endpoints adapted; NOT live UI, original bank authority/unlock/bind/transaction acceptance','cases':len(load)+len(roundtrips)+len(swaps)+len(domains)+1,'client_sha256':sha(raw),'mapped_original_sha256':sha(original),'source':source,'source_rows':source_rows,'armor48_cases':load,'roundtrip_cases':roundtrips,'same_id65_swap_cases':swaps,'producer_domain_cases':domains,'qty_zero_nonzero_metadata_control':'48 copies all20 even quantity0. Explicit zero20 is needed to clear inactive metadata.','native_widths':{hex(x):NativeLengths(original).query(x)[0] for x in (0x48,0x3b,0x41)},'executed_matched_instructions':len(visits),'tested_functions_not_stubbed':list(map(hex,tested)),'adapter_addresses':list(map(hex,sorted(o.helpers))),'frozen_runtime20_preserved':True,'previous_bank_tool_evidence_sha256_preserved':previous_hash,'tool_sha256':sha(Path(__file__).read_bytes()),'limits':['No original bank ownership/shared-account/capacity/grant/bind rule recovered','Instance fixture arbitrary20 bytes and high flags are transport controls, not valid original grants','Current-source EQU/TEQ exact unchanged1354 rows; no item->appearance/stat producer added','Native64 exposes42/43 transport destinations without testing source armor admission there; server ordinary bag scope still must be explicit','No UI/server/network/process/DB/client writes']}
 args.output_dir.mkdir(parents=True,exist_ok=False);(args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8');(args.output_dir/'contract.md').write_text(CONTRACT_TEXT,'utf-8')
 print('PASS',result['cases'],'new armor bank metadata/domain cases');print('Tool SHA256',result['tool_sha256']);print('Evidence SHA256',sha((args.output_dir/'native.json').read_bytes()))

CONTRACT_TEXT="""# Armor bank full20 native transport

Scope: current c5d8 original x86 functions, captured original70a4 parsed definitions, current EQU/TEQ1354 exact-equal rows. Arbitrary instance operands and flags are synthetic transport inputs, NOT recovered grants. Presentation and queue endpoints are inherited explicit adapters. No real UI or authoritative banking acceptance is claimed.

S2C48 logical29: page@1, opaque3@2..4, qty@5, slot@6, opaque2@7..8, metadata20@9. 471E50 writes ALL20, quantity and canonical physical slot byte. Reserved native raw-cell bytes2/3 remain local unchanged. All48 physical slots2..49, pages0..2, allfour EQU2/TEQ26 part samples, byte19 00/0F/F0/FF, high header flags and same-ID distinct20 replace/clear pass. UI resources/unlock are not proven. Six backing pages exist; caller only exposes two/three by edition as previously verified.

Original3B copies all20 and may force1 or add based on definition stack bit. Exact projection clear41 ->3B ->absolute41 supplies quantity1 metadata losslessly. Empty41 clears quantity/key only, retains inactive upper18 metadata. In contrast a zero20 S2C48 explicitly clears allmetadata20;48 does not auto-zero solely because qty0. Do not identify inactive bag bytes as an owned live instance.

Native bag-drop4723A0->63 checks family bits16..21 through4722B0. For armor2/26, MED0, WPN1 and gem8, ordinary bag sources0..29 can target bank2..49; bank0/1 reject. Equipped source30 rejects. bit31 alone does not change this machine bank check, but its original binding/transfer semantics remain UNKNOWN and require separate explicit authority policy.

Native bank-drop49F010 mode17->64 permits destination0..29 or42/43 by physical caller range, not family authorization. Ordinary armor scope must stay bag0..29;42/43 transport permission is not proof they are correct armor destinations. 63/64 quantity1 calls do not optimistically mutate owned source cells. Wire contains only target/page/source/destination/count, no metadata. Server must resolve exact owned full20, never derive instance from packet item ID.

Native bank-drag4719B0->65 tail1 swaps WHOLE raw24 cells, including distinct metadata20, local reserved bytes and stored slot byte, even when IDs match. Tail1 is not a request to move one item from a stack. Subsequent authoritative48 correctly rewrites canonical slot identity while copying all20. Root storage should persist ownership/quantity/full20 and reconstruct canonical physical cells, not preserve local reserved/index bytes as authority. Both occupied sides must be qualified; native transport does not establish shared-bank/account/access/grant rules.

CUSTOM-0067 foundation can use these exact transports with explicit per-character ownership, strict itemkey/family matching, scalar quantity1 armor, bounded ordinary slots/pages and transaction/CAS policy; those server rules are CUSTOM, not original banking formulas. Live current-client validation remains mandatory before activation.
"""
if __name__=='__main__':main()
