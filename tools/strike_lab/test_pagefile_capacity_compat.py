import copy
import unittest
from tools.strike_lab.pagefile_capacity_compat import contract


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(automatic=True,raw=[r'?:\pagefile.sys'],existing=[r'\??\D:\pagefile.sys'],
                          settings=[],usage=[dict(Name=r'D:\pagefile.sys',AllocatedBaseSize=4096)])

    def test_live_value_not_hardcoded(self):
        self.assertEqual(contract(self.state),(r'D:\pagefile.sys',4096,r'D:\pagefile.sys 4096'))

    def test_reject_ineligible_states(self):
        for key,value in [('automatic',False),('settings',[{}]),('raw',[r'C:\pagefile.sys 4096 8192']),
                          ('existing',[]),('usage',[]),('existing',[r'C:\pagefile.sys'])]:
            state=copy.deepcopy(self.state)
            state[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                contract(state)

    def test_reject_bad_capacity(self):
        for value in [None,True,699,0x80000000]:
            self.state['usage'][0]['AllocatedBaseSize']=value
            with self.subTest(value=value),self.assertRaises(ValueError):
                contract(self.state)


if __name__=='__main__':
    unittest.main()
