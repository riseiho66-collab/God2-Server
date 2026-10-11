"""Original native bank disassembly only; no execution or verification suite."""
import hashlib
import json
import struct
import capstone
from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Original native input pin differs')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    regions = []
    for start, end, purpose in [
        (0x97510, 0x97920, 'original65/63/64 direct and quantity-dialog producers'),
        (0x719b0, 0x71e50, 'native whole-cell swap caller and eligibility helpers'),
        (0x71e50, 0x722b0, 'native48 full24 storage/render and adjacent helpers'),
        (0x723a0, 0x724e0, 'bag-to-bank direct/quantity caller'),
        (0x9f010, 0x9f8d0, 'bank-to-bag native mode17 dispatch and adjacent modes')]:
        code = raw[start:end]
        regions.append({'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
                        'purpose': purpose, 'bytes_hex': code.hex(),
                        'sha256': hashlib.sha256(code).hexdigest(),
                        'instructions': [{'rva': f'{i.address-BASE:X}',
                                          'instruction': f'{i.mnemonic} {i.op_str}'}
                                         for i in md.disasm(code, BASE+start)]})
    receivers = []
    for opcode in (0x48, 0x3b, 0x41, 0x4b):
        leaf = struct.unpack_from('<I', raw, 0x1324+opcode*4)[0]-BASE
        dispatch = struct.unpack_from('<I', raw, 0x6b5d4+opcode*4)[0]-BASE
        receivers.append({'opcode': f'{opcode:02X}', 'length_leaf_rva': f'{leaf:X}',
                          'logical_size': struct.unpack_from('<i', raw, leaf+1)[0],
                          'length_leaf_hex': raw[leaf:leaf+6].hex(),
                          'dispatcher_rva': f'{dispatch:X}',
                          'dispatcher_hex': raw[dispatch:dispatch+24].hex()})
    return {'format': 'god2-static-beast-bank-source-contract-v1',
            'method': 'bounded mapped-image disassembly only',
            'tests_builds_emulator_client_execution': False,
            'mapped_image': {'path': IMAGE, 'sha256': PIN}, 'regions': regions,
            'c2s': {'logical_size': 7,
                    'layout': '63/64/65 targetWORDLE pageBYTE sourceBYTE destinationBYTE quantityBYTE',
                    'quantity': '63/64 actual amount;65 final1 whole-cell marker, not amount'},
            's2c': receivers,
            'native48_layout': 'logical29: page1, quantity5, localSlot6, metadata20@9; opaque2..4/7..8',
            'custom_source_route': {
                'design': 'CUSTOM-0085 extends opt-in0070; both flags required',
                'entry': 'Application original full-frame63/64/65 capture and positioned late dispatch -> OwnedMixedBankService',
                'rules': 'LuaEngine::beast_bank_allowed / gameplay/beast_bank.lua; inactive whole count1 PET',
                'storage': 'SqliteBeastBankRepository same-connection full50 bag/300 vault/all overlays/PET/raw-selection snapshot and typed unrelated row/schema/history/money preservation',
                'operations': '63 bag->empty vault,64 vault->empty bag,65 whole vault swap including complete qualified armor/weapon/gem/plain neighbour; pages0..2/local2..49',
                'identity': 'CUSTOM bag/vault selector namespaces; retain if free else lowest unused BYTE; only logical3 of4C/nullableC5 rebound; all other raw bytes/origin/evidence/pins retained',
                'selection': 'deposit retires matching valid/stale bag selection before FK parent removal; withdraw does not auto-select; others remain exact',
                'feature': 'independent beast_bank_schema_0085 version4 with empty vault-custody/receipt tables, no old ledger/DDL/receipt rewrite, no instance or capacity grant',
                'replies': 'all300 full48 on opening; changed full48 after commit and4B(0,0)/full30 native41/3B/41 bag; fresh full restoration after refusal; menu lease retirement only',
                'access': 'existing bank NPC/placement/money lease; no new banker, unlock or funding rule; existing scalar capacity provisioning remains owned opening only',
                'schema_installed': False, 'source_activation': False, 'deployment': False,
                'live_save_mutations': False, 'native_client_acceptance': False,
                'native_original_server_pairing': False},
            'remaining': ['native binding/activity/transfer and edition unlock policies',
                          'acquisition, food, riding, exploration activity and rewards',
                          'self/observer appearance and full whole-game phase2 tests/phase3 repairs']}


def main():
    output = SERVER/'artifacts/integration/packet-connections-20261006/beast-bank-static-contract.json'
    output.write_text(json.dumps(recover(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(output), 'method': 'STATIC_ONLY',
                      'tests_builds_native_execution': False}))


if __name__ == '__main__':
    main()
