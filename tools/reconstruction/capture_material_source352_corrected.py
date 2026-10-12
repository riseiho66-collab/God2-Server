"""Exclusive successor; retain failed source-range capture, then seal corrected cuts."""
from pathlib import Path
import hashlib
import json

out = Path(__file__).resolve().parent
assert out.resolve() == Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round352-original-bag-material-issuer-source-audit').resolve()
assert not (out / 'SEAL.json').exists()
failure = out / 'failure-initial'
assert not failure.exists()
failure.mkdir()
members = []
for folder in ('sources', 'cuts'):
    target = out / folder
    assert target.resolve().is_relative_to(out.resolve())
    for path in sorted(target.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            members.append({'path': path.relative_to(out).as_posix(), 'bytes': len(raw),
                            'sha256': hashlib.sha256(raw).hexdigest()})
    target.rename(failure / folder)
receipt = {'failed_helper': 'capture_material_source352.py', 'exit_code': 1,
    'error': 'AssertionError at line85: drafted importer cut117..156 exceeded actual148 lines.',
    'corrected_range': [117, 148], 'partial_members': members,
    'partial_member_count': len(members), 'partial_member_bytes': sum(x['bytes'] for x in members),
    'target_execution_count': 0, 'tracked_edits': 0}
(failure / 'failure-receipt.json').write_bytes((json.dumps(receipt, indent=2) + '\n').encode())
source = (out / 'capture_material_source352.py').read_text(encoding='utf-8')
old = "('tools/strike_lab/import_native_armor_20261002.py', 117, 156, 'definition-cache-import-not-player-instance')"
new = old.replace('117, 156', '117, 148')
assert source.count(old) == 1
source = source.replace(old, new)
source = source.replace("'helper_failures': [], 'helper_successes': 1", "'helper_failures': [{'helper': 'capture_material_source352.py', 'exit_code': 1, 'range': '117..156 beyond148; preserved failure-initial'}], 'helper_successes': 1")
source = source.replace('20261002.py1..53 and117..156', '20261002.py1..53 and117..148')
source = source.replace('no product target was executed. supplier-gap.json', 'no product target was executed. The initial range assertion and every partial member are retained in failure-initial; the exclusive successor corrects only the importer cut end148 and custody wording. supplier-gap.json')
edits = {'original_helper_sha256': hashlib.sha256((out / 'capture_material_source352.py').read_bytes()).hexdigest(),
    'changes': ['cut117..156 ->117..148', 'retained failure metadata', 'report range/custody wording'],
    'generation': 'compile/exec this source-only capture helper, not any product/parser/API',
    'successful_source_sha256': hashlib.sha256(source.encode()).hexdigest()}
(out / 'corrected-capture-recipe.json').write_bytes((json.dumps(edits, indent=2) + '\n').encode())
(out / 'successful-capture-source352.py').write_bytes(source.encode())
exec(compile(source, str(out / 'successful-capture-source352.py'), 'exec'),
     {'__file__': str(out / 'successful-capture-source352.py'), '__name__': '__main__'})
