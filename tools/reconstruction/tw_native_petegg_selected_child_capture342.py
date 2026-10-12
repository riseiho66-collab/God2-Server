"""Bounded static source/hash/PE/Capstone capture, never native execution."""
from pathlib import Path
import hashlib
import json
import capstone
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
MAPPED=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry/native-image.bin'
ORIGINAL=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry/originalPE.bin'
PRIOR=BASE/'tw-native-petegg-selection-lifecycle-source-341'
REPO=Path('C:/Users/risei/Desktop/God2/God2-Server')
def sha(b):
    return hashlib.sha256(b).hexdigest()
def emit(name,value):
    path=ROOT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if isinstance(value,bytes) else value.encode('utf-8'))
def jemit(name,value):
    emit(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
b=MAPPED.read_bytes()
p=ORIGINAL.read_bytes()
assert sha(b)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(p)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=p)
md=Cs(CS_ARCH_X86,CS_MODE_32)
md.detail=True
sealraw=(PRIOR/'seal.json').read_bytes()
assert sha(sealraw)=='4b3c244fd0e9dd35c35092613f03bc99b7b877677a60d387fbf21448ab6487ba'
seal=json.loads(sealraw)
for member in seal['members']:
    raw=(PRIOR/member['path']).read_bytes()
    assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
parentpath=PRIOR/'native/known-inventory-action-complete.bin'
parent=parentpath.read_bytes()
off=pe.get_offset_from_rva(0x9A330)
assert parent==b[0x9A330:0x9B5D1]==p[off:off+len(parent)]
parentins=list(md.disasm(parent,0x49A330))
assert parentins[-1].address==0x49B5CE and parentins[-1].mnemonic=='ret'
call=next(i for i in parentins if i.address==0x49AC57)
assert call.mnemonic=='call' and call.operands[0].imm==0x4BC2E0
refs=[{'path':str(MAPPED),'bytes':len(b),'sha256':sha(b)},
      {'path':str(ORIGINAL),'bytes':len(p),'sha256':sha(p)},
      {'path':str(PRIOR/'seal.json'),'bytes':len(sealraw),'sha256':sha(sealraw),
       'individual_members_verified':len(seal['members'])},
      {'path':str(parentpath),'bytes':len(parent),'sha256':sha(parent),
       'start_va':'0049A330','end_exclusive_va':'0049B5D1','mapped_pe_equal':True}]
for name in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md',
             'docs/research/current-battle-entry-20260919.md',
             'docs/research/tw-native-petegg-selection-and-b1-source-20261012.md']:
    path=REPO/name
    raw=path.read_bytes()
    refs.append({'path':str(path),'bytes':len(raw),'sha256':sha(raw),'read_only_source_reference':True})
jemit('source-references.json',{'inputs':refs,'capstone':capstone.__version__,'pefile':pefile.__version__})
jemit('sections.json',[{'name_hex':s.Name.hex(),'rva':s.VirtualAddress,
    'virtual_size':s.Misc_VirtualSize,'raw_offset':s.PointerToRawData,
    'raw_size':s.SizeOfRawData,'characteristics':s.Characteristics,
    'execute_flag':bool(s.Characteristics&0x20000000)} for s in pe.sections])
cuts=[]
def cut(name,a,z,complete=False,decode=True):
    raw=b[a-0x400000:z-0x400000]
    po=pe.get_offset_from_rva(a-0x400000)
    assert raw==p[po:po+len(raw)]
    ins=list(md.disasm(raw,a)) if decode else []
    if decode:
        assert sum(i.size for i in ins)==len(raw)
        if complete:
            assert ins[-1].mnemonic=='ret'
            starts={i.address for i in ins}
            for i in ins:
                if i.mnemonic.startswith('j') and i.operands[0].type==capstone.CS_OP_IMM:
                    assert i.operands[0].imm in starts
        emit('native/'+name+'.tsv','va\traw_hex\tmnemonic\toperands\n'+''.join(
            f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins))
    emit('native/'+name+'.bin',raw)
    cuts.append({'name':name,'start_va':f'{a:08X}','end_exclusive_va':f'{z:08X}',
        'bytes':len(raw),'sha256':sha(raw),'original_pe_offset':po,'mapped_pe_equal':True,
        'complete_entry_all_returns':complete,'ret_sites':[f'{i.address:08X}' for i in ins if i.mnemonic=='ret'],
        'instruction_sites':len(ins),'boundary_probe_only':not decode,'method_credit':0})
    return ins
