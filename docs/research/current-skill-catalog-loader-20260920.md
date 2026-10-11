# Same-VM original skill catalog loading

`current_skill_catalog_loader.py` executes original entry `12D3B0` to its
`ret 4`. This is an explicit constructor preparation stage, not execution of
the preceding `110C21` path-resolution/formatting caller or entire constructor.
The input path is the original image literal at VA `59C5E4`, not a fabricated
game-function return. The current source is `Data2/Fight/Spg/cbspec2.bin`, SHA-256
`7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.

The loader performs exactly these read-only CRT operations:

1. `14716F` opens the literal path with `rb`, returning to `12D3C3`.
2. `14785C` reads four version bytes into the caller argument slot, returning
   to `12D3DB`. Original `155980` performs the bounded version comparison;
   its captured locale state is checked, not replaced with a guessed result.
3. `14785C` reads `1B810` bytes into `manager+A7E0444`, returning to `12D42A`.
4. `147182` closes the stream, returning to `12D430` after all112660 bytes.

The existing `NativeIndoorResources` CRT adapter supplies file bytes. Every
caller, destination, size/count, stream position and mode is qualified before
delegation. All game instructions are original. Executable ranges are checked
against the pinned image, and unexpected code paths stop immediately. The
original function does not check fread item counts: native EAX=1 by itself is
not proof of a complete load. The oracle rejects short virtual streams and
requires exact complete destination bytes, unchanged neighbors and no open
handles on success. No malformed input is silently accepted as a native asset.

Independent tests compare all four complete banks and all448 populated110-byte
definitions; image bytes and adjacent memory remain unchanged. Changed source
hash, executable bytes, locale state, repeated load and truncated virtual stream
are rejected. Initial4/4 tests pass in0.270s.
The integrated bootstrap21/21 tests pass in108.605s, including byte-exact catalog
retention after the normal initializer and native S2C34 count/pointer writes.

## Bootstrap Composition

With explicit `character_row`, bootstrap loads the catalog AFTER preparation
poisoning so the existing adjacent UI storage cannot erase its first bytes.
`manager+A7E0444` equals `battle+A924D7C`, the address already passed by original
`1112C0` into `11BB80`. No destination bytes are transplanted from another VM.

Original `687EB..68804` publishes the catalog pointer into character root+4504
and clears root+A8. Optional explicit `learned_records` are exact four-byte
logical S2C34 records handled by `NativeBattleLearnedSkills` in that same VM.
The integrated diagnostic requests row100 / bank0 / entry1; actual `AA660`
writes count1 and a pointer to the first nonzero source definition. It stops
before `AA7BF` refresh. These records are test inputs, not captured learned
ownership or monster skill assignments. The complete actor changes must equal
native write traces before the normal initializer begins.

The normal initializer boundary remains `11BC2A` pending qualification of the
remaining selector setup and pagination. Catalog loading and S2C34 preparation
do not establish damage formulas, a monster repertoire, live battle acceptance,
or a complete initializer return. No server DB, C++ runtime, Lua rules, current
client files, UI or network processes are modified by these offline proofs.

```powershell
python -B -m unittest discover -s tests/research -p test_current_skill_catalog_loader.py -v
python -B -m unittest discover -s tests/research -p test_current_battle_bootstrap.py -v
```
