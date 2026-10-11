# Current-native C2S31/68 UI send gates, 2026-10-06

The verified mapped client image is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses below are RVAs at base `0x400000`. The bounded original bytes,
disassembly, and per-slice SHA-256 are in
`artifacts/integration/packet-connections-20261006/wrapper-ui-context-static-v3.json`;
`tools/reconstruction/wrapper_ui_context.py` reads only the verified archive.
This extends the earlier wrapper census and frontier without replacing them.

`BF300..BF505` establishes the direct C2S `31 00` route. First,
`UI+232DAA` must be a nonnegative row index whose widget flag has bit
`0x10`. Six further signed row indices are checked in sequence:
`UI+232DC8`, `+232DDC`, `+232E26`, `+232E28`, `+232DC0`, `+232E38`.
A nonnegative index whose widget flag has bit `0x08` diverts to `BF501`;
negative indices are skipped. Only after all six checks pass does
`BF465..BF471` call `961A0(0x31,1)`, followed by local cleanup. The
earlier wrapper census establishes that selector 2 queues `31 00`.
The widget flags are local presentation state, not server ownership, a
transaction commit, or an S2C reply. The earlier frontier's three-row
description covered only the tail; the bounded full function proves six.

The C2S `68 00` candidate has four distinct direct calls to `961A0` in
`C3750..C39C3`:

| call RVA | Immediate native gate |
| --- | --- |
| `C3795` | Input flag `0x04`, with `UI+E216C == 0` |
| `C37B3` | Input flag `0x20` and input word `== 2` |
| `C3832` | Signed `UI+232DA8` index nonnegative and selected widget flag `0x10` |
| `C39BD` | Signed `UI+232DA6` index with flag `0x20`, `UI+E216C == 0`, then selected `UI+232DA8` negative or its flag `0x20` absent |

The fourth sender's opposite selected-row branch calls a local UI function
and clears `UI+232F5C`; other branches also call local functions or show local
messages. Even at those four call instructions, wrapper `961A0` has its own
`UI+8AA4C/+F4` low-bit branch that may handle the event locally instead of
queueing. Thus a caller count is not a packet transmission count. Input
bits and widget flags are only native producer gates; they do not define
server-side authorization or response semantics.

Both C2S opcodes remain outside the current WORLD parser/Application route.
The same-number S2C entries have their own length/dispatch table entries;
matching numbers alone do not establish causality. The next useful trace is
to identify the owning UI action/row state and observe or statically prove
which server response updates it, then bind that to an authoritative saved
operation before implementing an Application handler. No success handler,
generic acknowledgement, or guessed S2C packet was added. This round ran no
client, build, test, acceptance or deployment.
