"""Round183 static actor-name publication source evidence, never native execution.

Retained native getter/startup interval; actual root source caller review is
separate from native inputs. All artifacts are immutable after final capture.
"""
from pathlib import Path
import csv
import io
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped

SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER/'artifacts/integration/packet-connections-20261006'
ROUND = ROOT/'native-common-actor-name-source-01'
OUT = ROUND/'agents/cn-actor-name-source'
EXE = SERVER.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_native_actor_name_source183.py'
SOURCE = ['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
    'src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedChatIdentitySource.h','src/game/SharedChatIdentitySource.cpp',
    'src/cn/auth/SharedCommonCharacterSummarySource.h','src/cn/auth/SharedCommonCharacterSummarySource.cpp',
    'src/cn/text/CnNativeActorText.h','src/cn/text/CnNativeActorText.cpp',
    'src/game/RecoveredCharacter.h','src/db/RecoveredCharacterRepository.h',
    'docs/research/cn-native-actor-text-projection-20261007.md',
    'tools/reconstruction/cn_native_actor_text_projection_delivery.py',
    'tools/reconstruction/cn_native_peer_name_binding182.py',
    'tools/reconstruction/cn_receiver_owner_frontier169.py']
ROOT_FINAL = ['src/game/SharedNativeActorNameSource.h','src/game/SharedNativeActorNameSource.cpp',
    'src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/game/SharedPublishedChatNameSource.h','src/game/SharedPublishedChatNameSource.cpp']
CONTEXT = ['src/cn/protocol/CnRemoteActor.h',
    'src/cn/world/SharedWorldPreparation.h','src/cn/world/SharedWorldPreparation.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/auth/SharedWorldSelection.h',
    'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
    'src/core/SharedWorldHostPlan.h','src/core/Application.cpp',
    'src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp',
    'src/game/SharedTaiwanNativeChatSource.h','src/game/SharedTaiwanNativeChatSource.cpp']
INPUTS = {'00405a30','00405a40','00405a60'}
SPANS = [('self_language_tag_zero','00405a30',0x405a30,0x405a33),
    ('startup_gate_getter','00405a40',0x405a40,0x405a46),
    ('startup_gate_writer_bounded','00405a60',0x405a60,0x405ac5)]


def dump(rel, value):
    p = OUT/rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=True)+'\n').encode())


def retain(rel, path, repository=False):
    raw = path.read_bytes()
    destination = OUT/rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
    return {'path':path.relative_to(SERVER).as_posix() if repository else str(path.resolve()),
            'copy':rel, 'bytes':len(raw), 'sha256':sha(raw)}


