"""Own-server immediate native6B selection after successful login; no UI claim."""
from contextlib import closing
import unittest
import test_owned_role_text_server as fixture

class NativeLoginWriteOrderTests(unittest.TestCase):
    server=fixture.OwnedRoleTextServerTests.server
    @classmethod
    def setUpClass(cls):fixture.OwnedRoleTextServerTests.setUpClass.__func__(cls)
    def test_immediate_post_login_character_selection_preserves_accounts_and_saves(self):
        with self.server() as state:
            with closing(fixture.sqlite3.connect(state.database)) as db:
                before={name:sorted(repr(row) for row in db.execute('select * from "'+name+'"'))
                        for name, in db.execute("select name from sqlite_master where type='table' order by name")}
            h=state.helper
            # No sleeps, silent() probes or server-log barriers between the
            # terminal bytes arriving and sending native6B. Exercise both owners.
            for attempt in range(32):
                account=b'codexslow' if attempt%2==0 else b'codexfixed'
                with h.connect(state.endpoint) as login:
                    h.handshake(login)
                    login.sendall(h.frame(*fixture.dual.credential(4,account,b'labtest2345')))
                    h.read_frame(login,0x1d,176);h.read_frame(login,4,8)
                    h.read_frame(login,5,12);h.read_frame(login,6,8);h.read_frame(login,0x0a,20)
                    login.sendall(fixture.dual.SELECT.read_bytes())
                    try:listing=h.read_frame(login,7,78)
                    except AssertionError as error:self.fail(str(error)+'\n'+state.log()[-6000:])
                    self.assertEqual(listing[3],1,'Immediate character selection was rejected')
            with closing(fixture.sqlite3.connect(state.database)) as db:
                after={name:sorted(repr(row) for row in db.execute('select * from "'+name+'"'))
                       for name, in db.execute("select name from sqlite_master where type='table' order by name")}
            self.assertEqual(after,before,'Login timing changed accounts or saved state')
            print('Immediate native6B selections:32/32; owners:2; saved rows unchanged',flush=True)

if __name__=='__main__':unittest.main()
