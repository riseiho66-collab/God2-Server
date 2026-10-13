from pathlib import Path
import hashlib
import json
import re
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
A = O.parent
T = A / 'round359-common-skill-definition-implementation'
P = A / 'round359-native-skill-text-common-source-plan'
R = A / 'round358-skills-raw-three-source-audit'
HEAD = '8520e6330e32631df630fecc46204f040a6f911a'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(r, b):
    p = O / r
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)

def jout(r, v):
    put(r, (json.dumps(v, indent=2, ensure_ascii=False) + '\n').encode())

prior = []
for folder, pin, count, total in [
    (P, '9f18104ef707b4adb6306da8c04058368c83fe5838bf9c166c3fff0b080df866', 55, 1033879),
    (T, '3b3ca79084688ceaf00a48933242771784d483c42ae32442605ad91961983bee', 96, 13637609),
]:
    b = (folder / 'seal.json').read_bytes()
    seal = json.loads(b)
    member_bytes = seal.get('member_bytes', seal.get('total_bytes'))
    assert type(member_bytes) is int
    if pin:
        assert sha(b) == pin and seal['member_count'] == count and member_bytes == total
    assert seal['member_count'] == len(seal['members'])
    assert member_bytes == sum(m['bytes'] for m in seal['members'])
    for m in seal['members']:
        raw = (folder / m['path']).read_bytes()
        assert len(raw) == m['bytes'] and sha(raw) == m['sha256']
    put('upstream/' + folder.name + '-seal.json', b)
    prior.append(dict(root=folder.as_posix(), seal_sha256=sha(b), member_count=seal['member_count'],
                     member_bytes=member_bytes, members=seal['members'], verified_in_place=True))
jout('upstream-individual-verification.json', prior)

pin_bytes = (T / 'final-candidate-current-pins.json').read_bytes()
pins = json.loads(pin_bytes)
assert len(pins) == 12 and len({r['path'] for r in pins}) == 12
put('final-candidate-current-pins.json', pin_bytes)
new = {'src/db/NativeSkillSource.h', 'src/db/SharedSkillDefinition.h', 'src/db/SharedSkillDefinition.cpp'}
tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', HEAD, '--', *new], cwd=S)
assert not tracked
current, baseline, refs = {}, {}, []
for p in pins:
    rel = p['path']
    b = (S / rel).read_bytes()
    assert len(b) == p['bytes'] and sha(b) == p['sha256']
    current[rel] = b
    retained = 'current/' + rel
    put(retained, b)
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        source_state='final current candidate; independent static review', baseline_head=HEAD))
    if rel not in new:
        raw = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
        baseline[rel] = raw
        retained = 'baseline/' + rel
        put(retained, raw)
        refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(raw), sha256=sha(raw),
            source_state='immutable published HEAD whole source', source_head=HEAD))
frozen = ['src/cn/assets/CnNativeSkillCatalog.h', 'src/cn/assets/CnNativeSkillCatalog.cpp',
    'src/cn/assets/CnNativeSkillBookBindings.h', 'src/cn/assets/CnNativeSkillBookBindings.cpp',
    'src/cn/world/SharedPrebornWindowSource.h', 'src/cn/world/SharedPrebornWindowSource.cpp',
    'src/core/Config.h', 'src/protocol/TaiwanNativeSkillCommand.h']
for rel in frozen:
    b = (S / rel).read_bytes()
    assert b == subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    retained = 'frozen/' + rel
    put(retained, b)
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        source_state='unchanged actual published HEAD source', source_head=HEAD))
assert len(refs) == 29
jout('source-references.json', refs)

# Reconstruct every existing file using the writer's exact literal receipts.
# New pure module stages are historical changes to new files, not old files.
initial_b = (T / 'exact-edits-and-inverse.json').read_bytes()
initial = json.loads(initial_b)
work = current.copy()
receipt_refs = []
for name in ['utility-include-correction.json', 'qualification-correction.json']:
    raw = (T / name).read_bytes()
    v = json.loads(raw)
    edits = v.get('edits', [v])
    for e in reversed(edits):
        rel = e['path']
        if rel in new:
            continue
        old, after = bytes.fromhex(e['old_hex']), bytes.fromhex(e['new_hex'])
        assert work[rel].count(after) == e.get('count', 1)
        work[rel] = work[rel].replace(after, old)
    receipt_refs.append(dict(actual_path=(T / name).as_posix(), retained=None, bytes=len(raw), sha256=sha(raw),
                             disposition='sealed upstream receipt verified in place; no duplicate large data'))
for e in reversed(initial['edits']):
    rel = e['path']
    if rel in new:
        continue
    old, after = bytes.fromhex(e['old_hex']), bytes.fromhex(e['new_hex'])
    assert work[rel].count(after) == e.get('count', 1), rel
    work[rel] = work[rel].replace(after, old)
