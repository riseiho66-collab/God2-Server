"""Own-server durable profiles and pinned parser slice, not live-client acceptance."""
from contextlib import closing
import hashlib
import os
from pathlib import Path
import socket
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

import test_post_server_select_server as prefix
import test_recovered_account_server as accounts
import test_character_create_server as create
import test_current_character_list_handler as handler
from test_current_post_create_builder import builder
from c2s0002 import key


def profile(name=b'CreatedHero',category=2):
    if not 1<=len(name)<=14 or b'\0' in name:raise ValueError('Test name bounds')
    p=bytearray(44);p[:len(name)]=name
    p[29]=category;p[31]=1;p[32]=3;p[33]=(category-1)%2;p[36]=0x41
    packed=p[33]+(9<<4)+(8<<10)
    p[38:40]=packed.to_bytes(2,'little');p[40]=4;p[41:44]=b'\xaa\xbb\xcc'
    return p


def frame(opcode,payload):
    plain=bytearray((len(payload)+4).to_bytes(2,'little')+bytes([opcode])+payload)
    plain.append(sum(b+0x3c for b in plain)&255)
    wire=bytearray(plain[:2]);previous=0
    for k,b in zip(key(prefix.ROOT),plain[2:]):
        wire.append(((k^b)+previous-3)&255);previous=b
    return bytes(wire)


def post_create(token=0):
    return frame(0x18,builder(0x18,1))+frame(0x1a,builder(0x1a,token))


