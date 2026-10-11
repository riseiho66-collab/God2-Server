"""Static source provenance for actual CN ready/native transport integration.

Source-ready capture then explicit BATCHFINAL full-current capture/seal. No PE,
native/API/codec/runtime/build/test/database execution or invented native input.
"""
from pathlib import Path
import hashlib
import json
import sys

SERVER=Path(__file__).resolve().parents[2]
ROUND=SERVER/'artifacts/integration/packet-connections-20261006/shared-native-world-transport-source-01'
OUT=ROUND/'agents/cn-ready-native-transports'
OWN='tools/reconstruction/cn_native_world_transports184.py'
MODIFIED=['src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp']
SOURCE=MODIFIED+['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/world/SharedPostWorldExit.h','src/cn/world/SharedPostWorldExit.cpp',
    'src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'src/cn/protocol/CnWorldEntry.h','src/cn/protocol/CnRemoteActor.h']
CONTEXT=['src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
    'src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(rel,value,replace=False):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('wb' if replace else 'xb') as stream:
        stream.write((json.dumps(value,indent=2)+'\n').encode())


def retain(rel,path,repository=True):
    raw=path.read_bytes();p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:stream.write(raw)
    return {'path':path.relative_to(SERVER).as_posix() if repository else str(path.resolve()),
        'copy':rel,'bytes':len(raw),'sha256':sha(raw)}


def findings(final):
    return {'round':184,'scope':'Actual source integration of optional same-presence CN ready/native transport registry, not original client evidence or completed routes.',
        'source_files_modified':MODIFIED,'owned_cpp_edits':4,'native_original_inputs':0,
        'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':0,'retained_bounded_native_bytes':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':address,'phase':None,'slot':None,'producer':None}
            for address in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'actual_source_connections':[
            {'key':'same_presence_optin_composition','sources':MODIFIED,
             'scope':'Sources.world_transports is optional; compose and Ready.attach reject mismatched presence registry. The identical configured pointer reaches Ready and actual SharedNativeChat.attach. Missing registry preserves existing non-optin behavior; no synthesized ready lease/profile/permission/native output.'},
            {'key':'bind_after_complete_initial_outward','sources':['src/cn/world/SharedWorldReady.cpp','src/cn/world/SharedActorVisibility.cpp'],
             'scope':'Real initial1C publication activates exact lease, installs actual gameplay owners, publishes initial visibility, and releases held incoming output. Only successful publish_outward_initial completion after every actual observer queue release reaches bind_native_transport before consume/gameplay remainder. Actual issuer explicit empty observer set is valid; partial/failure fanout cannot bind. Native queue acceptance is not client acceptance.'},
            {'key':'generation_token_disconnect_capsule','sources':['src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp','src/cn/net/SharedCredentialConnection.cpp'],
             'scope':'Independent NativeTransportState capsule contains exact optional Token and terminal released flag, captured by actual install_world_cleanup without strong Ready/connection. Token transport is weak. Registry-only release takes saved token and resets capsule before visibility/presence/release_world. Interrupted bind cannot resurrect a released capsule. No cleanup by alias/session/new lease lookup.'},
            {'key':'failure_paths_before_common_cleanup','sources':MODIFIED,
             'scope':'Ready.fail revokes exact native token before visibility/presence/close. Compose stores weak Ready registry-only release callback in Gameplay; finish(false) calls it before its existing visibility/presence cleanup. Actual post-world exit drain retains existing OnClosed path which invokes same capsule first. External direct presence release is not silently converted into registry successor deletion; lookup/current must fail when actual lease is no longer ready.'},
            {'key':'qualified_owned_token_bind','sources':['src/cn/world/SharedWorldReady.cpp','src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp'],
             'scope':'Bind holds actual strong current CN connection and full immutable lease, active batch, InWorld stage, ready ownership and admission around registry bind/current. Terminal capsule/binding guard prevents reentry resurrection. Saved Token is copied before external registry observers, so nested cleanup cannot destroy a borrowed optional element. Registry supplies private generation/weak actual connection, not a masked common ID or guessed transport.'},
        ],
        'additional_source_repair':'Owned Ready publication lambda explicitly captures batch used by its existing failure branch; no C++ build/test performed.',
        'missing_original_epoch':'First transient edit before the small endpoint/owned-token/catch refinement was not separately full-file captured. Freshbefore1313 actual originals and actual source-ready full copies are retained; no reconstructed bytes labeled original.',
        'gaps':['Actual opted-in Reservation/Entered and WorldOwner source configuration in Main/Application remain required.',
            'Registry supplies actual transport, not native header/body/audience/party/guild/mute/rate/visibility rights.',
            'No actual native client/runtime acceptance or whole-game completion established.'],
        'builds_tests_runtime_native_api_codec_db_deploy':False,'BATCHFINAL_received':final}


def source_ready():
    if not (OUT/'before-source-origins.json').exists():
        raise RuntimeError('Actual pre-edit copies must already exist')
    if (OUT/'findings.json').exists():
        raise RuntimeError('Preserve existing source-ready capture')
    before=json.loads((OUT/'before-source-origins.json').read_bytes())
    fresh={row['path']:row for row in json.loads((ROUND/'before-manifest.json').read_bytes())}
    for n,rel in enumerate(SOURCE[4:]):
        row=fresh[rel];p=ROUND/row['snapshot'];raw=p.read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:
            raise ValueError('Freshbefore1313 original differs '+rel)
        captured=retain(f'before/s{n:02d}{p.suffix}',p,False)
        captured.update({'path':rel,'snapshot_original':str(p.resolve()),'epoch':'Full actual freshbefore1313 source'})
        before.append(captured)
    dump('before-source-origins.json',before,True)
    initial=[retain(f'source-ready/i{n:02d}{Path(rel).suffix}',SERVER/rel)
             for n,rel in enumerate(MODIFIED+[OWN])]
    dump('source-ready-source-origins.json',initial)
    contexts=[retain(f'context-initial/k{n:02d}{Path(rel).suffix}',SERVER/rel)
              for n,rel in enumerate(CONTEXT)]
    dump('context-initial-source-origins.json',contexts)
    dump('native-original-inputs.json',[])
    dump('source-absence.json',{'absent_freshbefore1313':[OWN]+[rel for rel in CONTEXT if rel not in fresh],
        'native_original_inputs':0,'scope':'Only actual source/file reading; source code never mislabeled original PE evidence.'})
    dump('derived-inputs.json',[retain('derived/freshbefore1313.json',ROUND/'before-manifest.json',False)])
    dump('findings.json',findings(False))
    print(json.dumps({'state':'source-ready','cpp_files':len(MODIFIED),'native_inputs':0,
        'awaiting_BATCHFINAL':True,'tool_sha256':sha((SERVER/OWN).read_bytes())}))


def final_capture():
    if (OUT/'seal.json').exists():
        raise RuntimeError('Preserve sealed artifact')
    if not (OUT/'findings.json').exists():
        raise RuntimeError('Source-ready capture required')
    prior=(OUT/'findings.json').read_bytes()
    with (OUT/'findings-source-ready.json').open('xb') as stream:stream.write(prior)
    current=[retain(f'current/c{n:02d}{Path(rel).suffix}',SERVER/rel)
             for n,rel in enumerate(SOURCE+[OWN])]
    contexts=[retain(f'context-final/k{n:02d}{Path(rel).suffix}',SERVER/rel)
              for n,rel in enumerate(CONTEXT)]
    dump('current-source-origins.json',current)
    dump('context-final-source-origins.json',contexts)
    dump('original-inputs.json',[{**row,'path':str((SERVER/row['path']).resolve())}
        for row in current+contexts])
    initial=json.loads((OUT/'source-ready-source-origins.json').read_bytes())
    changes=[]
    for before in initial:
        after=next(row for row in current if row['path']==before['path'])
        changes.append({'path':before['path'],'source_ready_sha256':before['sha256'],
            'final_sha256':after['sha256'],'changed_since_source_ready':before['sha256']!=after['sha256']})
    dump('source-epoch-changes.json',changes)
    dump('findings.json',findings(True),True)
    readme=('Round184 CN optional same-presence native endpoint source integration.\n'
        'Owned C++4 files; native inputs/spans/relations/opcodes/phases/fullroutes0.\n'
        'Bind occurs only after actual initial held output and complete outward queue success, before gameplay remainder.\n'
        'Exact saved weak-transport Token capsule releases registry before actual presence cleanup on disconnect/failure.\n'
        'Optional pointer reaches Ready and actual Chat caller; original WorldOwner fields/rights remain actual authority.\n'
        'Complete actual freshbefore/source-ready/current/context source copies retained; no native/C++/codec/API/DB execution, builds or tests.\n')
    with (OUT/'README.txt').open('xb') as stream:stream.write(readme.encode())
    paths=sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT/'LIST.txt').open('xb') as stream:stream.write(('\n'.join(sorted(paths+['LIST.txt']))+'\n').encode())
    members=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
             for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json',{'round':184,'members':members,'member_count':len(members),
        'member_bytes':sum(row['bytes'] for row in members),'native_original_count':0,
        'current_source_count':len(current),'context_original_count':len(contexts),
        'all_actual_original_count':len(current+contexts),'immutable':True})
    print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'member_count':len(members),
        'files_including_seal':len(members)+1,'member_bytes':sum(row['bytes'] for row in members),
        'current_source_count':len(current),'context_original_count':len(contexts),
        'all_actual_original_count':len(current+contexts),'native_original_count':0,
        'tool_sha256':sha((SERVER/OWN).read_bytes())}))


if __name__=='__main__':
    if sys.argv[1:]==['--final']:
        final_capture()
    elif not sys.argv[1:]:
        source_ready()
    else:
        raise ValueError('Only source-ready or explicit --final capture')
