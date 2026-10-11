"""Read the same candidate table during a naturally entered isolated battle.

Our fixture values are CUSTOM_TEST_NOT_NATIVE. The actual runtime table is
observed without memory writes, screenshot capture or desktop switching.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_combat_producer_memory_20260927 as probe

lab = probe.lab
SOURCE = ROOT / 'artifacts/playtests/private-map-item-ui-20260923-01/town-diagnostic-accounts.db'
SOURCE_SHA = '2eb68a62bf39b42e029661542f3d56ebbb7bd9d052a5e63140b60b79827fb152'
CONFIG = ROOT / 'artifacts/playtests/private-skill-ui-20260926-18/server-config.json'
world_capture = probe.base_capture


def configure(config):
    require_source()
    fixture_config = json.loads(CONFIG.read_text('utf-8'))
    # Use only the previously accepted isolated development configuration.
    # Live account data, endpoints and production configuration stay untouched.
    config['development'] = fixture_config['development']
    config['development']['native_monster_placements_only'] = False
    config['development']['diagnostic_town']['native_npc_placements_only'] = True
    # Door-route configuration requires guide mode; the native-only gate
    # still prevents unqualified synthetic guide placements.
    config['development']['diagnostic_town']['spawn_guides'] = True


def require_source():
    lab.require(hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA,
                'EXISTING_BATTLE_FIXTURE_IDENTITY')


def prepare(connection):
    lab.require(connection.execute('SELECT stage FROM diagnostic_town_guide_progress '
                                   'WHERE character_id=4').fetchone() == (3,), 'FIXTURE_QUEST_STAGE')
    lab.require(connection.execute('SELECT count(*) FROM battle_settlements').fetchone() == (0,),
                'FIXTURE_ALREADY_SETTLED')
    connection.execute('INSERT INTO recovered_positions VALUES(4,2,15,18,12,87)')


def active_capture(handle, ui, output):
    deadline = time.monotonic() + 25
    marker = 'DIAGNOSTIC_VITALS88_SENT_AFTER_TIMER36'
    while marker not in (output / 'server.log').read_text('utf-8', errors='replace'):
        lab.require(time.monotonic() < deadline, 'NATURAL_BATTLE_NOT_ENTERED')
        time.sleep(.2)
    probe.base_capture = lambda h, u, o: world_capture(h, u, o, expected_scene=(0,2,15))
    result = probe.capture(handle, ui, output)
    result['combat_producer_state']['capture_phase'] = 'OWN_SERVER_NATURAL_BATTLE_ENTRY'
    result['combat_producer_state']['fixture_balance_authority'] = 'CUSTOM_TEST_NOT_NATIVE'
    result['combat_producer_state']['battle_entry_log_marker'] = marker
    return result


if __name__ == '__main__':
    require_source()
    lab.fixture.SOURCE_DB = SOURCE
    lab.configure_isolated_fixture = configure
    lab.prepare_isolated_clone = prepare
    lab.capture = active_capture
    lab.__file__ = __file__
    raise SystemExit(lab.main())
