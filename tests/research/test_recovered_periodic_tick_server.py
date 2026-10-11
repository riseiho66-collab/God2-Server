"""Own-loopback periodic-frame regressions, not live rendered-world acceptance."""
import unittest

import test_recovered_movement_server as movement
from test_current_movement import movement_wire
from test_current_periodic_tick import periodic_wire
from test_current_world_ready_builder import current_world_ready_wire


class RecoveredPeriodicTickServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        movement.RecoveredMovementServerTests.setUpClass()

    def test_fragmented_ticks_do_not_ack_mutate_or_advance_ring(self):
        m = movement.RecoveredMovementServerTests()
        w, h = m.harness()
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            with h.connect(endpoint) as game:
                m.ready(w, h, game, identity)
                tick = periodic_wire()
                for split in range(1, len(tick)):
                    game.sendall(tick[:split]); h.silent(game)
                    game.sendall(tick[split:]); h.silent(game)
                    self.assertEqual(m.positions(server.database), [])
                game.sendall(movement_wire(18, 12, 1)); m.ack(h, game, 1)
                saved = m.positions(server.database)
                game.sendall(tick * 5); h.silent(game)
                self.assertEqual(m.positions(server.database), saved)
                game.sendall(movement_wire(17, 13, 2)); m.ack(h, game, 2)

    def test_original_mixed_queue_and_coalesced_frames(self):
        m = movement.RecoveredMovementServerTests()
        w, h = m.harness()
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            with h.connect(endpoint) as game:
                m.ready(w, h, game, identity)
                game.sendall(periodic_wire([(18, 12, 1), (17, 13, 2)]))
                m.ack(h, game, 1); m.ack(h, game, 2); h.silent(game)
                game.sendall(periodic_wire() + movement_wire(18, 12, 3) + periodic_wire())
                m.ack(h, game, 3); h.silent(game)
                self.assertEqual(m.positions(server.database)[0][1:5], (2, 15, 18, 12))

    def test_invalid_tick_closes_without_position_commit(self):
        m = movement.RecoveredMovementServerTests()
        w, h = m.harness()
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            bad_checksum = bytearray(periodic_wire()); bad_checksum[-1] ^= 1
            cases = [bytes(bad_checksum), h.frame(0x30, b'\x01'), h.frame(0x30, b''),
                     h.frame(0x30, b'\x00\x00'), h.frame(0x31, b'\x00'),
                     h.frame(0x2e, b'\x12\x00\x0c\x00\x01\xa5\x30\x01')]
            for wire in cases:
                with self.subTest(wire=wire.hex()), h.connect(endpoint) as game:
                    m.ready(w, h, game, identity)
                    game.sendall(wire); h.closed(game)
                self.assertEqual(m.positions(server.database), [])

    def test_tick_coalesced_with_world_tail_but_not_before_selection(self):
        m = movement.RecoveredMovementServerTests()
        w, h = m.harness()
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            with h.connect(endpoint) as premature:
                h.game_ready(premature)
                premature.sendall(periodic_wire()); h.closed(premature)
            with h.connect(endpoint) as game:
                h.game_ready(game)
                game.sendall(h.frame(0x1a, movement.world.dual.selection_payload(0)))
                w.selected(h, game, identity)
                game.sendall(current_world_ready_wire(identity) + periodic_wire())
                w.state_candidate(h, game); h.silent(game)
                self.assertEqual(m.positions(server.database), [])
                game.sendall(movement_wire(18, 12, 1)); m.ack(h, game, 1)


if __name__ == '__main__':
    unittest.main()
