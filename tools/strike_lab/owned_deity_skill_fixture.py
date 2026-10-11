"""Explicit isolated assignments, with build-matched skill definitions only."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.strike_lab import import_native_skills as catalog

def verified_catalog(connection,client_root):
    expected=catalog.pinned_records(client_root)
    source=connection.execute('select '+catalog.SOURCE_COLUMNS+' from native_data_sources where dataset_id=?',(catalog.DATASET,)).fetchall()
    actual=connection.execute('select '+catalog.RECORD_COLUMNS+' from native_skill_catalog where dataset_id=? order by source_record_index',(catalog.DATASET,)).fetchall()
    if source!=[catalog.SOURCE_ROW] or actual!=expected:
        raise ValueError('Isolated learned-skill catalog differs from pinned current source')
    return expected

def assignments(rows):
    if len(rows)!=448:raise ValueError('Expected448 current definitions')
    identities=[(row[5],row[6]) for row in rows]
    if len(set(identities))!=448:raise ValueError('Duplicate source definitions')
    receipt=ROOT/'artifacts/playtests/private-deity-skills-20260927-06/ui-result.json'
    raw=receipt.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='bb815dbf4daeb4e7d2b597d6c9d2d28cfbb1fce8b5dc7f38da8b6e0d1e03e7a6':
        raise ValueError('Pinned native icon observation changed')
    evidence=json.loads(raw)
    if not evidence['accepted']:raise ValueError('Icon observation was not accepted')
    audit=evidence['skill_icon_audit']['rows']
    if [(r['kind'],r['id']) for r in audit]!=identities:raise ValueError('Incomplete icon identity audit')
    identities=[(r['kind'],r['id']) for r in audit if r['display_eligible']]
    if len(identities)!=409:raise ValueError('Current native resource scope changed')
    result={key:b''.join(bytes((0x34,key,*identities[((key-1)*100+i)%len(identities)])) for i in range(100)) for key in range(1,17)}
    observed={(blob[i+2],blob[i+3]) for blob in result.values() for i in range(0,len(blob),4)}
    if observed!=set(identities):raise ValueError('Fixture does not cover all display-qualified definitions')
    return result
