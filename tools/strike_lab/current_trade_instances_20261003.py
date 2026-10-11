"""NEW offline current/original PLAYER TRADE full-instance transport oracle.

Original native source parsing, 2A caller/producer, and 50 full24 consumer run.
Only external renderer/socket boundaries adapted. No server admission/grants.
"""
import argparse,json,struct
from pathlib import Path
from collections import Counter
import pefile
from unicorn.x86_const import UC_X86_REG_ESP
from tools.strike_lab.current_bank_weapon_gem_transport_20261003 import Bank,Source,ROOT,LIVE,PIN,sha,require,metadata,CAPTURE,itemmeta,growth,SOURCE_SHA,DECODED_SHA
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
from tools.strike_lab.current_party_20261002 import UI,BODY
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.import_native_weapons import validate_records as validate_weapons
from tools.strike_lab.import_native_armor_20261002 import validate_records as validate_armor

OUT=ROOT/'artifacts/research/current-trade-instances-20261003'
FROZEN=(ROOT/'tools/strike_lab/current_trade_20261002.py',ROOT/'tools/strike_lab/current_bank_weapon_gem_transport_20261003.py',ROOT/'artifacts/research/current-bank-weapon-gem-transport-20261003/run03/native.json')

class Sources(Source):
 ITEM_SECTIONS=('GOD','WPN','TWP','MIS02','EQU','TEQ')
 def __init__(self,current):
  self.current=current;self.matches=set();super().__init__()
 def _code(self,v,a,size,ctx):
  super()._code(v,a,size,ctx)
  if self.active_code and a!=self.stop_address:
   require(bytes(v.mem_read(a,size))==self.current[a-0x400000:a-0x400000+size],'Original/current source instruction mismatch '+hex(a));self.matches.add((a,size))

class Trade(Bank):
 def __init__(self,current,original,defs):
  super().__init__(current,original,defs)
  self.draws=[];self.helpers.update({0x49b820:24})
  for offset,widget in ((0x232dae,1),(0x232db0,2),(0x232db2,3),(0x232db4,4)):
   self.put(UI+offset,'<h',widget);self.flags(widget,0x10)
  self.put(UI+0x866d0,'<H',0x1234)
 def reset_trade(self):
  self.queued.clear();self.refusals.clear();self.draws.clear()
  self.vm.mem_write(UI+0x8560c,bytes(50*24));self.vm.mem_write(UI+0x866e8,bytes(384));self.put(UI+0x866e0,'<I',0);self.put(UI+0x855f0,'<h',-1)
 def hook(self,v,a,size,ctx):
  if a==0x5068c0:
   self.draws.append(list(struct.unpack('<4I',self.read(v.reg_read(UC_X86_REG_ESP)+4,16))))
  super().hook(v,a,size,ctx)

