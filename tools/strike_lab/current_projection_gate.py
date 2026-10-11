"""Original projection entry gate after timeGetTime; not a damage formula.

Start at 119E44 with an explicit clock result. The imported OS call and natural
function caller are not executed, stubbed, or claimed qualified.
"""
from .current_battle_entry import NativeRun, BATTLE, IMAGE_SHA256

START, ADMITTED, REJECTED = 0x119e44, 0x119e6e, 0x11a973
COUNT, LAST_TIME = 0xa9ea4f0, 0xa9ea598


def evaluate(count, previous_ms, current_ms):
    if any(type(value) is not int or not 0 <= value <= 0xffffffff
           for value in (count, previous_ms, current_ms)):
        raise ValueError('Explicit unsigned DWORD fixture required')
    n = NativeRun()
    n.put32(BATTLE + COUNT, count)
    n.put32(BATTLE + LAST_TIME, previous_ms)
    n.registers(ebp=BATTLE, eax=current_ms)
    n.run(START, ((START, ADMITTED),), {ADMITTED, REJECTED}, budget=20)
    return {'image_sha256': IMAGE_SHA256, 'start_rva': START,
            'stop_rva': n.stop, 'admitted': n.stop == ADMITTED,
            'count_after': n.get32(BATTLE + COUNT),
            'time_after': n.get32(BATTLE + LAST_TIME), 'writes': n.writes,
            'clock_input_is_synthetic': True, 'formula_recovered': False}
