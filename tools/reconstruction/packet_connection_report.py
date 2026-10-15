"""Round-end source inventory. Reads files only; never runs gameplay or tests.

Ledger rows qualify specific branches, not every use of an opcode. The native
producer scan is a candidate index and cannot supply a whole-game denominator.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .archive_inputs import SERVER
from .packet_connection_inventory import source_index

ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
LEDGER = ROOT / 'packet-route-ledger.json'


def report(round_name, catalog_name=None, round_directory=None):
    destination = ROOT / 'round-reports'
    if round_directory is not None:
        requested = Path(round_directory)
        owned = (Path.home()/'.codex/artifact-archives/god2-server').resolve()
        if not requested.is_absolute() or not requested.resolve().is_relative_to(owned) or requested.resolve()==owned:
            raise ValueError('External round reports require an absolute owned archive subdirectory')
        destination = requested.resolve()
    ledger_raw = LEDGER.read_bytes()
    ledger = json.loads(ledger_raw.decode('utf-8'))
    # Counts come from the current segments, never the historical catalog
    # pointer retained in the ledger. Match the catalog's scoped tuple method.
    def phase_bindings(keys):
        return [(direction,phase,op) for segment in ledger.get('dual_client_source_segments',[])
                for direction,key in keys for phase,ops in segment.get(key,{}).items() for op in ops]
    cn_bindings = phase_bindings([('C2S','native_c2s_by_phase'),('S2C','native_s2c_by_phase')])
    tw_bindings = phase_bindings([('C2S','tw_native_c2s_by_phase'),('S2C','tw_native_s2c_by_phase')])
    current_phase_counts = {
        'cn_unhosted_phase_source_bindings':len(cn_bindings),
        'cn_unique_unhosted_phase_source_binding_values':len(set(cn_bindings)),
        'tw_unhosted_phase_source_bindings':len(tw_bindings),
        'tw_unique_unhosted_phase_source_binding_values':len(set(tw_bindings)),
    }
    current_catalog = None
    if catalog_name is not None:
        if not catalog_name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in catalog_name):
            raise ValueError('Catalog name must be a simple file stem')
        catalog_index = ROOT / catalog_name
        catalog = catalog_index
        external_metadata=False
        if (catalog_index/'external-catalog.json').exists():
            pointer=json.loads((catalog_index/'external-catalog.json').read_bytes())
            owned=(Path.home()/'.codex/artifact-archives/god2-server').resolve()
            requested=Path(pointer['root'])
            if not requested.is_absolute() or not requested.resolve().is_relative_to(owned) or requested.resolve()==owned or pointer.get('round')!=catalog_name:
                raise ValueError('External catalog metadata requires its exact owned round index')
            catalog=requested.resolve()
            names={'summary.json','input-manifest.json','source-file-manifest.json','external-archive-manifest.json','catalog-tool.py'}
            rows=pointer.get('files',[])
            if not pointer.get('verified') or not pointer.get('original_bytes_retained') or len(rows)!=len(names) or {r['path'] for r in rows}!=names:
                raise ValueError('External catalog index must pin all five full metadata originals')
            if any((catalog_index/name).exists() for name in names):raise ValueError('Ambiguous local and external catalog metadata')
            for row in rows:
                raw=(catalog/row['path']).read_bytes()
                if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
                    raise ValueError('External catalog full metadata original differs')
            external_metadata=True
        summary_raw = (catalog/'summary.json').read_bytes()
        manifest_raw = (catalog/'input-manifest.json').read_bytes()
        rows = [row for row in json.loads(manifest_raw) if row['input']=='source-ledger']
        if len(rows)!=1:
            raise ValueError('Catalog must retain exactly one source ledger snapshot')
        snapshot=Path(rows[0]['snapshot'])
        if snapshot.is_absolute():
            owned=(Path.home()/'.codex/artifact-archives/god2-server').resolve()
            archive=json.loads((catalog/'external-archive-manifest.json').read_bytes())
            archive_root=Path(archive['root']).resolve()
            if not archive_root.is_relative_to(owned) or archive_root==owned or not snapshot.resolve().is_relative_to(archive_root):
                raise ValueError('Catalog ledger is outside its owned full archive')
            references=[r for r in archive['files'] if Path(r['path'])==snapshot]
            if not archive.get('verified') or not archive.get('original_bytes_retained') or len(references)!=1 or any(references[0][k]!=rows[0][k] for k in ['bytes','sha256']):
                raise ValueError('Catalog must pin the complete external ledger original')
        elif snapshot.as_posix()!='inputs/source-ledger.json':
            raise ValueError('Invalid local source ledger snapshot')
        retained_ledger = (catalog/snapshot).read_bytes()
        if len(retained_ledger)!=rows[0]['bytes']:
            raise ValueError('Catalog ledger byte count differs')
        if retained_ledger!=ledger_raw or rows[0]['sha256']!=hashlib.sha256(ledger_raw).hexdigest():
            raise ValueError('Catalog does not describe the current source ledger')
        summary = json.loads(summary_raw)
        if any(summary.get(key)!=value for key,value in current_phase_counts.items()):
            raise ValueError('Catalog and current source segment accounting disagree')
        current_catalog = {'root':str(catalog) if external_metadata else catalog.relative_to(SERVER).as_posix(),'summary':summary,
            'summary_sha256':hashlib.sha256(summary_raw).hexdigest(),
            'input_manifest_sha256':hashlib.sha256(manifest_raw).hexdigest(),
            'current_ledger_snapshot_matched':True}
        if external_metadata:
            current_catalog.update(index=catalog_index.relative_to(SERVER).as_posix(),external_metadata_full_originals_verified=True)
    index_path = ROOT / 'static-packet-index.json'
    native = json.loads(index_path.read_text(encoding='utf-8'))
    wrapper_path = ROOT / 'c2s-wrapper-census-v1.json'
    wrapper = json.loads(wrapper_path.read_text(encoding='utf-8'))
    wrapper_frontier_path = ROOT / 'c2s-wrapper-frontier-v1.json'
    wrapper_frontier = json.loads(wrapper_frontier_path.read_text(encoding='utf-8'))
    s2c_frontier_path = ROOT / 's2c-world-consumer-frontier-v27.json'
    s2c_frontier = json.loads(s2c_frontier_path.read_text(encoding='utf-8'))
    battle_frontier_path = ROOT / 's2c-battle-dispatch-frontier-v1.json'
    battle_frontier = json.loads(battle_frontier_path.read_text(encoding='utf-8'))
    battle83_path = ROOT / 's2c-battle83-action-frontier-v1.json'
    battle83 = json.loads(battle83_path.read_text(encoding='utf-8'))
    daily_bf_path = ROOT / 'daily-bf-purchase-producer-v2.json'
    daily_bf = json.loads(daily_bf_path.read_text(encoding='utf-8'))
    if wrapper['native_sha256'] != native['native_sha256'] or \
       wrapper['direct_wrapper_call_sites'] != len(native['c2s_known_wrapper_call_candidates']) or \
       wrapper_frontier['native_sha256'] != native['native_sha256'] or \
       s2c_frontier['native_sha256'] != native['native_sha256'] or \
       s2c_frontier['baseline_index_sha256'] != hashlib.sha256(index_path.read_bytes()).hexdigest() or \
       battle_frontier['native_sha256'] != native['native_sha256'] or \
       battle_frontier['world_index_sha256'] != hashlib.sha256(index_path.read_bytes()).hexdigest() or \
       battle83['native_sha256'] != native['native_sha256'] or \
       battle83['battle_outer_dispatch_sha256'] != hashlib.sha256(battle_frontier_path.read_bytes()).hexdigest() or \
       daily_bf['native_sha256'] != native['native_sha256'] or \
       daily_bf['distinct_known_bf_producer_branches'] != 4 or \
       daily_bf['dialog_jump_target_rva'] != '8433D' or \
       daily_bf['queue_target_rva'] != '132E0':
        raise ValueError('Native wrapper census and base packet index disagree')
    # The native frontier is immutable evidence from an earlier ledger revision.
    # A new C2S-only pending row may change the ledger digest without changing
    # the S2C classification. Reject any stale S2C classification explicitly.
    reviewed_s2c = {op for row in ledger['reviewed_world_source_groups'] for op in row['s2c']}
    pending_s2c = {op for row in ledger.get('pending_world_source_groups', [])
                   for op in row.get('s2c_format_only', [])}
    independent_s2c = set(ledger.get('independent_s2c_format_only', {}))
    external_bridge_s2c = set(ledger.get('external_s2c_bridge_format_only', {}))
    source_push_s2c = set(ledger.get('source_s2c_push_branches', {}))
    config_gated_push_s2c = set(ledger.get('config_gated_s2c_visibility_push_branches', {}))
    for entry in s2c_frontier['entries']:
        if entry['dispatch_class'] not in ('DEFAULT', 'NONDEFAULT'):
            continue
        op = entry['opcode']
        expected = [name for name, present in (
            ('REGISTERED_SOURCE_REPLY_OPCODE', op in reviewed_s2c),
            ('PENDING_FORMAT_ONLY', op in pending_s2c),
            ('INDEPENDENT_FORMAT_ONLY', op in independent_s2c),
            ('GM_TOOL_BRIDGE_FORMAT_ONLY', op in external_bridge_s2c),
            ('REGISTERED_SOURCE_PUSH_BRANCH', op in source_push_s2c),
            ('CONFIG_GATED_VISIBILITY_PUSH_BRANCH', op in config_gated_push_s2c)) if present]
        if entry['ledger_classifications'] != expected:
            raise ValueError('S2C frontier classification changed; create a new frontier artifact')
    direct_ops = set(native['direct_argument_opcode_candidates'])
    wrapper_ops = {int(x, 16) for x in wrapper['wrapper_argument_opcode_candidates']}
    known_argument_ops = direct_ops | wrapper_ops
    _, parser = source_index()
    parsed = {f'{x:02X}' for x in parser}
    candidate_not_world_parser = sorted(known_argument_ops - set(parser))
    world_parser_not_candidate = sorted(set(parser) - known_argument_ops)
    supplemental_path = ROOT / 'tw-supplemental-producers-01/summary.json'
    supplemental = json.loads(supplemental_path.read_text(encoding='utf-8'))
    if supplemental['native_sha256'] != native['native_sha256']:
        raise ValueError('Supplemental producer evidence is from a different native build')
    supplemental_ops = {int(x, 16) for x in supplemental['supplemental_opcode_values']}
    groups = ledger['reviewed_world_source_groups']
    pending_groups = ledger.get('pending_world_source_groups', [])
    linked = sorted({x for row in groups for x in row['c2s']})
    replies = sorted({x for row in groups for x in row['s2c']})
    controls = ledger['world_control_or_diagnostic_opcodes']
    gaps = ledger['world_unconnected_gameplay_opcodes']
    paths = sorted({p for row in groups + pending_groups for p in row['source_paths']} |
                   {p for row in ledger.get('dual_client_source_segments', []) for p in row['source_paths']} |
                   set(ledger.get('tw_native_pet2_e5_update326', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_e5_family_source327', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_e6_petegg_input_source328', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_petegg_selection_source329', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_petegg_deferred_source330', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_petegg_e7_list_input_source331', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_ui_byte_updates_source332', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_9c_and_petegg_list_boundaries333', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_f4_list_writer_and_web_handoff334', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_petroom_catalog_source335', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_petroom_spi_raw_source336', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_spi_definition_text337', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_spi_offsets_and_scalars338', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_rommaps_spi_resource339', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_spi_conditional_record340', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_petegg_local_state_source341', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_petroom_presend_storage_source342', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_c24_fullbank_alias_source343', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_c24_normal_entry_source344', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_normal_entry_movement_custody_source345', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_owned_mutation_response_custody_source346', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_normal_entry_readiness_authority_source347', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_catalog_material_helper_source348', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_item_helper_output_ui_source349', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_item_ui_acquisition_seam_source350', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_item_ui_blacklist_owner_source351', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_item_row_alias_blacklist_chain_source352', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_item_writer_original_response_source353', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_world_control_authority_frontier_source354', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_route_authority_source355', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_party_preview_transport_source356', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_party_callback_admission_source357', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_party_lifetime_source358', {}).get('source_paths', [])) |
                   set(ledger.get('tw_cn_shared_skill_source359', {}).get('source_paths', [])) |
                   set(ledger.get('tw_cn_common_owner_skill_definition_source360', {}).get('source_paths', [])) |
                   set(ledger.get('tw_cn_common_owned_skill_commit_source361', {}).get('source_paths', [])) |
                   set(ledger.get('tw_cn_owned_skill_bootstrap_write_source362', {}).get('source_paths', [])) |
                   set(ledger.get('tw_cn_owned_skill_input_continuation_source363', {}).get('source_paths', [])) |
                   set(ledger.get('tw_cn_common_skill_command_source364', {}).get('source_paths', [])) |
                   set(ledger.get('tw_common_skill_command_source365', {}).get('source_paths', [])) |
                   set(ledger.get('tw_world_skill_request_source366', {}).get('source_paths', [])) |
                   set(ledger.get('tw_selected_deity_common_skill_source367', {}).get('source_paths', [])) |
                   set(ledger.get('tw_world_skill_self_target_source368', {}).get('source_paths', [])) |
                   set(ledger.get('tw_deity_selection_commit_source369', {}).get('source_paths', [])) |
                   set(ledger.get('tw_deity_selection_publication_source370', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_world_skill_menu_event_source371', {}).get('source_paths', [])) |
                   set(ledger.get('tw_owned_item_presence_source372', {}).get('source_paths', [])) |
                   set(ledger.get('tw_preborn_input_source373', {}).get('source_paths', [])) |
                   set(ledger.get('tw_preborn_issuer_presence_source374', {}).get('source_paths', [])) |
                   set(ledger.get('tw_cn_preborn_grammar_source375', {}).get('source_paths', [])) |
                   set(ledger.get('preborn_current_source376', {}).get('source_paths', [])) |
                   set(ledger.get('tw_preborn_window_owner_source377', {}).get('source_paths', [])) |
                   set(ledger.get('tw_skillbook_use_source378', {}).get('source_paths', [])) |
                   set(ledger.get('tw_skill_command_presence_source379', {}).get('source_paths', [])) |
                   set(ledger.get('tw_skillbook_target_source380', {}).get('source_paths', [])) |
                   set(ledger.get('tw_skillbook_learning_source381', {}).get('source_paths', [])) |
                   set(ledger.get('tw_common_world_skill_restoration_source382', {}).get('source_paths', [])) |
                   set(ledger.get('tw_skillbook_shortcut_source383', {}).get('source_paths', [])) |
                   set(ledger.get('tw_battle_return_source384', {}).get('source_paths', [])) |
                   set(ledger.get('tw_paired_return_reservation_source385', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_record_publication_source386', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_output_hold_source387', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_consume_source388', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_write_source389', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_finish_source390', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_backend_lifecycle391', {}).get('source_paths', [])) |
                   set(ledger.get('tw_pk_native_identity392', {}).get('source_paths', [])) |
                   set(ledger.get('tw_pk_companion_whole393', {}).get('source_paths', [])) |
                   set(ledger.get('tw_pk_learning_closed394', {}).get('source_paths', [])) |
                   set(ledger.get('tw_initial_player395', {}).get('source_paths', [])) |
                   set(ledger.get('tw_pk_player_source396', {}).get('source_paths', [])) |
                   set(ledger.get('tw_pk_main_host397', {}).get('source_paths', [])) |
                   set(ledger.get('tw_pk_zero_deity398', {}).get('source_paths', [])) |
                   set(ledger.get('tw_learning_publication399', {}).get('source_paths', [])) |
                   set(ledger.get('tw_learning_pk_successor403', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_return_actor_field404', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_actor_override405', {}).get('source_paths', [])) |
                   set(ledger.get('tw_receiver_selector406', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_resource_bank407', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_native_lookup408', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_actor_saved409', {}).get('source_paths', [])) |
                   set(ledger.get('tw_return_profile_input410', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_native_arguments412', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_resources413', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_status_write_fence415', {}).get('source_paths', [])) |
                   set(ledger.get('mysql80_dictionary_format416', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_status_pending_writer417', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_status_incarnation418', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_status_profile_scope419', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_drv_fifth420', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_status_owned421', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_status_publication422', {}).get('source_paths', [])) |
                   set(ledger.get('tw_actor_drv_doll_tail423', {}).get('source_paths', [])) |
                   set(ledger.get('tw_native_route_assembly424', {}).get('source_paths', [])) |
                   set(ledger.get('tw_initial_scene_multiframe425', {}).get('source_paths', [])) |
                   set(ledger.get('tw_world_display_readset426', {}).get('source_paths', [])) |
                   set(ledger.get('tw_initial_population427', {}).get('source_paths', [])) |
                   set(ledger.get('tw_post_install_outward428', {}).get('source_paths', [])) |
                   set(ledger.get('tw_initial_saved_input429', {}).get('source_paths', [])) |
                   set(ledger.get('tw_full_actor_profile411', {}).get('source_paths', [])) |
                   set(ledger.get('tw_installed453_operator402', {}).get('source_paths', [])) |
                   set(ledger.get('tw_installed453_import401', {}).get('source_paths', [])) |
                   set(ledger.get('tw_installed453_profile400', {}).get('source_paths', [])) |
                   {'src/core/Application.cpp', 'src/protocol/RecoveredWorldRecords.h'})
    # A missing file is a report error, never silent qualification/completion.
    digests = {p: hashlib.sha256((SERVER / p).read_bytes()).hexdigest() for p in paths}
    counts = {
        's2c_length_entries': len(native['s2c']),
        's2c_fixed_length_opcodes': sum(x['length_kind'] == 'fixed' for x in native['s2c']),
        's2c_variable_length_opcodes': sum(x['length_kind'] == 'u16_variable' for x in native['s2c']),
        's2c_supported_length_opcodes': sum(x['length_kind'] in ('fixed', 'u16_variable') for x in native['s2c']),
        **s2c_frontier['counts'],
        **battle_frontier['counts'],
        **battle83['counts'],
        's2c83_action_values_outside_qualified_scalar_projection':
            battle83['counts']['s2c83_table_action_values'] -
            battle83['counts']['s2c83_scalar_attack_projection_qualified_actions'],
        's2c_world_or_battle_specialized_opcode_union':
            s2c_frontier['counts']['s2c_supported_nondefault_world_dispatch_entries'] +
            battle_frontier['counts']['battle_specialized_that_are_world_default'],
        'c2s_direct_queue_call_candidates': len(native['c2s_direct_queue_candidates']),
        'c2s_wrapper_call_candidates': len(native['c2s_known_wrapper_call_candidates']),
        'c2s_direct_argument_opcode_candidates': len(native['direct_argument_opcode_candidates']),
        'c2s_wrapper_argument_opcode_candidates': len(wrapper_ops),
        'c2s_bf_known_producer_branches': daily_bf['distinct_known_bf_producer_branches'],
        'c2s_bf_shared_queue_producer_branches': 1,
        'c2s_known_argument_opcode_candidates': len(known_argument_ops),
        'c2s_generic_plus_supplemental_opcode_union': len(known_argument_ops | supplemental_ops),
        'c2s_supplemental_native_branch_records': supplemental['supplemental_native_branch_records'],
        'world_parser_opcodes_without_generic_or_supplemental_evidence': len(set(parser) - known_argument_ops - supplemental_ops),
        'c2s_known_argument_candidates_in_world_parser': len(known_argument_ops & set(parser)),
        'c2s_known_argument_candidates_outside_world_parser': len(candidate_not_world_parser),
        'world_parser_opcodes_not_in_known_argument_candidates': len(world_parser_not_candidate),
        'c2s_secondary_35_raw_variant_candidates': 1 if wrapper_frontier.get('c2s35_raw_candidate') else 0,
        'world_c2s_parser_opcodes': len(parsed),
        'world_c2s_with_reviewed_source_branch': len(linked),
        'world_parser_opcode_scoped_branch_coverage_percent': round(100 * len(linked) / len(parsed), 1) if parsed else None,
        'reviewed_world_source_groups': len(groups),
        'pending_world_source_groups': len(pending_groups),
        'reviewed_s2c_reply_opcode_lower_bound': len(replies),
        'world_control_or_diagnostic_opcodes': len(controls),
        'world_unconnected_gameplay_opcodes': len(gaps),
        'world_parser_opcodes_without_ledger_classification': len(parsed - set(linked) - set(controls) - set(gaps)),
        'ledger_opcodes_absent_from_world_parser': len((set(linked) | set(controls) | set(gaps)) - parsed),
        'whole_game_distinct_packet_count': None,
        'whole_game_completed_route_count': None,
        'whole_game_completion_percent': None,
        'current_source_phase_new_deployments': 0,
        'cn_unhosted_partial_owner_chains': sum(x.get('source_owner_chains_added',0)
                                               for x in ledger.get('dual_client_source_segments',[])),
        'tw_unhosted_partial_owner_chains':sum(x.get('tw_source_owner_chains_added',0) for x in ledger.get('dual_client_source_segments',[])),
        'dual_client_unhosted_partial_owner_chains':sum(x.get('source_owner_chains_added',0)+x.get('tw_source_owner_chains_added',0)
            for x in ledger.get('dual_client_source_segments',[])),
        **current_phase_counts,
    }
    latest = ROOT / 'packet-progress-latest.json'
    prior = json.loads(latest.read_text(encoding='utf-8')) if latest.exists() else None
    delta = {k: v - prior['counts'][k] for k, v in counts.items()
             if isinstance(v, int) and prior and isinstance(prior['counts'].get(k), int)}
    if prior:
        # Earlier reports kept these qualified partial-source counts outside
        # counts. Read that actual prior evidence instead of implying all are new.
        previous_partial={
            'cn_unhosted_partial_owner_chains':prior.get('cn_shared_admission_owner_chains_in_source'),
            'cn_unhosted_phase_source_bindings':(prior.get('dual_client_endpoint_catalog') or {}).get('summary',{}).get('cn_unhosted_phase_source_bindings'),
            'cn_unique_unhosted_phase_source_binding_values':(prior.get('dual_client_endpoint_catalog') or {}).get('summary',{}).get('cn_unique_unhosted_phase_source_binding_values'),
        }
        for key,value in previous_partial.items():
            if key not in prior['counts'] and isinstance(value,int):delta[key]=counts[key]-value
        # TW associations already existed in the sealed prior source segments.
        # Derive their old count without modifying that report or implying all
        # seven are new in the first report exposing these columns.
        previous_tw=[(direction,phase,op) for segment in prior.get('dual_client_source_segments',[])
            for direction,key in [('C2S','tw_native_c2s_by_phase'),('S2C','tw_native_s2c_by_phase')]
            for phase,ops in segment.get(key,{}).items() for op in ops]
        for key,value in [('tw_unhosted_phase_source_bindings',len(previous_tw)),
            ('tw_unique_unhosted_phase_source_binding_values',len(set(previous_tw)))]:
            if key not in prior['counts']:delta[key]=counts[key]-value
    if prior and 'c2s_wrapper_argument_opcode_candidates' not in prior['counts']:
        delta['c2s_wrapper_argument_opcode_candidates'] = len(wrapper_ops)
        delta['c2s_known_argument_opcode_candidates'] = len(direct_ops | wrapper_ops) - len(direct_ops)
    if prior and 'c2s_secondary_35_raw_variant_candidates' not in prior['counts']:
        delta['c2s_secondary_35_raw_variant_candidates'] = counts['c2s_secondary_35_raw_variant_candidates']
    if prior and 'c2s_bf_known_producer_branches' not in prior['counts']:
        # The previous native BF census had three direct callers; this adds
        # one daily dialog32 branch through a previously shared queue call.
        delta['c2s_bf_known_producer_branches'] = counts['c2s_bf_known_producer_branches'] - 3
        delta['c2s_bf_shared_queue_producer_branches'] = 1
    if prior and 's2c_nondefault_external_tool_bridge_format_only_opcodes' not in prior['counts']:
        delta['s2c_nondefault_external_tool_bridge_format_only_opcodes'] = counts['s2c_nondefault_external_tool_bridge_format_only_opcodes']
    for key in ('s2c_nondefault_source_push_branch_opcodes',
                's2c_nondefault_config_gated_visibility_push_branch_opcodes'):
        if prior and key not in prior['counts']:
            delta[key] = counts[key]
    result = {
        'format': 'god2-round-packet-progress-v4', 'round': round_name,
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'method': 'STATIC_SOURCE_REVIEW_AND_PINNED_NATIVE_FORMAT_INDEX',
        'phase': 'CONNECT_ALL_ROUTES_FIRST', 'goal': 'INCOMPLETE',
        'goal_api_status': ledger.get('dual_client_execution_plan',{}).get('actual_goal_api_status'),
        'native_sha256': native['native_sha256'],
        'native_index_sha256': hashlib.sha256(index_path.read_bytes()).hexdigest(),
        'native_wrapper_census_sha256': hashlib.sha256(wrapper_path.read_bytes()).hexdigest(),
        'native_wrapper_frontier_sha256': hashlib.sha256(wrapper_frontier_path.read_bytes()).hexdigest(),
        'native_s2c_world_consumer_frontier_sha256': hashlib.sha256(s2c_frontier_path.read_bytes()).hexdigest(),
        'native_s2c_battle_dispatch_frontier_sha256': hashlib.sha256(battle_frontier_path.read_bytes()).hexdigest(),
        'native_s2c_battle83_action_frontier_sha256': hashlib.sha256(battle83_path.read_bytes()).hexdigest(),
        'native_daily_bf_producer_sha256': hashlib.sha256(daily_bf_path.read_bytes()).hexdigest(),
        'native_supplemental_producer_summary_sha256': hashlib.sha256(supplemental_path.read_bytes()).hexdigest(),
        'route_ledger_sha256': hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
        'counts': counts, 'delta_from_previous_report': delta if prior else None,
        'previous_round': prior['round'] if prior else None,
        'world_c2s_parser_opcodes': sorted(parsed),
        'c2s_known_argument_candidates_outside_world_parser':
            [f'{x:02X}' for x in candidate_not_world_parser],
        'world_parser_opcodes_not_in_known_argument_candidates':
            [f'{x:02X}' for x in world_parser_not_candidate],
        'c2s_wrapper_argument_opcodes': [f'{x:02X}' for x in sorted(wrapper_ops)],
        's2c_nondefault_without_route_ledger_classification':
            s2c_frontier['frontier_nondefault_opcodes'],
        's2c_battle_specialized_opcode_cases': battle_frontier['specialized_opcode_cases'],
        's2c_battle_86_subtype_cases': battle_frontier['battle_86_subtype_cases'],
        's2c_battle83_action_cases': battle83['actions'],
        'independent_s2c_format_only': ledger.get('independent_s2c_format_only', {}),
        'external_s2c_bridge_format_only': ledger.get('external_s2c_bridge_format_only', {}),
        'source_s2c_push_branches': ledger.get('source_s2c_push_branches', {}),
        'config_gated_s2c_visibility_push_branches': ledger.get('config_gated_s2c_visibility_push_branches', {}),
        'world_c2s_with_reviewed_source_branch': linked,
        'reviewed_s2c_reply_opcodes': replies,
        'source_groups': groups, 'control_or_diagnostic': controls,
        'pending_source_groups': pending_groups,
        'unconnected_gameplay': gaps,
        'outside_world_parser_open': ledger['outside_world_parser_open'],
        'frozen_pre_world_source_routes': ledger['frozen_pre_world_source_routes'],
        'dual_client_native_inventory': ledger.get('dual_client_native_inventory'),
        'dual_client_source_segments': ledger.get('dual_client_source_segments', []),
        'tw_owned_inventory_reply234': ledger.get('tw_owned_inventory_reply234'),
        'tw_item_definition235': ledger.get('tw_item_definition235'),
        'tw_deity_equipment236': ledger.get('tw_deity_equipment236'),
        'dual_client_endpoint_catalog': current_catalog,
        'historical_ledger_endpoint_catalog': ledger.get('dual_client_endpoint_catalog'),
        'phase_source_counts_method':'CURRENT_LEDGER_DIRECTION_PHASE_OPCODE_TUPLES',
        'tw_native_equipment_request_context324': ledger.get('tw_native_equipment_request_context324'),
        'tw_owned_quantity64_equipment_state325': ledger.get('tw_owned_quantity64_equipment_state325'),
        'tw_native_pet2_e5_update326': ledger.get('tw_native_pet2_e5_update326'),
        'tw_native_e5_family_source327': ledger.get('tw_native_e5_family_source327'),
        'tw_native_e6_petegg_input_source328': ledger.get('tw_native_e6_petegg_input_source328'),
        'tw_native_petegg_selection_source329': ledger.get('tw_native_petegg_selection_source329'),
        'tw_native_petegg_deferred_source330': ledger.get('tw_native_petegg_deferred_source330'),
        'tw_native_petegg_e7_list_input_source331': ledger.get('tw_native_petegg_e7_list_input_source331'),
        'tw_native_ui_byte_updates_source332': ledger.get('tw_native_ui_byte_updates_source332'),
        'tw_native_9c_and_petegg_list_boundaries333': ledger.get('tw_native_9c_and_petegg_list_boundaries333'),
        'tw_native_f4_list_writer_and_web_handoff334': ledger.get('tw_native_f4_list_writer_and_web_handoff334'),
        'tw_native_petroom_catalog_source335': ledger.get('tw_native_petroom_catalog_source335'),
        'tw_native_petroom_spi_raw_source336': ledger.get('tw_native_petroom_spi_raw_source336'),
        'tw_native_spi_definition_text337': ledger.get('tw_native_spi_definition_text337'),
        'tw_native_spi_offsets_and_scalars338': ledger.get('tw_native_spi_offsets_and_scalars338'),
        'tw_native_rommaps_spi_resource339': ledger.get('tw_native_rommaps_spi_resource339'),
        'tw_native_spi_conditional_record340': ledger.get('tw_native_spi_conditional_record340'),
        'tw_native_petegg_local_state_source341': ledger.get('tw_native_petegg_local_state_source341'),
        'tw_native_petroom_presend_storage_source342': ledger.get('tw_native_petroom_presend_storage_source342'),
        'tw_native_c24_fullbank_alias_source343': ledger.get('tw_native_c24_fullbank_alias_source343'),
        'tw_native_c24_normal_entry_source344': ledger.get('tw_native_c24_normal_entry_source344'),
        'tw_native_normal_entry_movement_custody_source345': ledger.get('tw_native_normal_entry_movement_custody_source345'),
        'tw_native_owned_mutation_response_custody_source346': ledger.get('tw_native_owned_mutation_response_custody_source346'),
        'tw_native_normal_entry_readiness_authority_source347': ledger.get('tw_native_normal_entry_readiness_authority_source347'),
        'tw_native_catalog_material_helper_source348': ledger.get('tw_native_catalog_material_helper_source348'),
        'tw_native_item_helper_output_ui_source349': ledger.get('tw_native_item_helper_output_ui_source349'),
        'tw_native_item_ui_acquisition_seam_source350': ledger.get('tw_native_item_ui_acquisition_seam_source350'),
        'tw_native_item_ui_blacklist_owner_source351': ledger.get('tw_native_item_ui_blacklist_owner_source351'),
        'tw_native_item_row_alias_blacklist_chain_source352': ledger.get('tw_native_item_row_alias_blacklist_chain_source352'),
        'tw_native_item_writer_original_response_source353': ledger.get('tw_native_item_writer_original_response_source353'),
        'tw_native_world_control_authority_frontier_source354': ledger.get('tw_native_world_control_authority_frontier_source354'),
        'tw_native_route_authority_source355': ledger.get('tw_native_route_authority_source355'),
        'tw_native_party_preview_transport_source356': ledger.get('tw_native_party_preview_transport_source356'),
        'tw_native_party_callback_admission_source357': ledger.get('tw_native_party_callback_admission_source357'),
        'tw_native_party_lifetime_source358': ledger.get('tw_native_party_lifetime_source358'),
        'tw_cn_shared_skill_source359': ledger.get('tw_cn_shared_skill_source359'),
        'tw_cn_common_owner_skill_definition_source360': ledger.get('tw_cn_common_owner_skill_definition_source360'),
        'tw_cn_common_owned_skill_commit_source361': ledger.get('tw_cn_common_owned_skill_commit_source361'),
        'tw_cn_owned_skill_bootstrap_write_source362': ledger.get('tw_cn_owned_skill_bootstrap_write_source362'),
        'tw_cn_owned_skill_input_continuation_source363': ledger.get('tw_cn_owned_skill_input_continuation_source363'),
        'tw_cn_common_skill_command_source364': ledger.get('tw_cn_common_skill_command_source364'),
        'tw_common_skill_command_source365': ledger.get('tw_common_skill_command_source365'),
        'tw_world_skill_request_source366': ledger.get('tw_world_skill_request_source366'),
        'tw_selected_deity_common_skill_source367': ledger.get('tw_selected_deity_common_skill_source367'),
        'tw_world_skill_self_target_source368': ledger.get('tw_world_skill_self_target_source368'),
        'tw_deity_selection_commit_source369': ledger.get('tw_deity_selection_commit_source369'),
        'tw_deity_selection_publication_source370': ledger.get('tw_deity_selection_publication_source370'),
        'tw_native_world_skill_menu_event_source371': ledger.get('tw_native_world_skill_menu_event_source371'),
        'tw_owned_item_presence_source372': ledger.get('tw_owned_item_presence_source372'),
        'tw_preborn_input_source373': ledger.get('tw_preborn_input_source373'),
        'tw_preborn_issuer_presence_source374': ledger.get('tw_preborn_issuer_presence_source374'),
        'tw_cn_preborn_grammar_source375': ledger.get('tw_cn_preborn_grammar_source375'),
        'preborn_current_source376': ledger.get('preborn_current_source376'),
        'tw_preborn_window_owner_source377': ledger.get('tw_preborn_window_owner_source377'),
        'tw_skillbook_use_source378': ledger.get('tw_skillbook_use_source378'),
        'tw_skill_command_presence_source379': ledger.get('tw_skill_command_presence_source379'),
        'tw_skillbook_target_source380': ledger.get('tw_skillbook_target_source380'),
        'tw_skillbook_learning_source381': ledger.get('tw_skillbook_learning_source381'),
        'tw_common_world_skill_restoration_source382': ledger.get('tw_common_world_skill_restoration_source382'),
        'tw_skillbook_shortcut_source383': ledger.get('tw_skillbook_shortcut_source383'),
        'tw_battle_return_source384': ledger.get('tw_battle_return_source384'),
        'tw_paired_return_reservation_source385': ledger.get('tw_paired_return_reservation_source385'),
        'tw_return_record_publication_source386': ledger.get('tw_return_record_publication_source386'),
        'tw_return_output_hold_source387': ledger.get('tw_return_output_hold_source387'),
        'tw_return_consume_source388': ledger.get('tw_return_consume_source388'),
        'tw_return_write_source389': ledger.get('tw_return_write_source389'),
        'tw_return_finish_source390': ledger.get('tw_return_finish_source390'),
        'tw_return_backend_lifecycle391': ledger.get('tw_return_backend_lifecycle391'),
        'tw_pk_native_identity392': ledger.get('tw_pk_native_identity392'),
        'tw_pk_companion_whole393': ledger.get('tw_pk_companion_whole393'),
        'tw_pk_learning_closed394': ledger.get('tw_pk_learning_closed394'),
        'tw_initial_player395': ledger.get('tw_initial_player395'),
        'tw_pk_player_source396': ledger.get('tw_pk_player_source396'),
        'tw_pk_main_host397': ledger.get('tw_pk_main_host397'),
        'tw_pk_zero_deity398': ledger.get('tw_pk_zero_deity398'),
        'tw_learning_publication399': ledger.get('tw_learning_publication399'),
        'tw_learning_pk_successor403': ledger.get('tw_learning_pk_successor403'),
        'tw_native_return_actor_field404': ledger.get('tw_native_return_actor_field404'),
        'tw_return_actor_override405': ledger.get('tw_return_actor_override405'),
        'tw_receiver_selector406': ledger.get('tw_receiver_selector406'),
        'tw_actor_resource_bank407': ledger.get('tw_actor_resource_bank407'),
        'tw_actor_native_lookup408': ledger.get('tw_actor_native_lookup408'),
        'tw_return_actor_saved409': ledger.get('tw_return_actor_saved409'),
        'tw_return_profile_input410': ledger.get('tw_return_profile_input410'),
        'tw_actor_native_arguments412': ledger.get('tw_actor_native_arguments412'),
        'tw_actor_resources413': ledger.get('tw_actor_resources413'),
        'tw_actor_status_write_fence415': ledger.get('tw_actor_status_write_fence415'),
        'mysql80_dictionary_format416': ledger.get('mysql80_dictionary_format416'),
        'tw_actor_status_pending_writer417': ledger.get('tw_actor_status_pending_writer417'),
        'tw_actor_status_incarnation418': ledger.get('tw_actor_status_incarnation418'),
        'tw_actor_status_profile_scope419': ledger.get('tw_actor_status_profile_scope419'),
        'tw_actor_drv_fifth420': ledger.get('tw_actor_drv_fifth420'),
        'tw_actor_status_owned421': ledger.get('tw_actor_status_owned421'),
        'tw_actor_status_publication422': ledger.get('tw_actor_status_publication422'),
        'tw_actor_drv_doll_tail423': ledger.get('tw_actor_drv_doll_tail423'),
        'tw_native_route_assembly424': ledger.get('tw_native_route_assembly424'),
        'tw_initial_scene_multiframe425': ledger.get('tw_initial_scene_multiframe425'),
        'tw_world_display_readset426': ledger.get('tw_world_display_readset426'),
        'tw_initial_population427': ledger.get('tw_initial_population427'),
        'tw_post_install_outward428': ledger.get('tw_post_install_outward428'),
        'tw_initial_saved_input429': ledger.get('tw_initial_saved_input429'),
        'tw_full_actor_profile411': ledger.get('tw_full_actor_profile411'),
        'tw_installed453_operator402': ledger.get('tw_installed453_operator402'),
        'tw_installed453_import401': ledger.get('tw_installed453_import401'),
        'tw_installed453_profile400': ledger.get('tw_installed453_profile400'),
        'current_catalog_supplied':current_catalog is not None,
        'tw_supplemental_producer_evidence': ledger.get('tw_supplemental_producer_evidence'),
        'cn_unresolved_receiver_evidence': ledger.get('cn_unresolved_receiver_evidence'),
        'cn_account_admission_evidence': ledger.get('cn_account_admission_evidence'),
        'cn_shared_admission_owner_chains_in_source': sum(x.get('source_owner_chains_added',0) for x in ledger.get('dual_client_source_segments',[])),
        'shared_admission_owner_chains_are_unhosted_partial_sources': True,
        'source_digests': digests,
        'limits': ledger['counting_limits'],
        'tests_builds_client_execution_live_mutation': False,
        'new_source_deployment': False,
        'historical_formal_service': 'schema51 last observed; no live reread in this static report',
    }
    out = destination / (round_name + '.json')
    if out.exists() or out.with_suffix('.md').exists():
        raise FileExistsError('Preserve previous round reports; use a new round name')
    out.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    with out.open('x',encoding='utf-8') as handle:
        handle.write(encoded)
    latest.write_text(encoded, encoding='utf-8')
    lines = [f'# GOD2 封包串接盤點：{round_name}', '',
             '本表只記錄靜態格式與程式來源；特定分支接入不代表整個 opcode 的所有用途完成。', '',
             '| 統計項目 | 數量 |', '|---|---:|',
             f"| S2C 可接收長度 opcode | {counts['s2c_supported_length_opcodes']}（230 固定＋22 可變） |",
             f"| 有長度且世界 dispatch 非預設的 S2C opcode | {counts['s2c_supported_nondefault_world_dispatch_entries']}（僅入口，非已接功能） |",
             f"| 有長度且世界 dispatch 為預設的 S2C opcode | {counts['s2c_supported_default_world_dispatch_entries']} |",
             f"| 非預設 S2C 中已有來源回覆登錄 | {counts['s2c_nondefault_registered_reply_opcodes']}（仍非全變體完成） |",
             f"| 非預設 S2C 中僅有待接／獨立格式登錄 | {counts['s2c_nondefault_pending_format_only_opcodes']}／{counts['s2c_nondefault_independent_format_only_opcodes']}（可能與回覆登錄重疊） |",
             f"| 非預設 S2C 中外部 GM 工具橋接格式 | {counts['s2c_nondefault_external_tool_bridge_format_only_opcodes']}（不算遊戲功能串接） |",
             f"| 非預設 S2C 中既有來源推送／配置限制可見性推送分支 | {counts['s2c_nondefault_source_push_branch_opcodes']}／{counts['s2c_nondefault_config_gated_visibility_push_branch_opcodes']}（不代表全變體或正式啟用） |",
             f"| 非預設 S2C 尚未在路徑帳本分類 | {counts['s2c_nondefault_without_route_ledger_classification']}（其他舊研究可能已有資料） |",
             f"| 戰鬥分派表 1C..89 專用／預設 opcode | {counts['battle_specialized_dispatch_opcodes']}／{counts['battle_default_dispatch_opcodes_within_range']}（110 個表內索引） |",
             f"| 戰鬥專用但 WORLD 預設的 opcode | {counts['battle_specialized_that_are_world_default']} |",
             f"| WORLD 或戰鬥至少一狀態的專用入口聯集 | {counts['s2c_world_or_battle_specialized_opcode_union']}（入口，非完整包種） |",
             f"| 戰鬥 86 子型別選擇值／不同case地址 | {counts['battle_86_subtype_selector_values']}／{counts['battle_86_distinct_subtype_case_rvas']} |",
             f"| 戰鬥 83 action選擇值／第一層／actor層不同case地址 | {counts['s2c83_table_action_values']}／{counts['s2c83_first_distinct_case_rvas']}／{counts['s2c83_second_distinct_actor_case_rvas']} |",
             f"| 83 action在目前單體攻擊投影範圍內／外 | {counts['s2c83_scalar_attack_projection_qualified_actions']}／{counts['s2c83_action_values_outside_qualified_scalar_projection']}（不是全opcode完成率） |",
             f"| C2S opcode 參數候選，尚非完整包種 | {counts['c2s_direct_argument_opcode_candidates']} |",
             f"| C2S 包裝函式另定位 opcode 參數候選 | {counts['c2s_wrapper_argument_opcode_candidates']}（{' '.join(f'{x:02X}' for x in sorted(wrapper_ops))}） |",
             f"| C2S BF 已知原生 producer 分支 | {counts['c2s_bf_known_producer_branches']}（3 直接＋1 每日面板共用queue；非完整BF變體） |",
             f"| C2S 直接與已知包裝函式參數候選聯集 | {counts['c2s_known_argument_opcode_candidates']}（非全遊戲總封包） |",
             f"| 已知參數候選與世界解析器交集 | {counts['c2s_known_argument_candidates_in_world_parser']}（僅 opcode 交集） |",
             f"| 已知參數候選在世界解析器外 | {counts['c2s_known_argument_candidates_outside_world_parser']}（混合階段、含未證候選） |",
             f"| 世界解析 opcode 未列於已知參數候選 | {counts['world_parser_opcodes_not_in_known_argument_candidates']}（盤點法漏列不等於無原生 producer） |",
             f"| C2S35 額外原生靜態 raw 變體候選 | {counts['c2s_secondary_35_raw_variant_candidates']}（可達性及功能未證） |",
             f"| 世界 C2S 解析 opcode | {len(parsed)} |",
             f"| 至少有一條已接入來源的特定功能分支之 C2S opcode | {len(linked)} |",
             f"| 世界解析 opcode 的限定分支覆蓋比率（不是全遊戲完成率） | {counts['world_parser_opcode_scoped_branch_coverage_percent']}% |",
             f"| 登錄功能群 | {len(groups)} |",
             f"| 登錄 S2C 回覆 opcode 下限 | {len(replies)} |",
             f"| 世界控制／診斷 opcode（不算功能完成） | {len(controls)} |",
             f"| 世界已解析但功能未接通 opcode | {len(gaps)} |",
             f"| CN／TW未掛載局部owner鏈 | {counts['cn_unhosted_partial_owner_chains']}／{counts['tw_unhosted_partial_owner_chains']}（條件式來源，非完整玩法） |",
             f"| 雙版本局部owner鏈合計 | {counts['dual_client_unhosted_partial_owner_chains']}（非完成路徑分子） |",
             f"| TW未掛載階段/封包來源關聯／去重 | {counts['tw_unhosted_phase_source_bindings']}／{counts['tw_unique_unhosted_phase_source_binding_values']}（原生變體仍未完整） |",
             '| 全遊戲總封包／完成路徑／完成率 | 未知 |',
             '| 本來源階段新增正式部署 | 0 |', '',
             '首次報告建立基準；沒有前輪差額。' if not prior else
             '相對前輪差額：`' + json.dumps(delta, ensure_ascii=False) + '`', '',
             'S2C dispatch 細分是同一原生長度表在不同狀態的入口；206／46／9／215 不是本輪新增串接數。', '',
             '| 功能分支 | C2S（十六進位） | S2C（十六進位） | 仍未完成 |', '|---|---|---|---|']
    for row in groups:
        lines.append('| ' + ' | '.join((row['name'], ' '.join(row['c2s']), ' '.join(row['s2c']), row['remaining'])) + ' |')
    lines += ['', '已知 C2S 參數候選但不在目前世界解析器：' +
              ' '.join(f'{x:02X}' for x in candidate_not_world_parser) +
              '。其中可能是登入／角色／戰鬥階段、未接世界功能或靜態掃描假候選；需逐項驗證方向與狀態。',
              '世界解析器有、此參數掃描未列：' +
              ' '.join(f'{x:02X}' for x in world_parser_not_candidate) +
              '。原生發送可能經動態參數／其他包裝；不能說沒有 producer。', '',
              '控制／診斷：' + '、'.join(f'{k} {v}' for k,v in controls.items()), '',
              '獨立 S2C 格式、未證請求因果：' + '；'.join(f'{k} {v}' for k,v in ledger.get('independent_s2c_format_only', {}).items()), '',
              '外部 GM 工具橋接格式、非遊戲功能串接：' + ' '.join(ledger.get('external_s2c_bridge_format_only', {})), '',
              '既有來源推送分支：' + ' '.join(ledger.get('source_s2c_push_branches', {})) +
              '；配置限制可見性推送：' + ' '.join(ledger.get('config_gated_s2c_visibility_push_branches', {})) + '。', '',
              '戰鬥狀態專用 S2C case：' + '、'.join(f'{k}→{v}' for k,v in battle_frontier['specialized_opcode_cases'].items()) +
              '；86 子型別0..6另有七個選擇值。case與子型別入口不是服務端完整串接或客戶端驗收。', '',
              '戰鬥83兩層action表：' + '、'.join(f"{x['action_hex']}→{x['first_case_rva']}/{x['second_actor_case_rva']}" for x in battle83['actions']) +
              '。目前單體攻擊投影僅限01/03；0D有獨立delta codec、07為診斷效果，不能將共享case當作同義。', '',
              '非預設 S2C 未在本路徑帳本分類：' + ' '.join(s2c_frontier['frontier_nondefault_opcodes']) +
              '。這是帳本缺口，不代表客戶端沒有 consumer 或既有研究完全沒有資料。', '',
              '已解析而功能未接通：' + '、'.join(f'{k} {v}' for k,v in gaps.items()), '',
              '世界解析器之外的未接通例：' + '；'.join(ledger['outside_world_parser_open']), '',
              '登入／角色流程：' + '；'.join(ledger['frozen_pre_world_source_routes']), '',
              *('- ' + x for x in ledger['counting_limits']), '']
    if pending_groups:
        lines += ['## 已加入來源、尚未接通的功能', '']
        for row in pending_groups:
            lines += ['- ' + row['name'] + '：' + row['remaining']]
        lines += ['']
    dual = ledger.get('dual_client_native_inventory')
    if dual:
        lines += ['## 陸服獨立版本盤點', '',
                  '以下取自固定CN來源快照，不與上述TW候選或限定來源分支直接相加。', '',
                  f"CN版本SHA256：`{dual['cn_client_sha256']}`；來源：`{dual['source_snapshot']}`。", '',
                  f"C2S已觀察opcode值：{dual['cn_c2s_observed_opcode_values']}；S2C階段/opcode項目：{dual['cn_s2c_phase_opcode_entries']}；可用長度opcode：{dual['cn_s2c_supported_length_opcodes']}。", '',
                  f"本共用服務端已完成CN雙向遊戲路徑：{dual['cn_complete_bidirectional_gameplay_routes']}；全遊戲總數／百分比：未知。", '',
                  '共用遊戲內容與權威資料表為預設；封包差異優先在適配器處理，只有已證儲存差異才使用表名後綴_tw/_cn的專屬表。', '']
        lines += ['## 雙版本條件式來源串接', '',
                  '以下包含CN、TW與共用來源；均保留正式掛載與完整路徑的缺口。', '']
        for segment in ledger.get('dual_client_source_segments', []):
            lines += ['- ' + segment['name'] + '：' + segment['status'] + '。仍缺：' + '；'.join(segment['remaining'])]
        lines += ['']
    lines += ['', 'TW 補充原生發送證據：歷史通用候選151保留；新增跨分支／參數追蹤2C、2D、6F、99、A9，共6個限定分支紀錄。合併opcode集合156；不是新增玩法串接，所有變體及階段仍未窮盡。',
              'CN 接收函式47DE70、4812B0已補owner、游標與條件分支；兩者呼叫階段仍未知，不因相同opcode或缺少直接caller而推定配對或不可達。', '']
    markdown = '\n'.join(lines)
    out.with_suffix('.md').write_text(markdown, encoding='utf-8')
    (ROOT / 'packet-progress-latest.md').write_text(markdown, encoding='utf-8')
    return {'report': str(out), 'counts': counts, 'delta': result['delta_from_previous_report']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--round', required=True)
    parser.add_argument('--catalog', help='Current immutable catalog directory stem or pinned external catalog index under packet-connections-20261006')
    parser.add_argument('--round-directory',type=Path,help='Owned external archive directory for new complete round reports; latest reports remain local')
    args = parser.parse_args()
    if not args.round or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.round):
        raise ValueError('Round name must be a simple file stem')
    print(json.dumps(report(args.round,args.catalog,args.round_directory), ensure_ascii=True))
