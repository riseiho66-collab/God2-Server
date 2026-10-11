"""Snapshot conditional native19/common identity source and retained provenance.

File reads/hashes only. Does not call C++ identity/gameplay, build, test, run
clients/servers, touch production databases or replace any prior evidence.
"""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, CN, PIN

NAME='cn-character-delete-identity-01'
ROUND='20261007-cn-character-delete-identity'
SOURCE=('src/cn/auth/SharedCharacterDeleteIdentity.h',
        'src/cn/auth/SharedCharacterDeleteIdentity.cpp',
        'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
        'src/cn/protocol/CnCharacterDelete.h','src/cn/protocol/CnCharacterSummary.h',
        'src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
        'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
        'src/db/RecoveredCharacterRepository.h','src/cn/auth/SharedAccountSelection.cpp',
        'CMakeLists.txt','docs/research/cn-character-delete-identity-20261007.md',
        'tools/reconstruction/cn_character_delete_identity_delivery.py')

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve sealed evidence')
    image=CN.parent/'XJZ-CN/God2_opt.exe'
    if hashlib.sha256(image.read_bytes()).hexdigest()!=PIN:
        raise RuntimeError('Pinned CN image changed')
    files=[]
    def save(rel,data,original=None):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        files.append({'path':rel,'original':original,'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):save(rel,(json.dumps(obj,indent=2)+'\n').encode())
    for rel in SOURCE:save('source/'+rel,(ROOT/rel).read_bytes(),str(ROOT/rel))
    for rel in ['cn-character-mutation-contract-01/native-manifest.json',
                'cn-character-mutation-contract-01/native/00446bd0.asm',
                'cn-character-mutation-contract-01/native/0047e960.asm',
                'cn-account-selection-owner-01/integration-manifest.json',
                'cn-world-selection-owner-01/integration-manifest.json',
                'cn-delete-completion-lifecycle-01/findings.json']:
        save('retained-provenance/'+rel,(base/rel).read_bytes(),str(base/rel))
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: saved deletion local return/UI/control source evidence and bounded close-control view',
        'identity_source_resolvers_added':1,'new_cpp_files':1,
        'source_selection_owner_entry':'SharedWorldSelection::resolve_deletion_identity',
        'current_check':'same weak connection/account/world-session, committed ticket-bound source bytes+ID order, unique advertised slots/IDs, current whole offered common ownership and owner phase',
        'credentials_retained_by_identity':False,
        'actual_deletion_ingress_connected':False,'actual_delete_transaction_added':False,
        'gameplay_handlers_added':0,'phase_opcode_source_bindings_added':0,
        'source_owner_chains_added':0,'new_packet_values':0,
        'new_complete_bidirectional_routes':0,'whole_game_completion_percent':None,
        'remaining':['Actual19 ingress/rule/online-owner/save-revision/CAS/atomic deletion and duplicate-operation owner still missing; identity snapshot is not permission or consumed token.',
          'Complete actual02/1E data,1E exception continuation,0204/03 close controller and formal Application hosting remain open.',
          'Independent resolver admits structural0..7 slots; current NativeOffer1A bounds stay below4 and high-slot lifecycle remains unhosted.',
          'Real native summary/world/login/bootstrap issuers,17/18/1B mutations and whole-game directional/phase/state/variant denominator remain open.'],
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'database_access':False,'levels_changed':False}
    dump('findings.json',findings)
    dump('source-manifest.json',{'files':files,'native_sha256':PIN,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False})
    print(json.dumps({'round':ROUND,'identity_source_resolvers_added':1,
        'source_snapshots':len(SOURCE),'actual_deletion_handlers_added':0,
        'new_complete_bidirectional_routes':0}))

if __name__=='__main__':main()
