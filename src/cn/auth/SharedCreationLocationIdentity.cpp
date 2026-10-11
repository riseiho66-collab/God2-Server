#include "cn/auth/SharedCreationLocationIdentity.h"
#include <algorithm>
#include <set>
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedCreationLocationIdentity::SharedCreationLocationIdentity(
    const std::shared_ptr<Connection>& connection,RecoveredCharacterRepository& characters,
    std::shared_ptr<const Request> request,RecoveredCharacter created,
    std::vector<std::uint8_t> choices,CurrentPendingCreate pending,Projection projection)
    :connection_(connection),characters_(&characters),request_(std::move(request)),
     created_snapshot_(std::move(created)),permitted_choices_(std::move(choices)),
     pending_(std::move(pending)),projection_(projection),
     account_(connection->verified_account_id()),character_(created_snapshot_.id),
     world_session_(connection->world_session_id()) {}
void SharedCreationLocationIdentity::owner() const {
    if(thread_!=std::this_thread::get_id())
        throw std::logic_error("CN creation-location game owner mismatch");
}
std::optional<SharedCreationLocationIdentity> SharedCreationLocationIdentity::resolve(
    const std::shared_ptr<Connection>& connection,RecoveredCharacterRepository& characters,
    std::shared_ptr<const Request> request,std::uint64_t created_id,
    std::span<const std::uint8_t> choices,CurrentPendingCreate pending,
    std::span<const std::uint8_t> bytes) {
    const auto choice=god2cn::CnCharacterLocationChoice::read_request(bytes);
    if(!choice || !connection || connection->closing() ||
       connection->role()!=Connection::Transport::Role::World || !request || !created_id ||
       !connection->verified_account_id() || !connection->world_session_id() ||
       !connection->world_admission_current() || !pending || choices.empty())return std::nullopt;
    std::set<std::uint8_t> unique;
    for(const auto value:choices)
        if(!god2cn::CnCreationLocationProjection::from_choice(value) ||
           !unique.insert(value).second)return std::nullopt;
    if(!unique.contains(choice->raw_choice_byte) || !pending(request,created_id,choices))return std::nullopt;
    const auto projection=god2cn::CnCreationLocationProjection::from_choice(choice->raw_choice_byte);
    if(!projection)return std::nullopt;
    const auto account=connection->verified_account_id();
    const auto owned=characters.list_for_account(account);
    const auto match=[account,created_id](const auto& row) {
        return row.id==created_id && row.account_id==account;
    };
    if(std::count_if(owned.begin(),owned.end(),match)!=1)return std::nullopt;
    // IDs come from the actual completed creation transaction. No18 byte,
    // cached07 row ordinal, name, routing key or TW profile identifies a role.
    const auto created=std::find_if(owned.begin(),owned.end(),match);
    SharedCreationLocationIdentity result(connection,characters,std::move(request),*created,
        {choices.begin(),choices.end()},std::move(pending),*projection);
    if(!result.current())return std::nullopt;
    return result;
}
bool SharedCreationLocationIdentity::current() const {
    owner();
    const auto connection=connection_.lock();
    if(!connection || connection->closing() ||
       connection->role()!=Connection::Transport::Role::World ||
       connection->verified_account_id()!=account_ || connection->world_session_id()!=world_session_ ||
       !connection->world_admission_current() || !request_ || !pending_ ||
       !pending_(request_,character_,permitted_choices_))return false;
    const auto owned=characters_->list_for_account(account_);
    unsigned matches=0;
    for(const auto& row:owned)if(row.id==character_ && row.account_id==account_) {
        ++matches;
        // Compare raw common snapshot without interpreting TW profile fields
        // as CN data. Actual transaction must protect these fields itself.
        if(row.slot!=created_snapshot_.slot || row.profile!=created_snapshot_.profile ||
           row.created_at!=created_snapshot_.created_at || row.name_codepage!=created_snapshot_.name_codepage ||
           row.streamer_privilege!=created_snapshot_.streamer_privilege)return false;
    }
    return matches==1 && pending_(request_,character_,permitted_choices_);
}
}
