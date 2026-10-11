"""TW pinned asset-name/candidate/open static source provenance.

Only file reads/copies/hashes, retained pure0516 decompression, text-token
inventory and Capstone are executed. No selection C++/native/runtime/tests.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import capstone
from tools.strike_lab.omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / 'artifacts/integration/packet-connections-20261006/tw-native-resource-selection-source-01'
ARTIFACT = ROUND / 'agents/tw-resource-selection'
IMAGE = ROOT / 'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
ASSET_ROOT = ROOT.parent / 'God2/Data2/map/island03/cityi2'
IMAGE_PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE_PIN = 'd41be7e12f13e1bbf802932483b03a98a20cc06f8601e316d79d7e7991d47cf0'
BASE = 0x400000
OWNED = ['src/game/TaiwanNativeResourceSelection.h','src/game/TaiwanNativeResourceSelection.cpp',
         'tools/reconstruction/tw_native_resource_selection175.py']
SPANS = [
    (0x29820,0x29AAB,'complete binary requested-name suffix/probe/fallback/reader selection','new_target'),
    (0x2530,0x266F,'complete text suffix/probe/fallback and temporary-materialization branch','new_target'),
    (0x4C6D0,0x4C6F0,'complete actual model prefix accessor object+1C','new_target'),
    (0x15AFCA,0x15B03E,'complete CString prefix/raw-reference concatenation wrapper','new_target'),
    (0x15AF26,0x15AF64,'complete actual two full byte sequences copied without path normalization','new_target'),
    (0x14713E,0x147182,'complete native fopen and share wrapper','new_CRT_support'),
    (0x14E343,0x14E4B3,'complete native fopen mode parser and supplied filename lower-open forwarding','new_CRT_support'),
    (0x4D2D0,0x4D34D,'ROMFILE ordinal loader caller, retained173 context not new recovery','retained173_context'),
    (0x4D350,0x4D44C,'actual ordered slot/name binder, retained173 context not new recovery','retained173_context'),
    (0x4D520,0x4D655,'complete raw ROMFILE token/prefix/ordinal caller, retained173 context','retained173_context'),
    (0x37900,0x379DE,'bounded text map caller and last-backslash directory prefix extraction','bounded_caller_context'),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def put(path,data):
    # Resume only identical incomplete writer output; never refresh a baseline.
    if path.exists():
        if path.read_bytes()!=data:
            raise RuntimeError(f'Existing retained original differs: {path}')
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def emit(name,value):
    put(ARTIFACT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())

def original(path,destination):
    data=path.read_bytes();put(ARTIFACT/destination,data)
    return {'path':path.resolve().as_posix(),'copy':destination,'bytes':len(data),'sha256':sha(data)}

def stage(label):
    rows=[original(ROOT/name,f'intermediate/{label}/{name}') for name in OWNED]
    emit(f'intermediate/{label}/source-origins.json',rows)
    return rows

def recover():
    raw=IMAGE.read_bytes();before=(ROUND/'before-manifest.json').read_bytes()
    if sha(raw)!=IMAGE_PIN or sha(before)!=BEFORE_PIN:
        raise RuntimeError('Actual pinned native/fresh before changed; never reset baseline')
    ARTIFACT.mkdir(parents=True,exist_ok=True)
    put(ARTIFACT/'root-before-manifest.json.raw',before)
    emit('root-lineage.json',{'fresh_before_inputs':1252,'fresh_before_sha256':BEFORE_PIN,
         'entire_prior174_members_retained':2124,'prior_integrity':'parent fresh receipt',
         'previous_sealed_artifacts_untouched':True})
    emit('new-files-before.json',[{'path':(ROOT/name).resolve().as_posix(),
         'state':'absent in fresh parent before','before_copy':None} for name in OWNED])
    inputs=[original(IMAGE,'input/native-image.bin'),original(ASSET_ROOT/'Wood_B.ROMZ','input/Wood_B.ROMZ'),
            original(ASSET_ROOT/'cityi2.mdlZ','input/cityi2.mdlZ'),
            original(ROOT/'tools/strike_lab/omega_assets.py','input/omega_assets.py')]
    emit('original-inputs.json',inputs)
    derived=[]
    for filename in ['Wood_B.ROMZ','cityi2.mdlZ']:
        encoded=(ASSET_ROOT/filename).read_bytes();decoded=decode_csvz(encoded)
        copy=f'derived/{filename}.decoded.bin';put(ARTIFACT/copy,decoded)
        derived.append({'encoded_original_path':(ASSET_ROOT/filename).resolve().as_posix(),
             'encoded_sha256':sha(encoded),'copy':copy,'bytes':len(decoded),'sha256':sha(decoded),
             'producer':'retained pure0516 file decoder','is_installed_original':False})
    emit('derived-inputs.json',derived)
    context_names=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
         'src/game/TaiwanNativeRomAsset.h','src/game/TaiwanNativeRomAsset.cpp',
         'src/game/TaiwanNativeMapAsset.h','src/game/TaiwanNativeMapAsset.cpp']
    emit('context-source-origins.json',[original(ROOT/name,f'context/{name}') for name in context_names])
    emit('prior-gaps-origin.json',original(ROOT/'artifacts/integration/packet-connections-20261006/tw-native-rom-geometry-source-01/agents/tw-rom-source/gaps.json','context/prior174-gaps.json'))
    emit('context-scope.json',{'concurrent MapAsset':'observed context only, not fresh before/current pin',
         '0516 and ROM/HMD readers':'retained context, not recounted new recovery',
         'root books/reports/catalog/ledger':'not current pinned'})
    decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    spans=[];instructions={}
    for number,(start,end,purpose,scope) in enumerate(SPANS):
        data=raw[start:end];copy=f'native-spans/s{number:02d}-{BASE+start:08X}-{BASE+end:08X}.bin'
        put(ARTIFACT/copy,data);disassembled=[]
        for instruction in decoder.disasm(data,BASE+start):
            row={'rva':f'{instruction.address-BASE:08X}','va':f'{instruction.address:08X}',
                 'bytes_hex':instruction.bytes.hex(),'mnemonic':instruction.mnemonic,'operands':instruction.op_str}
            disassembled.append(row);instructions[instruction.address-BASE]=row
        spans.append({'start_rva':f'{start:08X}','end_exclusive_rva':f'{end:08X}',
             'start_va':f'{BASE+start:08X}','end_exclusive_va':f'{BASE+end:08X}',
             'copy':copy,'bytes':len(data),'sha256':sha(data),'scope':scope,'purpose':purpose,
             'instructions':disassembled})
    emit('native-spans.json',spans)
    sites=[
        (0x29843,'binary native unsigned lowWORD bank gate512'),
        (0x2986A,'actual original full requested filename pointer'),
        (0x2988F,'copy exact original C string bytes, no basename normalization'),
        (0x298AB,'only raw requested[len-4] dot selects appended Z'),
        (0x298B1,'actual onebyte Z suffix literal'),
        (0x298E7,'candidate open mode rb'),(0x298ED,'open candidate via actual native fopen'),
        (0x298FC,'candidate open failure jumps plain original fallback'),
        (0x2990B,'candidate first prefix byte5'),(0x2991D,'candidate second prefix byte16'),
        (0x29920,'non0516 prefix jumps close then original fallback'),
        (0x299D1,'0516 candidate enters full memory ROM reader'),
        (0x29A5F,'compressed reader return joins cleanup, not original filename fallback'),
        (0x29A62,'invalid candidate marker closes opened original candidate'),
        (0x29A6F,'fallback exact original request ebx, not normalized candidate'),
        (0x29A70,'reopen original requested filename in rb'),
        (0x29A82,'original fallback enters native file ROM reader'),
        (0x2571,'text appends Z unconditionally'),(0x259E,'text opens appended candidate'),
        (0x25AA,'text candidate fopen failure branches to original'),
        (0x25C0,'text first prefix byte5'),(0x25D2,'text second prefix byte16'),
        (0x25FC,'text creates actual temporary decoded destination'),
        (0x2607,'text decompresses actual opened candidate'),
        (0x262B,'text reopens decoded temporary file in rt'),
        (0x2640,'failed temporary reopen falls through to original request'),
        (0x2647,'text fallback opens original request pointer'),
        (0x264F,'text original rt fopen'),(0x2665,'invalid marker closes candidate before fallback'),
        (0x4C6D6,'actual native model prefix is object+1C CString'),
        (0x4C6E4,'returns complete exact model prefix'),
        (0x15AFF6,'original raw reference strlen'),
        (0x15B006,'full native prefix CString byte length'),
        (0x15B00C,'concatenates prefix followed by raw reference'),
        (0x15AF33,'allocation uses sum of exact byte lengths'),
        (0x15AF47,'copies entire first byte sequence'),
        (0x15AF53,'second copy starts exactly at first length'),
        (0x15AF56,'copies entire second byte sequence without inserted separator'),
        (0x147179,'fopen wrapper forwards filename/mode/share to actual implementation'),
        (0x14E37A,'mode r native read flags'),(0x14E418,'mode b binary flag branch'),
        (0x14E47F,'original supplied filename forwarded to lower open'),
        (0x14E482,'native lower open call, cwd/ACP effects not executed/recreated'),
        (0x4D2F8,'retained caller passes actual ROMFILE ordinal'),
        (0x4D302,'retained loader calls429820'),
        (0x4D317,'successful native loader stores exact full requested name in ordinal slot'),
        (0x4D578,'retained ROMFILE raw token output destination'),
        (0x4D58E,'retained caller reads actual model prefix'),
        (0x4D5A5,'retained caller concatenates prefix/raw ROMFILE token'),
        (0x4D5DD,'retained original ROMFILE ordinal order'),
        (0x4D5F1,'retained full filename and ordinal binder call'),
        (0x37954,'bounded map caller gives actual text pathname'),
        (0x379B4,'bounded caller finds final backslash, not arbitrary guessed dirname'),
        (0x379C0,'retains actual trailing backslash in directory prefix'),
        (0x379C6,'no backslash gives native empty prefix'),
        (0x379D9,'bounded caller stores actual directory prefix in map+78'),
    ]
    emit('native-sites.json',[{'rva':f'{rva:08X}','va':f'{BASE+rva:08X}',
         'instruction':instructions[rva],'fact':fact,
         'scope':next(scope for start,end,_,scope in SPANS if start<=rva<end)} for rva,fact in sites])
    literals=[]
    for number,(address,length,purpose) in enumerate([(0x582350,3,'rb exact fopen mode'),
         (0x58236C,2,'Z suffix exact native bytes'),(0x582378,3,'rt exact fopen mode'),
         (0x584954,3,'raw ROMFILE %s token format'),(0x588BBC,8,'ROMFILE literal')]):
        data=raw[address-BASE:address-BASE+length];copy=f'native-literals/l{number:02d}-{address:08X}.bin'
        put(ARTIFACT/copy,data);literals.append({'rva':f'{address-BASE:08X}','va':f'{address:08X}',
             'copy':copy,'bytes':len(data),'sha256':sha(data),'raw_hex':data.hex(),'purpose':purpose})
    emit('native-literals.json',literals)
    text=(ARTIFACT/'derived/cityi2.mdlZ.decoded.bin').read_bytes()
    token_matches=list(re.finditer(rb'\S+',text));key=next(index for index,m in enumerate(token_matches) if m.group()==b'ROMFILE')
    count=int(token_matches[key+1].group());tokens=token_matches[key+2:key+2+count]
    emit('actual-ROMFILE-token-inventory.json',{'encoded_original':'input/cityi2.mdlZ',
         'decoded_derived':'derived/cityi2.mdlZ.decoded.bin','count':count,
         'records':[{'ordinal':number,'offset':m.start(),'end_offset':m.end(),'raw_hex':m.group().hex()}
                    for number,m in enumerate(tokens)],
         'selected_illustrating_original':'input/Wood_B.ROMZ','Wood_B_raw_ordinal':15,
         'actual_context_prefix_not_fabricated':True,'selection_Cpp_not_executed':True,
         'raw_CP950_model_content_retained_in_full_decoded':True})
    emit('selection-relations.json',{'native_image_sha256':IMAGE_PIN,
         'binary_RVA':'00029820','text_RVA':'00002530','actual_prefix_accessor_RVA':'0004C6D0',
         'prefix_reference_concat_RVA':'0015AFCA','concat_bytes_RVA':'0015AF26',
         'binary_suffix':'only native request[len-4] dot -> append ASCII Z',
         'text_suffix':'always append ASCII Z',
         'binary_fallback':'candidate fopen fails or prefix not0516; reopen original rb',
         'binary_marker_failure':'memory reader/decoder failure is not original fallback',
         'text_runtime_extra':'decoded temporary rt reopen failure may fallback; not reproduced by encoded selection',
         'pathnames':'full raw prefix+reference preserved, no inserted separator/normalization/case rewriting',
         'source_domain':['ASCII byte->filesystem mapping','actual absolute supplied cwd',
              'not drive-relative/rooted-without-drive','name including optional Z<=255 bytes',
              'Rom lowWORD bank<512','complete nonempty selected original','bounded successful full reads'],
         'new_game_target_spans':5,'new_CRT_support_spans':2,'retained173_spans':3,'bounded_caller_spans':1,
         'native_sites':len(sites),'new_opcodes':0,'complete_routes_added':0,'whole_game_percentage':None})
    emit('gaps.json',{'CP950_filesystem_mapping':'HIGH BYTE NAME MAPPING OPEN; full-game CP950 scope remains required; original bytes never transliterated',
         'native_CWD_drive_context':'actual working directory required; initial process state/provider not manufactured',
         'model_prefix_issuer':'actual object+1C prefix must be supplied by real caller/resource owner; accessor+concat proven, full initial issuer not claimed',
         'text_temporary_file_side_effects':'native temporary filename/materialization/reopen failures not recreated; selected encoded input only',
         'native_lower_open_OS_effects':'ANSI/drive/share/createfile errors not executed, no native HANDLE reused',
         'resource_lifecycle':'selection is not generation/Current/provider or gameplay authority',
         'encoded_banks':'full bank retained, lowWORD gate only; cross-ROM bank/remapping OPEN',
         'decoder_parser_render':'0516/ROM/HMD context retained, no decoder/parser/render execution completion',
         'allocation_or_IO_read_error':'aborts selection, never pretends native fopen failure to choose a fallback',
         'phase':'source/static only; no runtime/build/tests/API/DB/deployment'})
    rows=stage('source-01')
    print(json.dumps({'target_spans':5,'CRT_support_spans':2,'retained173_spans':3,
         'bounded_caller_spans':1,'sites':len(sites),'input_originals':len(inputs),'owned_sources':rows}))

def final():
    rows=[original(ROOT/name,f'current/{name}') for name in OWNED]
    emit('current-source-origins.json',rows)
    emit('source-sites.json',[{'path':row['path'],'copy':row['copy'],'bytes':row['bytes'],
         'sha256':row['sha256'],'full_original_source':True} for row in rows])
    emit('delivery.json',{'round':'20261008-tw-native-resource-selection-source',
         'BATCHFINAL_received':True,'owned_sources':rows,'new_Cpp_files':2,
         'new_game_target_spans':5,'new_CRT_support_spans':2,'retained173_spans':3,
         'bounded_caller_spans':1,'input_originals_manifest':'original-inputs.json',
         'derived_inputs_manifest':'derived-inputs.json','new_opcodes':0,'complete_routes_added':0,
         'whole_game_percentage':None,'source_only':True,'stop_after_round175':True})
    members=[]
    for path in sorted(ARTIFACT.rglob('*')):
        if path.is_file():
            raw=path.read_bytes();members.append({'path':path.relative_to(ARTIFACT).as_posix(),
                 'bytes':len(raw),'sha256':sha(raw)})
    emit('seal.json',{'format':'god2-agent-full-artifact-seal-v1','members':members,
         'member_count':len(members),'source_only':True,'whole_game_percentage':None})
    print(json.dumps({'member_count':len(members),'current_originals':len(rows),
         'seal_sha256':sha((ARTIFACT/'seal.json').read_bytes()),'owned_sources':rows}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final',action='store_true',help='only after explicit parent BATCHFINAL')
    final() if parser.parse_args().final else recover()
