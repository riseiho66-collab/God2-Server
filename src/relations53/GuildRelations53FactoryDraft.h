#pragma once
// PRIVATE CUSTOM-0084. One connection, one original creation-history reader,
// strict53 effective owner and strict53 write ports. No receiver permission.
#include "GuildAnnouncement53RepositoryDraft.h"
#include "NeighboringGuild53AdmissionRepositoryDraft.h"
#include "RelationsRepositoryDraft.h"
#include "RelationsSchemaDraft.h"
#include "db/GuildSuccessionSqliteMigrationsDraft.h"
#include "db/SqliteSupport.h"
namespace god2 {
struct GuildRelations53FlagsDraft {
    bool membership{},announcements{},officers{},succession{},relations{};
    bool operator==(const GuildRelations53FlagsDraft&)const=default;
    void qualify()const {
        if((officers&&(!membership||!announcements)) ||
           (succession&&(!membership||!announcements||!officers)) ||
           (relations&&(!membership||!announcements||!officers||!succession)))
            throw DatabaseError("PRIVATE CUSTOM84 invalid prerequisite flags");
    }
};
class GuildRelations53FactoryDraft final {
public:
    using Original=SqliteOwnedGuildMembershipRepository;
    GuildRelations53FactoryDraft(sqlite3* db,GuildRelations53FlagsDraft flags={})
      :db_(db),flags_(flags),original_(db),reader_(db,original_),
       relations_(db,original_,flags.relations),neighbors_(db,original_,reader_,flags.relations,&relations_),
       announcements_(db,reader_,flags.relations),notices_(db) {
        if(!db_)throw DatabaseError("PRIVATE CUSTOM84 null factory connection");
        flags_.qualify();reader_.require_exact_schema53();
    }
    GuildRelations53FactoryDraft(const GuildRelations53FactoryDraft&)=delete;
    GuildRelations53FactoryDraft& operator=(const GuildRelations53FactoryDraft&)=delete;
    Original& original(){exact();return original_;}
    Succession53ReaderDraft& owner(){exact();return reader_;}
    RelationsRepositoryDraft& relations(){exact();return relations_;}
    NeighboringGuild53AdmissionRepositoryDraft& neighbors(){exact();return neighbors_;}
    GuildAnnouncement53RepositoryDraft& announcements(){exact();return announcements_;}
    SqliteOwnedGuildAnnouncementRepository& notice_reader(){exact();return notices_;}
    const GuildRelations53FlagsDraft& flags()const{return flags_;}
    void require_flags(GuildRelations53FlagsDraft expected)const {
        expected.qualify();if(expected!=flags_)throw DatabaseError("PRIVATE CUSTOM84 flags immutable during database lifetime");
    }
    static std::vector<Migration> migrations(){
        auto result=owned_guild_succession_migrations_draft();
        result.push_back({53,"owned_guild_relations_private",relation53_migration()});return result;
    }
    // Explicitly called only after unchanged qualified52 base migration. Never
    // use generic migration53 INSERT; this owns wholetyped pre-COMMIT guards.
    static void append53(sqlite3* db,GuildRelations53FlagsDraft flags){
        flags.qualify();if(!flags.relations)throw DatabaseError("PRIVATE CUSTOM84 append disabled");
        RelationsRepositoryDraft::migrate53_private(db);
    }
private:
    void exact(){reader_.require_exact_schema53();}
    sqlite3* db_;const GuildRelations53FlagsDraft flags_;Original original_;
    Succession53ReaderDraft reader_;RelationsRepositoryDraft relations_;
    NeighboringGuild53AdmissionRepositoryDraft neighbors_;GuildAnnouncement53RepositoryDraft announcements_;
    SqliteOwnedGuildAnnouncementRepository notices_;
};
}