def main():
    if OUT.exists():
        raise RuntimeError('Preserve prior round183 capture')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('Pinned CN original changed')
    OUT.mkdir(parents=True)
    fresh = json.loads((ROUND/'before-manifest.json').read_bytes())
    by_path = {row['path']:row for row in fresh}
    before = []
    absent = []
    for n, rel in enumerate(SOURCE+ROOT_FINAL+CONTEXT+[OWN]):
        row = by_path.get(rel)
        if row is None:
            absent.append(rel)
            continue
        p = ROUND/row['snapshot']
        b = p.read_bytes()
        if len(b) != row['bytes'] or sha(b) != row['sha256']:
            raise ValueError('Freshbefore1306 original changed '+rel)
        saved = retain(f'before/b{n:02d}{Path(rel).suffix}',p)
        saved.update({'path':rel,'snapshot_original':str(p.resolve()),
                      'epoch':'freshbefore1306 actual complete original copy'})
        before.append(saved)
    dump('before-source-origins.json',before)
    dump('source-absence.json',{'absent_freshbefore1306':absent,'owned_cpp_edits':[],
        'excluded_current_pins':ROOT_FINAL+CONTEXT,
        'scope':'Historical before copies never substituted for current original files.'})
    context = [retain(f'context/c{n:02d}{Path(rel).suffix}',SERVER/rel,True)
               for n,rel in enumerate(CONTEXT)]
    dump('context-source-origins.json',context)
    root_final = [retain(f'root-final/f{n:02d}{Path(rel).suffix}',SERVER/rel,True)
                  for n,rel in enumerate(ROOT_FINAL)]
    dump('root-final-source-origins.json',root_final)
    dump('root-final-epoch.json',{'epoch':'After explicit parent183 BATCHFINAL and final Visibility refinement',
        'scope':'Actual full root C++ source context; not native inputs, not owned edits, not current pins.',
        'owned_cpp_edits':[]})
    intermediate = []
    first_final = json.loads((ROUND/'root-initial-final-source-review.json').read_bytes())['files']
    for n,row in enumerate(first_final):
        p = ROUND/row['copy']
        b = p.read_bytes()
        if len(b) != row['bytes'] or sha(b) != row['sha256']:
            raise ValueError('Root first-final epoch changed '+row['path'])
        copied = retain(f'intermediate/i{n:02d}{p.suffix}',p)
        copied.update({'path':row['path'],'snapshot_original':str(p.resolve()),
            'epoch':'Root initial-final before the final Visibility refinement, never current'})
        intermediate.append(copied)
    dump('intermediate-source-origins.json',intermediate)
    derived_paths = [ROOT/'cn-native-actor-text-projection-01/native-actor-text-contract.json',
        ROOT/'cn-chat-visible-identity-01/native-chat-identity-lineage.json',
        ROOT/'native-published-chat-identity-source-01/agents/cn-peer-name-binding-frontier/findings.json',
        ROOT/'native-published-chat-identity-source-01/agents/cn-peer-name-binding-frontier/seal.json',
        ROOT/'native-published-chat-identity-source-01/agents/cn-peer-name-binding-frontier/native/retained-sites.json',
        ROUND/'before-manifest.json',ROUND/'root-initial-final-source-review.json',
        ROUND/'root-final-source-review.json']
    dump('derived-inputs.json',[retain(f'derived/d{n:02d}{p.suffix}',p)
                              for n,p in enumerate(derived_paths)])
    metadata = list(csv.DictReader(io.StringIO((RECOVERY/'functions.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    selected = [row for row in metadata if row['address'] in INPUTS]
    if {row['address'] for row in selected} != INPUTS:
        raise ValueError('Selected original metadata missing')
    originals = [retain('inputs/pe.exe',EXE)]
    for n,name in enumerate(('functions.tsv','calls.tsv')):
        originals.append(retain(f'inputs/t{n}.tsv',RECOVERY/name))
    for row in selected:
        originals.append(retain('inputs/'+row['address']+'.c',RECOVERY/row['file']))
    dump('native-original-inputs.json',originals)
    dump('native/selected-original-metadata.json',selected)
    pe = pefile.PE(data=raw,fast_load=True)
    md = Cs(CS_ARCH_X86,CS_MODE_32)
    sites = []
    instructions = {}
    for name,owner,lo,hi in SPANS:
        off,b = mapped(pe,raw,lo,hi)
        decoded = []
        for instruction in md.disasm(b,lo):
            row = {'va':f'{instruction.address:08x}','bytes':bytes(instruction.bytes).hex(),
                'instruction':instruction.mnemonic+(' '+instruction.op_str if instruction.op_str else '')}
            decoded.append(row)
            instructions[row['va']] = row
        p = OUT/f'native/retained/{name}.bin'
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:
            stream.write(b)
        dump(f'native/retained/{name}.json',decoded)
        sites.append({'name':name,'owner':owner,'start_va':f'{lo:08x}',
            'end_va_exclusive':f'{hi:08x}','file_offset':off,'bytes':len(b),
            'raw_bytes':b.hex(),'sha256':sha(b),
            'decoded_bytes':sum(len(bytes.fromhex(row['bytes'])) for row in decoded),
            'complete_function':name!='startup_gate_writer_bounded',
            'retained_only':True,'new_native_increment':False})
    dump('native/retained-sites.json',sites)
    calls = list(csv.DictReader(io.StringIO((RECOVERY/'calls.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    dump('native/bounded-original-calls.json',[row for row in calls
        if any(lo<=int(row['callsite'],16)<hi for _,_,lo,hi in SPANS)])

    def fact(key, addresses, scope):
        return {'key':key,'scope':scope,'raw_sites':[instructions[address] for address in addresses],
                'retained_only':True,'new_native_increment':False}

    facts = [fact('pinned_self_language_tag_is_zero',['00405a30','00405a32'],
        'Complete pinned getter returns zero, with no page operand. Tag0 does not select936 or950 or create common identity.'),
        fact('gate_getter_is_not_a_codepage',['00405a40','00405a45'],
        'Complete pinned getter reads DWORD008AEEB8, not a recovered peer-name page or common-name source.'),
        fact('bounded_startup_boolean_gate_writer',['00405a8b','00405a96','00405a9e','00405aa0',
            '00405aa9','00405ab2','00405ab9','00405ac0'],
        'Startup interval writes Boolean008AEEB8 after actual result and struct-field checks. Recovery C labels its structure OSVERSIONINFO and call GetVersionExA; raw indirect target007EB5B4 was not independently matched to a declared PE import in this bounded research. Neither raw tag nor this Boolean proves fixed raw-name page. Full original1478B function/C retained as input but only101B gate interval used; callees, renderer/formatter/capacity and startup remainder are excluded.')]
    dump('native/retained-facts.json',facts)
    source_facts = [
        {'key':'actual_reservation_to_entered_publication',
         'sources':['src/cn/auth/SharedLoginComposition.cpp','src/cn/world/SharedWorldPreparation.cpp',
            'src/cn/world/SharedWorldGameplay.cpp','src/cn/world/SharedWorldReady.cpp'],
         'scope':'Explicit common_world_preparation.reserve -> prepare reserve_(Choice,stored position) -> actual Reservation::gameplay(connection,full64 lease,scene) -> gameplay compose -> ready consume1C entered_(lease,exact1C,finish). Complete incoming aggregates/slices and outward native models come from that actual issuer. No concrete raw profile/scene producer is proved in this examined source set; not a global absence assertion.'},
        {'key':'root_actual_common_original_name_publisher',
         'sources':['src/game/SharedNativeActorNameSource.h','src/game/SharedNativeActorNameSource.cpp',
            'src/cn/world/SharedActorVisibility.cpp','src/cn/world/SharedWorldReady.cpp'],
         'scope':'Final root explicit common_name_source selects exact same-presence owner. Active source full64 ready root/stored strict original is projected into actual recipient raw-state page936/950. CN tag0 only; source low12 native handle stays separate from uint64 common character. Actual full81B model, strong receiver and raw profile Current/revision required; recipient may be prepared. Show/initial/outward/current callers use project/current. Initial aggregate slices match complete supplied original81B before any projected record replacement.'},
        {'key':'first_field_owned_policy_and_preserved_native_operand',
         'sources':['src/cn/protocol/CnRemoteActor.h','src/game/SharedNativeActorNameSource.cpp'],
         'scope':'Only logical offsets29..44 (0x1D..0x2C), complete first16B name field, are changed. Root fills the entire field with zero and copies strict same original encoding; post-NUL bytes INSIDE this field are normalized, not preserved native padding evidence. All bytes outside firstfield, including native actor/header/tag, second/third fields and tail, remain complete supplied native original. No synthesized actor/flags/defaults or new wire layout.'},
        {'key':'old_input_native_page_conflation_and_actual_fix',
         'sources':['src/game/SharedPublishedChatNameSource.h','src/game/SharedPublishedChatNameSource.cpp'],
         'scope':'Freshbefore1306 incorrectly required preceding native-name page equal C2S lookup page and raw bytes equal raw_target. Final root Witness.codepage remains actual C2S input; native_name_codepage returns actual observed preceding6F page. observe separately strict-encodes the identical common original into input page for raw_target and into actual rawState native page for native_name. actual Current/requery/current comparisons use native page. No page/tag/alias/display-script change or synthetic source; tag1 adapted namespace remains OPEN.'},
        {'key':'final_publication_current_refinement',
         'sources':['src/cn/world/SharedActorVisibility.cpp'],
         'scope':'Final root show/outward copy supplied leases before actual observers; current uses captured complete entry/strong connection, rechecks exact registry endpoint and common_name_current after final repository source read. Initial-final full source and latest refinement are preserved as separate epochs, not silently relabeled current.'}]
    dump('source-name-publication-facts.json',source_facts)
    gaps = [
        {'gap':'Actual Reservation/Entered issuer and CN raw-name profile source',
         'next_actual_root':'Supply complete actual native81B and aggregate slices at same-account reservation/entered caller, with explicit MainlandRawNameState revision, actual wire_codepage and real Current. Tag0/405A30/getter405A40 are not page witnesses. No default fixed936 profile or guessed native appearance.'},
        {'gap':'Adapted tag1 native peer namespace and official gameplay rights',
         'next_actual_root':'Actual receiver environment and original native transformed-name/current source; raw common-original publisher intentionally covers only qualified CNtag0. Native5C header/audience/party/guild/offline rights remain actual WorldOwner source obligations.'},
        {'gap':'Main/Application whole native hosting and complete routes',
         'next_actual_root':'Actual native issuer/scene/resource/admission source, not this name projection or comparison. No new full route, phase, opcode or completed game denominator established.'},
        {'gap':'Unknown receiver helpers0047DE70/004812B0',
         'next_actual_root':'An actual original receive transfer must qualify caller/slot/phase; name-source evidence leaves all unknown.'}]
    dump('gaps.json',gaps)
    current = [retain(f'current/s{n:02d}{Path(rel).suffix}',SERVER/rel,True)
               for n,rel in enumerate(SOURCE+[OWN])]
    dump('current-source-origins.json',current)
    stable_absolute = [{**row,'path':str((SERVER/row['path']).resolve())} for row in current]
    # Actual used C++ root/context full originals are separate from native input.
    context_absolute = [{**row,'path':str((SERVER/row['path']).resolve())} for row in context+root_final]
    dump('context-original-inputs.json',context_absolute)
    dump('original-inputs.json',originals+stable_absolute+context_absolute)
    findings = {'round':183,'client_sha256':PIN,'new_bounded_native_spans':0,
        'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':len(sites),'retained_bounded_native_bytes':sum(row['bytes'] for row in sites),
        'retained_native_facts':facts,'source_name_publication_facts':source_facts,
        'native_original_inputs':len(originals),'current_stable_sources':len(current),
        'context_original_inputs':len(context_absolute),'all_actual_original_inputs':len(originals+stable_absolute+context_absolute),
        'cpp_edits':[],'root_cpp_context_only':ROOT_FINAL,
        'new_source_bindings':0,'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':address,'phase':None,'slot':None,'producer':None}
                              for address in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,'gaps':gaps,
        'scope':'Retained native getters and concrete actual root source publication/page-domain repair review. Agent owns only static tool/evidence; actual raw-state/scene supplier and Main/full route remain OPEN.',
        'builds_tests_runtime_codec_formatter_render_deploy':False,'BATCHFINAL_received':True}
    dump('findings.json',findings)
    readme = ('Round183 static CN actor-name source qualification.\n'
        'Native new spans/bytes/relations:0; retained3 spans110B. Agent C++ edits:0.\n'
        'Actual root final name publisher and input/native page separation are source context, not native inputs or complete routes.\n'
        'Native full original PE+2TSV+3C, stable current actual sources, complete root/context originals, freshbefore1306 and intermediate epochs are separately retained.\n'
        'Only first logical16B is normalized/projected; all outside that field remains original.\n'
        'Raw profile/scene issuer, adapted names, Main hosting/full routes remain OPEN. No execution/tests/codec/native/API/DB/formatter/capacity tracing. Stop after183.\n')
    with (OUT/'README.txt').open('xb') as stream:
        stream.write(readme.encode())
    files = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT/'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(sorted(files+['LIST.txt']))+'\n').encode())
    members = [{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
               for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json',{'round':183,'scope':'Complete owned artifact after BATCHFINAL183; immutable',
        'members':members,'member_count':len(members),'member_bytes':sum(row['bytes'] for row in members),
        'native_original_count':len(originals),'current_source_count':len(current),
        'context_original_count':len(context_absolute),'all_actual_original_count':len(originals+stable_absolute+context_absolute),
        'immutable':True})
    print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),
        'files_including_seal':len(members)+1,'member_bytes':sum(row['bytes'] for row in members),
        'native_original_count':len(originals),'current_source_count':len(current),
        'context_original_count':len(context_absolute),'all_actual_original_count':len(originals+stable_absolute+context_absolute),
        'before_count':len(before),'intermediate_count':len(intermediate),'derived_count':len(derived_paths),
        'tool_sha256':sha((SERVER/OWN).read_bytes())}))


if __name__ == '__main__':
    main()
