#pragma once
#include "db/SqliteGuildRepository.h"
#include "db/SqliteRoleTextRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include "game/SharedWorldPresence.h"
#include <memory>
#include <optional>
#include <span>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>

namespace god2 {
class SqliteDatabase;
// CUSTOM-0135 actual same-DB secondary text for private paired TW return.
// Only SqliteDatabase assembles this owner. The borrowed DB/repositories must
// outlive it and its receipts; the exact common presence is kept alive.
// Read-only source qualification, not actor/resource/audience/publication
// authority. Missing saved text fails; a saved empty row remains distinct.
// CUSTOM-0136 retains the actual common guild membership/name in the SAME
// snapshots as secondary text. Confirmed non-membership is a value; a failed
// owner/schema/provenance read must never manufacture an empty guild field.
// Retained global guild generation also detects maintenance join/leave ABA
// while absent. Any effective CUSTOM-0075 maintenance change invalidates it.
// CUSTOM-0137 also owns current common endpoint roots/poses in that final cut,
// including both returning participants when the directed scene is empty.
class OwnedTaiwanPkReturnRoleTextSource final {
    friend class SqliteDatabase;
    struct Identity {};
public:
    using Lease=SharedWorldPresence::Lease;
    struct EndpointRequest {Lease lease;RecoveredPosition position;};
    class EndpointObservation {
    public:
        EndpointObservation(const EndpointObservation&)=default;
        EndpointObservation& operator=(const EndpointObservation&)=default;
        EndpointObservation(EndpointObservation&&)=default;
        EndpointObservation& operator=(EndpointObservation&&)=default;
    private:
        friend class OwnedTaiwanPkReturnRoleTextSource;
        EndpointObservation(const OwnedTaiwanPkReturnRoleTextSource* owner,
                std::shared_ptr<const Identity> identity,Lease lease,RecoveredCharacter root,
                RecoveredPosition position)
            :owner_(owner),identity_(std::move(identity)),lease_(std::move(lease)),
             root_(std::move(root)),position_(position){}
        const OwnedTaiwanPkReturnRoleTextSource* owner_;
        std::shared_ptr<const Identity> identity_;
        Lease lease_;
        RecoveredCharacter root_;
        RecoveredPosition position_;
    };
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&&)=default;
        Observation& operator=(Observation&&)=default;
        const StoredRoleText& row()const noexcept{return row_;}
        const std::optional<StoredGuildMembership>& guild()const noexcept{return guild_;}
        bool operator==(const Observation&)const=default;
    private:
        friend class OwnedTaiwanPkReturnRoleTextSource;
        Observation(const OwnedTaiwanPkReturnRoleTextSource* owner,std::shared_ptr<const Identity> identity,
                Lease source,StoredRoleText row,std::optional<StoredGuildMembership> guild,
                std::uint64_t guild_epoch)
            :owner_(owner),identity_(std::move(identity)),source_(std::move(source)),
             row_(std::move(row)),guild_(std::move(guild)),guild_epoch_(guild_epoch){}
        const OwnedTaiwanPkReturnRoleTextSource* owner_;
        std::shared_ptr<const Identity> identity_; // Retained identity prevents owner-address reuse.
        Lease source_;
        StoredRoleText row_;
        std::optional<StoredGuildMembership> guild_;
        std::uint64_t guild_epoch_;
    };
    OwnedTaiwanPkReturnRoleTextSource(const OwnedTaiwanPkReturnRoleTextSource&)=delete;
    OwnedTaiwanPkReturnRoleTextSource& operator=(const OwnedTaiwanPkReturnRoleTextSource&)=delete;

    // Pure owner identity check: no SQL/presence/native observers. Any caught
    // recursive entry permanently invalidates this owner, including this check.
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>& value)const{
        owner();
        if(reading_){poisoned_=true;return false;}
        return !poisoned_&&value&&value==presence_;
    }
    std::optional<Observation> observe(const Lease& original)const{
        owner();
        try{
            Operation operation(*this);
            const auto source=original; // No caller alias survives an observer.
            const auto changes=sqlite3_total_changes64(db_);
            const auto row=qualified_row(source,changes);
            if(!row||!unchanged(changes))return {};
            return Observation(this,identity_,source,row->text,row->guild,row->guild_epoch);
        }catch(const std::exception&){return {};}
    }
    bool current(const Observation& original)const{
        owner();
        try{
            Operation operation(*this);
            const auto observation=original;
            if(observation.owner_!=this||observation.identity_!=identity_||!valid_lease(observation.source_))return false;
            const auto changes=sqlite3_total_changes64(db_);
            const auto row=qualified_row(observation.source_,changes);
            return row&&row->text==observation.row_&&row->guild==observation.guild_&&
                row->guild_epoch==observation.guild_epoch_&&unchanged(changes);
        }catch(const std::exception&){return false;}
    }
    // Actual concrete root/pose reads; expected pose is the current plan pose,
    // never the immutable entry Lease.position. No native/fullactor projection.
    std::optional<std::vector<EndpointObservation>> observe_endpoints(
            std::span<const EndpointRequest> supplied)const{
        owner();
        try{
            Operation operation(*this);
            const std::vector<EndpointRequest> requests(supplied.begin(),supplied.end());
            if(!owns_database()||!sqlite3_get_autocommit(db_))return {};
            const auto changes=sqlite3_total_changes64(db_);
            for(const auto& request:requests)
                if(!valid_lease(request.lease)||!presence_->ready(request.lease)||!unchanged(changes))return {};
            std::vector<EndpointObservation> observations;observations.reserve(requests.size());
            {
                ReadScope scope(db_);namespaces();
                for(const auto& request:requests){
                    auto root=read_root(request.lease);
                    const auto position=characters_.load_position(request.lease.account,request.lease.character);
                    if(!root||position!=std::optional{request.position}||!unchanged(changes))return {};
                    observations.push_back(EndpointObservation(this,identity_,request.lease,std::move(*root),*position));
                }
                namespaces();if(!unchanged(changes))return {};scope.finish();
            }
            // Presence callbacks are outside SQL. Re-read the whole saved set
            // AFTER them, then only pure retained registry checks follow.
            for(const auto& observation:observations)
                if(!presence_->ready(observation.lease_)||!unchanged(changes))return {};
            {
                ReadScope scope(db_);namespaces();
                for(const auto& observation:observations)
                    if(!endpoint_current(observation)||!unchanged(changes))return {};
                namespaces();if(!unchanged(changes))return {};scope.finish();
            }
            for(const auto& observation:observations)
                if(!presence_->retained_ready_current(observation.lease_)||!unchanged(changes))return {};
            return unchanged(changes)&&sqlite3_get_autocommit(db_)?
                std::optional{std::move(observations)}:std::nullopt;
        }catch(const std::exception&){return {};}
    }
    // Final ALL-row snapshot after the complete scene/other source observers.
    // Text, membership/name and all complete common roots/poses share this cut.
    // No presence/native/external observers or row refresh. Empty scenes still
    // qualify both retained participants; absence is never a
    // manufactured empty title. Caller's pure registry/Session fence follows.
    bool stored_current(std::span<const Observation> supplied,
            std::span<const EndpointObservation> supplied_endpoints)const{
        owner();
        try{
            Operation operation(*this);
            const std::vector<Observation> observations(supplied.begin(),supplied.end());
            const std::vector<EndpointObservation> endpoints(supplied_endpoints.begin(),supplied_endpoints.end());
            if(!owns_database()||!sqlite3_get_autocommit(db_))return false;
            for(const auto& observation:observations)
                if(observation.owner_!=this||observation.identity_!=identity_||!valid_lease(observation.source_))return false;
            for(const auto& endpoint:endpoints)
                if(endpoint.owner_!=this||endpoint.identity_!=identity_||!valid_lease(endpoint.lease_))return false;
            const auto changes=sqlite3_total_changes64(db_);
            {
                ReadScope scope(db_);
                namespaces();
                const auto epoch=guild_epoch();
                for(const auto& observation:observations){
                    if(epoch!=observation.guild_epoch_)return false;
                    const auto row=texts_.load(observation.source_.account,observation.source_.character);
                    if(!row||*row!=observation.row_||!unchanged(changes))return false;
                    const auto guild=guilds_.load(observation.source_.account,observation.source_.character);
                    if(guild!=observation.guild_||!unchanged(changes))return false;
                }
                for(const auto& endpoint:endpoints)
                    if(!endpoint_current(endpoint)||!unchanged(changes))return false;
                namespaces();
                if(!unchanged(changes))return false;
                scope.finish();
            }
            return unchanged(changes)&&sqlite3_get_autocommit(db_);
        }catch(const std::exception&){return false;}
    }
