from pathlib import Path
import json,hashlib
S=Path('C:/Users/risei/Desktop/God2/God2-Server')
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
D=A/'round343-c24-fullbank-alias-implementation'
ROOT=A/'tw-native-c24-fullbank-alias-source-delivery-343'
P='src/game/SharedTaiwanOwnedBagMoveSource.cpp'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,indent=2)+'\n').encode())
before=(S/P).read_bytes()
if D.exists() or before!=(ROOT/'before'/P).read_bytes():raise ValueError('Baseline/exclusive outputs differ')
anchor=b'    for(std::size_t slot=0;slot<50;++slot)if(!alias_row(next,slot))return std::nullopt;'
if before.count(anchor)!=2:raise ValueError('Expected before/next row checks differ')
insert=b'''    // A generic native alias BYTE admits0..255. Validate every exact TW
    // item20 alias, including cells outside the two requested bag locations;
    // the per-row checks below cannot see aliases outside the50-row bank.
    for(const auto& cell:next.inventory.cells)if(cell.instance)
        for(const auto& alias:cell.instance->aliases)
            if(alias.client_sha256==NativeEquipmentSnapshot::client_pin &&
               alias.profile==SharedTaiwanOwnedItemSelectionSource::alias_profile &&
               alias.native_slot>=50)return std::nullopt;
'''
after=before.replace(anchor,insert+anchor,1)
if after.replace(insert,b'',1)!=before:raise ValueError('Non-additive source delta')
D.mkdir();(S/P).write_bytes(after)
write(D/'SharedTaiwanOwnedBagMoveSource.before.cpp',before);write(D/'SharedTaiwanOwnedBagMoveSource.cpp',after)
write(D/'apply-c24-alias343.py',Path(__file__).read_bytes())
js(D/'source-manifest.json',dict(actual_path=(S/P).as_posix(),before_bytes=len(before),before_sha256=sha(before),after_bytes=len(after),after_sha256=sha(after),insert_bytes=len(insert),exact_before_preserved_except_single_insertion=True,
    new_Cplusplus_files=0,existing_Cplusplus_files_modified=1,both_C24_modes_guarded=True,native_source_storage_execution=False))
write(D/'REPORT.md',b'# Round343 actual C24 full-bank alias completeness fix\n\nThe generic alias BYTE/storage schema permits0..255. Before/next C24 row scans cover0..49 and silently skip out-of-bank exact TW item20 aliases. This additive preflight scans every owned instance/alias and rejects only the pinned TW client/profile pair with slot>=50 before the planner or joint write. Both same-tail and material modes share this plan. Inbound/outbound request slots remain below30; successful projection cannot introduce a new out-of-bank slot. No native mapping, grant, empty population, new provider or host activation is supplied. Other client/profile and in-bank aliases retain the existing path. Original C++ bytes survive exactly except one inserted block; no C++/SQL/runtime/build/test execution occurred.\n')
rows=[]
for p in sorted(D.rglob('*')):
    if p.is_file():
        b=p.read_bytes();rows.append(dict(path=p.relative_to(D).as_posix(),bytes=len(b),sha256=sha(b)))
js(D/'seal.json',dict(members=rows,member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows)))
print(json.dumps(dict(after_bytes=len(after),after_sha256=sha(after),insert_bytes=len(insert),seal_sha256=sha((D/'seal.json').read_bytes()),members=len(rows),member_bytes=sum(r['bytes'] for r in rows))))