for rel in baseline:
    assert work[rel] == baseline[rel], rel
old_struct = re.search(rb'struct NativeSkillSource \{.*?\n\};', baseline['src/db/NativeSkillCatalog.h'], re.S).group()
new_struct = re.search(rb'struct NativeSkillSource \{.*?\n\};', current['src/db/NativeSkillSource.h'], re.S).group()
assert old_struct == new_struct
receipt_refs.append(dict(actual_path=(T / 'exact-edits-and-inverse.json').as_posix(), retained=None,
    bytes=len(initial_b), sha256=sha(initial_b), disposition='sealed upstream literal receipt verified in place'))
newline_b = (T / 'cn-lookup-line-ending-exact-custody.json').read_bytes()
newline = json.loads(newline_b)
assert newline['baseline_sha256'] == sha(baseline['src/cn/assets/CnSharedSkillCatalog.cpp'])
assert newline['current_sha256'] == sha(current['src/cn/assets/CnSharedSkillCatalog.cpp'])
put('cn-lookup-line-ending-exact-custody.json', newline_b)
jout('nine-complete-byte-inverses-and-new3.json', dict(head=HEAD, inverse_equal_all=True,
    existing_files=[dict(source=rel, before_bytes=len(b), before_sha256=sha(b),
        final_bytes=len(current[rel]), final_sha256=sha(current[rel])) for rel,b in baseline.items()],
    new3_absent_at_HEAD=sorted(new), native_source_struct_byte_unchanged=True, receipt_references=receipt_refs))

# Independent source-text literal reconciliation: no C++ API, importer or BIN
# resource parser is executed. Already sealed raw bytes supply exact slices.
rawrefs = json.loads((R / 'source-references.json').read_bytes())
sources, inputs = {}, []
for r in rawrefs:
    b = (R / r['retained']).read_bytes()
    assert len(b) == r['bytes'] and sha(b) == r['sha256']
    sources[r['sha256']] = b
    inputs.append(dict(actual_path=(R / r['retained']).as_posix(), retained=None, bytes=len(b), sha256=sha(b),
                       disposition='sealed actual raw bytes verified in place; no whole BIN copy'))
raw150 = (P / 'retained-custom150-record.bin').read_bytes()
text = current['src/db/SharedSkillDefinition.cpp'].decode('utf-8')
lo = text.index('const Pin pins[]={\n') + len('const Pin pins[]={\n')
hi = text.index('\n};', lo)
lines = text[lo:hi].splitlines()
assert len(lines) == 907
counts, row_proof = {}, []
for line in lines:
    match = re.fullmatch(r'\s*\{(.*),\{\{(.*)\}\}\},', line)
    assert match
    row = json.loads('[' + match[1].replace('SharedSkillRegion::Taiwan', '"TW"').replace('SharedSkillRegion::China', '"CN"') + ']')
    region,kind,id,ordinal,offset,digest,source_digest,count,*literals = row
    expected = bytes(int(z,16) for z in match[2].split(','))
    actual = raw150 if source_digest == 'f159b61f0aeacc46e71519cd6e98910381eda22336ad07487b2cf7213ec6297d' else sources[source_digest][offset:offset+110]
    assert len(expected) == 110 and expected == actual and sha(expected) == digest and expected[:2] == bytes([id,kind])
    counts[region + ':' + source_digest] = counts.get(region + ':' + source_digest, 0) + 1
    row_proof.append(dict(region=region, kind=kind, id=id, ordinal=ordinal, source_offset=offset,
        source_sha256=source_digest, record_sha256=digest, bytes=110, expected_equal_source=True))
jout('907-full110-independent-source-proof.json', dict(rows=907, expected_bytes=99770,
    counts=counts, rows_verified=row_proof, inputs=inputs, execution='source text/hash/byte slices only'))

specs = [('src/db/NativeSkillCatalog.cpp', 64, 133), ('src/db/SharedSkillDefinition.cpp', 927, 1040),
    ('src/cn/assets/CnSharedSkillCatalog.cpp', 84, 109), ('src/cn/world/CnPrebornSkillChoiceSource.cpp', 26, 60),
    ('src/scripting/LuaEngine.cpp', 127, 158), ('src/scripting/LuaEngine.cpp', 290, 305),
    ('src/scripting/LuaEngine.cpp', 429, 487), ('src/core/Application.cpp', 848, 864),
    ('src/cn/world/SharedPrebornWindowSource.cpp', 115, 140)]
