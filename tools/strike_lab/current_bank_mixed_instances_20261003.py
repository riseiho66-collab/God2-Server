"""NEW offline original/current x86 mixed-family bank65 transport evidence.

Only emulated fixture memory is written. No process memory, client, DB, UI,
network, prior evidence or runtime is changed. Copy behavior is not admission.
"""
import argparse
import json
import struct
from pathlib import Path
import pefile
from tools.strike_lab.current_bank_weapon_gem_transport_20261003 import Bank,source,metadata,Source
from tools.strike_lab.current_bank_armor_transport_20261002 import defs,ROOT,LIVE,PIN,require,sha
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
from tools.strike_lab.current_party_20261002 import UI
from tools.strike_lab import recover_companion_growth as growth
from tools.strike_lab.omega_assets import decode_csvz

OUTPUT=ROOT/'artifacts/research/current-bank-mixed-instances-20261003/run01'
FAMILIES=(('EQU',1201,2),('TEQ',20201,26),('WPN',1,1),('TWP',19001,25),('GEM',16055,8),('MED',3107,0),('EMPTY',0,0))
FLAGS=(0,0x00400000,0x00800000,0x01000000,0x40000000,0x80000000,0xc1c00000)
OLD_FILES=('tools/strike_lab/current_bank_weapon_gem_transport_20261003.py',
 'tools/strike_lab/current_bank_armor_transport_20261002.py',
 'artifacts/research/current-bank-weapon-gem-transport-20261003/run03/native.json',
 'artifacts/research/current-bank-armor-transport-20261002/run02/native.json')

def instance(family,extra,salt):
 name,key,kind=family
 if not key:return bytes(20)
 # Gem remains the original displayed charge1..10 domain; other high bits
 # remain synthetic preservation controls, not recovered bind semantics.
 if kind==8:extra=(extra&0x01c00000)|(((salt%10)+1)<<25)
 return metadata(key,kind,extra,salt,(0,15,240,255)[salt%4])

