# Simplified client table byte recovery

The original client's `Data2/Patch/Comm/gamedata.csvZ` is mostly CP950, but
the decoded 2,783,008-byte source contains 46 CP950 replacement positions.
The first generated `gamedata-gb.csvZ` treated every one as an unknown glyph.
Several affected rows are item and pet names, so this can produce visible `?`
characters in Simplified mode. The pinned original compressed source remains
SHA256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.

`tools/locale_probe/build_simplified_assets.py` now decodes valid CP950 as
before, then retries **only a CP950-rejected sequence** as one Big5 HKSCS
character. It accepts that fallback only when the two source bytes decode to
one Unicode character. Remaining invalid source sequences become `?`; target
characters CP936 cannot encode also become `?`. The latter losses are not
silently claimed translated. This is an asset compatibility repair, not a
change to the original source or a claim that every rare glyph renders.

The candidate build recovered 27 HKSCS-only characters and left seven source
sequences unresolved. CP936 still replaced 43 Unicode characters, largely
rare glyphs. Compared with the prior packaged output, only
`gamedata-gb.csvZ` changed among 46 generated files; 23 rows differ and the
decoded target's literal question-mark count fell from 80 to 55. All 46 source
hashes remained identical. The old generated target is retained under
`artifacts/locale-simplified-hkscs-20260923/pre-change/`; the candidate report
and generated files are in the same artifact directory. The new target SHA256
is `66c296fa27ebfbaa9434cb3e3707e23b79828b37ce7a0129d439b393ff00a7ff`.

The new `gamedata-gb.csvZ` is installed identically in the launcher source
distribution, exported player package and current client directory. The
launcher project tests pass. Windows 10/11 visual inspection of the affected
rows is still required; this byte-level result does not prove client rendering
or resolve genuinely unrepresentable source names.