cuts = []
for i, (rel, first, last) in enumerate(specs):
    b = current.get(rel, (S / rel).read_bytes())
    lines = b.splitlines(keepends=True)
    assert 1 <= first <= last <= len(lines), (rel, len(lines))
    raw = b''.join(lines[first - 1:last])
    retained = 'cuts/%02d-%s-L%d-L%d.txt' % (i, Path(rel).name, first, last)
    put(retained, raw)
    cuts.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(raw), sha256=sha(raw),
        first_line=first, last_line=last, boundary='selected excerpt; complete containing source retained'))
jout('source-cuts.json', cuts)
put('REPORT.md', b'''# Round359 independent shared skill definition source review

PASS for final12 sources: existing9 complete byte-inverses equal immutable published8520e6330e32631df630fecc46204f040a6f911a; new3 absent at that HEAD. NativeSkillSource struct bytes moved unchanged. Twenty-nine whole references retain current12/baseline9/frozen8, and nine scoped excerpts retain actual handoff context. P359 and final implementation seals were individually checked in place. Original failures/corrections are historical upstream evidence, never silently refreshed. No target execution, SQL/API/native/codec/compiler/build/tests or tracked edit occurred.

One consequential initial finding was corrected before final freeze: public digest flag previously allowed a caller's mismatched raw110 to become OriginalRowPinned. Final qualify resets enum and compares ALL110 expected bytes plus source/digest/ordinal/offset/count/original image pins. The public digest flag is informational, not a proof. Independent source-text reconciliation verified907 literal arrays against sealed actual source bytes: TW448, CN453, installed owner5 and custom1501, totaling99770 bytes. Positional TW/CN region mismatches are rejected before composition; public enum/flag cannot bypass those checks. This row attestation is not whole-file/native-bank/current/entitlement attestation.

Canonical selection is explicit CUSTOM0138 owner policy: complete TW rows are primary for both-complete conflicts0/95 and1/129; confirmed missing1/83 and four reserved0/122..125 use complete CN rows, including CN Traditional text rather than generic TW reserve labels. Legitimate zero fields are retained; whole selected raw rows are not assembled by guessed field filling. Source literals remain bounded data, not recovered UI width. Unknown snapshots remain MetadataSnapshotOnly and do not supply fake parameters. Original NativeSkillRecord/default lookups/equality remain byte-exact; requested_native optional never fabricates a missing TW row or substitutes chosen TW for real CN native material. Unsupported digest provider preserves valid legacy raw data; exact source arrays can independently qualify equal rows.

The new explicit DB path owns BEGIN/COMMIT only under autocommit, otherwise borrows caller scope. Main's final Lua argument forwards the same actual Database reader; Lua owner checks/initialize/rebuild retain that provider lifetime and the old native getter. The returned owning metadata is not a new source Current, learning rule, MP debit or cast entitlement. CN lookup_shared retains existing private game-owner/reentry/terminal/store/native Current fences before and after observations, exact source/ordinal/offset/hash/full CN raw equality, and requested_native is the actual original CN row. Chosen common metadata never replaces native Current or source rights.

CN Facts owns common descriptors in original request order/duplicates and preserves book/subject/primary qualification. Existing final Current checks remain; actual SharedPreborn apply consumes owning facts and actual delivery receives those retained facts after source retirement, without reusing obsolete precommit Current. Frozen private native providers/window/config/native wire remain exact. Actual runtime population/import/learned grants/full protocol hosting/CNcustom visual compatibility/native acceptance and damage/hit/critical formulas remain separate OPEN work. This source connection is one common definition registry/provider, not a claimed full gameplay route. The client MP gate semantic package is independent and adds no recovered native-method credit.
''')
jout('capture-complete.json', dict(status='PASS', baseline_head=HEAD, whole_count=len(refs),
    current_count=12, existing_inverses=9, new_files=3, cut_count=len(cuts), pins_verified=907,
    upstream_count=len(prior), upstream_members=sum(p['member_count'] for p in prior),
    upstream_bytes=sum(p['member_bytes'] for p in prior), semantic_verdict='PASS', target_execution=False))
for rel,b in current.items():
    assert (S / rel).read_bytes() == b
members = []
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name != 'SEAL.json':
        b = p.read_bytes()
        members.append(dict(path=p.relative_to(O).as_posix(), bytes=len(b), sha256=sha(b)))
total = sum(m['bytes'] for m in members)
assert isinstance(total, int)
jout('SEAL.json', dict(status='PASS', member_count=len(members), member_bytes=total, members=members))
for m in members:
    b = (O / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
sb, hb = (O / 'SEAL.json').read_bytes(), Path(__file__).read_bytes()
assert b'\r' not in hb
print(json.dumps(dict(status='PASS', member_count=len(members), member_bytes=total,
    seal_bytes=len(sb), seal_sha256=sha(sb), helper_bytes=len(hb), helper_sha256=sha(hb))))
