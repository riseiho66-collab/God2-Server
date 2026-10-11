"""Static actual CN host/preparation/gameplay transport source provenance.

File/source capture only. No native PE, codec, runtime, builds, tests or DB.
"""
from pathlib import Path
import hashlib
import json
import sys

SERVER=Path(__file__).resolve().parents[2]
ROUND=SERVER/'artifacts/integration/packet-connections-20261006/native-world-transport-host-composition-01'
OUT=ROUND/'agents/cn-host-transports'
OWN='tools/reconstruction/cn_native_transport_host185.py'
MODIFIED=['src/cn/world/SharedWorldPreparation.h','src/cn/world/SharedWorldPreparation.cpp',
    'src/cn/auth/SharedLoginComposition.cpp']
SOURCE=MODIFIED+['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
    'src/cn/auth/SharedLoginComposition.h',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp']
CONTEXT=['src/game/SharedWorldHost.h','src/game/SharedWorldHost.cpp']


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
    return {'round':185,'scope':'Actual selected host transport source -> CN preparation -> real gameplay/Ready/Chat composition. Source connection, not native recovery or complete routes.',
        'source_files_modified':MODIFIED,'owned_cpp_edits':3,'native_original_inputs':0,
        'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':0,'retained_bounded_native_bytes':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':address,'phase':None,'slot':None,'producer':None}
            for address in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'actual_source_connections':[
            {'key':'host_same_source_concrete_preparation','sources':['src/cn/auth/SharedLoginComposition.cpp','src/cn/world/SharedWorldPreparation.cpp'],
             'scope':'compose_native_login captures actual Context.common_world->transports once, requires nonnull same-presence when actual host selected, and passes exact pointer to concrete common_preparation create. Assets/reservation/budgets, credentials, account directory and issued native callbacks stay mandatory.'},
            {'key':'preparation_source_identity','sources':['src/cn/world/SharedWorldPreparation.h','src/cn/world/SharedWorldPreparation.cpp'],
             'scope':'create/constructor optional final registry source is retained unchanged, rejects different presence. owns_transport_source compares exact pointer and real same-presence; null legacy matches null only. No new registry constructed by CN preparation.'},
            {'key':'actual_reservation_gameplay_source_injection','sources':['src/cn/world/SharedWorldPreparation.cpp','src/cn/world/SharedWorldGameplay.cpp'],
             'scope':'Actual Reservation.gameplay provides qualified Sources for existing lease/scene. Original release_world is first retained in ReleaseOnce. When host source selected, different supplied world_transports rejects without replacement; absent is filled with exact retained host source, same is preserved. Actual normal movement adoption/transfer qualification, full status02/begin2A and source Current remain unchanged before compose. No ID/name transport lookup or guessed defaults.'},
            {'key':'account_naming_alternative_source_qualification','sources':['src/cn/auth/SharedLoginComposition.cpp'],
             'scope':'Actual naming branch retains explicit bind_naming behavior and original conflicts; supplied naming_preparation must match actual repository/catalog, host presence/visibility and exact captured host transport source. Missing/different transport source rejects, not silently recreated.'},
            {'key':'world_alternative_source_qualification','sources':['src/cn/auth/SharedLoginComposition.cpp'],
             'scope':'World supplier either leaves preparation empty for selected concrete common_preparation or supplies actual alternative; selected host requires actual source/controller plus exact presence/visibility and transport pointer. Account/native offer/delete/naming rights and original selected callback remain independent mandatory obligations.'},
            {'key':'preparation_failure_cleanup_boundary','sources':['src/cn/world/SharedWorldPreparation.cpp','src/cn/world/SharedWorldReady.cpp','src/cn/world/SharedWorldGameplay.cpp'],
             'scope':'Post-compose preparation failure has not completed initial1C/held incoming/outward fanout and has no bound native endpoint token. Existing preparation generation-lease/release-once/close rollback is retained. Actual Ready disconnect capsule owns its saved registry token once later bind is permitted; no new release by session/character/alias is invented here. Native queue ordering and actual client acceptance are not newly proven.'}],
        'legacy_null_source':'Without Context.common_world, no host transport registry is constructed or injected. Original explicit supplier Sources and null create default remain as provided.',
        'original_epochs':'Full actual pre-edit originals match freshbefore1320; complete source-ready copies captured before any final-source edits, with mutable host context separate.',
        'gaps':['Actual Reservation/Entered native models/scene/resources/rules still require their real suppliers.',
            'Actual Native WorldOwner headers/body/audience/permissions remain unchanged source obligations.',
            'Main/Application hosting/native acceptance/whole-game routes are not established by this source composition.'],
        'builds_tests_runtime_native_api_codec_db_deploy':False,'BATCHFINAL_received':final}


def source_ready():
    if not (OUT/'before-source-origins.json').exists() or (OUT/'findings.json').exists():
        raise RuntimeError('Actual pre-edit copies required; preserve previous capture')
    before=json.loads((OUT/'before-source-origins.json').read_bytes())
    fresh={row['path']:row for row in json.loads((ROUND/'before-manifest.json').read_bytes())}
    for n,rel in enumerate(SOURCE[3:]+CONTEXT):
        row=fresh[rel];p=ROUND/row['snapshot'];raw=p.read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:
            raise ValueError('Freshbefore1320 source changed '+rel)
        saved=retain(f'before/s{n:02d}{p.suffix}',p,False)
        saved.update({'path':rel,'snapshot_original':str(p.resolve()),'epoch':'Full original freshbefore1320 actual source'})
        before.append(saved)
    dump('before-source-origins.json',before,True)
    dump('source-ready-source-origins.json',[retain(f'source-ready/i{n:02d}{Path(rel).suffix}',SERVER/rel)
        for n,rel in enumerate(MODIFIED+[OWN])])
    dump('context-initial-source-origins.json',[retain(f'context-initial/k{n:02d}{Path(rel).suffix}',SERVER/rel)
        for n,rel in enumerate(CONTEXT)])
    dump('native-original-inputs.json',[])
    dump('source-absence.json',{'absent_freshbefore1320':[OWN],
        'excluded_current_pins':CONTEXT+['src/core/Application.cpp','src/core/SharedTaiwanNativeWorldHostPlan.cpp'],
        'scope':'Only actual source originals; mutable host/application/TWplan/books/ledger/catalog/reports never current pinned.'})
    dump('derived-inputs.json',[retain('derived/freshbefore1320.json',ROUND/'before-manifest.json',False)])
    dump('findings.json',findings(False))
    print(json.dumps({'state':'source-ready','cpp_edits':3,'native_original_inputs':0,
        'tool_sha256':sha((SERVER/OWN).read_bytes()),'awaiting_BATCHFINAL':True}))


def final_capture():
    if (OUT/'seal.json').exists() or not (OUT/'findings.json').exists():
        raise RuntimeError('Preserve seal; require source-ready capture')
    with (OUT/'findings-source-ready.json').open('xb') as stream:stream.write((OUT/'findings.json').read_bytes())
    current=[retain(f'current/c{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(SOURCE+[OWN])]
    context=[retain(f'context-final/k{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(CONTEXT)]
    dump('current-source-origins.json',current)
    dump('context-final-source-origins.json',context)
    dump('original-inputs.json',[{**row,'path':str((SERVER/row['path']).resolve())} for row in current+context])
    initial=json.loads((OUT/'source-ready-source-origins.json').read_bytes())
    dump('source-epoch-changes.json',[{'path':row['path'],'source_ready_sha256':row['sha256'],
        'final_sha256':next(item['sha256'] for item in current if item['path']==row['path']),
        'changed_since_source_ready':row['sha256']!=next(item['sha256'] for item in current if item['path']==row['path'])}
        for row in initial])
    dump('findings.json',findings(True),True)
    with (OUT/'README.txt').open('xb') as stream:
        stream.write(('Round185 CN actual host/preparation transport source composition.\n'
            'Owned C++3; native inputs/spans/relations/opcodes/phases/fullroutes0.\n'
            'Exact actual host source reaches concrete preparation and real Reservation gameplay Sources; foreign source rejects, absent uses retained same host.\n'
            'Actual naming/world alternative preparation checks exact source. Legacy null creates no source.\n'
            'Before/source-ready/current/context full originals remain separate epochs; no build/test/runtime/native/codec/API/DB execution.\n').encode())
    paths=sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT/'LIST.txt').open('xb') as stream:stream.write(('\n'.join(sorted(paths+['LIST.txt']))+'\n').encode())
    members=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
        for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json',{'round':185,'members':members,'member_count':len(members),
        'member_bytes':sum(row['bytes'] for row in members),'native_original_count':0,
        'current_source_count':len(current),'context_original_count':len(context),
        'all_actual_original_count':len(current+context),'immutable':True})
    print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),
        'files_including_seal':len(members)+1,'member_bytes':sum(row['bytes'] for row in members),
        'current_source_count':len(current),'context_original_count':len(context),
        'all_actual_original_count':len(current+context),'native_original_count':0,
        'tool_sha256':sha((SERVER/OWN).read_bytes())}))


if __name__=='__main__':
    if sys.argv[1:]==['--final']:
        final_capture()
    elif not sys.argv[1:]:
        source_ready()
    else:
        raise ValueError('Only source-ready or explicit --final capture')