class RecoveredCharacterServerTests(unittest.TestCase):
    server=prefix.PostSelectServerTests.server
    closed=prefix.PostSelectServerTests.closed
    handshake=accounts.RecoveredAccountServerTests.handshake
    receive=accounts.RecoveredAccountServerTests.receive
    run_slice=handler.CurrentCharacterListHandlerTests.run_slice

    @classmethod
    def setUpClass(cls):
        cls.image=handler.IMAGE.read_bytes()
        if hashlib.sha256(cls.image).hexdigest()!=handler.IMAGE_SHA:
            raise AssertionError('Current client image changed')

    def character_server(self,database=None):
        return self.server('god2_legacy_character_list_candidate',allow_unverified_legacy=True,
            recovered_account_auth=True,local_account_registration=True,recovered_character_creation=True,
            run_for=10,database_path=database)

    def read_frame(self,client):
        header=self.receive(client,2);length=int.from_bytes(header,'little')
        self.assertTrue(4<=length<=176)
        wire=self.receive(client,length-2);plain=bytearray(header);previous=0
        for k,b in zip(key(prefix.ROOT),wire):
            previous=((b+3-previous)&255)^k;plain.append(previous)
        self.assertEqual(plain[-1],sum(b+0x3c for b in plain[:-1])&255)
        return bytes(plain)

    def login(self,client,name=b'CharacterOwner'):
        self.handshake(client);p=accounts.credential(name=name)
        client.sendall(accounts.encode(p));expected=bytearray(p);expected[0]=29
        self.assertEqual(self.receive(client,176),accounts.encode(expected))
        for name in ('S2C_SERVER_LIST_0001.bin','S2C_0004.bin'):
            wire=(prefix.PREFIX/name).read_bytes();self.assertEqual(self.receive(client,len(wire)),wire)
        client.sendall(prefix.REQUEST.read_bytes())
        result=self.read_frame(client)
        self.assertEqual(result[:3],b'\x4e\x00\x07')
        return result

    def result(self,client):
        plain=self.read_frame(client)
        self.assertEqual(plain,b'\x1a\x00\x02'+bytes(22)+b'\xf8')

    def rows(self,path):
        with closing(sqlite3.connect(path)) as db:
            return db.execute('SELECT id,account_id,slot,name_bytes,profile FROM recovered_characters ORDER BY id').fetchall()

    def test_commit_restart_owned_list_and_current_handler(self):
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'characters.db';p=profile()
            with self.character_server(database) as (client,root):
                self.assertEqual(self.login(client)[3],0)
                client.sendall(create.request_wire(p));self.result(client)
                saved=self.rows(database)
                self.assertEqual(len(saved),1);self.assertEqual(saved[0][2],0)
                self.assertEqual(saved[0][3],b'CreatedHero');self.assertEqual(saved[0][4],bytes(p[:40]))
                client.settimeout(.1)
                with self.assertRaises(socket.timeout):client.recv(1) # no unsolicited 07
                client.settimeout(5);client.sendall(post_create());self.result(client)
                log=(root/'stdout.log').read_text()
                self.assertIn('POST_CREATE_CHARACTER_BOUND',log)
                self.assertNotIn('CreatedHero',log)
                self.assertNotIn('CharacterOwner',log)
            with self.character_server(database) as (client,root):
                listing=self.login(client)
                self.assertEqual(listing[3],1)
                self.assertEqual(listing[5:17],b'CreatedHero\0')
                self.assertEqual(listing[22],2)
                self.assertEqual(listing[24],0)
                self.assertEqual(listing[25:30],b'\x41\x00\x90\x20\x01')
                # Current preview 9A10..9A65 builds the component block that
                # saved-character selection 8310..852E consumes at W[24..31].
                self.assertEqual(listing[29:37],b'\x01\x60\x01\x40\x01\x00\x81\x00')
                self.assertEqual(self.rows(database),saved)
                for converted in (False,True):self.run_slice(listing,converted)
            with self.character_server(database) as (client,root):
                self.assertEqual(self.login(client,b'OtherOwner')[3],0)
                self.assertEqual(self.rows(database),saved)

    def test_file_only_background_logger_keeps_character_list_live(self):
        with patch.dict(os.environ,{'GOD2_LOG_FILE_ONLY':'1'}):
            with self.character_server() as (client,root):
                self.assertEqual(self.login(client,b'FileOnlyOwner')[3],0)
                deadline=time.monotonic()+1
                while 'ACCOUNT_CHARACTER_LIST_QUEUED length=78' not in (root/'server.log').read_text():
                    self.assertLess(time.monotonic(),deadline,'file-only session log stalled')
                    time.sleep(.02)

    def test_duplicate_name_and_two_character_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'characters.db'
            for index,name in enumerate((b'FirstHero',b'SecondHero')):
                with self.character_server(database) as (client,root):
                    self.assertEqual(self.login(client)[3],index)
                    client.sendall(create.request_wire(profile(name)));self.result(client)
                    client.sendall(post_create(index));self.result(client)
            with self.character_server(database) as (client,root):
                listing=self.login(client);self.assertEqual(listing[3],2)
                self.run_slice(listing,False);self.run_slice(listing,True)
                client.sendall(create.request_wire(profile(b'ThirdHero')));self.closed(client)
                self.assertEqual(len(self.rows(database)),2)
            with self.character_server(database) as (client,root):
                self.login(client,b'OtherOwner')
                client.sendall(create.request_wire(profile(b'FirstHero')));self.closed(client)
                self.assertEqual(len(self.rows(database)),2)

    def test_commit_failure_and_profile_rejection_send_no_success(self):
        for failure in ('database','profile'):
            with self.subTest(failure=failure),self.character_server() as (client,root):
                self.login(client);p=profile()
                if failure=='database':
                    with closing(sqlite3.connect(root/'test.db')) as db:
                        db.execute("CREATE TRIGGER deny_profiles BEFORE INSERT ON recovered_characters "
                                   "BEGIN SELECT RAISE(ABORT, 'forced failure'); END")
                        db.commit()
                else:p[29]=9
                client.sendall(create.request_wire(p));self.closed(client)
                self.assertEqual(self.rows(root/'test.db'),[])
                self.assertNotIn('CHARACTER_PROFILE_COMMITTED',(root/'stdout.log').read_text())

    def test_fragmented_create_and_coalesced_or_fragmented_followup(self):
        for split in (False,True):
            with self.subTest(split=split),self.character_server() as (client,root):
                self.login(client);wire=create.request_wire(profile())
                client.sendall(wire[:47]);client.settimeout(.1)
                with self.assertRaises(socket.timeout):client.recv(1)
                self.assertEqual(self.rows(root/'test.db'),[])
                client.settimeout(5);client.sendall(wire[47:]);self.result(client)
                pair=post_create()
                if split:
                    for chunk in (pair[:1],pair[1:5],pair[5:45]):
                        client.sendall(chunk);client.settimeout(.1)
                        with self.assertRaises(socket.timeout):client.recv(1)
                    client.settimeout(5);client.sendall(pair[45:])
                else:client.sendall(pair)
                self.result(client)
                self.assertEqual(len(self.rows(root/'test.db')),1)

    def test_post_create_wrong_token_and_corrupt_frame_rejected(self):
        for failure in ('token','checksum','order'):
            with self.subTest(failure=failure),self.character_server() as (client,root):
                self.login(client);client.sendall(create.request_wire(profile()));self.result(client)
                pair=bytearray(post_create(1 if failure=='token' else 0))
                if failure=='checksum':pair[-1]^=1
                if failure=='order':pair=pair[5:]+pair[:5]
                client.sendall(pair);self.closed(client)
                self.assertEqual(len(self.rows(root/'test.db')),1)
                self.assertNotIn('POST_CREATE_CHARACTER_BOUND',(root/'stdout.log').read_text())

    def test_followup_cannot_skip_creation(self):
        with self.character_server() as (client,root):
            self.login(client);client.sendall(post_create());self.closed(client)
            self.assertEqual(self.rows(root/'test.db'),[])
            self.assertNotIn('POST_CREATE_CHARACTER_BOUND',(root/'stdout.log').read_text())


if __name__=='__main__':unittest.main()
