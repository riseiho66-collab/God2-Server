# Native Lab: current implementation boundary

Local research only. This standalone Win32 project is not included or installed
by the production server. No original client code is embedded in its binaries.

```powershell
cmake -S tools/native_lab -B build-native-lab -A Win32
cmake --build build-native-lab --config Release
ctest --test-dir build-native-lab -C Release --output-on-failure -V
python -B -m unittest discover -s tests/research -p 'test_native_*.py' -v
python -B tools/native_lab/action_equivalence.py
```

God2LabAgent.dll currently exports only identity/refusal diagnostics. Explicit
initialization checks the pinned lab working-copy path, executable SHA256,
image base, and four 16-byte runtime code hashes. Even when these match,
unproven layouts/action equivalence prevent internal invocation. No successful
live GOD2 initialization has been tested. DllMain performs no instrumentation.

God2NativeTransactionTest exercises a separate COW memory primitive on its own
VirtualAlloc arena: first-write page undo, rollback, commit, owner-thread checks,
and a persistent unsafe latch. It runs 512 synthetic candidate executions with
deterministic output/rollback checks. It does NOT run an original GOD2 handler,
protect client heap pages, restore CPU/TLS/stack, or intercept irreversible
effects. Unknown ordinary writes outside the arena are not automatically
detected; explicit MarkUnsafe is not a substitute for side-effect closure.

No main-thread executor, action thunk, named-pipe RPC, packet/crypto tap,
transactional allocator, network/UI virtualization, taint engine or solver is
implemented. Those must not be presented as available commands. No injector,
client launch or UI repair was performed. The transaction primitive is not
enabled in the DLL's GOD2 execution path.

The frozen human run lacks the builder/state-write trace required by the new
action equivalence rule. RVA 0x7010 remains a static candidate, not a callable
qualified action. Evidence validators check structure only, not provenance.
No new edge is accepted; no native POST_6B checkpoint or speedup is certified.

Windows implementation constraints were checked against Microsoft's
[VirtualProtect documentation](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualprotect)
and [DLL initialization guidance](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-best-practices).
