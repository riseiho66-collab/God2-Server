return R"REL84(-- PRIVATE CUSTOM-0084 DRAFT ONLY. NOT REGISTERED OR RUN BY ANY FACTORY.
-- Future exact migrations1..52 precede separately qualified53; preserve all old bytes.
CREATE TABLE owned_guild_relation_catalog_0084(
 singleton INTEGER PRIMARY KEY CHECK(typeof(singleton)='integer' AND singleton=1),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>=0),
 next_wire_id INTEGER NOT NULL CHECK(typeof(next_wire_id)='integer' AND next_wire_id BETWEEN 1 AND 4294967296),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0084'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
);
CREATE TABLE owned_guild_relation_wire_ids_0084(
 guild_id INTEGER PRIMARY KEY CHECK(typeof(guild_id)='integer' AND guild_id>0) REFERENCES owned_guilds(id),
 wire_id INTEGER NOT NULL UNIQUE CHECK(typeof(wire_id)='integer' AND wire_id BETWEEN 1 AND 4294967295),
 allocated_revision INTEGER NOT NULL CHECK(typeof(allocated_revision)='integer' AND allocated_revision>=0),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0084'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
);
CREATE TABLE owned_guild_relations_0084(
 guild_low INTEGER NOT NULL CHECK(typeof(guild_low)='integer' AND guild_low>0) REFERENCES owned_guild_relation_wire_ids_0084(guild_id),
 guild_high INTEGER NOT NULL CHECK(typeof(guild_high)='integer' AND guild_high>guild_low) REFERENCES owned_guild_relation_wire_ids_0084(guild_id),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 state INTEGER NOT NULL CHECK(typeof(state)='integer' AND state IN(0,1,2)),
 inviter_guild INTEGER CHECK(inviter_guild IS NULL OR (typeof(inviter_guild)='integer' AND inviter_guild IN(guild_low,guild_high))),
 low_owner_account INTEGER NOT NULL CHECK(typeof(low_owner_account)='integer' AND low_owner_account>0),
 low_owner_character INTEGER NOT NULL CHECK(typeof(low_owner_character)='integer' AND low_owner_character>0),
 low_ownership_revision INTEGER NOT NULL CHECK(typeof(low_ownership_revision)='integer' AND low_ownership_revision>=0),
 high_owner_account INTEGER NOT NULL CHECK(typeof(high_owner_account)='integer' AND high_owner_account>0),
 high_owner_character INTEGER NOT NULL CHECK(typeof(high_owner_character)='integer' AND high_owner_character>0),
 high_ownership_revision INTEGER NOT NULL CHECK(typeof(high_ownership_revision)='integer' AND high_ownership_revision>=0),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0084'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'),
 CHECK((state=1 AND inviter_guild IS NOT NULL) OR (state IN(0,2) AND inviter_guild IS NULL)),
 PRIMARY KEY(guild_low,guild_high)
) WITHOUT ROWID;
CREATE TABLE owned_guild_relation_events_0084(
 revision INTEGER PRIMARY KEY CHECK(typeof(revision)='integer' AND revision>0),
 guild_low INTEGER NOT NULL CHECK(typeof(guild_low)='integer' AND guild_low>0),
 guild_high INTEGER NOT NULL CHECK(typeof(guild_high)='integer' AND guild_high>guild_low),
 previous_pair_revision INTEGER NOT NULL CHECK(typeof(previous_pair_revision)='integer' AND previous_pair_revision>=0 AND previous_pair_revision<revision),
 before_state INTEGER NOT NULL CHECK(typeof(before_state)='integer' AND before_state IN(0,1,2)),
 after_state INTEGER NOT NULL CHECK(typeof(after_state)='integer' AND after_state IN(0,1,2)),
 action TEXT NOT NULL CHECK(action IN('propose','accept','withdraw','decline','remove','transfer_retire','disband_retire')),
 actor_guild INTEGER NOT NULL CHECK(typeof(actor_guild)='integer' AND actor_guild IN(guild_low,guild_high)),
 actor_account INTEGER NOT NULL CHECK(typeof(actor_account)='integer' AND actor_account>0),
 actor_character INTEGER NOT NULL CHECK(typeof(actor_character)='integer' AND actor_character>0),
 actor_slot INTEGER NOT NULL CHECK(typeof(actor_slot)='integer' AND actor_slot BETWEEN 0 AND 1),
 actor_session INTEGER NOT NULL CHECK(typeof(actor_session)='integer' AND actor_session>0),
 actor_world_generation INTEGER NOT NULL CHECK(typeof(actor_world_generation)='integer' AND actor_world_generation>0),
 actor_position_revision INTEGER NOT NULL CHECK(typeof(actor_position_revision)='integer' AND actor_position_revision>0),
 actor_battle_generation INTEGER NOT NULL CHECK(typeof(actor_battle_generation)='integer' AND actor_battle_generation>=0),
 actor_codepage INTEGER NOT NULL CHECK(typeof(actor_codepage)='integer' AND actor_codepage IN(950,936)),
 low_guild_revision INTEGER NOT NULL CHECK(typeof(low_guild_revision)='integer' AND low_guild_revision>0),
 low_ownership_revision INTEGER NOT NULL CHECK(typeof(low_ownership_revision)='integer' AND low_ownership_revision>=0),
 high_guild_revision INTEGER NOT NULL CHECK(typeof(high_guild_revision)='integer' AND high_guild_revision>0),
 high_ownership_revision INTEGER NOT NULL CHECK(typeof(high_ownership_revision)='integer' AND high_ownership_revision>=0),
 request_subtype INTEGER CHECK(request_subtype IS NULL OR (typeof(request_subtype)='integer' AND request_subtype IN(1,8))),
 request_name16 BLOB CHECK(request_name16 IS NULL OR (typeof(request_name16)='blob' AND length(request_name16)=16)),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0084'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'),
 FOREIGN KEY(guild_low,guild_high) REFERENCES owned_guild_relations_0084(guild_low,guild_high),
 CHECK((action='propose' AND before_state=0 AND after_state=1)
    OR (action='accept' AND before_state=1 AND after_state=2)
    OR (action IN('withdraw','decline','transfer_retire') AND before_state=1 AND after_state=0)
    OR (action='remove' AND before_state=2 AND after_state=0)
    OR (action='disband_retire' AND before_state IN(1,2) AND after_state=0)),
 CHECK(action IN('transfer_retire','disband_retire')
    OR (action IN('propose','accept') AND request_subtype=1)
    OR (action IN('withdraw','decline','remove') AND request_subtype=8)),
 CHECK((action IN('transfer_retire','disband_retire') AND request_subtype IS NULL AND request_name16 IS NULL)
    OR (action NOT IN('transfer_retire','disband_retire') AND request_subtype IS NOT NULL AND request_name16 IS NOT NULL))
);
-- No character/governance FK: audit identities survive former-founder deletion.
-- Read APIs must require live governance+effective52 owner; audit is never permission.
-- No INSERT, migration runner, live database or automatic53 activation is supplied.
)REL84";
