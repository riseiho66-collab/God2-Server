"""Round180 retained-only CN5C recipient field/call qualification.

Static PE/file reads only. No formatter, capacity, renderer, glyph, converter,
codec or native execution; no new recovered route, phase or field semantics.
"""
from pathlib import Path
import csv
import io
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
from .cn_receiver_owner_frontier169 import sha, mapped

SERVER=Path(__file__).resolve().parents[2]
ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
OUT=ROOT/'cn-native-chat-consumer-source-01/agents/cn-chat-recipient-frontier'
EXE=SERVER.parent.parent/'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY=EXE.parent.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN='tools/reconstruction/cn_native_chat_recipient180.py'
SOURCE=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
    'src/cn/protocol/CnChat.h','src/cn/text/CnChatContent.h','src/cn/text/CnChatContent.cpp',
    'docs/research/cn-chat-visible-identity-20261007.md',
    'tools/reconstruction/cn_receiver_owner_frontier169.py',
    'tools/reconstruction/cn_native_chat_family179.py',
    'tools/reconstruction/cn_chat_visible_identity_delivery.py']
CONTEXT=['src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp']
INPUTS={'0048fcc0','005485f0','0049a020','0048caa0','0048e830','0048da20','0048e3e0','004892b0'}
SPANS=[('world5C','0048fcc0',0x492278,0x4923e6,'edi'),
       ('battle5C','005485f0',0x5488bc,0x548900,'esi')]


def dump(rel,obj):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write((json.dumps(obj,indent=2,ensure_ascii=True)+'\n').encode())


def retain(rel,p,repository=False):
    b=p.read_bytes();q=OUT/rel;q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as f:f.write(b)
    return {'path':p.relative_to(SERVER).as_posix() if repository else str(p.resolve()),
            'copy':rel,'bytes':len(b),'sha256':sha(b)}


