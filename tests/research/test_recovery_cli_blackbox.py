"""Subprocess CLI checks using synthetic inputs and temporary output trees only."""
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

from tools.strike_lab import recover_companions as companions
from tools.strike_lab import recover_items as items
from tools.strike_lab import recover_quests as quests


REPO = Path(__file__).resolve().parents[2]
KINDS = ('items', 'quests', 'combat_skills', 'companions')
SENTINEL = b'previous artifact must survive failure\n'


def csvz(decoded):
    # Literal-only encoding exercises the real decoder, without client resources.
    chunks = [b'\xff' + decoded[i:i + 8] for i in range(0, len(decoded), 8)]
    return b'\x05\x16' + struct.pack('<I', len(decoded)) + b'\0' + b''.join(chunks)


def item_row(item_id=1):
    return str(item_id).encode() + b',0,Resource,1,Name,200,100,,,,,,,8400,' + b','.join([b'0'] * 11)


def fixtures(kind):
    header = b','.join(label.encode('cp950') for label in items.LABELS)
    if kind == 'items':
        return {items.SOURCE: b'\n'.join([
            b'RowDesc,1', header, b'ItemType,1', b'1,1000,WPN,Weapon',
            b'WPN,1', item_row()])}
    if kind == 'quests':
        rows = {'missions': b'1,Name,1\n,,1,Text',
                'requirements': b'1,,1,1,0,0,0,0,0,0',
                'daily': b'1,1,Name,1,0,0,0,0,0,0,1,Text'}
        return {quests.PREFIX + name: b'\n'.join([
            *([b'Synthetic metadata'] * (header_line - 1)),
            quests.HEADERS[table].encode('cp950'), tag + b',1', rows[table]])
            for table, (name, tag, header_line, _) in quests.SPECS.items()}
    if kind == 'combat_skills':
        return {items.SOURCE: header + b'\nSKB,1\n' + item_row(6501),
                'Data/Patch/Skill.csvZ': b'God Menu,1.01,5\n1,1,Synthetic menu'}
    types = [b'1,100,' + tag.encode() + b',' + label.encode('cp950')
             for tag, label in companions.FAMILY_LABELS.items()]
    sections = [b'ItemType,4', *types]
    for name in companions.SECTIONS[1:]:
        sections.extend([name.encode() + (b',2' if name == 'GOD' else b',1'), b'1,Raw'])
        if name == 'GOD':
            sections.append(b'2,Raw')
    messages = [str(key).encode() + b',,' + claim[2].encode('cp950')
                for key, claim in companions.MESSAGE_CLAIMS.items()]
    return {companions.GAME: b'\n'.join(sections),
            companions.MESSAGES: b'\n'.join([
                b'SystemMessage,' + str(len(messages)).encode(), *messages])}


