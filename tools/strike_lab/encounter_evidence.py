"""Bounded diagnostic evidence rollover; never mutates client or database."""
from copy import deepcopy


def archive_first_encounter(result):
    if result.get('completed_encounters'):
        raise ValueError('Only first-to-second diagnostic rollover is qualified')
    required = ('socket_battle_entry', 'socket_post_battle_world_loop_entry',
                'socket_skill_terminal_vitals', 'role_progress_return',
                'socket_character_exp_format_call')
    if any(key not in result for key in required):
        raise ValueError('Incomplete first encounter evidence')
    returned = result['socket_post_battle_world_loop_entry']
    if returned['world'] != result['world_initializer']['world_object']:
        raise ValueError('First encounter returned to a different world owner')
    if result['socket_battle_entry']['global_sequence'] >= returned['global_sequence']:
        raise ValueError('First encounter evidence order is invalid')
    levels = result.get('role_level_returns', [])
    if [(item['level'], item['progress']) for item in levels] != [(1, 0), (2, 1250)]:
        raise ValueError('First encounter progression differs from qualified fixture')
    if len(result.get('socket_skill_commands', [])) != 3:
        raise ValueError('Incomplete first encounter skill sequence')
    animations = result.get('animation_batch_completions', [])
    if len(animations) != 5 or any((x['expected'], x['completed'], x['timeout_fallback']) != (1, 1, False) for x in animations):
        raise ValueError('First encounter animations not naturally completed')
    if result['socket_character_exp_format_call']['amount'] != 250:
        raise ValueError('First encounter award differs from qualified fixture')
    keys = [key for key in result if key.startswith(('socket_', 'skill_', 'role_level_', 'role_progress_', 'animation_'))
            or key in ('world_resource_before_battle', 'world_resource_after_battle')]
    archive = deepcopy({key: result[key] for key in keys})
    # Allocate the complete copy before removing live observation fields.
    result['completed_encounters'] = [archive]
    for key in keys:
        del result[key]
    return archive