def main():
    if OUT.exists():raise RuntimeError('Preserve previous round180 evidence')
    raw=EXE.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN actual original changed')
    OUT.mkdir(parents=True)
    dump('before-source-origins.json',[retain(f'before/b{n:02d}{Path(r).suffix}',SERVER/r,True)
        for n,r in enumerate(SOURCE)])
    dump('context-before-source-origins.json',[retain(f'context/k{n:02d}{Path(r).suffix}',SERVER/r,True)
        for n,r in enumerate(CONTEXT)])
    dump('source-absence.json',{'new_tool_absent_freshbefore1290':OWN,'cpp_edits':[],
        'excluded_current_pins':CONTEXT,'no_new_source_intermediate':True})
    dump('intermediate-source-origins.json',[])
    old=ROOT/'cn-shared-native-chat-owner-01/native/chat-evidence.json'
    prior=ROOT/'tw-native-chat-family-source-01/agents/cn-chat-family-frontier'
    derived=[old,prior/'findings.json',prior/'seal.json',
        ROOT/'cn-native-chat-consumer-source-01/before-manifest.json']
    dump('derived-inputs.json',[retain(f'derived/d{n:02d}.json',p) for n,p in enumerate(derived)])
    metadata=list(csv.DictReader(io.StringIO((RECOVERY/'functions.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    selected=[r for r in metadata if r['address'] in INPUTS]
    originals=[retain('inputs/pe.exe',EXE)]
    for n,name in enumerate(('functions.tsv','calls.tsv')):
        originals.append(retain(f'inputs/t{n}.tsv',RECOVERY/name))
    for row in selected:originals.append(retain('inputs/'+row['address']+'.c',RECOVERY/row['file']))
    dump('native-original-inputs.json',originals);dump('native/selected-original-metadata.json',selected)
    pe=pefile.PE(data=raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    instructions={};sites=[];memory=[]
    for name,owner,lo,hi,record_base in SPANS:
        off,b=mapped(pe,raw,lo,hi);decoded=[];access=[]
        for i in md.disasm(b,lo):
            row={'va':f'{i.address:08x}','bytes':bytes(i.bytes).hex(),
                 'instruction':i.mnemonic+(' '+i.op_str if i.op_str else '')}
            decoded.append(row);instructions[row['va']]=row
            for operand in i.operands:
                if operand.type==X86_OP_MEM and i.reg_name(operand.mem.base)==record_base:
                    access.append(dict(row,displacement=operand.mem.disp,width_bytes=operand.size,
                        index=i.reg_name(operand.mem.index),
                        operation='address-only' if i.mnemonic=='lea' else 'bounded-record-operand'))
        p=OUT/f'native/retained/{name}.bin';p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(b)
        dump(f'native/retained/{name}.json',decoded)
        sites.append({'name':name,'owner':owner,'start_va':f'{lo:08x}','end_va_exclusive':f'{hi:08x}',
            'file_offset':off,'bytes':len(b),'raw_bytes':b.hex(),'sha256':sha(b),
            'decoded_bytes':sum(len(bytes.fromhex(r['bytes'])) for r in decoded),
            'retained_only':True,'no_new_native_span_increment':True})
        memory.append({'name':name,'record_base':record_base,'operands':access,
            'opaque_offsets_not_read_in_this_exact_interval':[3,4,10,11,12],
            'scope':'Only direct operands against unchanged original record register in this bounded case. No global unused-field claim; indirect callees/converter/transport/other paths remain outside this result.'})
    dump('native/retained-sites.json',sites);dump('native/record-operands.json',memory)
    calls=list(csv.DictReader(io.StringIO((RECOVERY/'calls.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    dump('native/bounded-original-calls.json',[r for r in calls if any(
        lo<=int(r['callsite'],16)<hi for _,_,lo,hi,_ in SPANS)])

    def fact(key,addresses,scope):
        return {'key':key,'scope':scope,'raw_sites':[instructions[a] for a in addresses],
                'retained_only':True,'new_server_rights':False,'new_full_route':False}
    facts=[
        fact('world5C_field_and_language_dispatch',
          ['00492278','00492280','0049228b','0049228e','00492293','0049229b','004922af','004922b4'],
          'World case addresses text+0x0D and reads BYTE+9 low7 channel/high1 tag; channels<=9 or18 may use existing converter if tag differs. Converter implementation is not traced, executed or qualified here.'),
        fact('ordinary_self_or_peer_actor_full_DWORD',
          ['004922e8','004922ec','00492346','0049234c','00492360','00492392','004923b2','004923bb'],
          'Only channel0/6 marker-gated branch here reads full DWORD record+5, compares same width with game+0x1478084 self identity and supplies it to00531EA0 peer callback. No low12 mask here. Self identity producer is not recovered; old peer6F low12 lineage is not proof for this separate self field. Renderer callback is not traced.'),
        fact('party_guild_named_nonbubble_source_call_contract',
          ['004922e8','004922ec','004922f1','004922f4','004923cd','004923d1','004923d7','004923d8','004923db','004923dc'],
          'Channels1/3/2/9 take non0/6/non12 branch into0049A020 with two args low7 channel and actual text, ECX game+0x89B26C. No packet/header/actor argument or party/guild member gate at this call. Does not prove absence of all native gates/state elsewhere or formal server permissions.'),
        fact('battle5C_different_direct_field_contract',
          ['005488bc','005488c4','005488cb','005488cd','005488d4','005488e4','005488f1','005488f9','005488fa','005488fb'],
          'Battle case directly uses text+0x0D/BYTE+9 only, conversion eligibility<=9 (not world18) and passes channel/text to0054B470. Actor DWORD and opaque header offsets have no direct read in this68B interval; no equality with ordinary world identity/bubble path. Downstream battle/render/control interpretation remains outside scope.'),
    ]
    dump('native/retained-recipient-facts.json',facts)
    gaps=[
        {'gap':'Opaque full5C source fields','next_actual_root':'Real complete native5C server header supplier and other build-matched consumers; header3/4/10/11/12 direct not-read within these intervals does not authorize defaults or invented meaning.'},
        {'gap':'Self actor identity producer/current lifecycle','next_actual_root':'World5C compares game+0x1478084 fullDWORD. Actual48CAA0/48DA20/48E3E0 pass pointers to this region;48E830 reads it,4892B0 clears a larger region. These context files alone do not qualify the actual writer or link it to common database ID.'},
        {'gap':'Nonbubble audience/rights','next_actual_root':'SharedNativeChat::WorldOwner real sender/membership/exact whisper recipient/audience/rate/mute/fullheader qualifier. Client channel-only consumer does not supply this server authority.'},
    ]
    actions=[
        {'source':'Existing CnChat::Reply/current native5C supplier',
         'action':'Preserve all opaque header bytes; do not convert requestWORD0/FFFF or database IDs into actor/header defaults. Treat bounded not-read as unknown source semantics.'},
        {'source':'SharedNativeChat peer/self delivery qualification',
         'action':'Keep actual channel0/6 peer binding proof separate from self game+1478084 identity source. Do not require this peer registry as invented party/guild/private actor proof, and do not drop actual server header/authority qualification.'},
        {'source':'Existing WorldOwner resolve/qualify_delivery for1/3/2/9',
         'action':'Supply real party/guild membership or exact target identity/audience and complete native reply. Consumer channel/text-only transfer proves neither permission nor full route.'},
    ]
    dump('gaps.json',gaps);dump('source-actions.json',actions)
    dump('findings.json',{'round':180,'client_sha256':PIN,
        'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':len(sites),'retained_bounded_native_bytes':sum(x['bytes'] for x in sites),
        'retained_recipient_facts':facts,'record_operands':memory,'source_actions':actions,
        'native_original_inputs':len(originals),'cpp_edits':[],'new_source_bindings':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':a,'phase':None,'slot':None,'producer':None} for a in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'gaps':gaps,'scope':'Retained-only bounded recipient/source qualification; native counts not incremented.',
        'builds_tests_runtime_codec_formatter_render_deploy':False,'awaiting_BATCHFINAL':True})


if __name__=='__main__':main()
