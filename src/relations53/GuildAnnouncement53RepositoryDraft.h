#pragma once
// NEW PRIVATE CUSTOM-0083 composition. Frozen0078 announcement bytes/schema unchanged.
#include "Succession53ReaderDraft.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
namespace god2 {
class GuildAnnouncement53RepositoryDraft {
public:
    using Membership=SqliteOwnedGuildMembershipRepository;
    using Succession=Succession53ReaderDraft;
    using Value=SqliteOwnedGuildAnnouncementRepository::Value;
    using Snapshot=SqliteOwnedGuildAnnouncementRepository::Snapshot;
    GuildAnnouncement53RepositoryDraft(sqlite3*,Succession&,bool enabled=false);
    static std::string schema(); // Identical existing50 text; no implicit install.
    Snapshot load(std::uint64_t);
    Snapshot save(const Succession::EffectiveLeader&,const Snapshot&,const std::string&,const Membership::Proof&);
private:sqlite3* db_;Succession& effective_;bool enabled_;
};
}