wrapper=cut('selected-global-reset-wrapper-complete',0x4BC2E0,0x4BC2F1,True)
child=cut('necessary-same-u-handle-child-complete',0x4BC2A0,0x4BC2D7,True)
invocation=cut('actual-parent-selected-invocation-excerpt',0x49AC31,0x49AC5C)
cut('wrapper-before-nop-boundary',0x4BC2D7,0x4BC2E0,False,False)
cut('wrapper-after-nop-boundary',0x4BC2F1,0x4BC300,False,False)
assert next(i for i in wrapper if i.mnemonic=='call').operands[0].imm==0x4BC2A0
assert next(i for i in child if i.mnemonic=='call').operands[0].imm==0x505230
jemit('native/cuts.json',cuts)
emit('native/direct-effects.tsv','va\teffect\tsource\n'
    '004BC2E0\tstack formal DWORD -1 pushed\tliteral FFFFFFFF\n'
    '004BC2E2\tglobal WORD5926B0=FFFF\tliteral FFFF\n'
    '004BC2EB\tCALL4BC2A0 same ECX U\tECX not modified in wrapper\n'
    '004BC2A0\tread signed WORD U232E56 into AX\tlive canonical U\n'
    '004BC2AC\tread global WORD5926B0 into DX\tlive global\n'
    '004BC2B3\tcompare DX with formal lowWORD\t[ESP+4]\n'
    '004BC2BF\tpush handle in AX lowWORD\tinitial U232E56 read\n'
    '004BC2C0\tECX=U+E2170\tcanonical context child projection\n'
    '004BC2C6\tCALL505230\tUI child context and handle; effects OPEN\n'
    '004BC2CB\tglobal WORD5926B0=FFFF after child\tliteral FFFF\n')
jemit('source-relation.json',{
    'actual_primary_context':'U=Main+A7F2F6C; previous341/329 qualification retained',
    'parent':'full49A330 ECX->ESI;49AC55 MOV ECX,ESI;49AC57 CALL4BC2E0',
    'wrapper':'no ECX change before4BC2EB directCALL4BC2A0;formalDWORD -1',
    'necessary_child_reason':'sole wrapper call directly carries genuine canonical U; closure of direct same-U effects',
    'child_direct_write':'WORD5926B0 only, after opaque505230 if selected branch',
    'ui_child':'505230 receives U+E2170 and lowWORD handle; no explicit U8/inventory pointer supplied',
    'conditional_wrapper_selected_branch':'with valid ordinary global storage and unchanged reads, globalFFFF equals formalFFFF; invoke505230 iff signedWORD U232E56>=0',
    'u8_or_inventory_direct_mutation':'none in the two complete retained bodies; children remain OPEN',
    'scope_stop':'no505230 descendant expansion absent actual U8/destination propagation',
    'u8_lifetime_or_selected_row_lease':'OPEN',
    'native_api_execution':False,'server_authority':False})
jemit('accounting.json',{'complete_body_count':2,'complete_body_code_bytes':72,
    'caller_excerpt_code_bytes':43,'boundary_probe_bytes':24,'data_cut_bytes':0,
    'complete_body_return_count':2,'new_method_credit':0,'new_opcode_credit':0,
    'connected_route_credit':0,'strict_execute_section_count':sum(bool(s.Characteristics&0x20000000) for s in pe.sections)})
print(json.dumps({'capture':'successful bounded static only','complete_body_bytes':72,
                  'caller_excerpt_bytes':43,'prior_members_verified':len(seal['members'])}))
