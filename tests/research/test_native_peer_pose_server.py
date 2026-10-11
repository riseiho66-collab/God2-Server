"""Isolated Application TCP pose replication; synthetic clients, real SQLite."""
import os
from pathlib import Path
import tempfile
import struct
import unittest
import test_player_visibility_server as visibility
import test_town_player_visibility_server as town
from test_current_movement import movement_wire

dual=visibility.dual
dual.BINARY=Path(os.environ.get('GOD2_PEER_POSE_TEST_BINARY',
    dual.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'))

class NativePeerPoseServerTests(unittest.TestCase):
    harness=visibility.PlayerVisibilityServerTests.harness
    ready=visibility.PlayerVisibilityServerTests.ready
    select=visibility.PlayerVisibilityServerTests.select
    create_character=visibility.PlayerVisibilityServerTests.create_character
    ack=visibility.PlayerVisibilityServerTests.ack

    @classmethod
    def setUpClass(cls):visibility.PlayerVisibilityServerTests.setUpClass()

    def test_battle_world_refresh_replays_stationary_observer_pose(self):
        w,h=self.harness()
        original=h.configuration
        def configuration(*args,**kwargs):
            result=original(*args,**kwargs)
            for flag in ('diagnostic_player_visibility','diagnostic_visibility_battle',
                         'diagnostic_battle_transition','diagnostic_battle_participants',
                         'diagnostic_battle_player_appearance','diagnostic_battle_animations',
                         'diagnostic_battle_terminal'):
                result['development'][flag]=True
            result['development']['diagnostic_remote_actor_language']=0
            return result
        h.configuration=configuration
        def logical(peer):return town.TownPlayerVisibilityServerTests.logical(h,peer)
        def command(action,enemy):return h.frame(0x35,struct.pack('<4BHHII',0,action,0,0,0,enemy,0,0))
        with tempfile.TemporaryDirectory(prefix='god2-pose-return-') as directory:
            with h.server(database=Path(directory)/'player-visibility-diagnostic.db') as server:
                endpoint,identity=w.create(h,server)
                other_id=self.create_character(h,server,dual.OTHER,b'PoseWatcher')
                with h.connect(endpoint) as owner,h.connect(endpoint) as observer:
                    self.ready(w,h,owner,identity)
                    owner.sendall(h.frame(0x30,b'\0'));h.silent(owner)
                    self.ready(w,h,observer,other_id,account=dual.OTHER)
                    observer.sendall(h.frame(0x30,b'\0'))
                    h.read_frame(owner,0x6f,84);h.read_frame(observer,0x6f,84)
                    observer.sendall(h.frame(0x66,b'\0\x17\0'))
                    expected=bytes((0x77,other_id&255,other_id>>8,0,0x17,0,0))
                    self.assertEqual(logical(owner),expected);self.assertEqual(logical(observer),expected)
                    observer.sendall(h.frame(0x30,b'\0'));h.silent(observer)
                    owner.sendall(h.frame(0x30,b'\0'));h.read_frame(owner,0x82,12)
                    owner.sendall(h.frame(0x36,b'\0'*8));self.assertTrue(logical(owner))
                    h.read_frame(observer,0x5e,16)
                    owner.sendall(command(0x0b,0));h.silent(owner)
                    owner.sendall(command(1,1));self.assertTrue(logical(owner))
                    owner.sendall(command(0x0b,1));self.assertEqual(logical(owner)[0],0x89)
                    h.read_frame(observer,0x5e,16)
                    owner.sendall(h.frame(0x30,b'\0'))
                    h.read_frame(owner,0x6f,84);self.assertEqual(logical(owner),expected)
                    h.silent(owner);h.silent(observer)

    def test_two_way_pose_late_join_movement_disconnect_and_unknown_payload(self):
        w,h=self.harness()
        original=h.configuration
        def configuration(*args,**kwargs):
            result=original(*args,**kwargs)
            result['development']['diagnostic_player_visibility']=True
            result['development']['diagnostic_remote_actor_language']=0
            return result
        h.configuration=configuration
        def pose(peer,identity,packed):
            self.assertEqual(h.read_frame(peer,0x77,10)[2:-1],
                bytes((0x77,identity&255,identity>>8,0,packed,0,0)))
        with tempfile.TemporaryDirectory(prefix='god2-native-peer-pose-') as directory:
            with h.server(database=Path(directory)/'player-visibility-diagnostic.db') as server:
                endpoint,first_id=w.create(h,server)
                other_id=self.create_character(h,server,dual.OTHER,b'PoseObserver')
                before=h.snapshot(server.database)
                with h.connect(endpoint) as first,h.connect(endpoint) as other:
                    self.ready(w,h,first,first_id)
                    first.sendall(h.frame(0x66,b'\0\x0f\xfe'));pose(first,first_id,15)
                    first.sendall(h.frame(0x30,b'\0'));h.silent(first)
                    self.ready(w,h,other,other_id,account=dual.OTHER)
                    other.sendall(h.frame(0x30,b'\0'))
                    h.read_frame(first,0x6f,84);h.read_frame(other,0x6f,84)
                    pose(other,first_id,15)
                    for source,identity,observer in ((first,first_id,other),(other,other_id,first)):
                        for mode in (1,2,3):
                            for direction in range(8):
                                packed=mode*8+direction
                                source.sendall(h.frame(0x66,bytes((0,packed,0xa5))))
                                pose(source,identity,packed);pose(observer,identity,packed)
                    first.sendall(h.frame(0x66,b'\0\xf7\xa5'))
                    h.silent(first);h.silent(other)
                    # A same-position/out-and-back movement batch invalidates
                    # stationary pose even though its final position is equal.
                    first.sendall(movement_wire(0,0,0,records=[(18,12,1),(17,13,2)]))
                    self.ack(h,first,1);self.ack(h,first,2)
                    h.read_frame(other,0x5e,16);h.read_frame(other,0x5e,16)
                    first.close();h.read_frame(other,0x73,8)
                    with h.connect(endpoint) as returned:
                        self.ready(w,h,returned,first_id)
                        returned.sendall(h.frame(0x30,b'\0'))
                        h.read_frame(other,0x6f,84);h.read_frame(returned,0x6f,84)
                        # Mode3 completes locally and remotely;77 has no time
                        # offset. Joining must not replay/restart that one-shot.
                        h.silent(other);h.silent(returned)
                    h.read_frame(other,0x73,8)
                    other.sendall(h.frame(0x66,b'\0\x17\0'));pose(other,other_id,23)
                    with h.connect(endpoint) as returned:
                        self.ready(w,h,returned,first_id)
                        returned.sendall(h.frame(0x30,b'\0'))
                        h.read_frame(other,0x6f,84);h.read_frame(returned,0x6f,84)
                        pose(returned,other_id,23)
                        h.silent(other);h.silent(returned)
                    h.read_frame(other,0x73,8)
                h.unchanged(server.database,before)

if __name__=='__main__':unittest.main()
