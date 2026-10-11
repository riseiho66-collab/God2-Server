"""Original current instructions, poisoned actors, and explicit resource state."""
import struct
import functools
import itertools
import unittest
from unittest.mock import patch

from tools.strike_lab.current_battle_entry import (
    BATTLE, BASE, NativeRun, UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP,
    native_length, pinned_image,
)
from tools.strike_lab.current_battle_participant import (
    ACTION_STATE_OFFSET, ACTION_STATE_SIZE, ENTITY_SIZE, EFFECT_STRIDE,
    GATE, MANAGER, OUT, consume,
    entity_address, pending_arguments,
)


def cases(names, values):
    """Expand named fixture rows into standard-library FunctionTestCases."""
    def decorate(test):
        rows = [dict(zip(names.split(','), value if isinstance(value, tuple) else (value,)))
                for value in values]
        prior = getattr(test, 'cases', [{}])
        test.cases = [dict(a, **b) for a, b in itertools.product(prior, rows)]
        return test
    return decorate


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, test in sorted(globals().items()):
        if name.startswith('test_') and callable(test):
            for index, row in enumerate(getattr(test, 'cases', [{}])):
                run = functools.partial(test, **row)
                run.__name__ = name + f'[{index}]'
                run.__doc__ = None
                suite.addTest(unittest.FunctionTestCase(run))
    return suite


def actor(*, ordinal=3, active=0, handle=7):
    data = bytearray(b'\xa5' * ENTITY_SIZE)
    struct.pack_into('<H', data, 0x1a, handle)
    data[0x239], data[0x277] = active, ordinal
    data[0xdf8:0xec4] = bytes(51 * 4)
    return bytes(data)


def record83(position=15, masks=(0x2000, 0), subtype=1, selector=4):
    data = bytearray.fromhex('83 01 0f 6b ee 00 20 00 00 34 12 09 04 ca fe')
    data[1], data[2], data[12] = subtype, position, selector
    struct.pack_into('<HH', data, 5, *masks)
    return bytes(data)


def record84(position=15, masks=(0x2000, 0), key=0x321):
    data = bytearray.fromhex('84 00 20 00 00 0f 09 04 6b 21 03 34 12 78 56')
    data[5] = position
    struct.pack_into('<HH', data, 1, *masks)
    struct.pack_into('<H', data, 9, key)
    return bytes(data)


def metadata(effect):
    data = bytearray(b'\xb6' * 0x114)
    struct.pack_into('<h', data, 0x112, effect)
    return {0x321: bytes(data)}


def effect_table(first=0x123, second=0x234, third=0x345):
    data = bytearray(b'\xc7' * (2 * EFFECT_STRIDE))
    struct.pack_into('<hh', data, EFFECT_STRIDE, first, second)
    struct.pack_into('<H', data, EFFECT_STRIDE + 6, third)
    return bytes(data)


def entity(n, position):
    return bytes(n.vm.mem_read(entity_address(position), ENTITY_SIZE))


