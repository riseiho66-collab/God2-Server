"""PHASE1 bounded original PE/mapped-byte E5 custody, no native/runtime/SQL."""
from pathlib import Path
import hashlib
import json
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

INPUT = Path.home() / '.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT = Path.home() / '.codex/artifact-archives/god2-server/20261012/tw-native-pet2-e5-capture-326'
SERVER = Path(__file__).resolve().parents[2]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    image = (INPUT / 'native-image.bin').read_bytes()
    original = (INPUT / 'originalPE.bin').read_bytes()
    if sha(image) != '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':
        raise ValueError('Mapped identity changed')
    if sha(original) != '5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':
        raise ValueError('Original PE identity changed')
    pe = pefile.PE(data=original)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    cuts = []
    def write(name, value):
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    def cut(name, va, end, scope, code=True):
        rva = va - 0x400000
        raw = image[rva:end - 0x400000]
        offset = pe.get_offset_from_rva(rva)
        if original[offset:offset + len(raw)] != raw:
            raise ValueError('Original PE cut differs: ' + name)
        (OUT / (name + '.bin')).write_bytes(raw)
        rows = list(md.disasm(raw, va)) if code else []
        if code and sum(i.size for i in rows) != len(raw):
            raise ValueError('Incomplete cut decode: ' + name)
        if code:
            (OUT / (name + '.tsv')).write_text('va\tbytes\tmnemonic\toperands\n' + ''.join(
                f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows), encoding='utf8')
        cuts.append(dict(name=name, va=f'{va:08X}', end_exclusive=f'{end:08X}', bytes=len(raw),
                         instruction_sites=len(rows), sha256=sha(raw), original_pe_offset=offset,
                         original_pe_equal=True, scope=scope, code=code))
        return raw
    cut('e5-generation-dispatch', 0x4a3320, 0x4a3362, 'Complete actual dispatcher method; child branches0/1/2 remain opaque')
    cut('e5-generation-table', 0x4a3364, 0x4a3374, 'Four actual high2-bit table cells', False)
    cut('e5-pet2-update', 0x4a5a40, 0x4a5d05, 'Complete actual method through RET4; child calls and GUI authority not recovered')
    cut('e5-pet2-update-table', 0x4a5d08, 0x4a5d50, '18 actual low6 selector targets', False)
    cut('e5-pet2-update-translation', 0x4a5d50, 0x4a5d73, '35 actual low6 translation bytes', False)
    cut('pet2-slot-guard', 0x4a5070, 0x4a5089, 'Complete actual leaf, slotBYTE42..44')
    cut('pet2-metadata-guard', 0x4a5090, 0x4a50ee, 'Complete actual method; metadata lookup459A60/assert402C70 remain opaque')
    cut('world-e5-case', 0x4691d9, 0x4691eb, 'Actual selected WORLD case, not a method entry')
    cut('world-e5-table-cell', 0x46b968, 0x46b96c, 'Original worldtable[E5]', False)
    cut('e5-length-leaf', 0x4012d0, 0x4012d6, 'Complete actual leaf MOV EAX,9/RET')
    cut('e5-length-table-cell', 0x4016b8, 0x4016bc, 'Original lengthtable[E5]', False)
    cut('secondary-map', 0x519370, 0x519908, 'Complete actual secondary receiver mechanical map; only E5 switch case/source joins qualified')
    cut('secondary-e5-translation', 0x519ae9, 0x519aea, 'Translation[E5] ->58', False)
    cut('secondary-e5-target', 0x5199f0, 0x5199f4, 'Actual translated table58 ->519839', False)
    references = [dict(path=str(INPUT/name), sha256=sha(raw), bytes=len(raw), copied=False)
                  for name, raw in [('native-image.bin', image), ('originalPE.bin', original)]]
    source = []
    for rel in ['AGENTS.md', 'docs/GOAL_ACCEPTANCE.md', 'docs/IMPLEMENTATION_PROVENANCE.md',
                'src/protocol/RecoveredPet2Stats.h', 'src/protocol/RecoveredPet2Revert.h',
                'src/handlers/RecoveredPet2RevertGate.cpp',
                'docs/research/current-stat-packet-return-path-20260920.md',
                'docs/research/native-pet2-revert-route-20260930.md']:
        raw = (SERVER / rel).read_bytes()
        dest = OUT / 'source' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        source.append(dict(path=str(SERVER/rel), bytes=len(raw), sha256=sha(raw), retained='source/'+rel))
    ledger = SERVER / 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json'
    raw = ledger.read_bytes()
    lines = raw.decode('utf-8-sig').splitlines()
    exact = '\n'.join(f'{i+1}: {line}' for i, line in enumerate(lines) if 514 <= i < 533) + '\n'
    (OUT / 'ledger-lines-515-533.txt').write_text(exact, encoding='utf8')
    references.append(dict(path=str(ledger), bytes=len(raw), sha256=sha(raw), copied=False,
                           exact_retained='ledger-lines-515-533.txt', scope='Named exact excerpts only, full ledger not copied'))
    write('references.json', references)
    write('source-references.json', source)
    write('cuts.json', cuts)
    write('selector-map.json', [dict(selector=i, translation=image[0xa5d50+i],
        target=f'{struct.unpack_from("<I",image,0xa5d08+image[0xa5d50+i]*4)[0]:08X}') for i in range(35)])
    print(json.dumps(dict(output=str(OUT), cuts=len(cuts), code_bytes=sum(c['bytes'] for c in cuts if c['code']),
                          data_bytes=sum(c['bytes'] for c in cuts if not c['code']), new_complete_routes=0)))

if __name__ == '__main__':
    main()
