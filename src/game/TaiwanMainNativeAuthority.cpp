#include "game/TaiwanMainNativeAuthority.h"
#include "db/NativeWorldEntrySnapshotRepository.h"
#include <algorithm>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <thread>

namespace god2 {
namespace {
using Source=SharedTaiwanNativeCharacterListSource;
using Snapshot=NativeCharacterSummarySnapshot;
using Auth=Session::NativeAuthenticatedInput;
using AuthPtr=std::shared_ptr<const Auth>;
bool roots_equal(std::span<const RecoveredCharacter> a,std::span<const RecoveredCharacter> b) {
    if(a.size()!=b.size())return false;
    for(std::size_t i=0;i<a.size();++i)if(!NativeWorldEntrySnapshot::same_root(a[i],b[i]))return false;
    return true;
}
bool authenticated(const AuthPtr& auth,Session& session,ProtocolMode mode) {
    return auth && auth->session==session.id() && auth->account==session.account_id && auth->account &&
        auth->mode==mode && session.recovered_native_authenticated_input()==auth &&
        session.state()==SessionState::Authenticated && !session.closing() && !session.character_id;
}
}
struct TaiwanMainNativeAuthority::State {
    AccountRepository& accounts;
    RecoveredCharacterRepository& characters;
    SqliteNativeCharacterSummarySnapshotRepository& writer;
    const std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration;
    const std::string client;
    const std::uint8_t group;
    const std::array<StorageScope,3> scopes;
    const std::size_t capacity;
    SharedTaiwanNativeCharacterOfferSource::Supply supply;
    Source::Prepare writer_prepare;
    const std::thread::id thread=std::this_thread::get_id();
    bool preparing=false,poisoned=false;
    std::uint64_t epoch=0;
    struct Publication {
        std::uint64_t epoch;
        std::uint8_t subgroup;
        Snapshot snapshot;
        std::vector<RecoveredCharacter> roots;
        std::weak_ptr<const Auth> issuer;
        std::weak_ptr<const Session::RecoveredServerSelection> selection;
    };
    // Only successful actual Prepare can install a Publication. No import,
    // approve(snapshot), setter or public publication constructor is exposed.
    using Key=std::pair<std::uint64_t,std::uint8_t>;
    std::map<Key,std::shared_ptr<const Publication>> published;
    struct Candidate {Snapshot snapshot;std::vector<RecoveredCharacter> roots;std::uint8_t subgroup;};
    std::shared_ptr<const Candidate> staging;
    State(AccountRepository& a,RecoveredCharacterRepository& c,SqliteNativeCharacterSummarySnapshotRepository& w,
        std::shared_ptr<const TaiwanNativeClientGroupConfiguration> config,std::string build,
        std::uint8_t g,std::array<StorageScope,3> scopes_in,std::size_t bound,
        SharedTaiwanNativeCharacterOfferSource::Supply actual)
        :accounts(a),characters(c),writer(w),configuration(std::move(config)),client(std::move(build)),
         group(g),scopes(scopes_in),capacity(bound),supply(std::move(actual)) {}
    ~State(){if(std::this_thread::get_id()!=thread)std::terminate();}
    void check() const {
        if(thread!=std::this_thread::get_id() || poisoned)
            throw std::logic_error("Main native authority GAME owner or reentry mismatch");
    }
    std::optional<std::uint8_t> selected(const Source::Scope& scope) const {
        const auto selection=scope.issued?scope.issued->issuer_scope().selection:scope.selection;
        if(!selection || selection->account!=scope.account)return {};
        const auto pair=selection->request.selector_bytes();
        if(pair[0]!=group || pair[1]>=3 || configuration->configured_slots(group)!=std::optional<std::uint8_t>{3})return {};
        return pair[1];
    }
    bool peer(Session& session,const Source::Scope& scope,std::uint8_t subgroup) const {
        check();
        if(scope.session!=session.id() || scope.account!=session.account_id || !scope.account ||
           scope.state!=SessionState::Authenticated || selected(scope)!=subgroup)return false;
        const auto auth=session.recovered_native_authenticated_input();
        if(scope.issued) {
            return authenticated(auth,session,ProtocolMode::God2CharacterConnection) &&
                scope.issued->source_alive() && scope.issued->active() && scope.input && scope.token &&
                scope.input->token()==*scope.token && *scope.token<=3 &&
                session.native_channel_bound() && session.native_channel_binding_current() &&
                session.native_channel_allows_destination(group,subgroup);
        }
        return authenticated(auth,session,ProtocolMode::God2LegacyCharacterListCandidate) &&
            scope.selection==session.recovered_server_selection() && scope.selection &&
            scope.selection->session==session.id() && scope.selection->advertisement &&
            scope.selection->advertisement->session==session.id() && scope.advertised_rows.has_value();
    }
    bool policy(const Snapshot& snapshot,std::span<const RecoveredCharacter> roots,std::uint8_t subgroup) const {
        if(subgroup>=3 || snapshot.client_sha256!=client || !snapshot.account || !snapshot.revision ||
           snapshot.group!=scopes[subgroup].group || snapshot.server!=scopes[subgroup].server ||
           snapshot.record.size()!=75 || snapshot.record[0]!=7 || snapshot.rows.size()!=roots.size() ||
           roots.size()>2 || snapshot.record[1]!=snapshot.rows.size())return false;
        // CUSTOM visibility: all owned common roots, exact producer order.
        // No hidden/deleted/foreign rows, prompt-marker or external role backing.
        std::set<std::uint64_t> ids;std::set<std::uint8_t> tokens;
        for(const auto& root:roots)
            if(!root.id || root.account_id!=snapshot.account || !ids.insert(root.id).second)return false;
        std::set<std::uint64_t> visible;
        for(std::size_t i=0;i<snapshot.rows.size();++i) {
            const auto& row=snapshot.rows[i];const auto at=3+36*i;
            const auto token=static_cast<std::uint8_t>(snapshot.record[at+19]&7);
            if(!ids.contains(row.character) || !visible.insert(row.character).second || row.role ||
               row.name_source!=Snapshot::NameSource::CommonIdentity || token>3 || !tokens.insert(token).second ||
               !snapshot.record[at+32])return false;
        }
        return true;
    }
    bool primary(const Source::Scope& scope,const Snapshot& snapshot,std::uint8_t subgroup) const {
        if(!scope.advertised_rows)return false;
        for(std::size_t i=0;i<snapshot.rows.size();++i) {
            const auto destination=scope.advertised_rows->primary_destination({group,subgroup,3},
                static_cast<std::uint8_t>(snapshot.record[3+36*i+19]&7),snapshot.record);
            if(!destination || !destination->port())return false;
        }
        return true;
    }
    bool current(const std::shared_ptr<const Publication>& value) {
        check();if(!value)return false;
        const Key key{value->snapshot.account,value->subgroup};
        const auto held=published.find(key);
        if(held==published.end() || held->second!=value || !policy(value->snapshot,value->roots,value->subgroup))return false;
        const auto account=accounts.find_by_id(key.first);check();
        if(!account || account->id!=key.first)return false;
        const auto roots=characters.list_for_account(key.first);check();
        if(!roots_equal(roots,value->roots))return false;
        const auto actual=writer.load(key.first,value->snapshot.group,value->snapshot.server,client);check();
        const auto fresh=published.find(key);
        return actual==std::optional<Snapshot>{value->snapshot} && fresh!=published.end() && fresh->second==value;
    }
    void prune_expired() {
        // No timeout/FIFO/latest-account eviction. A live Handoff record owns
        // its exact Auth and the Issued scope owns its exact selection, so a
        // pending cross-socket transfer survives L close. Dead observations
        // cannot qualify and need not consume the bounded publication table.
        for(auto it=published.begin();it!=published.end();) {
            const auto& value=it->second;
            if(!value || value->issuer.expired() || value->selection.expired())it=published.erase(it);
            else ++it;
        }
    }
    std::shared_ptr<const Publication> find(const Source::Scope& scope,const Snapshot& snapshot,
        std::span<const RecoveredCharacter> roots) {
        check();const auto subgroup=selected(scope);if(!subgroup)return {};
        const auto found=published.find(Key{scope.account,*subgroup});if(found==published.end())return {};
        auto value=found->second;
        const auto selection=scope.issued?scope.issued->issuer_scope().selection:scope.selection;
        if(!value || value->selection.lock()!=selection || value->snapshot!=snapshot ||
           !roots_equal(value->roots,roots) || !current(value))return {};
        return value;
    }
};
TaiwanMainNativeAuthority::Binding::Binding(Source::TargetSource t,Source::Qualify q,Handoff::Live l,
    Handoff::Authority a,Source::Prepare p)
    :target(std::move(t)),qualify(std::move(q)),live(std::move(l)),authority(std::move(a)),prepare(std::move(p)) {}

std::shared_ptr<TaiwanMainNativeAuthority> TaiwanMainNativeAuthority::create(AccountRepository& accounts,
    RecoveredCharacterRepository& characters,SqliteNativeCharacterSummarySnapshotRepository& writer,
    std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration,std::string client,
    std::uint8_t group,std::array<StorageScope,3> scopes,std::size_t capacity,
    SharedTaiwanNativeCharacterOfferSource::Supply supply) {
    if(!configuration || group>=10 || configuration->configured_slots(group)!=std::optional<std::uint8_t>{3} ||
       client!=TaiwanNativeClientGroupConfiguration::client_sha256 || !capacity || !supply ||
       !writer.owns_sources(accounts,characters))
        throw std::invalid_argument("Main authority requires exact native build/config, three actual slots, same writer/readers and full producer");
    for(std::size_t i=0;i<scopes.size();++i)for(std::size_t j=0;j<i;++j)
        if(scopes[i]==scopes[j])throw std::invalid_argument("Main authority needs distinct delivery scopes for its three native slots");
    auto state=std::make_shared<State>(accounts,characters,writer,std::move(configuration),std::move(client),group,scopes,capacity,std::move(supply));
    const std::weak_ptr<State> weak=state;
    state->writer_prepare=SharedTaiwanNativeCharacterOfferSource::create(writer,accounts,characters,state->client,
        [weak](Session& session,const Source::Scope& scope,const Source::Target& target,
            std::span<const RecoveredCharacter> roots,const std::optional<Snapshot>& expected)
            ->std::optional<SharedTaiwanNativeCharacterOfferSource::Offer> {
            const auto owner=weak.lock();if(!owner)return {};
            owner->check();const auto subgroup=owner->selected(scope);
            if(!owner->preparing || owner->staging || !subgroup || !owner->peer(session,scope,*subgroup))return {};
            const auto producer=owner->supply;
            auto result=producer(session,scope,target,roots,expected);owner->check();
            if(!result || !owner->peer(session,scope,*subgroup) ||
               !owner->policy(result->next_,roots,*subgroup) ||
               !owner->primary(scope,result->next_,*subgroup))return {};
            owner->staging=std::make_shared<const State::Candidate>(State::Candidate{
                result->next_,std::vector<RecoveredCharacter>(roots.begin(),roots.end()),*subgroup});
            return result;
        });
    return std::shared_ptr<TaiwanMainNativeAuthority>(new TaiwanMainNativeAuthority(std::move(state)));
}
TaiwanMainNativeAuthority::Binding TaiwanMainNativeAuthority::binding() const {
    state_->check();const auto state=state_;
    Source::TargetSource target=[capture=state](Session& session,const Source::Scope& scope)->std::optional<Source::Target> {
        const auto state=capture;
        state->check();const auto subgroup=state->selected(scope);
        if(!subgroup || !state->peer(session,scope,*subgroup))return {};
        const auto auth=session.recovered_native_authenticated_input();const auto selected=scope.selection;const auto issued=scope.issued;
        return Source::Target{state->scopes[*subgroup].group,state->scopes[*subgroup].server,
            [capture=state,auth,selected,issued,subgroup=*subgroup](Session& peer,const Source::Scope& probe) {
                const auto state=capture;
                return probe.selection==selected && probe.issued==issued &&
                    peer.recovered_native_authenticated_input()==auth && state->peer(peer,probe,subgroup);
            }};
    };
    Source::Qualify qualify=[capture=state](Session& session,const Source::Scope& scope,const Source::Target& target,
        const Snapshot& snapshot,std::span<const RecoveredCharacter> roots,Source::Check check) {
        const auto state=capture;
        state->check();auto publication=state->find(scope,snapshot,roots);
        if(!publication || !state->peer(session,scope,publication->subgroup) ||
           target.group!=snapshot.group || target.server!=snapshot.server)return false;
        if(check==Source::Check::List) {
            if(scope.issued || scope.input || scope.token || !scope.advertised_rows ||
               publication->issuer.lock()!=session.recovered_native_authenticated_input())return false;
            return state->primary(scope,snapshot,publication->subgroup);
        }
        if(!scope.issued || !scope.input || !scope.token || scope.issued->snapshot()!=snapshot)return false;
        std::size_t matches=0;
        for(std::size_t i=0;i<snapshot.rows.size();++i)
            if((snapshot.record[3+36*i+19]&7)==*scope.token &&
               (!scope.created || snapshot.rows[i].character==*scope.created))++matches;
        return matches==1;
    };
    Handoff::Live live=[capture=state](const Source::Issued& issued,const Auth& auth) {
        const auto state=capture;
        state->check();const auto& scope=issued.issuer_scope();
        if(!issued.source_alive() || auth.mode!=ProtocolMode::God2LegacyCharacterListCandidate ||
           auth.account!=scope.account || auth.session!=scope.session || !scope.selection ||
           scope.selection->session!=auth.session)return false;
        const auto publication=state->find(scope,issued.snapshot(),issued.roots());
        return publication && publication->issuer.lock().get()==&auth;
    };
    Handoff::Authority authority=[capture=state](Session& session,const Source::Scope& scope,const Source::Issued& issued,
        const Auth& issuer,const Auth& peer)->std::optional<Handoff::DestinationAuthority> {
        const auto state=capture;
        state->check();const auto auth=session.recovered_native_authenticated_input();
        auto publication=state->find(issued.issuer_scope(),issued.snapshot(),issued.roots());
        if(!publication || scope.issued.get()!=&issued || !auth || auth.get()!=&peer ||
           publication->issuer.lock().get()!=&issuer ||
           issuer.account!=scope.account || issuer.session!=issued.issuer_scope().session ||
           issuer.mode!=ProtocolMode::God2LegacyCharacterListCandidate ||
           !state->peer(session,scope,publication->subgroup))return {};
        return Handoff::DestinationAuthority{state->group,publication->subgroup,
            [capture=state,publication,auth,ticket=scope.issued](Session& peer,const Source::Scope& probe) {
                const auto state=capture;
                const auto retained=publication;const auto authentication=auth;const auto issued=ticket;
                return probe.issued==issued && peer.recovered_native_authenticated_input()==authentication &&
                    state->peer(peer,probe,retained->subgroup) && state->current(retained) &&
                    issued->snapshot()==retained->snapshot && roots_equal(issued->roots(),retained->roots);
            }};
    };
    Source::Prepare prepare=[capture=state](Session& session,const Source::Scope& scope,const Source::Target& target,
        std::span<const RecoveredCharacter> roots,const std::function<bool()>& parent_current) {
        const auto state=capture;
        const auto current=parent_current;
        state->check();
        if(state->preparing){state->poisoned=true;throw std::logic_error("Main authority preparation reentered");}
        const auto subgroup=state->selected(scope);
        if(!subgroup || scope.issued || !state->peer(session,scope,*subgroup) || !current ||
           target.group!=state->scopes[*subgroup].group || target.server!=state->scopes[*subgroup].server ||
           state->epoch==std::numeric_limits<std::uint64_t>::max())return false;
        const State::Key key{scope.account,*subgroup};
        state->prune_expired();
        if(!state->published.contains(key) && state->published.size()>=state->capacity)return false;
        state->preparing=true;state->staging.reset();
        struct Reset {State& s;~Reset(){s.staging.reset();s.preparing=false;s.poisoned=false;}} reset{*state};
        // Preallocate map slot before any durable write. A null slot never
        // qualifies. Failure retains the prior exact Publication if any.
        const auto inserted=state->published.try_emplace(key,nullptr).second;
        struct EmptySlot {State& s;State::Key key;bool inserted;~EmptySlot(){
            if(inserted){const auto found=s.published.find(key);if(found!=s.published.end()&&!found->second)s.published.erase(found);}
        }} empty{*state,key,inserted};
        const auto writer=state->writer_prepare;
        if(!writer(session,scope,target,roots,current))return false;
        state->check();const auto candidate=state->staging;
        if(!candidate || !state->peer(session,scope,*subgroup) || !current())return false;
        state->check();
        const auto actual=state->writer.load(scope.account,target.group,target.server,state->client);state->check();
        const auto actual_roots=state->characters.list_for_account(scope.account);state->check();
        const auto account=state->accounts.find_by_id(scope.account);state->check();
        if(!actual || *actual!=candidate->snapshot || !roots_equal(actual_roots,candidate->roots) ||
           !account || account->id!=scope.account || !current())return false;
        state->check();
        auto publication=std::make_shared<const State::Publication>(State::Publication{
            state->epoch+1,*subgroup,candidate->snapshot,candidate->roots,
            session.recovered_native_authenticated_input(),scope.selection});
        // Private mint only after genuine same-writer commit and exact readback.
        // Allocation failure cannot create authority for a committed witness.
        state->published.at(key)=std::move(publication);++state->epoch;
        return true;
    };
    return Binding{std::move(target),std::move(qualify),std::move(live),std::move(authority),std::move(prepare)};
}
bool TaiwanMainNativeAuthority::matches_sources(const AccountRepository& accounts,
    const RecoveredCharacterRepository& characters,const NativeCharacterSummarySnapshotRepository& writer) const {
    state_->check();return &state_->accounts==&accounts && &state_->characters==&characters &&
        &state_->writer==&writer && state_->writer.owns_sources(accounts,characters);
}
void TaiwanMainNativeAuthority::revoke(std::uint64_t account,std::uint8_t subgroup) {
    if(state_->thread!=std::this_thread::get_id())throw std::logic_error("Main authority revoke GAME mismatch");
    // Withdrawal is effective even when a producer attempts it inside an
    // in-flight preparation. Poison that write, but never preserve old rights.
    state_->published.erase(State::Key{account,subgroup});
    if(state_->preparing){state_->poisoned=true;throw std::logic_error("Main authority revoke during preparation");}
}
}
