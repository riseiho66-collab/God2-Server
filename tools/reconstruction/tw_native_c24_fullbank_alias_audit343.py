"""Static git/file source capture and integer-domain proof, no SQL/C++ execution."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Users/risei/Desktop/God2/God2-Server')
BASELINE='43f4d294b8f017d2b00d697aa68a9c2e3726d8d5'
FILES=['src/game/SharedTaiwanOwnedBagMoveSource.cpp',
       'src/game/SharedTaiwanOwnedItemSelectionSource.h',
       'src/db/OwnedInventoryRepository.h',
       'src/db/SqliteOwnedInventoryRepository.cpp',
       'src/db/NativeEquipmentSnapshotRepository.h',
       'src/db/SqliteOwnedEquipmentTransaction.cpp',
       'src/game/TaiwanOwnedBagItemMaterial.h']
def sha(b):
    return hashlib.sha256(b).hexdigest()
def emit(name,value):
    path=ROOT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if isinstance(value,bytes) else value.encode('utf-8'))
def jemit(name,value):
    emit(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def git(*args):
    return subprocess.run(['git','--no-pager',*args],cwd=REPO,check=True,
                          capture_output=True).stdout
assert git('rev-parse',BASELINE).decode().strip()==BASELINE
sources={}
refs=[]
for name in FILES:
    raw=git('show',BASELINE+':'+name)
    sources[name]=raw.decode('utf-8')
    emit('old-source/'+name,raw)
    refs.append({'git_commit':BASELINE,'git_path':name,'bytes':len(raw),
                 'sha256':sha(raw),'source_kind':'exact git blob, no source execution'})
old=sources[FILES[0]]
assert old.count('for(std::size_t slot=0;slot<50;++slot)if(!alias_row(next,slot))return std::nullopt;')==2
assert 'alias.native_slot!=slot)continue;' in old
assert 'alias.profile!=SharedTaiwanOwnedItemSelectionSource::alias_profile' in old
assert 'alias.client_sha256!=NativeEquipmentSnapshot::client_pin' in old
assert 'std::uint8_t native_slot{};' in sources[FILES[2]]
assert "native_slot BETWEEN 0 AND 255" in sources[FILES[3]]
assert 'inventory_bytes=50*24,record_bytes=inventory_bytes+15;' in sources[FILES[4]]
pin='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
profile='tw149c-item20'
assert f'client_pin="{pin}"' in sources[FILES[1]] and f'client_pin="{pin}"' in sources[FILES[4]]
assert f'alias_profile="{profile}"' in sources[FILES[1]]
jemit('baseline-source-references.json',refs)

excerpts=[]
def excerpt(name,path,start_marker,end_marker):
    text=sources[path]
    first=text.index(start_marker)
    last=text.index(end_marker,first)+len(end_marker)
    body=text[first:last].replace('\r\n','\n')
    line=text[:first].count('\n')+1
    emit('old-excerpts/'+name,body+'\n')
    excerpts.append({'name':name,'git_path':path,'start_line':line,
                     'end_line_inclusive':line+body.count('\n'),'sha256':sha((body+'\n').encode())})
excerpt('c24-alias-row-and-plan.cpp.txt',FILES[0],'bool alias_row(', '\nclass Owner final {')
excerpt('repository-valid.cpp.txt',FILES[3],'bool valid(const OwnedInventorySnapshot& v)', '\n}\n}\nSqliteOwnedInventoryRepository::')
excerpt('schema-native-alias.cpp.txt',FILES[3],'CREATE TABLE main.owned_item_native_aliases (', ') WITHOUT ROWID;')
excerpt('native-alias-type.h.txt',FILES[2],'struct OwnedItemNativeAlias {', '\n};')
jemit('old-excerpts/locations.json',excerpts)

# Universal partitions and set cardinalities only; no constructed inventory,
# plan invocation, SQL/native execution, generated event sequences or tests.
jemit('finite-domain-proof.json',{
    'uint8_domain_inclusive':[0,255],'uint8_domain_cardinality':256,
    'native_bank_domain_inclusive':[0,49],'native_bank_domain_cardinality':50,
    'out_of_bank_domain_inclusive':[50,255],'out_of_bank_domain_cardinality':256-50,
    'inventory_row_bytes':24,'inventory_bank_bytes':50*24,'appearance_suffix_bytes':15,
    'complete_witness_bytes':50*24+15,
    'exact_client_pin':pin,'exact_profile':profile,
    'old_alias_row_predicate':'for each s in[0,49], relevant iff client==pin AND profile==item20 AND native_slot==s',
    'blindspot_theorem':'for a.slot in[50,255], forall s in[0,49]: a.slot!=s; alias_row executes continue before validity/found checks',
    'both_modes':'material_mode false and true share same plan and both all50 loops',
    'other_cell_relation':'source/destination eligible/project only touch selected cells; an existing alias in another owned cell is not examined by eligible/project',
    'required_new_reject_predicate':'exists owned cell.instance alias: exact_client AND exact_profile AND native_slot>=50',
    'unaffected_predicate_complement':'all exactpair aliases <=49, OR nonmatchingclient/profile regardless uint8 slot',
    'repository_schema_policy':'generic client/profile slot uint8 retains0..255; no global schema narrowing',
    'source_execution':False,'logical_fixture_generated':False})
current=(REPO/FILES[0]).read_bytes()
assert len(current)==14455 and sha(current)=='ea9a0cec45068d33ff21990145926f5381a492e72f5aba59d46624e7bd068a56'
insertion=(
    '    // A generic native alias BYTE admits0..255. Validate every exact TW\n'
    '    // item20 alias, including cells outside the two requested bag locations;\n'
    '    // the per-row checks below cannot see aliases outside the50-row bank.\n'
    '    for(const auto& cell:next.inventory.cells)if(cell.instance)\n'
    '        for(const auto& alias:cell.instance->aliases)\n'
    '            if(alias.client_sha256==NativeEquipmentSnapshot::client_pin &&\n'
    '               alias.profile==SharedTaiwanOwnedItemSelectionSource::alias_profile &&\n'
    '               alias.native_slot>=50)return std::nullopt;\n').encode('utf-8')
assert len(insertion)==562
oldraw=sources[FILES[0]].encode('utf-8')
assert len(oldraw)==13893 and sha(oldraw)=='66468113a8e5219e3cfcd6d239982907dedd89ca1e49cfe9a9953531f26a4891'
marker=b'    for(std::size_t slot=0;slot<50;++slot)if(!alias_row(next,slot))return std::nullopt;'
at=oldraw.index(marker)
assert current==oldraw[:at]+insertion+oldraw[at:]
emit('verified-exact-insertion.cpp.txt',insertion)
emit('current-source/'+FILES[0],current)
jemit('current-source-reference.json',{'path':str(REPO/FILES[0]),'bytes':len(current),
    'sha256':sha(current),'baseline_commit':BASELINE,'source_read_only':True})
emit('old-to-current.diff',git('diff','--no-ext-diff',BASELINE,'--',FILES[0]))
implementation=ROOT.parent/'round343-c24-fullbank-alias-implementation'
implementation_seal_raw=(implementation/'seal.json').read_bytes()
assert sha(implementation_seal_raw)=='52b337bb2c7f4c225d69c68ea81cba14d130dca8adb0b0790f51ae3ddc85bf11'
implementation_seal=json.loads(implementation_seal_raw)
for member in implementation_seal['members']:
    raw=(implementation/member['path']).read_bytes()
    assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
jemit('implementation-seal-reference.json',{
    'path':str(implementation/'seal.json'),'bytes':len(implementation_seal_raw),
    'sha256':sha(implementation_seal_raw),'individual_members_verified':len(implementation_seal['members']),
    'exact_single_insertion_verified':True,'insertion_bytes':len(insertion),
    'new_guard_precedes_first_all50_check':True,'source_mode_control_flow_unchanged':True,
    'projected_slot_assignments':'both requested slots are<30;only projected selected instance aliases change slot',
    'all_route_method_opcode_credits':0,'source_execution':False})
print(json.dumps({'capture':'successful source only','baseline':BASELINE,
                  'old_source_files':len(FILES),'current_sha256':sha(current)}))