def definitions(current):
 raw=(CAPTURE/'Data2/Patch/Comm/gamedata.csvZ').read_bytes();require(sha(raw)==SOURCE_SHA,'Original source changed');plain=decode_csvz(raw);require(sha(plain)==DECODED_SHA,'Decoded source changed')
 live=decode_csvz((LIVE.parent/'Data2/Patch/Comm/gamedata.csvZ').read_bytes());live_sections=growth.parse_sections(live,('WPN','TWP','EQU','TEQ','MIS02'))
 old=itemmeta.CLIENT;itemmeta.CLIENT=CAPTURE
 try:n=Sources(current)
 finally:itemmeta.CLIENT=old
 caches=[]
 for file,validator in (('native-weapons-20260926',validate_weapons),('native-armor-20261002',validate_armor)):
  groups=json.loads((ROOT/f'artifacts/research/{file}/records.json').read_text('utf-8'))
  normalized=[[[bytes.fromhex(v) if gi==1 and ix in (6,8) else v for ix,v in enumerate(r)] for r in g] for gi,g in enumerate(groups)]
  validator(normalized);caches.extend(groups[1])
 cache={r[1]:r for r in caches};require(len(cache)==2613,'Source key collisions')
 defs={};facts=[];bindings={}
 for family,count,kind in (('WPN',630,1),('TWP',629,25),('EQU',692,2),('TEQ',662,26),('MIS02',2226,8)):
  rows=n.sections[family]['records'];require(len(rows)==count,'Source count differs');require([r['raw_record_hex'] for r in rows]==[r['raw_record_hex'] for r in live_sections[family]['records']],'Current source rows changed')
  ordinal,selector=n.lookup_section(family);bindings[family]={'ordinal':ordinal,'loader_selector':selector,'instance_type':kind,'all_current_rows_exact':True,'rows':count}
  require(selector==kind if family!='MIS02' else selector==24,'Original loader binding differs')
  for index,row in enumerate(rows):
   key=int(growth.fields(row)[0])
   if family=='MIS02' and key!=16055:continue
   parsed=n.item_row(family,index)['record']
   if family!='MIS02':require(cache[key][0]==family and bytes.fromhex(cache[key][8])==parsed and bytes.fromhex(cache[key][6])==bytes.fromhex(row['raw_record_hex']).rstrip(b'\r\n'),'All2613 cache/native equality failed')
   require(key not in defs,'Duplicate key');defs[key]=parsed;facts.append({'key':key,'family':family,'type':kind,'source_index':index,'source_line':row['source_line'],'parsed396_sha256':sha(parsed),'flags11A':parsed[0x11a],'flags11B':parsed[0x11b]})
 require(len(defs)==2614,'All definitions incomplete');return defs,facts,bindings,n.matches

