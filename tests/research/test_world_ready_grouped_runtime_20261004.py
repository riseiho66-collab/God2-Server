"""Bounded owned-loopback world initializer regression; NOT_LIVE_CLIENT_UI.

Uses frozen formal-config TCP clone/transport helpers. No working client,
formal DB, desktop or server is changed. Explicit candidate is required;
port2599 must be free. Packet peers are synthetic, not live raw capture.
"""
from contextlib import contextmanager, ExitStack
from pathlib import Path
import hashlib, json, os, re, time, unittest
import test_native_guild_formal_server_20261004 as formal

ROOT = formal.ROOT
OUTPUT = Path(os.environ['GOD2_WORLD_READY_GROUPED_TEST_OUTPUT']) if os.environ.get('GOD2_WORLD_READY_GROUPED_TEST_OUTPUT') else None
EVENTS = []


class GroupedWorldReadyRuntimeTests(formal.NativeGuildFormalTests):
    @classmethod
    def setUpClass(cls):
        if formal.PORT != 2599:
            raise AssertionError('This bounded test exclusively owns loopback2599')
        super().setUpClass()
        if OUTPUT is not None:
            OUTPUT.mkdir(parents=True, exist_ok=False)

    @contextmanager
    def isolated(self, label):
        with self.server() as state:
            try:
                yield state
            finally:
                if OUTPUT is not None:
                    (OUTPUT/(label+'-server.log')).write_bytes((state.here/'server.log').read_bytes())
                    (OUTPUT/(label+'-stdout.log')).write_bytes((state.here/'stdout.log').read_bytes())

    def before_tail(self, s, lifetime):
        """Same normal dual-connection auth/selection as frozen enter_peer.

        Stops at received2A, before any initializer is sent. Credentials are
        existing isolated-fixture credentials and never written to evidence.
        """
        h = s.helper
        offset = len(s.log())
        login = lifetime.enter_context(h.connect(s.endpoint))
        h.handshake(login)
        login.sendall(h.frame(*formal.fixture.dual.credential(4, b'codexslow', b'labtest2345')))
        h.read_frame(login, 0x1d, 176); h.read_frame(login, 4, 8)
        address = h.read_frame(login, 5, 12)
        h.read_frame(login, 6, 8); h.read_frame(login, 0x0a, 20)
        self.assertEqual(h.list_characters(login)[3], 1)
        peer = lifetime.enter_context(h.connect(('127.0.0.1', int.from_bytes(address[9:11], 'little'))))
        h.handshake(peer, game=True)
        peer.sendall(h.frame(*formal.fixture.dual.credential(0, b'codexslow', b'labtest2345')))
        h.read_frame(peer, 0x1f, 128)
        peer.sendall(h.frame(0x1a, formal.fixture.dual.selection_payload(0)))
        h.read_frame(peer, 2, 26)
        entry = h.read_frame(peer, 0x2a, 40)
        self.assertEqual(int.from_bytes(entry[3:5], 'little') & 0x3fff, 4)
        ids = re.findall(r'session_id=(\d+) EXISTING_CHARACTER_BOUND character_id=4;', s.log()[offset:])
        self.assertEqual(len(ids), 1, 'Selection must identify one fresh owned world session')
        return peer, ids[0]

    @staticmethod
    def logical(flag):
        return bytes((0x30, 0, 0x1f, 0, 0x23, 0, 0x1c, 4, 0, flag, 0))

    @staticmethod
    def wire(s, logical):
        return s.helper.frame(logical[0], logical[1:])

    def session_lines(self, s, sid):
        return [line for line in s.log().splitlines() if re.search(r'session_id='+sid+r'\b', line)]

    def published(self, s, peer, sid, flag, wire, shape):
        frames = self.drain(s, peer, first=True)
        self.assertTrue(frames, 'Owned world projection must publish native records')
        lines = self.session_lines(s, sid)
        tails = [line for line in lines if 'WORLD_INITIALIZER_TAIL_ACCEPTED' in line]
        self.assertEqual(len(tails), 1)
        self.assertIn('config_flag='+str(flag), tails[0])
        self.assertTrue(any('OWNED_WORLD_SNAPSHOT_RESTORED' in line for line in lines), lines)
        self.assertTrue(any('RECOVERED_WORLD_BATCH_HANDLED' in line for line in lines), lines)
        self.assertFalse(any('World initialization tail contract rejected' in line for line in lines))
        # A normal readonly help route proves the post-tail parser receives
        # subsequent world records; it must preserve all typed saved rows.
        menu = self.menu(s, peer)
        self.assertEqual(menu[:5], b'\x7a\x1c\0\4\xe7')
        EVENTS.append({'page':936 if flag else 950, 'shape':shape, 'session_id':int(sid),
                       'initializer_wire_hex':wire.hex(), 'initializer_wire_length':len(wire),
                       'world_ready_once':True, 'config_flag':flag, 'world_projection':True,
                       'subsequent_readonly_help_received':True, 'accepted':True})

    def test_grouped14_following_world_frame_both_locales(self):
        for page, flag in ((950, 0), (936, 1)):
            with self.subTest(page=page), self.isolated('grouped14-'+str(page)) as s, ExitStack() as lifetime:
                peer, sid = self.before_tail(s, lifetime)
                wire = self.wire(s, self.logical(flag)); self.assertEqual(len(wire), 14)
                # One TCP write joins initializer and a distinct worldTick frame.
                # Session must stop exactly after initializer and preserve Tick.
                peer.sendall(wire+self.wire(s, b'\x30\0'))
                self.published(s, peer, sid, flag, wire, 'native14+separate_world_tick_coalesced')

    def test_four_frames23_fragmented_both_locales(self):
        for page, flag in ((950, 0), (936, 1)):
            with self.subTest(page=page), self.isolated('fourframes23-'+str(page)) as s, ExitStack() as lifetime:
                peer, sid = self.before_tail(s, lifetime)
                logical = self.logical(flag)
                wire = b''.join(self.wire(s, logical[lo:hi]) for lo, hi in ((0,2),(2,4),(4,6),(6,11)))
                self.assertEqual(len(wire), 23)
                for index, byte in enumerate(wire):
                    peer.sendall(bytes((byte,)))
                    if index+1 < len(wire):
                        s.helper.silent(peer)
                        self.assertFalse(any('WORLD_INITIALIZER_TAIL_ACCEPTED' in line for line in self.session_lines(s,sid)))
                s.helper.silent(peer)
                peer.sendall(self.wire(s, b'\x30\0'))
                self.published(s, peer, sid, flag, wire, 'four_whole_records23_bytewise_tcp')

    def test_strict_rejections_both_locales_no_world_publication(self):
        for page, flag in ((950, 0), (936, 1)):
            with self.isolated('reject-'+str(page)) as s:
                base = self.logical(flag)
                mutations = {
                    'duplicate_tick': base,
                    'wrong_order': base[:2]+b'\x23\0\x1f\0'+base[6:],
                    'wrong_identity': base[:7]+b'\x05'+base[8:],
                    'invalid_flag': base[:9]+b'\x02'+base[10:],
                    'checksum': base,
                }
                for reason, logical in mutations.items():
                    with self.subTest(page=page, reason=reason), ExitStack() as lifetime:
                        peer, sid = self.before_tail(s, lifetime)
                        before = self.saved(s)
                        wire = self.wire(s, logical)
                        if reason == 'duplicate_tick': wire = self.wire(s,b'\x30\0')+wire
                        if reason == 'checksum': wire = wire[:-1]+bytes((wire[-1]^1,))
                        peer.sendall(wire)
                        s.helper.closed(peer)
                        lines = self.session_lines(s,sid)
                        self.assertTrue(any('World initialization tail contract rejected' in line for line in lines), lines)
                        for marker in ('WORLD_INITIALIZER_TAIL_ACCEPTED','OWNED_WORLD_SNAPSHOT_RESTORED','RECOVERED_WORLD_BATCH_HANDLED'):
                            self.assertFalse(any(marker in line for line in lines), marker)
                        self.assertEqual(self.saved(s),before,'Rejected initializer changed saved state')
                        EVENTS.append({'page':page,'reason':reason,'session_id':int(sid),
                            'initializer_wire_hex':wire.hex(),'rejected':True,'world_published':False,'SQL_exact':True})
                    # Account lease must be released before next legitimate auth.
                    deadline=time.monotonic()+3
                    while not any('DISCONNECT_GAME_EXIT' in line for line in self.session_lines(s,sid)):
                        self.assertLess(time.monotonic(),deadline,'Rejected-session cleanup did not finish');time.sleep(.01)


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(GroupedWorldReadyRuntimeTests(name) for name in GroupedWorldReadyRuntimeTests.__dict__ if name.startswith('test_'))


if __name__ == '__main__':
    result = unittest.main(exit=False)
    if OUTPUT is not None and OUTPUT.exists():
        receipt={'scope':'NOT_LIVE_CLIENT_UI_OWNED_LOOPBACK2599_COPIED_DB','accepted':result.result.wasSuccessful(),
            'tests_run':result.result.testsRun,'failures':len(result.result.failures),'errors':len(result.result.errors),
            'events':EVENTS,'candidate_path':str(formal.BINARY),'candidate_sha256':hashlib.sha256(formal.BINARY.read_bytes()).hexdigest(),
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'desktop_used':False,'live_client_used':False}
        (OUTPUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.result.wasSuccessful() else 1)
