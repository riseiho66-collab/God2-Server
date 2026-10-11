#include "RelationsSchemaDraft.h"
namespace god2 {
std::string relation53_ddl(){
#include "schema53.inc"
}
std::string relation53_migration(){
    // Entire53 schema+initial allocator installation is one migration transaction.
    // Immutable wireIDs follow durable guildID order; no read-side allocation.
    return relation53_ddl()+R"SQL(
INSERT INTO owned_guild_relation_wire_ids_0084
(guild_id,wire_id,allocated_revision,origin,design_id,source_sha256)
SELECT guild_id,ROW_NUMBER() OVER(ORDER BY guild_id),0,'CUSTOM_DESIGNED','CUSTOM-0084',
'149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
FROM owned_guild_governance_0078;
INSERT INTO owned_guild_relation_catalog_0084
(singleton,revision,next_wire_id,origin,design_id,source_sha256)
SELECT 1,0,COUNT(*)+1,'CUSTOM_DESIGNED','CUSTOM-0084',
'149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
FROM owned_guild_relation_wire_ids_0084;
)SQL";
}
}
