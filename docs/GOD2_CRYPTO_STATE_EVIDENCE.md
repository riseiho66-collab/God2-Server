# Crypto state instruction evidence

Source: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
Image base 0x400000. Addresses below are VA, not RVA. Read-only Capstone inspection.

Encode 0x410690 loads codec+0x2556 at 0x4106A2, resets index at 0x4106AC,
reads key codec+0x2420 at 0x4106C7 and preserves current plaintext at 0x4106D2
before ciphertext store 0x4106D8. Decode 0x4106F0 loads feedback at 0x410702,
resets index at 0x41070C, reads the same key at 0x410730 and XORs at 0x410737.
Neither writes the final index/feedback back. Key indexing cycles modulo 256.

Thus packet boundaries RESET to key index 0 and codec+0x2556. Only within a
packet does feedback chain from the previous plaintext byte. It is incorrect
to carry the last plaintext byte into the next packet for these routines.

Both routines use the same fields of their codec object. This does not prove
that every connection/direction references the same object; observer identity
and directional state remain separate until runtime evidence ties them.

Checksum 0x410670 is sum(byte+0x3c) modulo 256. Header bytes stay clear.
The cipher flag is DWORD codec+8. TX tests it at 0x4109E1..0x4109E8 before
encode call 0x4109F5; RX tests at 0x410A15..0x410A24 before decode 0x410A30.

Seed installation 0x410570 copies 16 seed bytes. Key expansion 0x410490 uses
table VA0x584C30 and helper0x410370. Feedback generation at 0x4104D0..0x4104F1
is negative sum of all 256 key bytes, modulo 256. `c2s0002.key()` is specifically
the zero-seed fixture, not a general fresh-session key derivation function.

Instruction proof does not establish fresh nonzero-seed interoperability or
live parser acceptance. Those remain runtime qualification requirements.
