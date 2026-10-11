"""Round179 independent CN ordinary chat source/caller frontier, static only.

Retains the already recovered complete producer; no formatter/capacity execution,
title-chain retry, decoder execution, invented audience, header or permission.
"""
from pathlib import Path
import csv
import io
import json
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped

SERVER=Path(__file__).resolve().parents[2]
ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
OUT=ROOT/'tw-native-chat-family-source-01/agents/cn-chat-family-frontier'
EXE=SERVER.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN='tools/reconstruction/cn_native_chat_family179.py'
SOURCE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
    'src/cn/text/CnChatContent.h','src/cn/text/CnChatContent.cpp','src/cn/protocol/CnChat.h',
    'src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp',
    'src/cn/world/SharedWorldGameplay.cpp',
    'tools/reconstruction/cn_shared_native_chat_owner_delivery.py',
    'tools/reconstruction/cn_chat_consumer_capacity_delivery.py',
    'tools/reconstruction/cn_chat_visible_identity_delivery.py',
    'tools/reconstruction/cn_receiver_owner_frontier169.py']
CONTEXT=['src/cn/protocol/CnChatConsumerContract.h']
C_INPUTS={'004b1390','004b1468','004b1648','004b168f','004b1706',
    '0049a020','0052c2c0','004ddcd5','00544010'}
SPANS=[
    ('UI-body-target-transfer','004ddcd5',0x4de17f,0x4de198,True),
    ('UI-body-only-transfer','004ddcd5',0x4de1e0,0x4de1f4,True),
    ('generated-template-caller','0052c2c0',0x52c2c0,0x52c49f,True),
    ('retained-complete-producer','004b1390',0x4b1390,0x4b1a10,False),
    ('retained-auto-reply-caller','0049a020',0x49a020,0x49a698,False),
]


def dump(rel,obj):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write((json.dumps(obj,indent=2,ensure_ascii=True)+'\n').encode())


def retain(rel,p,repository=False):
    b=p.read_bytes();q=OUT/rel;q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as f:f.write(b)
    return {'path':p.relative_to(SERVER).as_posix() if repository else str(p.resolve()),
            'copy':rel,'bytes':len(b),'sha256':sha(b)}


