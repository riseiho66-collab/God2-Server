from pathlib import Path
import hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round342-petroom-presend-argument-audit')
BASE=OUT.parent;sha=lambda b:hashlib.sha256(b).hexdigest()
prior=BASE/'round342-petroom-presend-storage-audit';sealraw=(prior/'seal.json').read_bytes();seal=json.loads(sealraw)
for m in seal['members']:
    b=(prior/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
assert seal['member_count']==len(seal['members']) and seal['member_bytes']==sum(m['bytes'] for m in seal['members'])
md=Cs(CS_ARCH_X86,CS_MODE_32);rows=[];refs=[]
for folder,name,start in [('tw-native-petroom-presend-context-source-342','large-child-null-input-tail',0x4bbffb),('tw-native-petegg-selected-child-source-342','selected-global-reset-wrapper-complete',0x4bc2e0),('tw-native-petegg-selected-child-source-342','necessary-same-u-handle-child-complete',0x4bc2a0)]:
    package=BASE/folder;path=package/'native'/(name+'.bin');raw=path.read_bytes()
    upstream=json.loads((package/'seal.json').read_bytes());member=next(m for m in upstream['members'] if m['path']=='native/'+name+'.bin')
    assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
    ins=list(md.disasm(raw,start));assert sum(i.size for i in ins)==len(raw)
    for i in ins:
        if start==0x4bbffb and i.address<0x4bc0d5:
            continue
        rows.append(dict(va=f'{i.address:08X}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str))
    refs.append(dict(path=str(path),bytes=len(raw),sha256=sha(raw),upstream_individual_seal_equal=True,copied=False))
assert next(r for r in rows if r['va']=='004BC0D7')['bytes']=='83c8ff'
assert next(r for r in rows if r['va']=='004BC2A0')['bytes']=='668b81562e2300'
assert next(r for r in rows if r['va']=='004BC2BF')['bytes']=='50'
(OUT/'argument-source-evidence.json').write_text(json.dumps(dict(prior_audit_seal_sha256=sha(sealraw),prior_audit_all_individual_members_verified=len(seal['members']),source_references=refs,selected_instructions=rows,manual_conclusion='Selected EAX upper16FFFF; low16 live handle; PUSH wholeDWORD FFFF0000|handle. Generic child upper16 incoming/unknown. Optional postchild WORD store requires normal child return.',target_execution=0),indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(prior_audit_members_verified=len(seal['members']),selected_source_bins_verified=len(refs),manual_argument_recipe='FFFF0000 | live_handle_lowWORD',target_execution=0)))
