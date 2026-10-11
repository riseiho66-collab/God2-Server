"""Full sixteen/100 restoration over real TCP and a restarted isolated server."""
import unittest
import hashlib
import json
import subprocess
import test_owned_companions_server as owned

class NativeDeitySkillCapacityServerTests(unittest.TestCase):
    def test_cpp_guard_matches_all_native_resource_observations(self):
        receipt=owned.ROOT/'artifacts/playtests/private-deity-skills-20260927-06/ui-result.json'
        raw=receipt.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'bb815dbf4daeb4e7d2b597d6c9d2d28cfbb1fce8b5dc7f38da8b6e0d1e03e7a6')
        audit=json.loads(raw)['skill_icon_audit']['rows']
        candidate=owned.ROOT/'build-town-visibility/tests/Release/recovered_deity.exe'
        result=subprocess.check_output([str(candidate),'--icon-audit'],text=True,timeout=10)
        actual=[tuple(map(int,line.split())) for line in result.splitlines()]
        self.assertEqual(actual,[(r['kind'],r['id'],int(r['display_eligible'])) for r in audit])
        self.assertEqual(sum(r[2] for r in actual),409)
    def test_capacity_restore_selection_and_restart(self):
        owned.OwnedCompanionsServerTests.setUpClass()
        peer=owned.OwnedCompanionsServerTests()
        peer.run_case(native_only=True,deity_templates=True,deity_skill_catalog=True)

if __name__=='__main__':unittest.main()
