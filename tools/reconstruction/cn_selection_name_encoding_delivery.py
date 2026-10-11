"""Retain static primary CN name/display evidence and actual identity integration.

File-only receipt; no native/API/DLL, codec, gameplay, build, test or SQL run.
Encoding identity policy is a bounded server source requirement, not recovered
official naming authority or observed Windows NLS acceptance.
"""
import csv
import hashlib
import json
import capstone
from capstone.x86 import X86_OP_MEM
import pefile
from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN
from .cn_pe_import_directory import FileView, import_directory
from .cn_delete_caller_seh_frontier import decode_cfg

NAME='cn-selection-name-encoding-01'
ROUND='20261007-cn-selection-name-encoding'
FUNCTIONS=('0047f750','00433b00','0053f880')
SOURCES=('src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp',
    'src/cn/auth/CnSelectionNameProjection.h','src/cn/auth/CnSelectionNameProjection.cpp',
    'src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountNameOperation.cpp',
    'tools/reconstruction/cn_selection_name_encoding_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py',
    'docs/research/cn-selection-name-encoding-20261007.md')
REMAINING=[
    'Actual native naming permission, cross-encoding equivalence/uniqueness, replay/operation lease and source-issued complete native07/1E; no configured native provider/hosting.',
    'Native canonicalization/aliases, non-normal or mixed/aggregate D3, actual Windows NLS/codec qualification and committed-name publication/crash recovery remain open.',
    'Existing codepage0 nonASCII saves remain unbound and untouched. Explicit owner binding/migration and all cross-process invalidation remain open.',
    'Full auth/catalog/world providers, all TW/CN/web gameplay/numeric wire/object/display and directional/state/variant/indirect/deferred denominator. Levels unchanged.']

DOCUMENT='''# CN selection naming: original identity and explicit common encoding

PHASE1 static source/primary PE accounting only. No builds, tests, native/API/DLL/codec/server execution, SQL access, migration or deployment. Levels remain unchanged. The preceding D3 operation source turn was progress; this turn strengthens that existing chain and does not add another handler, owner chain or phase binding.

Three pinned metadata envelopes retain primary bytes, entry-rooted assembly/CFG and navigation C:47F750 (D3 producer/full07 consumer),433B00 (bounded raw UI extraction),53F880 (actor display conversion). Calls are recorded but not followed, unresolved edges retained; metadata boundaries do not close the whole program. Prior sealed submit/operation evidence retains the actual ACCOUNT callers, max14 argument and full native07/1E lengths. These envelopes do not newly prove server naming rules or packet variants.

53F880 has native runtime gates at008A4594/405A40 and a separate display path: CP936 flags0 decode size query, LCMapStringA locale0804/flags04000000 with twice that query capacity, mapped CP936 decode, then flags0 CP950 encode. Current primary instructions/import declarations are retained; imports do not prove loaded implementations or NLS behavior. This display/script mapping remains in existing CnNativeActorText. It must never decide account name identity or silently convert the saved name. Existing LegacyChineseCodec, ChineseText, native role/actor display codecs and text conversion are untouched.

OwnedCharacterNameText adds an immutable bounded original-identity projection at the existing nonempty14-byte/noNUL common-name boundary. Only explicit936/950 or the existing metadata0 are admitted.0 is not CP_ACP or host locale: unchanged ASCII alone qualifies until an actual owner binds encoding; old nonASCII0 rows are never rewritten here.936/950 use the existing strict decoder/encoder, validate UTF8 and require exact byte roundtrip; construction from UTF8 additionally requires exact Unicode equality. No trimming, normalization, case folding, display/script mapping, replacement characters, truncation or encoding fallback. Invalid/unrepresentable returns absent; unavailable codec/runtime/allocation errors propagate to the existing ingress failure boundary. The codec is not executed in this round, and OS/iconv mapping equivalence remains a later qualification task.

CnSelectionNameProjection binds the complete original25-byte D3 record, native CP936 original UTF8 and explicit common16-byte candidate/codepage. Its native shape is the already recovered normal max14-byte prompt branch. A supplied candidate must have nonemptyNUL within the first15 bytes, fit14 bytes and decode to exactly the same originalUTF8. All supplied16 bytes, including postNUL bytes, are retained. The convenience factory takes an explicit owner-selected common codepage and constructs only that encoding with local zero padding; unrepresentable text remains absent, with no automatic950-to936 fallback. Submitted row ordinals/IDs, native prefix/tail and all record bytes remain bound, so an otherwise matching projection from another D3 cannot be reused accidentally. This qualification is not native permission, name lookup, unique-name authority or replay proof.

Actual integration: SharedAccountSelection::NameDecision success now requires this qualified projection rather than an unrelated raw candidate. receive_name checks its complete record binding before SQL, then passes the same retained common16 bytes/codepage into the actual SharedCharacterNameReplacement writer and expected full-account-root CAS snapshot. Existing source-issued full75-byte07 must still map the exact character and echo the raw CN submission; mandatory native rule leases, BeforeReplace/BeforeCommit staged roots, actual COMMIT, all-TW/CN old-offer invalidation and queue-publication barrier remain required. Only the first16 profile bytes/name_codepage change through that existing authorized writer. Levels, profile remainder, IDs, ownership, slot, creation/style fields and save descendants stay intact. Complete07 flags/opaque/inactive bytes still come from the actual source issuer, and complete1E remains an actual supplied failure rather than a guessed reply.

Scope: unchanged original-name normal D3 form only. Native canonicalization/alias/cross-encoding unique-name rules, full providers/configured host, mixed aggregates, operation/replay and committed-name publication/crash recovery are still missing. SQL raw-byte uniqueness alone does not establish Unicode or native equivalence. This is a source identity boundary1, typed CN common-name projection1 and existing D3 operation chain strengthening1; new packet values0, new owner chains0, new phase bindings0 and complete bidirectional routes0. Whole-game total/percentage remain unknown. Preserve all historical receipts and current native fonts, Chinese conversion, authentication, chat, IME, portraits, saves and native levels.
'''

