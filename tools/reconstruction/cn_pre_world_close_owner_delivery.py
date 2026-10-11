"""Capture actual pre-world terminal ingress/composition source, file-only."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, CN, PIN

NAME='cn-pre-world-close-owner-01'
ROUND='20261007-cn-pre-world-close-owner'
SOURCES=('src/cn/auth/SharedPreWorldCloseReply.h',
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
    'tools/reconstruction/cn_pre_world_close_owner_delivery.py',
    'docs/research/cn-pre-world-close-owner-20261007.md')
CONTEXT=('src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp',
    'src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
    'src/cn/protocol/CnPreWorldCloseControl.h','src/cn/protocol/CnPreWorldCloseReply.h',
    'src/cn/auth/SharedCharacterDeleteIdentity.cpp','src/cn/net/SharedCredentialServer.cpp')


def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';out=b/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve prior artifacts')
    image=CN.parent/'XJZ-CN/God2_opt.exe'
    if hashlib.sha256(image.read_bytes()).hexdigest()!=PIN:
        raise RuntimeError('Pinned native input changed')
    files=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        files.append({'path':rel,'original':str(origin),'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,value):
        save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),
             'current static source accounting')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    for rel in CONTEXT:save('context/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    reused=[]
    for prior_name,rels in (
        ('cn-close-producer-variants-01',('findings.json','native/0043d280.bin','native/0043d280.asm',
            'native/00446bd0.bin','native/00446bd0.asm','native/00480b10.bin','native/00480b10.asm')),
        ('cn-world-close-drain-01',('findings.json','native03-primary-branches.json',
            'native/world03-return8-caller.bin','native/length03-slot.bin'))):
        prior=b/prior_name
        manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={row['path']:row['sha256'] for row in manifest['files']}
        for rel in rels:
            data=(prior/rel).read_bytes()
            if hashlib.sha256(data).hexdigest()!=pins[rel]:
                raise RuntimeError('Sealed retained evidence changed')
            save('retained-native/'+prior_name+'/'+rel,data,prior/rel)
        reused.append(prior_name)
    dump('source-chain.json',{
        'composition':'SharedLoginSources::World::terminal_close ->compose_native_login ->SharedWorldSelection::attach',
        'ingress':'preselected receive exact02control0/3/4 after actual1F queue ->receive_close',
        'identity':'verified common account +lifetime-unique world session +current committed ticket',
        'operation':'required exact-scope actual current-operation predicate; wire control is not permission',
        'reply':'complete source supplied native03 with both unresolved payload bytes preserved',
        'transport':'close_after_native_world_reply ->native queue +owner recheck ->drain_and_close',
        'cleanup':'same transport existing generation-qualified world ticket release, not account connection',
        'offer_invalidation':'terminal uses world_owned/current ticket, never stale offered_source/character membership',
        'completion':'single-use local TCP drain result; closing/ticket deliberately not rechecked after cleanup',
        'limits':'03 issuer/native rule/transaction/replay and complete17/19 routes still absent'})
    findings={'round':ROUND,'previous_goal_turn_classification':'progress: new entry-rooted native CFG evidence and catalog65 sealed',
        'new_cpp_headers':1,'modified_cpp_files':4,'new_conditional_terminal_ingress_owner_chains':1,
        'new_phase_opcode_source_bindings':2,'new_native_opcode_values':0,
        'qualified_control_forms':['0200','0203','0204'],'existing_control_forms_reused':True,
        'retained_native_artifacts_reused':reused,'current_ticket_not_stale_offer':True,
        'actual_native03_issuer_added':False,'actual_mutation_transaction_added':False,
        'formal_application_hosted':False,'new_complete_bidirectional_routes':0,
        'remaining':['Actual native17/19 rules, pending-operation/replay ownership and common create/delete transaction must supply truthful terminal operation state; no wire control alone authorizes close or mutation.',
          'Actual complete03 payload/issuance and02/1E/18 issuers remain open; no zero-filled success or TW permission substitution.',
          'Actual configured Application providers/hosting, Native0 upstream state variants, aggregate/indirect/deferred paths and whole-game denominator remain incomplete.'],
        'levels_changed':False,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False}
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({k:findings[k] for k in ('round','new_cpp_headers','modified_cpp_files',
        'new_conditional_terminal_ingress_owner_chains','new_phase_opcode_source_bindings','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
