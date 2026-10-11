"""208 bounded Taiwan frontier: file/source capture only, no game execution."""
from pathlib import Path
import hashlib, json

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/tw-first-route-closure-01/agents/tw-native-frontier'
def digest(b): return hashlib.sha256(b).hexdigest()
def write(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def capture(paths,folder):
    rows=[]
    for i,rel in enumerate(paths):
        p=ROOT/rel;b=p.read_bytes();copy=f'{folder}/{i:02d}-{p.name}'
        q=OUT/copy;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
        rows.append(dict(path=str(p.resolve()),copy=copy,bytes=len(b),sha256=digest(b)))
    return rows

def main():
    if (OUT/'seal.json').exists(): raise RuntimeError('Sealed evidence is immutable')
    OUT.mkdir(parents=True,exist_ok=True)
    guides=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
    own='tools/reconstruction/tw_native_frontier208.py'
    stable=['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
        'src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp',
        'src/game/SharedTaiwanWorldEntrySource.h','src/game/SharedTaiwanWorldEntered.h',
        'src/game/SharedTaiwanNativeMovementScene.h','src/game/TaiwanNativeSceneResourceOwner.h',
        'src/game/SharedTaiwanNativeMovementHost.h','src/scripting/TaiwanMovementRules.h',
        'src/scripting/TaiwanMovementRules.cpp','scripts/tw/native_movement.lua',
        'src/protocol/RecoveredNativeMovement.h','src/db/RecoveredCharacterRepository.h',
        'src/db/SqliteRecoveredCharacterRepository.cpp']
    current=capture(guides+[own],'current')
    originals=current+capture(stable,'originals')
    write('current-source-origins.json',current)
    write('original-inputs.json',originals)
    context_paths=['src/Main.cpp','src/core/Application.h','src/core/Application.cpp',
        'src/core/SharedWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.h',
        'src/core/SharedTaiwanNativeWorldHostPlan.cpp','src/net/Session.h',
        'src/protocol/RecoveredWorldRecords.h','docs/PACKET_CONNECTION_GOAL_20261006.md',
        'artifacts/integration/packet-connections-20261006/packet-progress-latest.json']
    context=capture(context_paths,'read-epoch-context')
    write('context-origins.json',context)
    report=json.loads((OUT/context[-1]['copy']).read_bytes())
    write('historical-report-scope.json',dict(round=report['round'],counts=report['counts'],
        pending_source_groups=report['pending_source_groups'],unconnected_gameplay=report['unconnected_gameplay'],
        limitation='Historical 207 accounting, not current route completion proof; retained verbatim.'))
    prior=[]
    for folder in ['tw-native-host-composition-source-01/agents/tw-authority-frontier',
                   'tw-native-movement-scene-source-01/agents/tw-live-scene']:
        prefix='artifacts/integration/packet-connections-20261006/'+folder+'/'
        prior+=capture([prefix+n for n in ['findings.json','gaps.json','seal.json']],
                       'retained/'+folder.split('/')[0])
    write('retained-original-origins.json',prior)
    source_paths=list(dict.fromkeys(stable+context_paths[:8]+[p for group in report['pending_source_groups']
        for p in group.get('source_paths',[]) if p.startswith('src/') or p.startswith('scripts/')]))
    sites=[]
    needles=['run_server(config','world_plan=nullptr','make_taiwan_world_entry','make_taiwan_entered_async',
        'make_taiwan_movement','install_records','struct Sources','NativeSource','authorize(',
        'commit_owned_step','commit_position','rules_.prepare','read_ack','native_cell_qualifies',
        'spectator6e','spectator_close','companion_controls6b','e4_controls']
    for rel in source_paths:
        p=ROOT/rel
        if not p.exists(): continue
        for line,text in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
            matched=[n for n in needles if n in text]
            if matched: sites.append(dict(path=str(p.resolve()),line=line,text=text,matched=matched))
    write('source-sites.json',sites)
    branch_paths={}
    for opcode in report['unconnected_gameplay']:
        paths=[p for g in report['pending_source_groups'] if opcode in g.get('c2s',[])
               for p in g.get('source_paths',[]) if p.startswith('src/') or p.startswith('scripts/')]
        if opcode=='D6': paths=['src/core/Application.cpp','src/protocol/RecoveredWorldRecords.h']
        if opcode in ['A3','CB','6E']:
            paths+=['src/game/SharedTaiwanNativeSpectatorSource.h',
                    'src/core/SharedTaiwanNativeWorldHostPlan.cpp','src/core/Application.cpp']
        branch_paths[opcode]=[str((ROOT/p).resolve()) for p in dict.fromkeys(paths)]
    write('findings.json',dict(round=208,scope='TW upstream source review only',
        priority='Latest human TW-first resume supersedes historical stop207; CN retained without new CN work.',
        recommendation=dict(source_paths=[str((ROOT/p).resolve()) for p in context_paths[:6]+stable],
            connection='Supply actual strong-lifetime Taiwan entry/entered/resource/authority SourceFactory to SharedTaiwanNativeWorldHostPlan::create; call existing selected-world-plan run_server overload from Main.',
            existing_positive_chain='Actual raw2E -> Lua adjacent direction/native cell predicate -> mandatory Scene Authority full5D/current ticket -> complete common position/revision CAS -> actual scene publication and ordered peers/reply.',
            missing_handler='Main currently calls default run_server(config,seconds), whose run_server_impl world_plan is nullptr. Conditional native plan factories exist but real native source supplier is not supplied by Main.',
            missing_authority='Full original5D value/admission, timing/pending/reset/transfer/battle/collision/dynamic-object and one-use publication ticket remain actual Authority responsibility; client presentation does not supply official server rules.',
            missing_material='Qualified full entry frame and same-root/position initial native peers, actual overlay/map/cells/window-object resource lifecycle and generation issuer.',
            storage='Existing SharedWorldPresence commit_owned_step calls complete common repository position/revision CAS; no new storage algorithm proposed.',
            rules='native_movement.lua supplies only direction and nonzero-cell necessary predicate; cannot authorize entire map/path.',
            native_consumer='Retained TW logical5D stores actual byte and pops oldest pending point without echo comparison; full5D cannot be manufactured from request sequence.'),
        unconnected_branch_source_paths=branch_paths,
        branch_gaps=report['unconnected_gameplay'],
        current_reconciliation=[
            'Historical report6E wording has not been rewritten: typed conditional spectator/close sources and plan/Application routing now exist; actual room/battle/target/window rights, ordered native reply suppliers and Main remain OPEN.',
            'A3/CB optional CloseOwner preserves opaque saved-this highBYTE; actual close/window issuer and authority are not default6E permission.',
            'Reviewed42/parser65, 13 unconnected, reply43 lower bound, controls10 are separate source inventories, not complete directional/phase/state/variant denominator.',
            'Root208 stack99 scalar inventory write domain is separate bounded integration and does not close Main/native material or claim Taiwan100%.'],
        native_evidence='Only prior immutable TW findings/gaps/seals reused. No PE read/copy/disassembly or new native byte coverage.',
        source_read_scope='Full stable movement/Presence/Lua/interfaces read; Main full read; Application and plan selective concrete source branches. Full source copies preserve original context and do not claim full-file review.',
        new_native_spans=0,new_native_bytes=0,new_opcode=0,new_complete_routes=0,
        whole_game_denominator=None,whole_game_percentage=None,
        no_execution=True,src_modified=False,stop='Terminal bounded208 agent task; parent may continue authorized TW work.'))
    write('native-input-references.json',dict(new_inputs=[],new_raw_bytes=0,
        retained_evidence=prior,original_TW_image_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763',
        qualification='Image hash retained from original176 findings; not re-read or requalified in208.'))
    rows=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p!=OUT/'seal.json' and p!=OUT/'LIST.json':
            b=p.read_bytes();rows.append(dict(path=p.relative_to(OUT).as_posix(),bytes=len(b),sha256=digest(b)))
    write('LIST.json',rows)
    b=(OUT/'LIST.json').read_bytes()
    rows.append(dict(path='LIST.json',bytes=len(b),sha256=digest(b)))
    rows=sorted(rows,key=lambda r:r['path'])
    # Nested historical seal copies are members; exclude only this top-level seal.
    write('seal.json',dict(members=rows,count=len(rows),bytes=sum(r['bytes'] for r in rows),
                          method='Full nested inventory, excludes only top-level seal.json'))
    print(json.dumps(dict(members=len(rows),files=len(rows)+1,current=len(current),originals=len(originals),
        context=len(context),retained=len(prior),seal_sha256=digest((OUT/'seal.json').read_bytes()),
        tool_sha256=digest(Path(__file__).read_bytes())),indent=2))

if __name__=='__main__': main()
