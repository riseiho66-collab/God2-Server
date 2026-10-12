"""PHASE1 native E5 family0/2 file/PE/Capstone custody; no runtime or SQL."""
from pathlib import Path
import hashlib
import json
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

SERVER = Path(__file__).resolve().parents[2]
BASE = Path.home() / '.codex/artifact-archives/god2-server/20261012'
INPUT = BASE / 'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT = BASE / 'tw-native-e5-family02-capture-327'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    image = (INPUT / 'native-image.bin').read_bytes()
    original = (INPUT / 'originalPE.bin').read_bytes()
    if sha(image) != '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':
        raise ValueError('Mapped image identity differs')
    if sha(original) != '5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':
        raise ValueError('Original PE identity differs')
    pe = pefile.PE(data=original)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    cuts = []

    def put(name, value):
        (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf8')

    def cut(name, start, end, scope, code=True):
        raw = image[start-0x400000:end-0x400000]
        offset = pe.get_offset_from_rva(start-0x400000)
        if original[offset:offset+len(raw)] != raw:
            raise ValueError('PE bytes differ: ' + name)
        rows = list(md.disasm(raw, start)) if code else []
        if code and sum(i.size for i in rows) != len(raw):
            raise ValueError('Incomplete static decode: ' + name)
        (OUT / (name + '.bin')).write_bytes(raw)
        if code:
            (OUT / (name + '.tsv')).write_text('va\tbytes\tmnemonic\toperands\n' + ''.join(
                f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows), encoding='utf8')
        cuts.append(dict(name=name, va=f'{start:08X}', end_exclusive=f'{end:08X}',
                         bytes=len(raw), sites=len(rows), sha256=sha(raw),
                         original_pe_offset=offset, original_pe_equal=True, code=code, scope=scope))

    cut('family0-inventory', 0x4a32d0, 0x4a331c,
        'Complete actual family0 function; signed slot and no slot/owner guard')
    cut('family2-pet1', 0x4a33f0, 0x4a36ec,
        'Complete actual family2 function; only direct writes/guards qualified; HUD/GUI children opaque')
    cut('family2-target-table', 0x4a36ec, 0x4a3748, '23 actual target DWORDs', False)
    cut('family2-translation', 0x4a3748, 0x4a376a, '34 actual selector bytes', False)
    cut('known-pet1-slot-guard', 0x4a2980, 0x4a2999, 'Known complete slot guard, not new method credit')
    cut('known-pet1-metadata-guard', 0x4a29a0, 0x4a2a04,
        'Known complete metadata predicate; actual lookup/assert children opaque')
    put('selector-map.json', [dict(selector=i, translation=image[0xa3748+i],
        target=f'{struct.unpack_from("<I", image, 0xa36ec+image[0xa3748+i]*4)[0]:08X}') for i in range(34)])
    put('cuts.json', cuts)
    put('native-input-references.json', [dict(path=str(INPUT/name), bytes=len(raw), sha256=sha(raw), copied=False)
        for name, raw in [('native-image.bin', image), ('originalPE.bin', original)]])
    sources = []
    for name in ['src/protocol/RecoveredE5Update.h', 'src/protocol/RecoveredPet1Stats.h',
                 'tools/reconstruction/tw_native_e5_family02_capture327.py',
                 'docs/research/tw-native-pet2-e5-update-source-20261012.md']:
        raw = (SERVER / name).read_bytes()
        target = OUT / 'sources' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        sources.append(dict(path=name, retained='sources/'+name, bytes=len(raw), sha256=sha(raw)))
    put('source-inputs.json', sources)
    put('scope.json', dict(method='STATIC_FILE_PE_CAPSTONE_ONLY', builds=0, tests=0,
        native_execution=False, runtime=False, resource_codec=False, game_database_SQL=False,
        deploy=False, new_complete_routes=0, global_native_novelty=False,
        incoming_source='Known round326 E5 full9 and4A3320 table; those bytes not recredited',
        exploratory='Initial exploratory unsealed stdout prefixes excluded; retained actual complete functions only'))
    members = []
    for path in sorted(OUT.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            members.append(dict(path=path.relative_to(OUT).as_posix(), bytes=len(raw), sha256=sha(raw)))
    put('seal.json', dict(members=members, count=len(members), bytes=sum(m['bytes'] for m in members),
                          excludes='seal.json only; full native inputs are hashed references'))
    print(json.dumps(dict(root=str(OUT), seal_sha256=sha((OUT/'seal.json').read_bytes()),
        members=len(members), member_bytes=sum(m['bytes'] for m in members),
        code_bytes=sum(c['bytes'] for c in cuts if c['code']), data_bytes=sum(c['bytes'] for c in cuts if not c['code']))))


if __name__ == '__main__':
    main()
