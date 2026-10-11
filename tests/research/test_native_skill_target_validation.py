"""Independent recovered-server boundary checks; only temporary DBs are writable."""
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from tools.strike_lab import import_native_skills as catalog
from tools.strike_lab import current_skill_target_setup as targeting


PRELUDE = r"""
assert(GOD2_FIXTURE_MODE == false)
local function state()
    local s = {masks={0x80000000,0xffffffff},
               saved_masks={0xffffffff,0x80000000},entity_words={}}
    for i=1,28 do s.entity_words[i]=false end
    return s
end
local function rejected(s, label)
    local ok, err=pcall(native_skill_target_setup,3,8,0,s)
    assert(not ok and type(err)=='string' and
           err:find('native_skill_target_setup',1,true), label)
end
"""


class NativeSkillTargetValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='god2-target-validation-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.database = self.root / 'validation.sqlite'
        self.executable = catalog.ROOT / 'build/Release/god2-server.exe'
        self.assertTrue(self.executable.is_file(), 'Build Release god2-server first')
        self.config = json.loads(
            (catalog.ROOT / 'config/recovered-world-entry.json').read_text())
        self.config['database']['path'] = str(self.database)
        self.config['server'].update(host='127.0.0.1', port=0,
                                     character_port=0, worker_threads=1)
        self.config['logging']['file'] = str(self.root / 'server.log')
        self.config['protocol']['packet_dump'] = False
        scripts = self.root / 'scripts'
        scripts.mkdir()
        self.bootstrap = scripts / 'bootstrap.lua'
        self.config['lua'].update(bootstrap=str(self.bootstrap),
                                  script_root=str(scripts), hot_reload=False)
        self.config_path = self.root / 'server.json'
        self.config_path.write_text(json.dumps(self.config), encoding='utf-8')
        self.run_server('--migrate-only')
        self.db = sqlite3.connect(self.database)
        self.addCleanup(self.db.close)
        catalog.import_catalog(self.db, catalog.ROOT.parent / 'God2')
        self.records = catalog.pinned_records(catalog.ROOT.parent / 'God2')
        self.original = list(self.db.iterdump())

    def run_server(self, *arguments):
        result = subprocess.run(
            [str(self.executable), '--config', str(self.config_path), *arguments],
            cwd=catalog.ROOT, capture_output=True, text=True, timeout=30)
        log = self.root / 'server.log'
        output = result.stdout + result.stderr
        if log.exists():
            output += log.read_text(encoding='utf-8')
        self.assertEqual(result.returncode, 0, output)
        return output

    def check_bootstrap(self, script):
        self.bootstrap.write_text(
            PRELUDE + script + '\nlog("TARGET_VALIDATION_FINISHED")\n', encoding='ascii')
        output = self.run_server('--run-for', '1')
        self.assertIn('TARGET_VALIDATION_FINISHED', output)
        self.assertEqual(list(self.db.iterdump()), self.original)
        self.assertEqual(self.db.execute('PRAGMA quick_check').fetchall(), [('ok',)])
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_raw_tables_ignore_hostile_metatables(self):
        self.check_bootstrap(r"""
local calls=0
local function trap() calls=calls+1; error('metamethod executed') end
local mt={__index=trap,__newindex=trap,__pairs=trap,__len=trap,
          __tostring=trap,__eq=trap,__metatable='locked'}
local s=state()
setmetatable(s,mt)
for _,field in ipairs({'masks','saved_masks','entity_words'}) do
    setmetatable(s[field],mt)
end
local r=native_skill_target_setup(3,8,0,s)
assert(r and r.saved_masks[1]==0xffffffff and calls==0)

-- Metatables cannot synthesize missing raw fields or array entries.
local fake=setmetatable({}, {__index=state(),__pairs=function()
    calls=calls+1; return next,state(),nil
end,__len=function() calls=calls+1; return 3 end})
rejected(fake,'proxy state accepted')
for _,field in ipairs({'masks','saved_masks','entity_words'}) do
    local a=state(); local original=a[field]
    a[field]=setmetatable({}, {__index=original,__pairs=function()
        calls=calls+1; return next,original,nil
    end,__len=function() calls=calls+1; return #original end})
    rejected(a,'proxy array accepted: '..field)
    a=state(); a[field][1]=nil
    setmetatable(a[field],{__index=function() calls=calls+1; return 0 end})
    rejected(a,'sparse array accepted: '..field)
    for _,key in ipairs({false,{},'1',1.5,math.huge,-1}) do
        a=state(); a[field][key]=0
        rejected(a,'nonarray key accepted: '..field)
    end
end
local a=state(); a['masks'..string.char(0)..'suffix']=a.masks
rejected(a,'NUL-suffixed state field accepted')
a=state(); a.masks=a
rejected(a,'cyclic state accepted')
a=state(); a.entity_words[1]=a.entity_words
rejected(a,'cyclic entity accepted')
assert(calls==0,'raw validation invoked a metamethod')
""")

    def test_numeric_types_and_signed_boundaries(self):
        self.check_bootstrap(r"""
local bad={true,'0',{},function() end,0/0,math.huge,-math.huge,
           0.5,math.maxinteger,math.mininteger}
for _,field in ipairs({'masks','saved_masks','entity_words'}) do
    for _,value in ipairs(bad) do
        local s=state(); s[field][1]=value
        rejected(s,'invalid numeric type accepted: '..field)
    end
end
for _,field in ipairs({'masks','saved_masks'}) do
    for _,value in ipairs({false,-1,4294967296.0}) do
        local s=state(); s[field][2]=value
        rejected(s,'DWORD boundary accepted: '..field)
    end
end
for _,value in ipairs({-32769,32768,65535,4294967295}) do
    local s=state(); s.entity_words[28]=value
    rejected(s,'out-of-range signed WORD accepted')
end
local s=state()
s.masks={0.0,4294967295.0}; s.saved_masks={2147483648.0,4294967295.0}
local words={false,-32768.0,-1.0,-0.0,32767.0}
for i=1,28 do s.entity_words[i]=words[(i-1)%5+1] end
local r=native_skill_target_setup(3.0,8.0,-0.0,s)
assert(r and r.saved_masks[1]==2147483648 and r.saved_masks[2]==4294967295)
assert(s.entity_words[2]==-32768 and s.entity_words[4]==0)
assert(native_skill_target_setup(3,255,0,s)==nil)
s.entity_words[1]=true
local ok,err=pcall(native_skill_target_setup,3,255,0,s)
assert(not ok and err:find('native_skill_target_setup',1,true),
       'missing record bypassed state validation')
""")

    def test_sparse_states_against_current_model(self):
        by_key = {(row[5], row[6]): row for row in self.records}
        selected = {}
        for row in self.records:
            selected.setdefault(row[4][0x45], row)
        for key in ((3, 7), (3, 8), (3, 9), (3, 10), (3, 11)):
            selected[key] = by_key[key]
        words = (None, -32768, -1, 0, 32767, None, -1) * 4
        states = (
            targeting.TargetState((0x80000000, 0x40000000), (0xffffffff, 0), words),
            targeting.TargetState((0x2001, 0x40000420), (0, 0x80000000), words),
        )
        script = []
        cases = 0
        for row in selected.values():
            fields = targeting.Fields.from_record(row[4])
            for actor, state in zip((5, 12), states):
                expected = targeting.target_masks(fields, actor, state)
                setup = (targeting.setup_parameters(fields.mode_45)
                         if 1 <= fields.mode_45 <= 17 else None)
                script.append(
                    'do local s={masks={%d,%d},saved_masks={%d,%d},entity_words={%s}};'
                    % (*state.masks, *state.saved_masks,
                       ','.join('false' if x is None else str(x) for x in state.entity_words)))
                script.append(
                    'local r=native_skill_target_setup(%d,%d,%d,s); assert(r);'
                    'assert(r.masks[1]==%d and r.masks[2]==%d);'
                    'assert(r.saved_masks[1]==%d and r.saved_masks[2]==%d);'
                    'assert(r.stored_mode==%d and r.passes_kind_gate==%s);'
                    'assert(r.setup_valid==%s and r.setup_value==%s and r.setup_flag==%s);'
                    'assert(r.record_sha256==%s and r.source.dataset_id==%s);'
                    'assert(s.masks[1]==%d and s.masks[2]==%d); end'
                    % (row[5], row[6], actor, *expected.masks, *expected.saved_masks,
                       expected.stored_mode, str(fields.passes_kind_gate).lower(),
                       str(setup is not None).lower(), str(setup[0]) if setup else 'nil',
                       str(setup[1]) if setup else 'nil', json.dumps(row[3]),
                       json.dumps(catalog.DATASET), *state.masks))
                cases += 1
        self.assertEqual(cases, 44)
        self.check_bootstrap('\n'.join(script))

    def test_snapshot_isolation_with_aliased_inputs(self):
        mode17 = next(row for row in self.records if row[4][0x45] == 17)
        self.check_bootstrap(r"""
local s=state(); s.saved_masks=s.masks
local first=native_skill_target_setup(KIND,ID,13,s)
local second=native_skill_target_setup(KIND,ID,13,s)
assert(first.masks[1]==0x2000 and first.masks[2]==0)
assert(first.saved_masks[1]==0x80000000 and first.saved_masks[2]==0xffffffff)
assert(not rawequal(first.saved_masks,s.masks))
assert(not rawequal(first.saved_masks,first.masks))
assert(not rawequal(first.saved_masks,second.saved_masks))
assert(not rawequal(first.source,second.source))
local digest=first.record_sha256
local source=first.source.source_sha256
s.masks[1]=0; s.entity_words[1]=32767
first.masks[1]=99; first.saved_masks[1]=99; first.source.source_sha256='changed'
assert(second.masks[1]==0x2000 and second.saved_masks[1]==0x80000000)
assert(second.source.source_sha256==source and second.record_sha256==digest)
local third=native_skill_target_setup(KIND,ID,13,s)
assert(third.saved_masks[1]==0 and third.saved_masks[2]==0xffffffff)
assert(third.source.source_sha256==source and third.record_sha256==digest)
local catalog_snapshot=native_skill_catalog(KIND,ID)
catalog_snapshot.raw_record='changed'; catalog_snapshot.source.source_sha256='changed'
assert(native_skill_catalog(KIND,ID).source.source_sha256==source)
assert(third.damage==nil and third.cast_allowed==nil and third.multiplier==nil)
""".replace('KIND', str(mode17[5])).replace('ID', str(mode17[6])))


if __name__ == '__main__':
    unittest.main()
