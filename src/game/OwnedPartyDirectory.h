#pragma once
#include "db/RecoveredCharacterRepository.h"
#include "game/NativeParty.h"
#include "net/Session.h"
#include "protocol/TaiwanNativePartyMenu.h"
#include <cstddef>
#include <map>
#include <memory>
#include <vector>
#include <utility>
namespace god2 {
// CUSTOM-0097 transient discovery only. No membership, invitation or AB rights.
class OwnedPartyDirectory final {
public:
    struct Actor {
        std::weak_ptr<Session> session;
        std::uint64_t session_id,account,character,battle;
        SessionState phase;
        RecoveredCharacter root;
        CharacterRoleSnapshot role;
        RecoveredPosition position;
        Session::NormalWorldInitialization initialization;
        std::uint16_t native_actor;
        std::string name;
        std::uint8_t level,profession;
        bool same(const Actor& b) const {
            return session.lock()==b.session.lock() && session_id==b.session_id && account==b.account && character==b.character &&
                battle==b.battle && phase==b.phase && root.id==b.root.id && root.account_id==b.root.account_id &&
                root.slot==b.root.slot && root.profile==b.root.profile && root.created_at==b.root.created_at &&
                root.name_codepage==b.root.name_codepage && root.streamer_privilege==b.root.streamer_privilege &&
                role==b.role && position==b.position && native_actor==b.native_actor && name==b.name && level==b.level && profession==b.profession &&
                initialization.entry_frame()==b.initialization.entry_frame() && initialization.accepted_tail()==b.initialization.accepted_tail();
        }
        bool same_detail_identity(const Actor& b) const {
            if(position.area!=b.position.area || position.scene!=b.position.scene)return false;
            auto comparable=*this;comparable.position=b.position;
            return comparable.same(b); // Same-scene movement is not a membership/identity change.
        }
        bool same_owner(const Actor& b) const {
            return session.lock()==b.session.lock() && session_id==b.session_id && account==b.account && character==b.character && native_actor==b.native_actor;
        }
    };
    struct Listing {Actor actor;std::array<std::uint8_t,24> raw;};
    struct Detail {
        Actor owner,target;
        std::vector<Actor> members; // Complete actual group; display prefix alone is not authority.
        std::shared_ptr<const NativeParty> party;
        std::vector<std::uint8_t> raw_request; // Full C90, including opaque highWORD.
    };
    // CUSTOM-0101 actual issued AB presentation only. This readset is NOT
    // C91 permission and is never consumed as an invitation/join authority.
    // Retain only relevant ordered membership, not unrelated pending offers.
    struct Presentation {
        Actor owner,target;
        std::vector<Actor> members; // Complete group, including undisplayed fifth member.
        std::vector<std::uint64_t> participants;
        std::size_t party_size;
    };
    struct Query {
        Actor actor;std::array<std::uint8_t,24> raw;std::size_t page{};
        std::map<std::uint16_t,Actor> issued;
        std::vector<std::uint16_t> visible; // Exact most recent A7 rows, not every historical page.
        std::shared_ptr<const Detail> detail;
        std::vector<std::uint8_t> last_join_request; // Full C91; never interpreted as a nonce.
        std::map<std::uint16_t,std::array<std::uint8_t,22>> descriptions; // Actual issued A7/A9 bytes, including retained post-NUL tail.
        std::shared_ptr<const Presentation> presentation; // Last actual AB; never authorizes C91.
    };
    struct State {std::map<std::uint64_t,Listing> listings;std::map<std::uint64_t,Query> queries;};
    using Snapshot=std::shared_ptr<const State>;
    OwnedPartyDirectory():state_(std::make_shared<const State>()) {}
    Snapshot snapshot() const noexcept {return state_;}
    bool publish(const Snapshot& expected,Snapshot next) noexcept {
        if(state_!=expected || !next)return false;state_=std::move(next);return true;
    }
    void disconnect(const Session& session) {
        // Avoid allocating or publishing anything for an unrelated disconnect.
        const auto listing=state_->listings.find(session.id());
        const auto query=state_->queries.find(session.id());
        const bool own_listing=listing!=state_->listings.end() && listing->second.actor.session.lock().get()==&session;
        const bool own_query=query!=state_->queries.end() && query->second.actor.session.lock().get()==&session;
        if(!own_listing && !own_query)return;
        auto next=std::make_shared<State>(*state_);bool changed=false;
        if(const auto at=next->listings.find(session.id());at!=next->listings.end() && at->second.actor.session.lock().get()==&session){next->listings.erase(at);changed=true;}
        if(const auto at=next->queries.find(session.id());at!=next->queries.end() && at->second.actor.session.lock().get()==&session){next->queries.erase(at);changed=true;}
        if(changed)state_=std::move(next);
    }
private: Snapshot state_;
};
}
