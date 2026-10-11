"""Save CN31/68/6D exact consumer/source operands; never gameplay tests."""
import difflib,hashlib,json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT,PIN
NAME='cn-same-opcode-consumer-source-01'
ROUND='20261008-cn-same-opcode-consumer-source'
SOURCES=(
    'src/cn/protocol/CnWorldConsumerRecords.h','src/cn/world/CnWorldConsumerSource.h',
    'src/cn/world/CnWorldConsumerSource.cpp',
    'docs/research/cn-same-opcode-consumer-source-20261007.md',
    'tools/reconstruction/cn_same_opcode_consumer_source_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
    'Actual31 owned-row/list/registry and68 resource/table/UI lifetime suppliers,6D retained tail/text/UI conflict providers remain unconfigured.',
    'These consumer operands are not common authoritative stats/monster skills, request/reply pairing, gameplay handlers/persistence or native success.',
    'All31/68/6D upstream/indirect/state variants, formal account/world/native appearance suppliers, PC/web/WSS hosting, shared numeric/gameplay/security and exhaustive route denominator remain open.']
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh source snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    old={x['path']:(out/x['snapshot']).read_bytes() for x in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source changed')
        if row['path'] not in set(SOURCES)|set(books):
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected context differs')
            protected.append(row)
    previous=(out/'prior/cn-deferred-role-refresh-source-01/manifest.json').read_bytes()
    if sha(previous)!='bb71916bb08ecf14624014d8f5dcef49a6a5b31fc214f7888668b9587b321249' or not json.loads(previous)['sealed']:
        raise RuntimeError('Previous static seal differs')
    env=json.loads((out/'native/function-envelopes.json').read_text(encoding='utf-8'))
    if env['sha256']!=PIN:raise RuntimeError('Native identity differs')
    tables=json.loads((out/'native/primary-table-relations.json').read_text(encoding='utf-8'))
    covered=set()
    for r in env['ranges']:covered.update(range(int(r['va'],16),int(r['va'],16)+r['bytes']))
    for r in tables:
        for key,n in [('world_cell_va',4),('length_cell_va',4),('length_target',7)]:
            va=int(r[key],16);covered.update(range(va,va+n))
    consumers=[
        dict(opcode='31',logical_size=29,dispatch_target='0049134c',dispatch_callsite='00491356',handler='004d58b0',
            owner_alias='main+89b26c',related_owner='UI+430a8',record_count='BYTE owner+D4',row_base='owner+D8',row_stride=0x3ec,
            gates=['First signedBYTE payload0 versus signedWORD row0 match','No match/count0 returns; no insertion'],
            mutation='BYTE1->row2; five unsignedWORD->DWORD44..54; fourWORD->WORD38..3E; WORD18 low15/topbit ->28/5A; retained count1F0 ceil/25',
            opaque_payload_ranges=['0C..0F','1A..1B'],presentation='Exact flag5A==1 active-prefix scan, selectionD0/CF;4D5030/5440/5520 require actual resources/retained abilities; not authoritative monster stats'),
        dict(opcode='68',logical_size=13,dispatch_target='00491edc',dispatch_callsite='00491f2a',handler='004c4060',
            owner_alias='main+89b26c',related_owner='main+A69F20',record_count='signedWORD resource+B2F78',row_base='DWORD resource+B2F7C',row_stride=0x8c,
            gates=['unsigned logicalWORD3 must be nonzero and<=signed count','negative signed UIhandle1C84C4 returns before null row assertion','valid handle plus null row asserts/returns'],
            operands='resource signedWORDB2F76; logicalDWORD5/BYTE9/BYTEA; rowDWORD4=BYTE9,DWORDC=signextended resourceWORD,DWORD10=(BYTEA==1?105:100)',
            opaque_logical_ranges=['01..02','0B..0C'],presentation='Actual4C4880/4C3800 before writes;30 actual resource key/icon reads and UI conflict paths remain open'),
        dict(opcode='6D',logical_size=29,dispatch_target='004902cb',dispatch_callsite='004902d5',handler='0052ae10',
            owner_alias='main+89b26c',copy='All28 payload bytes ->UI3E71C..3E737',cursor=0,
            page_count='max(1,ceil((payloadBYTE4&7F)/10))',presentation='52A9E0 UI conflict gates,52AF60 actual resource strings/history/entries beyond copied prefix,456AB0(-1); no full list fabricated')]
    for r in consumers:r.update(direction='S2C',phase='world-connection-1',source_runtime_connected=False,
        source_issuer_configured=False,server_request_pairing=None,complete_bidirectional_route=False,native_acceptance=False)
    dump('native/consumer-relations.json',dict(client_sha256=PIN,primary_tables=tables,consumers=consumers,
        high_address_recovery_used_as_primary=False,all_upstream_or_state_variants_closed=False))
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: sealed105-file deferred refresh source and catalog112',
        crossed_local_calendar_day=True,research_source_name_preserved='20261007',exact_native_consumer_record_views_added=3,
        native_fixed6D_header_operands_added=1,actual_owned31_and_resource68_source_readers_added=2,
        exact_existing_row31_projections_added=1,exact_resource68_lookup_operand_sources_added=1,
        existing_cn_world_endpoint_native_consumers_attached=3,
        native_function_envelopes_read=len(env['ranges']),native_metadata_bytes_read=env['metadata_bytes'],
        native_unique_bytes_read=len(covered),new_packet_values=0,new_native_phase_source_bindings=0,
        new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        source_issuer_configured=False,formal_application_hosted=False,levels_changed=False,common_storage_changed=False,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_reader_run=False,database_access=False,deployed=False,
        preserved_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_same_opcode_consumer_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN original WORLD31/68/6D retained records ->actual native UI/list/resource consumer operands',
        version_scope='cn-native-consumer-source-only',status='Readonly record/source projections; native/shared providers and gameplay handlers unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Continue formal CN account/admission issuer/native world provider source; native31/68/6D state/upstream/consumer providers remain open. No opcode pairing from equal values. Full numeric/gameplay/PC/web/WSS/denominator pending; PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN original WORLD31/68/6D consumers ('+ROUND+')\n\n'
            'Three exact29/13/29-byte records and actual UI=main+89B26C ownership recovered.31 uses first signedBYTE/WORD identity match and preserved1004B actual row;68 signed resource-count/one-based140B row lookup and native handle gates;6D original28B/page header, retained tail/text/UI dependencies still required. Added actualCurrent/revision/list/resource readonly source operands; attached native evidence to existing three WORLD endpoints without source binding/owner/full-route inflation. Ten envelopes15959B; no native/provider authority, invented stats/skills or request/reply pairing. All formal account/world/gameplay/numeric/hosting/denominator pending; no build/test/runtime/DB/deploy, levels/frozen state unchanged. See research/cn-same-opcode-consumer-source-20261007.md; date7 source filename retained for cross-midnight continuity.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data);origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','exact_native_consumer_record_views_added','native_function_envelopes_read','native_unique_bytes_read','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