class RecoveryCliBlackboxTests(unittest.TestCase):
    def prepare(self, folder, kind, decoded=None):
        base = Path(folder)
        client, classic, xjz = (base / name for name in ('client', 'classic', 'xjz'))
        for root in (client, classic, xjz):
            root.mkdir()
        for relative, plain in (fixtures(kind) if decoded is None else decoded).items():
            path = client / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(csvz(plain))
        for root, paths in ((classic, companions.CLASSIC_FILES), (xjz, companions.XJZ_FILES)):
            for relative in paths:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Synthetic legacy fixture\n', encoding='utf-8')
        for root, relative, anchor in (
            (classic, 'src/God2.ClassicServer.Runtime/PhysicalSkillDamageRuntime.cs', 'No community-measured physical'),
            (classic, 'src/God2.ClassicServer.Runtime/MagicSkillDamageRuntime.cs', 'No community-measured magic'),
            (xjz, 'evidence-combat-formula-v0.md', 'packet_evidence_boundary'),
            (xjz, 'cpp/xjz_evidence_repository.hpp', 'GetSkillBookTemplate('),
            (xjz, 'cpp/xjz_evidence_models.hpp', 'struct SkillBookTemplate'),
        ):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic anchor: ' + anchor, encoding='utf-8')
        cwd = REPO
        output = base / 'output' / (kind + '.json')
        if kind == 'combat_skills':
            # Its fixed output policy is retained; relocate only the test package.
            cwd = base / 'package'
            package = cwd / 'tools' / 'strike_lab'
            package.mkdir(parents=True)
            for name in ('recover_combat_skills.py', 'omega_assets.py'):
                shutil.copyfile(REPO / 'tools' / 'strike_lab' / name, package / name)
            output = cwd / 'artifacts/world-atlas/combat-skills.json'
        args = [sys.executable, '-m', 'tools.strike_lab.recover_' + kind,
                '--client' if kind == 'quests' else '--client-root', str(client),
                '--output', str(output)]
        if kind in ('combat_skills', 'companions'):
            args.extend(['--classic-root', str(classic), '--xjz-root', str(xjz)])
        return args, cwd, client, output

    def run_cli(self, args, cwd):
        return subprocess.run(args, cwd=cwd, capture_output=True, timeout=10)

    def assert_rejected(self, args, cwd, output):
        # Check both creation and replacement: failed extraction must publish neither.
        for existing in (False, True):
            if existing:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(SENTINEL)
            result = self.run_cli(args, cwd)
            self.assertNotEqual(result.returncode, 0, result.stdout.decode(errors='replace'))
            self.assertEqual(result.stdout, b'', result.stdout.decode(errors='replace'))
            self.assertTrue(result.stderr)
            if existing:
                self.assertEqual(output.read_bytes(), SENTINEL)
            else:
                self.assertFalse(output.exists(), 'Failed CLI published an artifact')

    def test_valid_cli_determinism_and_unknown_semantics(self):
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                args, cwd, _, output = self.prepare(folder, kind)
                result = self.run_cli(args, cwd)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
                self.assertTrue(result.stdout)
                first = output.read_bytes()
                self.assertEqual(self.run_cli(args, cwd).returncode, 0)
                self.assertEqual(output.read_bytes(), first)
                catalog = json.loads(first)
                if kind == 'items':
                    self.assertFalse(catalog['records'][0]['runtime_eligible'])
                    self.assertIsNone(catalog['records'][0]['server_effect_handler'])
                    self.assertEqual(bytes.fromhex(catalog['records'][0]['raw_fields_hex'][4]), b'Name')
                elif kind == 'quests':
                    self.assertEqual(catalog['quests'][0]['transitions'], 'UNKNOWN')
                    self.assertEqual(catalog['counts']['server_integrated'], 0)
                elif kind == 'combat_skills':
                    self.assertEqual(bytes.fromhex(catalog['skills']['definitions'][0]['raw_record_hex']), item_row(6501))
                    self.assertNotIn('runtime_skill_id', catalog['skills']['definitions'][0])
                else:
                    self.assertTrue(all(not row['runtime_eligible'] for row in catalog['transition_and_restriction_evidence']))

    def test_missing_client_rejected(self):
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                args, cwd, client, output = self.prepare(folder, kind)
                args[args.index(str(client))] = str(client / 'missing')
                self.assert_rejected(args, cwd, output)

    def test_csvz_truncation_and_expansion_bound_rejected(self):
        for kind in KINDS:
            for corruption in ('truncated', 'oversized', 'magic'):
                with self.subTest(kind=kind, corruption=corruption), tempfile.TemporaryDirectory() as folder:
                    args, cwd, client, output = self.prepare(folder, kind)
                    source = client / next(iter(fixtures(kind)))
                    raw = source.read_bytes()
                    if corruption == 'truncated':
                        raw = raw[:-1]
                    elif corruption == 'oversized':
                        raw = raw[:2] + struct.pack('<I', 64 * 1024 * 1024 + 1) + raw[6:]
                    else:
                        raw = b'XX' + raw[2:]
                    source.write_bytes(raw)
                    self.assert_rejected(args, cwd, output)

    def test_column_or_classification_header_mismatch_rejected(self):
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                decoded = fixtures(kind)
                relative = next(iter(decoded))
                old = (b'STEP' if kind == 'quests' else
                       companions.FAMILY_LABELS['GOD'].encode('cp950') if kind == 'companions' else b'ITEM_ID')
                decoded[relative] = decoded[relative].replace(old, b'UNSUPPORTED', 1)
                args, cwd, _, output = self.prepare(folder, kind, decoded)
                self.assert_rejected(args, cwd, output)

    def test_truncated_decoded_sections_rejected(self):
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                decoded = fixtures(kind)
                relative = next(iter(decoded))
                decoded[relative] = decoded[relative].rsplit(b'\n', 1)[0]
                args, cwd, _, output = self.prepare(folder, kind, decoded)
                self.assert_rejected(args, cwd, output)

    def test_companion_section_counts_rejected(self):
        for count in (b'1', b'3', b'+2', b'2,extra'):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as folder:
                decoded = fixtures('companions')
                decoded[companions.GAME] = decoded[companions.GAME].replace(b'GOD,2\n', b'GOD,' + count + b'\n')
                args, cwd, _, output = self.prepare(folder, 'companions', decoded)
                self.assert_rejected(args, cwd, output)

    def test_quest_missing_definition_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            decoded = fixtures('quests')
            relative = quests.PREFIX + quests.SPECS['requirements'][0]
            decoded[relative] = decoded[relative].rsplit(b'\n', 1)[0]
            args, cwd, _, output = self.prepare(folder, 'quests', decoded)
            self.assert_rejected(args, cwd, output)

    def test_unknown_combat_lookup_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            args, cwd, _, output = self.prepare(folder, 'combat_skills')
            self.assert_rejected(args + ['--item-id', '-1'], cwd, output)

    def test_output_path_errors_do_not_print_success(self):
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                args, cwd, _, output = self.prepare(folder, kind)
                output.parent.mkdir(parents=True)
                output.mkdir()
                result = self.run_cli(args, cwd)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b'')
                self.assertTrue(result.stderr)
                self.assertEqual(list(output.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
