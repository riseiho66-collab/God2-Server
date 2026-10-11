"""Loopback wire regression, not original-client acceptance."""
import socket
import sys
import unittest

import test_post_server_select_server as post_select

sys.path.insert(0, str(post_select.ROOT / 'tools/strike_lab'))
from c2s0002 import key


class CharacterListCandidateServerTests(unittest.TestCase):
    server = post_select.PostSelectServerTests.server
    prefix = post_select.PostSelectServerTests.prefix
    closed = post_select.PostSelectServerTests.closed

    def candidate_server(self):
        return self.server('god2_legacy_character_list_candidate', allow_unverified_legacy=True)

    def receive_candidate(self, client):
        wire = bytearray()
        while len(wire) < 78:
            chunk = client.recv(78 - len(wire))
            self.assertTrue(chunk, 'Premature EOF in candidate frame')
            wire.extend(chunk)
        self.assertEqual(wire[:2], b'\x4e\x00')
        k = key(post_select.ROOT)
        self.assertEqual((-sum(k)) & 255, 0)
        plain = bytearray(wire[:2])
        previous = 0
        for index, value in enumerate(wire[2:]):
            previous = ((value + 3 - previous) & 255) ^ k[index]
            plain.append(previous)
        # Historical empty layout; current static handler reads count/flags
        # as separate bytes, followed by two 36-byte records.
        expected = bytearray(78)
        expected[:3] = b'\x4e\x00\x07'
        expected[21:41] = bytes.fromhex('0102030020001114016001200120812004000300')
        expected[-1] = sum(value + 0x3c for value in expected[:-1]) & 255
        self.assertEqual(plain, expected)
        return bytes(plain)

    def test_prefix_then_selection_produces_one_candidate(self):
        with self.candidate_server() as (client, root):
            self.prefix(client)
            client.settimeout(.1)
            with self.assertRaises(socket.timeout):
                client.recv(1)
            client.settimeout(1)
            client.sendall(post_select.REQUEST.read_bytes())
            self.receive_candidate(client)
            client.settimeout(.1)
            with self.assertRaises(socket.timeout):
                client.recv(1)
            log = (root / 'stdout.log').read_text()
            self.assertIn('LEGACY_CHARACTER_LIST_CANDIDATE_SENT', log)
            self.assertIn('current client acceptance UNKNOWN', log)
            self.assertNotIn('CODEX_VERIFIED', log)

    def test_fragmented_selection_waits_for_complete_frame(self):
        with self.candidate_server() as (client, root):
            self.prefix(client)
            request = post_select.REQUEST.read_bytes()
            client.sendall(request[:-1])
            client.settimeout(.1)
            with self.assertRaises(socket.timeout):
                client.recv(1)
            client.settimeout(1)
            client.sendall(request[-1:])
            self.receive_candidate(client)

    def test_invalid_selection_does_not_send_candidate(self):
        with self.candidate_server() as (client, root):
            self.prefix(client)
            request = bytearray(post_select.REQUEST.read_bytes())
            request[-1] ^= 1
            client.sendall(request)
            self.closed(client)
            self.assertNotIn('LEGACY_CHARACTER_LIST_CANDIDATE_SENT', (root / 'stdout.log').read_text())

    def test_unknown_next_request_not_silently_promoted_to_gameplay(self):
        with self.candidate_server() as (client, root):
            self.prefix(client)
            client.sendall(post_select.REQUEST.read_bytes())
            self.receive_candidate(client)
            client.sendall(post_select.REQUEST.read_bytes())
            self.closed(client)
            self.assertIn('Post-selection next C2S contract unknown', (root / 'stdout.log').read_text())


if __name__ == '__main__':
    unittest.main()