def offer(o,key,kind,source_slot,index,salt,extra=0,byte19=255):
 o.reset_trade();meta=metadata(key,kind,extra,salt,byte19);bagraw=bytes([1,source_slot,0xa1,0xa2])+meta;o.vm.mem_write(o.bag(source_slot),bagraw)
 for prior in range(index):o.vm.mem_write(UI+0x866e8+prior*24,bytes([1,29,0,0])+metadata(1,1,0,prior,0))
 before_self=o.read(UI+0x866e8,192);o.put(UI+0x855f0,'<h',source_slot);o.call(0x49e440,0,1)
 wire=b'\x2a'+struct.pack('<HBBH',key,source_slot,1,0x1234)
 require(o.queued==[wire],'Native2A payload mismatch');require(o.read(UI+0x866e8+index*24,24)==bagraw,'Local offer full24 differs')
 require(o.read(UI+0x866e8,index*24)==before_self[:index*24],'Local preceding offers altered')
 empty=bytearray(bagraw);empty[0]=0;empty[4:6]=bytes(2);require(o.read(o.bag(source_slot),24)==bytes(empty),'Native optimistic bag clear differs');require(o.read(UI+0x855f0,2)==b'\xff\xff','Drag selected slot not retired')
 # Server reply is an explicit fixture. Its index is not the sourceBag slot.
 peer=bytes([1,index,0xb1,0xb2])+meta;o.call(0x49df10,BODY,body=peer);require(o.read(UI+0x867a8+index*24,24)==peer,'Peer50 full24 lost metadata')
 alternate=metadata(key,kind,extra,salt+1,byte19^255);second=bytes([1,index,0xc1,0xc2])+alternate;o.call(0x49df10,BODY,body=second);require(o.read(UI+0x867a8+index*24,24)==second,'SameID peer50 alternate20 was deduplicated')
 require(o.read(UI+0x866e8+index*24,24)==bagraw,'Peer50 overwrote local cache')
 return {'key':key,'type':kind,'source_bag':source_slot,'offer_index':index,'metadata20_hex':meta.hex(),'C2S2A':wire.hex(),'local_offer24_hex':bagraw.hex(),'S2C50':(b'\x50'+peer).hex(),'alternate_S2C50':(b'\x50'+second).hex(),'local_byte1_is_source_peer_byte1_is_offerindex':True,'all24_exact':True,'reply_scope':'Explicit fixture authoritative reply, not original server causality'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=OUT);args=ap.parse_args();require(not args.output_dir.exists(),'NEW output directory required')
 frozen={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in FROZEN};raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current EXE pin');current=pefile.PE(data=raw).get_memory_mapped_image();original=qualified_image()
 defs,facts,bindings,source_visits=definitions(current);print('Qualified2613 native source rows +gem16055',flush=True);o=Trade(current,original,defs);cases=[]
 for i,row in enumerate(facts):cases.append(offer(o,row['key'],row['type'],i%30,i%8,i,((i%1024)<<22) if row['family']!='MIS02' else (10<<25)|(7<<22),(0,15,240,255)[i%4]))
 print('Passed2614 all-source native offer/full50 cases',flush=True)
 matrix=[]
 for key,kind in ((1,1),(19001,25),(1001,2),(20001,26),(16055,8)):
  for source_slot in range(30):
   for index in range(8):matrix.append(offer(o,key,kind,source_slot,index,source_slot*8+index,(10<<25) if kind==8 else 0,(0,15,240,255)[index%4]))
 negative=[]
 for slot in (8,29,127,128,255):
  o.reset_trade();before=o.read(UI+0x866e8,384);body=bytes([1,slot,0xa1,0xa2])+metadata(1,1,0,2,255);o.call(0x49df10,BODY,body=body);require(o.read(UI+0x866e8,384)==before,'Peer50 invalid signed index wrote cache');negative.append({'case':'invalid_peer_index','raw_index':slot,'no_cache_write':True})
 for source_slot in (30,34,42,43):
  o.reset_trade();o.vm.mem_write(o.bag(source_slot),bytes([1,0,0,0])+metadata(1,1,0,2,255));o.put(UI+0x855f0,'<h',source_slot);o.call(0x49e440,0,1);require(bool(o.queued)==(source_slot in (42,43)),'Trade native physical caller range differs');negative.append({'case':'physical_source_control','source':source_slot,'queued':[x.hex() for x in o.queued],'refusal_program_labels':list(o.refusals),'no_server_admission':True})
 o.reset_trade();o.vm.mem_write(UI+0x866e8,(bytes([1,0,0,0])+metadata(1,1,0,2,255))*8);o.vm.mem_write(o.bag(0),bytes([1,0,0,0])+metadata(1,1,0,3,255));o.put(UI+0x855f0,'<h',0);before=o.read(UI+0x866e8,384);o.call(0x49e440,0,1);require(not o.queued and o.read(UI+0x866e8,384)==before and o.read(o.bag(0),1)==b'\x01','Full8 offer capacity control mutated');negative.append({'case':'full8_local_offers','no_queue_no_bag_or_cache_write':True})
 # Actual producer does not validate source slot, item identity, quantity or target.
 raw_producers=[]
 for target,key,slot in ((0,0,255),(0x10001,0x10002,128),(0xffff,0xffff,29)):
  o.queued.clear();o.call(0x497290,target,key,slot);wire=b'\x2a'+struct.pack('<HBBH',key&65535,slot,1,target&65535);require(o.queued==[wire],'Native direct2A truncation differs');raw_producers.append({'record':wire.hex(),'no_native_authority_validation':True})
 for quantity in (0,1,127,128,255):
  o.queued.clear();body=struct.pack('<HBBH',1,29,quantity,0x1234);o.call(0x4972d0,BODY,body=body);require(o.queued==[b'\x2a'+body],'Native pointer2A rawcopy differs');raw_producers.append({'pointer_copy_quantity':quantity,'record':o.queued[0].hex(),'no_native_authority_validation':True})
 tested=(0x49e440,0x49e290,0x497290,0x4972d0,0x49df10,0x49e1a0,0x49b720,0x49b770,0x49b850,0x459a60);require(not set(tested).intersection(o.helpers) and set(tested).issubset({a for a,n in o.visited}),'Tested trade path stubbed/not executed')
 require(sha(LIVE.read_bytes())==PIN and all(sha((ROOT/p).read_bytes())==h for p,h in frozen.items()),'Current client or frozen evidence changed')
 result={'status':'PASS','scope':'OFFLINE_NATIVE_PLAYER_TRADE_FULL20_TRANSPORT_NOT_SERVER_ADMISSION_OR_UI_ACCEPTANCE','cases':len(cases)+len(matrix)+len(negative)+len(raw_producers),'all_source_cases':cases,'bag0_29_offer0_7_matrix':matrix,'negative_controls':negative,'raw_producer_controls':raw_producers,'source_rows':facts,'source_binding':bindings,'native_width50':NativeLengths(original).query(0x50)[0],'local_cache':'UI+866E8 +offerIndex*24: count, sourceBagSlot, opaque2, full20','peer_cache':'UI+867A8 +offerIndex*24: count, offerIndex, opaque2, full20','client_sha256':PIN,'mapped_original_sha256':sha(original),'source_sha256':SOURCE_SHA,'source_instructions_matched':len(source_visits),'trade_instructions_matched':len(o.visited),'tested_not_stubbed':[hex(a) for a in tested],'external_helpers':[hex(a) for a in sorted(o.helpers)],'frozen_sha256':frozen,'tool_sha256':sha(Path(__file__).read_bytes()),'OPEN':['Native2A carries no20 metadata and cannot authorize owned source identity','Native physical42/43 send path does not admit special ownership/server grants','No original bind/tradability/equipment role policy/escrow settlement rules','No UI/pixels/DB/client/runtime/server writes; VM memory fixtures only']}
 args.output_dir.mkdir(parents=True,exist_ok=False);p=args.output_dir/'native.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8');(args.output_dir/'contract.md').write_text(CONTRACT,'utf-8');print('PASS',result['cases'],'cases');print('Tool SHA',result['tool_sha256']);print('Evidence SHA',sha(p.read_bytes()))