def main():
    if OUT.exists():raise RuntimeError('Preserve old round179 artifact')
    raw=EXE.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Actual pinned CN original changed')
    OUT.mkdir(parents=True)
    dump('before-source-origins.json',[retain(f'before/b{n:02d}{Path(r).suffix}',SERVER/r,True)
        for n,r in enumerate(SOURCE)])
    dump('context-before-source-origins.json',[retain(f'context/k{n:02d}{Path(r).suffix}',SERVER/r,True)
        for n,r in enumerate(CONTEXT)])
    dump('new-source-absence.json',{'new_tool_absent_freshbefore1285':OWN,'cpp_edits':[],
        'excluded_current_pins':CONTEXT,'root_mutable_adapters_contracts_books_catalogs_not_pinned':True})
    dump('intermediate-source-origins.json',[])
    old=ROOT/'cn-shared-native-chat-owner-01/native/chat-evidence.json'
    old_obj=json.loads(old.read_text(encoding='utf-8'))
    derived=[old,ROOT/'cn-shared-native-chat-owner-01/integration-manifest.json',
        ROOT/'tw-native-chat-family-source-01/before-manifest.json']
    dump('derived-inputs.json',[retain(f'derived/d{n:02d}.json',p) for n,p in enumerate(derived)])
    dump('native/retained-previous-facts.json',{'whole_producer_previous_range':old_obj['producer_contiguous_range'],
        'original_reported_metadata_not_complete_CFG':True,
        'previous_fields':old_obj['c2s_fields'],'previous_grammar':old_obj['grammar'],
        'native_gate_is_not_server_authority':True})
    metadata=list(csv.DictReader(io.StringIO((RECOVERY/'functions.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    selected=[r for r in metadata if r['address'] in C_INPUTS]
    originals=[retain('inputs/pe.exe',EXE)]
    for n,name in enumerate(('functions.tsv','calls.tsv')):
        originals.append(retain(f'inputs/t{n}.tsv',RECOVERY/name))
    for row in selected:
        originals.append(retain('inputs/'+row['address']+'.c',RECOVERY/row['file']))
    dump('native-original-inputs.json',originals);dump('native/selected-original-metadata.json',selected)
    pe=pefile.PE(data=raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
    instructions={};news=[];retained=[]
    for name,owner,lo,hi,isnew in SPANS:
        off,b=mapped(pe,raw,lo,hi)
        decoded=[{'va':f'{i.address:08x}','bytes':bytes(i.bytes).hex(),
                  'instruction':i.mnemonic+(' '+i.op_str if i.op_str else '')}
                 for i in md.disasm(b,lo)]
        instructions.update({i['va']:i for i in decoded})
        scope='new' if isnew else 'retained';p=OUT/f'native/{scope}/{name}.bin';p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(b)
        dump(f'native/{scope}/{name}.json',decoded)
        item={'name':name,'owner':owner,'start_va':f'{lo:08x}','end_va_exclusive':f'{hi:08x}',
            'file_offset':off,'bytes':len(b),'raw_bytes':b.hex(),'sha256':sha(b),
            'decoded_bytes':sum(len(bytes.fromhex(i['bytes'])) for i in decoded),
            'scope':'Complete bounded transfer or original reported caller extent; not global CFG/phase proof.'}
        (news if isnew else retained).append(item)
    dump('native/new-sites.json',news);dump('native/retained-sites.json',retained)
    data=[]
    for name,lo,hi in [('switch-table',0x4b1a08,0x4b1a7e),
        ('retained-private-format',0x7f2f90,0x7f2f98),('retained-space',0x7efb9c,0x7efb9e),
        ('generated-prefix',0x7f3c78,0x7f3c7a)]:
        off,b=mapped(pe,raw,lo,hi)
        data.append({'name':name,'start_va':f'{lo:08x}','end_va_exclusive':f'{hi:08x}',
            'file_offset':off,'bytes':len(b),'raw_bytes':b.hex(),'sha256':sha(b),
            'new_data_span':name=='switch-table'})
    table=bytes.fromhex(data[0]['raw_bytes']);targets=list(struct.unpack('<6I',table[:24]));indices=table[24:]
    selector=[]
    for character in ['!','#','$','^','~']:
        index=indices[ord(character)-0x21]
        selector.append({'literal_ascii':character,'literal_byte':ord(character),'byte_index':index,
            'actual_target_va':f'{targets[index]:08x}'})
    dump('native/data-sites.json',data)
    dump('native/actual-prefix-table.json',{'switch_targets':[f'{x:08x}' for x in targets],
        'index_bytes':indices.hex(),'index_count':len(indices),'selectors':selector,
        'actual_consumers':[instructions[a] for a in ['004b1430','004b143e','004b1444','004b1447','004b144d','004b1454']]})
    calls=list(csv.DictReader(io.StringIO((RECOVERY/'calls.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    dump('native/bounded-original-calls.json',[r for r in calls
        if r['caller'] in C_INPUTS and (r['target']=='004b1390' or r['caller'] in ['004b1390','004b1706'])])

    def rel(key,addresses,scope):
        return {'key':key,'scope':scope,'raw_sites':[instructions[a] for a in addresses],
                'new_server_rights':False,'new_full_route':False}
    relations=[
        rel('exact_declared_native_prefix_table',
            ['004b1430','004b143e','004b1444','004b1447','004b144d','004b1454'],
            'New full six-target pointer table and94-byte selector map: !->004B1468,#->004B1497,$->004B14C3,^->004B153F,~->004B145B. Retained whole producer gates/effective-channel decisions remain old evidence. Table membership is not receiver phase, opcode count or server membership.'),
        rel('actual_UI_two_source_argument_transfers',
            ['004de17f','004de185','004de187','004de188','004de18a','004de18c','004de192','004de193',
             '004de1e0','004de1e2','004de1e4','004de1e6','004de1ec','004de1ee','004de1ef'],
            'Actual004DDCD5 source transfers body local[EBP-0x84], optional target local[EBP-0x94], original game ECX, channel argument0 and opaque WORD argument0. Body-only sibling passes target null. Later channel choice is the same retained native producer domain, not inferred party/guild permission.'),
        rel('generated_template_source_not_ordinary_UI_witness',
            ['0052c476','0052c47d','0052c484','0052c486','0052c487','0052c489'],
            'Actual0052C2C0 generated message-template row0x26C and literal~ source sends channelarg0/opaqueWORD0xFFFF/targetnull. Different source action from ordinary UI; actual final body bytes/template grammar were not decoded, so plain/control classification remains unknown and this is no added player-chat route.'),
    ]
    prior_facts=[
        {'fact':'party/guild client gate only','raw_sites':[instructions[a] for a in ['004b1468','004b147e','004b1484','004b1486','004b1497','004b14ad','004b14b6','004b14b8']],
         'scope':'! channel1 reads client+0x430A8 ->DWORD+0x3F98; # channel3 reads same object BYTE+6. Failed gate retains prefix/effective-channel fallback. Neither supplies formal server member list or send right.'},
        {'fact':'private envelope identity/body','raw_sites':[instructions[a] for a in ['004b14cf','004b14dd','004b14e2','004b1500','004b1505','004b153d','004b16b5','004b16bb','004b170c','004b1717','004b1721','004b174e']],
         'scope':'Retained $ parser uses literal ASCII space, copies target bytes and skips leading spaces in original entered body; channels2/9 use original literal $%s %s. Channel9 actual argument override and WORDFFFF exist. Do not run formatters or treat client target string as authoritative lookup.'},
        {'fact':'opaque word and ordinary wire header','raw_sites':[instructions[a] for a in ['004b1794','004b179f','004b17a6','004b17ac','004b17b1','004b17b4','004b17bb','004b199b','004b199d']],
         'scope':'Retained2F total-length WORD, low7 channel/high1 tag, caller-supplied WORD atrecord5 for ordinary family; record4 remains opaque. A zero/FFFF argument is not a common character ID. No original full5C server producer/header claimed.'},
    ]
    dump('native/retained-family-facts.json',prior_facts)
    actions=[
        {'actual_source':'CnChatContent::split','scope':'Ordinary0/1/3 PlayerText and2/9 $target+ASCII space+body are already classified; controls/board/unresolved variants not silently converted. Original target_wire_name bytes remain identity; convert body only.',
         'necessary_action':'Real WorldOwner.resolve must supply channel-specific membership/audience/name lookup/rights for the verified same lease; no membership from client gate.'},
        {'actual_source':'SharedWorldGameplay::split/dispatch ->SharedNativeChat ingress/dispatch',
         'scope':'Existing2F length/shape handler installs actual Chat ingress and resolves lease-current publication; native family grammar is already reachable in source.',
         'necessary_action':'Supply full current native5C reply/header, exact body offset/size, original UTF8 body, actual audience and recipient owner/tag. Current codec/contract is not this supplier.'},
        {'actual_source':'SharedNativeChat WorldOwner contract',
         'scope':'Supported party/guild/private input does not create actual member list, whisper recipient or server rule.',
         'necessary_action':'Use shared authoritative party/guild membership and exact whisper identity lookup, native header producers, rate/mute/rights/state and qualified native consumer. No default same-map fanout or guessed5C header.'},
    ]
    gaps=[{'gap':'Actual party/guild membership and channel-specific permissions','next_actual_root':'Existing SharedNativeChat::WorldOwner::resolve/qualify_delivery actual server source; client+430A8 fields only retained UI gate.'},
          {'gap':'Native named whisper recipient and full5C fields','next_actual_root':'Real exact target_wire_name identity lookup and native5C fullheader producer; opaque requestWORD0/FFFF cannot select common identity.'},
          {'gap':'Generated-template body domain','next_actual_root':'0052C2C0 row0x26C actual resource bytes and generating source required before plain/control classification; no decoder/codec execution this round.'}]
    dump('source-actions.json',actions);dump('gaps.json',gaps)
    dump('findings.json',{'round':179,'client_sha256':PIN,
        'new_bounded_native_spans':len(news),'new_bounded_native_bytes':sum(x['bytes'] for x in news),
        'new_native_data_spans':1,'new_native_data_bytes':118,
        'previously_preserved_data_bytes':8,'unique_new_native_data_bytes':110,
        'new_data_scope':'Full118B table is new bounded table analysis; first8B were retained in old contiguous producer. Do not count118B as unique fresh bytes.',
        'retained_bounded_native_spans':len(retained),
        'new_native_relations':relations,'retained_family_facts':prior_facts,'source_actions':actions,
        'native_original_inputs':len(originals),'cpp_edits':[],'new_source_bindings':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':a,'phase':None,'slot':None,'producer':None} for a in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'gaps':gaps,'builds_tests_runtime_codec_deploy':False,'awaiting_BATCHFINAL':True})


if __name__=='__main__':
    main()
