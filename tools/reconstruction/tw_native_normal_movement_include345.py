from pathlib import Path
import hashlib, json

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round345-normal-entry-movement-implementation')
source = ROOT / 'src/handlers/RecoveredMovementService.cpp'
prior = source.read_bytes()
assert hashlib.sha256(prior).hexdigest() == 'fde6907bd8cfcfb1f5e9bbe62e927c91c018a708fc5a65b499e2f973f0168751'
needle = b'#include <limits>\n'
addition = b'#include <string_view>\n'
assert prior.count(needle) == 1 and addition not in prior
final = prior.replace(needle, needle + addition, 1)
assert final.replace(addition, b'', 1) == prior
assert source.read_bytes() == prior
source.write_bytes(final)
(OUT / 'frozen-RecoveredMovementService.cpp').write_bytes(final)
(OUT / 'frozen-RecoveredMovementService.h').write_bytes((ROOT / 'src/handlers/RecoveredMovementService.h').read_bytes())
receipt = {'correction': 'Explicit direct <string_view> include; original limits line is LF, initial generated snapshot stays immutable',
           'initial_sha256': hashlib.sha256(prior).hexdigest(),
           'final_sha256': hashlib.sha256(final).hexdigest(),
           'final_bytes': len(final), 'inverse_equals_initial': True,
           'target_execution': False}
(OUT / 'direct-include-correction.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(receipt))
