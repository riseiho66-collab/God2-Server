"""Code-only repair of scene-arrival owner identity; preserve config and saves."""
import json
import argparse
from pathlib import Path
import shutil
from tools.operations import native_quest_catalog_release as managed
from tools.operations import native_logout_doors_release_20260927 as release_base

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-name',default='native-scene-identity-chat-fix-20260927-01')
    args=parser.parse_args()
    if not args.release_name.startswith('native-scene-identity-chat-fix-') or '/' in args.release_name or '\\' in args.release_name:
        raise ValueError('Invalid release directory')
    root=managed.ROOT
    release=root/'artifacts/releases'/args.release_name
    evidence_path=root/'artifacts/research/current-scene-arrival-identity-20260927.json'
    evidence=json.loads(evidence_path.read_text('utf-8'))
    if not evidence.get('accepted'):raise ValueError('Original producer qualification failed')
    if release.exists():raise ValueError('Release already exists')
    config=json.loads(managed.CONFIG.read_text('utf-8'));database=Path(config['database']['path'])
    managed.listener() # No active players. Owner explicitly requested this restart.
    release.mkdir(parents=True)
    shutil.copy2(managed.ACTIVE,release/'god2-server.before.exe')
    shutil.copy2(release_base.CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(managed.CONFIG,release/'server-config.before.json')
    shutil.copy2(managed.CONFIG,release/'server-config.candidate.json')
    managed.backup(database,release/'accounts.before.db')
    manifest={'candidate_sha256':managed.sha(release_base.CANDIDATE),
        'old_server_sha256':managed.sha(managed.ACTIVE),'config_sha256':managed.sha(managed.CONFIG),
        'client_sha256':managed.sha(managed.CLIENT),'database':str(database),
        'town_doors':config['development']['diagnostic_town']['all_door_routes'],
        'kunlun_doors':config['development']['diagnostic_town']['kunlun_door_routes'],
        'database_replacement':False,'configuration_change':False,
        'scope':'Owned scene-arrival identity; early-chat presence after accepted world tail; area+scene chat isolation',
        'native_evidence':str(evidence_path),'native_evidence_sha256':managed.sha(evidence_path),
        'current_client_chat_acceptance':'pending; owner requested restart for validation'}
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    release_base.apply(release)

if __name__=='__main__':main()
