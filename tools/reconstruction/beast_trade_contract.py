"""Bounded original native trade bytes/disassembly; no runtime verification.

PET eligibility, selector rebinding and storage pairing are CUSTOM0085.
"""
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
        raise ValueError('Original mapped native input changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    functions = []
    for start, end, purpose in [
        (0x97250, 0x97290, 'C2S29 targetWORD/opaqueWORD'),
        (0x97290, 0x972ee, 'C2S2A direct quantity1 and pointer quantity-dialog producers'),
        (0x97a30, 0x97a60, 'C2S2B targetWORD/opaqueWORD/moneyDWORD'),
        (0x97a60, 0x97a82, 'C2S2C/2D controlBYTE producer'),
        (0x9e440, 0x9e78b, 'native ordinary drag caller: source0..29,count1 ->97290; full24 copy without class-specific eligibility branch'),
        (0x9d980, 0x9e050, 'original trade consumers and adjacent native helpers; bounded interval'),
        (0x9fb40, 0x9fbc7, '4B selection presentation'),
        (0x991e0, 0x99300, '41 physical clear and matching beast presentation close')]:
        code = raw[start:end]
        functions.append({'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
                          'purpose': purpose, 'bytes_hex': code.hex(),
                          'sha256': hashlib.sha256(code).hexdigest(),
                          'instructions': [{'rva': f'{i.address-BASE:X}',
                                            'instruction': f'{i.mnemonic} {i.op_str}'}
                                           for i in md.disasm(code, BASE+start)]})
    receivers = []
    for opcode in (0x4e, 0x50, 0x51, 0x53, 0x4f, 0x52, 0x27, 0x4b, 0x3b, 0x41):
        leaf = struct.unpack_from('<I', raw, 0x1324+opcode*4)[0]-BASE
        dispatch = struct.unpack_from('<I', raw, 0x6b5d4+opcode*4)[0]-BASE
        receivers.append({'opcode': f'{opcode:02X}', 'length_leaf_rva': f'{leaf:X}',
                          'length_leaf_hex': raw[leaf:leaf+6].hex(),
                          'logical_size': struct.unpack_from('<i', raw, leaf+1)[0],
                          'dispatcher_rva': f'{dispatch:X}',
                          'dispatcher_hex': raw[dispatch:dispatch+24].hex()})
    return {'format': 'god2-static-beast-trade-source-contract-v1',
            'method': 'bounded original mapped-image disassembly only',
            'tests_builds_emulator_client_execution': False,
            'mapped_image': {'path': IMAGE, 'sha256': PIN},
            'functions': functions, 's2c': receivers,
            'custom_source_route': {
                'design': 'CUSTOM-0085 extends opt-in CUSTOM-0069; both flags required',
                'entry': 'Application owned_trade_peer -> OwnedInstanceTradeService',
                'requests': '29 open,2A item,2B money,2C confirm,2D cancel; no new opcode',
                'rules': 'LuaEngine::beast_transfer_allowed / gameplay/beast_transfer.lua',
                'admitted': 'already owned whole count1 ordinary PET, no native exploring label or alternate7/8 presentation; both ready same scene, full PET projection, no pending battle',
                'storage': 'same-connection complete both-owner scalar/overlay/wallet/PET/raw-selection CAS; full typed unrelated schema/history guard; atomic ownership transfer after both confirmations',
                'identity': 'CUSTOM per-character selector: retain if unused, otherwise lowest unused BYTE; only logical3 of4C/nullableC5 rebinding; preserve all remaining bytes/origin/evidence/pins',
                'selection': 'retire outgoing matching valid or stale sender selection before FK parent removal; no recipient auto-selection/activity',
                'replies': '4E open,50 full peer instance,51 money,53 confirmation;52 success close or4F rollback close then4B(0,0)/full30 native41/3B/41 bag projection/S2C27 purse',
                'restoration': 'cancel/disconnect/60s custom timeout uses fresh owned state; reconnect existing full PET projection/valid selected4C',
                'view': 'retire per-session custom exploration menu lease on trade delivery; no activity cancellation',
                'journal': 'existing0069 receipt DDL/history untouched; conditional tagged0085 full PET/selection before+after state on new receipts',
                'schema_installed': False, 'source_activation': False, 'deployment': False,
                'native_client_acceptance': False, 'native_original_server_pairing': False},
            'remaining': ['original bind/transfer/activity eligibility',
                          'bank full PET custody, ground pickup/drop, acquisition and rewards',
                          'food, riding, exploration authority and self/observer appearance',
                          'whole-game phase2 comprehensive tests then phase3 repairs']}


def main():
    output = SERVER/'artifacts/integration/packet-connections-20261006/beast-trade-static-contract.json'
    output.write_text(json.dumps(recover(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(output), 'method': 'STATIC_ONLY',
                      'client_execution_tests_builds': False}))


if __name__ == '__main__':
    main()