def swap(o,left,right,page,source_slot,dest,flags,salt,qty_left=None,qty_right=None,tag='ordered_pair'):
 o.reset(page)
 a=instance(left,flags,salt);b=instance(right,flags^0x80000000,salt+1)
 qa=(0 if not left[1] else 7 if left[0]=='MED' else 1) if qty_left is None else qty_left
 qb=(0 if not right[1] else 11 if right[0]=='MED' else 1) if qty_right is None else qty_right
 o.snapshot48(page,source_slot,qa,a);o.snapshot48(page,dest,qb,b)
 # Mark local bytes to distinguish complete24 exchange from only20 copying.
 o.vm.mem_write(o.cell(page,source_slot)+2,b'\x12\x34')
 o.vm.mem_write(o.cell(page,dest)+2,b'\x56\x78')
 before=(o.read(o.cell(page,source_slot),24),o.read(o.cell(page,dest),24))
 vault_before=o.read(UI+0x839cc,300*24)
 bag_before=o.read(UI+0x8560c,50*24)
 o.queued.clear();o.put(UI+0x83994,'<h',source_slot);o.call(0x4719b0,dest,1)
 after=(o.read(o.cell(page,source_slot),24),o.read(o.cell(page,dest),24))
 expected=b'\x65'+struct.pack('<HBBBB',3793,page,source_slot,dest,1)
 queued=bool(o.queued)
 require(o.queued in ([],[expected]),'65 original raw7 differs')
 require(after==(before[::-1] if queued else before),'65 partial swap/corruption')
 vault_expected=bytearray(vault_before)
 if queued:
  for slot,value in ((source_slot,before[1]),(dest,before[0])):
   offset=(page*50+slot)*24;vault_expected[offset:offset+24]=value
 require(o.read(UI+0x839cc,300*24)==bytes(vault_expected),'65 mutated unrelated page/cell')
 require(o.read(UI+0x8560c,50*24)==bag_before,'65 mutated inventory')
 # Reconstruct canonical server snapshots independently after the local swap.
 canonical=[]
 for slot,value in ((source_slot,after[0]),(dest,after[1])):
  wire=o.snapshot48(page,slot,value[0],value[4:])
  actual=o.read(o.cell(page,slot),24)
  require(actual==bytes([value[0],slot])+value[2:],'48 canonical refresh lost20/reserved')
  canonical.append({'wire29':wire.hex(),'raw24':actual.hex()})
 # Every occupied payload also traverses true 3B/41 bag consumers; scalar MED
 # is normalized to one here to isolate full20 transport from stack behavior.
 projected=[]
 for bag_slot,value in ((5,after[0]),(7,after[1])):
  if value[0] and int.from_bytes(value[4:6],'little'):
   wires=o.projection3b41(bag_slot,value[4:]);actual=o.read(o.bag(bag_slot),24)
   require(actual[0]==1 and actual[4:]==value[4:],'3B41 full20 lost after cross-family swap')
   projected.append({'slot':bag_slot,'wire':wires,'raw24':actual.hex()})
 return {'case':tag,'left':left[0],'right':right[0],'page':page,'source':source_slot,'destination':dest,
  'header_flags':hex(flags),'source_quantity':qa,'destination_quantity':qb,
  'queued':queued,'C2S65':[v.hex() for v in o.queued],'refusals':list(o.refusals),
  'before_raw24':[v.hex() for v in before],'after_raw24':[v.hex() for v in after],
  'whole24_if_queued_else_unchanged':True,'other298_cells_and_bag_unchanged':True,
  'canonical48':canonical,'bag3B41':projected,'scope':'Direct native caller fixture, not UI or server permission'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=OUTPUT);args=ap.parse_args()
 require(not args.output_dir.exists(),'New evidence directory required')
 previous={p:sha((ROOT/p).read_bytes()) for p in OLD_FILES}
 raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current client pin')
 current=pefile.PE(data=raw).get_memory_mapped_image();original=qualified_image()
 armor,armor_facts,armor_source=defs(original,current)
 weapons,weapon_facts,bindings,source_visits=source(current)
 definitions={**weapons,**armor}
 # Constructor code ran before the dynamic hook; independently match all
 # declared source spans to avoid claiming pre-hook code qualification.
 spans=[]
 for begin,end in Source.CODE:
  require(current[begin:end]==original[begin:end],'Source constructor span differs')
  spans.append({'start':hex(begin+0x400000),'end':hex(end+0x400000),'sha256':sha(original[begin:end])})
 live_sections=growth.parse_sections(decode_csvz((LIVE.parent/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()),('MED02',))
 from tools.strike_lab.current_bank_armor_transport_20261002 import CAPTURE
 old_sections=growth.parse_sections(decode_csvz((CAPTURE/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()),('MED02',))
 require([r['raw_record_hex'] for r in live_sections['MED02']['records']]==[r['raw_record_hex'] for r in old_sections['MED02']['records']],'Current MED02 rows differ')
 o=Bank(current,original,definitions);cases=[]
 for page in range(3):
  for left in FAMILIES:
   for right in FAMILIES:
    for i,flags in enumerate(FLAGS):
     cases.append(swap(o,left,right,page,2,49,flags,i+page*13))
  print('Passed full ordered-pair page',page,flush=True)
 # Special physical sources/destinations are measured, never authorized.
 for page in range(6):
  for left in FAMILIES[:-1]:
   for right in FAMILIES[:-1]:
    for a,b in ((0,2),(1,2),(2,0),(2,1)):
     cases.append(swap(o,left,right,page,a,b,0x80000000,page+2,tag='special_domain'))
 # All ordinary destination cells with every distinct ordered family pair.
 for dest in range(2,50):
  src=49 if dest!=49 else 2
  for i,left in enumerate(FAMILIES[:-1]):
   right=FAMILIES[(i+1)%6];cases.append(swap(o,left,right,dest%3,src,dest,FLAGS[dest%7],dest,tag='all_ordinary_slots'))
 # Identical ID with different complete20 and meaningful MED stack counts.
 for page in range(3):
  for family in FAMILIES[:-1]:
   for quantity in ((1,7,127,255) if family[0]=='MED' else (1,)):
    cases.append(swap(o,family,family,page,2,49,0xc1c00000,page+5,quantity,1,tag='same_id_distinct20'))
 # Empty count alone does not clear inactive20; confirm48 literal behavior.
 empty=[]
 for page in range(6):
  for slot in (0,1,2,49):
   stale=bytes(2)+bytes([0xa5])*18;o.snapshot48(page,slot,0,stale)
   require(o.read(o.cell(page,slot),24)[0]==0 and o.read(o.cell(page,slot),24)[4:]==stale,'48 incorrectly zeroed inactive20')
   o.snapshot48(page,slot,0,bytes(20));require(o.read(o.cell(page,slot),24)[4:]==bytes(20),'48 explicit clear failed')
   empty.append({'page':page,'slot':slot,'qty0_stale20_copied':True,'explicit_zero20_cleared':True})
 tested=(0x4719b0,0x471d40,0x497510,0x471e50,0x498dd0,0x4991e0,0x459a60,0x49b850)
 require(set(tested).isdisjoint(o.helpers) and set(tested).issubset({a for a,n in o.visited}),'Tested consumer/producer stubbed or missing')
 require(sha(LIVE.read_bytes())==PIN and all(sha((ROOT/p).read_bytes())==h for p,h in previous.items()),'Client or old evidence changed')
 result={'status':'PASS','scope':'Original149c/currentc5 offline transport only; not original bank admission/bind/ownership or live UI',
  'cases':len(cases)+len(empty),'ordered_pairs_including_empty':len(FAMILIES)**2,'occupied_ordered_pairs':36,
  'swap_cases':cases,'empty48_controls':empty,'source_rows':armor_facts+weapon_facts,
  'source_binding':bindings,'MED02_current_original_raw_exact':True,'armor_source':armor_source,
  'client_sha256':sha(raw),'mapped_original_sha256':sha(original),'source_constructor_matched_spans':spans,
  'source_dynamic_instruction_matches':len(source_visits),'bank_dynamic_instruction_matches':len(o.visited),
  'widths':{hex(op):NativeLengths(original).query(op)[0] for op in (0x48,0x3b,0x41)},
  'executed_not_stubbed':[hex(a) for a in tested],'adapters':[hex(a) for a in sorted(o.helpers)],
  'previous_tool_evidence_unchanged':previous,'tool_sha256':sha(Path(__file__).read_bytes()),
  'OPEN':['Synthetic header/tail operands are not original generated instances or grants',
   'Original transfer binding/tradability/shared-account/bank access policy unknown',
   'Backing pages3..5 were direct consumer/caller inputs, not reachable UI page claims',
   'Special cells0/1 cannot be admitted from mechanical sender behavior',
   'No runtime/client/formal DB/network/live UI/process memory writes']}
 args.output_dir.mkdir(parents=True,exist_ok=False)
 (args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
 print('PASS',result['cases'],'mixed native bank cases',flush=True)
 print('Tool',result['tool_sha256']);print('Evidence',sha((args.output_dir/'native.json').read_bytes()))

if __name__=='__main__':main()
