"""Current-client town/Island01 model point evidence; no live portal authority."""
import hashlib
import json
import struct
import unittest

import test_current_route_advertisement as routes
from tools.strike_lab.current_monster_binary_producer import parse_mdl
from tools.strike_lab.omega_assets import decode_csvz
from unicorn.x86_const import UC_X86_REG_EIP


ROOT = routes.ROOT
CLIENT = ROOT.parent / 'God2/Data2/map/island01'
TOWN_SHA = 'bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618'
ISLAND_SHA = 'cbdc0c946618a1bf4a9b2f221283a17fa58b1f49941b2ea336046851a2519d8d'


def references(path, digest, suffix):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise AssertionError('Pinned original model changed: ' + str(path))
    mdl = parse_mdl(decode_csvz(data), allow_parent_rom=True)
    return [(placement, mdl['models'][placement['fields'][0]]['extra_8_ints'])
            for placement in mdl['placements']
            if (placement['attached_reference'] or '').replace('\\', '/').lower().endswith(suffix)]


def consensus(artifact, x, y):
    values = {window['cells_hex'][2 * ((y-window['origin_y'])*63 + x-window['origin_x']):
                                  2 * ((y-window['origin_y'])*63 + x-window['origin_x'])+2]
              for window in artifact['windows']
              if window['origin_x'] <= x < window['origin_x']+63 and
                 window['origin_y'] <= y < window['origin_y']+63}
    return values


class IslandBoundaryTests(unittest.TestCase):
    vm = routes.CurrentRouteAdvertisementTests.vm
    call = routes.CurrentRouteAdvertisementTests.call
    run_to = routes.CurrentRouteAdvertisementTests.run_to

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Pinned original executable changed')

    def test_western_parent_boundary_original_projection_and_navigation(self):
        town = references(CLIENT/'CityI1/cityI1.mdlZ', TOWN_SHA, '/island01.mdt')
        island = references(CLIENT/'Island01.mdlZ', ISLAND_SHA, '/cityi1.mdt')
        self.assertEqual((len(town), len(island)), (23, 23))
        town_west = sorted(((p, points) for p, points in town if p['fields'][3] == 56),
                           key=lambda item: item[0]['fields'][4])
        island_west = sorted(((p, points) for p, points in island if p['fields'][3] == 477),
                             key=lambda item: item[0]['fields'][4])
        self.assertEqual(len(town_west), 6)
        self.assertEqual(len(island_west), 6)
        vm = self.vm()

        def project(placement, points, index):
            pair = points[2*index:2*index+2]
            self.assertGreaterEqual(pair[0], 0)
            output = routes.OUTPUT
            vm.mem_write(output, b'\xa5'*8)
            self.call(vm, 0x49bb0, pair[0], pair[1], output, output+4)
            self.assertEqual(vm.reg_read(UC_X86_REG_EIP), routes.RETURN)
            px, py = struct.unpack('<ii', vm.mem_read(output, 8))
            anchor = placement['fields'][3:5]
            return anchor[0]+px, anchor[1]+py

        town_exits = [project(p, points, 1) for p, points in town_west]
        town_arrivals = [project(p, points, 3) for p, points in town_west]
        island_exits = [project(p, points, 1) for p, points in island_west]
        island_arrivals = [project(p, points, 3) for p, points in island_west]
        self.assertEqual(sorted(town_exits), [(55, y) for y in range(75,81)])
        self.assertEqual(sorted(town_arrivals), [(56, y) for y in range(75,81)])
        self.assertEqual(sorted(island_exits), [(477, y) for y in range(209,215)])
        self.assertEqual(sorted(island_arrivals), [(476, y) for y in range(209,215)])
        town_grid = json.loads((ROOT/'artifacts/world-atlas/town-2-4.json').read_text())
        island_grid = json.loads((ROOT/'artifacts/world-atlas/island01-entry-2-0.json').read_text())
        for point in town_exits:
            self.assertEqual(consensus(town_grid, *point), {'02'}, point)
        for point in town_arrivals:
            self.assertEqual(consensus(town_grid, *point), {'01'}, point)
        for point in island_exits:
            self.assertEqual(consensus(island_grid, *point), {'02'}, point)
        for point in island_arrivals:
            self.assertEqual(consensus(island_grid, *point), {'01'}, point)


if __name__ == '__main__':
    unittest.main()