def sha(raw):return hashlib.sha256(raw).hexdigest()

def import_references(pe,raw,decoded):
    # This unpacked file aliases short import arrays. General pefile parsing
    # stops before later descriptors; use the existing primary bounded reader.
    directory=import_directory(pe,raw)
    imports={int(i['iat_va'],16):i for i in directory['bindings']}
    references=[]
    for entry,instructions in decoded.items():
        for i in instructions.values():
            if i.mnemonic not in ('call','mov'):continue
            for operand in i.operands:
                if operand.type!=X86_OP_MEM:continue
                mem=operand.mem
                if mem.base or mem.index or mem.disp not in imports:continue
                references.append({'function':entry,'site':f'{i.address:08x}',
                    'kind':'declared_indirect_call' if i.mnemonic=='call' else 'declared_slot_load',
                    'bytes':bytes(i.bytes).hex(),'import':imports[mem.disp],
                    'loaded_target_observed':False,'register_alias_calls_exhausted':False})
    return directory,references

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before receipt required')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before snapshot changed')
        if row['path'] not in SOURCES and row['path'] not in (
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json',
            'docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    prior=base/'cn-selection-name-operation-01'
    seal=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in seal['files']}
    if not seal['sealed']:raise RuntimeError('Prior operation unsealed')
    for rel in ('findings.json','source-relations.json','native/index.json'):
        raw=(prior/rel).read_bytes()
        if sha(raw)!=pins[rel]:raise RuntimeError('Prior operation differs')
        save('retained-operation/'+rel,raw)
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned native changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    native=[];decoded={}
    for entry in FUNCTIONS:
        row=rows[entry];va=int(entry,16);code=view.read(va-ib,int(row['bytes']))
        cfg,asm,ins=decode_cfg(md,code,va,va+len(code),{})
        decoded[entry]=ins
        save('native/'+entry+'.bin',code);save('native/'+entry+'.asm',asm)
        dump('native/'+entry+'.cfg.json',cfg);save('native/'+entry+'.c',(RECOVERY/row['file']).read_bytes())
        native.append({'entry':entry,'metadata':row,'bytes':len(code),'sha256':sha(code),
            'rooted_instructions':len(ins),'open_edges':cfg['open_edges'],'instruction_overlap':cfg['instruction_overlap_found'],
            'calls_followed':False,'whole_program_closure':False})
    directory,references=import_references(pe,raw,decoded)
    dump('native/index.json',native);dump('native/declared-import-call-references.json',references)
    used={r['import']['descriptor_index'] for r in references}
    dump('native/qualified-import-descriptors.json',{
        'method':directory['method'],'full_descriptor_count':directory['descriptor_count'],
        'full_binding_count':directory['binding_count'],
        'referenced_descriptors':[d for d in directory['descriptors'] if d['index'] in used],
        'loaded_binding_observed':False,'native_execution':False})
    dump('native/metadata-provenance.json',{'original':str(RECOVERY/'functions.tsv'),'sha256':sha(metadata),
        'selected_rows':[rows[e] for e in FUNCTIONS],'navigation_C_is_primary_bytes':False})
    relations={'source_chain':'D3 complete25 ->explicit936 original identity ->explicit common16/codepage ->typed NameDecision ->same full-root SQL writer ->source full07/raw CN echo ->exact selection publication',
        'native_name_producer':'Scoped UI max14 raw extraction433B00;47F750 strncpy15 into zero16. No native uniqueness/encoding canonicalization authority inferred.',
        'native_display_separate':'53F880 actor display LCMapStringA/gated936-to950 path is not account name identity; no display/script mapping used for storage projection.',
        'common0':'Existing unbound metadata, ASCII only qualified; no locale guess or old-row rewrite.',
        'full_record_binding':'Projection matches all25 D3 bytes before SQL, not just a decoded name.',
        'source_qualification':'No codec/API execution or native acceptance; strict unchanged-identity form only.',
        'required_native_sources':'Permission/equivalence/unique/replay lease and complete07/1E issuer remain actual source obligations.'}
    dump('source-relations.json',relations)
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: sealed D3 actual CAS/new07 chain plus additive web local-controller correction',
        'native_metadata_envelopes_retained':len(native),'common_original_name_identity_boundaries_added':1,
        'cn_typed_selection_name_projections_added':1,'existing_D3_operation_source_bindings_strengthened':1,
        'new_source_owner_chains':0,'new_native_phase_source_bindings':0,'new_packet_values':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'native_naming_rule_recovered':False,'configured_native_provider_installed':False,'production_hosted':False,
        'display_script_mapping_used_for_name_identity':False,'existing_sources_unchanged':unchanged,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'remaining':REMAINING}
    dump('findings.json',findings)
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:f.write(DOCUMENT)
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','native_metadata_envelopes_retained',
        'common_original_name_identity_boundaries_added','cn_typed_selection_name_projections_added',
        'existing_D3_operation_source_bindings_strengthened','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
