"""Static file/hash/PE/Capstone capture only. No native execution or source imports."""
from pathlib import Path
import hashlib
import json
import struct
import capstone
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_MEM, CS_AC_WRITE
from capstone.x86_const import X86_REG_ESI, X86_REG_ESP

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
MAPPED = BASE / 'tw-native-entry-body-alias-and-remote-opaque-315/native-entry/native-image.bin'
PE = BASE / 'tw-native-entry-body-alias-and-remote-opaque-315/native-entry/originalPE.bin'
EXPECTED = ('149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763',
            '5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde')
def sha(b):
    return hashlib.sha256(b).hexdigest()
def out(name, value):
    p = ROOT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        p.write_bytes(value)
    else:
        p.write_bytes(value.encode('utf-8'))
def jout(name, value):
    out(name, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

b = MAPPED.read_bytes()
p = PE.read_bytes()
assert (sha(b), sha(p)) == EXPECTED
pe = pefile.PE(data=p)
assert pe.OPTIONAL_HEADER.ImageBase == 0x400000
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
refs = [{'path': str(x), 'bytes': len(v), 'sha256': sha(v)} for x, v in [(MAPPED,b),(PE,p)]]
for package in ['tw-native-e5-egg-input-source-328', 'tw-native-petegg-selection-source-329']:
    seal_path = BASE / package / 'seal.json'
    seal_bytes = seal_path.read_bytes()
    seal = json.loads(seal_bytes)
    for member in seal['members']:
        raw = (seal_path.parent / member['path']).read_bytes()
        assert len(raw) == member['bytes'] and sha(raw) == member['sha256']
    refs.append({'path': str(seal_path), 'bytes': len(seal_bytes), 'sha256': sha(seal_bytes),
                 'verified_individual_members': len(seal['members'])})
jout('source-references.json', {'inputs': refs, 'capstone': capstone.__version__, 'pefile': pefile.__version__})
jout('sections.json', [{'name_hex': s.Name.hex(), 'rva': s.VirtualAddress,
    'virtual_size': s.Misc_VirtualSize, 'raw_offset': s.PointerToRawData,
    'raw_size': s.SizeOfRawData, 'characteristics': s.Characteristics,
    'execute_flag': bool(s.Characteristics & 0x20000000)} for s in pe.sections])

cuts = []
def cut(name, start, end, complete=False):
    raw = b[start-0x400000:end-0x400000]
    original_offset = pe.get_offset_from_rva(start-0x400000)
    assert raw == p[original_offset:original_offset+len(raw)]
    ins = list(md.disasm(raw,start))
    assert sum(i.size for i in ins) == len(raw)
    if complete:
        assert ins[-1].mnemonic == 'ret'
        addresses = {i.address for i in ins}
        for i in ins:
            if i.mnemonic.startswith('j') and i.operands[0].type == capstone.CS_OP_IMM:
                assert i.operands[0].imm in addresses
    out('native/'+name+'.bin',raw)
    out('native/'+name+'.tsv', 'va\traw_hex\tmnemonic\toperands\n' + ''.join(
        f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins))
    cuts.append({'name':name,'start_va':f'{start:08X}','end_exclusive_va':f'{end:08X}',
        'bytes':len(raw),'sha256':sha(raw),'original_pe_offset':original_offset,
        'mapped_pe_equal':True,'complete_entry_all_returns':complete,
        'ret_sites':[f'{i.address:08X}' for i in ins if i.mnemonic=='ret'],
        'instruction_sites':len(ins),'method_credit':0})
    return ins

parent = cut('known-inventory-action-complete',0x49A330,0x49B5D1,True)
cut('necessary-drag-visual-child-complete',0x499A60,0x499AD4,True)
cut('known-slot-validator-complete',0x4D6C40,0x4D6C7A,True)
cut('known-slot-key-validator-complete',0x4D6C80,0x4D6D1E,True)
# Excerpts are explicitly not function constructions. Their complete enclosing
# inventory action / primary dispatcher is captured here or retained in329.
cut('actual-primary-inventory-invocation-excerpt',0x4825AC,0x4825CB)
cut('false-u8-hit-formal-output-excerpt',0x46714A,0x4671AB)
cut('main-primary-alias-prefix-excerpt',0x466B00,0x466B14)
jout('native/cuts.json',cuts)
out('native/inventory-action-direct-esi-writes.tsv', 'va\twidth\tdisplacement\toperands\n'+''.join(
    f'{i.address:08X}\t{i.operands[0].size}\t{i.operands[0].mem.disp:X}\t{i.op_str}\n'
    for i in parent if i.operands and i.operands[0].type==CS_OP_MEM and
    i.operands[0].mem.base==X86_REG_ESI and i.operands[0].access & CS_AC_WRITE))
out('native/inventory-action-all-calls.tsv','va\toperands\n'+''.join(
    f'{i.address:08X}\t{i.op_str}\n' for i in parent if i.mnemonic=='call'))

hits = []
for target in [0x4D53F0,0x4D4B80,0x4D6C80,0x4D5970,0x49A330]:
    for off in range(len(b)-5):
        if b[off] in (0xE8,0xE9) and off+0x400005+struct.unpack_from('<i',b,off+1)[0]==target:
            hits.append({'candidate_va':f'{off+0x400000:08X}','opcode':f'{b[off]:02X}',
                'target_va':f'{target:08X}','scope':'all mapped bytes; candidate only, not code qualification'})
jout('raw-rel32-candidates.json',hits)
byte_hits = []
for off,x in enumerate(b):
    if x not in (0x88,0xC6):
        continue
    i = next(md.disasm(b[off:off+16],off+0x400000,count=1),None)
    if i and i.mnemonic=='mov' and i.operands[0].type==CS_OP_MEM and \
       i.operands[0].mem.disp==8 and i.operands[0].mem.index==0 and i.operands[0].mem.base!=X86_REG_ESP:
        byte_hits.append({'candidate_va':f'{i.address:08X}','raw_hex':i.bytes.hex(),
                         'operands':i.op_str,'code_or_alias_proof':False})
jout('raw-byte-disp8-candidates.json',byte_hits)
jout('capture-summary.json',{'full_body_bytes':sum(c['bytes'] for c in cuts if c['complete_entry_all_returns']),
    'excerpt_bytes':sum(c['bytes'] for c in cuts if not c['complete_entry_all_returns']),
    'data_bytes':0,'full_bodies':4,'method_credit':0,'opcode_credit':0,'connected_route_credit':0,
    'strict_execute_sections':sum(bool(s.Characteristics&0x20000000) for s in pe.sections),
    'raw_byte_candidate_count':len(byte_hits),'raw_rel32_candidate_count':len(hits)})
print(json.dumps({'capture':'successful static only','cuts':len(cuts),
                  'full_body_bytes':sum(c['bytes'] for c in cuts if c['complete_entry_all_returns'])}))
