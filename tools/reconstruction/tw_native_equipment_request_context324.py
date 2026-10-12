"""PHASE1 bounded PE/Capstone source capture; no native execution or game SQL."""
import hashlib
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

SERVER = Path(__file__).resolve().parents[2]
ARCHIVES = Path.home() / '.codex/artifact-archives/god2-server/20261012'
INPUT = ARCHIVES / 'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT = ARCHIVES / 'tw-native-equipment-request-context-source-324'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    # A completed capture is immutable. Do not overwrite historical evidence.
    OUT.mkdir(exist_ok=False)
    image = (INPUT / 'native-image.bin').read_bytes()
    original = (INPUT / 'originalPE.bin').read_bytes()
    if sha(image) != '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':
        raise ValueError('Mapped input identity differs')
    if sha(original) != '5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':
        raise ValueError('Original PE identity differs')
    pe = pefile.PE(data=original)
    md = Cs(CS_ARCH_X86, CS_MODE_32)

    def put(name, value):
        (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf8')

    refs = []
    for name, raw in [('native-image.bin', image), ('originalPE.bin', original)]:
        refs.append(dict(path=str(INPUT / name), bytes=len(raw), sha256=sha(raw),
                         copied=False, scope='Full input hashed; only selected code retained here'))
    put('native-input-references.json', refs)
    spans = []
    maps = {}

    def capture(name, start, end, scope):
        raw = image[start - 0x400000:end - 0x400000]
        offset = pe.get_offset_from_rva(start - 0x400000)
        if original[offset:offset + len(raw)] != raw:
            raise ValueError('Original PE code differs')
        rows = list(md.disasm(raw, start))
        if sum(i.size for i in rows) != len(raw):
            raise ValueError('Incomplete static decode')
        maps[name] = rows
        (OUT / (name + '.bin')).write_bytes(raw)
        (OUT / (name + '.tsv')).write_text('va\tbytes\tmnemonic\toperands\n' + ''.join(
            f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows), encoding='utf8')
        spans.append(dict(name=name, va=f'{start:08X}', end_exclusive=f'{end:08X}',
                          bytes=len(raw), sites=len(rows), sha256=sha(raw), original_pe_offset=offset,
                          original_pe_equal=True, scope=scope))
        return rows

    ui = capture('known-ui-boundary-map', 0x49a330, 0x49b5d1,
                 'Mechanical complete known method map; selected caller only manually reviewed')
    producer = capture('known-producer-boundary-map', 0x496550, 0x49660b,
                       'Known complete producer; only return/call relationship credited')
    capture('post-request-panel', 0x4d5910, 0x4d5968, 'Complete direct method; child calls bounded below')
    capture('panel-selection-reset', 0x4d7940, 0x4d7974,
            'Complete direct child; 5073E0 remains opaque')
    capture('panel-related-dismiss', 0x4dc830, 0x4dc871,
            'Complete direct child; 507BB0 remains opaque')
    capture('panel-local-word-reset', 0x4d7de0, 0x4d7de7, 'Complete leaf writing UI+52=FFFF')
    replacement = capture('known-replacement-selector', 0x4999c0, 0x499a59,
                          'Known method, now exact selected fields/loop/return reviewed; no invocation owner inferred')
    starts = {i.address for i in ui}
    ends = {i.address + i.size for i in ui}
    if 0x49a58f not in starts or 0x49a5ce not in ends:
        raise ValueError('Selected caller not aligned in actual method')
    capture('actual-ui-post-request-cut', 0x49a58f, 0x49a5ce,
            'Selected known UI caller, anchored in actual complete boundary map')
    calls = []
    for address, target in [(0x49a5b5, 0x496550), (0x49a5bc, 0x4d5910),
                            (0x4d5947, 0x4d7940), (0x4d5961, 0x4dc830),
                            (0x4d7944, 0x4d7de0), (0x499a39, 0x496550), (0x499a4b, 0x496550)]:
        raw = image[address - 0x400000:address - 0x400000 + 5]
        if raw[0] != 0xe8 or address + 5 + int.from_bytes(raw[1:], 'little', signed=True) != target:
            raise ValueError('Direct call differs')
        calls.append(dict(va=f'{address:08X}', bytes=raw.hex(), target=f'{target:08X}'))
    put('spans.json', spans)
    put('direct-calls.json', calls)
    put('manual-trace.json', dict(
        ui='49A5B5 calls496550 then49A5BC calls4D5910 without testing a return/status. Metadata11A bit04 and49B5E0==1 are prior client gates.',
        panel='4D5910 tests signed panelWORD232E66>=0 and rowE2988 bit20; active branch writes UI+50=0, calls4D7940,507BB0,4DC830. No inventory/DA/stat body is built in this direct method; opaque UI helper effects remain open.',
        children='4D7940 calls4D7DE0 (UI+52=FFFF) then5073E0 twice with26 and32;4DC830 independently tests signed panelWORD232EA2 and row bit20, writes UI+50=0 and calls507BB0. No whole UI helper closure claimed.',
        selector='4999C0 scans equipment30..37 in increasing order for key!=0 and ((instanceDWORD+0C)&7F00)<=0200. First selected key searches bag0..29 increasing for same lowWORD key and masked value>0200. It reads no count byte on either search.',
        fallback='No qualifying bag:496550(key,equipmentSlot,1). First qualifying bag:496550(key,bagSlot,1). It never continues to a later equipment slot after selecting the first eligible one.',
        returns='Both request branches unconditionally return EAX=1 after496550; no success check. Empty equipment scan returns0. Producer has modal/gate exits before4132E0; selector return1 is not emission or server acceptance proof.',
        width='Packed field is seven bits8..14 of instanceDWORD+0C (byte13 low7), not byte12, not quantity, not metadata396. No durability/repair/quality semantic name or server eligibility inferred.',
        open=['Original full next inventory/native1200 cache/DA15/frozen2A source and real C28 Action',
              'Original3B/41 opaque/count metadata, complete stat/self/observer order and post-COMMIT recovery',
              'Actual4999C0 invocation/phase ownership and opaque5073E0/507BB0 effects',
              'Whole-game route denominator and source-completion percentage']))
    source_paths = ['AGENTS.md', 'docs/GOAL_ACCEPTANCE.md', 'docs/IMPLEMENTATION_PROVENANCE.md',
                    'docs/research/current-player-equipment-frontier-20260926.md',
                    'docs/research/current-weapon-mapping-fields-20260926.md',
                    'docs/research/tw-native-entry-npc-label-source-20261012.md',
                    'tools/reconstruction/tw_native_equipment_request_context324.py']
    (OUT / 'sources').mkdir()
    sources = []
    for index, name in enumerate(source_paths):
        raw = (SERVER / name).read_bytes()
        retained = f'sources/{index:02d}-{Path(name).name}'
        (OUT / retained).write_bytes(raw)
        sources.append(dict(path=name, retained=retained, bytes=len(raw), sha256=sha(raw)))
    put('source-inputs.json', sources)
    put('readscope.json', dict(phase='PHASE1 static files/Capstone only', native_execution=False,
        builds=0, tests=0, resource_codec=False, database_SQL=False, deploy=False,
        new_native_method_credit=0, global_novelty=False, new_cpp_sources=0,
        complete_routes_increment=0, opcode_increment=0, whole_game_percentage=None,
        history='Known20260926 method descriptions retained. No global prior coverage scan or new-byte novelty claim.',
        exploratory='Unaligned exploratory stdout cuts excluded; final selected UI cut aligned against actual complete method map.'))
    members = []
    for path in sorted(OUT.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            members.append(dict(path=path.relative_to(OUT).as_posix(), bytes=len(raw), sha256=sha(raw)))
    put('seal.json', dict(members=members, count=len(members), bytes=sum(m['bytes'] for m in members),
                          excludes='seal.json only; external native inputs are hashed references, not captured members'))
    print(json.dumps(dict(root=str(OUT), seal_sha256=sha((OUT / 'seal.json').read_bytes()),
                          members=len(members), member_bytes=sum(m['bytes'] for m in members),
                          new_complete_routes=0, new_native_methods=0)))


if __name__ == '__main__':
    main()