private:
    sqlite3* const db_;
    SqliteRoleTextRepository& texts_;
    SqliteGuildRepository& guilds_;
    SqliteRecoveredCharacterRepository& characters_;
    const std::shared_ptr<SharedWorldPresence> presence_;
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    const std::thread::id thread_=std::this_thread::get_id();
    mutable bool reading_=false,poisoned_=false;

    OwnedTaiwanPkReturnRoleTextSource(sqlite3* db,SqliteRoleTextRepository& texts,SqliteGuildRepository& guilds,
            SqliteRecoveredCharacterRepository& characters,std::shared_ptr<SharedWorldPresence> presence)
        :db_(db),texts_(texts),guilds_(guilds),characters_(characters),presence_(std::move(presence)){
        if(!db_||!texts_.uses_connection(db_)||!guilds_.uses_connection(db_)||
           !characters_.uses_connection(db_)||!presence_||!presence_->owns_repository(characters_))
            throw DatabaseError("TW return role text requires actual same-DB sources");
    }
    void owner()const{
        if(thread_!=std::this_thread::get_id())
            throw std::logic_error("TW return role text game owner mismatch");
    }
    struct Operation {
        const OwnedTaiwanPkReturnRoleTextSource& source;
        explicit Operation(const OwnedTaiwanPkReturnRoleTextSource& value):source(value){
            if(source.reading_){source.poisoned_=true;
                throw std::logic_error("TW return role text source reentry");}
            if(source.poisoned_)throw DatabaseError("TW return role text source is poisoned");
            source.reading_=true;
        }
        ~Operation(){source.reading_=false;}
    };
    struct ReadScope {
        sqlite3* db;bool finished=false;
        explicit ReadScope(sqlite3* value):db(value){
            if(!sqlite3_get_autocommit(db))throw DatabaseError("TW return role text needs its own read scope");
            sqlite_detail::execute(db,"BEGIN");
        }
        ~ReadScope(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
        void finish(){sqlite_detail::execute(db,"COMMIT");finished=true;}
    };
    bool owns_database()const{
        return db_&&texts_.uses_connection(db_)&&guilds_.uses_connection(db_)&&
            characters_.uses_connection(db_)&&presence_&&presence_->owns_repository(characters_)&&!poisoned_;
    }
    bool unchanged(sqlite3_int64 changes)const{
        return owns_database()&&sqlite3_total_changes64(db_)==changes;
    }
    static bool valid_lease(const Lease& source)noexcept{
        return source.session&&source.account&&source.character&&source.generation&&source.actor_handle<=0xfff;
    }
    void namespaces()const{
        // Existing concrete repository uses unqualified table names. It may
        // read only actual main tables, never a TEMP shadow or substituted view.
        sqlite_detail::Statement shadows(db_,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('character_role_text','recovered_characters','owned_guilds','owned_guild_members','accounts','recovered_positions') OR tbl_name COLLATE NOCASE IN ('character_role_text','recovered_characters','owned_guilds','owned_guild_members','accounts','recovered_positions')");
        if(shadows.row())throw DatabaseError("TW return role text TEMP shadow rejected");
        sqlite_detail::Statement tables(db_,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('character_role_text','recovered_characters','owned_guilds','owned_guild_members','accounts','recovered_positions')");
        if(!tables.row()||tables.integer(0)!=6||tables.row())
            throw DatabaseError("TW return role text requires actual main tables");
    }
    static bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b)noexcept{
        return a.id==b.id&&a.account_id==b.account_id&&a.slot==b.slot&&a.profile==b.profile&&
            a.created_at==b.created_at&&a.name_codepage==b.name_codepage&&a.streamer_privilege==b.streamer_privilege;
    }
    std::optional<RecoveredCharacter> read_root(const Lease& lease)const{
        std::optional<RecoveredCharacter> result;
        for(const auto& root:characters_.list_for_account(lease.account))if(root.id==lease.character){
            if(result||root.account_id!=lease.account)return {};
            result=root;
        }
        return result;
    }
    bool endpoint_current(const EndpointObservation& endpoint)const{
        if(endpoint.owner_!=this||endpoint.identity_!=identity_||!valid_lease(endpoint.lease_))return false;
        const auto root=read_root(endpoint.lease_);
        return root&&same_root(*root,endpoint.root_)&&
            characters_.load_position(endpoint.lease_.account,endpoint.lease_.character)==std::optional{endpoint.position_};
    }
    struct StoredRows {
        StoredRoleText text;
        std::optional<StoredGuildMembership> guild;
        std::uint64_t guild_epoch;
        bool operator==(const StoredRows&)const=default;
    };
    std::uint64_t guild_epoch()const{
        // CUSTOM-0075 retains guild rows and advances the global maximum for
        // every effective admin creation/assignment/removal. Query actual main
        // rather than accepting an absent membership as a reusable generation.
        sqlite_detail::Statement clock(db_,"SELECT COALESCE(MAX(revision),0) FROM main.owned_guilds");
        if(!clock.row())throw DatabaseError("TW return guild generation missing");
        const auto epoch=clock.number<std::uint64_t>(0);
        if(clock.row())throw DatabaseError("TW return guild generation ambiguous");
        return epoch;
    }
    std::optional<StoredRows> read_row(const Lease& source,sqlite3_int64 changes)const{
        if(!owns_database()||!sqlite3_get_autocommit(db_)||!unchanged(changes))return {};
        std::optional<StoredRows> row;
        {
            ReadScope scope(db_);
            namespaces();
            const auto text=texts_.load(source.account,source.character);
            if(!text||!unchanged(changes))return {};
            const auto guild=guilds_.load(source.account,source.character);
            row=StoredRows{*text,guild,guild_epoch()};
            namespaces();
            if(!row||!unchanged(changes))return {};
            scope.finish();
        }
        return unchanged(changes)&&sqlite3_get_autocommit(db_)?row:std::nullopt;
    }
    std::optional<StoredRows> qualified_row(const Lease& source,sqlite3_int64 changes)const{
        if(!valid_lease(source)||!owns_database()||!sqlite3_get_autocommit(db_)||
           !presence_->ready(source)||!unchanged(changes))return {};
        const auto before=read_row(source,changes);
        if(!before||!presence_->ready(source)||!unchanged(changes))return {};
        // The final presence observer can access the actual character source.
        // Re-read both complete rows AFTER it, then only pure retained registry.
        const auto after=read_row(source,changes);
        if(!after||*after!=*before||!presence_->retained_ready_current(source)||!unchanged(changes))return {};
        return after;
    }
};
}
