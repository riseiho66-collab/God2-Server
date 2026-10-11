"""Retain native creation-location projection and common identity source only."""
import csv
import hashlib
import io
import json
import struct
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT,CN,RECOVERY,PIN
from .cn_pe_import_directory import FileView

NAME='cn-owned-creation-location-01'
ROUND='20261007-cn-owned-creation-location'
FUNCTIONS=('0043d280','0043d580','00445040','00445b40','00448950','0047db70')
SOURCES=('src/cn/protocol/CnCreationLocationProjection.h',
    'src/cn/auth/SharedCreationLocationIdentity.h','src/cn/auth/SharedCreationLocationIdentity.cpp',
    'tools/reconstruction/cn_owned_creation_location_delivery.py',
    'docs/research/cn-owned-creation-location-20261007.md')

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';out=b/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve prior evidence')
    image=CN.parent/'XJZ-CN/God2_opt.exe';raw=image.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise RuntimeError('Pinned CN image changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    with (RECOVERY/'functions.tsv').open(encoding='utf-8-sig') as f:
        rows={r['address'].lower():r for r in csv.DictReader(f,delimiter='\t')}
    files=[];functions=[]
    def save(rel,data,original=None):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        files.append({'path':rel,'original':original,'bytes':len(data),
            'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):save(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    for entry in FUNCTIONS:
        row=rows[entry];va=int(entry,16);code=view.read(va-ib,int(row['bytes']))
        save('native/'+entry+'.bin',code,str(image)+':VA'+entry)
        save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes(),str(RECOVERY/row['file']))
        save('native/'+entry+'.asm',('\n'.join(
            f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in md.disasm(code,va))+'\n').encode())
        functions.append({'entry':entry,'metadata_bytes':len(code),
            'method':'METADATA_BOUNDED_LINEAR_DISASSEMBLY_NOT_GLOBAL_CFG_CLOSURE'})
    labels_raw=view.read(0x886578-ib,36);ids=struct.unpack('<18H',labels_raw)
    records=view.read(0x8865ac-ib,18*48)
    save('native/location-label-ids-00886578.bin',labels_raw,str(image)+':VA00886578')
    save('native/location-records-008865ac.bin',records,str(image)+':VA008865AC')
    words=[struct.unpack_from('<H',records,n*48+32)[0] for n in range(18)]
    resource=b/'cn-create-status-resource-01/resources'
    receipt_raw=(resource/'prior-account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_raw)
    packed_path=CN.parent/'XJZ-CN/Data2/Patch/Comm/message.csvZ';packed=packed_path.read_bytes()
    plain=(resource/'message.csv').read_bytes();sha=lambda data:hashlib.sha256(data).hexdigest()
    if receipt['client_sha256']!=PIN or receipt['asset']['codepage']!=936 or \
       sha(plain)!=receipt['asset']['decoded_sha256'] or sha(packed)!=receipt['asset']['sha256']:
        raise RuntimeError('Current resource scope differs from retained receipt')
    save('resources/message.csv',plain,str(resource/'message.csv'))
    save('resources/current-packed-resource-reference.json',(json.dumps({'path':str(packed_path),
        'sha256':sha(packed),'bytes':len(packed),'decoded_sha256':sha(plain)})+'\n').encode())
    rows_csv=list(csv.reader(io.StringIO(plain.decode('cp936'))))
    start=next(n for n,row in enumerate(rows_csv) if row and row[0]=='ProgramMsg')
    messages={int(row[0]):row[1:] for row in rows_csv[start+1:start+1+int(rows_csv[start][1])]}
    choices=[{'one_based_choice':n+1,'label_id':ids[n],'native_label_columns':messages[ids[n]],
        'word_va':f'{0x8865cc+n*48:08x}','packed_word':word,'endpoint_routing_key':word&15,
        'scene_selector':(word>>4)&3,'location_index':word>>6,
        'availability_or_spawn_proven':False} for n,word in enumerate(words)]
    prior_path=CN/'artifacts/native/20261006-cn-creation-locations-01/creation-location-evidence.json'
    prior_raw=prior_path.read_bytes();prior=json.loads(prior_raw)
    if prior['client_sha256']!=PIN or [row['packed_word'] for row in prior['choices']]!=words or \
       [row['program_msg_id'] for row in prior['choices']]!=list(ids):
        raise RuntimeError('Prior location table scope differs')
    save('retained-provenance/creation-location-evidence.json',prior_raw,str(prior_path))
    dump('native-creation-location-references.json',choices)
    dump('ordinary-location-reply-consumer.json',{
        'ordinary_after17':'0043D472 ->00481440 emits18,0043D494 ->0047DB70 waits18',
        'separate_location_call':'0043D580 sends18 and calls0047DB70 without sending17 locally; upstream pending-operation proof still required',
        'special1b':'00448950 sends18 then1A without ordinary18 waiter; not admitted by this identity source',
        'slot_copy':'0047DC8E reads first payloadBYTE;0047DC94 writes outputBYTE',
        'ui_cache_update':'0043D4AC..B4 masks low3 into LAST cached07 row;0043D4C1 stores full rawBYTE as selectionWORD',
        'second_reply_byte_used_by_qualified_waiter':False,
        'cached_ui_row_not_common_identity':True,'raw_slot_not_common_character_id':True,
        'wire_request_size':2,'wire_reply_size':3,
        'actual_reply_issuer_or_second_byte_recovered':False})
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),str(ROOT/rel))
    findings={'round':ROUND,'native_sha256':PIN,'functions':functions,
        'previous_goal_turn_classification':'progress: bound native status49 name-collision resource and complete23-byte read-only create status view',
        'creation_location_references':len(choices),'label_ids':list(ids),'packed_words':words,
        'prior_creation_location_artifact_sha256':sha(prior_raw),
        'common_creation_location_identity_resolvers_added':1,
        'source_creation_location_projection_added':1,
        'new_phase_opcode_source_bindings':0,'source_owner_chains_added':0,
        'actual_location_ingress_connected':False,'real_native18_issuer_added':False,
        'new_complete_bidirectional_routes':0,'levels_changed':False,
        'remaining':['Actual common creation transaction, native rules and exclusive pending-operation/authorized-choice source must supply this identity resolver; it is not a consumed token, permission or storage CAS.',
          'Native location tuple is not a shared map/spawn; endpoint/map/resource/coordinate joins and complete18 second reply byte plus issuer remain open.',
          'Ordinary17 and separate18 caller upstream conditions, special1B continuation, real02/03 replies and whole-game phase/state/variant denominator remain open.'],
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'database_access':False}
    dump('findings.json',findings);dump('native-source-manifest.json',{'native_sha256':PIN,'files':files})
    print(json.dumps({k:findings[k] for k in ('round','creation_location_references',
        'common_creation_location_identity_resolvers_added','source_creation_location_projection_added',
        'new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
