"""Round181 static retained CN names/common identity qualification.

File/PE/Capstone reads only; no codec, formatter, renderer or native execution.
Existing native spans and target-name producer evidence are retained, not new.
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
OUT=ROOT/'shared-native-chat-identity-source-01/agents/cn-whisper-identity-frontier'
EXE=SERVER.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN='tools/reconstruction/cn_native_whisper_identity181.py'
SOURCE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
    'src/cn/auth/CnSelectionNameProjection.h','src/cn/auth/CnSelectionNameProjection.cpp',
    'src/cn/auth/CnCreationNameProjection.h','src/cn/auth/CnCreationNameProjection.cpp',
    'src/cn/auth/SharedCommonCharacterSummarySource.h','src/cn/auth/SharedCommonCharacterSummarySource.cpp',
    'src/cn/auth/SharedStoredCharacterSummarySource.h','src/cn/auth/SharedStoredCharacterSummarySource.cpp',
    'src/cn/auth/CnNativeCharacterSummaryCommit.h','src/cn/auth/CnNativeCharacterSummaryCommit.cpp',
    'src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp',
    'src/cn/auth/SharedAccountSelectionName.cpp','src/cn/protocol/CnCharacterSummary.h',
    'src/cn/protocol/CnSelectionNameSubmission.h','src/cn/protocol/CnCharacterCreate.h',
    'src/cn/protocol/CnChat.h','src/cn/text/CnChatContent.h','src/cn/text/CnChatContent.cpp',
    'src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp',
    'src/db/NativeCharacterSummarySnapshotRepository.h','src/db/RecoveredCharacterRepository.h',
    'tools/reconstruction/cn_receiver_owner_frontier169.py',
    'tools/reconstruction/cn_native_chat_family179.py',
    'tools/reconstruction/cn_selection_name_identity_delivery.py',
    'tools/reconstruction/cn_summary_local_cache_delivery.py']
CONTEXT=['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedChatIdentitySource.h','src/game/SharedChatIdentitySource.cpp',
    'src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp',
    'src/game/SharedTaiwanNativeChatSource.h','src/game/SharedTaiwanNativeChatSource.cpp']
INPUTS={'00481640','0047f750','00446bd0','004b1390','004ddcd5','00433b00'}
SPANS=[('normal07_name_cache','00481640',0x4817ef,0x48184a),
       ('D3_accepted07_name_cache','0047f750',0x47f929,0x47f984),
       ('selection_prompt_marker','00446bd0',0x447c7d,0x447ccf),
       ('D3_name_and_ordinal','0047f750',0x47f750,0x47f7af),
       ('UI_body_target_transfer','004ddcd5',0x4de17f,0x4de198),
       ('UI_body_only_transfer','004ddcd5',0x4de1e0,0x4de1f4)]


def dump(rel,obj):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write((json.dumps(obj,indent=2,ensure_ascii=True)+'\n').encode())


def retain(rel,p,repository=False):
    b=p.read_bytes();q=OUT/rel;q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as f:f.write(b)
    return {'path':p.relative_to(SERVER).as_posix() if repository else str(p.resolve()),
            'copy':rel,'bytes':len(b),'sha256':sha(b)}


def main():
    if OUT.exists():raise RuntimeError('Preserve previous round181 evidence')
    raw=EXE.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN original image changed')
    OUT.mkdir(parents=True)
    dump('before-source-origins.json',[retain(f'before/b{n:02d}{Path(r).suffix}',SERVER/r,True)
        for n,r in enumerate(SOURCE)])
    dump('context-source-origins.json',[retain(f'context/k{n:02d}{Path(r).suffix}',SERVER/r,True)
        for n,r in enumerate(CONTEXT)])
    dump('context-epoch.json',{'scope':'Actual read epoch during concurrent root181 work; not freshbefore1294 or root-before-edit. Not final current pins.','paths':CONTEXT})
    dump('source-absence.json',{'new_tool_absent_freshbefore1294':OWN,'cpp_edits':[],
        'excluded_current_pins':CONTEXT,'no_source_intermediate':True})
    dump('intermediate-source-origins.json',[])
    derived=[ROOT/'cn-selection-name-identity-01/findings.json',
        ROOT/'cn-selection-name-identity-01/native/name-prompt-primary-sites.json',
        ROOT/'cn-summary-local-cache-01/local-cache-source-relations.json',
        ROOT/'tw-native-chat-family-source-01/agents/cn-chat-family-frontier/findings.json',
        ROOT/'cn-native-chat-consumer-source-01/agents/cn-chat-recipient-frontier/findings.json',
        ROOT/'shared-native-chat-identity-source-01/before-manifest.json']
    dump('derived-inputs.json',[retain(f'derived/d{n:02d}.json',p) for n,p in enumerate(derived)])
    metadata=list(csv.DictReader(io.StringIO((RECOVERY/'functions.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    selected=[r for r in metadata if r['address'] in INPUTS]
    if {r['address'] for r in selected}!=INPUTS:raise ValueError('Actual native C metadata missing')
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
        p=OUT/f'native/retained/{name}.bin';p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(b)
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
    facts=[fact('raw_name_cache_not_common_identity',
        ['00481810','00481815','00481819','0048181b','00481835','0048183c',
         '0047f950','0047f955','0047f959','0047f95b','0047f975','0047f97c'],
        'Accepted07 raw name including NUL is copied into local124B cache +4+40*i. Row+0x13 low3 is native slot, not commonID. BYTE loop does not decode names, supply server rights or establish alias/common-ID equality. Existing source evidence, not newly recovered.'),
      fact('raw_native_prompt_marker_not_alias',
        ['00447c7d','00447c84','00447c87','00447c90','00447cb1','00447cb6','00447cc1','00447cca'],
        'Selected signedWORD UI ordinal indexes raw07 rows36B; raw NUL-terminated name length>=3 and first/last BYTE25h enters existing prompt. A native UI branch, not common name namespace, alias, ready-world identity or permission. Callee not traced.'),
      fact('D3_ordinal_not_character_ID',
        ['0047f774','0047f780','0047f782','0047f786','0047f791','0047f795','0047f7a2','0047f7a5','0047f7aa'],
        'Existing producer zeroes local24B payload, retains WORD selected row ordinal at payload+0x14 and copies name via existing strncpy15 call, sendsD3/24payload. Callee/codec not executed or traced; common resolver uses actual published ID vector and full roots, never submitted name/ordinal as ID.'),
      fact('UI_target_name_pointer_not_common_ID',
        ['004de17f','004de185','004de187','004de188','004de18a','004de18c','004de192','004de193',
         '004de1e0','004de1e2','004de1e4','004de1e6','004de1ec','004de1ee','004de1ef'],
        'Existing ordinary UI transfer calls004B1390 with body pointer, optional target-name pointer, channelarg0 and WORD0. Previously retained179 ordinary party/guild/native dollar grammar remains scoped producer evidence; WORD/target bytes provide no common ID or permission. No format implementation traced.')]
    dump('native/retained-name-facts.json',facts)
    source_facts=[
      {'key':'selection_D3_original_identity_projection','sources':['src/cn/auth/CnSelectionNameProjection.h','src/cn/auth/CnSelectionNameProjection.cpp','src/cn/protocol/CnSelectionNameSubmission.h'],
       'scope':'Exact full25B D3 shape with<=14 raw name bytes. Explicit wire936 decode and explicit common codepage qualify identical original_utf8; preserves complete common16 including postNUL. No name uniqueness/authorization/script conversion.'},
      {'key':'creation_original_identity_projection','sources':['src/cn/auth/CnCreationNameProjection.h','src/cn/auth/CnCreationNameProjection.cpp','src/cn/protocol/CnCharacterCreate.h'],
       'scope':'Ordinary17 exact45B form, ui_name <=14 encoded bytes. Explicit936 original identity equals complete actual common40 profile name. matches_created verifies slot/profile/codepage/style only; real owner must separately qualify uint64 account/character.'},
      {'key':'common_name_domain','sources':['src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp'],
       'scope':'Nonempty noNUL <=14 encoded bytes; page936/950 strict roundtrip valid originalUTF8. Page0 unchanged ASCII only, not host locale. No folding/normalization/display conversion/default replacement. Codecs read as source, never executed.'},
      {'key':'native_summary_name_mode_proof','sources':['src/cn/auth/SharedCommonCharacterSummarySource.h','src/cn/auth/SharedCommonCharacterSummarySource.cpp','src/cn/auth/SharedStoredCharacterSummarySource.cpp','src/db/NativeCharacterSummarySnapshotRepository.h'],
       'scope':'NameSource is explicit storage metadata, not wire flag. Ordered Row.character uint64 is selected by commonID within complete same-account roots, same account+group/server+actual client/revision/authority. CommonIdentity copies exact encoded936 originalname and NUL only; NativePromptMarker retains original07. CommonIdentity projected07 marker is refused. Full original/projected07, rows, optional22 and roots remain in observing proof.'},
      {'key':'NativeSummary_vs_NameIdentity_domain','sources':['src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp','src/cn/auth/SharedAccountSelectionName.cpp'],
       'scope':'NativeSummary roots/IDs/record/current all private. NameIdentity exposes uint64 account/character from actual published07, selected offer, ordinal/current actual account name-prompt phase; it is pre-mutation D3 identity, not ready-world chat lease. Complete root ID/account/slot/profile/created_at/codepage/style repeated. Never reuse old roots as staged post-mutation proof.'},
      {'key':'private_target_original_bytes_and_opaque_numbers','sources':['src/cn/text/CnChatContent.h','src/cn/text/CnChatContent.cpp','src/cn/protocol/CnChat.h'],
       'scope':'Only channel2/9 plain dollar target space body supplies raw target-name view. Board/control/unresolved variants remain separate. Request opaqueWORD and full native5C actorDWORD are distinct unknown native fields, not common uint64ID. Prior180 actor-low12 peer evidence cannot establish self/fullID/common equivalence.'},
    ]
    dump('source-name-qualification.json',source_facts)
    actions=[
      {'source':'Actual SharedWorldPresence ready common roots -> root181 SharedChatIdentitySource',
       'action':'Keep full uint64 ID/account, source/lease/generation/current ready state, full common root/profile/codepage. Use exact original UTF8 equality only within actual ready population; ambiguous/missing/unrepresentable are explicit observations, not default row, alias, offline rule or sender reply. Current must retain same observing population and owner proof.'},
      {'source':'NativePromptMarker vs common ready identity',
       'action':'Do not lift raw07 prompt marker into ready name lookup or treat it as alias. Conversely, a qualified common-ready root name containing percent bytes is not globally forbidden by this account UI marker evidence; explicit name-source/domain proof decides which source it is.'},
      {'source':'Actual CN2F named-whisper and TW independent chat caller',
       'action':'Retain raw CN936 target bytes plus strict original identity; independent TW edge remains explicit950. Actual owner must qualify sender/target/membership/mute/audience/current complete native header. No actor narrowing/commonID cast, WORD-ID mapping, guessed5C or offline response.'},
    ]
    gaps=[
      {'gap':'Actual full native5C identity/header producer and server policy',
       'next_actual_root':'SharedNativeChat actual WorldOwner resolve/current native fullreply and real common readiness recipient owner. Name identity lookup alone supplies no sender rights/membership/native actor mapping or official no-ready-target reply.'},
      {'gap':'Original native alias/equivalence/uniqueness and offline target policy',
       'next_actual_root':'Actual server-owned issuer/rule evidence for corresponding native family, not UI marker/target bytes/privateWORD. Exact original equality is current common source lookup scope, not recovered official aliases or rules.'},
      {'gap':'Receiver selector47DE70/4812B0 phase',
       'next_actual_root':'Bounded original direct/indirect qualified receive transfer; independent name namespace evidence provides no receiver phase.'},
    ]
    dump('source-actions.json',actions);dump('gaps.json',gaps)
    dump('findings.json',{'round':181,'client_sha256':PIN,'new_bounded_native_spans':0,
        'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':len(sites),'retained_bounded_native_bytes':sum(r['bytes'] for r in sites),
        'retained_name_facts':facts,'source_name_qualification':source_facts,'source_actions':actions,
        'native_original_inputs':len(originals),'cpp_edits':[],'new_source_bindings':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':a,'phase':None,'slot':None,'producer':None} for a in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,'gaps':gaps,
        'scope':'Retained-only native names and static current common identity qualification; root owns actual181 readiness/chat caller implementation.',
        'builds_tests_runtime_codec_formatter_render_deploy':False,'awaiting_BATCHFINAL':True})


if __name__=='__main__':main()
