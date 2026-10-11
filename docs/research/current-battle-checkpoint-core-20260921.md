# Battle checkpoint core

CUSTOM-0007 checkpoint()/restore() preserves snapshot ID, revision, all28 actor
slots, controller identities, resources, attack/defense values, outcome and full
mt19937 state. It is trusted server state, not a native C2S message or stat source.
No seed is substituted on restore and defeated actors remain defeated.

Restore rejects unknown version, zero identity/revision, pending/invalid state,
slot mismatch, invalid resources/stat limits, missing sides and contradictory
winner/living-side conditions. RNG input is bounded to10000 bytes; expected word
count comes from the current runtime's default-engine serialization. Words are
bounded to32 bits, optional cursor to624, trailing/noncanonical text is rejected.
This qualifies current-runtime round trips, not arbitrary cross-library migration.

An initial test failed because MSVC serializes624 rotated state words without an
extra cursor. Local MSVC14.44 random header confirmed stream extraction seeds those
words and emission uses _At ordering. Validation now derives runtime layout rather
than imposing625 words. Future disk formats must record engine/runtime compatibility.

Release build and battle_transaction/recovered_battle_service pass. Tests restore
after player multi-target attack plus retaliation, then compare subsequent critical
rolls, native-framed responses and complete checkpoints for both original and
restored cores. Twelve invalid checkpoint cases are rejected. A finished defeat
round-trips with winner preserved and cannot act again. No client live run claimed.

Still required: durable atomic resource/checkpoint storage, policy version and
authorized action/control state, ownership lease, reconnect handshake and native
client battle reinitialization. This API alone does not implement crash recovery.
