"""Pinned static beast UI disassembly/source extraction; no client execution/tests."""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE
from .beast_panel_contract import section_rows


def recover():
    reader = ArchivedInputs()
    message_path = 'artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/message.csvZ'
    try:
        raw = reader.read(IMAGE)
        message = reader.read(message_path)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped native source identity changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    functions = []
    for start, size, purpose in [
            (0x9fc50, 0x32e, 'main panel construction; control7/8 sprite indices, food ProgramMsg96'),
            (0x9ff80, 0x170, 'local auxiliary panel initialization, not exploration server authority'),
            (0xa0700, 0x8c, 'body6 WORD -> FILD -> FLOAT0.01 -> %6.2f%s and ProgramMsg362'),
            (0xd83a0, 0xef, 'C5 state0/2/other changes local controls; no operation effect recovered'),
            (0xd8680, 0xb0, 'exploration control dispatch to9E producers and local9F close'),
            (0xd89f0, 0x168, 'option rendering/selection: state0 enables options, state2 selected-only')]:
        code = raw[start:start+size]
        functions.append({'rva': f'{start:X}', 'size': size, 'purpose': purpose,
                          'bytes_hex': code.hex(), 'sha256': hashlib.sha256(code).hexdigest(),
                          'instructions': [{'rva': f'{i.address-BASE:X}', 'instruction': f'{i.mnemonic} {i.op_str}'}
                                           for i in md.disasm(code, BASE+start)]})
    end = raw.index(b'\0', 0x190c68, 0x190ca8)
    return {
        'format': 'god2-static-beast-display-controls-v1',
        'method': 'bounded static original-code disassembly and archived resource decoding only',
        'tests_builds_emulator_client_execution': False,
        'mapped_image': {'path': IMAGE, 'sha256': PIN},
        'functions': functions,
        'labels': section_rows('Data2/Patch/Comm/message.csvZ', b'ProgramMsg',
                              {96, 362, 645, 646, 647}, compressed=message, path_label=message_path),
        'percent_word': {
            'snapshot_body_offset': 6, 'delta_body_offset': 6, 'width': 'WORD',
            'refresh_rva': 'A0700', 'constant_rva': '171204',
            'float_bytes_hex': raw[0x171204:0x171208].hex(),
            'float_value': struct.unpack_from('<f', raw, 0x171204)[0],
            'format_rva': '190C68', 'format_hex': raw[0x190c68:end].hex(),
            'format_ascii': raw[0x190c68:end].decode('ascii'),
            'suffix': 'ProgramMsg362 percent sign; not a time unit',
            'prior_unsupported_name': 'lifetime_display_raw',
            'gameplay_meaning': 'UNKNOWN_PERCENT_DISPLAY_NOT_EXPIRY_TICK_AUTHORITY'},
        'control7_8_sprite_words': {
            'rva': '190C30', 'bytes_hex': raw[0x190c30:0x190c40].hex(),
            'meaning': 'native visual indices only; not original gameplay verbs'},
        'original_rules_remaining': ['control7 all kinds and control8 alternate/non-exploration effects',
                                     '9E operation0/1/2 activity verbs, timers, costs and rewards',
                                     'source-bound PET acquisition and actor appearance']}


def main():
    root = SERVER / 'artifacts/integration/packet-connections-20261006'
    result = recover()
    (root/'beast-display-controls-static.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    panel = root/'beast-panel-static-contract.json'
    prior = root/'beast-panel-static-contract-v2-prior-analysis.json'
    if not prior.exists():
        prior.write_bytes(panel.read_bytes())
    value = json.loads(panel.read_text(encoding='utf-8'))
    value['format'] = 'god2-static-beast-panel-contract-v4' if 'inventory_offset_correction' in value else 'god2-static-beast-panel-contract-v3'
    value['snapshot_fields_body_relative']['6'] = 'percent-display WORD; A0700 FLOAT0.01, %6.2f%s and ProgramMsg362; prior lifetime name unsupported'
    value['delta_fields_body_relative']['6'] = 'same selected percent-display WORD raw; no qualified time unit'
    value['percent_word_correction'] = result['percent_word']
    value['display_controls_evidence'] = 'beast-display-controls-static.json'
    panel.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(root/'beast-display-controls-static.json'),
                      'method': 'STATIC_ONLY', 'client_execution_tests_builds': False}))


if __name__ == '__main__':
    main()