def action_expected(initial, *, target, marker=0x6b, subtype=1, ordinal=3):
    data = bytearray(initial)
    data[0x1e7], data[0x1e9] = marker, subtype
    data[0x1ea], data[0x233] = (0x11 if subtype == 1 else 0x85), 0
    data[0x235] = (initial[0x235] & 0x70) | (target % 14) | ((target // 14) << 7)
    if subtype == 1:
        data[0x277] = ordinal
        if not initial[0x239]:
            data[0x2c4:0x2c6] = bytes(2)
            data[0x4d0:0x55c] = b'\xff' * 0x8c
            data[0xb60:0xd90] = bytes(0x230)
            data[0x55c:0x62e] = bytes(0xd2)
    return data


@cases('opcode', [0x83, 0x84])
def test_native_length(opcode):
    assert native_length(opcode) == 15


def test_original_instruction_witnesses():
    witnesses = {
        0x114332: '8a4500', 0x11439c: 'e83f270000',
        0x114410: 'e82b230000', 0x116bba: '8a4802',
        0x11686a: '8a4805', 0x116962: '668b4708',
        0x116bee: '7304', 0x116bfe: '68a0c85900',
        0x1168dc: '668b1457', 0x11e607: '668b0c5f',
        0x11e75a: '8b448e38', 0x12c54a: '8a5602',
        0x12c615: '668b4e08', 0x12c46c: '668b460c',
        0x12c471: '668b4e0a',
        0x11698c: '0fbf8812010000', 0x1166b0: '668917',
        0x1166e3: '66894f02', 0x1166eb: '66895704',
        0x116dc1: '89948ff80d0000', 0x116df1: 'e89a86f4ff',
        0x11668a: 'e8c18e0100', 0x1166c1: 'e88a8e0100',
        0x12a953: '8896e7010000', 0x12a95f: '8886e9010000',
        0x12c631: 'e82aeaffff', 0x12c486: 'e8d5ebffff',
        0x12b11d: '8b84d3ccbc7f0a', 0x12b12b: '8bbcd3d0bc7f0a',
        0x12b132: 'e86973ffff', 0x1224ab: '668b044598d15900',
        0x12b137: '0fbfc0', 0x12b153: '8d0482',
        0x12b3cd: '6689bd86020000', 0x12b3d4: '66898d88020000',
        0x12b48e: '0fbfc7', 0x12b49c: 'e856c60100',
        0x12b225: '0fbf542464', 0x12b22a: '0fbf442460',
        0x12b23b: 'e8b7c80100', 0x12b36a: 'e8c1ffeeff',
        0x12b397: 'e86428ffff', 0x12b844: 'c22000',
    }
    image = pinned_image()
    for rva, encoded in witnesses.items():
        expected = bytes.fromhex(encoded)
        assert image[rva:rva + len(expected)] == expected, hex(rva)


@cases('active', [0, 2])
def test_83_continuous_action_setup_exact_all_actor_bytes(active):
    before, target = actor(active=active), actor(ordinal=0xfe)
    n = consume(record83(), entities={15: before, 13: target})
    assert n.stop == 0x12c631
    assert {0x11439c, 0x116ae0, 0x11e5e0, 0x11e6e0,
            0x12c520, 0x12a8d0, 0x12a9cc} <= set(n.visits)
    assert 0x12b060 not in n.visits
    assert entity(n, 15) == action_expected(before, target=13, ordinal=0xfe)
    expected = bytearray(target)
    expected[0x277] = 0xff
    assert entity(n, 13) == expected
    assert bytes(n.vm.mem_read(MANAGER + 0x309, 1)) == b'\x6b'
    assert n.get32(BATTLE + 0xa9e9c6c) == 0
    # MOV AX/CX/AL leaves upper bits live; only documented low widths are asserted.
    args = pending_arguments(n, 8)
    assert tuple(value & 255 for value in args[:4]) == (1, 1, 0, 13)
    assert args[4] & 0xffff == 0x1234
    assert args[5] == 0 and args[6] & 255 == 9 and args[7] == 0x22
    reads = {(offset, size) for _, offset, size in n.packet_reads}
    assert reads == {(0, 1), (1, 1), (2, 1), (3, 1), (5, 2),
                     (9, 2), (11, 1), (12, 1)}


@cases('position', [0, 13, 14, 27])
@cases('opcode', [0x83, 0x84])
def test_position_boundaries_and_mask_order(position, opcode):
    make = record83 if opcode == 0x83 else record84
    kwargs = {} if opcode == 0x83 else {'metadata': metadata(0)}
    n = consume(make(position=position, masks=(0xc004, 0x2001)),
                entities={position: actor(), 2: actor()}, **kwargs)
    assert n.stop == (0x12c631 if opcode == 0x83 else 0x12c486)
    args = pending_arguments(n, 8)
    assert tuple(x & 255 for x in args[:4]) == (position // 14, position % 14, 0, 2)


@cases('position', [28, 255])
@cases('opcode', [0x83, 0x84])
def test_invalid_source_stops_before_assertion(position, opcode):
    make = record83 if opcode == 0x83 else record84
    before = actor()
    n = consume(make(position=position), entities={13: before})
    assert n.stop == (0x116c03 if opcode == 0x83 else 0x1168af)
    assert entity(n, 13) == before and 0x2c70 not in n.visits


@cases('masks', [((0, 0),), ((0xc000, 0xc000),)])
def test_empty_or_high_only_masks_83_self_fallback_but_84_asserts(masks):
    before = actor(ordinal=255)
    n = consume(record83(masks=masks), entities={15: before})
    assert n.stop == 0x12c631
    expected = action_expected(before, target=15, ordinal=0)
    assert entity(n, 15) == expected
    assert tuple(x & 255 for x in pending_arguments(n, 4)) == (1, 1, 1, 1)
    m = consume(record84(masks=masks), entities={15: before})
    assert m.stop == 0x116917 and entity(m, 15) == before


def test_second_side_lowest_bit_is_selected():
    n = consume(record84(masks=(0x8000, 0x2400)),
                entities={15: actor(), 24: actor()}, metadata=metadata(0))
    assert n.stop == 0x12c486
    assert tuple(x & 255 for x in pending_arguments(n, 4)) == (1, 1, 1, 10)


@cases('selector', [1, 2])
def test_83_association_write_before_real_resource_lookup(selector):
    before = actor()
    n = consume(record83(subtype=3, selector=selector), entities={15: before})
    assert n.stop == 0x116df1 and 0x5f490 not in n.visits
    expected = bytearray(before)
    pointer = BATTLE + 0xa924d12 + 9 * 110 + selector * 28164
    struct.pack_into('<I', expected, 0xdf8, pointer)
    assert entity(n, 15) == expected
    assert tuple(x & 255 for x in pending_arguments(n, 2)) == (selector, 9)
    assert (0x116dc1, entity_address(15) + 0xdf8, 4, pointer) in n.writes


@cases('family', [84, 85])
def test_84_prebound_effects_and_action_exact_all_actor_bytes(family):
    before, target = actor(), actor(ordinal=0xfe)
    n = consume(record84(), entities={15: before, 13: target},
                metadata=metadata(family * 100 + 1),
                effect_tables={family: effect_table()})
    assert n.stop == 0x12c486
    assert {0x114410, 0x116740, 0x59a60, 0x116640, 0x5e0b0,
            0x12c430, 0x12a8d0, 0x12ab08} <= set(n.visits)
    assert entity(n, 15) == action_expected(before, target=13, subtype=5)
    expected = bytearray(target)
    struct.pack_into('<HHH', expected, 0x1cc, 0x123, 0x234, 0x345)
    assert entity(n, 13) == expected
    args = pending_arguments(n, 8)
    assert tuple(x & 255 for x in args[:4]) == (1, 1, 0, 13)
    assert tuple(x & 0xffff for x in args[4:6]) == (0x1234, 0x5678)
    assert tuple(x & 255 for x in args[6:]) == (9, 4)
    assert {(off, size) for _, off, size in n.packet_reads} == {
        (0, 1), (1, 2), (5, 1), (6, 1), (7, 1), (8, 1),
        (9, 2), (11, 2), (13, 2),
    }


@cases('first,second,stop', [(-1, 7, 0x11668a), (7, -1, 0x1166c1)])
def test_84_unbound_resource_stops_before_call_with_exact_partial_write(first, second, stop):
    before = actor()
    n = consume(record84(), entities={15: before, 13: before},
                metadata=metadata(8401), effect_tables={84: effect_table(first, second)})
    assert n.stop == stop and 0x12f550 not in n.visits
    expected = bytearray(before)
    if first >= 0:
        struct.pack_into('<H', expected, 0x1cc, first)
    assert entity(n, 13) == expected and entity(n, 15) == before


@cases('effect,tables', [(0, None), (8401, {}), (8402, {84: effect_table()})])
def test_84_native_no_effect_or_lookup_miss_writes_sentinels(effect, tables):
    before = actor()
    n = consume(record84(), entities={15: before, 13: before},
                metadata=metadata(effect), effect_tables=tables)
    assert n.stop == 0x12c486
    expected = bytearray(before)
    expected[0x1cc:0x1d2] = b'\xff' * 6
    assert entity(n, 13) == expected


def test_missing_resource_state_is_not_implicitly_successful():
    actors = {15: actor(), 13: actor()}
    assert consume(record84(), entities=actors).stop == 0x11696a
    assert consume(record84(), entities=actors, metadata=metadata(8401)).stop == 0x116671
    for meta in ({}, metadata(-1)):
        n = consume(record84(), entities=actors, metadata=meta)
        assert n.stop == (0x116982 if not meta else 0x116714)
        assert entity(n, 13) == actors[13]


@cases('key', [0x7f58, 0xffff])
def test_84_metadata_key_native_unsigned_upper_bound(key):
    n = consume(record84(key=key), entities={15: actor(), 13: actor()}, metadata={})
    assert n.stop == 0x116982 and 0x59a79 in n.visits


@cases('opcode', [0x83, 0x84])
def test_local_target_action_bit_is_written_by_original_helper(opcode):
    record = record83() if opcode == 0x83 else record84()
    n = consume(record, entities={15: actor(), 13: actor()}, local_slot=13,
                **({} if opcode == 0x83 else {'metadata': metadata(0)}))
    assert n.get32(BATTLE + 0xa9e9c74) == 0xa5a5a5b5
    assert (0x116a3e, BATTLE + 0xa9e9c74, 4, 0xa5a5a5b5) in n.writes


def test_missing_target_returns_zero_without_actor_creation():
    n = consume(record84(), entities={15: actor()})
    assert n.stop == 0x114415 and n.vm.reg_read(UC_X86_REG_EAX) == 0
    assert 0x11696a not in n.visits
    assert n.get32(MANAGER + 0x38 + 13 * 24) == 0


def test_83_missing_source_does_not_create_an_entity():
    n = consume(record83(), entities={13: actor()})
    assert n.stop == 0x1143a1 and n.vm.reg_read(UC_X86_REG_EAX) == 1
    assert n.get32(MANAGER + 0x38 + 15 * 24) == 0
    assert 0x12a8d0 not in n.visits


def test_one_continuous_dispatcher_start_and_unmodified_original_image():
    starts = []
    original_run = NativeRun.run

    def observe(n, start, *args, **kwargs):
        starts.append(start)
        return original_run(n, start, *args, **kwargs)

    with patch.object(NativeRun, 'run', observe):
        n = consume(record84(), entities={15: actor(), 13: actor()},
                    metadata=metadata(8401), effect_tables={84: effect_table()})
    assert starts == [0x114332]
    assert n.vm.reg_read(UC_X86_REG_EIP) == BASE + 0x12c486
    assert n.stop not in n.visits
    assert bytes(n.vm.mem_read(BASE, len(n.image))) == pinned_image()


@cases('matched', [False, True])
def test_83_association_existing_entry_matching_or_next_slot(matched):
    before = bytearray(actor())
    struct.pack_into('<I', before, 0xdf8, entity_address(15) + 0x34)
    before[0x34:0x36] = b'\x09\x01' if matched else b'\x08\x01'
    n = consume(record83(subtype=3, selector=1), entities={15: bytes(before)})
    assert n.stop == 0x116df1
    struct.pack_into('<I', before, 0xdf8 + (0 if matched else 4),
                     BATTLE + 0xa924d12 + 9 * 110 + 28164)
    assert entity(n, 15) == before


@cases('opcode', [0x83, 0x84])
def test_gate_and_phase_preconditions_stop_before_unknown_calls(opcode):
    record = record83() if opcode == 0x83 else record84()
    n = consume(record, entities={}, gate=-1)
    assert n.stop == (0x114384 if opcode == 0x83 else 0x1143f6)
    assert n.get32(GATE) == 0x6b and 0x12af90 not in n.visits
    n = consume(record, entities={}, phase_started=False)
    assert n.stop == (0x116b14 if opcode == 0x83 else 0x116771)
    assert n.get32(BATTLE + 0xa9df6b8) == 1 and 0x12aee0 not in n.visits
    n = consume(record, entities={}, gate=0x6c)
    assert n.stop == 0x1145c0 and n.get32(OUT) == 1
    assert n.get32(BATTLE + 0xa9ea4c4) == n.get32(BATTLE + 0xa9df6c0) == 0
    assert 0x116ae0 not in n.visits and 0x116740 not in n.visits


def test_contract_rejects_unqualified_variants():
    for record in (b'', record83()[:-1], record84() + b'\0', bytes(15),
                   record83(subtype=2)):
        with unittest.TestCase().assertRaises(ValueError):
            consume(record, entities={})
    with unittest.TestCase().assertRaises(ValueError):
        consume(record83(), entities={28: actor()})


def action_state():
    data = bytearray(b'\xd8' * ACTION_STATE_SIZE)
    struct.pack_into('<H', data, 0, 0x1234)
    struct.pack_into('<H', data, 4, 0x5678)
    for position in range(28):
        struct.pack_into('<II', data, 0x70 + position * 8,
                         0x12340000 + position, 0xffff0000 + position)
    return {'manager_tail': bytes(data), 'manager_0c': 0x7600000}


def pair_expected(snapshot, position, ordinal):
    first, second = struct.unpack_from('<II', snapshot['manager_tail'], 0x70 + position * 8)
    signed_step = struct.unpack_from('<h', pinned_image(), 0x19d198 + ordinal * 2)[0]
    return first, (second + signed_step * 15) & 0xffffffff


def assert_action_snapshot_unchanged(n, snapshot):
    assert bytes(n.vm.mem_read(MANAGER + ACTION_STATE_OFFSET, ACTION_STATE_SIZE)) == snapshot['manager_tail']
    assert n.get32(MANAGER + 0xc) == snapshot['manager_0c']
    assert snapshot['manager_0c'] & ~4095 not in n.pages


@cases('opcode', [0x83, 0x84])
def test_action_extension_preserves_default_and_one_original_caller(opcode):
    record = record83() if opcode == 0x83 else record84()
    kwargs = {'entities': {15: actor(), 13: actor()}}
    if opcode == 0x84:
        kwargs['metadata'] = metadata(0)
    default = consume(record, **kwargs)
    assert default.stop == (0x12c631 if opcode == 0x83 else 0x12c486)
    assert 0x12b060 not in default.visits
    starts = []
    original_run = NativeRun.run

    def observe(n, start, *args, **kw):
        starts.append(start)
        return original_run(n, start, *args, **kw)

    with patch.object(NativeRun, 'run', observe):
        n = consume(record, **kwargs, action_state=action_state())
    assert starts == [0x114332]
    assert {0x12b060, 0x1224a0, 0x1224b3} <= set(n.visits)
    assert n.stop == (0x12b49c if opcode == 0x83 else 0x12b397)
    assert n.vm.reg_read(UC_X86_REG_EIP) == BASE + n.stop
    assert n.stop not in n.visits
    assert not {0x147af7, 0x11dc00, 0x1b330} & set(n.visits)
    assert bytes(n.vm.mem_read(BASE, len(n.image))) == pinned_image()


@cases('value', [0, 0x7fff, 0x8000, 0xffff])
def test_83_action_words_and_signed_argument_exact_poisoned_states(value):
    before, target = actor(), actor(ordinal=2)
    record = bytearray(record83())
    struct.pack_into('<H', record, 9, value)
    snapshot = action_state()
    n = consume(bytes(record), entities={15: before, 13: target}, action_state=snapshot)
    assert n.stop == 0x12b49c
    expected = action_expected(before, target=13, ordinal=2)
    struct.pack_into('<HH', expected, 0x286, value, 0)
    assert entity(n, 15) == expected
    expected_target = bytearray(target)
    expected_target[0x277] = 3
    assert entity(n, 13) == expected_target
    buffer, template, argument = pending_arguments(n, 3)
    assert template == 0x59d968
    assert argument == (value if value < 0x8000 else value - 0x10000) & 0xffffffff
    assert struct.unpack('<II', n.vm.mem_read(buffer - 8, 8)) == pair_expected(snapshot, 13, 2)
    assert bytes(n.vm.mem_read(buffer, 50)) == bytes(50)
    assert n.action_reads == [(0x12b11d, 0xa7fbccc + 13 * 8, 4),
                              (0x12b12b, 0xa7fbcd0 + 13 * 8, 4)]
    assert (0x12b3cd, entity_address(15) + 0x286, 2, value) in n.writes
    assert (0x12b3d4, entity_address(15) + 0x288, 2, 0) in n.writes
    assert_action_snapshot_unchanged(n, snapshot)


@cases('selector,stop,template', [(6, 0x12b453, 0x5b4640),
                                 (7, 0x12b43a, 0x59ce00),
                                 (8, 0x12b421, 0x59ce48)])
def test_83_packet_b_selects_original_formatting_boundary(selector, stop, template):
    record = bytearray(record83())
    record[11] = selector
    before = actor()
    n = consume(bytes(record), entities={15: before, 13: before}, action_state=action_state())
    assert n.stop == stop
    assert pending_arguments(n, 2)[1] == template
    expected = action_expected(before, target=13)
    struct.pack_into('<HH', expected, 0x286, 0x1234, 0)
    assert entity(n, 15) == expected


@cases('target_position,ordinal', [(0, 0), (13, 2), (27, 3)])
def test_84_raw_manager_pair_and_original_signed_step_to_11dc00(target_position, ordinal):
    before, target = actor(ordinal=ordinal), actor()
    masks = (1 << target_position, 0) if target_position < 14 else (0, 1 << (target_position - 14))
    snapshot = action_state()
    n = consume(record84(masks=masks), entities={15: before, target_position: target},
                metadata=metadata(0), action_state=snapshot)
    assert n.stop == 0x12b397
    args = pending_arguments(n, 6)
    assert args[0] == snapshot['manager_0c']
    assert args[1] & 0xffff == 0x1234 and args[5] & 0xffff == 0x5678
    assert args[2:4] == pair_expected(snapshot, target_position, ordinal)
    assert args[4] == 0
    assert n.vm.reg_read(UC_X86_REG_ECX) == entity_address(15) + 0x2c8
    assert entity(n, 15) == action_expected(before, target=target_position, subtype=5)
    expected = bytearray(target)
    expected[0x1cc:0x1d2] = b'\xff' * 6
    assert entity(n, target_position) == expected
    frame = n.vm.reg_read(UC_X86_REG_ESP) + 24
    assert bytes(n.vm.mem_read(frame + 0x18, 50)) == bytes(50)
    assert n.action_reads == [(0x12b11d, 0xa7fbccc + target_position * 8, 4),
                              (0x12b12b, 0xa7fbcd0 + target_position * 8, 4),
                              (0x12b36f, 0xa7fbc60, 2), (0x12b37f, 0xa7fbc5c, 2)]
    assert_action_snapshot_unchanged(n, snapshot)


@cases('handle', [7, 0xfff])
def test_84_existing_handle_requires_real_cleanup_before_later_setup(handle):
    before = bytearray(actor())
    struct.pack_into('<H', before, 0x2c2, handle)
    snapshot = action_state()
    n = consume(record84(), entities={15: bytes(before), 13: actor()},
                metadata=metadata(0), action_state=snapshot)
    assert n.stop == 0x12b36a and 0x1b330 not in n.visits
    assert pending_arguments(n, 1) == (snapshot['manager_0c'] + handle * 0x290 + 0x10,)
    assert entity(n, 15) == action_expected(before, target=13, subtype=5)


@cases('selector,stop', [(0x22, 0x12b1f3), (0x24, 0x12b23b)])
def test_84_packet_7_selects_signed_packet_b_d_arguments(selector, stop):
    before = actor()
    record = bytearray(record84())
    record[7] = selector
    struct.pack_into('<HH', record, 11, 0x8000, 0xffff)
    n = consume(bytes(record), entities={15: before, 13: before},
                metadata=metadata(0), action_state=action_state())
    assert n.stop == stop
    args = pending_arguments(n, 3 if selector == 0x22 else 4)
    assert args[1] == (0x59d968 if selector == 0x22 else 0x59da58)
    assert args[2] == 0xffff8000
    if selector == 0x24:
        assert args[3] == 0xffffffff
    # These 84 words are only pushed, not yet stored in the source actor.
    assert entity(n, 15) == action_expected(before, target=13, subtype=5)


@cases('handle', [0x1000, 0xffff])
def test_84_invalid_target_handle_returns_from_12b060_without_snapshot_read(handle):
    before = actor()
    n = consume(record84(), entities={15: before, 13: actor(handle=handle)},
                metadata=metadata(0), action_state=action_state())
    assert n.stop == 0x12c48b and 0x12b844 in n.visits
    assert not n.action_reads and 0x1224a0 not in n.visits
    assert entity(n, 15) == action_expected(before, target=13, subtype=5)


def test_action_extension_cannot_cross_prior_resource_boundary():
    n = consume(record83(subtype=3), entities={15: actor()}, action_state=action_state())
    assert n.stop == 0x116df1 and 0x12b060 not in n.visits
    n = consume(record84(), entities={15: actor(), 13: actor()},
                metadata=metadata(8401), effect_tables={84: effect_table(-1)},
                action_state=action_state())
    assert n.stop == 0x11668a and 0x12b060 not in n.visits


def test_action_snapshot_rejects_missing_unknown_and_wrong_width_inputs():
    valid = action_state()
    invalid = [True, b'', {}, {'manager_tail': valid['manager_tail']},
               dict(valid, unknown=0), dict(valid, manager_tail=b''),
               dict(valid, manager_tail=valid['manager_tail'] + b'\0'),
               dict(valid, manager_tail=bytearray(valid['manager_tail'])),
               dict(valid, manager_0c=True), dict(valid, manager_0c=-1),
               dict(valid, manager_0c=0x100000000)]
    for snapshot in invalid:
        with unittest.TestCase().assertRaises(ValueError):
            consume(record83(), entities={}, action_state=snapshot)
