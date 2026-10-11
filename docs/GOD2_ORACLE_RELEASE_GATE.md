# Oracle qualification and release gate

Phase 31 requires a passing capsule corpus, zero output and state mismatches,
two fresh sessions A/B with distinct seeds and keys, accepted C2S and S2C,
and zero brute-force work. Offline replay alone never proves recovery.

`tools/crypto_oracle/qualification.py:evaluate_qualification(report)` is an
independent, nonexecuting evaluator. Its maximum status is
`ORACLE_EQUIVALENT_OFFLINE`; `CRYPTO_RECOVERED` is always false and
`promotion_blocked` is always true. Invalid offline evidence returns
`ORACLE_EVIDENCE_REJECTED`. Every result names the next live gate and missing
evidence. There is no runtime adapter, validator callback, CLI, client launch,
or emulator here. The parent owns diff execution, corpus and CLI integration.

## Report contract

Required top-level fields: `capsule_corpus_pass` (literal true),
`output_mismatches`, `state_mismatches`, `brute_force_count` (strict integer
zero, never booleans), nonempty `run_id` and `session_id`, `offline_vectors`,
and `live_sessions`. A summary PASS flag is insufficient.

Each raw reference is an object with `type`, lowercase `sha256`, and
lowercase `raw_hex`. The hash covers the actual decoded bytes. Those bytes
encode a UTF-8 JSON object; duplicate JSON keys are rejected. A digest without
bytes, a mismatched digest, or a boolean is rejected. Hashes establish byte
integrity only; supplied hashes do not establish trusted capture provenance.

`offline_vectors` contains `oracle_diff_vector_v1` references. Each decoded
record has `run_id`, `session_id`, `vector_id`, `direction` (`C2S` or `S2C`),
`sequence` (per direction contiguous integer starting at 1), and nonempty raw
hex fields `input_hex`, `state_before_hex`, `oracle_output_hex`,
`clean_output_hex`, `oracle_state_after_hex`, `clean_state_after_hex`.
At least two packets in each direction are required. Exact output and state
bytes must match, consecutive state must chain, and vector IDs and payload
identities must not be duplicated. The producer must include every relevant
state byte: this evaluator cannot discover omitted state or omitted corpus
vectors. Offline status applies only to the supplied evidence set.

`live_sessions` must contain exactly two `live_session_v1` references, labeled
`A` and `B`. Decoded records require distinct `run_id`, `session_id`,
`seed_sha256`, `key_sha256`, `backend: "Clean"`, `fresh: true`, integer
`c2s_count`/`s2c_count`, and `packets`. Packets use `live_packet_v1` with the
same fields as offline vectors plus `client_output_hex`,
`client_state_after_hex` and `acceptance`. Three-way bytes must agree.
`acceptance` is a `parser_acceptance_v1` raw reference bound to the same
run/session/vector/direction, with nonempty `parser_event_id`,
`result: "accepted"`, and `consumer: "clean_parser"` for C2S or
`consumer: "original_client"` for S2C. Counts must match the raw records.

These live schema checks are diagnostics, not runtime validation. Even a
fully populated, correctly hashed synthetic report cannot promote recovery.
A future separately reviewed typed trusted runtime adapter must attest raw
capture provenance, actual fresh initialization and seed/key derivation,
complete relevant state, Clean execution, and actual parser/client acceptance.
No report field can enable that absent adapter. No live sessions should be
launched to satisfy this task; full-client/UI launches remain frozen.

## Parent-owned production guards

The parent must add `GOD2_ENABLE_ORACLE_LAB` default OFF and a fatal configure
error when enabled for the production server. This is required independent of
Debug/Release configuration: a Debug production target must not admit OracleLab.
This agent does not edit CMake or claim that the guard is already installed.

Review found the root build uses `src/*.cpp` recursively for `god2_core`, links
`god2-server` to it, and installs the server, protocol-replay, config and scripts.
Keeping extracted code out of `src` is essential. The separate strike-lab build
does not by itself prove release isolation. Parent release tests should assert:

- Static CMake checks find the default-OFF option and fatal production guard,
  and reject capsule/oracle paths in production source/link/install rules.
- A configure test with the option ON fails before building production targets;
  an OFF configure succeeds without requiring local capsule files. Test both
  single-config and multi-config generators where available.
- Inspect the generated production target dependency graph and source list:
  no original code, embedded capsule bytes, emulator or OracleLab executable.
- Stage installation and package archives in a fresh directory. Compare every
  file to an explicit release allowlist; reject capsule pages, snapshots,
  original binaries, local oracle executables and raw capture artifacts.
- Check installed executable imports/dependencies and resource content against
  local artifact manifests/hashes. Filename checks alone do not catch renamed
  or embedded original code. Review runtime process-launch paths as well.
- The server has no route to spawn/load the local oracle in production. Lab
  execution accepts only explicitly configured local restricted artifacts;
  hashes never grant permission to bundle or redistribute them.

Existing generated capsules remain local artifacts, never source or distribution
inputs. Release tests must not copy them into a package just to test exclusion.
Use synthetic sentinel fixtures for static/package negative tests. Raw references
may contain sensitive bytes and belong in restricted local storage; normal
qualification output returns only counts and diagnostics, no raw payloads or keys.
