"""Regression for the actual native helper callback and post-kick launch contract.
No clients or servers started; original-member expectation and waits preserved.
"""
import ast
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
NEW=ROOT/'tools/strike_lab/private_guild_kick_0080_v02_20261005.py'
OLD=ROOT/'tools/strike_lab/private_guild_kick_0080_v01_20261005.py'

class ReloginContract(unittest.TestCase):
    def setUp(self):
        self.tree=ast.parse(NEW.read_text('utf-8'))
        self.launch=next(n for n in ast.walk(self.tree) if isinstance(n,ast.FunctionDef) and n.name=='launch')
        self.branch=next(n for n in self.launch.body if isinstance(n,ast.If) and isinstance(n.test,ast.UnaryOp) and isinstance(n.test.operand,ast.Name) and n.test.operand.id=='expect_prompt')
        self.wait=next(n.value for n in self.branch.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='wait_until')
    def callback(self,actual,expected):
        env={'c':{'ui':1},'number':lambda *_:4096,'cstring':lambda *_:actual,'expected_guild':expected}
        return eval(compile(ast.Expression(self.wait.args[0]),'<actual-native-relogin-callback>','eval'),env)()
    def test_removed_member_requires_empty_native_name(self):
        self.assertTrue(self.callback(b'',b''))
        self.assertFalse(self.callback(b'guild80',b''))
    def test_existing_member_still_requires_guild(self):
        self.assertTrue(self.callback(b'guild80',b'guild80'))
        self.assertFalse(self.callback(b'',b'guild80'))
        self.assertEqual(ast.unparse(self.launch.args.defaults[-1]),'NAME.encode()')
    def test_postkick_launch_explicitly_expects_empty(self):
        calls=[n for n in ast.walk(self.tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='launch' and n.keywords]
        self.assertEqual(len(calls),1)
        self.assertEqual([a.value for a in calls[0].args],[5,False])
        self.assertEqual([(k.arg,k.value.value) for k in calls[0].keywords],[('expected_guild',b'')])
    def test_wait_and_default_member_calls_not_weakened(self):
        self.assertEqual(self.wait.args[1].value,5)
        self.assertEqual(self.wait.args[2].value,'RELOGIN_NATIVE_GUILD_NAME_MISMATCH')
        old=ast.parse(OLD.read_text('utf-8'))
        prev=[ast.unparse(n) for n in ast.walk(old) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='launch']
        now=[ast.unparse(n) for n in ast.walk(self.tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='launch']
        self.assertEqual(len(prev),len(now))
        for a,b in zip(prev,now):
            self.assertTrue(a==b or (a=='launch(5, False)' and b=="launch(5, False, expected_guild=b'')"),(a,b))

if __name__=='__main__':unittest.main()
