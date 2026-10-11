"""C++ loopback 02/2A -> original-code-generated world tail, not live UI E2E."""
import json
from pathlib import Path
import tempfile
import unittest

import test_recovered_dual_connection_server as dual
from test_current_world_ready_builder import current_world_ready_wire


class RecoveredWorldEntryServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dual.RecoveredDualConnectionServerTests.setUpClass()
        cls.body=bytes.fromhex(json.loads((dual.ROOT/'tests/fixtures/recovered-world-entry.json').read_text())['body_hex'])

    def harness(self):
        h=dual.RecoveredDualConnectionServerTests('test_explicit_character_port_matches_05_and_accepts_g')
        original=h.configuration
        def configuration(*args,**kwargs):
            config=original(*args,**kwargs)
            config['development']['recovered_world_entry']=True
            return config
        h.configuration=configuration
        return h

    def selected(self,h,game,identity,coordinates=None):
        reply=h.read_frame(game,2,26)
        self.assertEqual(reply[3:-1],bytes(22))
        entry=h.read_frame(game,0x2a,40)
        self.assertEqual(int.from_bytes(entry[3:5],'little')&0x3fff,identity)
        expected=bytearray(self.body)
        profile=dual.profile(dual.HEROES[0])
        expected[13]=(expected[13]&0x1f)|(profile[32]<<5)
        expected[15]=(expected[15]&0x1f)|(profile[36]&0xe0)
        expected[20:24]=bytes((profile[36],0,profile[38],profile[39]))
        if coordinates is not None:
            x,y=coordinates
            expected[28:32]=((expected[28]&3)|(x<<2)|(y<<17)).to_bytes(4,'little')
        self.assertEqual(entry[5:-1],expected[2:])
        h.silent(game)

    def create(self,h,server):
        with h.connect(server.endpoint) as login:
            endpoint=h.login(login);h.list_characters(login)
            with h.connect(endpoint) as game:
                h.game_ready(game);h.create(game,dual.HEROES[0])
                identity=h.snapshot(server.database)[1][0][0]
                game.sendall(h.frame(0x18,b'\x01')+h.frame(0x1a,dual.selection_payload(0)))
                self.selected(h,game,identity)
                h.send(game,current_world_ready_wire(identity),fragmented=True)
                self.state_candidate(h,game)
        h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',1)
        return endpoint,identity

    def state_candidate(self,h,game):
        # Retained helper name for callers; historical scalar injection is retired.
        h.silent(game)

    def test_create_restart_and_existing_selection_accept_original_world_tail(self):
        h=self.harness()
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'world.db'
            with h.server(database=database) as server:
                _,identity=self.create(h,server)
                saved=h.snapshot(database)
                self.assertEqual(h.marker_count(server.root,'WORLD_ENTRY_CANDIDATE_SENT'),1)
            with h.server(database=database,registration=False) as server:
                with h.connect(server.endpoint) as login:
                    endpoint=h.login(login);listing=h.list_characters(login)
                    self.assertEqual(listing[3],1)
                    with h.connect(endpoint) as game:
                        h.game_ready(game)
                        login.close()
                        game.sendall(h.frame(0x1a,dual.selection_payload(0)))
                        self.selected(h,game,identity)
                        game.sendall(current_world_ready_wire(identity,(4,3)))
                        self.state_candidate(h,game)
                h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',1)
                self.assertEqual(h.marker_count(server.root,'WORLD_STATE_CANDIDATE_SENT'),0)
                h.unchanged(database,saved)
                self.assertIn('config_flag=0',h.logs(server.root))
                self.assertNotIn('InWorld established',h.logs(server.root))

    def test_ready_checks_identity_order_constants_and_checksum(self):
        h=self.harness()
        with h.server() as server:
            endpoint,identity=self.create(h,server);saved=h.snapshot(server.database)
            logical=b'\x1f\0\x23\0\x1c'+identity.to_bytes(2,'little')+b'\x01\0'
            bad_flag=bytearray(logical);bad_flag[-2]=2
            bad_constant=bytearray(logical);bad_constant[1]=1
            bad_order=logical[2:4]+logical[:2]+logical[4:]
            wire=current_world_ready_wire(identity)
            cases=(current_world_ready_wire(identity+1),h.frame(bad_flag[0],bad_flag[1:]),
                   h.frame(bad_constant[0],bad_constant[1:]),h.frame(bad_order[0],bad_order[1:]),
                   wire[:-1]+bytes([wire[-1]^1]),b'\xff\xff')
            for wire in cases:
                with self.subTest(wire_length=len(wire)),h.connect(endpoint) as game:
                    h.game_ready(game)
                    game.sendall(h.frame(0x1a,dual.selection_payload(0)))
                    self.selected(h,game,identity)
                    game.sendall(wire);h.closed(game)
                h.unchanged(server.database,saved)
                self.assertEqual(h.marker_count(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED'),1)
                self.assertEqual(h.marker_count(server.root,'WORLD_STATE_CANDIDATE_SENT'),0)

    def test_separate_frames_and_incomplete_checksum_never_advance_early(self):
        h=self.harness()
        with h.server() as server:
            endpoint,identity=self.create(h,server)
            with h.connect(endpoint) as game:
                h.game_ready(game);game.sendall(h.frame(0x1a,dual.selection_payload(0)))
                self.selected(h,game,identity)
                game.sendall(h.frame(0x1f,b'\0')+h.frame(0x23,b'\0'))
                h.silent(game)
                tail=h.frame(0x1c,identity.to_bytes(2,'little')+b'\x01\0')
                game.sendall(tail[:-1]);h.silent(game)
                self.assertEqual(h.marker_count(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED'),1)
                game.sendall(tail[-1:]);self.state_candidate(h,game)
                h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',2)
                self.assertEqual(h.marker_count(server.root,'WORLD_STATE_CANDIDATE_SENT'),0)
                # No repeat or invented gameplay acceptance after the known tail.
                game.sendall(tail);h.closed(game)
                self.assertEqual(h.marker_count(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED'),2)
                self.assertEqual(h.marker_count(server.root,'WORLD_STATE_CANDIDATE_SENT'),0)


if __name__=='__main__':unittest.main()
