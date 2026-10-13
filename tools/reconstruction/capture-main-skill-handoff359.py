from pathlib import Path
import json,hashlib,subprocess
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');P=A/'round359-main-shared-skill-committed-handoff';M=Path('C:/Users/risei/Desktop/God2/God2');HEAD='224830cf68f458c1489c19e1d0eaeab60e9985df';sha=lambda b:hashlib.sha256(b).hexdigest()
assert not P.exists();P.mkdir()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
def blob(rel):
 p=Path(rel);assert not p.is_absolute() and '..' not in p.parts
 return subprocess.check_output(['git','show',HEAD+':'+rel],cwd=M)
contracts=['integration/SHARED_SKILL_SOURCE_V1.json','integration/SHARED_SKILL_COMPARISON_V1.json','integration/GROWTH_SOURCE_HANDOFF_V1.json']
raws={rel:blob(rel) for rel in contracts};v=json.loads(raws[contracts[0]]);comparison=json.loads(raws[contracts[1]])
assert v['schema']=='god2-shared-skill-source/1' and v['version']=='1.0.0'
assert len(raws[contracts[1]])==v['comparison']['bytes'] and sha(raws[contracts[1]])==v['comparison']['sha256']
assert v['sharedDefinitions']==comparison['sharedDefinitions']==449 and v['originalIdentical']==445 and v['regionalVariants']==3
refs=[]
for r in v['sourceScripts']:
 b=blob(r['path']);assert type(r['bytes']) is int and len(b)==r['bytes'] and sha(b)==r['sha256'];raws[r['path']]=b
for rel,b in raws.items():
 write(P/'committed'/rel,b);refs.append(dict(repository='God2-WebClient-Main',commit=HEAD,path=rel,retained='committed/'+rel,bytes=len(b),sha256=sha(b)))
catalog=v['catalog'];present=subprocess.check_output(['git','ls-tree',HEAD,'--',catalog['path']],cwd=M)
assert not present
js(P/'source-references.json',refs)
js(P/'handoff-review.json',dict(commit=HEAD,committed_blobs_only=True,source_scripts_read_as_text_only=True,generated_catalog_private_excluded_from_commit=True,private_catalog_not_copied=True,expected_catalog=catalog,native_BINS_unmodified=True,shared_445_plus_4_confirmed_reserved_borrow=449,regional_variants_remain=3,full_learning_or_casting_not_proved=True,server_runtime_or_DB_execution=False,owner_complete_valid_source_preferred=True,owner_all_skills_one_common_core_required=True,owner_custom_CN_skills=['CUSTOM-0058/0/126','CUSTOM-0059/0/150'],growth_OWNER_CONFIRMED_custom_diagnostic_not_native=True))
write(P/'capture-main-skill-handoff359.py',(A/'capture-main-skill-handoff359.py').read_bytes())
members=[]
for p in sorted(P.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(P).as_posix(),bytes=len(b),sha256=sha(b)))
js(P/'seal.json',dict(members=members,member_count=len(members),member_bytes=sum(r['bytes'] for r in members)))
sealraw=(P/'seal.json').read_bytes();seal=json.loads(sealraw);total=0;seen=set()
for r in seal['members']:
 p=P/r['path'];b=p.read_bytes();assert p.resolve().is_relative_to(P.resolve()) and r['path'] not in seen and type(r['bytes']) is int and len(b)==r['bytes'] and sha(b)==r['sha256'];total+=len(b);seen.add(r['path'])
assert len(seen)==seal['member_count'] and total==seal['member_bytes']
print(json.dumps(dict(root=P.as_posix(),seal_sha256=sha(sealraw),members=len(members),member_bytes=total,committed_blobs=len(refs),private_generated_catalog_not_copied=True)))

