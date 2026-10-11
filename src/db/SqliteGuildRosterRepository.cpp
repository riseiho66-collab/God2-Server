#include "db/SqliteGuildRosterRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <limits>
#include <set>

namespace god2 {
namespace {
constexpr auto native_source="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void positive(std::uint64_t value,const char* message) {
    if(!value || value>maximum)throw DatabaseError(message);
}
class ReadSnapshot {
    sqlite3* db_;
    bool committed_=false;
public:
    explicit ReadSnapshot(sqlite3* db):db_(db) {
        if(!sqlite3_get_autocommit(db_))throw DatabaseError("Guild roster requires an independent read snapshot");
        // Deferred BEGIN establishes its snapshot on the first SELECT and does
        // not acquire the BEGIN IMMEDIATE reserved writer lock.
        sqlite_detail::execute(db_,"BEGIN");
    }
    ~ReadSnapshot() {if(!committed_)sqlite3_exec(db_,"ROLLBACK",nullptr,nullptr,nullptr);}
    void commit() {sqlite_detail::execute(db_,"COMMIT");committed_=true;}
};
std::string identity(const GuildRosterMember& member) {
    const std::string bytes(reinterpret_cast<const char*>(member.name_bytes.data()),member.name_bytes.size());
    try {
        if(member.name_codepage==0) {
            if(std::any_of(member.name_bytes.begin(),member.name_bytes.end(),[](auto byte){return byte>=0x80;}))
                throw DatabaseError("Guild member name encoding has not been established");
            if(LegacyChineseCodec::decode(bytes,false)!=bytes || LegacyChineseCodec::decode(bytes,true)!=bytes ||
               LegacyChineseCodec::encode(bytes,false)!=bytes || LegacyChineseCodec::encode(bytes,true)!=bytes)
                throw DatabaseError("Unknown-page guild ASCII identity mismatch");
            return bytes;
        }
        if(member.name_codepage!=950 && member.name_codepage!=936)
            throw DatabaseError("Invalid guild member name encoding");
        const auto unicode=LegacyChineseCodec::decode(bytes,member.name_codepage==936);
        if(unicode.empty() || unicode.find('\0')!=std::string::npos ||
           LegacyChineseCodec::encode(unicode,member.name_codepage==936)!=bytes)
            throw DatabaseError("Guild member name is not lossless");
        return unicode;
    }catch(const std::exception&) {throw DatabaseError("Invalid or unknown guild member name encoding");}
}
}

SqliteGuildRosterRepository::SqliteGuildRosterRepository(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null guild roster connection");
}
std::optional<StoredGuildRoster> SqliteGuildRosterRepository::load(std::uint64_t account,std::uint64_t character) {
    positive(account,"Invalid guild roster requester");positive(character,"Invalid guild roster requester");
    ReadSnapshot transaction(db_);
    {
        sqlite_detail::Statement owner(db_,
            "SELECT c.id,c.account_id,a.id FROM recovered_characters c "
            "LEFT JOIN accounts a ON a.id=c.account_id WHERE c.id=? AND c.account_id=?");
        owner.bind_id(1,character);owner.bind_id(2,account);
        if(!owner.row() || owner.number<std::uint64_t>(0)!=character || owner.number<std::uint64_t>(1)!=account ||
           owner.number<std::uint64_t>(2)!=account)
            throw DatabaseError("Guild roster requesting account/character owner is missing");
    }
    SqliteGuildRepository membership_reader(db_);
    const auto membership=membership_reader.load(account,character);
    if(!membership) {transaction.commit();return std::nullopt;}
    StoredGuildRoster result{account,character,*membership,{}};
    sqlite_detail::Statement query(db_,
        "SELECT m.character_id,m.guild_id,m.revision,m.origin,m.design_id,m.source_sha256,"
        "c.id,c.account_id,c.slot,c.profile,c.name_bytes,c.name_codepage,a.id,"
        "r.character_id IS NOT NULL,r.logical,r.revision,r.design_id "
        "FROM owned_guild_members m "
        "LEFT JOIN recovered_characters c ON c.id=m.character_id "
        "LEFT JOIN accounts a ON a.id=c.account_id "
        "LEFT JOIN character_role_snapshots r ON r.character_id=c.id "
        "WHERE m.guild_id=? ORDER BY m.character_id");
    query.bind_id(1,membership->guild_id);
    std::set<std::pair<std::uint64_t,std::uint8_t>> owner_slots;
    std::uint64_t previous=0;
    bool requester_found=false;
    while(query.row()) {
        GuildRosterMember member;
        member.character_id=query.number<std::uint64_t>(0);
        const auto guild=query.number<std::uint64_t>(1);
        member.membership_revision=query.number<std::uint64_t>(2);
        positive(member.character_id,"Invalid guild roster character identity");
        positive(member.membership_revision,"Invalid guild roster membership generation");
        if(guild!=membership->guild_id || member.membership_revision>membership->guild_revision ||
           query.text(3)!="CUSTOM_DESIGNED" || query.text(4)!="CUSTOM-0075" || query.text(5)!=native_source)
            throw DatabaseError("Guild roster membership/provenance mismatch");
        // Strict typed columns on LEFT JOIN NULLs reject orphan memberships;
        // never hide corrupt rows with an INNER JOIN.
        if(query.number<std::uint64_t>(6)!=member.character_id)
            throw DatabaseError("Guild roster character ownership mismatch");
        member.account_id=query.number<std::uint64_t>(7);
        positive(member.account_id,"Invalid guild roster account owner");
        if(query.number<std::uint64_t>(12)!=member.account_id)
            throw DatabaseError("Guild roster account owner is missing");
        member.slot=query.number<std::uint8_t>(8);
        if(member.slot>1 || !owner_slots.emplace(member.account_id,member.slot).second || member.character_id<=previous)
            throw DatabaseError("Invalid guild roster character slot/order");
        previous=member.character_id;
        const auto profile=query.blob(9,40,40),name=query.blob(10,1,14);
        std::copy(profile.begin(),profile.end(),member.profile.begin());
        member.name_bytes.assign(name.begin(),name.end());
        if(std::find(name.begin(),name.end(),0)!=name.end() ||
           !std::equal(name.begin(),name.end(),member.profile.begin()) || member.profile[name.size()]!=0)
            throw DatabaseError("Guild roster profile/name coherence mismatch");
        member.name_codepage=query.number<std::uint16_t>(11);
        member.name_utf8=identity(member);
        if(query.integer(13)) {
            CharacterRoleSnapshot role{};
            const auto logical=query.blob(14,25,25);
            std::copy(logical.begin(),logical.end(),role.logical.begin());
            role.revision=query.number<std::uint64_t>(15);role.design_id=query.text(16);
            const auto parsed=RecoveredRoleLevel::parse(role.logical);
            if(!parsed || !parsed->level() || !parsed->max_hp() || !role.revision || role.design_id!="CUSTOM-0013")
                throw DatabaseError("Invalid guild roster role snapshot");
            member.role=std::move(role);
        }
        if(member.character_id==character) {
            if(member.account_id!=account || member.membership_revision!=membership->membership_revision || requester_found)
                throw DatabaseError("Guild roster requesting owner changed");
            requester_found=true;
        }
        result.members.push_back(std::move(member));
    }
    if(!requester_found || result.members.empty())throw DatabaseError("Guild roster requesting member is missing");
    // Rechecks remain inside the same SQLite snapshot. Runtime publication must
    // separately re-read this full value and revalidate its live session lease.
    if(membership_reader.load(account,character)!=membership)
        throw DatabaseError("Guild roster requesting membership changed");
    transaction.commit();return result;
}
}
