#include "game/TaiwanNativeSceneSourceLifetime.h"
#include "net/Session.h"

namespace god2 {
TaiwanNativeSceneSourceLifetime::TaiwanNativeSceneSourceLifetime(
        const std::shared_ptr<Session>& session,const SharedWorldPresence::Lease& lease)
    :session_(session),lease_(lease) {}
bool TaiwanNativeSceneSourceLifetime::owned_by(
        const Session& session,const SharedWorldPresence::Lease& lease)const noexcept {
    return session_.lock().get()==&session && lease_==lease &&
        session.id()==lease_.session && session.account_id==lease_.account &&
        session.character_id==lease_.character;
}
}
