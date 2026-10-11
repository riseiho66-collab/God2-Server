#include "auth/SharedTaiwanCharacterRemoval.h"
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
bool same_row(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
        a.profile==b.profile && a.created_at==b.created_at &&
        a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
bool preselection(const Session& connection,std::uint64_t session,std::uint64_t account) {
    return session && account && connection.id()==session && !connection.closing() &&
        connection.account_id==account && !connection.character_id &&
        !connection.recovered_world_ready() && connection.state()==SessionState::Authenticated;
}
}
SharedTaiwanCharacterRemoval::SharedTaiwanCharacterRemoval(Sources sources):sources_(std::move(sources)) {}
void SharedTaiwanCharacterRemoval::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW character removal game owner mismatch");
}
SharedTaiwanCharacterRemoval::Handler SharedTaiwanCharacterRemoval::handler(Sources sources) {
    if(!sources || !sources.login->owns_repository(*sources.accounts) ||
       !sources.presence->owns_repository(*sources.characters))return {};
    auto owner=std::shared_ptr<SharedTaiwanCharacterRemoval>(new SharedTaiwanCharacterRemoval(std::move(sources)));
    return [owner](Session& session,const RecoveredCharacterDelete& request) {return owner->handle(session,request);};
}
std::uint64_t SharedTaiwanCharacterRemoval::verify(const RecoveredCharacterDelete& request) {
    // Reuse the exact frozen TW deletion login semantics. flag0 forbids local
    // registration even when the actual Login owner enables it for flag4.
    // No display/codepage conversion or account identity normalization here.
    RecoveredC2S0002::Payload credentials{};
    credentials[0]=0;credentials[167]=0xc8;
    std::copy(request.account.begin(),request.account.end(),credentials.begin()+1);
    std::copy(request.password.begin(),request.password.end(),credentials.begin()+25);
    const auto checked=RecoveredC2S0002::parse(RecoveredC2S0002::encode(credentials),0);
    return checked?sources_.login->authenticate(*checked):0;
}
std::optional<RecoveredCharacter> SharedTaiwanCharacterRemoval::resolve(
    std::uint64_t account,const RecoveredCharacterDelete& request) {
    if(!account || request.token>1)return {};
    const auto end=std::find(request.name.begin(),request.name.end(),0);
    if(end==request.name.begin() || end==request.name.end())return {};
    const auto name=std::span<const std::uint8_t>{request.name.begin(),end};
    std::optional<RecoveredCharacter> selected;
    for(const auto& row:sources_.characters->list_for_account(account)) {
        if(row.slot!=request.token)continue;
        // Reject ambiguous owned slots rather than choosing list iteration order.
        if(selected || !row.id || row.account_id!=account)return {};
        const auto stored_end=std::find(row.profile.begin(),row.profile.begin()+15,0);
        if(stored_end==row.profile.begin() || stored_end==row.profile.begin()+15 ||
           !std::equal(name.begin(),name.end(),row.profile.begin(),stored_end))return {};
        selected=row;
    }
    return selected;
}
bool SharedTaiwanCharacterRemoval::handle(Session& session,const RecoveredCharacterDelete& request) {
    owner();if(busy_)return false;
    const auto session_id=session.id(),account=session.account_id;
    if(!preselection(session,session_id,account))return false;
    // Session supplies a parsed TW19. Defend direct source callers too; do not
    // retain its credentials in Scope, policy, admission, SQL or replay evidence.
    for(const auto* text:{&request.account,&request.password,&request.name})
        if(text->front()==0 || std::find(text->begin(),text->end(),0)==text->end())return false;
    busy_=true;
    struct Release {bool& busy;~Release(){busy=false;}} release{busy_};
    if(verify(request)!=account || !preselection(session,session_id,account))return false;
    const auto expected=resolve(account,request);
    if(!expected || !sources_.presence->unreserved(account,expected->id))return false;
    const Scope scope{account,session_id,expected->id,request.token,
        std::shared_ptr<const Attempt>(new Attempt)};
    const auto live=session.weak_from_this();
    const auto selection_current=[&session,live,&scope] {
        return live.lock().get()==&session && preselection(session,scope.session,scope.account);
    };
    if(!selection_current())return false;
    // Real rule/guild/replay owner observes the copied saved snapshot. It cannot
    // substitute native slot/name for common ownership or pre-authorize absence.
    auto policy=sources_.prepare(scope,*expected);
    if(!policy || !*policy || !selection_current() ||
       !sources_.presence->unreserved(account,expected->id))return false;
    const auto after_prepare=resolve(account,request);
    if(!after_prepare || !same_row(*after_prepare,*expected))return false;
    const auto actual=[&selection_current,&policy,&scope](Phase phase) {
        return selection_current() && (*policy)(scope,phase) && selection_current();
    };
    // Full row CAS, both prepared/active registries and all TW/CN offer
    // invalidations are mandatory in the already concrete common writer.
    // The predicate's lifetime ends with this synchronous serial transaction.
    // Return committed truth directly: no post-COMMIT failure becomes a false
    // native result. Existing Session owns02 framing/queue and02/04->03 drain;
    // durable post-COMMIT/disconnect receipts are an explicit remaining gap.
    return SharedCharacterRemoval::commit(*sources_.characters,*sources_.admission,
        *sources_.presence,*expected,actual);
}
}
