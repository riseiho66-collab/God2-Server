"""Build a disposable, hash-pinned client whose startup port is isolated."""
from hashlib import sha256
from pathlib import Path
import struct
import sys


SOURCE_SHA = 'ae997bbe726afaaee3a02ff9b718eff03f3d726002bc6aa36ce66a1964241f7f'
PATCH_SITE = bytes.fromhex('c7 80 e9 1e 01 00 20 0a 00 00')


def main():
    source, target, port = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    if not (1024 <= port <= 65535):
        raise ValueError('private port outside allowed range')
    raw = source.read_bytes()
    if sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('deployed source client changed')
    pe = struct.unpack_from('<I', raw, 0x3c)[0]
    count = struct.unpack_from('<H', raw, pe + 6)[0]
    header = pe + 24 + struct.unpack_from('<H', raw, pe + 20)[0]
    sections = []
    for index in range(count):
        at = header + index * 40
        sections.append((raw[at:at + 8].rstrip(b'\0'),
                         struct.unpack_from('<I', raw, at + 20)[0],
                         struct.unpack_from('<I', raw, at + 16)[0]))
    match = [(start, size) for name, start, size in sections if name == b'.w10fix']
    if len(match) != 1 or raw.count(PATCH_SITE) != 1:
        raise ValueError('port patch site not unique')
    offset = raw.index(PATCH_SITE)
    start, size = match[0]
    if not (start <= offset and offset + len(PATCH_SITE) <= start + size):
        raise ValueError('port patch site outside .w10fix')
    changed = bytearray(raw)
    changed[offset + 6:offset + 10] = struct.pack('<I', port)
    if target.exists():
        raise ValueError('private target already exists')
    target.write_bytes(changed)
    print(f'private_port={port} offset={offset:#x} sha256={sha256(changed).hexdigest()}')


if __name__ == '__main__':
    main()
