# CN offered summary, ordered common IDs and native world-mode lineage

Source/static-only round 2026-10-07. No builds, tests, client/server/socket
execution, Lua, asset loaders, production DB access or deployment. Previous
goal turn was progress: catalog30 sealed actual conditional Application/CN
listener and native-login composition sources. This round continues that chain.

## Shared source connection

Previously account A6's qualified07 stored only the common character ID list in
SharedWorldAdmission. World NativeOffer separately accepted a07 plus common IDs
from a supplier; membership checks did not prove that supplier's07 flags/raw
rows or common-ID order matched the earlier account offer. Two same-account
offered IDs could be exchanged without either losing membership.

SharedAccountSelection now supplies the exact complete75-byte07, together with
its ordered actual common IDs, before queuing that07. SharedWorldAdmission keeps
both in the same selected grant generation and destination; every subsequent
selection replaces both together. The4096-byte opaque-snapshot bound is an
operational budget, not a recovered packet length. No database schema is added.

Only a currently committed WorldOwned Ticket with matching grant generation,
world session and reservation can obtain OfferSource. Missing adapter bytes
return absent. SharedCredentialConnection exposes this only for its owned world
ticket. NativeOffer retains the full original07 and its supplied ID row order;
SharedWorldSelection compares both with that actual ticket source, then checks
current shared repository ownership, **before queuing1F**. Mismatch closes the
connection through the existing failure path. No synthetic reply is generated.

CnCharacterSummary::record_bytes copies its already validated full payload,
including flags, inactive rows, row18 and other opaque bytes. It does not fill
missing data or infer CN fields from TW profiles. This is a bounded server source
lineage invariant, not a recovered official server equality check. Live updates,
reoffers and other native variants still require qualified source/lifecycle work.

## Primary native owner chain

Existing native07 evidence00481640 stores payload1&1 at account network+4200.
00449310 copies account network UI+1617C to world network UI+16180; transfer
0044D5F0 has its corresponding+66C/+670 network copy.00445040 binds those UI
network pointers from the main owner+454/+458.

New primary owner trace:

-0048CAA0 copies main+458 world network to renderer+8885E4, then stores it at
  element1 of the actual initializer array passed to004AC850 at0048D670.
-004AC850 passes initializer[1] to004B09C0 at004ACD5E.
-004B09C0 stores that argument at player/UI owner+4308C.
-0050E3B0 reads owner+4308C ->network+4200 to select request branches; every
  recovered00481440 send in this producer uses the same owner+4308C as ECX.

This closes the network owner alias for this specific world producer. It does
not assign a business role (GM, ban, billing, observer, region, entitlement) to
bit0. Bits1..7 and server issuance policy remain unresolved.

## Bounded world request variants from0050E3B0

The dispatcher gets its selector from0050E5E0 using actual native UI state at
owner+22CE4 and the two actual arguments. Arguments-1 return without a request.
Mode1's named selector branches are19/23/24; other assertion/fallback domains
are not promoted as server permissions or complete producer variants.

| native branch | mode0 source | mode1 source | output in this producer |
|---|---|---|---|
|selector11 |owner+2E234 |generic fallback if obtained |94 payload8 |
|12 |owner+2F1FC |generic fallback if obtained |94 payload8 |
|15/16 |owner+30688/+36560 |generic fallback if obtained |94 payload8 |
|17/18 |owner+345D0/+35598 |generic fallback if obtained |94 payload8 |
|19 |owner+30E80 |owner+30E80 |94 payload8 |
|1B/21/22 |owner+31678/+32640/+33608 |generic fallback if obtained |94 payload8 |
|23 |owner+36D58 |owner+36D58 |94 payload8 |
|24 |[owner+1C85A8]+46A8 |same |94 payload8 |
|25/26 |D1 bytes25,01 or26,01; return |generic fallback if obtained |mode0 D1 only |
|27/28 |D1 bytes27,01 or28,01; fall through |generic fallback if obtained |mode0 D1 then94 |
|other selector |owner+22D0C+selector*3F0 |same generic fallback |94 payload8 |

94 copies eight stack bytes from EBP-8: selector at payload0, payload1..3 are
not written on this recovered path, and DWORD payload4..7 normally comes from
the selected owner field. For mode0 selector27/28, the primary branch sendsD1
then jumps to0050E525, queuing94 **without assigning EBP-4 on that path**.
Do not call these bytes zero padding, interpret their value as a common-ID
permission, or serialize invented zeros. Receiver, actual backend meaning,
authority and replies remain missing. No same-opcode S2C association is inferred.

## Function fragment evidence

0050E3B0's recovered header says153 bytes, and functions.tsv lists0050E449 as
another function entry. Primary JMP-table0050E544 nevertheless targets its
0050E449..0050E50D case blocks and shares the0050E522/525 output/return tail
through0050E541. Entry+153 stops at0050E449 and misses these native send blocks.
0050E5E0 and00511620 similarly have primary jump-table bodies beyond early
metadata function entries. Header size is not a proof of a contiguous complete
body. This round explicitly retains these code envelopes and table data.

The new static tool follows decoded direct branch/fallthrough edges, records
calls without executing them, and follows only the explicitly bounded primary
switch tables. It never treats table bytes as instructions or follows arbitrary
computed targets. Its local closure is not whole-image reachability/ownership.
Historical span scans and receipts remain unchanged; their bounded results must
not be promoted to full CFG/fragment closure or a complete game denominator.

## Accounting and next work

Source changes:8 existing C++ files,1 catalog tool; no newly introduced C++
handler or gameplay table. New native world producer sites qualified by this
owner chain:4 (threeD1, one94), with mode-dependent ordered output. These are
existing opcode values, not4 new packets or completed server routes. Existing
39 CN phase-source bindings/28 unique,7 TW bindings/7 unique and18 CN/2 TW
partial owner chains are unchanged. Complete routes added0; whole-game total,
completed route count and percentage stay unknown.

Remaining: real native07/1F and1D/0A value/alias issuers; complete mode0/mode1
producer/backend/receiver variants, authority and world rules; common actor/
scene02/2A/readiness, TW enrollment and later gameplay; fragment-aware indirect/
deferred whole-game inventory. Native bit0 is preserved source data, never a
shortcut for constructing success or authorizing gameplay.
