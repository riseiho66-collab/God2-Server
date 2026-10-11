#include "handlers/RecoveredCharacterService.h"
#include <stdexcept>

namespace god2 {
RecoveredCharacterListCandidate::Frame RecoveredCharacterService::list(std::uint64_t account_id,std::uint8_t route_id) {
    if(!account_id) throw std::invalid_argument("Character list requires account binding");
    return RecoveredCharacterListCandidate::wire(characters_.list_for_account(account_id),route_id);
}
std::uint64_t RecoveredCharacterService::create(std::uint64_t account_id,const RecoveredCharacterCreate& request) {
    std::array<std::uint8_t,40> profile{};
    std::copy_n(request.payload.begin(),profile.size(),profile.begin());
    if(!account_id || request.payload[40]!=4 || !RecoveredCharacterListCandidate::valid_profile(profile))
        throw std::invalid_argument("Character creation profile rejected");
    // Bytes 41..43 are unwritten client stack tail, not entity fields.
    return characters_.create(account_id,profile).id;
}
std::uint64_t RecoveredCharacterService::select_created(std::uint64_t account_id,std::uint64_t created_id,std::uint8_t token) {
    if(created_id && select_existing(account_id,token)==created_id) return created_id;
    throw std::invalid_argument("Post-create character ownership or token rejected");
}
std::uint8_t RecoveredCharacterService::created_slot(std::uint64_t account_id,std::uint64_t created_id) {
    if(account_id && created_id) {
        for(const auto& character:characters_.list_for_account(account_id))
            if(character.id==created_id && character.slot<2 &&
               RecoveredCharacterListCandidate::valid_profile(character.profile)) return character.slot;
    }
    throw std::invalid_argument("Created slot requires owned persisted character");
}
std::uint64_t RecoveredCharacterService::select_existing(std::uint64_t account_id,std::uint8_t token) {
    if(account_id) {
        for(const auto& character:characters_.list_for_account(account_id))
            if(character.slot==token &&
               RecoveredCharacterListCandidate::valid_profile(character.profile)) return character.id;
    }
    throw std::invalid_argument("Character ownership or token rejected");
}
RecoveredWorldEntry::Frame RecoveredCharacterService::world_entry_candidate(std::uint64_t account_id,std::uint64_t character_id) {
    if(account_id && character_id) {
        for(const auto& character:characters_.list_for_account(account_id))
            if(character.id==character_id && RecoveredCharacterListCandidate::valid_profile(character.profile))
                return RecoveredWorldEntry::wire(character_id,character.profile);
    }
    throw std::invalid_argument("World candidate requires owned persisted character");
}
}
