from pathlib import Path
import json,hashlib,subprocess,re
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round359-common-skill-definition-implementation'
H=lambda b:hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
pins=load(D/'final-candidate-current-pins.json');assert len(pins)==12
current={}; refs=[]
for pin in pins:
 p=pin['path'];b=(S/p).read_bytes();assert len(b)==pin['bytes'] and H(b)==pin['sha256'],p
 current[p]=b;q=D/'source'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 refs.append({'actual_path':str(S/p).replace('\\','/'),'retained':q.relative_to(D).as_posix(),'bytes':len(b),'sha256':H(b)})
# Reverse the actual immutable receipts, never a guessed newline convention.
restored=dict(current)
def undo(p,x,y):
 assert restored[p].count(y)==1,(p,'inverse target multiplicity')
 restored[p]=restored[p].replace(y,x)
for name in ['custom0138-comment-correction.json','positional-region-correction.json','utility-include-correction.json']:
 e=load(D/name);undo(e['path'],bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex']))
e=load(D/'full110-pin-correction.json')
for v in reversed(e['cpp_edits']):undo(e['cpp_path'],bytes.fromhex(v['old_hex']),bytes.fromhex(v['new_hex']))
undo(e['header_path'],bytes.fromhex(e['header_old_hex']),bytes.fromhex(e['header_new_hex']))
e=load(D/'reserve-text-correction.json');undo(e['path'],bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex']))
for e in reversed(load(D/'qualification-correction.json')['edits']):
 undo(e['path'],bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex']))
initial=load(D/'exact-edits-and-inverse.json')
for e in reversed(initial['edits']):
 x,y=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex'])
 assert restored[e['path']].count(y)==e['count']
 restored[e['path']]=restored[e['path']].replace(y,x)
existing=[v['path'] for v in initial['files'] if not v['new_file']]
new=[v['path'] for v in initial['files'] if v['new_file']]
assert len(existing)==9 and len(new)==3
baseline=[]
for p in existing:
 b=(D/'before'/p).read_bytes()
 head=subprocess.run(['git','show','8520e6330e32631df630fecc46204f040a6f911a:'+p],cwd=S,check=True,capture_output=True).stdout
 assert restored[p]==b==head,p
 baseline.append({'path':p,'bytes':len(b),'sha256':H(b),'whole_inverse':True})
for p in new:
 r=subprocess.run(['git','cat-file','-e','8520e6330e32631df630fecc46204f040a6f911a:'+p],cwd=S,capture_output=True)
 assert r.returncode!=0
 assert (D/'source'/p).resolve().is_relative_to((D/'source').resolve())
oldh=(D/'before/src/db/NativeSkillCatalog.h').read_bytes().decode()
newh=current['src/db/NativeSkillCatalog.h'].decode()
def structure(t,name):
 start=t.index('struct '+name+' {');end=t.index('\n};',start)+3
 return t[start:end].replace('\r\n','\n')
assert structure(oldh,'NativeSkillRecord')==structure(newh,'NativeSkillRecord')
assert structure(oldh,'NativeSkillSource')==structure(current['src/db/NativeSkillSource.h'].decode(),'NativeSkillSource')
# Old actual lookup bodies are preserved as bytes; the whole inverses above
# also prove every untouched source span and old Main lambda/constructor args.
for p in ['src/db/NativeSkillCatalog.cpp','src/cn/assets/CnSharedSkillCatalog.cpp']:
 old=(D/'before'/p).read_bytes()
 marker=b'std::optional<NativeSkillRecord> NativeSkillCatalog::lookup(' if 'db/' in p else b'std::optional<CnSharedSkillCatalog::Record> CnSharedSkillCatalog::lookup('
 start=old.index(marker);end=old.index(b'\n}',start)+2
 assert old[start:end] in current[p]
# Actual original901 + owner6 full records, not caller-provided digest flags.
rawroot=A/'round358-skills-raw-three-source-audit'
rawsources={}
for ref in load(rawroot/'source-references.json'):
 b=(rawroot/ref['retained']).read_bytes();assert H(b)==ref['sha256'] and len(b)==ref['bytes']
 rawsources[ref['sha256']]=b
raw150=(A/'round359-native-skill-text-common-source-plan/retained-custom150-record.bin').read_bytes()
text=current['src/db/SharedSkillDefinition.cpp'].decode()
start=text.index('const Pin pins[]={\n')+len('const Pin pins[]={\n');end=text.index('\n};',start)
lines=text[start:end].splitlines();assert len(lines)==907
proof=[];concat=b'';counts={}
for line in lines:
 left,right=line.strip().rsplit(',{{',1);assert right.endswith('}}},')
 expected=bytes(int(v,16) for v in right[:-4].split(','))
 assert len(expected)==110
 row=json.loads('['+left[1:].replace('SharedSkillRegion::Taiwan','"Taiwan"').replace('SharedSkillRegion::China','"China"')+']')
 assert len(row)==12
 region,kind,id,ordinal,offset,sha,source_sha,row_count,*names=row
 raw=raw150 if source_sha=='f159b61f0aeacc46e71519cd6e98910381eda22336ad07487b2cf7213ec6297d' else rawsources[source_sha][offset:offset+110]
 assert expected==raw and expected[:2]==bytes([id,kind]) and H(raw)==sha
 counts[source_sha]=counts.get(source_sha,0)+1;concat+=raw
 proof.append({'region':region,'kind':kind,'id':id,'ordinal':ordinal,'offset':offset,'source_sha256':source_sha,'bytes':110,'sha256':sha,'full_expected_equal':True})
assert counts=={'7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51':448,
 '857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004':453,
 '3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7':5,
 'f159b61f0aeacc46e71519cd6e98910381eda22336ad07487b2cf7213ec6297d':1}
assert 'b.raw!=p.expected' in text and 'if(!b.row_digest_verified' not in text
assert 'b.qualification=SharedSkillRowQualification::MetadataSnapshotOnly;' in text
assert 'Shared skill positional region mismatch' in text and 'CUSTOM-0138' in text
assert 'd.status==SharedSkillStatus::BorrowedCNReserve && c && matched[*c]' in text
# In-place upstream members verified individually, excluding only root seal.
up=[]
for label,root in [('raw358',rawroot),('plan359',A/'round359-native-skill-text-common-source-plan')]:
 sealpath=root/'seal.json';seal=load(sealpath);members=seal.get('members',seal.get('files'))
 seen=set();total=0;entries=[]
 for m in members:
  path=m.get('path',m.get('name'));assert isinstance(path,str) and path and path not in seen;seen.add(path)
  n=m['bytes'];assert type(n)==int and n>=0
  p=(root/path).resolve();assert p.is_relative_to(root.resolve())
  b=p.read_bytes();assert len(b)==n and H(b)==m['sha256']
  total+=n;entries.append({'path':path,'bytes':n,'sha256':H(b)})
 assert type(total)==int
 up.append({'label':label,'root':str(root).replace('\\','/'),'seal_bytes':sealpath.stat().st_size,'seal_sha256':H(sealpath.read_bytes()),'member_count':len(entries),'member_bytes':total,'members':entries})
deps=['src/db/SqliteSupport.h','src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillBookBindings.h',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp',
 'src/text/ChineseText.h','src/text/ChineseText.cpp','CMakeLists.txt',
 'resources/opencc/STPhrases.txt','resources/opencc/STCharacters.txt']
deprefs=[]
for p in deps:
 b=(S/p).read_bytes();q=D/'dependencies'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 deprefs.append({'actual_path':str(S/p).replace('\\','/'),'retained':q.relative_to(D).as_posix(),'bytes':len(b),'sha256':H(b)})
write(D/'source-references.json',refs);write(D/'dependency-references.json',deprefs)
write(D/'final-source-manifest.json',{'files':refs,'existing':9,'new':3,'current_bytes':sum(v['bytes'] for v in refs),'source_freeze':True})
write(D/'final-whole-inverse-proof.json',{'baseline':initial['baseline'],'existing':baseline,'new_absent_in_baseline':new,'existing_count':9,'new_count':3,'original_NativeSkillRecord_exact':True,'NativeSkillSource_exact_struct_move':True,'all_9_whole_inverse':True,'new_3_contained':True})
write(D/'full907-static-pin-readback.json',{'count':907,'expected_bytes':len(concat),'expected_concat_sha256':H(concat),'counts':counts,'members':proof,'static_only':True,'Cplusplus_or_API_execution':False})
write(D/'upstream-individual-readback.json',up)
helpers=['apply_common_skill_definition359_v3.py','correct_shared_qualification359.py','correct_borrowed_reserve_text359.py','add_full110_source_pins359.py','add_shared_catalog_utility359_v2.py','check_shared_region_and_custody359.py','annotate_common_skill_custom0138_359.py','capture_common_skill_definition359.py']
helpermeta=[]
for name in helpers:
 b=(D/name).read_bytes();assert not b.startswith(b'\xef\xbb\xbf') and b'\r\n' not in b
 helpermeta.append({'path':name,'bytes':len(b),'sha256':H(b),'successful_execution_count':1,'LF_no_BOM':True})
write(D/'successful-LF-helper-metadata.json',helpermeta)
report='''Common skill definition provider359: static source PASS.

The same NativeSkillCatalog read view now composes one owning SharedSkillDefinition for both the new actual Main Lua common_skill_definition getter and the existing CN preborn selection Facts delivered to apply/qualify_delivery. Original NativeSkillRecord fields/equality, default native lookups, exact original CN source qualification, and old Main native getter remain unchanged. The new result separately retains an optional requested-native snapshot; a CN-selected common profile never masquerades as a TW original row.

CUSTOM-0138 is owner-selected source composition. Original TW448/CN453 are independently pinned per row; five installed TW reserve/custom rows and CUSTOM0059 candidate150 have separate owner provenance. Every907 pin retains all110 expected bytes and checks them exactly with source SHA/row count/ordinal/offset and declared row digest. Original rows additionally require the original image annotation. Runtime digest verification is informational; a public boolean/qualification enum cannot promote differing bytes. Positional Taiwan/China region arguments are checked. These are selected-row data attestations, never observed whole-file/current native-bank or permission receipts.

The complete common parameter base defaults to qualified TW. Explicit TW1/83 chooses complete CN; owner-approved CN0/122..125 reuse chooses CN and its real name/short instead of the TW reserve placeholder. Conflicts0/95 and1/129 choose complete TW under the owner directive while retaining full original CN parameters and explicit conflict status. Physical matching identity/tail bytes are not damage-formula proof. Single available qualified profiles are represented; unknown snapshots stay MetadataSnapshotOnly and original raw results survive unavailable runtime digest/CN counterpart. No general blank-text/zero-parameter inactivity heuristic is used.

Text is bounded source policy: name[2,20h), short[20h,3Eh), CP950/CP936. Nonempty actual TW text is primary except the explicit reserve-placeholder override. Pinned CN fallback is converted for Traditional display by static literal mappings from the retained OpenCC dictionaries. Source/raw text/provenance and converted text remain distinct. This does not qualify those ranges as native UI widths: the known MP-display name actually comes from an SKB/item lookup result+8. WORD3E and all110 bytes are retained.

Actual CN selection resolves existing qualified native records, obtains the same common resolver metadata, and requires requested-original equality before storing owning definitions at the end of Facts. It keeps existing operation/thread/lifetime/reentry/current fences, original raw definition vectors, book/source predicates, and authorization unchanged. Owned Facts persist through commit without invoking obsolete captured Current. The Lua optional provider is at the end of constructor arguments and is forwarded to both initial and reloaded VMs. The old getter and original native source remain separate.

Nine whole-file inverses restore exact published8520e633 bytes. Three new paths were absent in that Git baseline and are contained. Original NativeSkillRecord is exact; NativeSkillSource is an exact struct move. All12 frozen source copies and907 expected arrays were independently read back. Prior raw audit35 members and source plan55 members were individually hash/length/containment verified in place; no full native-image copies were made. Failed prewrite helpers and every additive corrective candidate/inverse are retained, including the actual mixed-newline insertion proof.

No build, test, C++/native/API/codec/parser/VM/CRT execution, SQL/database operation/import/migration, client-resource write, activation or deployment occurred. This adds real shared-definition source handoffs; it does not add casting rights, grant all skills, implement unknown formulas/MP debit/effects, widen the native CN453 catalog, or complete a gameplay route. BattlePolicy integration and complete formulas remain future separately qualified work.
'''
(D/'REPORT.md').write_text(report,encoding='utf-8',newline='\n')
write(D/'PASS.json',{'status':'PASS','static_only':True,'source_count':12,'source_bytes':sum(v['bytes'] for v in refs),'original_pins':901,'owner_pins':6,'full_expected_bytes':99770,'whole_existing_inverse':9,'new_contained':3,'upstream_count':2,'upstream_members':sum(v['member_count'] for v in up),'upstream_bytes':sum(v['member_bytes'] for v in up),'no_target_execution':True})
for v in refs:
 b=Path(v['actual_path']).read_bytes();assert len(b)==v['bytes'] and H(b)==v['sha256']
print(json.dumps({'status':'PASS','source_count':12,'source_bytes':sum(v['bytes'] for v in refs),'pins':907,'whole_inverse':9,'upstream_members':sum(v['member_count'] for v in up),'upstream_bytes':sum(v['member_bytes'] for v in up),'REPORT_bytes':(D/'REPORT.md').stat().st_size,'REPORT_sha256':H((D/'REPORT.md').read_bytes())}))

