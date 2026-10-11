#include "cn/auth/SharedCharacterDeleteIdentity.h"
#include "cn/protocol/CnCharacterSummary.h"
#include <algorithm>
#include <set>
#include <utility>

namespace god2::cn {
SharedCharacterDeleteIdentity::SharedCharacterDeleteIdentity(
    const std::shared_ptr<Connection>& connection,RecoveredCharacterRepository& characters,
    SharedWorldAdmission::OfferSource source,std::uint64_t account,std::uint64_t session,
    std::uint64_t character,std::uint8_t slot,CurrentPhase phase)
    :connection_(connection),characters_(&characters),source_(std::move(source)),
     account_(account),world_session_(session),character_(character),native_slot_(slot),
     phase_(std::move(phase)) {}
bool SharedCharacterDeleteIdentity::owned_offer(const std::shared_ptr<Connection>& connection,
    RecoveredCharacterRepository& characters,const SharedWorldAdmission::OfferSource& source) {
    if(!connection || connection->closing() || connection->role()!=Connection::Transport::Role::World ||
       !connection->world_session_id() || !connection->verified_account_id())return false;
    const auto current=connection->world_offer_source();
    if(!current || current->adapter_record!=source.adapter_record ||
       current->character_ids!=source.character_ids)return false;
    const auto summary=god2cn::CnCharacterSummary::read(source.adapter_record);
    if(!summary || source.character_ids.size()!=summary->count())return false;
    const auto account=connection->verified_account_id();
    const auto owned=characters.list_for_account(account);
    std::set<std::uint64_t> ids;
    std::set<std::uint8_t> slots;
    for(unsigned index=0;index<summary->count();++index) {
        const auto row=summary->character(index);const auto id=source.character_ids[index];
        if(!row || !id || !ids.insert(id).second || !slots.insert(row->native_slot()).second ||
           !connection->world_character_offered(id))return false;
        if(std::count_if(owned.begin(),owned.end(),[account,id](const auto& item) {
            return item.id==id && item.account_id==account;
        })!=1)return false;
    }
    return true;
}
std::optional<SharedCharacterDeleteIdentity> SharedCharacterDeleteIdentity::resolve(
    const std::shared_ptr<Connection>& connection,RecoveredCharacterRepository& characters,
    const god2cn::CnCharacterDelete& request,CredentialEcho echo,CurrentPhase phase) {
    if(!connection || !echo || !phase || !phase() ||
       !echo(request.account(),request.credential()))return std::nullopt;
    const auto source=connection->world_offer_source();
    if(!source || !owned_offer(connection,characters,*source))return std::nullopt;
    const auto summary=god2cn::CnCharacterSummary::read(source->adapter_record);
    if(!summary)return std::nullopt;
    const auto index=summary->row_for_native_slot(request.native_slot());
    if(!index)return std::nullopt;
    const auto row=summary->character(*index);
    // Compare exact bytes of the advertised row, preserving CP936 identity.
    // The name is an echo check AFTER owned slot/row-ID resolution, never a
    // repository lookup or cross-version/TW profile/name join.
    if(!row || row->name_bytes()!=request.character_name())return std::nullopt;
    const auto account=connection->verified_account_id();
    const auto session=connection->world_session_id();
    SharedCharacterDeleteIdentity result(connection,characters,*source,account,session,
        source->character_ids[*index],request.native_slot(),std::move(phase));
    if(!result.current())return std::nullopt;
    // Credentials are neither retained in this value, sent to Lua nor logged.
    return result;
}
bool SharedCharacterDeleteIdentity::current() const {
    if(!phase_ || !phase_())return false;
    const auto connection=connection_.lock();
    if(!connection || connection->closing() || connection->verified_account_id()!=account_ ||
       connection->world_session_id()!=world_session_ ||
       !connection->world_character_offered(character_) || !owned_offer(connection,*characters_,source_))return false;
    const auto summary=god2cn::CnCharacterSummary::read(source_.adapter_record);
    if(!summary)return false;
    const auto index=summary->row_for_native_slot(native_slot_);
    return index && source_.character_ids[*index]==character_ && phase_();
}
}
