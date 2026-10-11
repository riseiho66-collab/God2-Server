# Battle Owner Slot Binding

Current native image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

The bootstrap frontier at RVA110228 reads a WORD at owner+85A30.
This equals the first WORD of the existing slot store:
`owner+85610 + 44*24`. It is not a new constant or default-zero field.

`test_battle_owner_slot_binding.py` executes both original opcode3B dispatches
and the original98DD0 store, then enters110210 in the same VM without modifying
the resulting owner record. Five distinct WORDs (0,1,7FFF,8000,FFFF) each take
both equal and changed previous-value paths:20 producer/consumer cases.
Each asserts the exact110228 read address and width, preservation of all50
slot records and neighboring poison, unchanged battle/window memory and code.
The changed path stops at11023C with DI holding the packet-derived WORD;
the equal path executes the original return1102FF and restores its stack.

This is synthetic decoded-input proof with explicit battle/owner pointer and
window fixtures. It does not supply a real player's slot44 value, establish
its gameplay meaning, qualify item metadata/resources after11023C, connect
the bootstrap VM to this VM, or complete live battle initialization.
The bootstrap remains stopped at110228 until its owner binding is qualified.

Independent command:

```powershell
python -B -m unittest discover -s tests/research -p test_battle_owner_slot_binding.py -v
```

Initial main execution: all20 cases passed in0.539s.
