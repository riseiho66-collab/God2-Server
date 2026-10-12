from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round342-petroom-presend-storage-audit')
BASE=OUT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
verified=[]
for name in ['tw-native-petroom-presend-context-source-342','tw-native-petegg-selected-child-source-342']:
    package=BASE/name;sealraw=(package/'seal.json').read_bytes();seal=json.loads(sealraw)
    rows=[]
    for m in seal['members']:
        raw=(package/m['path']).read_bytes()
        assert len(raw)==m['bytes'] and sha(raw)==m['sha256']
        rows.append(dict(path=m['path'],bytes=len(raw),sha256=sha(raw)))
    total=sum(m['bytes'] for m in rows)
    assert len(rows)==seal['member_count'] and total==seal.get('total_bytes',seal.get('member_bytes'))
    verified.append(dict(package=str(package),seal_sha256=sha(sealraw),seal_bytes=len(sealraw),member_count=len(rows),member_bytes=total,members=rows,all_individual_members_equal=True,copied=False))
(OUT/'upstream-member-verification.json').write_text(json.dumps(verified,indent=2)+'\n',encoding='utf8',newline='\n')
PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
image=(PIN/'native-image.bin').read_bytes();original=(PIN/'originalPE.bin').read_bytes()
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32)
proof=[]
for folder,cutsrel in [('tw-native-petroom-presend-context-source-342','child-selected-cuts.json'),('tw-native-petegg-selected-child-source-342','native/cuts.json')]:
    package=BASE/folder;cuts=json.loads((package/cutsrel).read_bytes())
    print(folder,json.dumps(cuts,indent=2))
    for c in cuts:
        print('CUT_KEYS',list(c))
    proof.append(dict(package=str(package),cuts=cuts))
(OUT/'upstream-cut-metadata.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(individually_verified=sum(v['member_count'] for v in verified),original_inputs_hashed=True,native_execution=0)))
