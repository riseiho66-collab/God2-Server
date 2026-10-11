# Explicit-table progression policy

Follow-up: the default-off diagnostic_progress_span path now calls this API
with committed owned XP and an explicit test interval. See
current-derived-progress-20260921.md. The historical no-Application-call note
below describes the initial delivery; production remains disabled.

CUSTOM-0013 is a pure Lua policy, not a recovered formula or production curve.
The owner allows documented custom fallback but requires balance and real-client
acceptance before production. No supplied official table has been established.

## Targeted evidence check

Existing current-role-progression and role-growth reports prove packet-fed
level/proportion fields, not absolute XP thresholds. On2026-09-21, targeted
searches for site:xjz.17173.com upgrade experience tables and Bahamut8591
experience/level pages did not yield a verified per-role threshold table.
Direct xjz.17173.com fetch timed out and the supplied Bahamut namespace entry
returned403. This is a limited search/access result, not proof of absence.

Search surfaced Bahamut185 issue material discussing progression gates and
experience-transfer items, not a numeric threshold curve:
https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%EF%BC%91%EF%BC%98%EF%BC%95%E6%9C%9F
The supplied community source is not automatically current-build authority.
No dates, levels, caps or values from those snippets were installed as rules.
Player, companion, pet and guild experience categories must remain separate.

## Contract

Input: signed64-compatible banked totalXP; explicit cumulative threshold vector
with first entry0, strictly increasing, at most255 entries; explicit unlocked
level1..table-size. No default thresholds, level cap or unlocked level exists.
Each interval is limited to INT64_MAX/10000 for exact integer multiplication.
This is an implementation arithmetic bound, not an official game XP limit.

Lua computes the highest earned level not exceeding the supplied unlock gate.
Within an interval it floors earned*10000/span, clamping earned at that span.
At the explicit table cap it returns10000. Locked surplus remains banked in
the caller's totalXP; this is a custom retention policy, not original behavior.
Output is level plus0..10000 display proportion. No total, resources, player,
database, reward or packet is mutated. Input snapshots isolate Lua from live
state. C++ checks widths, policy validity, return bounds and unearned levels.

Only tests use cumulative0/100/300/1000. They cover1201 totals including exact
thresholds and multilevel jumps; a lock at2, unlocking at4, rounding, signed64
maximum banked XP, largest exact interval, malformed/missing tables and reload.
The25XP ->2500 example follows only that explicit synthetic table; it does NOT
retroactively turn the earlier native sentinel experiment into a real curve.

## Activation boundary

Application does not call this API. No production row or initial character
level changes, no native packet is added, and no balance approval is asserted.
Stat gains, level-up packet22, lock quests, total reset/transfer behavior,
curve version persistence, authoritative companion state and re-login display
still require implementation/qualification. The existing native2B sentinel
remains an independent diagnostic, not automatically a production projection.
