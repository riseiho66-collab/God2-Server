from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent
REV = '43f4d294b8f017d2b00d697aa68a9c2e3726d8d5'
SPEC = {
    'src/main.cpp': [(12, 27), (41, 86)],
    'src/core/Application.h': [(1, 20)],
    'src/core/Application.cpp': [(557, 579), (668, 715), (843, 852), (1007, 1058), (1198, 1214), (1375, 1381), (2208, 2219), (2231, 2256), (2291, 2305), (2354, 2390), (2568, 2619), (2621, 2655), (4440, 4468), (4495, 4507), (4554, 4584), (4763, 4773), (5723, 5742), (6441, 6449), (6490, 6507), (6701, 6740), (7361, 7374)],
    'src/core/Config.h': [(14, 49), (120, 126)],
    'src/core/Config.cpp': [(525, 548), (633, 656)],
    'src/net/Session.h': [(108, 129), (267, 275), (328, 348), (421, 440), (459, 468)],
    'src/net/Session.cpp': [(61, 68), (116, 150), (1530, 1568), (1585, 1628), (1940, 1968), (2184, 2208), (2318, 2359), (3185, 3200)],
    'src/handlers/RecoveredMovementService.h': [(17, 21), (38, 68), (118, 154)],
    'src/handlers/RecoveredMovementService.cpp': [(203, 234), (289, 318), (480, 521)],
    'src/handlers/RecoveredWorldService.h': [(6, 38)],
    'src/handlers/RecoveredWorldService.cpp': [(6, 18), (85, 101)],
    'src/handlers/InventoryMoveService.cpp': [(8, 36)],
    'src/protocol/RecoveredInventoryMoveRequest.h': [(8, 35)],
    'src/protocol/RecoveredWorldEntryView.h': [(72, 94)],
    'src/db/SqliteDatabase.h': [(63, 98)],
    'src/db/SqliteDatabase.cpp': [(206, 225), (263, 296)],
    'src/db/SqliteOwnedEquipmentTransaction.h': [(17, 30), (87, 101), (105, 156)],
    'src/db/SqliteOwnedEquipmentTransaction.cpp': [(7, 24), (36, 89), (192, 231)],
    'src/db/NativeEquipmentSnapshotRepository.h': [(11, 40)],
    'src/db/SqliteRecoveredCharacterRepository.cpp': [(958, 996)],
    'src/game/SharedTaiwanOwnedBagMoveSource.h': [(6, 23)],
    'src/game/SharedTaiwanOwnedBagMoveSource.cpp': [(6, 112), (113, 218)],
    'src/game/SharedTaiwanWorldRecordSource.h': [(35, 72)],
    'src/game/SharedTaiwanMovementSource.cpp': [(44, 53), (148, 155), (199, 209)],
    'src/game/SharedTaiwanOwnedInventoryReplySource.cpp': [(83, 113)],
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

refs = []
cuts = []
file_end_adjustments = []
text = []
head_start = git('rev-parse', 'HEAD').decode().strip()
for name, ranges in SPEC.items():
    # Every retained cut is from the immutable named commit, including old C24.
    body = git('show', f'{REV}:{name}')
    lines = body.decode('utf-8-sig').splitlines()
    working = (ROOT / name).read_bytes()
    refs.append({'path': name, 'snapshot_git_revision': REV, 'snapshot_bytes': len(body), 'snapshot_sha256': sha(body),
                 'working_bytes_at_capture': len(working), 'working_sha256_at_capture': sha(working),
                 'working_equals_snapshot': working == body})
    for low, high in ranges:
        if high > len(lines):
            file_end_adjustments.append({'path': name, 'requested_end': high, 'actual_end': len(lines)})
            high = len(lines)
        if not 1 <= low <= high <= len(lines):
            raise ValueError((name, low, high, len(lines)))
        cut = ''.join(f'{name}:{i}: {lines[i-1]}\n' for i in range(low, high+1)).encode()
        cuts.append({'path': name, 'first_line': low, 'last_line': high, 'numbered_cut_bytes': len(cut), 'sha256': sha(cut)})
        text.append(cut.decode())

(OUT / 'retained-source-cuts.txt').write_bytes('\n'.join(text).encode())
metadata = {'scope': 'Static source/hash only. No target code, API, compiler, tests, runtime, database or SQL executed.',
            'snapshot_revision': REV, 'head_at_capture_start': head_start, 'head_at_capture_end': git('rev-parse', 'HEAD').decode().strip(),
            'source_count': len(refs), 'cut_count': len(cuts), 'file_end_adjustments': file_end_adjustments, 'sources': refs}
(OUT / 'source-references.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8', newline='\n')
(OUT / 'source-cuts.json').write_text(json.dumps(cuts, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'sources': len(refs), 'cuts': len(cuts), 'snapshot': REV, 'working_differences': [r['path'] for r in refs if not r['working_equals_snapshot']]}))
