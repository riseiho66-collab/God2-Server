from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_CALL,CS_GRP_JUMP,CS_GRP_RET,CS_AC_WRITE
from capstone.x86 import X86_OP_MEM
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petroom-presend-context-source-342')
PIN=OUT.parent/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(PIN/'native-image.bin').read_bytes();original=(PIN/'originalPE.bin').read_bytes()
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
cuts=[]
for name,start,end in [('large-child-selected-entry',0x4b5be0,0x4b5c35),('large-child-null-input-tail',0x4bbffb,0x4bc121)]:
    raw=image[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000)
    assert raw==original[off:off+len(raw)]
    ins=list(md.disasm(raw,start));assert sum(i.size for i in ins)==len(raw)
    calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.group(CS_GRP_CALL)]
    branches=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.group(CS_GRP_JUMP)]
    returns=[dict(va=f'{i.address:08X}',pop=i.op_str) for i in ins if i.group(CS_GRP_RET)]
    writes=[dict(va=f'{i.address:08X}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in ins if any(o.type==X86_OP_MEM and o.access&CS_AC_WRITE for o in i.operands)]
    if name.endswith('tail'):
        assert returns==[dict(va='004BC0D2',pop='0x18'),dict(va='004BC11E',pop='0x18')]
        assert all(start<=i.operands[0].imm<end for i in ins if i.group(CS_GRP_JUMP))
    (OUT/'native'/f'{name}.bin').write_bytes(raw)
    (OUT/'native'/f'{name}.tsv').write_text('va\tbytes\tmnemonic\toperands\n'+'\n'.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}' for i in ins)+'\n',encoding='utf8',newline='\n')
    cuts.append(dict(name=name,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,whole_method_complete=False,calls=calls,branches=branches,returns=returns,explicit_memory_write_destinations=writes))
(OUT/'child-selected-cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8',newline='\n')
projection=dict(scope='Selected authentic entry and null-input tail; not whole 4B5BE0',caller_child_formals=[0,0,18,0,0,0],receiver_alias='ECX same U -> EBP at4B5BED; ECX=EBP at4BC10D before CALL4BC2E0',frame_condition='Actual stack-allocation helper547B50 returns with the1184h frame established and preserved argument layout; helper itself opaque here',frame_argument_offsets=['1198','119C','11A0','11A4','11A8','11AC'],selected_path=['4B5BE0','4B5C11 WORD5926B0=12h','4B5C20 JE4BBFFB because A5=0','4BC005 JBE4BC0D5 because A4 lowWORD=0','4BC10F CALL4BC2E0 with sameU','4BC11E RET18'],ordered_direct_persistent_writes=[dict(va='004B5C11',address='005926B0',width=2,value=18),dict(va='004BC0DA',address='005B7838',width=4,value=0),dict(va='004BC0E0',address='005926B2',width=2,value=65535),dict(va='004BC0E6',address='005B783C',width=4,value=0),dict(va='004BC0EC',address='005926B4',width=2,value=65535),dict(va='004BC0F2',address='005B7840',width=4,value=0),dict(va='004BC0F8',address='005B7830',width=2,value=0),dict(va='004BC101',address='005B7844',width=4,value=0),dict(va='004BC107',address='005B7848',width=4,value=0)],direct_U_write=False,direct_queue_call=False,selected_full20_copy=False,absolute_fields_semantics='Unqualified shared native absolute storage; no pending-action/requestID/queue field interpretation',opaque_children=['004B5BE5 ->00547B50 stack allocation helper','004BC10F ->004BC2E0 sameU zero-input child'],unselected_tail_children=['005077C0','0050F580','004B4ED0'],next_actual_source='Complete4BC2E0 if scope later extended; nonzero-input4B5C35..4BBFFB omitted',native_execution=0,credits=0)
(OUT/'child-selected-projection.json').write_text(json.dumps(projection,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(new_bounded_code_bytes=sum(c['bytes'] for c in cuts),whole_large_method_recovered=False,native_execution=0,credits=0)))
