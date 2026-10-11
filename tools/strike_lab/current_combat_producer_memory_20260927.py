"""Capture source-qualified combat planner fields on our hidden loopback client.

No memory writes or breakpoints. A zero/inactive planning table is not an
original balance value, and our server's received fields are not original data.
"""
from pathlib import Path
import hashlib
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_logged_world_memory_20260927 as lab

base_capture = lab.capture


def capture(handle, ui, output):
    result = base_capture(handle, ui, output)
    skill = int(result['skills']['address'], 16)
    manager = skill - 0xa7e0444
    battle = manager - 0x144938
    lab.require(manager > 0x10000 and battle > 0x10000, 'BATTLE_OWNER_RANGE')
    # The actual skill source and the role's independently published pointer
    # qualify the owner relation. Keep this derived alias explicitly visible.
    states = []
    for label, offset, size in (
        ('command_selection', 0xa9ea4d0, 0x20),
        ('projection_plan', 0xa9ea4f0, 0xac),
    ):
        raw = lab.exact(handle, battle + offset, size)
        states.append({'name': label, 'address': hex(battle + offset),
                       'offset': hex(offset), 'size': size, 'hex': raw.hex(),
                       'sha256': hashlib.sha256(raw).hexdigest()})
    data = states[1]
    raw = bytes.fromhex(data['hex'])
    count = struct.unpack_from('<i', raw)[0]
    lab.require(0 <= count <= 5, 'PLANNING_ROW_COUNT_UNCLASSIFIED')
    constants = []
    for address, size in ((0x59c924, 0x28), (0x5823b4, 4),
                          (0x5823c8, 2), (0x59c48c, 17), (0x5715e0, 4)):
        current = lab.exact(handle, address, size)
        constants.append({'address': hex(address), 'size': size, 'hex': current.hex()})
    result['combat_producer_state'] = {
        'battle_owner': hex(battle), 'skill_manager': hex(manager),
        'owner_relation': 'role+4504 -> verified entire cbspec body; manager=source-A7E0444; battle=manager-144938',
        'states': states, 'planning_rows': count, 'constants': constants,
        'authority': 'ACTUAL_RAM_OUR_SERVER_WORLD; inactive rows are not original damage coefficients',
        'original_formulas_recovered': 0,
    }
    return result


if __name__ == '__main__':
    lab.capture = capture
    # The owner launches this wrapper on the existing hidden fixture desktop;
    # module state is reinitialized there and never injected into the game.
    lab.__file__ = __file__
    raise SystemExit(lab.main())
