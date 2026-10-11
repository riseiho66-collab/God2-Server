#pragma once
// NEW PRIVATE CUSTOM-0083 composition. Frozen0078 announcement bytes/schema unchanged.
#include "db/GuildSuccessionSqliteMigrationsDraft.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
namespace god2 {
class EffectiveGuildAnnouncementRepositoryDraft {
public:
    using Membership=SqliteOwnedGuildMembershipRepository;
    using Succession=SqliteOwnedGuildSuccessionRepositoryDraft;
    using Value=SqliteOwnedGuildAnnouncementRepository::Value;
    using Snapshot=SqliteOwnedGuildAnnouncementRepository::Snapshot;
    EffectiveGuildAnnouncementRepositoryDraft(sqlite3*,Succession&);
    static std::string schema(); // Identical existing50 text; no implicit install.
    Snapshot load(std::uint64_t);
    Snapshot save(const Succession::EffectiveLeader&,const Snapshot&,const std::string&,const Membership::Proof&);
private:sqlite3* db_;Succession& effective_;
};
}
