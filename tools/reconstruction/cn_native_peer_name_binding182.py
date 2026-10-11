"""Round182 static CN published peer name/common identity binding frontier.

Retained native field evidence only; no codec/native/API/renderer execution.
Source actions concern actual map lifetime and recipient/current qualifications.
"""
from pathlib import Path
import csv
import io
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped

SERVER=Path(__file__).resolve().parents[2]
ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
OUT=ROOT/'native-published-chat-identity-source-01/agents/cn-peer-name-binding-frontier'
EXE=SERVER.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN='tools/reconstruction/cn_native_peer_name_binding182.py'
SOURCE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
    'src/cn/protocol/CnRemoteActor.h','src/cn/text/CnNativeActorText.h','src/cn/text/CnNativeActorText.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedChatIdentitySource.h','src/game/SharedChatIdentitySource.cpp',
    'src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp',
    'src/game/RecoveredCharacter.h','src/db/RecoveredCharacterRepository.h','src/cn/protocol/CnChat.h',
    'src/cn/auth/SharedCommonCharacterSummarySource.h','src/cn/auth/SharedCommonCharacterSummarySource.cpp',
    'docs/research/cn-chat-visible-identity-20261007.md',
    'tools/reconstruction/cn_receiver_owner_frontier169.py',
    'tools/reconstruction/cn_native_whisper_identity181.py',
    'tools/reconstruction/cn_chat_visible_identity_delivery.py']
CONTEXT=['src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp',
    'src/game/SharedTaiwanNativeChatSource.h','src/game/SharedTaiwanNativeChatSource.cpp']
INPUTS={'00532410','0052f5a0','00531ea0','0048fcc0'}
SPANS=[('free_actor_entry_anchor','00532410',0x532410,0x532445),
       ('low12_and_first_name_copy','00532410',0x5324f3,0x53251d),
       ('peer_DWORD_lookup_and_first_name','00531ea0',0x531ed0,0x531f17)]


def dump(rel,obj):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write((json.dumps(obj,indent=2,ensure_ascii=True)+'\n').encode())


def retain(rel,p,repository=False):
    b=p.read_bytes();q=OUT/rel;q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as f:f.write(b)
    return {'path':p.relative_to(SERVER).as_posix() if repository else str(p.resolve()),
            'copy':rel,'bytes':len(b),'sha256':sha(b)}


