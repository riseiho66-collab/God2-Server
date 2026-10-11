"""Pinned TW IGSROM02 static source/section/geometry provenance preservation.

Only files, pure decompression, bounded record inventory and Capstone execute.
No native/C++/Lua/emulator/client/server/API/DB/build/test/deployment executes.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

import capstone
from tools.strike_lab.omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / 'artifacts/integration/packet-connections-20261006/tw-native-rom-geometry-source-01'
ARTIFACT = ROUND / 'agents/tw-rom-source'
IMAGE = ROOT / 'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
ASSET = ROOT.parent / 'God2/Data2/map/island03/cityi2/Wood_B.ROMZ'
IMAGE_PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
ASSET_PIN = 'c165b833c0654071170ef4963bc5aa11cf757ff42efc6156bc6b9ed13e84503a'
DECODED_PIN = '12c167635c1e8f4e6b9469c41a17fa2062bdf2f82e7fc66c6631581bf14b4b40'
BEFORE_PIN = '7997753644b7d1864cf4d4a42f33fe4a3083efb67b0e7dd5042f2ae450a456ff'
BASE = 0x400000
OWNED = ['src/game/TaiwanNativeRomAsset.h', 'src/game/TaiwanNativeRomAsset.cpp',
         'tools/reconstruction/tw_native_rom_geometry174.py']
SPANS = [
    (0x29AB0, 0x2A1C5, 'complete IGSROM02 file reader with all original action/image/opaque section branches', 'target'),
    (0x2A1D0, 0x2AAC6, 'complete IGSROM02 memory reader and explicit consumed-buffer bound', 'target'),
    (0x2AAD0, 0x2AF36, 'complete IGSROM02 writer proves action/step/pool/block envelopes and FILE_END', 'target'),
    (0x2AF40, 0x2AFB5, 'full DWORD action lookup, positional<=256 then first matching declared ID', 'target'),
    (0x2B4C0, 0x2B5A2, 'actual whole-action image/anchor geometry', 'target'),
    (0x2D050, 0x2D157, 'actual first-step command0 terminal metadata/image lookup, no earlier-command execution', 'target'),
    (0x4A800, 0x4A97C, 'actual type7 width0/explicit dimensions and checked-domain ceil framecount', 'target'),
    (0x2BEB0, 0x2C084, 'actual PCX/PCA/PCS raw dimensions/RLE row consumption and RWIF trailer', 'target'),
    (0x2D160, 0x2D245, 'actual TGA image metadata/pixel words and RWIF trailer', 'target'),
    (0x2B000, 0x2B116, 'complete reader postload command10 cross-ROM operand rewrite, not executed by source', 'excluded_runtime_context'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def emit(name, value):
    put(ARTIFACT / name, (json.dumps(value, ensure_ascii=True, indent=2) + '\n').encode())


def copy_file(path, destination):
    raw = path.read_bytes()
    put(ARTIFACT / destination, raw)
    return {'path': path.resolve().as_posix(), 'copy': destination,
            'bytes': len(raw), 'sha256': sha(raw)}


def stage(name):
    rows = [copy_file(ROOT / relative, f'intermediate/{name}/{relative}') for relative in OWNED]
    emit(f'intermediate/{name}/source-origins.json', rows)
    return rows


def recover():
    raw = IMAGE.read_bytes()
    encoded = ASSET.read_bytes()
    before = (ROUND / 'before-manifest.json').read_bytes()
    if sha(raw) != IMAGE_PIN or sha(encoded) != ASSET_PIN or sha(before) != BEFORE_PIN:
        raise RuntimeError('Pinned actual input changed; do not reset fresh baseline')
    plain = decode_csvz(encoded)
    if sha(plain) != DECODED_PIN:
        raise RuntimeError('Actual full derived Wood_B ROM differs')
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    put(ARTIFACT / 'root-before-manifest.json.raw', before)
    emit('root-lineage.json', {'fresh_before_inputs': 1246, 'fresh_before_sha256': BEFORE_PIN,
         'entire_prior173_members_retained': 2134, 'prior_verification': 'parent_receipt',
         'prior_artifacts_unchanged': True})
    emit('new-files-before.json', [{'path': (ROOT / relative).resolve().as_posix(),
         'state': 'absent_in_fresh_parent_before', 'before_copy': None} for relative in OWNED])
    inputs = [copy_file(IMAGE, 'input/native-image.bin'), copy_file(ASSET, 'input/Wood_B.ROMZ'),
              copy_file(ROOT / 'tools/strike_lab/omega_assets.py', 'input/omega_assets.py')]
    emit('native-original-inputs.json', inputs)
    put(ARTIFACT / 'derived/Wood_B.decoded.bin', plain)
    emit('decoded-input.json', {'copy': 'derived/Wood_B.decoded.bin', 'bytes': len(plain),
         'sha256': sha(plain), 'origin': 'pure file decompression of exact selected installed Wood_B.ROMZ',
         'encoded_original_sha256': ASSET_PIN, 'decoder_original_copy': 'input/omega_assets.py',
         'decoded_is_not_an_installed_original': True, 'Cpp_or_native_parser_not_executed': True})
    context = [copy_file(ROOT / relative, f'before-context/{relative}') for relative in [
        'src/cn/assets/CnRomAsset.h', 'src/cn/assets/CnRomAsset.cpp',
        'src/game/TaiwanNativeMapAsset.h', 'src/game/TaiwanNativeMapAsset.cpp']]
    emit('context-source-origins.json', context)
    emit('context-scope.json', {'CN_source': 'lead only, never TW proof',
         'existing0516_decoder': 'previous173 qualification retained, not new format recovery',
         'concurrent_MapAsset_sources': 'actual observations at copy time, not fresh-before baseline/current pins',
         'root_books_catalog_reports': 'never current pinned'})
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    spans, instructions = [], {}
    for index, (start, end, purpose, classification) in enumerate(SPANS):
        data = raw[start:end]
        destination = f'native-spans/s{index:02d}-{BASE+start:08X}-{BASE+end:08X}.bin'
        put(ARTIFACT / destination, data)
        decoded = []
        for instruction in decoder.disasm(data, BASE + start):
            row = {'rva': f'{instruction.address-BASE:08X}', 'va': f'{instruction.address:08X}',
                   'bytes_hex': instruction.bytes.hex(), 'mnemonic': instruction.mnemonic,
                   'operands': instruction.op_str}
            decoded.append(row)
            instructions[instruction.address-BASE] = row
        spans.append({'start_rva': f'{start:08X}', 'end_exclusive_rva': f'{end:08X}',
                      'start_va': f'{BASE+start:08X}', 'end_exclusive_va': f'{BASE+end:08X}',
                      'copy': destination, 'bytes': len(data), 'sha256': sha(data),
                      'purpose': purpose, 'classification': classification, 'instructions': decoded})
    emit('native-spans.json', spans)
    selected = [
        (0x29AF2, 'read first eight-byte IGSROM02 header'),
        (0x29B01, 'read initial sizeDWORD but section starts immediately'),
        (0x29B0E, 'compare exact IGSROM02 bytes'),
        (0x29B4D, 'initialize actual native ROM identity FFFFFFFF'),
        (0x29B79, 'each section reads exact8-byte tag'),
        (0x29B88, 'each section reads exact4-byte length'),
        (0x29BBD, 'ACTINDEX stores zero-extended lowWORD'),
        (0x29BC3, 'last ACTINDEX overwrites actual identity'),
        (0x29C4B, 'PCX_DATA dispatches actual image reader'),
        (0x29C56, 'actual image registered at next ordinal without compaction'),
        (0x29DE6, 'TGA_DATA/RWIF dispatch actual raw16bit image reader'),
        (0x29E3E, 'ACT_DATA exact payload read into actual scratch metadata'),
        (0x29E4D, 'zero action ID skips actual registration and nested loops'),
        (0x29E8A, 'registered action DWORD ID retained unchanged'),
        (0x29ED0, 'actual step count header+16'),
        (0x29EE2, 'actual frame count header+20'),
        (0x29F31, 'nested step reads tag but no tag compare'),
        (0x29F40, 'nested step reads length'),
        (0x29F84, 'native nested step instruction count length/10 stored WORD'),
        (0x29F98, 'step full original bytes copied'),
        (0x2A00E, 'actual pool payload copied into scratch'),
        (0x2A045, 'actual pool signed anchor x lowWORD'),
        (0x2A05D, 'actual pool signed anchor y lowWORD'),
        (0x2A098, 'actual pool unsigned image ordinal WORD+6'),
        (0x2A0C3, 'nested ACTBLOCK length read'),
        (0x2A104, 'nested ACTBLOCK full bytes read without invented meanings'),
        (0x2A149, 'FLC_DATA goes to separate list, not image table'),
        (0x2A17F, 'FILE_END selects terminal branch'),
        (0x2A189, 'unknown sections skip actual announced length'),
        (0x2A1B3, 'postload command fixup is outside this source parser'),
        (0x2A21E, 'memory variant reads exact8-byte header'),
        (0x2A248, 'memory variant compares same IGSROM02 tag'),
        (0x2AA21, 'memory variant checks actual bytes consumed against supplied buffer size'),
        (0x2AB89, 'writer emits actual IGSROM02 bytes'),
        (0x2ABCC, 'writer emits ACTINDEX as actual two-byte native identity'),
        (0x2AE95, 'writer emits actual ACTBLOCK fullpayload'),
        (0x2AEDE, 'writer emits exact FILE_END tag'),
        (0x2AF4B, 'unsigned fullDWORD <=256 action operand passes positionally'),
        (0x2AF66, 'greater fullDWORD action compares actual header DWORD ID'),
        (0x2AF70, 'first matching action ID preserved'),
        (0x2AFAD, 'missing action returns FFFFFFFF, never action0'),
        (0x2B4FF, 'whole-action extent uses full action lookup'),
        (0x2B53D, 'extent reads actual pool image ordinal WORD'),
        (0x2B541, 'extent reads signed anchor x'),
        (0x2B54E, 'extent width=image signed16 width-anchor x'),
        (0x2B556, 'max width begins0, follows actual fullframe order'),
        (0x2B560, 'extent height=image signed16 height-anchor y'),
        (0x2B57F, 'iterate all actual action frames'),
        (0x2D08C, 'terminal helper lookup accepts actual fullDWORD operand'),
        (0x2D0B3, 'first actual step pointer'),
        (0x2D0BE, 'metadata helper compares command byte with0'),
        (0x2D0C3, 'nonzero commands only advance10, never execute or switch ROM/action'),
        (0x2D0C6, 'direct scan loop jump, no calls before terminal'),
        (0x2D0E1, 'terminal byte+3 selects actual frame'),
        (0x2D0F9, 'selected pool WORD+6 selects actual image'),
        (0x2D108, 'terminal palette pointer assignment does not alter image dimensions'),
        (0x2D10B, 'terminal stores original operand lowWORD only after fullDWORD lookup'),
        (0x4A82A, 'type7 width0 calls actual whole-action extent helper'),
        (0x4A83C, 'tile retains resulting actual width'),
        (0x4A83F, 'tile retains resulting actual height'),
        (0x4A948, 'framecount selected image height signedWORD'),
        (0x4A94E, 'ceil numerator actual height+tileheight-1'),
        (0x4A953, 'native signed division by actual tileheight'),
        (0x4A957, 'selected image width signedWORD'),
        (0x4A963, 'native signed division by actual tilewidth'),
        (0x4A967, 'native actual framecount product'),
        (0x2BED4, 'image reader copies full128-byte PCX header'),
        (0x2BF17, 'actual lowWORD native image width'),
        (0x2BF31, 'actual lowWORD native image height'),
        (0x2BF47, 'actual dimensions are subsequently signed16'),
        (0x2BF94, 'RLE command selects high two bits'),
        (0x2BFA3, 'actual runlength low6bits'),
        (0x2BFDC, 'run bytes written without normalization'),
        (0x2BFF5, 'PCX actual row byte count from header+66'),
        (0x2C05E, 'RWIF reads height*4 original row table'),
        (0x2D199, 'TGA initializes native image kind'),
        (0x2D19D, 'TGA first DWORD width destination'),
        (0x2D1AE, 'TGA second DWORD height destination'),
        (0x2D1B9, 'TGA actual signed dimension product'),
        (0x2D1C3, 'TGA pixels are two-byte words'),
        (0x2D1EE, 'TGA reads complete actual pixel payload'),
        (0x2D222, 'TGA_RWIF reads actual height*4 table'),
        (0x2B073, 'excluded postload fixup terminates atcommand0'),
        (0x2B075, 'excluded fixup only recognizes command10'),
        (0x2B098, 'excluded fixup rewrites nonterminal bank WORD+2'),
        (0x2B0C5, 'excluded fixup rewrites nonterminal action WORD+4'),
    ]
    emit('native-sites.json', [{'rva': f'{rva:08X}', 'va': f'{BASE+rva:08X}',
         'instruction': instructions[rva], 'fact': fact,
         'scope': 'excluded_runtime_context' if 0x2B000<=rva<0x2B116 else 'target'} for rva, fact in selected])
    literals = []
    for index, start in enumerate(range(0x186BB4,0x186C51,12)):
        data = raw[start:start+8]
        destination = f'native-literals/l{index:02d}-{BASE+start:08X}.bin'
        put(ARTIFACT / destination, data)
        literals.append({'rva': f'{start:08X}', 'va': f'{BASE+start:08X}', 'copy': destination,
                         'bytes': len(data), 'sha256': sha(data), 'raw_hex': data.hex()})
    emit('native-literals.json', literals)
    # Actual original binary-section inventory, not execution of C++ or any
    # geometry formula/acceptance. Every original payload remains copied in full.
    cursor, sections = 12, []
    while cursor<len(plain):
        if len(plain)-cursor<12:
            raise RuntimeError('Actual original section header truncated')
        header=cursor;tag=plain[cursor:cursor+8];size=struct.unpack_from('<I',plain,cursor+8)[0]
        cursor+=12
        if size>len(plain)-cursor:
            raise RuntimeError('Actual original section payload truncated')
        data=plain[cursor:cursor+size]
        row={'header_offset':header,'payload_offset':cursor,'size':size,'tag_hex':tag.hex(),
             'payload_sha256':sha(data),'origin':'actual pinned installed input decoded bytes'}
        if tag.startswith((b'PCX_',b'PCA_',b'PCS_')) and len(data)>=128:
            row['raw_PCX_bounds_words']=list(struct.unpack_from('<4H',data,4))
            row['raw_PCX_row_bytes_word']=struct.unpack_from('<H',data,66)[0]
        sections.append(row);cursor+=size
        if tag==b'FILE_END':break
    emit('actual-resource-sections.json', {'source_sha256':ASSET_PIN,'decoded_sha256':DECODED_PIN,
         'full_payload_copy':'derived/Wood_B.decoded.bin','initial_size_dword':struct.unpack_from('<I',plain,8)[0],
         'sections':sections,'section_count':len(sections),'consumed_offset':cursor,'decoded_bytes':len(plain),
         'native_Cpp_or_gameplay_not_executed':True})
    emit('geometry-relations.json', {'format':'tw-native-rom-geometry174-source-v1',
         'native_input_sha256':IMAGE_PIN,'file_reader_RVA':'00029AB0','memory_reader_RVA':'0002A1D0',
         'writer_RVA':'0002AAD0','full_DWORD_action_lookup_RVA':'0002AF40',
         'terminal_metadata_RVA':'0002D050','action_extent_RVA':'0002B4C0','type7_extent_RVA':'0004A800',
         'command_scan':'first step, bounded10-byte records to first0; preceding commands not executed',
         'cross_ROM_fixup':'not run; modifies command10 nonterminal operands only, not terminal frame/image/dimensions',
         'width0':'max(all action image signed16 dimensions - pool signed16 anchors), initialmax0',
         'positive_declared_width':'actual declared width/height, no fallback when invalid',
         'frame_count':'ceil(selected_terminal_image.width/tilewidth)*ceil(image.height/tileheight)',
         'source_qualified_domains':['full exact IGSROM02/FILE_END section exhaustion','positive signed16 image extents',
              'PCX bytesPerLine==nativewidth and nonoverrunning RLE rows','complete RWIF rowtable',
              'complete signed16 TGA pixel words','nonoverflowing native signed32 framecount arithmetic'],
         'raw_source_preserved':True,'no_native_slot_path_default_image_default_action':True,
         'new_opcodes':0,'complete_routes_added':0,'whole_game_percentage':None,'source_only':True})
    emit('gaps.json', {'actual_ROMFILE_ordinal_name_binding':'peer owner must supply actual selected source, not ACTINDEX guessing',
         'actual_resource_lifecycle':'real NativeCurrent/provider remains mandatory beyond static geometry',
         'render_palette_script_animation':'opaque original bytes retained, execution/completion not claimed',
         'unsupported_domains':['unknown IGSROM versions','nonpositive or unqualified image metadata',
              'PCX padded stride/overlong row runs','image native address/allocator effects','dynamic action changes',
              'cross-ROM command execution/remapping','overflowing native framecount arithmetic','missing/truncated actions/images'],
         '0516':'retained prior173 codec context, not newly counted','phase':'source/static only, no runtime/testing/deployment'})
    rows=stage('source-01')
    print(json.dumps({'artifact':ARTIFACT.as_posix(),'target_spans':9,'excluded_runtime_context_spans':1,
         'native_sites':len(selected),'literal_count':len(literals),'original_inputs':inputs,
         'derived_decoded_bytes':len(plain),'actual_record_inventory':len(sections),'owned_sources':rows,'source_only':True}))


def final():
    rows=[copy_file(ROOT/relative,f'current/{relative}') for relative in OWNED]
    emit('current-source-origins.json',rows)
    emit('delivery.json',{'round':'20261008-tw-native-rom-geometry-source','owned_sources':rows,
         'BATCHFINAL_received':True,'only_owned_stable_source_current_pinned':True,
         'native_original_inputs_manifest':'native-original-inputs.json','derived_decoded_manifest':'decoded-input.json',
         'target_spans':9,'excluded_runtime_context_spans':1,'new_opcodes':0,'full_routes_added':0,
         'whole_game_percentage':None,'source_only':True})
    members=[]
    for path in sorted(ARTIFACT.rglob('*')):
        if path.is_file():
            raw=path.read_bytes();members.append({'path':path.relative_to(ARTIFACT).as_posix(),
                  'bytes':len(raw),'sha256':sha(raw)})
    emit('seal.json',{'format':'god2-agent-full-artifact-seal-v1','members':members,
         'member_count':len(members),'source_only':True,'whole_game_percentage':None})
    print(json.dumps({'members':len(members),'current_originals':len(rows),
         'seal_sha256':sha((ARTIFACT/'seal.json').read_bytes()),'owned_sources':rows}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final',action='store_true',help='only after explicit parent BATCHFINAL')
    args=parser.parse_args()
    final() if args.final else recover()
