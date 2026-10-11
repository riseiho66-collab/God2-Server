# POST_6B capture prerequisite

The saved ui-gate-real-04 evidence does not contain a replayable post-send
memory snapshot. No next direction, handler, candidate, or transition is known.

`post_server_select_observer.py` now calls `post_six_snapshot.capture_post_six`
while stopped at the matched six-byte send return, before releasing the hold.
This is an initial capture seed, NOT God2ProtocolOracleVM or a complete capsule.
It has not been exercised against a live debugger.

The seed stores x86 integer registers/flags, 4 KiB of stack, the 0x255c-byte
codec, and two continuation code pages. It additionally stores 0x40d8 bytes
of the protocol object only when saved-stack, ESI, EDI and continuation
relationships agree. Each complete region has a SHA256. Short reads are not
accepted; existing capture directories are never overwritten.

Opaque memory may contain credentials or keys. It stays under the ignored
run-local `protocol-private/post-six/` directory, not ordinary JSON logs.
This is source-control exclusion, not encryption or a filesystem ACL.

UI object identity, globals, synchronization helpers, remaining dependencies,
pointer canonicalization and three deterministic original-code replays remain
required. The seed always reports CAPSULE_INCOMPLETE and replay_ready=false.
No cache key or semantic state fingerprint is fabricated from raw addresses.

The latest native Computer Use availability check failed with missing native
pipe (os error 2). No new client session or full-client iteration was started.
VM, forkserver, solver, codegen and speed certification remain unimplemented;
their prerequisites are not met. Existing server and crypto code are unchanged.
