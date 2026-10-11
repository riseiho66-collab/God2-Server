"""Follow the 119E30 tail continuously to the text encoder call boundary.

Only the tail has synthetic live-ins. No original arithmetic-to-text prefix,
transport call, real server transaction, or authoritative combat is claimed.
"""
import hashlib
import json
import struct

from .current_battle_entry import (
    BASE, BATTLE, CONTEXT, NET, ROOT_OBJECT, SP, STACK, NativeRun, pinned_image,
    IMAGE_SHA256, UC_X86_REG_ESP, UC_X86_REG_ECX,
)

RANGES = ((0x11a959, 0x11a971), (0x96990, 0x96f29),
          (0x148810, 0x148848), (0x147f90, 0x148010),
          (0x148990, 0x148a5c), (0x131c10, 0x131c2d))


def run_sink(text=b'!\x05\x16actor 3', *, padding=0):
    if (type(text) is not bytes or not text.startswith(b'!\x05\x16') or
            b'\x00' in text or not 3 <= len(text) <= 120 or
            type(padding) is not int or not 0 <= padding <= 255):
        raise ValueError('Expected bounded synthetic candidate-tail text')
    image = pinned_image()
    n = NativeRun(image)
    n.put(STACK, bytes([padding]) * 0x8000)
    n.put32(BATTLE + 0x20, CONTEXT)
    n.put32(CONTEXT + 0x86874, NET)
    # The original '!' branch requires a nonzero related-object field.
    n.put32(CONTEXT + 0x86888, ROOT_OBJECT)
    n.put32(ROOT_OBJECT + 0x3f98, 1)
    n.put(CONTEXT + 0x5bfa8, bytes(264))
    n.put(SP + 0x1d4, text + b'\x00')
    # Tail has completed whole-DWORD text copies; zero trailing bytes remain.
    n.registers(esp=SP, ebp=BATTLE, eax=0, ecx=0)
    try:
        n.run(0x11a959, RANGES, {0x132e0}, budget=10000)
    except Exception as exc:
        last = hex(n.visits[-1]) if n.visits else 'none'
        raise AssertionError(f'Native sink failed closed at {last}') from exc
    sp = n.vm.reg_read(UC_X86_REG_ESP)
    return_va, opcode, pointer, size = struct.unpack('<4I', n.vm.mem_read(sp, 16))
    body = bytes(n.vm.mem_read(pointer, size))
    outside_stack = [w for w in n.writes if not STACK <= w[1] < STACK + 0x8000]
    return {
        'authority': 'NATIVE_TAIL_TO_TEXT_ENCODER_BOUNDARY_NOT_COMBAT_FORMULA',
        'image_sha256': IMAGE_SHA256,
        'range_hashes': {f'{a:06x}-{b:06x}': hashlib.sha256(image[a:b]).hexdigest()
                         for a, b in RANGES},
        'synthetic_text_hex': text.hex(), 'stack_padding': padding,
        'stop_rva': n.stop, 'return_rva': return_va - BASE,
        'encoder_this': n.vm.reg_read(UC_X86_REG_ECX),
        'opcode': opcode, 'body_hex': body.hex(), 'body_size': size,
        'declared_length': struct.unpack_from('<H', body)[0],
        'channel': body[2] & 0x7f, 'text_hex': body[6:].hex(),
        'instruction_count': len(n.visits),
        'calls_reached': [r for r in (0x96990, 0x148810, 0x131c10, 0x147f90)
                          if r in n.visits],
        'outside_stack_writes': outside_stack,
        'limitations': ['synthetic tail text; upstream formula-to-text not executed',
                        'stopped before encoder; no network transmission',
                        'header byte3 not assigned in this path; not a wire schema'],
    }


if __name__ == '__main__':
    print(json.dumps(run_sink(), sort_keys=True))
