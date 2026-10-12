from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_CALL,CS_GRP_JUMP,CS_GRP_RET,CS_AC_WRITE
from capstone.x86 import X86_OP_MEM
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petroom-action-context-source-341')
BASE=OUT.parent;PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
sha=lambda b:hashlib.sha256(b).hexdigest()
refs=[]
def ref(path,scope):
    b=path.read_bytes();refs.append(dict(path=str(path),bytes=len(b),sha256=sha(b),scope=scope,copied=False));return b
def put(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8',newline='\n')
image=ref(PIN/'native-image.bin','Pinned149c mapped image hashed in place')
original=ref(PIN/'originalPE.bin','Pinned5fc original PE hashed in place')
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
native=OUT/'native';native.mkdir(exist_ok=True);cuts=[];writes=[]
def dis(raw,start):
    ins=list(md.disasm(raw,start));assert sum(i.size for i in ins)==len(raw);return ins
def census(ins,scope):
    return [dict(scope=scope,va=f'{i.address:08X}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str,limitation='Explicit memory destination only; opaque/implicit/aliased child writes not excluded') for i in ins if any(o.type==X86_OP_MEM and o.access&CS_AC_WRITE for o in i.operands)]
for name,start,end,complete in [('primary-pre-action-context-complete',0x4d7230,0x4d78c7,True),('close-status-child-complete',0x4d7940,0x4d7974,True),('adjacent-other-window-context-complete',0x4d9f20,0x4da0de,True),('known-primary-pre-action-caller',0x482274,0x482296,False)]:
    raw=image[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000);assert raw==original[off:off+len(raw)]
    ins=dis(raw,start);sites={i.address for i in ins}
    branches=[dict(va=f'{i.address:08X}',mnemonic=i.mnemonic,target=i.op_str) for i in ins if i.group(CS_GRP_JUMP)]
    if complete:assert all(int(b['target'],16) in sites for b in branches) and ins[-1].group(CS_GRP_RET)
    returns=[dict(va=f'{i.address:08X}',pop=i.op_str) for i in ins if i.group(CS_GRP_RET)]
    calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.group(CS_GRP_CALL)]
    (native/(name+'.bin')).write_bytes(raw)
    (native/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+'\n'.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}' for i in ins)+'\n',encoding='utf8',newline='\n')
    cuts.append(dict(name=name,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,complete=complete,returns=returns,branches=branches,calls=calls,scope='Actual bounded direct context; no queue/server authority, UI/FPU descendants opaque'))
    writes+=census(ins,name)
known=[]
specs=[('tw-native-petegg-selection-source-329','native/action-complete.bin',0x4d6940),('tw-native-petegg-selection-source-329','native/b1-producer-complete.bin',0x4d6ba0),('tw-native-petegg-selection-source-329','native/close-complete.bin',0x4d5910),('tw-native-petegg-selection-source-329','native/primary-action-dispatch-complete.bin',0x4820a0),('tw-native-petegg-alternative-actions-source-330','native/alternative23-open-complete.bin',0x4dc710),('tw-native-petegg-alternative-actions-source-330','native/alternative23-action-complete.bin',0x4dc880),('tw-native-petegg-alternative-actions-source-330','native/alternative23-close-known-complete.bin',0x4dc830),('tw-native-petegg-alternative-actions-source-330','native/alternative16-action-complete.bin',0x4da730),('tw-native-e5-egg-input-source-328','native/e6-complete-receiver.bin',0x4d6d20),('tw-native-e5-egg-input-source-328','native/known-egg-open-complete.bin',0x4d53f0),('tw-native-petegg-e7-list-input-source-331','native/e7-receiver-complete.bin',0x4d6340),('tw-native-petegg-operation-selection-source-336','native-final/controller-status-complete.bin',0x4d7980),('tw-native-petegg-operation-selection-source-336','native-final/controller-reset-complete.bin',0x4d7de0),('tw-native-e5-family1-source-327','native-family1/family1-complete.bin',0x4d6dd0),('tw-native-petegg-global-list-write-source-334','native-final/f4-receiver-complete.bin',0x4a3380)]
for folder,rel,start in specs:
    path=BASE/folder/rel
    if not path.exists():
        # Preserve the exact missing guessed filename as a scope correction,
        # then use that immutable package's actual cut metadata filename.
        put('missing-f4-filename-draft.json',dict(path=str(path),correction='See actual package native-final/cuts.json; no source absence inferred'))
        meta=json.loads((BASE/folder/'native-final/cuts.json').read_bytes())
        cut=next(c for c in meta if int(c.get('va',c.get('start_va','0')),16)==start)
        path=BASE/folder/'native-final'/(cut['name']+'.bin');rel=path.relative_to(BASE/folder).as_posix()
    raw=ref(path,'Immutable prior complete method reference, no recredit/capture rerun')
    off=pe.get_offset_from_rva(start-0x400000);assert raw==image[start-0x400000:start-0x400000+len(raw)]==original[off:off+len(raw)]
    sealpath=BASE/folder/'seal.json';sealbytes=ref(sealpath,'Immutable prior seal referenced in place')
    seal=json.loads(sealbytes);member=next(m for m in seal['members'] if m['path']==rel)
    assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
    ins=dis(raw,start)
    known.append(dict(path=str(path),start_va=f'{start:08X}',end_exclusive_va=f'{start+len(raw):08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,individual_seal_member_equal=True,seal_sha256=sha(sealbytes),returns=[dict(va=f'{i.address:08X}',pop=i.op_str) for i in ins if i.group(CS_GRP_RET)]))
    if start in [0x4d6940,0x4d6ba0,0x4dc880,0x4da730,0x4a3380]:writes+=census(ins,'known-'+f'{start:08X}')
imports=[dict(dll=d.dll.decode('ascii'),name=(s.name or b'').decode('ascii'),iat_va=f'{s.address:08X}') for d in pe.DIRECTORY_ENTRY_IMPORT for s in d.imports if s.address==0x5707bc]
put('selected-clock-import.json',dict(imports=imports,scope='Original PE symbol only; not invoked, no OS/timer server-rule interpretation'))
put('cuts.json',cuts);put('explicit-write-census.json',writes);put('prior-individual-member-comparisons.json',known);put('references.json',refs)
put('accounting.json',dict(complete_direct_ranges=3,selected_caller_spans=1,complete_rets=sum(len(c['returns']) for c in cuts if c['complete']),code_bytes=sum(c['bytes'] for c in cuts),prior_individual_method_comparisons=len(known),native_API_codec_SQL_test_execution=0,new_method_format_opcode_route_credit=0,current_native_request_identity_proved=False,server_authority_proved=False))
print(json.dumps(dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts),prior_individuals=len(known),native_execution=0)))
