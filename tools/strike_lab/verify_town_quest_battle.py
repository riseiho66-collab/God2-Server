"""Check the isolated CUSTOM-0028 native run and its cold reconnect."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tables(path):
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        assert db.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {name: db.execute('SELECT * FROM "' + name + '" ORDER BY rowid').fetchall() for name in names}


def result(run):
    return json.loads((run / (run.name + '-result.json')).read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('battle_run', type=Path)
    parser.add_argument('reconnect_run', type=Path)
    parser.add_argument('--movement-run', type=Path)
    parser.add_argument('--movement-reconnect-run', type=Path)
    parser.add_argument('--return-run', type=Path)
    parser.add_argument('--door-run', type=Path)
    parser.add_argument('--door-reconnect-run', type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    battle = (args.battle_run / 'town-diagnostic-accounts.db').resolve(strict=True)
    cold = (args.reconnect_run / 'town-diagnostic-accounts.db').resolve(strict=True)
    before, after, restored = (tables(path) for path in (source, battle, cold))
    assert before.keys() == after.keys() == restored.keys()
    changed = sorted(name for name in before if before[name] != after[name])
    assert changed == ['battle_reservations', 'battle_settlements', 'character_experience',
                       'character_resources', 'sqlite_sequence'], changed
    assert after == restored, 'Cold reconnect changed saved tables'
    assert before['recovered_positions'] == [(1, 2, 15, 18, 12, 55)]
    assert after['diagnostic_town_guide_progress'] == before['diagnostic_town_guide_progress']
    assert after['diagnostic_town_guide_reward'] == before['diagnostic_town_guide_reward']
    assert after['diagnostic_inventory_slots'] == before['diagnostic_inventory_slots']
    assert before['diagnostic_town_guide_progress'][0][1] == 3
    assert before['diagnostic_inventory_slots'][0][2:4] == (5569, 1)
    assert before['diagnostic_town_guide_reward'][0][4:6] == (5569, 1)
    assert after['character_resources'] == [(1, 100, 120, 42, 80, 2, 'CUSTOM-0012')]
    assert len(after['battle_reservations']) == len(after['battle_settlements']) == 1
    assert after['battle_checkpoints'] == []
    assert after['battle_settlements'][0][3] == 0
    live = result(args.battle_run)
    assert live['result'] == 'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP'
    for key in ('socket_battle_entry', 'socket_skill_command_return', 'socket_skill_terminal_vitals',
                'socket_outcome_panel_return', 'socket_post_battle_world_loop_entry', 'indoor_reconnect_final'):
        assert key in live, key
    assert len(live['journal_restore_returns']) == 15
    for observed in (live, reconnect := result(args.reconnect_run)):
        scene = observed['indoor_reconnect_final']['snapshot']
        assert tuple(scene[key] for key in ('area', 'scene', 'kind', 'x', 'y')) == (2, 15, 2, 18, 12)
    assert reconnect['result'] == 'NATIVE_CROSS_MAP_RECONNECT_RESTORED'
    assert len(reconnect['journal_restore_returns']) == 15
    restore = json.loads((args.battle_run / 'town-restore.json').read_text(encoding='utf-8'))
    assert restore['source_sha256'] == digest(source), 'Original source changed after read-only backup'
    report = {'result': 'PASS', 'source_sha256': digest(source), 'battle_sha256': digest(battle),
              'cold_sha256': digest(cold), 'battle_changed_tables': changed,
              'cold_changed_tables': [], 'native_battle_result': live['result'],
              'native_reconnect_result': reconnect['result']}
    if args.movement_run or args.movement_reconnect_run:
        assert args.movement_run and args.movement_reconnect_run
        move_db = (args.movement_run / 'town-diagnostic-accounts.db').resolve(strict=True)
        move_cold_db = (args.movement_reconnect_run / 'town-diagnostic-accounts.db').resolve(strict=True)
        moved, moved_cold = tables(move_db), tables(move_cold_db)
        assert moved_cold == moved, 'Movement cold reconnect changed saved tables'
        assert moved['recovered_positions'] == [(1, 2, 15, 19, 12, 58)]
        for name in before:
            if name not in changed + ['recovered_positions']:
                assert moved[name] == before[name], name
        for name in changed:
            assert moved[name] == after[name], name
        movement = result(args.movement_run)
        assert movement['result'] == 'NATIVE_MOVEMENT_PATH_COMPLETED'
        assert [step['town_target'] for step in movement['movement_steps']] == [[19, 12], [18, 12], [19, 12]]
        assert [step['ack_hex'] for step in movement['movement_steps']] == ['5d01', '5d02', '5d03']
        assert movement['movement_completion']['motion_state'] == 0
        moved_reconnect = result(args.movement_reconnect_run)
        assert moved_reconnect['result'] == 'NATIVE_CROSS_MAP_RECONNECT_RESTORED'
        assert len(moved_reconnect['journal_restore_returns']) == 15
        scene = moved_reconnect['indoor_reconnect_final']['snapshot']
        assert tuple(scene[key] for key in ('area', 'scene', 'kind', 'x', 'y')) == (2, 15, 2, 19, 12)
        for run, parent in ((args.movement_run, source), (args.movement_reconnect_run, move_db)):
            provenance = json.loads((run / 'town-restore.json').read_text(encoding='utf-8'))
            assert provenance['source_sha256'] == digest(parent)
        report.update(movement_sha256=digest(move_db), movement_cold_sha256=digest(move_cold_db),
                      movement_result=movement['result'], movement_reconnect_result=moved_reconnect['result'],
                      movement_changed_tables=sorted(name for name in before if before[name] != moved[name]),
                      movement_reconnect_changed_tables=[])
    if args.return_run:
        return_db = (args.return_run / 'town-diagnostic-accounts.db').resolve(strict=True)
        returned = tables(return_db)
        return_changed = sorted(name for name in before if before[name] != returned[name])
        assert return_changed == changed[:4] + ['recovered_positions', 'sqlite_sequence'], return_changed
        assert returned['recovered_positions'] == [(1, 2, 4, 110, 70, 56)]
        for name in changed:
            assert returned[name] == after[name], name
        for name in before:
            if name not in return_changed:
                assert returned[name] == before[name], name
        live_return = result(args.return_run)
        assert live_return['result'] == 'NATIVE_POST_BATTLE_DURABLE_TOWN_RETURN'
        for key in ('socket_battle_entry', 'socket_skill_command_return', 'socket_skill_terminal_vitals',
                    'socket_outcome_panel_return', 'socket_post_battle_world_loop_entry',
                    'indoor_reconnect_final', 'town_map_request_return', 'town_scene_return',
                    'town_return_durable'):
            assert key in live_return, key
        assert live_return['town_map_request_return']['queued_hex'] == '25c1150000'
        scene = live_return['town_return_durable']['snapshot']
        assert tuple(scene[key] for key in ('area', 'scene', 'kind', 'x', 'y', 'loaded_scene_id')) == (2, 4, 0, 110, 70, 258)
        assert scene['ring_hex'] == '010001'
        assert live_return['town_return_durable']['saved_position'] == [1, 2, 4, 110, 70, 56]
        entries = [entry for pool in live_return['town_return_durable']['npcs']['pools'] for entry in pool['entries']]
        assert sorted((entry['identity'], entry['x'], entry['y']) for entry in entries) == [
            (1606, 110, 69), (1607, 112, 70)]
        restore = json.loads((args.return_run / 'town-restore.json').read_text(encoding='utf-8'))
        assert restore['source_sha256'] == digest(source)
        report.update(return_sha256=digest(return_db), return_result=live_return['result'],
                      return_changed_tables=return_changed)
    if args.door_run:
        door_db = (args.door_run / 'town-diagnostic-accounts.db').resolve(strict=True)
        door_saved = tables(door_db)
        door_changed = sorted(name for name in before if before[name] != door_saved[name])
        assert door_changed == changed[:4] + ['recovered_positions', 'sqlite_sequence'], door_changed
        assert door_saved['recovered_positions'] == [(1, 2, 4, 86, 71, 64)]
        for name in changed:
            assert door_saved[name] == after[name], name
        for name in before:
            if name not in door_changed:
                assert door_saved[name] == before[name], name
        live_door = result(args.door_run)
        assert live_door['result'] == 'NATIVE_POST_BATTLE_DOORWAY_TOWN_RETURN'
        assert live_door.get('error') is None
        assert 'town_map_probe' not in live_door
        for key in ('socket_battle_entry', 'socket_skill_command_return', 'socket_skill_terminal_vitals',
                    'socket_outcome_panel_return', 'socket_post_battle_world_loop_entry',
                    'indoor_reconnect_final', 'town_post_battle_door_final'):
            assert key in live_door, key
        path = [(17, 13), (16, 14), (15, 15), (14, 16), (14, 17), (15, 18), (16, 19), (16, 20)]
        assert [tuple(step) for step in live_door['door_probe']['path']] == path
        assert len(live_door['door_probe']['arrivals']) == len(path)
        assert [step['ack_hex'] for step in live_door['movement_steps']] == [f'5d{i:02x}' for i in range(1, 9)]
        final = live_door['town_post_battle_door_final']
        scene = final['snapshot']
        assert tuple(scene[key] for key in ('area', 'scene', 'kind', 'x', 'y', 'loaded_scene_id')) == (2, 4, 0, 86, 71, 258)
        assert scene['ring_hex'] == '010001'
        assert bytes.fromhex(scene['metadata_hex']).startswith(b'CityI1\0')
        assert final['saved_position'] == [1, 2, 4, 86, 71, 64]
        entries = [entry for pool in final['npcs']['pools'] for entry in pool['entries']]
        assert sorted((entry['identity'], entry['x'], entry['y']) for entry in entries) == [
            (1606, 110, 69), (1607, 112, 70)]
        packets = []
        folder = args.door_run / 'crypto-private'
        for metadata_path in folder.glob('*.json'):
            meta = json.loads(metadata_path.read_text(encoding='utf-8'))
            if not meta.get('plain_file') or meta['sequence'] <= live_door['socket_post_battle_world_loop_entry']['sequence']:
                continue
            plain = (folder / meta['plain_file']).read_bytes()
            wire = (folder / meta['wire_file']).read_bytes()
            assert meta['checksum_valid'] and not meta['brute_force_used']
            assert digest(folder / meta['plain_file']) == meta['plain_sha256']
            assert digest(folder / meta['wire_file']) == meta['wire_sha256']
            if plain[2] in (0x2e, 0x5d, 0x61, 0x1c, 0x25):
                packets.append((meta['sequence'], meta['socket'], meta['direction'], plain[2:-1].hex()))
        packets.sort()
        assert not any(logical.startswith('25') for _, _, _, logical in packets)
        first_move = next(sequence for sequence, _, direction, logical in packets
                          if direction == 'C2S' and logical.startswith('2e'))
        packets = [packet for packet in packets if packet[0] >= first_move]
        expected = []
        for index, (x, y) in enumerate(path, 1):
            request = f'2e{x.to_bytes(2, "little").hex()}{y.to_bytes(2, "little").hex()}{index:02x}c2'
            expected.extend([('C2S', request), ('S2C', f'5d{index:02x}')])
        expected += [('S2C', '610201000058018e00'), ('C2S', '1c01000000')]
        assert [(direction, logical) for _, _, direction, logical in packets] == expected
        assert len({socket for _, socket, _, _ in packets}) == 1
        assert packets[-1][0] < final['sequence']
        log = (args.door_run / 'cpp-server.log').read_text(encoding='utf-8')
        assert log.count('DIAGNOSTIC_DOOR_COMMITTED') == 1
        assert log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED') == 1
        assert log.count('DIAGNOSTIC_TOWN_GUIDES_SENT') == 1
        assert 'policy or response rejected' not in log
        restore = json.loads((args.door_run / 'town-restore.json').read_text(encoding='utf-8'))
        assert restore['source_sha256'] == digest(source)
        report.update(door_sha256=digest(door_db), door_result=live_door['result'],
                      door_changed_tables=door_changed, door_packet_count=len(packets))
    if args.door_reconnect_run:
        assert args.door_run, 'Door reconnect requires its source run'
        reconnect_db = (args.door_reconnect_run / 'town-diagnostic-accounts.db').resolve(strict=True)
        assert tables(reconnect_db) == door_saved, 'Door cold reconnect changed saved tables'
        reconnect = result(args.door_reconnect_run)
        assert reconnect['result'] == 'NATIVE_DOOR_ROUNDTRIP_RECONNECT_RESTORED'
        assert reconnect.get('error') is None
        assert len(reconnect['journal_restore_returns']) == 15
        snap = reconnect['door_reconnect_final']['snapshot']
        assert tuple(snap[key] for key in ('area', 'scene', 'kind', 'x', 'y', 'ring_hex')) == (2, 4, 0, 86, 71, '010001')
        entries = [entry for pool in reconnect['door_reconnect_final']['npcs']['pools'] for entry in pool['entries']]
        assert sorted((entry['identity'], entry['x'], entry['y']) for entry in entries) == [
            (1606, 110, 69), (1607, 112, 70)]
        assert 'socket_battle_entry' not in reconnect
        restore = json.loads((args.door_reconnect_run / 'town-restore.json').read_text(encoding='utf-8'))
        assert restore['source_sha256'] == digest(door_db)
        report.update(door_reconnect_sha256=digest(reconnect_db), door_reconnect_result=reconnect['result'],
                      door_reconnect_changed_tables=[])
    print(json.dumps(report, indent=2))
    (args.reconnect_run / 'town-battle-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if args.movement_reconnect_run:
        (args.movement_reconnect_run / 'town-battle-movement-verification.json').write_text(
            json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if args.return_run:
        (args.return_run / 'town-battle-return-verification.json').write_text(
            json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if args.door_run:
        (args.door_run / 'town-battle-door-verification.json').write_text(
            json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if args.door_reconnect_run:
        (args.door_reconnect_run / 'town-battle-door-reconnect-verification.json').write_text(
            json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
