#include "db/SqliteCompanionRepository.h"
#include "db/SqliteSupport.h"

namespace god2 {
Pet2TransferCommit SqliteCompanionRepository::move_pet_reserves(std::uint64_t account,
        std::uint64_t character,const StoredPet2Slot& supplied_source,const StoredPet2Slot& supplied_destination,
        const std::function<void(const Pet2TransferCommit&)>& supplied_prepare,std::function<bool()> current) {
    // Own every caller value before shared transaction observers can run.
    const auto source=supplied_source,destination=supplied_destination;
    auto prepare=supplied_prepare;
    const auto reserve=[](std::uint8_t slot){return slot==42||slot==43;};
    if(!reserve(source.slot)||!reserve(destination.slot)||source.slot==destination.slot||!prepare)
        throw DatabaseError("Invalid pet reserve move");
    // CUSTOM-0039: same full-instance custody swap, not a native growth rule.
    // Activation and reserve reorder share the actual sqlite connection guard,
    // complete CAS, claims, source fences and post-COMMIT durable truth.
    return swap_pet_cells(account,character,source,destination,std::move(prepare),std::move(current));
}
}
