"""Bounded offline player journal scenarios, not quest gameplay or live E2E.

Reuse the existing native oracle without calling its compiler/process setup.
Packets and page/click inputs are synthetic; description bytes are original.
Run with python -B -m tools.strike_lab.quest_player_scenarios [--json].
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from .recover_quests import build_catalog

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/research'))
import test_current_quest_record as oracle
from unicorn import UcError, UC_HOOK_CODE

UI = oracle.UI
UNKNOWN_RULES = (
    'authoritative main/side classification', 'availability and prerequisites',
    'NPC dialogue and acceptance', 'objective progress and branching',
    'completion and turn-in', 'item/EXP/money rewards and claim deduplication',
    'abandonment and repeat/reset rules', 'ACTMIS/daily namespace joins',
    'persistence and authoritative initial journal',
    'C2S requests and server session authorization',
    'page-button/input dispatch, open-widget rendering and live E2E',
)


class Evidence:
    def __init__(self, client=ROOT.parent / 'God2'):
        self.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                      'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(self.image).hexdigest() != oracle.quest.routes.IMAGE_SHA:
            raise AssertionError('Pinned native image changed')
        self.catalog = build_catalog(client)
        table = self.catalog['tables']['missions']
        if (table['source_sha256'], table['decoded_sha256']) != (
                oracle.SOURCE_SHA, oracle.DECODED_SHA):
            raise AssertionError('Pinned Mission_data changed')
        if self.catalog['validation']['structural_issues']:
            raise AssertionError('Malformed source catalog')
        self.rows = {r['source_line']: r for r in table['records']}
        self.missions = self.catalog['quests']
        self.texts = []
        for index, mission in enumerate(self.missions, 1):
            if mission['id'] != index or [o['step'] for o in mission['objectives_text']] != list(
                    range(1, mission['step_field'] + 1)):
                raise AssertionError('Source order no longer matches the native loader')
            self.texts.append([bytes.fromhex(self.rows[o['source_line']]['raw_fields_hex'][3])
                               for o in mission['objectives_text']])

    def source(self, mission_id):
        mission = self.missions[mission_id - 1]
        row = self.rows[mission['source_line']]
        return {'id': mission_id, 'name': mission['name'],
                'name_hex': row['raw_fields_hex'][1], 'source_line': mission['source_line'],
                'source_record_sha256': row['source_record_sha256'],
                'description_count': mission['step_field'],
                'main_side_classification': 'UNKNOWN'}


def packet(slot, subtype, value):
    """Synthetic test stimulus, not an implementation of the production codec."""
    if subtype not in (4, 5):
        raise ValueError('Scenario scope only includes DB4/DB5')
    return bytes((0xdb, subtype, 0, 0, 0)) + struct.pack('<II', slot, value)


class Player:
    def __init__(self, evidence):
        self.evidence = evidence
        self.oracle = oracle.CurrentQuestRecordTests(methodName='runTest')
        self.oracle.image, self.oracle.texts = evidence.image, evidence.texts
        self.vm = self.oracle.vm()
        self.vm.mem_write(UI + 0xc2144, struct.pack('<hh', 0, 1))
        self.refreshes = 0
        self.trace = []
        refresh = oracle.BASE + 0xc9170
        self.hook = self.vm.hook_add(UC_HOOK_CODE, self._refresh, begin=refresh, end=refresh)

    def _refresh(self, uc, address, size, context):
        self.refreshes += 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.vm.hook_del(self.hook)

    def state(self):
        for offset in (0xc2100, 0xc2140, 0xc2148):
            self.oracle.assertEqual(bytes(self.vm.mem_read(UI + offset, 4)), b'\xa5' * 4)
        page, pages = struct.unpack('<hh', self.vm.mem_read(UI + 0xc2144, 4))
        return {'slots': list(struct.unpack('<15I', self.vm.mem_read(UI + 0xc2104, 60))),
                'page': page, 'pages': pages,
                'selected': struct.unpack('<I', self.vm.mem_read(UI + 0x232eb8, 4))[0],
                'suppression': struct.unpack('<I', self.vm.mem_read(UI + 0x232eb0, 4))[0],
                'refresh_calls': self.refreshes}

    def receive(self, slot, subtype, value, action='receive'):
        self.oracle.dispatch(self.vm, packet(slot, subtype, value))
        state = self.state()
        self.trace.append({'action': action, 'slot': slot, 'subtype': subtype,
                           'packed': value, 'state': state})
        return state

    def describe(self, slot, click):
        if not 0 <= slot < 15:
            raise ValueError('Only established journal slots can be selected')
        before = self.state()
        packed = before['slots'][slot]
        mission, selector = packed & 0xffff, packed >> 16
        index = max(selector - 1, 0)
        valid = 1 <= mission <= len(self.evidence.texts) and index < len(
            self.evidence.texts[mission - 1])
        pointer = self.oracle.description(self.vm, slot=slot, click=click)
        expected = self.oracle.pointers[mission - 1][index] if valid else oracle.BASE + 0x1b4640
        self.oracle.assertEqual(pointer, expected)
        text = self.evidence.texts[mission - 1][index] if valid else b''
        self.oracle.assertEqual(bytes(self.vm.mem_read(pointer, len(text) + 1)), text + b'\0')
        after = self.state()
        wanted = dict(before)
        if click:
            # Existing oracle stages page and click registers, not a page-button event.
            wanted['page'] = slot // 5
            if valid:
                wanted['selected'] = packed
        self.oracle.assertEqual(after, wanted)
        result = {'action': 'staged_page_select' if click else 'describe',
                  'slot': slot, 'packed': packed, 'valid_description': valid,
                  'text_hex': text.hex(), 'state': after,
                  'source_line': self.evidence.missions[mission - 1]['objectives_text'][index][
                      'source_line'] if valid else None}
        self.trace.append(result)
        return result


def lifecycle(evidence, subtype):
    """Receive actual source references, inspect three pages, replay, clear, replay."""
    with Player(evidence) as player:
        check = player.oracle.assertEqual
        slots = [0] * 15
        selected, refreshes, suppression = 0, 0, 1

        def receive(slot, value, pages, page, action):
            nonlocal selected, refreshes, suppression
            slots[slot] = value
            if subtype == 5:
                selected, refreshes = value, refreshes + 1
            elif slot == 14:
                refreshes += int(suppression == 0)
                suppression = 0
            check(player.receive(slot, subtype, value, action), {
                'slots': slots.copy(), 'page': page, 'pages': pages, 'selected': selected,
                'suppression': suppression, 'refresh_calls': refreshes})

        # 165 has the actual maximum 29 description rows; 418 has a literal
        # main-line title. Neither fact defines server progression or side quests.
        for slot, mission, pages in ((0, 1, 1), (5, 165, 2), (14, 418, 3)):
            receive(slot, 0x10000 | mission, pages, 0, 'receive_source_reference')
        for slot in (0, 5, 14):
            player.describe(slot, click=False)
            player.describe(slot, click=True)
            selected = slots[slot]
        receive(14, slots[14], 3, 2, 'duplicate')
        receive(14, slots[14], 3, 2, 'replay')
        for slot, mission in ((0, 1), (5, 165), (14, 418)):
            value = (len(evidence.texts[mission - 1]) << 16) | mission
            receive(slot, value, 3, player.state()['page'], 'replace_with_last_description')
            player.describe(slot, click=False)
            player.describe(slot, click=True)
            selected = value
        for slot, pages in ((14, 2), (5, 1), (0, 1)):
            receive(slot, 0, pages, 0, 'clear')
            receive(slot, 0, pages, 0, 'duplicate_clear')
            player.describe(slot, click=False)
        receive(14, 0x10000 | 418, 3, 0, 'old_record_after_clear')
        player.describe(14, click=True)
        return {'scenario': 'journal_lifecycle', 'subtype': subtype, 'status': 'PASS',
                'trace': player.trace}


def bounds(evidence, subtype):
    trace = []
    with Player(evidence) as player:
        for value in (1, 0x10001, 0x20001, 0x30001, 0x80000001,
                      0, 0xffff0000, 419, 0xffffffff):
            before = player.state()
            state = player.receive(14, subtype, value, 'description_boundary')
            player.oracle.assertEqual(state['slots'], [0] * 14 + [value])
            player.oracle.assertEqual(state['selected'], value if subtype == 5 else before['selected'])
            player.oracle.assertEqual(state['pages'], 3 if 1 <= (value & 0xffff) <= 418 else 1)
            player.describe(14, click=False)
            player.describe(14, click=True)
        trace.extend(player.trace)
    for slot in (15, 255, 0x80000000, 0xffffffff):
        with Player(evidence) as player:
            player.receive(0, subtype, 0x10001)
            player.describe(0, click=True)
            before = player.state()
            player.oracle.dispatch(player.vm, packet(slot, subtype, 0x801a2), stop=0xc9688)
            after = player.state()
            expected = dict(before)
            if subtype == 5:
                expected['selected'] = 0x801a2
            player.oracle.assertEqual(after, expected)
            trace.append({'action': 'invalid_slot_assertion_boundary', 'slot': slot,
                          'assertion_continuation': 'NOT_EXECUTED', 'state': after})
    for length in range(1, 13):
        with Player(evidence) as player:
            player.receive(0, subtype, 0x10001)
            player.describe(0, click=True)
            before = player.state()
            with player.oracle.assertRaises(UcError):
                player.oracle.dispatch(player.vm, packet(1, subtype, 0x801a2)[:length])
            player.oracle.assertEqual(player.state(), before)
            trace.append({'action': 'truncated_record_native_fault', 'length': length,
                          'journal_state_unchanged': True})
    return {'scenario': 'journal_bounds', 'subtype': subtype, 'status': 'PASS', 'trace': trace}


def run(evidence=None):
    evidence = evidence or Evidence()
    return {'qualification': 'OFFLINE_NATIVE_JOURNAL_SCENARIOS_ONLY',
            'stimulus': 'SYNTHETIC logical S2C records, initial memory and staged page/click inputs',
            'source_text_status': 'ORIGINAL_BYTES; text claims are not runtime rules',
            'initial_state_status': 'TEST_PRECONDITION_ONLY; authoritative initial state UNKNOWN',
            'image_sha256': oracle.quest.routes.IMAGE_SHA,
            'mission_source_sha256': oracle.SOURCE_SHA,
            'mission_decoded_sha256': oracle.DECODED_SHA,
            'source_entries': [evidence.source(i) for i in (1, 165, 418)],
            'main_side_classification': 'UNKNOWN; literal titles are presentation evidence only',
            'unimplemented_rules': list(UNKNOWN_RULES),
            'scenarios': [scenario(evidence, subtype) for scenario in (lifecycle, bounds)
                          for subtype in (4, 5)]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Print complete observations to stdout')
    args = parser.parse_args(argv)
    report = run()
    if not args.json:
        report = {**report, 'scenarios': [
            {k: v for k, v in scenario.items() if k != 'trace'} |
            {'observations': len(scenario['trace'])} for scenario in report['scenarios']]}
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
