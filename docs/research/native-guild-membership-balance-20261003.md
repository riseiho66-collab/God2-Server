# CUSTOM-0078 membership policy reference

Observed 2026-10-03. Scope: isolated implementation and candidate verification;
not installed in the formal server. Source is community historical documentation,
not a build-matched original server database or executable formula.

[Bahamut8591: 洞府成立條件及規則](https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E6%B4%9E%E5%BA%9C%E6%88%90%E7%AB%8B%E6%A2%9D%E4%BB%B6%E5%8F%8A%E8%A6%8F%E5%89%87)
describes a level30 requirement, a50000 creation fee, and an initial20 members
including the leader. Its growth rule adds2 places per guild level up to40.
It also describes a three-day wait after departure and leader admission authority.
These are observations from the reference; they do not recover server execution.

The pinned current client's ProgramMsg181 independently displays a50000 creation
fee. Only this display statement is native evidence. The Lua policy selects
50000/30/20 as explicitly reference-based CUSTOM rules. Native roster capacity50
is a client technical ceiling, not the chosen gameplay limit.

Balance acceptance must verify exact boundary levels29/30 and wallets49999/50000,
one debit per successful creation, conservation of unrelated balances, collisions
and repeated requests without extra debit, and capacity20 with full rollback of
a twenty-first membership. No test fixture money or level may enter formal saves.

Joining creates a pending application; it is not instant membership. Approval
requires a currently authoritative owner and the complete expected roster. This
isolated stage implements no guild EXP, automatic capacity growth, officers,
leadership transfer, dissolution or three-day departure cooldown. Existing
CUSTOM-0077 leave behavior remains frozen. Those gaps block complete playable
guild acceptance and must be addressed before promoting this membership feature.

Replacement: retain native build/source provenance and migrate these individual
rules explicitly if original server evidence becomes available.
