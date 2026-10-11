# Native Debugger Pivot

Native x64 CDB is now the preferred observation path. Prior stack/sync/frame
captures remain intact as LEGACY_X86_TRACE. Their failures remain unexplained,
not reclassified as successful returns.

## Results

- NATIVE_WOW64_TRACE = QUALIFIED for one known boundary, reproduced in native-f
  and native-g. x86 entry 0x77547000 / ESP 0x1AFE68 crossed to native
  0x77547009 (CS=0033). Native return at 0x7754198B executed a far jump through
  selector 0x23 to 0x775CA03C / ESP 0x1AFE6C, same PID/TID. These are measured
  addresses for these sessions, not ASLR-independent constants.
- GOD2-NATIVE-MASTER-CAPTURE-01 collected unpack images, ordered major startup
  checkpoints, native boundary context, post-0x54A46E execution, loaded-module
  lists, and stable/next-stop images in one process.
- Its own G02 certificate is CODEX_VERIFIED. G03 remains NEED_MORE_EVIDENCE;
  no G04 or protocol claim was promoted.
- The next stop was ExitProcess(0), caller return address 0x54C7B4. No observed
  Winsock API hit preceded that stop. The process was then debugger-terminated.
- A focused native follow-up observed an empty argument string at 0x531DC5,
  then the untaken JNE at 0x531DCA and early-return path 0x531DCC.
- A separate controlled loopback argument test used
  `127.0.0.1 127.0.0.1 6001 1`. At 0x531E16 EAX=4; JGE at 0x531E19 was taken
  to 0x531E28. This is argument-parser acceptance, NOT connection/login success.
  It was intentionally stopped there. Existing launcher source suggested the
  four-token shape; its remote addresses were not used.

All screen/network milestones remain unestablished. Next work is startup with
controlled arguments and observation of the next real blocking condition,
not further repair of the legacy x86 tracer.

## Evidence

Capture: `6231f41eb441ea70a737fe6ab9929a46fb2e795aed93065d35c16181d8c243d7`

G02 receipt: `a686ee6f97ca40569478b67eff5fcd7a80f7b30978403c9aea9a783bba910e7e`

Receipt digest and bound-file hashes were checked after publication. It is a
local unsigned Codex-only receipt, not human attestation. G02's narrow unpack
claim is independent of the subsequent exit; that exit still limits G03.

Reports: `artifacts/reports/native-wow64-20260919/`.
`wow64-context-ledger.json` keeps EIP/ESP separate from RIP/RSP and links native
lines. Six priority loaded-module disk files were preserved, with hashes and
export tables. 342 image pointer slots matched those exports; they remain
OBSERVED_POINTER_NOT_REPAIRED_IAT. No import-directory repair was performed.
Disk copies after capture are not proof that every loaded module page matched.

Native-a stopped incorrectly at the extra WOW64 loader breakpoint and failed;
native-b rejected ambiguous transition symbols; native-d exhausted a short
trace budget in native REP code. Its marker named NATIVE_X86_RETURN does NOT
represent a real x86 return: CS remained 0x33 and the context conflicted.
Native-c/e showed partial boundary observations; only native-f/g underpin
qualification. All attempts are retained rather than rewritten.

Three new focused validator tests passed. The complete research suite was not
rerun this turn (previous turn: 84 passed). No original client edit, security
policy disablement, external server connection, or credential submission.
Existing work-copy firewall checks passed before launches. Native CDB used an
explicit local symbol path; the native debugger itself was not firewalled.
This is host debugging, not VM isolation.

Restricted archive: `artifacts/capture_work/g03-native-archive-20260919/`.

## Tooling

The installed WinDbg package already contained Microsoft-signed amd64 CDB
10.0.29617.1000. Earlier PATH/Windows Kits-only inventory was incomplete.
No download was needed. Tool SHA256:
`5f54abafca3ae5638bbf807d402fabb350a64575c1dfa9fbfc7f5732df5bee67`.

Commands follow [Microsoft's WOW64 debugging model](https://learn.microsoft.com/en-us/windows/win32/winprog64/debugging-wow64).
Changing effective disassembly mode alone is not proof of native execution;
qualification also checks actual CS selectors, native instructions, return
target, and coherent same-thread stack observations.
