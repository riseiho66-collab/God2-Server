"""Original 12D3B0 cbspec2 loader, with bounded read-only CRT file operations."""
import hashlib

from .current_indoor_resources import NativeIndoorResources, BASE, SP, RETURN
from .current_skill_identity import SOURCE, SOURCE_SHA256, FILE_SIZE, decode_definitions
from .current_battle_character_binding import IMAGE, IMAGE_SHA
from .recover_combat_rules import CLIENT, read_pinned
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP

OFFSET = 0xa7e0444
BODY_SIZE = FILE_SIZE - 4
PATH_POINTER = BASE + 0x19c5e4
FILE_RVAS = (0x14716f, 0x14785c, 0x147182)
CODE_RANGES = ((0x12d3b0, 0x12d43d), (0x155980, 0x155a82))


def handles_service(native, address):
    return getattr(native, 'skill_catalog_loading', False) and address - BASE in FILE_RVAS


def file_service(native, vm, address, size, context):
    """Qualify each original call before using the existing CRT adapter."""
    sp = vm.reg_read(UC_X86_REG_ESP)
    arg = lambda i: native.u32(sp + 4 + i * 4)
    ret = native.u32(sp) - BASE
    phase = len(native.skill_catalog_io)
    dest = native.skill_catalog_destination
    if phase == 0:
        if (address != BASE + 0x14716f or ret != 0x12d3c3 or
                native.string(arg(0)) != b'data2\\fight\\spg\\cbspec2.bin' or
                native.string(arg(1)) != b'rb'):
            raise AssertionError('Unexpected original skill fopen')
        event = ('open', SOURCE.lower())
    elif phase in (1, 2):
        expected = (SP + 4, 4, 1) if phase == 1 else (dest, BODY_SIZE, 1)
        if (address != BASE + 0x14785c or ret != (0x12d3db if phase == 1 else 0x12d42a)
                or tuple(arg(i) for i in range(3)) != expected):
            raise AssertionError('Unexpected original skill fread')
        data, position = native.handles[arg(3)]
        if len(data) != FILE_SIZE or position != (0 if phase == 1 else 4):
            raise AssertionError('Skill stream length/position differs')
        event = ('read', position, expected[1])
    elif phase == 3:
        if address != BASE + 0x147182 or ret != 0x12d430:
            raise AssertionError('Unexpected original skill fclose')
        if native.handles[arg(0)][1] != FILE_SIZE:
            raise AssertionError('Original skill loader left unread bytes')
        event = ('close', FILE_SIZE)
    else:
        raise AssertionError('Extra skill file operation')
    NativeIndoorResources._service(native, vm, address, size, context)
    native.skill_catalog_io.append(event)


def load_catalog(native, manager):
    """Destination must already be mapped; returns actual retained source bytes.

    Entry is the original loader, not the preceding path-resolution constructor.
    Short streams are rejected by the oracle: native EAX=1 alone is not evidence
    of a complete read, because this original loader does not check fread counts.
    """
    if getattr(native, 'skill_catalog_attempted', False) or native.handles:
        raise ValueError('Fresh skill load and no open file handles required')
    image = read_pinned(IMAGE, IMAGE_SHA)
    source = read_pinned(CLIENT / SOURCE, SOURCE_SHA256)
    definitions = decode_definitions(source)
    if len(definitions) != 448:
        raise ValueError('Current skill catalog definition count changed')
    for lo, hi in CODE_RANGES:
        if bytes(native.vm.mem_read(BASE + lo, hi - lo)) != image[lo:hi]:
            raise ValueError('Original skill loader executable changed')
    if native.string(PATH_POINTER) != SOURCE.lower().replace('/', '\\').encode():
        raise ValueError('Original skill source literal changed')
    if bytes(native.vm.mem_read(0x6f6ed4, 4)) != image[0x2f6ed4:0x2f6ed8]:
        raise ValueError('Unqualified CRT comparison locale')
    dest = manager + OFFSET
    before = bytes(native.vm.mem_read(dest - 16, 16))
    after = bytes(native.vm.mem_read(dest + BODY_SIZE, 16))
    native.files[SOURCE.lower()] = source
    native.skill_catalog_attempted = native.skill_catalog_loading = True
    native.skill_catalog_destination = dest
    native.skill_catalog_io = []
    executed = set()

    def code(vm, address, size, data):
        rva = address - BASE
        if address == RETURN:
            return
        if rva not in FILE_RVAS and not any(lo <= rva and rva + size <= hi for lo, hi in CODE_RANGES):
            raise AssertionError(f'Unqualified skill-loader instruction {rva:x}')
        executed.add(rva)

    hook = native.vm.hook_add(UC_HOOK_CODE, code)
    try:
        result = native.call(0x12d3b0, PATH_POINTER, this=manager)
    finally:
        native.skill_catalog_loading = False
        native.vm.hook_del(hook)
    body = bytes(native.vm.mem_read(dest, BODY_SIZE))
    if (result != 1 or len(native.skill_catalog_io) != 4 or native.handles or body != source[4:]
            or bytes(native.vm.mem_read(dest - 16, 16)) != before
            or bytes(native.vm.mem_read(dest + BODY_SIZE, 16)) != after
            or 0x155980 not in executed):
        raise AssertionError('Original skill loader did not preserve the complete catalog')
    return {'body': body, 'destination': dest, 'source_sha256': hashlib.sha256(source).hexdigest(),
            'body_sha256': hashlib.sha256(body).hexdigest(), 'definition_count': len(definitions),
            'io': list(native.skill_catalog_io), 'result': result, 'executed': sorted(executed)}
