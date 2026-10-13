#include "game/SharedTaiwanOwnedItemRequestSource.h"
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
using Source=SharedTaiwanOwnedItemRequestSource;
struct Owner {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> selection;
    const std::shared_ptr<SharedWorldPresence> presence;
    Source::Action action;
    bool operating=false,reentered=false,invalidating=false,releasing=false;
    Owner(std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> reader,
        std::shared_ptr<SharedWorldPresence> common,Source::Action actual)
        :selection(std::move(reader)),presence(std::move(common)),action(std::move(actual)) {}
    ~Owner() {if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("TW C28 owned request game owner mismatch");
    }
    void invalidate() {
        owner();if(!operating)return;
        reentered=true;if(invalidating)return;
        invalidating=true;
        struct Reset {bool& flag;~Reset(){flag=false;}} reset{invalidating};
        const auto invalidate=action.invalidate_active;invalidate();
    }
    struct Operation {
        Owner& state;
        explicit Operation(Owner& actual):state(actual) {
            state.owner();
            if(state.operating || state.releasing) {state.invalidate();throw std::logic_error("TW C28 owned request reentry rejected");}
            state.operating=true;state.reentered=false;
        }
        ~Operation() {state.operating=false;}
    };
    bool ready(Session& session,const Session::NativeWorldSelectionInput& input,
        const SharedTaiwanOwnedItemSelectionSource::Selection& owned) const {
        const auto& lease=owned.lease();
        const auto local=[&] {
            return presence->retained_ready_current(lease) && !reentered && !session.closing() && session.state()==SessionState::InWorld &&
                session.id()==lease.session && session.account_id==lease.account && session.character_id==lease.character &&
                session.battle_generation()==owned.battle_generation() && session.world_selection_input_current(input) &&
                session.recovered_world_ready() && session.common_world_delivery_current(lease.account,lease.character,lease.generation) &&
                !session.common_world_entry_current(lease.account,lease.character,lease.generation);
        };
        if(!local())return false;
        const auto actual=presence->ready_lease(lease.session,lease.account,lease.character);
        const auto position=presence->saved_position(lease);
        // Presence reads call actual repository observers; requalify all local
        // state after them, even if an observer caught a rejected reentry.
        return actual && *actual==lease && position && *position==owned.saved_position() && local();
    }
    std::optional<Source::Reply> dispatch(Session& session,const Session::NativeWorldSelectionInput& input) {
        Operation operation(*this);
        try {
        // Claim before any selection/provider/rule callback. Copies of this
        // private receipt share the one actual occurrence's dispatch marker.
        if(!session.claim_world_selection_action(input) || session.state()!=SessionState::InWorld) {
            invalidate();return std::nullopt;
        }
        const auto owned=selection->select(session,input.request());
        if(!owned || !ready(session,input,*owned) || !selection->current(session,*owned) ||
           !ready(session,input,*owned)) {invalidate();return std::nullopt;}
        const auto handle=action.handle;auto reply=handle(session,input,*owned);
        // Intended CAS changes the old custody population. Do not compare it
        // to old Selection after mutation. Real action owns full next issuer /
        // durable receipts; outer mixed Current observes the advanced prefix.
        if(!ready(session,input,*owned) || !reply ||
           (reply->native_no_reply() && !reply->bytes().empty()) ||
           (!reply->native_no_reply() && reply->bytes().empty())) {invalidate();return std::nullopt;}
        return reply;
        }catch(...) {
            const auto failure=std::current_exception();
            try {invalidate();}catch(...) {}
            std::rethrow_exception(failure);
        }
    }
    void release(Session& session) {
        owner();
        if(releasing) {invalidate();throw std::logic_error("TW C28 recursive release rejected");}
        releasing=true;
        struct Reset {bool& flag;~Reset(){flag=false;}} reset{releasing};
        // Run real cleanup even when it interrupts an observing action.
        std::exception_ptr failure;
        try {invalidate();}catch(...) {failure=std::current_exception();}
        const auto release=action.release;
        try {release(session);}catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
};
}
SharedTaiwanWorldRecordSource::SelectionBinding SharedTaiwanOwnedItemRequestSource::create(
    std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> selection,
    std::shared_ptr<SharedWorldPresence> presence,Action action) {
    if(!selection || !presence || !selection->owns_presence(presence) ||
       !action.handle || !action.release || !action.invalidate_active)
        throw std::invalid_argument("TW C28 requires actual owned selection/common presence and complete action owner");
    auto owner=std::make_shared<Owner>(std::move(selection),std::move(presence),std::move(action));
    return {
        [owner](Session& session,const Session::NativeWorldSelectionInput& input){return owner->dispatch(session,input);},
        [owner](Session& session){owner->release(session);},
        [owner]{owner->invalidate();}
    };
}
}
