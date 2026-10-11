"""Own-server account persistence over recovered wire; not live-client E2E."""
from pathlib import Path
from contextlib import closing
import socket
import sqlite3
import json
import tempfile
import unittest

import test_post_server_select_server as prefix
import test_character_list_candidate_server as candidate
from c2s0002 import key


def encode(payload):
    clear=bytes(payload)+bytes([(176+2*0x3c+sum(b+0x3c for b in payload))&255])
    wire=bytearray(b'\xb0\x00');previous=0
    for k,b in zip(key(prefix.ROOT),clear):
        wire.append(((k^b)+previous-3)&255);previous=b
    return bytes(wire)


def credential(name=b'PersistAccount',password=b'SyntheticSecret131'):
    if len(name)>23 or len(password)>131:
        raise ValueError('Test credential bounds')
    payload=bytearray(173);payload[0]=4;payload[167]=0xc8
    payload[1:1+len(name)]=name
    payload[25:25+len(password)]=password
    return payload


class RecoveredAccountServerTests(unittest.TestCase):
    server=prefix.PostSelectServerTests.server
    closed=prefix.PostSelectServerTests.closed
    receive_candidate=candidate.CharacterListCandidateServerTests.receive_candidate

    def auth_server(self,registration=True,database_path=None):
        return self.server('god2_legacy_character_list_candidate',allow_unverified_legacy=True,
            recovered_account_auth=True,local_account_registration=registration,run_for=10,database_path=database_path)

    def receive(self,client,length):
        data=b''
        while len(data)<length:
            chunk=client.recv(length-len(data))
            self.assertTrue(chunk,'Unexpected EOF before response')
            data+=chunk
        return data

    def handshake(self,client):
        client.settimeout(5)
        self.assertEqual(self.receive(client,19),(prefix.PREFIX/'S2C_0001.bin').read_bytes())
        client.sendall((prefix.PREFIX/'C2S_0001.bin').read_bytes())
        self.assertEqual(self.receive(client,5),(prefix.PREFIX/'S2C_0002.bin').read_bytes())

    def accept(self,client,payload):
        expected=bytearray(payload);expected[0]=29
        self.assertEqual(self.receive(client,176),encode(expected))
        for name in ('S2C_SERVER_LIST_0001.bin','S2C_0004.bin'):
            wire=(prefix.PREFIX/name).read_bytes()
            self.assertEqual(self.receive(client,len(wire)),wire)
        client.sendall(prefix.REQUEST.read_bytes())
        self.receive_candidate(client)

    def rows(self,path):
        with closing(sqlite3.connect(path)) as db:
            return db.execute('SELECT id,username,password_hash FROM accounts ORDER BY id').fetchall()

    def test_persistence_restart_and_wrong_password(self):
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'persist.db'
            payload=credential()
            with self.auth_server(database_path=database) as (client,root):
                self.handshake(client);client.sendall(encode(payload));self.accept(client,payload)
                saved=self.rows(database)
                self.assertEqual(len(saved),1)
                self.assertEqual(saved[0][1],'god2-bytes:'+b'PersistAccount'.hex())
                self.assertNotIn('SyntheticSecret131',saved[0][2])
                log=(root/'stdout.log').read_text()
                self.assertIn('RECOVERED_ACCOUNT_BOUND account_id='+str(saved[0][0]),log)
                self.assertNotIn('PersistAccount',log)
                self.assertNotIn('SyntheticSecret131',log)
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM characters').fetchone()[0],0)
            # A fresh process with registration disabled must reuse the committed account.
            with self.auth_server(registration=False,database_path=database) as (client,root):
                self.handshake(client);client.sendall(encode(payload));self.accept(client,payload)
                self.assertEqual(self.rows(database),saved)
            with self.auth_server(database_path=database) as (client,root):
                self.handshake(client);client.sendall(encode(credential(password=b'WrongSecret')))
                self.closed(client)
                self.assertEqual(self.rows(database),saved)
                log=(root/'stdout.log').read_text()
                self.assertNotIn('LOGIN_TERMINAL_SENT',log)
                self.assertNotIn('RECOVERED_ACCOUNT_BOUND',log)

    def test_wrong_password_then_valid_login_same_server(self):
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'retry.db'
            valid=credential(name=b'RetryAccount',password=b'RetrySecret131')
            with self.auth_server(database_path=database) as (client,root):
                port=json.loads((root/'config.json').read_text())['server']['port']
                self.handshake(client);client.sendall(encode(valid));self.accept(client,valid)
                client.close()
                with closing(socket.create_connection(('127.0.0.1',port),timeout=5)) as wrong:
                    self.handshake(wrong)
                    wrong.sendall(encode(credential(name=b'RetryAccount',password=b'WrongSecret')))
                    self.closed(wrong)
                with closing(socket.create_connection(('127.0.0.1',port),timeout=5)) as retry:
                    self.handshake(retry);retry.sendall(encode(valid));self.accept(retry,valid)
                self.assertEqual(len(self.rows(database)),1)

    def test_registration_off_rejects_unknown_account(self):
        with self.auth_server(registration=False) as (client,root):
            self.handshake(client);client.sendall(encode(credential()));self.closed(client)
            self.assertEqual(self.rows(root/'test.db'),[])
            self.assertNotIn('LOGIN_TERMINAL_SENT',(root/'stdout.log').read_text())

    def test_empty_or_corrupt_credentials_never_commit(self):
        for payload,corrupt in ((credential(name=b''),False),(credential(password=b''),False),
                                (credential(),True)):
            with self.subTest(corrupt=corrupt),self.auth_server() as (client,root):
                self.handshake(client)
                wire=bytearray(encode(payload))
                if corrupt:wire[-1]^=1
                client.sendall(wire);self.closed(client)
                self.assertEqual(self.rows(root/'test.db'),[])
                self.assertNotIn('LOGIN_TERMINAL_SENT',(root/'stdout.log').read_text())

    def test_fragmented_request_binds_only_after_checksum(self):
        with self.auth_server() as (client,root):
            self.handshake(client)
            payload=credential();wire=encode(payload)
            client.sendall(wire[:-1]);client.settimeout(.15)
            with self.assertRaises(socket.timeout):client.recv(1)
            self.assertEqual(self.rows(root/'test.db'),[])
            client.settimeout(5);client.sendall(wire[-1:]);self.accept(client,payload)
            self.assertEqual(len(self.rows(root/'test.db')),1)

    def test_database_commit_failure_cannot_send_success(self):
        with self.auth_server() as (client,root):
            with closing(sqlite3.connect(root/'test.db')) as db:
                db.execute("CREATE TRIGGER deny_accounts BEFORE INSERT ON accounts "
                           "BEGIN SELECT RAISE(ABORT, 'test database failure'); END")
                db.commit()
            self.handshake(client);client.sendall(encode(credential()));self.closed(client)
            self.assertEqual(self.rows(root/'test.db'),[])
            log=(root/'stdout.log').read_text()
            self.assertIn('Recovered account authentication rejected',log)
            self.assertNotIn('LOGIN_TERMINAL_SENT',log)
            self.assertNotIn('RECOVERED_ACCOUNT_BOUND',log)


if __name__=='__main__':unittest.main()
