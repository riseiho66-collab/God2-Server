# Login Terminal Acceptance

Final run: artifacts/runs/login-terminal-final-01.
Golden: artifacts/golden/login/login-terminal-final-01 (six packets, execution-order CSV).

LOGIN=true is now reserved for a successful terminal return AND an actual exit from the credential state.
Credential-request provenance alone no longer sets LOGIN. Historical runs retain their original metadata.

## Evidence

- After opcode 0x1d: enabled=1, accumulated=0; codec flags 0/4/8/c=0/0/1/1, feedback=0.
- No new transform was observed on that path. The installed zero-seed transform remains applicable.
- Opcode 0x0a: 17-byte payload (opcode + 16 result bytes), total frame 20.
- Exact accepted wire: 14000707fdfdfdfdfdfdfdfdfdfdfdfdfdfdba15.
- Handler RVA 0x14386 copies four DWORDs from payload offsets 1,5,9,13 to the result object.
- It compares result byte 0 with 5; value 5 adds a message, not a failure return.
- Zero result follows the direct return path. No account/profile meanings are assigned to the other bytes.
- RVA 0xb0d9 returns EAX=0; caller requests state 2; RVA 0xaffc writes it.
- Runtime evidence at RVA 0xb3a3: current state 2, previous state 0xf.
- Separate opcode30 / RVA0x14325 is a rejection path; not exercised in this iteration.

## Next Boundary

No new client TX was observed after acceptance before the next message-box stop.
The client reported that no servers were open. It has not reached a character screen.
NEXT_PHASE=CHARACTER, prerequisite POST_LOGIN_SERVER_LIST_EMPTY.
Do not infer client-first or server-first character exchange from this stopped observation.
No further login handlers were investigated after this acceptance.

## Reproduce

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --mode MODE_COMPAT --network-strike --cpp-server --post-seed --c2s-strike --s2c0003 --login-terminal --lab-case A --run-id UNIQUE_NAME --timeout 20
```

The dedicated loopback config adds the terminal frame after opcode29 in the same C++ write queue.
Prior packet encoders and configs are unchanged. Sending is not treated as acceptance.
The server remains a reconstruction lab, not a production authentication service.
Verification: 11 C++ suites, existing 24 Python tests, 4 new terminal tests passed. Processes cleaned.
