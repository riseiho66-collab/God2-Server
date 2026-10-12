#pragma once
#include "db/NativeMapCatalog.h"
#include "db/RecoveredCharacterRepository.h"
#include "net/Session.h"
#include "game/SharedTaiwanNativeCharacterListSource.h"
#include "game/SharedWorldPresence.h"
#include "game/TaiwanWorldEntryIdentity.h"
#include <cstdint>
#include <functional>
#include <optional>

namespace god2 {
// Saved common position and real full native TW entry material, qualified
// before use. This source neither constructs a candidate frame nor writes
// placement. Native reservation/scene ownership stays with the real supplier.
class SharedTaiwanWorldEntrySource {
public:
    using Entry=decltype(Session::RecoveredCharacterHandlers::world_entry);
    using Frame=RecoveredWorldEntry::Frame;
    struct Scope {
        std::uint64_t session,account,character;
        RecoveredPosition position;
        NativeMapRecord map;
        // Complete selected common root; geometry alone cannot qualify profile.
        RecoveredCharacter selected;
        SharedTaiwanNativeCharacterListSource::SelectedPtr selection;
        TaiwanWorldEntryIdentity identity{TaiwanWorldEntryIdentity::SelectedCharacter};
    };
    using Current=std::function<bool(const Scope&,const Frame&)>;
    struct Native {
        Frame frame;
        Current current;
        // Mandatory actual full frame and provenance/lifetime qualification;
        // there is no default constructor or fallback current predicate.
        Native(Frame,Current);
    };
    using NativeSource=std::function<std::optional<Native>(const Scope&)>;
    // Explicit actual issuer, before capturing stored Native material. Current
    // observes root/position/map/selected lineage; no old-entry-tuple equality
    // during the writer's staged-next BeforeCommit. Never retain arguments.
    using Prepare=std::function<bool(const Scope&,const std::function<bool()>& current)>;
    // Invoke create on the actual serial game owner. Repository/catalog and
    // their connections must outlive every Entry invocation; copied Entry
    // shares its owner/reentry guard. Providers/Current must be synchronous,
    // must not yield, pump, write, or retain Scope references/borrowed Context.
    // They own actual native material and its qualification, not guessed data.
    // Failures throw to Session's existing character-selection rejection path.
    static Entry create(RecoveredCharacterRepository&,const NativeMapCatalog&,NativeSource,
        SharedTaiwanNativeCharacterListSource::SelectedSource actual_selection={},Prepare actual_issuer={},
        std::shared_ptr<SharedWorldPresence> actual_native_presence={},
        TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter);
    // Explicit scene mode retains the genuine selected common owner separately
    // from the full native frame's qualified1..FFF handle. No ID allocation or
    // guessed frame fields; actual selected lineage/presence are mandatory.
    // Selected native entry uses the SAME common registry as its later actual
    // lifecycle preparation. Reject an already reserved character before
    // issuer writes, including prepared/stale unreleased leases. This observes
    // existing global exclusion policy; it neither reserves nor supplies native
    // per-Issued admission/replay rights. Legacy unselected entry has no guard.
    // The rechecks are pre-use only. A returned frame does not solve later
    // network queue Current atomicity, native acceptance or scene publication.
};
}
