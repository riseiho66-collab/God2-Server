# Fresh town guide reward and restart (2026-09-23)

The isolated CUSTOM-0021/0022 town guide previously required a saved empty
inventory slot0 before the final item grant. That is a deliberate distinction:
an absent slot is not accepted as an empty slot by the reward transaction.
Fresh characters had no slot row and therefore could begin the guide but could
not finish it without external database preparation.

CUSTOM-0031 adds `provision_town_reward_slot` during authenticated world-ready
binding **only when** the default-off diagnostic town quest mode is enabled.
The repository verifies character ownership and the guide state, refuses a
pending battle, and creates exactly one empty slot0 with the pinned native map
source hash and revision1 in a SQLite transaction. It grants no item, resources
or progress. Re-entry is idempotent; an existing occupied slot is preserved,
an empty slot with conflicting provenance is rejected, and a completed guide
with a missing slot is rejected as corrupt. CUSTOM-0022 still requires the
explicit owned empty row and atomically updates stage, inventory and receipt.
The original-client empty initial inventory is consistent with this policy,
but this server-side provisioning rule is custom, not recovered official
character-creation behavior.

The fresh-character two-connection socket regression imports the pinned
original map and 2,014-row quest display catalogs into an isolated database.
From town110,70 with no position row, the current-format world tick supplies
both guide NPCs. Three C2S37/C2S85 pairs select1606,1607,1606; S2C7A returns
text keys894,899,896 and S2CDB returns journal values0x10001,0x20001,0.
The terminal response also projects S2C41 item5569/count1 into slot0. SQLite
has stage3/revision3, slot revision2, one reward receipt, and still no
position row. After a fresh server restart, one world tick restores the two
NPCs, completed journal and item. Replaying the old confirmation closes that
connection without changing any of those tables; SQLite quick_check is OK.

The repository regression injects a failure during empty-slot insertion and
confirms no row or progress mutation remains. It also checks foreign-owner
rejection, idempotence, no overwrite after reward, existing atomic grant
failure rollback and replay refusal. The existing native original-client
town quest captures qualify the saved-character workflow. This new fresh
character path is verified with reconstructed original-format sockets, not
physical input or rendered UI, and remains an isolated custom game policy.
