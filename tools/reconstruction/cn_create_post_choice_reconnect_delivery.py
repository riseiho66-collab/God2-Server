"""Retain file-only CN ordinary post18 reconnect and actual terminal-owner source."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, PIN

NAME='cn-create-post-choice-reconnect-01'
ROUND='20261007-cn-create-post-choice-reconnect'
SOURCES=('src/cn/auth/SharedPreWorldCloseReply.h','src/cn/auth/SharedWorldSelection.cpp',
    'tools/reconstruction/cn_create_post_choice_reconnect_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py',
    'docs/research/cn-create-post-choice-reconnect-20261007.md')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; preserve prior delivery')
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before receipt changed')
        if row['path'] not in SOURCES:
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Existing/frozen source changed')
            unchanged.append(row)
    index=json.loads((out/'native/index.json').read_text(encoding='utf-8'))
    if index['native_sha256']!=PIN or index['native_executed']:
        raise RuntimeError('Native provenance mismatch')
    for row in index['functions']:
        if sha((out/'native'/(row['entry']+'.bin')).read_bytes())!=row['sha256']:
            raise RuntimeError('Native span receipt changed')
    for name in ('cn-choice-common-position-cas-01','cn-close-producer-variants-01'):
        original=base/name
        # Older artifacts may use integration-manifest; find the actual sealed receipt.
        manifests=[p for p in (original/'manifest.json',original/'integration-manifest.json') if p.exists()]
        if len(manifests)!=1:raise RuntimeError('Require exact prior sealed receipt')
        manifest=json.loads(manifests[0].read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        raw=(original/'findings.json').read_bytes()
        if not manifest['sealed'] or sha(raw)!=pins['findings.json']:
            raise RuntimeError('Prior evidence changed')
        p=out/'retained-source'/name/'findings.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: actual common initial-position CAS wired through existing18, catalog83 sealed',
        'primary_metadata_function_envelopes_retained':len(index['functions']),
        'ordinary_post18_reconnect_chains_qualified_not_routes':1,
        'existing_pre_world_terminal_bindings_strengthened':1,'mutation_scope_identity_bindings_added':1,
        'new_packet_values':0,'new_source_owner_chains':0,'new_native_phase_source_bindings':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'existing_sources_unchanged':unchanged,'levels_changed':False,'build_run':False,
        'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'remaining':['Actual native full03 issuer, operation/replay authority and configured terminal drain/release host.',
            'Fresh account success/directory/A6 summary/selection and world00/1F providers must use actual common rows after ordinary creation.',
            'Standalone43D580 and other callers/phase variants; do not generalize ordinary reconnect to every18.',
            'Actual native choice-to-common spawn/full18 source, durable recovery, all gameplay and complete native denominator.']}
    relations={'ordinary_success18':[
        {'pc':'0043D494','call':'0047DB70','meaning':'wait complete18; success continuation'},
        {'pc':'0043D4A3..0043D4B4','meaning':'last active07 row19 low3 replaced, high5 retained'},
        {'pc':'0043D4BD/0043D4C1','meaning':'full reply firstBYTE zero-extended into UI selectionWORD'},
        {'pc':'0043D4D7','call':'00480B10','arguments':[2,0,1],'meaning':'actual world owner: C2S0200; wait03, timeout path separate'},
        {'pc':'0043D4EA','call':'0047F310','meaning':'actual account owner: C2S0A account16 then disconnect/clear active'},
        {'pc':'0043D4F3','call':'00440CA0','arguments':[2],'meaning':'retry count2; not a role selector'}],
        'fresh_both_inactive_chain':[
        {'pc':'00440CFF','call':'00448DC0','next':'00448E33->004468F0->004469BD->0047FE30','meaning':'account credentials, version200, complete1D/directory/0A waiter'},
        {'pc':'00440D0E','call':'00449060','next':'0044906E->00449310->00449363->00481640','meaning':'group/server selection and accountA6/full07'},
        {'pc':'00440D25','call':'004490F0','next':'0044915A->0047FAA0;00449175->0047E6C0(F0);004491A6->00444EC0','meaning':'world connect/version240/world00/complete1F'},
        {'pc':'00444F3E','call':'004814D0','meaning':'world00 using actual retained login'},
        {'pc':'00444F57','call':'0047E060','meaning':'complete1F barrier; no fabricated payload'}],
        'account_alive_world_inactive':'00440D76->00445B40 separate world reconnect path, not unconditional fresh account login',
        'standalone18':'0043D580 updates cached row/selection; no local close or440CA0 in bounded metadata function; callers remain open',
        'source_binding':'actual retained creation/deletion shared_ptr identity added to terminal Scope; checked before supplied03, queue and drain qualification',
        'identity_is_native_field':False,'mutation_kind_implies_native_reason_or_permission':False,
        'terminal_quiescent_rechecked_after_terminal_flag':False,
        'reply_contract':'mandatory full3-byte03 plus observing CurrentOperation for exact Scope, form and actual operation',
        'grant_update_added':False,'new_native_reply_issuer':False,
        'cfg_scope':'bounded metadata entry-rooted file decode; calls not followed automatically; explicit open edges; no loaded/whole-program closure'}
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:
        f.write('# CN ordinary post18 reconnect and designated terminal owner\n\n'
            'PHASE1 file/source work only. No builds, tests, native/server/SQL execution, migrations or deploy. Levels unchanged.\n\n'
            'Pinned CN43D280 ordinary17->18 success updates the last active raw07 row19 low3 and stores the full returned firstBYTE in the UI selectionWORD. At43D4D7 it closes the actual world through480B10(2,0,1), then at43D4EA disconnects the actual account through47F310 with notification, and at43D4F3 calls440CA0(2). The2 is an attempt count, not transport role.480B10 sends0200 and waits03; its timeout also clears flags, so a zero return alone is not receipt of03.47F310 sends C2S0A account16, not the unrelated S2C billing0A.\n\n'
            'With both native connections inactive,440CA0 calls448DC0(account credentials)->4468F0(version200)->47FE30(account response/directory waiter), then449060->449310->481640(A6/full07), then4490F0->47FAA0(world connect)->47E6C0(version240)->444EC0(world00 and complete1F). The account-alive/world-inactive branch calls445B40 separately. These branches must not be collapsed into a blanket reconnect rule.13 actual metadata function envelopes and exact file bytes/CFG are retained; attempted447FA0 has no metadata and is not counted. Calls are decoded file references, not runtime observations or automatically traversed complete functions.\n\n'
            'Standalone43D580 sends/waits18 and changes the same cached row/selection, but this bounded function contains no local world/account close or440CA0. Its upstream phase/pending owner is still open. The previous post18 in-place grant-refresh frontier is therefore narrowed: ordinary43D280 uses fresh account selection/world admission after reconnect; no newly created common ID may be inserted into an old grant merely to accept1A. Prior round reports stay unchanged; other variants require their own recovered lineage.\n\n'
            'Actual source change: SharedPreWorldCloseReply::Scope retains MutationKind and shared_ptr<const void> for the exact designated creation/deletion controller. None requires a null pointer, mutation kinds require a real pointer, and unknown kinds reject. SharedWorldSelection builds the Scope from its retained actual operation and checks that identity through native03 supplier, write and drain qualification; simultaneous mutation owners reject. This is serial source identity/lifetime, not a native field/reason/permission or durable replay token. Existing account/session/form checks and full3-byte03 plus mandatory CurrentOperation remain. Mutation suppliers must preserve the supplied Scope rather than reconstruct only account/session/form.\n\n'
            'Quiescence is checked before entering terminal stage. It is deliberately not queried again after terminal_started_: creation selection-current correctly excludes that stage. The retained pointer comparison prevents borrowing another operation without inventing new native success bytes. Committed deletion may invalidate the old07 offer, so terminal qualification continues to use the exact current world-owned ticket, not stale offer qualification. The terminal callback remains local TCP write completion, not native acceptance. Actual native03 authority, replay/operation policy and configured hosting are still missing.\n\n'
            'Existing create/choice/delete controllers, common admission, credential transport, Application, Session and login composition are unchanged. Increment: existing terminal binding strengthened1 and actual mutation identity binding1; ordinary reconnect chain qualified1. New packet/phase/owner/full-route counts0; whole-game total and percentage null. Fresh native account/07/world00/1F providers must reflect actual common post-creation rows. Choice/spawn/full18 authority, durable commit-versus-queue recovery, standalone variants and all gameplay remain open.\n')
    for name,value in (('findings.json',findings),('source-relations.json',relations)):
        with (out/name).open('x',encoding='utf-8') as f:f.write(json.dumps(value,indent=2)+'\n')
    for rel in SOURCES:
        p=out/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','primary_metadata_function_envelopes_retained','existing_pre_world_terminal_bindings_strengthened','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
