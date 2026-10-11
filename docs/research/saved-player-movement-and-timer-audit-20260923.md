# Saved player position and timer audit (2026-09-23)

The last visible black-screen reproduction on the original client used the
older launcher-generated executable. Its isolated server log accepted world
initialization at11:11:58.801 and projected town guides at11:11:59.368. At
11:11:59.369 the client immediately sent a native severity1 diagnostic with
text `timeGetTime`. There is **no accepted movement record before that
diagnostic**. The later two-byte opcode02 arrived at11:12:15 after the modal
and was rejected. This ordering supports the client timer check as the first
observed failure; it does not support a server movement rejection as the cause.

The latest launcher-built executable (SHA256
`ae997bbe726afaaee3a02ff9b718eff03f3d726002bc6aa36ce66a1964241f7f`)
patches both startup and world-loop timer checks. Native-function tests cover
the world-loop branch under the hooked `timeGetTime` prologue. There is no
post-login rendered town run of this latest build yet; the visible black-screen
outcome remains unverified. The Desktop `封神2.lnk` shortcut points to
`God2ClassicLauncher.exe`, which uses the native support build. Old generated
EXEs also remain in the game directory and should not be treated as the
latest patch during any future playtest.

To independently check the saved player position, a consistent copy of the
persistent SQLite database was made under
`artifacts/playtests/user-position-20260923-01`. Only the copied account2
credentials were replaced with laboratory credentials. `probe.py` used
original-format dual-socket login and an original-code-generated world-ready
tail for the saved character2 at town59,55/revision9. Two legal adjacent
movement records went to59,56 and58,56 with S2C5D ACKs, saving revision11.
After a fresh isolated server process, the same character re-entered the
world, received guide NPCs and restored58,56/revision11. SQLite `quick_check`
passed. The original persistent database still has character2 at59,55/
revision9 and no inventory slot rows for that character; its quick_check is
`ok`. This verifies the current server path for the player's saved character
under the recovered packet contract, not physical mouse movement or rendering.

The persistent service remained running at127.0.0.1:2592 throughout this
audit. No desktop input, original account credentials or original player save
were used in the isolated probe.