def main():
    if OUT.exists():raise RuntimeError('Preserve previous round182 evidence')
    raw=EXE.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN original changed')
    OUT.mkdir(parents=True)
    dump('before-source-origins.json',[retain(f'before/b{n:02d}{Path(r).suffix}',SERVER/r,True)
        for n,r in enumerate(SOURCE)])
    context=[retain(f'context/k{n:02d}{Path(r).suffix}',SERVER/r,True) for n,r in enumerate(CONTEXT)]
    dump('context-source-origins.json',context)
    dump('context-epoch.json',{'scope':'Actual-read epoch during concurrent root182 edits, not freshbefore1300 and not final current pins.',
        'known_context_paths':CONTEXT,'new_published_name_paths':'Not present in initial bounded file inventory; parent owns these new sources, never current-pinned here.'})
    dump('source-absence.json',{'new_tool_absent_freshbefore1300':OWN,'cpp_edits':[],
        'excluded_current_pins':CONTEXT,'also_exclude':'All root new published-name sources/catalog/books/reports/artifacts',
        'no_source_intermediate':True})
    dump('intermediate-source-origins.json',[])
    derived=[ROOT/'cn-chat-visible-identity-01/native-chat-identity-lineage.json',
        ROOT/'shared-actor-visibility-01/native/cn/world-6f-branch.c.txt',
        ROOT/'shared-native-chat-identity-source-01/agents/cn-whisper-identity-frontier/findings.json',
        ROOT/'shared-native-chat-identity-source-01/agents/cn-whisper-identity-frontier/seal.json',
        ROOT/'native-published-chat-identity-source-01/before-manifest.json']
    dump('derived-inputs.json',[retain(f'derived/d{n:02d}{p.suffix}',p) for n,p in enumerate(derived)])
    metadata=list(csv.DictReader(io.StringIO((RECOVERY/'functions.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    selected=[r for r in metadata if r['address'] in INPUTS]
    if {r['address'] for r in selected}!=INPUTS:raise ValueError('Actual C metadata missing')
    originals=[retain('inputs/pe.exe',EXE)]
    for n,name in enumerate(('functions.tsv','calls.tsv')):
        originals.append(retain(f'inputs/t{n}.tsv',RECOVERY/name))
    for row in selected:originals.append(retain('inputs/'+row['address']+'.c',RECOVERY/row['file']))
    dump('native-original-inputs.json',originals);dump('native/selected-original-metadata.json',selected)
    pe=pefile.PE(data=raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
    sites=[];instructions={}
    for name,owner,lo,hi in SPANS:
        off,b=mapped(pe,raw,lo,hi);decoded=[]
        for i in md.disasm(b,lo):
            row={'va':f'{i.address:08x}','bytes':bytes(i.bytes).hex(),
                 'instruction':i.mnemonic+(' '+i.op_str if i.op_str else '')}
            decoded.append(row);instructions[row['va']]=row
        q=OUT/f'native/retained/{name}.bin';q.parent.mkdir(parents=True,exist_ok=True)
        with q.open('xb') as f:f.write(b)
        dump(f'native/retained/{name}.json',decoded)
        sites.append({'name':name,'owner':owner,'start_va':f'{lo:08x}','end_va_exclusive':f'{hi:08x}',
            'file_offset':off,'bytes':len(b),'raw_bytes':b.hex(),'sha256':sha(b),
            'decoded_bytes':sum(len(bytes.fromhex(r['bytes'])) for r in decoded),
            'retained_only':True,'new_native_increment':False})
    dump('native/retained-sites.json',sites)
    calls=list(csv.DictReader(io.StringIO((RECOVERY/'calls.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    dump('native/bounded-original-calls.json',[r for r in calls if any(
        lo<=int(r['callsite'],16)<hi for _,_,lo,hi in SPANS)])

    def fact(key,addresses,scope):
        return {'key':key,'scope':scope,'raw_sites':[instructions[a] for a in addresses],
                'retained_only':True,'new_native_increment':False}
    facts=[fact('actor_pool_entry_base',
        ['0053241c','00532422','00532427','0053242d','00532436','00532439'],
        'Constructor root ECX points at pool: free identity DWORD at ECX+0x18, stride0x268,128 entries. ESI is selected entry+0x18. Native allocation evidence only, not a server/common-ID allocator or observed client acceptance.'),
      fact('low12_DWORD_and_first_raw_text',
        ['005324f3','005324f6','005324f8','005324fb','00532502','00532508',
         '00532510','00532512','00532515','00532519','0053251b'],
        'Body DWORD0 low12 is written as DWORD at entry+0x18. First body string+0x1C/logical+0x1D copies BYTE-through-NUL into entry+0x1C. Existing wrapper WORLD6F body origin+1 retained separately. No common uint64ID, raw-name alias, codepage or native server producer proof follows from these instructions.'),
      fact('peer_full_DWORD_and_native_first_name',
        ['00531ed3','00531ed9','00531edb','00531ee1','00531ee6','00531f07',
         '00531f10','00531f13','00531f15'],
        'Peer callback compares supplied fullDWORD actor with entry+0x18 across128 stride0x268 entries and addresses first stored name at+0x1C. Not self identity/common root equivalence. Downstream board/formatter/bubble/renderer/capacity code is explicitly outside this bounded decode.')]
    dump('native/retained-peer-name-facts.json',facts)
    source_facts=[
      {'key':'raw_complete6F_name_identity_operand','sources':['src/cn/protocol/CnRemoteActor.h'],
       'scope':'Full81B original6F mandatory; identity low12 and bodybit25 tag independent of common64ID. wire_name only first logical+0x1D within16B terminated region; server parse admission is not official rejection/capacity policy.'},
      {'key':'tag1_receiver_prediction_not_common_original','sources':['src/cn/text/CnNativeActorText.h','src/cn/text/CnNativeActorText.cpp'],
       'scope':'Projection source/current compares identity/tag1/all48 raw text bytes, ignores independent movement, and requires nonzero revision/gates plus actual qualified_receiver_environment_current callback. Predicted expected[0] is receiver-transformed native string, separate from raw first wire-name original and common stored identity. API source read only, never executed or recursively traced.'},
      {'key':'ready_common_full_identity','sources':['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/game/SharedChatIdentitySource.h','src/game/SharedChatIdentitySource.cpp','src/game/RecoveredCharacter.h'],
       'scope':'Readiness domain is actual active lease/full same-account common root/actual current position; uint64 IDs/session/account/generation remain fullwidth. Name lookup holds immutable complete population and strict original names; native actor handle is separate. No visible-model raw name joins can supply commonID.'},
      {'key':'summary_prompt_mode_not_peer_binding','sources':['src/cn/auth/SharedCommonCharacterSummarySource.h','src/cn/auth/SharedCommonCharacterSummarySource.cpp','src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp'],
       'scope':'NativePromptMarker/CommonIdentity are explicit account07 source modes, not a world6F actor/common binding. Common14-byte name and strict original encoding remains mandatory; a marker or low12/native name cannot bypass ready-root/current authority.'},
    ]
    dump('source-name-binding-qualification.json',source_facts)
    visibility=next(r for r in context if r['path']=='src/cn/world/SharedActorVisibility.cpp')
    actions=[
      {'key':'copy_actual_entry_before_external_current','actual_source':visibility,
       'function':'SharedActorVisibility::current / mainland_chat_actor','scope':'Actual-read epoch context, not final root182 implementation claim.',
       'action':'Do not retain map iterator/reference across presence repository or native projection Current callbacks. Capture full Entry/Binding/position/Native by value, retain strong actual recipient connection, qualify before and after every external observer against same private incarnation and current source/recipient lease, admission and saved position. Replacement/hide/reset/release must invalidate old observation.'},
      {'key':'separate_raw_original_and_receiver_expected','actual_source':visibility,
       'function':'SharedActorVisibility::mainland_chat_actor / CnNativeActorText::Projection::current',
       'action':'Tag0 yields raw first wire name; tag1 yields supplied successful receiver prediction expected[0]. Keep actual raw first6F operand and receiver current/revision proof. Native expected bytes cannot be decoded as universal936 identity or replace common original. Do not invent tag1 fallback or recreate predictions with a display converter.'},
      {'key':'explicit_common_to_native_published_name_issuer','sources':['src/game/SharedChatIdentitySource.h','src/cn/protocol/CnRemoteActor.h','src/text/OwnedCharacterNameText.h'],
       'action':'Root new actual published-name owner must bind fullready common root/originalUTF8 to actual supplied complete native6F/first raw name through explicit source encoding and authority. Retain actual source/recipient generations, full native record/current publication, observer scope and strong transport. Never infer relation merely from equal native actor low12, prompt marker or name lookup.'},
      {'key':'native_header_and_rights_stay_actual_owner','sources':['src/cn/protocol/CnChat.h'],
       'action':'Existing native5C full actorDWORD is checked against the actual native published peer binding, not narrowed commonID. New name readiness proof grants no sender/recipient audience/membership/mute/rate/offline reply/native header policy; actual WorldOwner still supplies these.'},
    ]
    gaps=[
      {'gap':'Complete native published name/common identity issuer and lifetime qualification',
       'next_actual_root':'Root182 new published-name source plus actual CN/TW chat ingress/caller and fullready roots; explicit raw name source encoding/authority and native receiver/current proof. No getter/default/namejoin invented here.'},
      {'gap':'Self/native5C source and actual server rights',
       'next_actual_root':'Actual WorldOwner full native5C header actor/audience/rights source; peer low12 pool does not establish self actor DWORD or common ID relation.'},
      {'gap':'Receiver47DE70/4812B0 qualified phase',
       'next_actual_root':'Actual original receive direct/indirect qualified transfer; peer-name binding evidence does not change unknown phase/slot.'},
    ]
    dump('source-actions.json',actions);dump('gaps.json',gaps)
    dump('findings.json',{'round':182,'client_sha256':PIN,'new_bounded_native_spans':0,
        'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':len(sites),'retained_bounded_native_bytes':sum(r['bytes'] for r in sites),
        'retained_peer_name_facts':facts,'source_name_binding_qualification':source_facts,
        'bounded_actual_source_actions':actions,'native_original_inputs':len(originals),
        'cpp_edits':[],'new_source_bindings':0,'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':a,'phase':None,'slot':None,'producer':None} for a in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,'gaps':gaps,
        'scope':'Retained native fields plus actual current-source binding/lifetime actions; root owns182 actual caller and published-name implementation.',
        'builds_tests_runtime_codec_formatter_render_deploy':False,'awaiting_BATCHFINAL':True})


if __name__=='__main__':main()
