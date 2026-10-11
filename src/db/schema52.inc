return R"SQL(-- CUSTOM DESIGN PROPOSAL ONLY. NO DATABASE CREATED OR MIGRATED.
-- Exact immutable migrations1..51 must precede this separately reviewed52.
-- No character/governance FK: past owners may leave/be deleted; native75 retains
-- gid and historical audits while removing governance. Audit is never authority
-- without a live original-creation row and an exact live current-owner join.
CREATE TABLE owned_guild_successions_0083(
 guild_id INTEGER NOT NULL CHECK(typeof(guild_id)='integer' AND guild_id>0) REFERENCES owned_guilds(id),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 previous_ownership_revision INTEGER NOT NULL CHECK(typeof(previous_ownership_revision)='integer' AND previous_ownership_revision>=0),
 guild_revision_before INTEGER NOT NULL CHECK(typeof(guild_revision_before)='integer' AND guild_revision_before>0 AND guild_revision_before<revision),
 from_account INTEGER NOT NULL CHECK(typeof(from_account)='integer' AND from_account>0),
 from_character INTEGER NOT NULL CHECK(typeof(from_character)='integer' AND from_character>0),
 from_slot INTEGER NOT NULL CHECK(typeof(from_slot)='integer' AND from_slot BETWEEN 0 AND 1),
 from_join_revision INTEGER NOT NULL CHECK(typeof(from_join_revision)='integer' AND from_join_revision>0),
 to_account INTEGER NOT NULL CHECK(typeof(to_account)='integer' AND to_account>0),
 to_character INTEGER NOT NULL CHECK(typeof(to_character)='integer' AND to_character>0 AND to_character<>from_character),
 to_slot INTEGER NOT NULL CHECK(typeof(to_slot)='integer' AND to_slot BETWEEN 0 AND 1),
 to_join_revision INTEGER NOT NULL CHECK(typeof(to_join_revision)='integer' AND to_join_revision>0 AND to_join_revision<=guild_revision_before),
 target_previous_role INTEGER NOT NULL CHECK(typeof(target_previous_role)='integer' AND target_previous_role IN(1,2)),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0083'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'),
 PRIMARY KEY(guild_id,revision)
) WITHOUT ROWID;
-- Original target eligibility, consent, cooldown, fee, old-owner office and
-- succession limits are NOT recovered. These columns encode a reviewed role1/2
-- proposal, not historical game-server data.
)SQL";
