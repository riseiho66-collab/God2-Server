"""Bounded current MBD v1.2 block extraction, not collision interpretation."""
import struct

BLOCK_SIDE = 21
CELL_BYTES = 8
BLOCK_BYTES = BLOCK_SIDE * BLOCK_SIDE * CELL_BYTES
WINDOW_SIDE = 3 * BLOCK_SIDE


def project_base_window(blocks, initial):
    """Match 47440..474E6 only; missing slots retain their previous bytes."""
    if len(blocks) != 9 or len(initial) != WINDOW_SIDE * WINDOW_SIDE:
        raise ValueError('Expected nine blocks and a 63x63 initial window')
    result = bytearray(initial)
    for index, block in enumerate(blocks):
        if block is None:
            continue
        if len(block) != BLOCK_BYTES:
            raise ValueError('Invalid 21x21 cell block size')
        base_x, base_y = (index % 3) * BLOCK_SIDE, (index // 3) * BLOCK_SIDE
        for y in range(BLOCK_SIDE):
            for x in range(BLOCK_SIDE):
                result[(base_y+y)*WINDOW_SIDE+base_x+x] = (block[(y*BLOCK_SIDE+x)*CELL_BYTES+7] >> 6) & 1
    return bytes(result)


def apply_model_pass(window, x, y, width, height, cells):
    """47440 model Pass layer; x/y are already relative to the 63x63 window.

    Does not apply model special points or dynamic actor blockers.
    """
    if len(window) != WINDOW_SIDE * WINDOW_SIDE or not 1 <= width <= 512 or not 1 <= height <= 512:
        raise ValueError('Invalid window or model grid dimensions')
    if len(cells) != width * height:
        raise ValueError('Invalid model Pass grid size')
    if not -32768 <= x <= 32767 or not -32768 <= y <= 32767:
        raise ValueError('Model placement exceeds importer bounds')
    result = bytearray(window)
    for row in range(height):
        for column in range(width):
            tx, ty = x + column - row // 2, y + column + (row + 1) // 2
            if cells[row * width + column] == 0 and 0 <= tx < WINDOW_SIDE and 0 <= ty < WINDOW_SIDE:
                result[ty * WINDOW_SIDE + tx] = 0
    return bytes(result)


def apply_model_points(window, x, y, points):
    """Native 476AF..4774C: first two model points write value 2."""
    if len(window) != WINDOW_SIDE * WINDOW_SIDE or len(points) != 2:
        raise ValueError('Expected window and two model points')
    result = bytearray(window)
    def half(value):
        return value // 2 if value >= 0 else -((-value) // 2)
    for px, py in points:
        if not all(-32768 <= v <= 32767 for v in (x,y,px,py)):
            raise ValueError('Point exceeds importer bounds')
        if px < 0:
            continue
        tx, ty = x + px - half(py), y + px + half(py+1)
        if 0 <= tx < WINDOW_SIDE and 0 <= ty < WINDOW_SIDE:
            result[ty*WINDOW_SIDE+tx] = 2
    return bytes(result)


def parse_mbd(data):
    if not 16 <= len(data) <= 64 * 1024 * 1024 or data[:8] != b'MBD v1.2':
        raise ValueError('Unsupported MBD header or size')
    width, height = struct.unpack_from('<II', data, 8)
    if not 1 <= width <= 256 or not 1 <= height <= 256:
        raise ValueError('MBD block dimensions exceed import bounds')
    table_end = 16 + 4 * width * height
    if table_end > len(data):
        raise ValueError('Truncated MBD offset table')
    offsets = struct.unpack_from('<' + 'I' * (width * height), data, 16)
    spans = sorted(set(offset for offset in offsets if offset))
    for index, offset in enumerate(spans):
        if offset < table_end or offset + BLOCK_BYTES > len(data):
            raise ValueError('MBD block points outside payload')
        if index and offset < spans[index - 1] + BLOCK_BYTES:
            raise ValueError('Partially overlapping MBD blocks')
    # Zero entries are absent; never manufacture walkable/default cells.
    return {'width': width, 'height': height, 'offsets': offsets,
            'blocks': tuple(None if not offset else data[offset:offset + BLOCK_BYTES]
                            for offset in offsets)}
