"""Synthetic golden replay over C++ loopback; not original-client acceptance."""

import socket
import time
import unittest

if __package__:
    from . import test_post_server_select_server as post_select
else:
    import test_post_server_select_server as post_select


class RecoveredPrefixFragmentationTests(unittest.TestCase):
    # Reuse the hidden, bounded process and temporary-artifact lifecycle.
    server = post_select.PostSelectServerTests.server
    prefix = post_select.PostSelectServerTests.prefix
    closed = post_select.PostSelectServerTests.closed

    def receive_golden(self, client, name):
        expected = (post_select.PREFIX / name).read_bytes()
        data = bytearray()
        previous_timeout = client.gettimeout()
        deadline = time.monotonic() + 1
        try:
            while len(data) < len(expected):
                remaining = deadline - time.monotonic()
                self.assertGreater(remaining, 0, name + ': reply deadline exceeded')
                client.settimeout(remaining)
                chunk = client.recv(len(expected) - len(data))
                self.assertTrue(chunk, name + ': premature EOF')
                data.extend(chunk)
        finally:
            client.settimeout(previous_timeout)
        # Compare every wire byte without including credential-bearing payloads
        # in assertion diagnostics.
        self.assertTrue(data == expected, name + ': golden reply mismatch')

    def assert_silent(self, client):
        previous_timeout = client.gettimeout()
        try:
            client.settimeout(.1)
            with self.assertRaises(socket.timeout, msg='Expected an open, silent socket'):
                client.recv(1)
        finally:
            client.settimeout(previous_timeout)

    def send_fragmented(self, client, wire, split):
        self.assertGreater(split, 0)
        self.assertLess(split, len(wire))
        client.sendall(wire[:split])
        # Leave time for a separate server read and reject early replies/EOF.
        self.assert_silent(client)
        client.sendall(wire[split:])

    def seed_exchange(self, client, split=None):
        self.receive_golden(client, 'S2C_0001.bin')
        wire = (post_select.PREFIX / 'C2S_0001.bin').read_bytes()
        self.assertEqual(len(wire), 19)
        if split is None:
            client.sendall(wire)
        else:
            self.send_fragmented(client, wire, split)
        self.receive_golden(client, 'S2C_0002.bin')

    def login_exchange(self, client, split=None):
        wire = (post_select.PREFIX / 'C2S_0002.bin').read_bytes()
        self.assertEqual(len(wire), 176)
        if split is None:
            client.sendall(wire)
        else:
            self.send_fragmented(client, wire, split)
        for name in ('S2C_0003.bin', 'S2C_SERVER_LIST_0001.bin', 'S2C_0004.bin'):
            self.receive_golden(client, name)
        self.assert_silent(client)

    def assert_log_marker(self, root, marker, present=True):
        found = marker in (root / 'stdout.log').read_text()
        self.assertEqual(found, present, 'Unexpected presence of log marker: ' + marker)

    def test_seed_fragmented_within_and_after_length_header(self):
        for split in (1, 2):
            with self.subTest(split=split), self.server() as (client, root):
                self.seed_exchange(client, split)
                self.login_exchange(client)
                self.assert_log_marker(root, 'GOD2_SEED_EXCHANGE_ACCEPTED')
                self.assert_log_marker(root, 'C2S0002_ACCEPTED')

    def test_login_fragmented_at_representative_boundaries(self):
        for split in (1, 2, 175):
            with self.subTest(split=split), self.server() as (client, root):
                self.seed_exchange(client)
                self.login_exchange(client, split)
                self.assert_log_marker(root, 'C2S0002_ACCEPTED')

    def test_selection_fragmented_at_every_boundary_has_no_reply(self):
        wire = post_select.REQUEST.read_bytes()
        self.assertEqual(len(wire), 6)
        for split in range(1, 6):
            with self.subTest(split=split), self.server() as (client, root):
                self.prefix(client)
                self.send_fragmented(client, wire, split)
                self.assert_silent(client)
                self.assert_log_marker(root, 'POST_SERVER_SELECT_C2S_ACCEPTED length=6')

    def test_corrupt_fragmented_frames_close_without_reply(self):
        cases = (
            ('seed', post_select.PREFIX / 'C2S_0001.bin',
             'GOD2_SEED_EXCHANGE_ACCEPTED', 'Recovered seed proof rejected'),
            ('login', post_select.PREFIX / 'C2S_0002.bin',
             'C2S0002_ACCEPTED', 'C2S0002 contract rejected'),
            ('selection', post_select.REQUEST,
             'POST_SERVER_SELECT_C2S_ACCEPTED', 'Post-selection contract rejected'),
        )
        for stage, path, accepted, rejected in cases:
            with self.subTest(stage=stage), self.server() as (client, root):
                if stage == 'seed':
                    self.receive_golden(client, 'S2C_0001.bin')
                elif stage == 'login':
                    self.seed_exchange(client)
                else:
                    self.prefix(client)
                wire = bytearray(path.read_bytes())
                wire[-1] ^= 1
                self.send_fragmented(client, wire, len(wire) - 1)
                self.closed(client)
                self.assert_log_marker(root, accepted, present=False)
                self.assert_log_marker(root, rejected)


if __name__ == '__main__':
    unittest.main()
