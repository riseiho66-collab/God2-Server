# Role progress packet preparation

Current-role-progression-20260919.md already proved native S2C2B stores and
percent conversion. This change connects those known instructions to actual
C++ codec output; it does not claim their discovery as new evidence.

RecoveredRoleProgress accepts exactly21 logical bytes starting2B and owns a
lossless copy. The exposed logical offsets are roleHP1/DWORD, roleMP9/DWORD,
role progress17/WORD, companionHP5/DWORD, unclassified companion scalar13/WORD
and companion progress19/WORD. Logical15..16 remain opaque. The scalar at13
is deliberately not assigned an MP or attribute meaning.

with_role requires an existing complete parsed record and changes ONLY role
HP/MP/progress. It never synthesizes companion state, normalizes unknown bytes,
or treats progress as an absolute XP counter. Full WORD bit patterns survive;
the native reader uses unsigned WORD rather than masking the high bit as the
different companion31 producer does. No runtime sender has been activated.

## Verification

C++ checks all shorter lengths, oversized input, all256 opcodes, owned-copy
behavior, zero/high-bit/max DWORDs, field replacement and every preserved byte.
Standalone build uses C++20; private native-test build uses the existing strict
compiler adapter.

test_current_role_progress_codec.py sends11 records through the compiled C++
parse/update/encode path, then executes unmodified pinned current instructions:

- E6390..E63C5 role stores: whole actor snapshot comparison checks HP5C,MP64,
  progress58 only. A poisoned level26 remains unchanged.
- AA3F0..AA422 companion stores: whole companion snapshot checks2C/34/28.
- AC2C0..AC2FF plus149630..149657 converts the resulting role WORD to the
  integer bar argument using original x87 arithmetic. Input values include
  0,1,99,100,101,2499,2500,9999,10000,32768,65535. No actor mutation follows.
- Original packet body remains unchanged. Unknown15..16 are nonzero canaries.

Two new Python tests pass, including the compiled C++ self-test. These are
bounded native slices with synthetic state, not a live receive/UI acceptance.
The original helper bounds and pinned image hash remain enforced.

## Next Integration Requirement

Use the committed server XP ledger with a separately qualified level threshold
policy to derive a progress display. Native thresholds remain unproved; do not
reinterpret DWORD5 of89 or WORD17 of2B as that missing policy. A custom policy
must stay labeled and pass balance before production. Build a complete current
role/companion snapshot before sending2B, then qualify the live consumer and
world/battle transitions. No level-up, growth, persisted companion state or
normal-gameplay completion is claimed by this codec.
