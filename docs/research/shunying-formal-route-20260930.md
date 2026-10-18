# CUSTOM-0058 formal learned-skill route

2026-10-19 source correction: current native8 consumes the signed83 amount at
its deferred hit event, while adjacent86/0 writes final HP during queue drain.
The current126 skill reply therefore omits per-target HP86 to avoid a second
client subtraction; friendly MP and barrier-delayed88 remain. Native DWORD
state checks are retained. See [round464 source](tw-skill-deferred-hp-source-20261019.md).
Historical tests/releases below were not rerun; this correction is source-only.

Owner authorized deployment of the accepted custom 瞬影三煞斬 on 2026-09-30.
This is custom kind0/id126, not one of the448 original native skill definitions.
The original catalog and native icon/bank counts are unchanged.

## Authority and acquisition

`character_deities.skills` stores original S2C34 records `(34,row_key,kind,id)`
inside a character-owned deity snapshot. This is learned state on a deity row,
not a recovered character-wide skill acquisition rule. Formal authorization
requires the session's account to own the character, the saved selected deity
to belong to that character, and that deity to contain kind0/id126. Presence in
the custom registry alone grants nothing. No F1 command, automatic skill grant,
test stats, additional deity, or manual battle fixture is enabled by this change.

The narrow custom126 exception permits trusted persistence/restoration of that
learned record for the installed client bridge. Other out-of-bank or missing
native icons remain rejected. Existing companion provenance is retained;
future trusted grants must retain CUSTOM-0058 evidence instead of claiming
native acquisition. Acquisition gameplay remains unimplemented.

## Combat and wire route

`Application.cpp` adds the skill policy while binding the existing encounter,
only when ownership above succeeds. It sends selectable87/126, preserves the
selected saved deity, and avoids the old diagnostic GOD1/id1 seed and policy for
this route. The existing C++ service validates authenticated actor/context,
opposing living distinct targets and1..3 target count; clones are presentation
only. The selected learned skill cannot be switched during pending battle by
the existing repository guard.

The approved coefficient is physical300% and cost20MP once for the whole cast.
The action retains existing defense and critical policy. C++ owns transactions,
RNG, source statistics and persistence; `scripts/gameplay/combat.lua` evaluates
CUSTOM-0006: floor(attack*300/100), minus floor(defense*defense_percent/100),
minimum1, then the existing critical floor and damage cap. Lua numeric inputs
are bounded unsigned32 values (attack<=1,000,000, percent<=10,000), so these
integer products remain exact. This does not certify native damage, hit,
defense, growth or balance formulas. For attack31/defense13, noncritical damage
is80 per target; 1/2/3 targets all consume exactly20MP.

The native83/type3 results carry126 and per-target signed16 HP deltas (reject
loss>32767). The accepted custom client bridge maps126 to native8 event timing
and borrows the current caster appearance. Native86 HP updates follow each
hit. Friendly caster MP is projected with86/1. The existing native86/1 consumer
does not qualify enemy MP display, so opposing casts charge server MP without
inventing such a record. Current-cycle88 closes a terminal cast; for a surviving
target the existing retaliation encoder closes the exchange with88. The next
grant still requires the existing native receipt. Owned126 encounters may
continue past the old one-round diagnostic cap so a300% cast cannot stall the
encounter after a surviving hit.

## Verification and limits

`test_shunying_sanshazhan.cpp` executes the real Lua rule for both sides and
1/2/3 selected targets, checks80 damage and20MP once,126/native88 serialization,
and atomic refusal of dead/duplicate/fourth targets and insufficient MP.
`test_owned_companions.cpp` covers absent/unselected/wrong-account/wrong-kind
authorization, saved126 restoration, and rejection of neighboring custom125.

The current formal encounter still has one enemy and existing CUSTOM diagnostic
actor statistics/retaliation. Its route can expose only the one-target case.
The core supports both sides and up to three existing opponents; there is no
new multi-enemy encounter, PvP, multiplayer battle sharing, skill acquisition,
or recovered native statistical formula. Unit/codec checks do not establish
new formal-current-client gameplay acceptance. Release deployment and live
acceptance evidence are recorded separately by the release operator.