CONTRACT='''# Current original native PLAYER TRADE full instances

2A logical7 from497290: itemWORD@1, sourceBagBYTE@3, quantityBYTE@4 (fixed1), targetWORD@5. Pointer4972D0 copies6 unchanged. There is no20byte instance or offer index in this C2S. Server must obtain exact full20 from owned qualified source, never reconstruct it from item key.

Ordinary49E440 drop caller finds first empty low-item-WORD offer among8 via49E290. It emits2A, copies all24 bag bytes to UI866E8+offerIndex*24, overwritesbyte1 with sourceBagSlot, then decrements/empties selected bag optimistically. Qty1 clears count and low itemWORD only, preserves inactive upper18. Self cache byte1 is sourceBagSlot, not offerIndex.

50 logical25 dispatcher46A071→49DF10: countBYTE@1, offerIndexBYTE@2, opaque2@3..4, full20@5..24. Signed index0..7 copies all24 into UI867A8+offerIndex*24 andcalls original49E1A0 renderer. No item type/quantity/bind validator in copy. Same-ID different20 overwrite is exact. 8/29/127/128/255 rejected without cachewrite. Server supplied zero20 is required for an empty authoritative offer; native50 itself only copies.

All630WPN+629TWP+692EQU+662TEQ original396 reparse against accepted source caches; source loader bindings and current unchanged rows are verified, plusgem16055. Synthetic instance types1/25/2/26/8 with varying20bytes prove transport only, not source→instance generation or role equip admission. All30 ordinarybag×8 offers per5classes execute real caller, producer, all24 self/peercache and actual native icon/quantity renderer up to external presentation adapters. Original physical42/43 drop support remains mechanical exposure, never permission.

Native source data and executed spans match original149c/currentc5. Socket queue, external sprite/text/bagdrag endpoint adaptations do not establish live UI acceptance. Original grant/bind/tradability/escrow settlement policy remains OPEN.
'''
if __name__=='__main__':main()
