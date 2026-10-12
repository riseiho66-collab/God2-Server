from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_CALL,CS_GRP_JUMP,CS_GRP_RET,CS_AC_WRITE
from capstone.x86 import X86_OP_MEM
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petroom-presend-context-source-342')
BASE=OUT.parent;PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
sha=lambda b:hashlib.sha256(b).hexdigest()
refs=[]
def ref(path,scope):
    b=path.read_bytes();refs.append(dict(path=str(path),bytes=len(b),sha256=sha(b),scope=scope,copied=False));return b
def put(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8',newline='\n')
image=ref(PIN/'native-image.bin','Pinned149c mapped source image hashed in place')
original=ref(PIN/'originalPE.bin','Pinned5fc originalPE source image hashed in place')
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
native=OUT/'native';native.mkdir(exist_ok=True);cuts=[]
def dis(raw,start):
    ins=list(md.disasm(raw,start));assert sum(i.size for i in ins)==len(raw);return ins
for name,start,end,complete in [('presend-forwarder-complete',0x49b820,0x49b843,True),('known-primary-zero-prefix',0x4d699e,0x4d69b1,False),('known-deferred-zero-prefix',0x4da730,0x4da744,False),('known-list-zero-prefix',0x4dc883,0x4dc896,False)]:
    raw=image[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000);assert raw==original[off:off+len(raw)]
    ins=dis(raw,start)
    calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.group(CS_GRP_CALL)]
    branches=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.group(CS_GRP_JUMP)]
    returns=[dict(va=f'{i.address:08X}',pop=i.op_str) for i in ins if i.group(CS_GRP_RET)]
    destinations=[dict(va=f'{i.address:08X}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in ins if any(o.type==X86_OP_MEM and o.access&CS_AC_WRITE for o in i.operands)]
    if complete:
        assert branches==[] and returns==[dict(va='0049B840',pop='0x18')] and calls==[dict(va='0049B83B',target='0x4b5be0')] and destinations==[]
    (native/(name+'.bin')).write_bytes(raw)
    (native/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+'\n'.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}' for i in ins)+'\n',encoding='utf8',newline='\n')
    cuts.append(dict(name=name,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,complete=complete,returns=returns,branches=branches,calls=calls,explicit_memory_write_destinations=destinations,scope='Direct caller/forwarder only; child and implicit stack effects not excluded'))
prior=[]
for folder,rel,start,complete in [('tw-native-petegg-selection-source-329','native/action-complete.bin',0x4d6940,True),('tw-native-petegg-selection-source-329','native/b1-producer-complete.bin',0x4d6ba0,True),('tw-native-petegg-selection-source-329','native/primary-action-dispatch-complete.bin',0x4820a0,True),('tw-native-petegg-selection-source-329','native/primary-action-main-prefix.bin',0x466b00,False),('tw-native-petegg-alternative-actions-source-330','native/alternative16-action-complete.bin',0x4da730,True),('tw-native-petegg-alternative-actions-source-330','native/alternative23-action-complete.bin',0x4dc880,True)]:
    path=BASE/folder/rel;raw=ref(path,'Immutable actual parent/producer; no recredit or recapture')
    sealpath=BASE/folder/'seal.json';sealbytes=ref(sealpath,'Immutable old seal referenced in place')
    member=next(m for m in json.loads(sealbytes)['members'] if m['path']==rel)
    assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
    off=pe.get_offset_from_rva(start-0x400000);assert raw==image[start-0x400000:start-0x400000+len(raw)]==original[off:off+len(raw)]
    ins=dis(raw,start)
    prior.append(dict(path=str(path),start_va=f'{start:08X}',end_exclusive_va=f'{start+len(raw):08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,individual_seal_member_equal=True,seal_sha256=sha(sealbytes),complete=complete,returns=[dict(va=f'{i.address:08X}',pop=i.op_str) for i in ins if i.group(CS_GRP_RET)],scope='Full actual caller except explicitly partial Main prefix'))
put('cuts.json',cuts);put('prior-individual-member-comparisons.json',prior);put('references.json',refs)
put('formal-argument-map.json',dict(complete_method_start='0049B820',complete_method_end_exclusive='0049B843',ret_va='0049B840',caller_formals=['A1','A2','A3','A4','A5','A6'],actual_child_call_va='0049B83B',child_target='004B5BE0',child_formals=['A1','A2','literal0x12','A5','A3','A6'],ignored_original_formals=['A4'],ecx_same_U_directly_preserved=True,common_actual_zero_calls=['004D69AC','004DA73F','004DC891'],common_child_values=[0,0,18,0,0,0],no_direct_receiver_field_read_or_write=True,no_direct_queue_call=True,implicit_stack_writes=True,opaque_child_effects_not_absent=True,selected_preview4D68D0_not_expanded=True,next_actual_source=dict(target='004B5BE0',context='ECX sameU; argument3 literal12h, others0 on common action prefixes',open='Complete authentic child body and its direct context writes/selected zero branch')))
print(json.dumps(dict(new_complete_forwarder_bytes=35,selected_prefix_bytes=sum(c['bytes'] for c in cuts if not c['complete']),prior_individuals=len(prior),native_execution=0,credits=0)))
