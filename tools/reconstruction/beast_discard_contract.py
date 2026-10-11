"""Static original27 producer and4B/41 UI retirement contracts only.

No runtime tests, emulator/client execution, schema install or save mutation.
Request-response pairing and discard eligibility are explicitly CUSTOM0085.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE


def recover():
    reader=ArchivedInputs()
    try:
        raw=reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Selected original mapped native image changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    functions=[]
    for start,end,purpose in [
        (0x97720,0x97760,'original C2S27 raw itemWORD,slotBYTE,quantityBYTE ->queue132E0'),
        (0x9fb40,0x9fbc7,'S2C4B sets85ABD selector to its first bodyBYTE; second bodyBYTE unconsumed'),
        (0x991e0,0x99300,'S2C41 native slot/count/key copy and matching85ABD close'),
        (0x9fbd0,0x9fc04,'closes main beast window, invokes original9F old-context close and auxiliary cleanup'),
        (0xd8610,0xd8672,'old-context C2S9F on a visible exploration window; no activity cancellation proof')]:
        code=raw[start:end]
        functions.append({'rva':f'{start:X}','end_rva_exclusive':f'{end:X}',
                          'purpose':purpose,'bytes_hex':code.hex(),'sha256':hashlib.sha256(code).hexdigest(),
                          'instructions':[{'rva':f'{i.address-BASE:X}','instruction':f'{i.mnemonic} {i.op_str}'}
                                          for i in md.disasm(code,BASE+start)]})
    receivers=[]
    for opcode in (0x4b,0x41):
        leaf=struct.unpack_from('<I',raw,0x1324+opcode*4)[0]-BASE
        dispatch=struct.unpack_from('<I',raw,0x6b5d4+opcode*4)[0]-BASE
        receivers.append({'opcode':f'{opcode:02X}','length_leaf_rva':f'{leaf:X}',
                          'length_leaf_hex':raw[leaf:leaf+6].hex(),
                          'logical_size':struct.unpack_from('<i',raw,leaf+1)[0],
                          'dispatcher_rva':f'{dispatch:X}','dispatcher_hex':raw[dispatch:dispatch+24].hex()})
    return {
        'format':'god2-static-beast-discard-source-contract-v1',
        'method':'bounded original mapped-image disassembly only',
        'tests_builds_emulator_client_execution':False,
        'mapped_image':{'path':IMAGE,'sha256':PIN},'functions':functions,'s2c':receivers,
        'c2s27':{'logical_size':5,'layout':'27 itemWORDLE slotBYTE quantityBYTE',
                 'scope':'client slot/key/quantity supply no generation, owner or native bind/drop policy'},
        'custom_source_route':{
            'design':'CUSTOM-0085',
            'entry':'Application immutable original-frame capture before prefixes, OwnedBeastDiscardService',
            'rules':'LuaEngine::beast_discard_allowed / scripts/gameplay/beast_discard.lua',
            'admitted':'already owned count1 ordinary-bag PET, quantity1, source-qualified native exploring label absent, control7/8 alternate bits absent, ready positioned idle WORLD, no trade/transition/pending battle',
            'storage':'SqliteBeastBagRepository::discard complete full50-slot/custody/raw-selection/peripheral CAS, retire matching valid or stale selection, delete full custody, clear exact scalar with advanced revision',
            'journal':'additive beast_discard_schema_0085 version3; full metadata20/panel4C/nullableC5/origin/evidence/source/client/instance revisions and retired raw selection in removal record',
            'reply':'CUSTOM pairing4B physicalSourceBYTE 00 then41 0000 physicalSourceBYTE 00; makes native85ABD match physical clear and retires current beast presentation',
            'modal_scope':'retire current custom beast view/bank leases; no activity cancellation or other remaining instance selection change',
            'refusal':'current authoritative qualified full source projection from same owner; no stale key echo or forged success',
            'reconnect':'existing WORLD restore emits surviving owned instances/current valid selection; removed instance never reappears from journal',
            'source_activation':False,'schema_installed':False,'deployment':False,
            'native_client_acceptance':False,'native_original_server_pairing':False},
        'remaining':['original bind/drop restrictions, equipment37 and genuine activity-lease domains',
                     'world-ground item creation/pickup, bank/trade full PET transfers',
                     'acquisition, food, riding, activity and self/observer appearance',
                     'full phase2 tests and client acceptance after whole-game source connections']}


def main():
    output=SERVER/'artifacts/integration/packet-connections-20261006/beast-discard-static-contract.json'
    output.write_text(json.dumps(recover(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(output),'method':'STATIC_ONLY','client_execution_tests_builds':False}))


if __name__=='__main__':
    main()
