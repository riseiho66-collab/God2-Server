"""Bounded loopback position tests against the existing build; no client UI.

Movement packets come from the original executable's builder in movement_wire.
SQL is used only to inspect state and inject persistence failures/conflicts.
Run: python -B -m unittest discover -s tests/research
     -p test_recovered_position_blackbox.py -v
"""
from contextlib import closing
import sqlite3
import unittest

import test_recovered_movement_server as movement
from test_current_movement import movement_wire
from test_current_world_ready_builder import current_world_ready_wire


dual = movement.world.dual


class RecoveredPositionBlackboxTests(unittest.TestCase):
    harness = movement.RecoveredMovementServerTests.harness
    ack = movement.RecoveredMovementServerTests.ack
    positions = movement.RecoveredMovementServerTests.positions

    @classmethod
    def setUpClass(cls):
        movement.RecoveredMovementServerTests.setUpClass()

    def select(self, w, h, game, identity, coordinates=(17, 13),
               account=dual.OWNER, slot=0):
        h.game_ready(game, name=account)
        game.sendall(h.frame(0x1a, dual.selection_payload(slot)))
        w.selected(h, game, identity, coordinates)

    def ready(self, w, h, game, identity, coordinates=(17, 13),
              account=dual.OWNER, slot=0):
        self.select(w, h, game, identity, coordinates, account, slot)
        game.sendall(current_world_ready_wire(identity))
        w.state_candidate(h, game)

    def execute(self, database, sql, parameters=()):
        with closing(sqlite3.connect(database, timeout=dual.IO_TIMEOUT)) as db:
            db.execute(sql, parameters)
            db.commit()

    def create_character(self, h, server, account, name):
        with h.connect(server.endpoint) as login:
            endpoint = h.login(login, name=account)
            h.list_characters(login)
            with h.connect(endpoint) as game:
                h.game_ready(game, name=account)
                h.create(game, name)
        return next(row[0] for row in h.snapshot(server.database)[1] if row[3] == name)

    def test_duplicate_selection_reserves_character_before_world_ready(self):
        w, h = self.harness()
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            before = h.snapshot(server.database)
            with h.connect(endpoint) as first:
                self.select(w, h, first, identity)
                for _ in range(2):
                    with h.connect(endpoint) as duplicate:
                        h.game_ready(duplicate)
                        duplicate.sendall(h.frame(0x1a, dual.selection_payload(0)))
                        h.closed(duplicate)
                    self.assertEqual(self.positions(server.database), [])
                    h.silent(first)
                first.sendall(current_world_ready_wire(identity))
                w.state_candidate(h, first)
                first.sendall(movement_wire(18, 12, 1))
                self.ack(h, first, 1)
            with h.connect(endpoint) as reconnected:
                self.ready(w, h, reconnected, identity, (18, 12))
                reconnected.sendall(movement_wire(17, 13, 1))
                self.ack(h, reconnected, 1)
            self.assertEqual(self.positions(server.database), [(identity, 2, 15, 17, 13, 2)])
            h.unchanged(server.database, before)

    def test_failed_or_abandoned_world_ready_releases_reservation(self):
        w, h = self.harness()
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            before = h.snapshot(server.database)
            for failure in ('wrong_identity', 'incomplete_tail', 'disconnect'):
                with self.subTest(failure=failure):
                    with h.connect(endpoint) as game:
                        self.select(w, h, game, identity)
                        if failure == 'wrong_identity':
                            game.sendall(current_world_ready_wire(identity + 1))
                            h.closed(game)
                        elif failure == 'incomplete_tail':
                            game.sendall(current_world_ready_wire(identity)[:-1])
                            h.silent(game)
                    self.assertEqual(self.positions(server.database), [])
                    with h.connect(endpoint) as reconnected:
                        self.ready(w, h, reconnected, identity)
            with h.connect(endpoint) as game:
                self.ready(w, h, game, identity)
                game.sendall(movement_wire(18, 12, 1))
                self.ack(h, game, 1)
            self.assertEqual(self.positions(server.database), [(identity, 2, 15, 18, 12, 1)])
            h.unchanged(server.database, before)

    def test_rejected_request_restores_last_commit_and_fresh_ring(self):
        w, h = self.harness()
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            before = h.snapshot(server.database)
            cases = {
                'duplicate': movement_wire(18, 12, 1),
                'skipped_slot': movement_wire(17, 13, 3),
                'nonadjacent': movement_wire(30, 30, 2),
                'invalid_batch_suffix': movement_wire(0, 0, 0, records=[(17, 13, 2), (30, 30, 3)]),
            }
            revision = 0
            for failure, wire in cases.items():
                with self.subTest(failure=failure):
                    with h.connect(endpoint) as game:
                        self.ready(w, h, game, identity)
                        game.sendall(movement_wire(18, 12, 1))
                        self.ack(h, game, 1)
                        revision += 1
                        saved = [(identity, 2, 15, 18, 12, revision)]
                        self.assertEqual(self.positions(server.database), saved)
                        game.sendall(wire)
                        h.closed(game)
                    self.assertEqual(self.positions(server.database), saved)
                    with h.connect(endpoint) as reconnected:
                        self.ready(w, h, reconnected, identity, (18, 12))
                        reconnected.sendall(movement_wire(17, 13, 1))
                        self.ack(h, reconnected, 1)
                        revision += 1
                    self.assertEqual(self.positions(server.database), [(identity, 2, 15, 17, 13, revision)])
            h.unchanged(server.database, before)

    def test_parallel_characters_and_accounts_keep_positions_and_rings_isolated(self):
        w, h = self.harness()
        with h.server() as server:
            endpoint, first_id = w.create(h, server)
            second_id = self.create_character(h, server, dual.OWNER, dual.HEROES[1])
            other_id = self.create_character(h, server, dual.OTHER, b'PositionOther')
            before = h.snapshot(server.database)
            with h.connect(endpoint) as first, h.connect(endpoint) as second, h.connect(endpoint) as other:
                self.ready(w, h, first, first_id)
                self.ready(w, h, second, second_id, slot=1)
                self.ready(w, h, other, other_id, account=dual.OTHER)
                first.sendall(movement_wire(18, 12, 1))
                self.ack(h, first, 1)
                second.sendall(movement_wire(17, 13, 1))
                self.ack(h, second, 1)
                other.sendall(movement_wire(18, 12, 1))
                self.ack(h, other, 1)
                first.sendall(movement_wire(17, 13, 2))
                self.ack(h, first, 2)
                # A rejected duplicate must release neither of the other bindings.
                second.sendall(movement_wire(18, 12, 1))
                h.closed(second)
                other.sendall(movement_wire(18, 12, 2))
                self.ack(h, other, 2)
                first.sendall(movement_wire(18, 12, 3))
                self.ack(h, first, 3)
            expected = [(first_id, 2, 15, 18, 12, 3),
                        (second_id, 2, 15, 17, 13, 1),
                        (other_id, 2, 15, 18, 12, 2)]
            self.assertEqual(self.positions(server.database), expected)
            for identity, account, slot, point in (
                    (first_id, dual.OWNER, 0, (18, 12)),
                    (second_id, dual.OWNER, 1, (17, 13)),
                    (other_id, dual.OTHER, 0, (18, 12))):
                with h.connect(endpoint) as game:
                    self.ready(w, h, game, identity, point, account, slot)
            self.assertEqual(self.positions(server.database), expected)
            h.unchanged(server.database, before)

    def test_external_position_change_rejects_stale_entry_and_move(self):
        for phase in ('selected', 'ready'):
            for existing in (False, True):
                with self.subTest(phase=phase, existing=existing):
                    w, h = self.harness()
                    with h.server() as server:
                        endpoint, identity = w.create(h, server)
                        before = h.snapshot(server.database)
                        if existing:
                            with h.connect(endpoint) as initial:
                                self.ready(w, h, initial, identity)
                                initial.sendall(movement_wire(17, 13, 1))
                                self.ack(h, initial, 1)
                        with h.connect(endpoint) as stale:
                            self.select(w, h, stale, identity)
                            if phase == 'ready':
                                stale.sendall(current_world_ready_wire(identity))
                                w.state_candidate(h, stale)
                            if existing:
                                self.execute(server.database, 'UPDATE recovered_positions SET x=18,y=12,revision=revision+1 WHERE character_id=?', (identity,))
                            else:
                                self.execute(server.database, 'INSERT INTO recovered_positions VALUES(?,2,15,18,12,1)', (identity,))
                            saved = self.positions(server.database)
                            stale.sendall(current_world_ready_wire(identity) if phase == 'selected'
                                          else movement_wire(17, 13, 1))
                            h.closed(stale)
                            self.assertEqual(self.positions(server.database), saved)
                        with h.connect(endpoint) as fresh:
                            self.ready(w, h, fresh, identity, (18, 12))
                            fresh.sendall(movement_wire(17, 13, 1))
                            self.ack(h, fresh, 1)
                        self.assertEqual(self.positions(server.database),
                                         [(identity, 2, 15, 17, 13, saved[0][5] + 1)])
                        h.unchanged(server.database, before)

    def test_ownership_change_during_play_cannot_write_position(self):
        w, h = self.harness()
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            with h.connect(server.endpoint) as login:
                h.login(login, name=dual.OTHER)
                h.list_characters(login)
            before = h.snapshot(server.database)
            owner_id = before[1][0][1]
            other_id = next(row[0] for row in before[0] if row[0] != owner_id)
            with h.connect(endpoint) as game:
                self.ready(w, h, game, identity)
                game.sendall(movement_wire(18, 12, 1))
                self.ack(h, game, 1)
                saved = self.positions(server.database)
                self.execute(server.database, 'UPDATE recovered_characters SET account_id=? WHERE id=?',
                             (other_id, identity))
                transferred = h.snapshot(server.database)
                game.sendall(movement_wire(17, 13, 2))
                h.closed(game)
            self.assertEqual(self.positions(server.database), saved)
            h.unchanged(server.database, transferred)
            with h.connect(endpoint) as old_owner:
                h.game_ready(old_owner)
                old_owner.sendall(h.frame(0x1a, dual.selection_payload(0)))
                h.closed(old_owner)
            with h.connect(endpoint) as new_owner:
                self.ready(w, h, new_owner, identity, (18, 12), account=dual.OTHER)
                new_owner.sendall(movement_wire(17, 13, 1))
                self.ack(h, new_owner, 1)
            self.assertEqual(self.positions(server.database), [(identity, 2, 15, 17, 13, 2)])
            h.unchanged(server.database, transferred)

    def test_batch_transaction_failure_rolls_back_side_effects_and_reconnects(self):
        effects = {
            'after_write_fail': "SELECT RAISE(FAIL,'position fault');",
            'transaction_rollback': "SELECT RAISE(ROLLBACK,'position fault');",
            'readback_mismatch': 'UPDATE recovered_positions SET x=17,y=13 WHERE character_id=NEW.character_id;',
            'deferred_commit_failure': 'INSERT INTO position_commit_probe VALUES(999999);',
        }
        wire = movement_wire(0, 0, 0, records=[(18, 12, 1), (17, 13, 2), (18, 12, 3)])
        for operation in ('INSERT', 'UPDATE'):
            for failure, effect in effects.items():
                with self.subTest(operation=operation, failure=failure):
                    w, h = self.harness()
                    with h.server() as server:
                        endpoint, identity = w.create(h, server)
                        before = h.snapshot(server.database)
                        if operation == 'UPDATE':
                            with h.connect(endpoint) as initial:
                                self.ready(w, h, initial, identity)
                                initial.sendall(movement_wire(17, 13, 1))
                                self.ack(h, initial, 1)
                        saved = self.positions(server.database)
                        self.execute(server.database, 'CREATE TABLE position_commit_probe(account_id INTEGER REFERENCES accounts(id) DEFERRABLE INITIALLY DEFERRED)')
                        self.execute(server.database,
                                     f'CREATE TRIGGER position_failure AFTER {operation} ON recovered_positions BEGIN '
                                     "UPDATE accounts SET password_hash='rollback probe'; " + effect + ' END')
                        with h.connect(endpoint) as game:
                            self.ready(w, h, game, identity)
                            game.sendall(wire)
                            h.closed(game)
                        self.assertEqual(self.positions(server.database), saved)
                        h.unchanged(server.database, before)
                        with closing(sqlite3.connect(server.database)) as db:
                            self.assertEqual(db.execute('SELECT count(*) FROM position_commit_probe').fetchone()[0], 0)
                        self.execute(server.database, 'DROP TRIGGER position_failure')
                        # An ACK for every record is visible only after the entire batch commits.
                        with h.connect(endpoint) as fresh:
                            self.ready(w, h, fresh, identity)
                            fresh.sendall(wire)
                            for slot in (1, 2, 3):
                                self.ack(h, fresh, slot)
                        revision = saved[0][5] + 1 if saved else 1
                        self.assertEqual(self.positions(server.database), [(identity, 2, 15, 18, 12, revision)])
                        with h.connect(endpoint) as restored:
                            self.ready(w, h, restored, identity, (18, 12))
                        h.unchanged(server.database, before)


if __name__ == '__main__':
    unittest.main()
