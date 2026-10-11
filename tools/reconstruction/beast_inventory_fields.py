"""Recover original PET metadata display branches by bounded static decoding.

No tests, build, client/emulator execution, instance grant or database mutation.
"""
import collections
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE
from .beast_panel_contract import section_rows
from .beast_source_catalog import SOURCE, DECODED


def recover():
    message_path='artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/message.csvZ'
    source_path='artifacts/capture_work/host-20260918-1430/client/Data2/Patch/Comm/gamedata.csvZ'
    reader=ArchivedInputs()
    try:
        raw=reader.read(IMAGE)
        message=reader.read(message_path)
        gamedata=reader.read(source_path)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Original mapped image identity changed')
    source=section_rows('Data2/Patch/Comm/gamedata.csvZ',b'PET',None,
                        compressed=gamedata,path_label=source_path)
    if source['compressed_sha256']!=SOURCE or source['decoded_sha256']!=DECODED:
        raise ValueError('Original PET resource identity changed')
    flags=[]
    for row in source['rows']:
        columns=bytes.fromhex(row['raw_hex']).split(b',')
        flags.append({'id':row['id'],'line':row['line'],'decoded_offset':row['decoded_offset'],
                      'row_sha256':row['row_sha256'],'column27_raw_hex':columns[27].hex(),
                      'column27_decimal':int(columns[27]),'definition11c_byte':int(columns[27])&255})
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    functions=[]
    for start,end,purpose in [
        (0x51b50,0x51bdc,'column getter: zero-based380-byte row token slots; decimal scan'),
        (0x596f2,0x59721,'definition class5 dispatch stores source column27 AL at11C'),
        (0xb6430,0xb6451,'third tooltip class dispatch, class5 ->B90E7'),
        (0xb90e7,0xb95ea,'class5 metadata tooltip: palette/fatigue, packed date OR classic level/EXP/use'),
        (0xa0970,0xa0a8d,'4D panel then inventory writes; metadata0 atUI85610'),
        (0xa06a0,0xa0700,'selected beast tooltip caller uses full inventory metadata'),
        (0x9ff1c,0x9ff59,'exact three embedded label records; loop stride22, not four records'),
        (0x9b7f0,0x9b890,'inventory tooltip wrapper ->4B5BE0')]:
        code=raw[start:end]
        functions.append({'rva':f'{start:X}','end_rva_exclusive':f'{end:X}',
                          'purpose':purpose,'sha256':hashlib.sha256(code).hexdigest(),
                          'bytes_hex':code.hex(),
                          'instructions':[{'rva':f'{i.address-BASE:X}','instruction':f'{i.mnemonic} {i.op_str}'}
                                          for i in md.disasm(code,BASE+start)]})
    tables=[]
    for name,map_rva,table_rva in [('parser class5',0x59984,0x59960),
                                    ('tooltip third class5',0xbc1d0,0xbc188)]:
        index=raw[map_rva+4]
        target=struct.unpack_from('<I',raw,table_rva+4*index)[0]-BASE
        tables.append({'name':name,'class':5,'map_index':4,'map_rva':f'{map_rva:X}',
                       'table_index':index,'jump_table_rva':f'{table_rva:X}',
                       'target_rva':f'{target:X}',
                       'map_bytes_hex':raw[map_rva:map_rva+6].hex(),
                       'selected_pointer_bytes_hex':raw[table_rva+4*index:table_rva+4*index+4].hex()})
    formats=[]
    for rva in [0x1823b4,0x19292c,0x19290c,0x192974,0x192718,0x192948]:
        end=raw.index(b'\0',rva,rva+180)
        value=raw[rva:end]
        formats.append({'rva':f'{rva:X}','bytes_hex':value.hex(),
                        'ascii':value.decode('ascii'),'scope':'exact native bytes; no normalized format'})
    labels=section_rows('Data2/Patch/Comm/message.csvZ',b'ProgramMsg',
                        {58,84,86,362,417,528,677,678,679,680,695,735},
                        compressed=message,path_label=message_path)
    if labels['compressed_sha256']!='5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598' or labels['decoded_sha256']!='370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8':
        raise ValueError('Original ProgramMsg resource identity changed')
    embedded=[]
    for rva in range(0x1711c0,0x171202,22):
        record=raw[rva:rva+22]
        text=record[2:18].split(b'\0',1)[0]
        embedded.append({'rva':f'{rva:X}','record_hex':record.hex(),
                         'control_word':struct.unpack_from('<H',record)[0],
                         'text_hex':text.hex(),'cp950_text':text.decode('cp950'),
                         'position_words':struct.unpack_from('<hh',record,18)})
    tags=[]
    for selector in (5,9):
        pointer=struct.unpack_from('<I',raw,0x1897ec+selector*4)[0]-BASE
        tag=raw[pointer:raw.index(b'\0',pointer,pointer+12)]
        tags.append({'selector':selector,'tag':tag.decode('ascii'),
                     'pointer_rva':f'{0x1897ec+selector*4:X}','target_rva':f'{pointer:X}'})
    return {
        'format':'god2-static-beast-inventory-fields-v1',
        'method':'bounded mapped-image disassembly and pinned original resource decoding only',
        'tests_builds_emulator_client_execution':False,
        'mapped_image':{'path':IMAGE,'sha256':PIN},'functions':functions,
        'dispatch_tables':tables,'native_formats':formats,'original_labels':labels,
        'embedded_label_table':{'records':embedded,'loop_rva':'9FF1C..9FF59',
                                'scope':'three control0/1/2 labels only; no loyalty/fatigue gauge-field qualification'},
        'source_tag_bindings':tags,
        'source_flag':{'path':source_path,'compressed_sha256':SOURCE,'decoded_sha256':DECODED,
                       'column':27,'indexing':'zero-based;51B60 derives ecx+78+index*380',
                       'parser':'5970D push27 ->51B50 ->51BA0 ->decimal scan;59716 storesAL definition11C',
                       'distribution':dict(collections.Counter(r['definition11c_byte'] for r in flags)),
                       'all147_rows':flags,
                       'scope':'raw flag/date-branch selector; numerical hours or expiry policy not established'},
        'metadata_fields':{
            '4':'WORD low14 fatigue limit Program528; high2 mode. Does not identify current panel numerator.',
            '8':'BYTE==1 plusmode8000 displays Program417 exploring; date branch uses WORD8 with lowBYTE cleared',
            '9':'BYTE classic level Program84; same location as4D body3 fullBYTE copy',
            '10':'WORD low3 palette Program86;4D body2 guard1..6. Not panel selection.',
            '12':'WORD classic EXP percent Program58, FLOAT0.01; date branch contributes packed date',
            '14':'WORD classic4000/8000 elapsed minutes ->hours/remainder60; otherclassic use count; date branch contributes packed date',
            '16':'WORD bit15 flag/low15 transfer use count Program735 ONLY classic4000/8000 path'},
        'float_display':{'rva':'171204','bytes_hex':raw[0x171204:0x171208].hex(),
                         'value':struct.unpack_from('<f',raw,0x171204)[0],
                         'scope':'display scaling only; no inverse reward formula'},
        'delta_offset_correction':{'metadata_base':'UI85610, record base8560C+4 already applied',
                                   'native_writes':['WORD UI8561A ->metadata10 low3',
                                                    'WORD UI85618 highBYTE ->metadata9',
                                                    'WORD UI8561C ->metadata12'],
                                   'prior_wrong_offsets':[6,5,8],
                                   'prior_evidence':'beast-inventory-controls-static-v1-prior-analysis.json'},
        'source_integration':['RecoveredBeastPanel corrected exact inventory projection',
                              'NativeBeastSourceCatalog original column27 lowBYTE per row',
                              'RecoveredBeastInventoryFields source-qualified branch view',
                              'StoredBeastSnapshot::inventory_fields used by actual custody validation'],
        'remaining':['6B food eligibility, quantity/effect/caps/threshold and atomic consumption/reply',
                     'panel percentage BYTE and meter gameplay meaning',
                     'date decode/calendar/timing/expiry gameplay authority',
                     'riding/activity/stat/appearance and acquisition routes']}


def main():
    output=SERVER/'artifacts/integration/packet-connections-20261006/beast-inventory-fields-static.json'
    output.write_text(json.dumps(recover(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(output),'method':'STATIC_ONLY','tests_builds_client_execution':False}))


if __name__=='__main__':
    main()
