from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent;h=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 with (O/n).open('xb') as f:f.write(b)
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
refs=json.loads((O/'source-references.json').read_bytes())
for r in refs:
 b=Path(r['actual_path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256'] and b==(O/r['retained']).read_bytes()
report='''PASS bounded raw three-source skill BIN comparison358; no source implementation.

All three real plain uncompressed cbspec2.bin files are112660B/versionASCII1.03.
Each original is read/hash-checked and retained exactly. OriginalTW7676acd... is
an actual immutable research INPUT backup, counts121/129/87/111=448. Installed
TW3adcda70... is live installed owner-modified resource, counts126/129/87/111=453.
OriginalCN857b52... at fixed XJZ-CN/Data2/Fight/Spg actual client path has counts
125/130/87/111=453. That CN is the independently pinned582f-compatible source,
not a retired archive. Existing current resource remains unchanged. All rows
retain full110B, source hash/offset/identity and per-row SHA. Raw identity geometry
is8+kind*6E04+(ID-1)*6E; every row begins exactID/kind. Counts are declarations,
not active/learnable skills, gameplay completeness or entitlement. Each source
has45 blank name candidate entries. No padded/unpopulated rows were synthesized.

Three comparisons are separately retained. OriginalTW/CN shared keys448/union453:
zero identical full110B records,445 identical physical suffixes3E..6D and42..6D.
Only numerical physical suffix differences are0/95,1/83,1/129. InstalledTW/CN
shared452/union454:TW-only0/126, CN-only1/130. OriginalTW->installedTW all448 raw
records are fully identical and exactly five keys0/122..126 are added. Equal
counts453 do not imply equal identities, common records or shared formulas.

The five installed additions exactly match the existing owner source recipe
read as text, never executed:0/122..125 are named reserved placeholder records
with zero remainder;0/126 CUSTOM0058 is base0/8 with ID/name/short-text/reach44=7/
target45=16 changes. It is the existing custom instantaneous multi-target skill,
not one of448 originalTW definitions. The augmentation byte proof independently
reconstructs only static literal bytes and compares, not product APIs or scripts.
Historical release source says122..125reserved and126active; no DB/current
runtime row was inspected. No reservedTW key is relabeled a real CN ability.

Original numerical differences:0/95 TWphysicalWORD42=120/CN50 (other suffixsame);
1/83 both literal names blank, TW WORD42=0/B44=0/B45=0/WORD46=60/WORD48=0/
WORD4A=0 vsCN100/5/5/828/1/35, plus6B difference.1/129 TW WORD42=120/WORD4A55
vsCN100/35; their literal names/categories differ too. TW has仙道-高級團體技能/
鯨吞亂舞 whileCN says水生-特殊攻击-3/鲸吞魔舞. Same key does not attest same ability.
Explicit raw per-offset values/differences remain inspectable for all pairs.

CN original five extras0/122..125 and1/130 have no originalTW records. Literal
views say火神/火神/猎神/碧冰截速/雷神 respectively, with separate short strings.
TW installed0/122..125 still say預留技能 and are byte-different;1/130 absent.
TW-only0/126 is the owner custom, so remapping CN1/130 toTW0/126 would erase both
identity provenance and custom behavior. A versioned identity mapping must not
be inferred from same ordinal/name or one shared native count.

Chinese literal views preserve exact CP950TW/CP936CN source bytes with strict
character decoding (zero errors); they do not execute a compressed resource
codec. Candidate name slice2..1F and short text20..3D are kept separately with
NUL position/raw bytes. Current custom producer explicitly preservesWORD3E and
therefore rejects treating20..3F wholly as text. This bounded audit does NOT
newly qualify both original native consumers' field widths/meaning, or call a
short caption a full description. Native name/caption reader qualification is
separate. Source byte equality2..41 is reported physically, not as text semantics.

User preference: where originalTW corresponding text is actually qualified,
common presentation should retain its Taiwanese Traditional Chinese source.
Mechanics/physical parameters must remain separate from text provenance. Do not
prefer installed reserved placeholder over a real CN-only ability name, synthesize
a missingTW name, automatically translate unknown names or overwrite frozen
assets. This audit implements no text merge. Exact candidate literal lists are
provided for later source-qualified presentation review.

445 equal raw suffixes are useful common-parameter candidates ONLY. No execution
of native selected-definition arithmetic is made and no original damage/cast/
MPdebit/hit/critical/formula equality follows. Existing NativeSkillRecord source
qualifies TWWORD42 as client MP threshold, not original server charge. Existing
126120 consumer uses4C..64 as nonzero text-label selectors for supplied amount,
not damage coefficients; this historical source is read, not rerun or elevated
to CN. WORD46/range/flags/duration/unknown tail cannot acquire formula semantics
merely by values. Client formula-reader worker owns independent new arithmetic
qualification; online guides are secondary and absent from this raw audit.

No tracked source/client/resource edit, native/CRT/API/VM/emulator/productparser/
resourcecodec/SQL/DB/compiler/build/test/import/migration/activation/deployment.
Own standard-library staticstruct extraction/hash/strict literal text reads only.
All original raw records and evidence source refs retain exact path/bytes/hash;
source Current/runtime/native-loaded identity is not inferred. No battle, learn,
grant or acquired-owned skill is manufactured; formula completion/route credits0.

Original literal/custom helper created its evidence then failed only printing
CN simplified characters to a CP950 console. It is retained with failed exit;
readback-only successor verifies those files and outputs escaped console text,
never reruns the failed producer. Successful rawread/readback/sharing/seal helpers
are LF/noBOM, each successfulonce. All failure/history is retained before seal.
This bounded audit is delivered to root for source-scope review before any
implementation; no359 or arbitrary formula tree expansion begins here.
'''
put('REPORT.md',report.encode())
helpers=[]
for n in ['read_three_plain_skill_bins358.py','verify_raw_text_outputs358.py','describe_sharing_boundary358.py','seal_raw_skill_audit358.py']:
 b=(O/n).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');helpers.append(dict(path=n,bytes=len(b),sha256=h(b),successful_execution_count=1))
out('successful-LF-helper-metadata.json',helpers)
for r in refs:
 b=Path(r['actual_path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256'] and b==(O/r['retained']).read_bytes()
rows=[]
for p in sorted(O.rglob('*')):
 if not p.is_file():continue
 assert p.resolve().is_relative_to(O.resolve()) and p!=O/'seal.json'
 b=p.read_bytes();rows.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=h(b)))
seal=dict(verdict='PASS raw three-source comparison; formula/common identity semantics unqualified',member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows),members=rows,excludes='seal.json',source_files=3,declared_counts=[448,453,453],original_shared_rawsuffix_equal=445,full110_identical_original_pair=0,formula_credit=0,tracked_mutations=0)
out('seal.json',seal)
for r in rows:
 b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
print(json.dumps(dict(seal_sha256=h((O/'seal.json').read_bytes()),seal_bytes=(O/'seal.json').stat().st_size,members=len(rows),member_bytes=seal['member_bytes'],report_sha256=h((O/'REPORT.md').read_bytes()),report_bytes=(O/'REPORT.md').stat().st_size)))
