# Review fixes: saved chat-name encoding and HUD hairstyle

## Changes

Migration19 adds name_codepage (0/936/950). New characters are inserted with0; first successful native world tail binds its language once, conditional on0 and authenticated ownership. Later logins never overwrite this field. Chat decodes the original name bytes with this stored source code page and encodes for the recipient. Character names are not phrase-translated. No raw profile or name bytes are rewritten.

The native creation record has no qualified language field before world entry. Therefore a new character's encoding is bound when its first world entry completes, not guessed from overlapping Big5/GBK byte ranges. Changing language after creating a character but before its first completed world entry is not qualified by this contract. Historical rows default to950, matching the original Taiwan-client convention; encoding cannot be reconstructed unambiguously for arbitrary pre-existing Chinese names. All actual deployed legacy names were inspected and are ASCII, so this migration is lossless for the current save. Imports containing legacy Chinese names require an explicit source-code-page mapping.

RecoveredWorldEntry now masks C36 with E7 for the HUD: high3 color bits remain, low5 hairstyle is reduced modulo8, matching original selection7FBD..8011. Source profiles remain unchanged.

## Tests and second review

- Nine isolated real C++ server chat tests pass, including Chinese names created under each encoding, same-language chat, server restart, opposite-language re-login and unchanged persisted codepage/name bytes.
- Native selection/HUD comparison now includes the original selection normalization instructions:448 cases (2 sexes x7 colors x32 hairstyles) pass. Calls into rendering are observed, not pixel captures.
- Eight original world-entry decoder/actor tests pass. The C++ assertion fixture also checks the normalized low5 maximum value.
- Two town presence/door/battle/chat regressions pass.
- Migration18->19 on a SQLite backup preserved every pre-existing table value; only the new metadata column and migration history were added. quick_check passed.
- Deployment occurred with no established player connections. Full pre-migration save and previous server executable are retained in artifacts/runs/name-encoding-fix-20260925.
- Live server PID6052 at127.0.0.1:2592: test and test1 authenticated, portraits matched their selection records, own and peer chat included the correct name, and database integrity passed. Post-deployment accounts and original character columns exactly match the backup.
- Client EXE unchanged. No foreground input, graphical capture, password resets, or movement were performed. Actual rendered UI acceptance is not claimed.

Evidence: artifacts/runs/name-encoding-fix-20260925/verification.json and live-verification.json. No remaining failing test in the scoped regression set. This does not certify the entire game or every client packet.
