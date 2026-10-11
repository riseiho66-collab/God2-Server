#pragma once
#include "db/RecoveredCharacterRepository.h"
#include "protocol/RecoveredCharacterCreate.h"
#include "protocol/RecoveredCharacterListCandidate.h"
#include "protocol/RecoveredWorldEntry.h"

namespace god2 {
// Serial game-executor service. No world stats or Lua gameplay are synthesized.
class RecoveredCharacterService {
public:
    explicit RecoveredCharacterService(RecoveredCharacterRepository& characters):characters_(characters) {}
    RecoveredCharacterListCandidate::Frame list(std::uint64_t account_id,std::uint8_t route_id=0);
    std::uint64_t create(std::uint64_t account_id,const RecoveredCharacterCreate& request);
    std::uint64_t select_existing(std::uint64_t account_id,std::uint8_t token);
    std::uint64_t select_created(std::uint64_t account_id,std::uint64_t created_id,std::uint8_t token);
    std::uint8_t created_slot(std::uint64_t account_id,std::uint64_t created_id);
    RecoveredWorldEntry::Frame world_entry_candidate(std::uint64_t account_id,std::uint64_t character_id);
private:
    RecoveredCharacterRepository& characters_;
};
}
