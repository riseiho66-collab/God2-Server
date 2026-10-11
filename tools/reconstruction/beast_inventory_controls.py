"""Bounded original-code disassembly for PET25 and4D inventory projection.

No native emulation, tests, builds, database writes or client execution.
"""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE
from .beast_panel_contract import section_rows
from .beast_source_catalog import SOURCE, DECODED


def recover():
    reader = ArchivedInputs()
    source_path = 'artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/gamedata.csvZ'
    try:
        raw = reader.read(IMAGE)
        gamedata = reader.read(source_path)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped native source identity changed')
    food = section_rows('Data2/Patch/Comm/gamedata.csvZ', b'PFD', None,
                        compressed=gamedata, path_label=source_path)
    if food['compressed_sha256'] != SOURCE or food['decoded_sha256'] != DECODED:
        raise ValueError('Original food source identity changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    ranges = [
        (0x9a330, 0x9b5e0, 'whole inventory event handler; same-slot PET25 at9AA07; C2S28 domain separate'),
        (0xa0470, 0xa04d0, 'food lane0 producer dispatch; no food eligibility or gain rule'),
        (0xa0970, 0xa0a90, '4D selected panel writes then guarded inventory class5 writes'),
        (0x98dd0, 0x98fc0, '3B full metadata consumer; slot37 key change closes beast UI'),
        (0x991e0, 0x99300, '41 count/key consumer; closes UI when slot matches85ABD'),
        (0x9fbd0, 0x9fc10, 'beast panel close invokes exploration9F and local state cleanup'),
    ]
    functions = []
    for start, end, purpose in ranges:
        code = raw[start:end]
        functions.append({
            'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}', 'purpose': purpose,
            'bytes_hex': code.hex(), 'sha256': hashlib.sha256(code).hexdigest(),
            'instructions': [{'rva': f'{i.address-BASE:X}', 'instruction': f'{i.mnemonic} {i.op_str}'}
                             for i in md.disasm(code, BASE+start)]})
    return {
        'format': 'god2-static-beast-inventory-controls-v2',
        'correction': 'V1 incorrectly subtracted record+4 twice. UI85610 is metadata0; inventory writes are WORD10, BYTE9, WORD12. V1 retained as prior analysis.',
        'method': 'bounded mapped-image disassembly only',
        'tests_builds_emulator_client_execution': False,
        'mapped_image': {'path': IMAGE, 'sha256': PIN},
        'functions': functions,
        'panel25': {
            'shortcut': '963C0 quotient53/55; source PET membership independently required',
            'same_slot_release': '9A330: selected0..49, mask20, same-slot, metadata flag4, quotient52/53/54 ->9AD06 modal gate ->9AA07 call96350',
            'other_alternative': 'packed type35; not automatically PET or COM/NCP',
            'source_integration': 'OwnedBeastPanelService expanded52/54; ordinary0..29 and separately ledger-qualified37 custody',
            'pairing': 'CUSTOM0085 25->4B/4C presentation, not original server effect recovery'},
        'delta4d_inventory': {
            'consumer_rva': 'A0970', 'guard_and_writes_rva': 'A0A11..A0A8C',
            'slot': 'body0 BYTE indexes native inventory24-byte records; no native0..29 guard here',
            'guard': 'metadata DWORD0 bits16..21 type5 and delta body2 BYTE1..6',
            'metadata20_writes': {
                '10': 'WORD low3 palette = body2 &7, upper13 preserved',
                '9': 'full level BYTE = body3; metadata8 lowBYTE preserved',
                '12': 'WORD = body6; tooltip EXP percent only for original PET column27 lowBYTE0; nonzero definition uses packed-date branch'},
            'preserved': 'key, type, every other inventory metadata byte; no numerator or percentage BYTE copy',
            'namespace': 'body2 inventory palette low3 and selected panel instance selector BYTE are distinct native fields',
            'source_integration': 'RecoveredBeastPanel::apply_inventory_delta pure projection, not an authorized mutation'},
        'food6b': {
            'dispatch': 'A0470 selected dragged inventory slot ->972F0 lane0,85ABD selector,slot BYTE',
            'rule_gap': 'No original food eligibility, consumption, gain/cap or request-response pairing in producer',
            'original_pfd_source': food,
            'description_scope': 'PFD6901..6905 fatigue-15;6906..6910 loyalty+10;6911..6915 experience+1 text only; not executable formulas or packet-field mapping',
            'separate_generation': 'MED01 two-generation mount food3026 onward must not replace PET/PFD or MED02 HP/MP policy'},
        'equipment37': {
            '3b': '98EF8..98F13: slot37 and key changed ->9FBD0 closes panel; does not reopen or synthesize4C',
            '41': '992A9..992B8: matching85ABD slot ->9FBD0 closes panel',
            'close': '9FBD0 ->D8610 exploration close and A01A0 local cleanup',
            'storage_scope': 'Source CUSTOM0085 additive equipmentv2 supports bag/37 custody and28 placement; originalv1 ledgers preserved; migration NOT executed; activity/appearance still open'},
        'remaining': ['PET equipment activity/stat/appearance effects and other protected domains',
                      'Food eligibility, Lua effect/consumption rules and atomic4D full-owned-state mutation',
                      'Original acquisition, activity timers/results and self/observer appearance']}


def main():
    output = SERVER/'artifacts/integration/packet-connections-20261006/beast-inventory-controls-static.json'
    prior=output.with_name('beast-inventory-controls-static-v1-prior-analysis.json')
    if output.exists() and not prior.exists():
        prior.write_bytes(output.read_bytes())
    output.write_text(json.dumps(recover(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(output), 'method': 'STATIC_ONLY',
                      'tests_builds_client_execution': False}))


if __name__ == '__main__':
    main()
