"""PHASE1 E5 family1 exact source capture: file/hash/PE/Capstone only."""
from pathlib import Path
import hashlib
import json
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

ROOT = Path.home() / '.codex/artifact-archives/god2-server/20261012'
INPUT = ROOT / 'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT = ROOT / 'tw-native-e5-family1-capture-327'
SERVER = Path(__file__).resolve().parents[2]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    image = (INPUT / 'native-image.bin').read_bytes()
    original = (INPUT / 'originalPE.bin').read_bytes()
    if sha(image) != '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':
        raise ValueError('Mapped identity differs')
    if sha(original) != '5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':
        raise ValueError('PE identity differs')
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
            raise ValueError('Incomplete static cut decode: ' + name)
        if code:
            (OUT / (name + '.tsv')).write_text('va\tbytes\tmnemonic\toperands\n' + ''.join(
                f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows), encoding='utf8')
        cuts.append(dict(name=name, va=f'{va:08X}', end_exclusive=f'{end:08X}', bytes=len(raw),
                         sites=len(rows), sha256=sha(raw), original_pe_offset=offset,
                         original_pe_equal=True, scope=scope, code=code))
        return rows
    cut('family1-complete', 0x4d6dd0, 0x4d7083, 'New complete actual family1 method; no child effects substituted')
    cut('family1-table', 0x4d7084, 0x4d70b4, 'New twelve actual selector21..32 table cells', False)
    cut('unsigned-byte-change-marker', 0x4d6db0, 0x4d6dc9, 'New complete pure helper; unsigned lowBYTE comparison only')
    cut('family1-control-bridge', 0x4d7e40, 0x4d7e64, 'New complete direct bridge;507150 remains opaque')
    cut('retained-family-dispatch', 0x4a3320, 0x4a3362, 'Retained326 complete actual dispatcher; only family1 input qualified this round')
    cut('retained-family-table', 0x4a3364, 0x4a3374, 'Retained326 four actual family cells', False)
    cut('retained-world-e5-case', 0x4691d9, 0x4691eb, 'Retained326 actual WORLD case, not method entry')
    cut('retained-world-e5-table-cell', 0x46b968, 0x46b96c, 'Retained326 WORLD E5 target', False)
    cut('retained-e5-length-leaf', 0x4012d0, 0x4012d6, 'Retained326 complete actual length leaf')
    cut('retained-e5-length-cell', 0x4016b8, 0x4016bc, 'Retained326 original E5 length cell', False)
    imports = []
    for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
        for imported in entry.imports:
            if imported.address == 0x5707bc:
                imports.append(dict(iat_va=f'{imported.address:08X}', dll=entry.dll.decode('ascii'),
                                    name=imported.name.decode('ascii') if imported.name else None,
                                    ordinal=imported.ordinal, scope='PE declaration only; never called'))
    references = [dict(path=str(INPUT / name), bytes=len(raw), sha256=sha(raw), copied=False)
                  for name, raw in [('native-image.bin', image), ('originalPE.bin', original)]]
    sources = []
    for rel in ['src/protocol/RecoveredE5Update.h', 'docs/research/tw-native-pet2-e5-update-source-20261012.md',
                'docs/GOAL_ACCEPTANCE.md', 'docs/IMPLEMENTATION_PROVENANCE.md']:
        raw = (SERVER / rel).read_bytes()
        dest = OUT / 'source' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        sources.append(dict(path=str(SERVER / rel), bytes=len(raw), sha256=sha(raw), retained='source/' + rel))
    ledger = SERVER / 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json'
    raw = ledger.read_bytes()
    references.append(dict(path=str(ledger), bytes=len(raw), sha256=sha(raw), copied=False,
                           scope='Reference only; no14MB ledger copy'))
    write('references.json', references)
    write('sources.json', sources)
    write('cuts.json', cuts)
    write('import-declaration.json', imports)
    write('selector-targets.json', [dict(selector=21+i, target=f'{struct.unpack_from("<I",image,0xd7084+i*4)[0]:08X}') for i in range(12)])
    print(json.dumps(dict(output=str(OUT), cuts=len(cuts), code_bytes=sum(c['bytes'] for c in cuts if c['code']),
                          data_bytes=sum(c['bytes'] for c in cuts if not c['code']), gameplay_routes_added=0)))

if __name__ == '__main__':
    main()
