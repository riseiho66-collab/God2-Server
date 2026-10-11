"""Candidate-specific1D gate, preserving pose/chat regressions."""
import hashlib,io,json,subprocess,sys,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tests/research'))
import test_native_peer_pose_server as pose
import test_current_options_1d_server as options
import test_player_visibility_server as visibility
from tools.strike_lab.current_options_1d_20261002 import prove

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    folder=ROOT/'artifacts/releases/native-options-1d-20261002'
    binary=ROOT/'build-town-visibility/Release/god2-server-native-results.exe';pose.dual.BINARY=binary
    options.pet2.BINARY=binary;suite=unittest.TestSuite()
    for cls in (pose.NativePeerPoseServerTests,options.CurrentOptionsServerTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    suite.addTest(visibility.PlayerVisibilityServerTests('test_visible_peers_exchange_converted_chat_and_keep_movement'))
    stream=io.StringIO();tested=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (folder/'tcp-gate.log').write_text(str(binary)+'\n'+stream.getvalue(),encoding='utf-8')
    if not tested.wasSuccessful() or tested.testsRun!=4:raise RuntimeError('Candidate TCP failure')
    for label,command in (
        ('cpp',['ctest','--test-dir','build-town-visibility','-C','Release','-R',
          '^(recovered_world_records|recovered_world_service|recovered_visibility)$','--output-on-failure']),
        ('inventory',[sys.executable,'-B','-m','unittest','tests.research.test_current_packet_gap_ledger','-v']),
        ('frozen',[sys.executable,'-B','-m','tools.operations.verify_frozen_chat_20260927'])):
        run=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        (folder/(label+'-gate.log')).write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError(label+' gate failed')
    native=prove();(ROOT/'artifacts/research/native-options-1d-20261002.json').write_text(json.dumps(native,indent=2),encoding='utf-8')
    names=['src/protocol/RecoveredWorldRecords.h','src/handlers/RecoveredWorldService.cpp','src/core/Application.cpp',
        'tests/test_recovered_world_records.cpp','tests/test_recovered_world_service.cpp',
        'tests/research/test_current_options_1d_server.py','tests/research/test_current_packet_gap_ledger.py',
        'tools/strike_lab/current_options_1d_20261002.py','tools/strike_lab/private_options_1d_20261002.py',
        'tools/strike_lab/native_options_1d_gate_20261002.py','tools/operations/native_options_1d_release_20261002.py']
    manifest={'time':datetime.now(timezone.utc).isoformat(),'candidate_sha256':sha(binary),
        'formal_deployed':False,'source_sha256':{name:sha(ROOT/name) for name in names},
        'verification':{'tcp_cases':4,'cpp_targets':3,'inventory_cases':1,'native_producer_cases':native['passed'],
          'frozen_chat_passed':True},'whole_game_completion_percent':None,
        'limits':'Native1D transport and local UI acceptance only; original server effects and battle/mixed variants open'}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'accepted':True,'tcp':4,'cpp':3,'inventory':1,'native':native['passed']}))
if __name__=='__main__':main()
