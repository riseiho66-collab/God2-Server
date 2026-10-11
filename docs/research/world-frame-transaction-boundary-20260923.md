# Native world frame transaction boundary

The original connection carries length-delimited world frames. TCP may deliver
several complete frames in one read; that read boundary is not a client
operation. The prior `Session::Impl::feed_world` appended every decoded record
from one read into a single callback. A valid movement frame followed by a
chat or NPC frame could therefore be rejected as a mixed policy batch solely
because those frames arrived together.

`feed_world` now validates and dispatches one complete frame at a time, then
drains already buffered complete frames before reading the socket again.
Records inside **one** frame remain one policy batch, so a malformed chat
behind movement in the same frame cannot commit the movement prefix. A
continuing native skill sequence still stages its records across frames until
the terminal skill record arrives, with its existing deadline and sequence
checks. Independent earlier frames may commit before a later frame fails;
they are separate client operations.

Verification:

- Release server and `god2-tests` build. The build also exposed and fixed a
  missing CMake exclusion for the standalone native skill-book catalog test.
- CTest `session_state` (93.64 seconds) and `session_skill_sequence` pass. The
  socket test now requires two coalesced complete frames to invoke the world
  handler twice, and requires movement followed by chat in one TCP write to
  reach separate policy callbacks.
- Eleven recovered movement socket tests pass, including fragmentation,
  coalesced movement, same-frame invalid batch rejection, rollback and restart.
- `recovered_chat_server` checks movement ACK before independent chat delivery,
  a same-frame malformed chat blocking movement, and a later malformed frame
  leaving the earlier ACK/position committed. It passes with two actual
  authenticated original-protocol sockets.
- CTest `native_skill_book_catalog`, `recovered_world_records`,
  `recovered_world_service` and the repeated skill sequence pass.

This repairs transport grouping; it does not authorize a true client-produced
compound operation such as `85+37` in one frame, supply an NPC gameplay rule,
or establish rendered client acceptance. The dated
`current_protocol_coverage.py` formal-route source snapshot is still stale:
its policy classifications predate typed Application routes. Its hash must not
be renewed without a separate route re-audit.
