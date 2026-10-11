"""Reproducible candidate-specific native pose release gate."""
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/research'))
from tools.strike_lab.current_peer_pose_20261002 import prove
import test_native_peer_pose_server as native
import test_player_visibility_server as visibility

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    folder=ROOT/'artifacts/releases/native-peer-pose-20261002'
    candidate=ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
    native.dual.BINARY=candidate
    suite=unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(native.NativePeerPoseServerTests))
    for name in ('test_visible_peers_exchange_converted_chat_and_keep_movement',
                 'test_join_committed_batch_leave_and_reconnect',
                 'test_owned_battle_sets_title_until_terminal_receipt'):
        suite.addTest(visibility.PlayerVisibilityServerTests(name))
    stream=io.StringIO();tested=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (folder/'candidate-tcp-gate.log').write_text(str(candidate)+'\n'+stream.getvalue(),encoding='utf-8')
    if not tested.wasSuccessful() or tested.testsRun!=5:raise RuntimeError('Candidate TCP gate failed')
    for label,command in (
        ('candidate-cpp-gate',['ctest','--test-dir','build-town-visibility','-C','Release','-R',
          '^(recovered_visibility|recovered_world_service|peer_role_text)$','--output-on-failure']),
        ('frozen-chat-gate',[sys.executable,'-B','-m','tools.operations.verify_frozen_chat_20260927'])):
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        (folder/(label+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(label+' failed')
    oracle=prove()
    (ROOT/'artifacts/research/native-peer-pose-20261002.json').write_text(json.dumps(oracle,indent=2),encoding='utf-8')
    files=['src/protocol/RecoveredCharacterPose.h','src/handlers/RecoveredVisibility.h','src/core/Application.cpp',
        'tests/test_recovered_visibility.cpp','tests/research/test_native_peer_pose_server.py',
        'tools/strike_lab/current_peer_pose_20261002.py','tools/strike_lab/private_peer_pose_20261002.py',
        'tools/strike_lab/native_peer_pose_gate_20261002.py','tools/operations/native_peer_pose_release_20261002.py']
    old=folder/'manifest.json'
    if not (folder/'manifest.initial.json').exists():shutil.copy2(old,folder/'manifest.initial.json')
    manifest={'time':datetime.now(timezone.utc).isoformat(),'candidate_sha256':sha(candidate),
        'formal_sha256':sha(ROOT/'build-town-visibility/Release/god2-server.exe'),'formal_deployed':False,
        'native_rendered_client_accepted':False,'source_sha256':{name:sha(ROOT/name) for name in files},
        'verification':{'native_consumer_cases':{'passed':oracle['passed'],'total':48},
          'native_lifecycle_cases':{'passed':oracle['lifecycle_passed'],'total':6},
          'tcp_cases':{'passed':tested.testsRun,'total':5,'new':2,'existing_regressions':3,
                       'binary':str(candidate),'binary_sha256':sha(candidate)},
          'cpp_targets':['recovered_visibility','recovered_world_service','peer_role_text'],
          'frozen_chat_passed':True},'whole_game_completion_percent':None,
        'limitations':['Original server membership/cache policy remains CUSTOM-0027',
                       'Rendered pixels not tested; real-client animation/ACT acceptance recorded separately']}
    old.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    shutil.copy2(candidate,folder/'god2-server.candidate.exe')
    print(json.dumps({'accepted':True,'tcp':5,'cpp':3,'native':oracle['passed'],'lifecycle':oracle['lifecycle_passed']}))
if __name__=='__main__':main()
