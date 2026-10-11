"""Current-native C2 mode1 five-widget gate, independent of F5-fed modes."""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT=SERVER/'artifacts/integration/packet-connections-20261006/c2-mode1-five-widget-gate-v9.json'
SLICES=((0xb17a0,0xb17b1,'UI event caller of mode1 producer'),
        (0xcede0,0xcef0a,'five-widget 0x10 gate, C2 mode1 queue or local failure'))


def recover():
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Pinned native image changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    slices=[]
    for begin,end,purpose in SLICES:
        body=raw[begin:end]
        ins=list(md.disasm(body,BASE+begin))
        if not ins or ins[-1].address+ins[-1].size!=BASE+end:
            raise ValueError(f'Unaligned native slice {begin:X}')
        slices.append({'begin_rva':f'{begin:X}','end_rva_exclusive':f'{end:X}',
                       'purpose':purpose,'sha256':hashlib.sha256(body).hexdigest(),
                       'bytes_hex':body.hex(),
                       'instructions':[{'rva':f'{i.address-BASE:X}',
                                        'instruction':f'{i.mnemonic} {i.op_str}'} for i in ins]})
    return {'format':'god2-current-native-c2-mode1-five-widget-gate-v9',
            'native_image':IMAGE,'native_sha256':PIN,
            'method':'PINNED_BOUNDED_DISASSEMBLY_ONLY',
            'mode1_caller_rva':'B17A2','producer_entry_rva':'CEDE0',
            'widget_indices':['232E74','232DAE','232DB0','232DB2','232DB4'],
            'each_widget_gate':'signed index >= 0 and widget state bit0x10 set',
            'queue_call_rva':'CEEF6','body':'raw8; only first word explicitly set to mode1',
            'f5_field_dependency':'NONE_IN_THIS_BRANCH',
            'limits':['UI widget readiness is not server ownership or operation authority.',
                      'Unwritten request bytes remain opaque; no zero rule or response is inferred.'],
            'builds_tests_client_execution_deployment':False,'slices':slices}


def main():
    if OUT.exists():raise FileExistsError('Preserve prior native evidence')
    OUT.write_text(json.dumps(recover(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(OUT)


if __name__=='__main__':main()
