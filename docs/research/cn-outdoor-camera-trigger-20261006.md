# CN camera projection and native map-reference trigger

The previous round made concrete progress: decoded outdoor profiles and complete
nine-slot cache transitions were sealed. This round adds two C++ sources and
connects the actual native camera projection/visibility/reference preparation to
that same cache identity/generation. No build, asset reader, Lua, client/server,
test, production DB or deployment is executed. Native fonts, conversion, frozen
chat/IME, accounts and saves remain unchanged.

## Native projection

00472380 mode0 adds3360/840 pixels before00475BE0 with21/21, then subtracts
21/63 from its result.00475BE0 uses signed truncating division/remainders by80/40
and004749A0's five diamond regions. Pinned SSE constants are+0.5,-0.5,20,0;
their residue expressions are exact half-integers, so scaled integer comparisons
preserve native boundary ties. The five x/y offsets at007F0FB8/007F0FCC are
retained with exact native bytes. Unsupported arithmetic overflow is absence,
not malformed-input wraparound or a fabricated camera/position.

0046CE10 derives four viewport corners using actual map+FD8 viewport+1C/+20,
loaded-center tile extents+34/+38 and the converted camera point. Shift thresholds
are less than-19 and greater than/equal40; each axis yields-1/0/1. The native
nine visibility flags are explicitly cleared, then marked from in-range corner
slots using signed truncating division by21. The exact unique-corner bridge
conditions are retained: bridge first two when count>1, remaining pairs only
when count==3. This is not a rectangular fill or an actor movement direction.

These View values must come from the real scene/camera owner. They are never
decoded from2E, inferred from catalog kind, assumed from desktop dimensions or
supplied by a client protocol/language bit. World authority and per-recipient
visibility are separate from this recovered renderer calculation.

## Native .map reference and switch candidate

00473120 only tries a mode0 resource switch when shift is nonzero and map+34
is5/16/17. It adds that shift to the current origin/21 center; negative candidate
coordinates skip switching. Its name uses the actual map+1044 native prefix and
format007F0100="%s%sx%s.map". Axis helper004621F0 uses007F0384="%c%d":
the integer quotient by10 plus65 produces the letter and the remainder the digit. Thus the
qualified axis subset isA0..Z9, not decimal strings.00461ED0 accepts ASCII
alphabet/digit and uppercases the letter: (letter-'A')*10+digit. The formatter
emits nonalphabet characters above259; those and locale-dependent high-byte
classification remain unresolved variants, not silently normalized.

CnOutdoorWindow.prepare_camera uses that actual owner prefix, current cache
center, supplied View and native map+34 to create a CameraPrepared candidate.
It carries the private cache identity/generation, recovered Projection and an
optional MapSwitch containing its native reference/requested coordinates.
current rejects another cache or a changed generation. This does not mutate
camera, native cache, player storage or packets.

00470440's nine actual screen offsets at007F0E68 determine the camera position
AFTER real00470C90 success. The candidate retains this conditional result; it
must never be applied just because projection or reference formatting worked.
No callback with a default success, invented opcode or guessed5D is added.

## Still open

00470C90 selects/replaces map+1024[map+102C], qualifies its .mdt/.map source,
clamps MBD/MDT coordinates and loads conditional/standalone resources. Native
prefix/resource identity, replacement and successful publication remain actual
owner obligations. It is not generally equivalent to0046C830 or reloading the
same retained asset on every move. Native camera state/actor linkage and visible
slot/render application remain unhosted.

Full failed/null/partial loads, runtime object/mask changes, actual actor/scene
revision, timing/sequence/reset/5D, common position/cache transaction, TW/CN
publication, later dispatcher and Application remain missing. The new helpers
are concrete source branches, not completed source routes or playable movement.
M1 still requires all direction/phase/state/variant/indirect/deferred paths.
Added opcode/phase bindings0; complete routes0; whole-game total/completed/%null.
All historical manifests and old native source hashes remain unchanged; this
round separately preserves new C/ASM/PE/table/format evidence and source edits.
