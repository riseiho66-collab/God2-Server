#pragma once
#include "game/SharedTaiwanOwnedItemSelectionSource.h"
#include "game/SharedTaiwanWorldRecordSource.h"

namespace god2 {
// Actual accepted C28 occurrence -> exact common owned full-item selection ->
// mandatory actual action. Neither flag1 nor key/slot determines equip rules.
class SharedTaiwanOwnedItemRequestSource final {
public:
    using Reply=SharedTaiwanWorldRecordSource::Reply;
    struct Action {
        // Synchronous game owner only; no retain/yield/event pump. Real action
        // must qualify ownership/definition/phase/rules/destination, perform
        // its whole-state CAS and provide the complete ordered native reply.
        // The existing joint transaction can use receipt-current at each issuer
        // stage. Receipt-current alone is not entitlement or semantic replay
        // protection: identical bytes in a later batch are a new occurrence.
        std::function<std::optional<Reply>(Session&,const Session::NativeWorldSelectionInput&,
            const SharedTaiwanOwnedItemSelectionSource::Selection&)> handle;
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
    };
    static SharedTaiwanWorldRecordSource::SelectionBinding create(
        std::shared_ptr<SharedTaiwanOwnedItemSelectionSource>,
        std::shared_ptr<SharedWorldPresence>,Action);
};
}
