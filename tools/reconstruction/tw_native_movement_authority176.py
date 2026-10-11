"""Pinned TW movement authority frontier, static original-source preservation.

No native/client/C++/Lua/API/DB/SQL/browser/server/build/tests/codec execution.
Only complete original file copies/hashes and bounded Capstone disassembly.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import capstone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-host-composition-source-01'
ARTIFACT=ROUND/'agents/tw-authority-frontier'
IMAGE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
IMAGE_PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE_PIN='58c05401e6e9145a44641e5842e875cdab3051ddd9968102859ecacca0cec9ca'
BASE=0x400000
OWNED='tools/reconstruction/tw_native_movement_authority176.py'
SOURCE=[
    'src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp',
    'src/game/SharedTaiwanNativeMovementScene.h','src/game/SharedTaiwanNativeMovementScene.cpp',
    'src/protocol/RecoveredMovement.h','src/protocol/RecoveredNativeMovement.h',
    'src/scripting/TaiwanMovementRules.h','src/scripting/TaiwanMovementRules.cpp',
    'scripts/tw/native_movement.lua',
]
CONTEXT=[
    'AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
    'docs/research/shared-taiwan-movement-20261007.md',
    'docs/research/current-movement-20260919.md',
    'docs/research/current-live-movement-20260920.md',
    'docs/research/saved-player-movement-and-timer-audit-20260923.md',
    'tools/strike_lab/apex.py',
]
GOLDEN=ROOT/'artifacts/golden/post-seed/native-movement-ack-20260920-02'
SPANS=[
    (0x68950,0x68A2D,'complete actual C2S send wrapper, local-mode branches and independent primary actor gate','new_target'),
    (0x1029A0,0x102B4D,'complete elapsed float integration, remaining displacement, map window and finish result','new_target'),
    (0x102B50,0x102B8E,'complete symmetric half-threshold fractional rounding helper','new_target'),
    (0x102B90,0x102BEA,'complete rawcell target path-vs-partial-line dispatch','new_target'),
    (0x102BF0,0x102EDF,'complete partial straight path cell sampling and60 point cutoff','new_target'),
    (0x1035B0,0x103634,'complete pathsearch adapter preserving rawcell2 distinction and actual search owner','new_target'),
    (0x6BCC0,0x6C51C,'complete native61/world reset-map entry with full branching and original pending reset','new_target'),
    (0x67860,0x67CC3,'complete frame loop, entry pending completion, timestamp producer and unsigned5..200ms clamp','new_target'),
    (0x101F90,0x10220A,'complete pending-full recovery, owned point restore, scene projection and ring reinitialization','new_target'),
    (0x6CC00,0x6CD5C,'complete native5D downstream effect publisher, no server ACK byte producer','expanded_consumer_context'),
    (0x102700,0x1028EB,'complete step sender extending known direction prefix with pose/speed/float/ring behavior','expanded_known_step_context'),
    (0x102570,0x102684,'complete native path completion/next-step routine, historical function identity retained','expanded_known_completion_context'),
    (0x149630,0x149657,'complete x87 truncate helper with restored original control word','new_CRT_support'),
    (0x1024C0,0x10256E,'complete path entry known from historical lab, not new server authority','retained_historical_context'),
    (0x15790,0x157C5,'complete original2E builder retained known WORD/slot/residue layout','retained_previous_context'),
    (0x692FA,0x69345,'complete original5D dispatch store/pop/publish block, retained known semantics','retained_previous_context'),
    (0x69345,0x69369,'complete native61 dispatch block that invokes actual entry/reset consumer','new_dispatch_support'),
    (0x103640,0x103651,'complete known ring initializer','retained_ring_context'),
    (0x103660,0x103678,'complete known empty ring predicate','retained_ring_context'),
    (0x103680,0x1036A5,'complete known capacity39 ring full predicate','retained_ring_context'),
    (0x1036B0,0x1036FB,'complete known point push/count/write modulo40','retained_ring_context'),
    (0x103700,0x103741,'complete known oldest point pop/signedWORD projections','retained_ring_context'),
    (0x103750,0x103782,'complete last-written point getter, raw signedWORD coordinate projection','retained_ring_context'),
    (0x103790,0x1037C9,'complete oldest point peek and boolean existence','retained_ring_context'),
    (0x1216,0x121C,'actual5D fixed logical length2 return stub','retained169_length_context'),
    (0x1246,0x124C,'actual5E fixed logical length13 return stub','retained169_length_context'),
    (0x12D0,0x12D6,'actual61 fixed logical length9 return stub','retained169_length_context'),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def put(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def emit(name,value):
    put(ARTIFACT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())

def original(path,copy):
    data=path.read_bytes();put(ARTIFACT/copy,data)
    return {'path':path.resolve().as_posix(),'copy':copy,'bytes':len(data),'sha256':sha(data)}

def copy_sources(stage,names):
    rows=[original(ROOT/name,f'{stage}/s{index:02d}{Path(name).suffix}') for index,name in enumerate(names)]
    emit(f'{stage}-source-origins.json',rows)
    return rows

def recover():
    raw=IMAGE.read_bytes();before=(ROUND/'before-manifest.json').read_bytes()
    if sha(raw)!=IMAGE_PIN or sha(before)!=BEFORE_PIN or len(json.loads(before))!=1260:
        raise RuntimeError('Pinned actual original/fresh before mismatch; never reset baseline')
    ARTIFACT.mkdir(parents=True,exist_ok=True)
    put(ARTIFACT/'root-before.raw',before)
    emit('root-lineage.json',{'fresh_before_inputs':1260,'fresh_before_sha256':BEFORE_PIN,
         'entire_prior175_members_retained':2160,'prior_verification':'parent fresh receipt',
         'previous_sealed_artifacts_unchanged':True})
    copy_sources('before',SOURCE)
    emit('new-file-before.json',{'path':(ROOT/OWNED).as_posix(),'state':'absent in parent fresh before','copy':None})
    contexts=[original(ROOT/name,f'context/c{index:02d}{Path(name).suffix}') for index,name in enumerate(CONTEXT)]
    emit('context-originals.json',contexts)
    inputs=[original(IMAGE,'input/native.bin')]
    for index,path in enumerate(sorted(GOLDEN.iterdir())):
        if path.is_file():inputs.append(original(path,f'input/g{index:02d}{path.suffix}'))
    emit('original-inputs.json',inputs)
    emit('derived-inputs.json',{'decoded_native_or_wire_files':[],
         'generated_disassembly':'native-spans.json and native-sites.json',
         'codecs_geometry_native_or_Cpp_not_executed':True})
    golden_session=json.loads((GOLDEN/'session.json').read_bytes())
    put(ARTIFACT/'historical-trace-scope.json',(json.dumps({
         'source_scope':'surviving golden files are original captured seed/post-seed exchange, not movement acceptance',
         'actual_session':golden_session,'actual_csv_original':next(row['copy'] for row in inputs if row['path'].endswith('protocol-core.csv')),
         'LOGIN_field':golden_session['LOGIN'],'actual_last_state':golden_session['LAST_ACCEPTED_STATE'],
         'actual_movement_run_originals_missing':[
              'artifacts/runs/native-movement-ack-20260920-02',
              'artifacts/runs/native-movement-chain-20260920-03'],
         'no_archive_restoration_or_historical_baseline_refresh':True,
         'lab_documentary_ack_is_not_official_server_producer':True},indent=2)+'\n').encode())
    decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    spans=[];instructions={}
    for index,(start,end,purpose,scope) in enumerate(SPANS):
        data=raw[start:end];copy=f'raw/n{index:02d}.bin';put(ARTIFACT/copy,data)
        disassembled=[]
        for instruction in decoder.disasm(data,BASE+start):
            row={'rva':f'{instruction.address-BASE:08X}','va':f'{instruction.address:08X}',
                 'bytes_hex':instruction.bytes.hex(),'mnemonic':instruction.mnemonic,'operands':instruction.op_str}
            disassembled.append(row);instructions[instruction.address-BASE]=row
        spans.append({'start_rva':f'{start:08X}','end_exclusive_rva':f'{end:08X}',
             'start_va':f'{BASE+start:08X}','end_exclusive_va':f'{BASE+end:08X}',
             'copy':copy,'bytes':len(data),'sha256':sha(data),'purpose':purpose,'scope':scope,
             'instructions':disassembled})
    emit('native-spans.json',spans)
    sites=[
        (0x6895A,'local actor mode2 bypasses local UI branches, does not itself block network send'),
        (0x68982,'local mode0/1 resources only determine local UI position calls'),
        (0x689F8,'actual main actor DWORD decides whether any2E is sent'),
        (0x68A0D,'raw original caller slot DWORD forwarded; builder only writes lowBYTE'),
        (0x68A21,'actual C2S builder call415790'),
        (0x1027B9,'direction selects actual motion record pointer'),
        (0x1027BE,'actual actor/pose/resource modifier qualification WORD'),
        (0x1027F8,'actor motion modifier ID from actual packed actor state'),
        (0x102808,'speed selector is BYTE230, not sequence231/236'),
        (0x102810,'actual motion table and modifier add before scale multiplication'),
        (0x102819,'actual float velocity x stored24'),
        (0x10283C,'actual float velocity y stored28'),
        (0x102846,'remaining signed x displacement14 from actual direction record'),
        (0x10284E,'remaining signed y displacement18 from actual direction record'),
        (0x102851,'fractional accumulators1C/20 zeroed on a new step'),
        (0x102864,'calls actual network wrapper before trying pending point push'),
        (0x102877,'pending point push follows send, not send success authority'),
        (0x102882,'full pending ring invokes recovery, not generic success'),
        (0x1028BC,'accepted client step updates actual facing direction'),
        (0x1025A3,'state8 calls complete screen animation integrator before advancing path'),
        (0x1025D0,'pending deferred actor update flag consumed only when segment finished'),
        (0x1025E4,'path cursor34 increment after segment completion'),
        (0x102608,'next path segment uses actual ring writeBYTE236'),
        (0x10265B,'terminal path completion sets client state30 idle0'),
        (0x1029AB,'elapsed ms supplied by actual previous native frame timestamp producer'),
        (0x1029BD,'unsigned elapsedDWORD represented as positive QWORD for x87'),
        (0x1029C7,'elapsed multiplied by actual float velocity24'),
        (0x1029CA,'float0.001 constant transforms milliseconds to seconds'),
        (0x1029D0,'accumulate fractional x displacement1C'),
        (0x1029DE,'elapsed multiplied by actual y velocity28'),
        (0x1029EE,'rounded integer x incremental displacement'),
        (0x1029FA,'rounded integer y incremental displacement'),
        (0x102A1F,'x/y fractional residues subtract emitted integer displacement'),
        (0x102A2D,'positive remaining x clamped at segment completion'),
        (0x102A4B,'negative remaining x tested signed after emitted delta'),
        (0x102A69,'remaining y independently tested/clamped'),
        (0x102ABC,'native projected actor screen position increments, not saved grid CAS'),
        (0x102B23,'actual map window shift publishes other retained actor offsets'),
        (0x102B45,'step completes only both x/y remaining conditions finished'),
        (0x102B55,'round helper begins truncate-to-zero conversion'),
        (0x102B68,'residue >=positive0.5 qualifies increment'),
        (0x102B7C,'residue <=negative0.5 qualifies decrement'),
        (0x14963F,'x87 temporary control word forces truncate and is restored'),
        (0x149649,'actual QWORD integer conversion width retained'),
        (0x102BAF,'path dispatch samples actual raw destination cell'),
        (0x102BB6,'nonzero destination selects pathsearch adapter'),
        (0x102BC6,'actual pathsearch adapter5035B0'),
        (0x102BDF,'zero destination uses straight partial path construction'),
        (0x1035D3,'zero-displacement appends only when actual path list already exists'),
        (0x103600,'path adapter reads full raw destination independently'),
        (0x103605,'exact raw2 distinction passed to native pathsearch, no normalization'),
        (0x103610,'actual search adapter mode argument prepared'),
        (0x103623,'actual path list length38 and full point array3C'),
        (0x103628,'actual pathsearch owner462FF0, full algorithm remains OPEN'),
        (0x102C54,'straight path stops at first actual zero sample'),
        (0x102C71,'straight partial path cutoff after count becomes greater60'),
        (0x102DD4,'sloped path samples actual map cell'),
        (0x102DDb,'sloped path stops at actual zero sample'),
        (0x67874,'frame starts by advancing prior animation/pending path'),
        (0x67A77,'timestamp from actual imported timer, not executed here'),
        (0x67A85,'timer wrap/order branch updates native timestamp counters'),
        (0x67AB1,'unsigned elapsed=current_timestamp-previous_frame_timestamp'),
        (0x67ABC,'unsigned elapsed minimum5ms'),
        (0x67ACF,'unsigned elapsed maximum200ms'),
        (0x67AE1,'previous frame timestamp advances after clamp'),
        (0x67BA9,'ACK token231 consumed here only in debug display'),
        (0x692FA,'full5D byte read independently from request slot'),
        (0x6930A,'stores complete ACK bodyBYTE at world231 without slot compare'),
        (0x69314,'unconditional pop oldest pending point, no test of pop result'),
        (0x6933B,'unconditional downstream effect publisher6CC00'),
        (0x10370D,'native empty ring pop returns without output initialization'),
        (0x103714,'native pending coordinate projected from signed lowWORD'),
        (0x103736,'pending read index modulo40'),
        (0x103738,'pending count decreases on real pop only'),
        (0x103699,'ring capacity predicate compares next write modulo40 to read'),
        (0x1036B6,'push rejects when ring capacity39 full'),
        (0x1036EE,'actual ring write index advances modulo40'),
        (0x69358,'native61 complete dispatch calls actual reset/map entry with mode1'),
        (0x6BCF8,'native61 compares existing map/scene identity'),
        (0x6BD0B,'same map and actual payload bit10000 select fast entry branch'),
        (0x6BD12,'fast branch clears payload bit in local native copy'),
        (0x6BD28,'actual new map/scene state retained from payload'),
        (0x6BD41,'low2 state/mode bits retained'),
        (0x6C198,'actual new grid x from packed low15 coordinates'),
        (0x6C1AA,'actual new grid y from upper packed15 coordinates'),
        (0x6C2B9,'fast branch reaches pending reset; changed scene uses other initialization path'),
        (0x6C41D,'pending ring initializer at actual native61 fast reset'),
        (0x6C43E,'enqueue actual position as reset baseline'),
        (0x6C4F7,'entry may send original additional ready path, not automatic movement ack'),
        (0x102003,'ring full recovery peeks oldest actual retained position'),
        (0x102014,'ring full recovery restores that position as client baseline'),
        (0x10214A,'ring full recovery clears actual path and animation state'),
        (0x1021D6,'ring full recovery resets pending ring'),
        (0x1021E3,'ring full recovery reenqueues recovered actual baseline'),
        (0x6CC0B,'5D downstream effect publisher uses actual actor effect context'),
        (0x6CD26,'5D downstream publishes client effect, no response generation'),
        (0x1216,'original full logical5D size2'),
        (0x1246,'original full logical5E size13'),
        (0x12D0,'original full logical61 size9'),
    ]
    emit('native-sites.json',[{'rva':f'{rva:08X}','va':f'{BASE+rva:08X}',
         'instruction':instructions[rva],'fact':fact,
         'scope':next(scope for start,end,_,scope in SPANS if start<=rva<end)} for rva,fact in sites])
    data_rows=[]
    for index,(start,length,role) in enumerate([
         (0x171310,4,'float millisecond scale0.001'),(0x1709A8,4,'float positive half threshold'),
         (0x170C28,4,'float negative half threshold'),
         (0x6B5D4+0x5D*4,4,'actual5D dispatch pointer'),
         (0x6B5D4+0x61*4,4,'actual61 dispatch pointer'),
         (0x1324+0x5D*4,4,'retained1695D length-resolver pointer'),
         (0x1324+0x61*4,4,'retained16961 length-resolver pointer')]):
        data=raw[start:start+length];copy=f'raw/d{index:02d}.bin';put(ARTIFACT/copy,data)
        data_rows.append({'rva':f'{start:08X}','va':f'{BASE+start:08X}','copy':copy,
             'bytes':len(data),'sha256':sha(data),'raw_hex':data.hex(),'role':role})
    emit('native-data.json',data_rows)
    fields=[
        ('30','DWORD','client animation/path state8 ordinary-moving,0 idle; other modes not inferred as server rights'),
        ('34','DWORD','client path cursor'),('38','DWORD','client path point count'),
        ('3C','8-byte entries','actual client path point array'),
        ('224/228','DWORD','actual client grid coordinates'),
        ('21C/220','DWORD','projected client screen coordinates'),
        ('230','BYTE','actual motion speed selector, not request sequence'),
        ('231','BYTE','full received5D token; shown by debug UI, no inferred echo'),
        ('234/235/236','BYTE/BYTE/BYTE','pending count/read/write ring modulo40, capacity39'),
        ('14/18','signedDWORD','remaining screen displacement for current segment'),
        ('1C/20','float32','fractional screen displacement residues'),
        ('24/28','float32','actual client velocity from direction/actor/motion resources'),
        ('A7F2F10','DWORD','client elapsed ms from real previous frame, unsigned clamped5..200'),
        ('A7F2F14','DWORD','previous actual client frame timestamp'),
        ('15396840','DWORD','actual main actor presence gate for C2S emission'),
        ('A7E05DC->BC','pointer','actual map owner/rawcell/window lifecycle; no fabricated pointer'),
    ]
    emit('actual-client-field-relations.json',[{'world_relative_offset_hex':offset,'native_width':width,
         'proven_client_role':role,'server_authority_inference':False} for offset,width,role in fields])
    emit('source-field-frontier.json',{
         'actual_existing_API':'SharedTaiwanNativeMovementScene::Authority::authorize(Candidate)->optional Permit(full_native_ack,current,publish_authority)',
         'already_bound':['actual complete Lease/session/account/character/delivery generation','saved before position/revision',
              'scene and real resource generation','raw native cell and preserved full2E request','actual owner pose/direction',
              'full supplied logical5D2B','single common position CAS','one-use authority publication'],
         'external_owner_inputs_still_required':['actual server pending/ring/reset epoch and request admission',
              'actual authoritative elapsed/deadline/cooldown provenance, not client5..200 animation',
              'actual battle/transfer/phase generation','actual dynamic collision/path/corner/actor ownership',
              'actual full native5D byte supplier without request-index echo invention'],
         'API_change_required_for_recovered_geometry':False,
         'API_note':'existing real Authority can strongly own these tickets, capture exact Candidate and recheck through current/publish; Candidate itself is not a server admission ticket',
         'no_cpp_policy_patch':'parent/peer own actual host integration; this agent only tool/static provenance',
         'native_server_producer':'not present in supplied client evidence; must obtain original server producer or current matching server trace, otherwise explicitly document a separate custom policy',
         'existing_frozen_ack_convenience':'RecoveredMovement::ack remains historical fixture helper; not consumed as recovered original authority'})
    emit('gaps.json',{
         'original_server_5D_byte_producer':'OPEN; client consumer acceptsBYTE without verifying slot, cannot prove echo or admission semantics',
         'actual_server_pending_timing_reset_battle_transfer':'OPEN; actual Authority owner must provide qualified immutable ticket/current/publication',
         'pathsearch_462FF0':'OPEN full actual search/corner/dynamic entity algorithm; rawcell2 adapter is newly bounded but not all authority',
         'client_animation_vs_server_rate':'new full bounded client formulas are presentation/pending completion, not original server timing policy',
         'native_61_variants':'full parser preserved; changed-scene resources/entry policies and additional ready path are separate pending routes',
         'empty_native_5D_pop':'client still publishes uninitialized output if empty; server source must not manufacture missing pending success',
         'historical_original_ack_runs':'original run paths missing; surviving golden files only seed exchange, no new acceptance baseline',
         'own_lab_policy':'historical generated5D/firstslot/mod40 observations are not official server producer',
         'full_game_counts':'complete directional/state/variant denominator unknown, percentage null',
         'phase':'source/static only, no execution/build/tests/runtime/API/DB/SQL/deploy'})
    rows=copy_sources('intermediate',[OWNED])
    print(json.dumps({'full_native_spans':len(spans),'new_target_spans':9,'new_CRT_support_spans':1,
         'new_dispatch_support_spans':1,'expanded_context_spans':3,'retained_spans':13,
         'native_sites':len(sites),'raw_data_spans':len(data_rows),'original_inputs':len(inputs),
         'before_original_sources':len(SOURCE),'owned_tool':rows[0]}))

def final():
    rows=copy_sources('current',SOURCE+[OWNED])
    emit('source-sites.json',[{'path':row['path'],'copy':row['copy'],'bytes':row['bytes'],
         'sha256':row['sha256'],'complete_original_source':True} for row in rows])
    emit('delivery.json',{'round':'20261008-tw-native-host-composition-source','BATCHFINAL_received':True,
         'owned_source_files':[OWNED],'modified_game_CPP':0,'current_originals':len(rows),
         'new_target_spans':9,'new_CRT_support_spans':1,'new_dispatch_support_spans':1,
         'expanded_context_spans':3,'retained_spans':13,'new_opcodes':0,'complete_routes_added':0,
         'whole_game_percentage':None,'only_stable_source_current_pinned':True,'source_only':True})
    members=[]
    for path in sorted(ARTIFACT.rglob('*')):
        if path.is_file():
            raw=path.read_bytes();members.append({'path':path.relative_to(ARTIFACT).as_posix(),
                 'bytes':len(raw),'sha256':sha(raw)})
    emit('seal.json',{'format':'god2-agent-full-artifact-seal-v1','member_count':len(members),
         'members':members,'source_only':True,'whole_game_percentage':None})
    print(json.dumps({'current_originals':len(rows),'sealed_members':len(members),
         'tool_sha256':sha((ROOT/OWNED).read_bytes()),'seal_sha256':sha((ARTIFACT/'seal.json').read_bytes())}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final',action='store_true',help='only after explicit parent BATCHFINAL')
    final() if parser.parse_args().final else recover()
