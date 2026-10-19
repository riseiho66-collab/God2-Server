#pragma once
#include "game/SharedWorldHost.h"
#include "game/SharedChannelCharacterOwnership.h"
#include <array>
#include <memory>
#include <thread>

namespace god2 {
// CUSTOM-0159: the three real common-world containers and their one character
// occupation owner. Persistent repositories remain shared; visibility and
// native transports never cross worlds. Runtime gameplay owners/listeners must
// bind the chosen world separately; this collection does not install handlers.
// Construct/access/drain on the same actual game owner. Borrowed repository
// outlives every retained world/registry copy, including after collection drain.
class SharedTaiwanChannelWorlds final {
public:
    static constexpr std::uint8_t channel_count=SharedChannelCharacterOwnership::channel_count;
    explicit SharedTaiwanChannelWorlds(RecoveredCharacterRepository&);
    ~SharedTaiwanChannelWorlds();
    SharedTaiwanChannelWorlds(const SharedTaiwanChannelWorlds&)=delete;
    SharedTaiwanChannelWorlds& operator=(const SharedTaiwanChannelWorlds&)=delete;
    std::shared_ptr<SharedWorldHost> world(std::uint8_t channel) const;
    bool character_reserved(std::uint64_t character) const;
    bool owns_repository(const RecoveredCharacterRepository&) const;
private:
    void owner() const;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::shared_ptr<SharedChannelCharacterOwnership> ownership_;
    const std::array<std::shared_ptr<SharedWorldHost>,channel_count> worlds_;
};
}
