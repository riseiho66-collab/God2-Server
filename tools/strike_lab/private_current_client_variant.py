"""Make a disposable port-isolated copy of the current unpacked client.

Only the startup TCP port immediate is changed. The deployed God2.exe is read
and hash-checked but never written.
"""
from hashlib import sha256
from pathlib import Path
import struct
import sys


SOURCE_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
SITE = bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00')


def main():
    source, target, port = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    if not (1024 <= port <= 65535):
        raise ValueError('private port outside allowed range')
    raw = source.read_bytes()
    if sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('current client identity changed')
    if target.exists() or source.resolve() == target.resolve():
        raise ValueError('private target exists or aliases source')
    if raw.count(SITE) != 1:
        raise ValueError('startup port site not unique')
    site = raw.index(SITE)
    pe = struct.unpack_from('<I', raw, 0x3c)[0]
    section_count = struct.unpack_from('<H', raw, pe + 6)[0]
    section_header = pe + 24 + struct.unpack_from('<H', raw, pe + 20)[0]
    text_ranges = []
    for index in range(section_count):
        at = section_header + index * 40
        if raw[at:at + 8].rstrip(b'\0') == b'.text':
            text_ranges.append((struct.unpack_from('<I', raw, at + 20)[0],
                                struct.unpack_from('<I', raw, at + 16)[0]))
    if len(text_ranges) != 1 or not (text_ranges[0][0] <= site and
                                     site + len(SITE) <= sum(text_ranges[0])):
        raise ValueError('startup port site outside unique .text')
    changed = bytearray(raw)
    changed[site + 1:site + 5] = struct.pack('<I', port)
    assert sum(a != b for a, b in zip(raw, changed)) <= 4
    target.write_bytes(changed)
    print(f'private_port={port} offset={site + 1:#x} source_sha256={SOURCE_SHA} '
          f'copy_sha256={sha256(changed).hexdigest()}')


if __name__ == '__main__':
    main()
