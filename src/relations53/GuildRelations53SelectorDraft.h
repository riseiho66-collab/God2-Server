#pragma once
#include "GuildRelations53FactoryDraft.h"
#include <filesystem>
namespace god2 {
inline std::vector<Migration> configured_guild_relations53(const std::filesystem::path& path,GuildRelations53FlagsDraft flags){
    flags.qualify();
    if(std::filesystem::exists(path)){
        const auto text=path.u8string();sqlite3* raw=nullptr;
        const int rc=sqlite3_open_v2(reinterpret_cast<const char*>(text.c_str()),&raw,SQLITE_OPEN_READONLY|SQLITE_OPEN_FULLMUTEX,nullptr);
        std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> connection(raw,sqlite3_close_v2);
        if(rc!=SQLITE_OK)throw DatabaseError("PRIVATE CUSTOM84 cannot inspect database");
        sqlite_detail::execute(raw,"PRAGMA query_only=ON;BEGIN");int installed=0;
        {sqlite_detail::Statement q(raw,"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations'");if(q.row()&&q.integer(0)){sqlite_detail::Statement h(raw,"SELECT max(version) FROM schema_migrations");if(h.row())installed=static_cast<int>(h.integer(0));}}
        if(installed>=53){GuildRelations53FactoryDraft exact(raw,flags);return GuildRelations53FactoryDraft::migrations();}
    }
    auto base=configured_guild_succession_migrations_draft(path,{flags.membership,flags.announcements,flags.officers,flags.succession});
    if(flags.relations){if(base.size()!=52)throw DatabaseError("PRIVATE CUSTOM84 requires qualified52 base");return GuildRelations53FactoryDraft::migrations();}
    return base;
}
}
