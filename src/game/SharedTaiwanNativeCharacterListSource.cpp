#include "game/SharedTaiwanNativeCharacterListSource.h"
#include "game/SharedTaiwanCharacterListHandoff.h"
#include "db/NativeWorldEntrySnapshotRepository.h"
#include "protocol/RecoveredWorldFrame.h"
#include "text/OwnedCharacterNameText.h"
#include <algorithm>
#include <memory>
#include <map>
#include <limits>
#include <set>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
using Source=SharedTaiwanNativeCharacterListSource;
struct Observation {
    NativeCharacterSummarySnapshot snapshot;
    std::vector<RecoveredCharacter> roots;
    Source::Target target;
};
struct State {
    AccountRepository& accounts;
    RecoveredCharacterRepository& characters;
    NativeCharacterSummarySnapshotRepository& snapshots;
    const std::string client;
    Source::TargetSource targets;
    Source::Qualify qualify;
    const std::size_t capacity;
    Source::Publish publish;
    Source::LinkSource links;
    Source::Prepare prepare;
    const std::thread::id thread=std::this_thread::get_id();
    bool active=false,reentered=false;
    struct Pending {Source::Scope scope;Observation observation;Session::NativeCharacterList delivery;};
    std::map<std::uint64_t,Pending> pending;
    struct SelectionRecord {
        Source::SelectedPtr selected;
        Observation observation;
        Source::Link link;
        std::weak_ptr<Session> session;
    };
    std::map<std::uint64_t,SelectionRecord> selections;
    std::uint64_t sequence=0; // Game owner, never reused or put on native wire.
    struct Guard {
        State& state;
        explicit Guard(State& value):state(value) {
            if(std::this_thread::get_id()!=state.thread)throw std::logic_error("TW native list owner mismatch");
            if(state.active) {state.reentered=true;throw std::logic_error("TW native list source reentered");}
            state.active=true;state.reentered=false;
        }
        ~Guard(){state.active=false;state.reentered=false;}
    };
    bool session_current(Session& session,const Source::Scope& scope) const {
        const auto input=session.recovered_native_selection_input();
        return !reentered && !session.closing() && session.id()==scope.session &&
            session.account_id==scope.account && !session.character_id &&
            session.recovered_server_selection()==scope.selection &&
            (!scope.selection || (scope.selection->session==scope.session && scope.selection->account==scope.account &&
                scope.selection->advertisement && scope.selection->advertisement->session==scope.session &&
                !scope.selection->advertisement->wire.empty())) &&
            session.state()==scope.state && scope.state==SessionState::Authenticated &&
            (!scope.input || (input && input->session==scope.session && input->account==scope.account &&
                input->input==*scope.input && input->created==scope.created)) &&
            snapshots.owns_sources(accounts,characters);
    }
    bool roots_current(const std::vector<RecoveredCharacter>& wanted,std::uint64_t account) {
        const auto actual=characters.list_for_account(account);
        if(actual.size()!=wanted.size())return false;
        for(std::size_t i=0;i<actual.size();++i)
            if(!NativeWorldEntrySnapshot::same_root(actual[i],wanted[i]))return false;
        return true;
    }
    bool current(Session& session,const Source::Scope& scope,const Observation& observation) {
        if(!session_current(session,scope) || !roots_current(observation.roots,scope.account))return false;
        const auto stored=snapshots.load(scope.account,observation.target.group,observation.target.server,client);
        if(!stored || *stored!=observation.snapshot || !roots_current(observation.roots,scope.account))return false;
        if(!observation.target.current(session,scope) || !session_current(session,scope) ||
           !roots_current(observation.roots,scope.account))return false;
        return snapshots.load(scope.account,observation.target.group,observation.target.server,client)==stored &&
            roots_current(observation.roots,scope.account) && session_current(session,scope);
    }
    void prune_selections() {
        // Pure Session observations only: no external callback with a live
        // iterator. A retained receipt never extends the connection lifetime.
        for(auto it=selections.begin();it!=selections.end();) {
            const auto session=it->second.session.lock();
            const auto& scope=it->second.selected->scope();
            const auto input=session?session->recovered_native_selection_input():nullptr;
            if(!session || session->closing() || session->id()!=scope.session ||
               session->account_id!=scope.account || !input || !scope.input ||
               input->input!=*scope.input || input->created!=scope.created)
                it=selections.erase(it);
            else ++it;
        }
    }
    bool selected_current(const SelectionRecord& record) {
        const auto selected=record.selected;
        const auto session=record.session.lock();
        if(!selected || !selected->source_alive() || !session)return false;
        const auto& scope=selected->scope();
        const auto registered=[&] {
            const auto found=selections.find(scope.session);
            return found!=selections.end() && found->second.selected==selected &&
                found->second.session.lock()==session && session_current(*session,scope);
        };
        if(!scope.issued || !scope.issued->active() || !scope.issued->source_alive() ||
           record.link.issued!=scope.issued || !record.link.current || !registered() ||
           !current(*session,scope,record.observation))return false;
        if(!qualify(*session,scope,record.observation.target,record.observation.snapshot,
                record.observation.roots,Source::Check::Select) || !registered() ||
           !current(*session,scope,record.observation))return false;
        return record.link.current(*session,scope) && registered() &&
            current(*session,scope,record.observation) && registered();
    }
    bool delivery_current(Session& session,const Pending& pending,const Session::NativeCharacterList& delivery) {
        return delivery && pending.delivery==delivery && delivery->session==pending.scope.session &&
            delivery->account==pending.scope.account && delivery->selection==pending.scope.selection &&
            current(session,pending.scope,pending.observation) &&
            qualify(session,pending.scope,pending.observation.target,pending.observation.snapshot,
                    pending.observation.roots,Source::Check::List) &&
            current(session,pending.scope,pending.observation);
    }
    void shape(const Observation& observed,std::uint64_t account) {
        const auto& s=observed.snapshot;
        if(s.account!=account || s.client_sha256!=client || s.group!=observed.target.group ||
           s.server!=observed.target.server || !s.revision || s.record.size()!=75 || s.record[0]!=7 ||
           s.rows.size()>2 || s.record[1]!=s.rows.size())
            throw std::invalid_argument("TW native list lacks the complete actual75 record and ordered bindings");
        // <=2 is the existing common account/fixed75 geometry budget, not a
        // recovered native permission: the bounded client receiver has no clamp.
        std::set<std::uint64_t> ids;std::set<std::uint8_t> tokens;
        for(std::size_t i=0;i<s.rows.size();++i) {
            const auto& row=s.rows[i];
            if(!row.character || !ids.insert(row.character).second || row.role ||
               row.name_source!=NativeCharacterSummarySnapshot::NameSource::CommonIdentity)
                throw std::invalid_argument("TW native list needs real common-name binding, not CN22/prompt projection");
            const auto root=std::find_if(observed.roots.begin(),observed.roots.end(),[&](const auto& r){return r.id==row.character;});
            if(root==observed.roots.end() || root->account_id!=account)
                throw std::invalid_argument("TW native list row is not an actual owned common character");
            const auto name_end=std::find(root->profile.begin(),root->profile.begin()+15,0);
            const std::string encoded(root->profile.begin(),name_end);
            const auto original=OwnedCharacterNameText::from_encoded(encoded,root->name_codepage);
            const auto tw=original?OwnedCharacterNameText::from_utf8(original->original_utf8(),950):std::nullopt;
            const auto start=3+36*i;
            const auto end=std::find(s.record.begin()+start,s.record.begin()+start+16,0);
            if(end==s.record.begin()+start+16 || !tw ||
               std::string(s.record.begin()+start,end)!=tw->encoded_bytes())
                throw std::invalid_argument("TW native list exact name/codepage identity differs");
            const auto token=static_cast<std::uint8_t>(s.record[start+19]&7);
            if(token>3 || !tokens.insert(token).second)
                throw std::invalid_argument("TW native list issued tokens exceed current transport budget or alias");
            // Do not rewrite post-NUL bytes, row flags, routeBYTE32 or opaque
            // appearance/resource words. raw36 is not selected/create40.
        }
    }
    Observation read(Session& session,const Source::Scope& scope,bool materialize=false) {
        if(!scope.session || !scope.account || !session_current(session,scope))
            throw std::invalid_argument("TW native list requires this actual authenticated unselected Session");
        auto roots=characters.list_for_account(scope.account);
        std::set<std::uint64_t> ids;
        for(const auto& root:roots)if(!root.id || root.account_id!=scope.account || !ids.insert(root.id).second)
            throw std::invalid_argument("TW native list common account roots are ambiguous");
        auto target=targets(session,scope);
        if(!target || !target->current || !session_current(session,scope) || !roots_current(roots,scope.account))
            throw std::invalid_argument("TW native list actual destination is absent or changed");
        if(materialize && prepare) {
            const auto ready=[&] {
                if(!session_current(session,scope) || !roots_current(roots,scope.account))return false;
                const bool accepted=target->current(session,scope);
                return accepted && session_current(session,scope) && roots_current(roots,scope.account);
            };
            // No snapshot equality here: BeforeCommit sees staged-next. A
            // failed selected issuer never falls back to an older stored list.
            if(!ready() || !prepare(session,scope,*target,roots,ready) || !ready())
                throw std::invalid_argument("TW native list actual issuer preparation failed");
        }
        auto snapshot=snapshots.load(scope.account,target->group,target->server,client);
        if(!snapshot)throw std::invalid_argument("TW native list has no actual stored issuer record");
        Observation result{std::move(*snapshot),std::move(roots),std::move(*target)};
        shape(result,scope.account);
        if(!current(session,scope,result))throw std::invalid_argument("TW native list source is stale");
        return result;
    }
};
}
std::optional<SharedTaiwanNativeCharacterListSource::Binding>
SharedTaiwanNativeCharacterListSource::Binding::for_handoff(
        const std::shared_ptr<SharedTaiwanCharacterListHandoff>& expected) const {
    // Do not lock an affine owner on a forbidden thread, including after expiry.
    if(!expected || handoff_thread_!=std::this_thread::get_id() || !canonical_handoff_binding_)return {};
    const auto actual=handoff_owner_.lock();
    if(!actual || actual.get()!=expected.get() || actual.owner_before(expected) || expected.owner_before(actual))return {};
    auto result=*canonical_handoff_binding_;
    result.handoff_owner_=handoff_owner_;
    result.canonical_handoff_binding_=canonical_handoff_binding_;
    result.handoff_thread_=handoff_thread_;
    return result;
}
SharedTaiwanNativeCharacterListSource::Binding
SharedTaiwanNativeCharacterListSource::Binding::reseal_host_handoff(Binding wrapped,const Binding& original) {
    if(original.handoff_thread_!=std::this_thread::get_id())
        throw std::logic_error("TW handoff host seal requires original GAME owner");
    const auto owner=original.handoff_owner_.lock();
    if(!owner || !original.for_handoff(owner))
        throw std::invalid_argument("TW handoff host seal lacks its canonical source");
    // Snapshot has no proof -> no canonical->self cycle. Its callbacks may own
    // HostOwner, which owns only the earlier original source, never this seal.
    wrapped.handoff_owner_.reset();wrapped.canonical_handoff_binding_.reset();wrapped.handoff_thread_={};
    const auto canonical=std::make_shared<const Binding>(wrapped);
    wrapped.handoff_owner_=owner;wrapped.canonical_handoff_binding_=canonical;
    wrapped.handoff_thread_=std::this_thread::get_id();return wrapped;
}
SharedTaiwanNativeCharacterListSource::Binding
SharedTaiwanNativeCharacterListSource::create_with_handoff(
        AccountRepository& accounts,RecoveredCharacterRepository& characters,
        NativeCharacterSummarySnapshotRepository& snapshots,std::string client,TargetSource target,Qualify qualify,
        std::size_t capacity,std::shared_ptr<SharedTaiwanCharacterListHandoff> owner,Prepare prepare) {
    if(!owner || !owner->matches_sources(accounts,characters,snapshots,client,capacity))
        throw std::invalid_argument("TW native list requires the exact actual shared handoff sources");
    auto handoff=owner->binding();
    auto result=create(accounts,characters,snapshots,std::move(client),std::move(target),std::move(qualify),
        capacity,std::move(handoff.publish),std::move(handoff.link),std::move(prepare));
    const auto canonical=std::make_shared<const Binding>(result); // proof still empty
    result.handoff_owner_=owner;result.canonical_handoff_binding_=canonical;
    result.handoff_thread_=std::this_thread::get_id();return result;
}
SharedTaiwanNativeCharacterListSource::Target::Target(std::uint16_t g,std::uint16_t s,
        std::function<bool(Session&,const Scope&)> check):group(g),server(s),current(std::move(check)) {
    if(!current)throw std::invalid_argument("TW native list target requires actual Current");
}
SharedTaiwanNativeCharacterListSource::Binding SharedTaiwanNativeCharacterListSource::create(
        AccountRepository& accounts,RecoveredCharacterRepository& characters,
        NativeCharacterSummarySnapshotRepository& snapshots,std::string client,TargetSource target,Qualify qualify,
        std::size_t capacity,Publish publish,LinkSource links,Prepare prepare) {
    if(client.size()!=64 || !std::all_of(client.begin(),client.end(),[](char c){return
        (c>='0' && c<='9') || (c>='a' && c<='f');}) || !target || !qualify ||
        !snapshots.owns_sources(accounts,characters) || !capacity || !publish || !links)
        throw std::invalid_argument("TW native list requires actual same-source reader/build/target/qualification");
    auto state=std::make_shared<State>(State{accounts,characters,snapshots,std::move(client),std::move(target),std::move(qualify),capacity,
        std::move(publish),std::move(links),std::move(prepare)});
    Binding result;
    result.invalidate_active=[state] {
        if(std::this_thread::get_id()!=state->thread)throw std::logic_error("TW native list invalidation owner mismatch");
        if(state->active)state->reentered=true;
    };
    result.invalidate_selection=[state](std::uint64_t session) {
        if(std::this_thread::get_id()!=state->thread)throw std::logic_error("TW selected invalidation owner mismatch");
        state->selections.erase(session);
        if(state->active)state->reentered=true;
    };
    result.list=[state](Session& session) {
        const auto owner=state;State::Guard guard(*owner);
        if(owner->pending.contains(session.id()) || owner->pending.size()>=owner->capacity ||
           owner->sequence==std::numeric_limits<std::uint64_t>::max())
            throw std::invalid_argument("TW native list pending capacity or sequence exhausted");
        const auto selection=session.recovered_server_selection();
        const auto advertisement=selection && selection->advertisement?
            RecoveredTaiwanServerAdvertisement::parse(selection->advertisement->wire):std::nullopt;
        const Scope scope{session.id(),session.account_id,session.state(),{}, {},selection,advertisement};
        if(!scope.selection)throw std::invalid_argument("TW native list lacks this actual account selection input");
        if(!scope.advertised_rows)throw std::invalid_argument("TW native list lacks the complete observed advertisement format");
        const auto observation=owner->read(session,scope,true);
        if(!owner->qualify(session,scope,observation.target,observation.snapshot,observation.roots,Check::List) ||
           !owner->current(session,scope,observation))throw std::invalid_argument("TW native list issuer/phase qualification failed");
        const auto encoded=RecoveredWorldFrame::encode(observation.snapshot.record);
        Frame frame;
        if(encoded.size()!=frame.size())throw std::invalid_argument("TW native list complete envelope size differs");
        std::copy(encoded.begin(),encoded.end(),frame.begin());
        if(!owner->current(session,scope,observation))throw std::invalid_argument("TW native list changed before pre-use return");
        Session::NativeCharacterList delivery=std::make_shared<const Session::NativeCharacterListDelivery>(
            Session::NativeCharacterListDelivery{scope.session,scope.account,++owner->sequence,frame,scope.selection});
        owner->pending.emplace(scope.session,State::Pending{scope,observation,delivery});
        return delivery;
    };
    result.current=[state](Session& session,const Session::NativeCharacterList& delivery) {
        const auto owner=state;State::Guard guard(*owner);
        const auto found=owner->pending.find(session.id());
        return found!=owner->pending.end() && owner->delivery_current(session,found->second,delivery);
    };
    result.complete=[state](Session& session,const Session::NativeCharacterList& delivery,bool written) {
        const auto owner=state;State::Guard guard(*owner);
        const auto found=owner->pending.find(session.id());
        if(found==owner->pending.end() || found->second.delivery!=delivery)return false;
        // Retire before source callbacks can throw; duplicate completion cannot
        // publish or erase a different preparation. No affine owner on strand.
        auto pending=std::move(found->second);owner->pending.erase(found);
        if(!written || session.recovered_native_character_list_written()!=delivery ||
           !owner->delivery_current(session,pending,delivery))return false;
        auto issued=std::shared_ptr<Issued>(new Issued{owner,delivery,pending.observation.snapshot,pending.observation.roots,pending.scope});
        const IssuedPtr observation=issued;
        if(!owner->publish(session,observation) || !owner->delivery_current(session,pending,delivery))return false;
        issued->active_=true; // Last: provider-caught reentry/throw cannot activate.
        return true;
    };
    result.select=[state](Session& session,const RecoveredPostCreateSelect::Selection& input,std::optional<std::uint64_t> created) {
        const auto owner=state;State::Guard guard(*owner);
        owner->selections.erase(session.id()); // A failed new input cannot reuse its predecessor.
        owner->prune_selections();
        if(owner->selections.size()>=owner->capacity)
            throw std::invalid_argument("TW native selected provenance capacity exhausted");
        const auto decoded=RecoveredPostCreateSelect::selection_from_frame(input.raw);
        if(!decoded || decoded->logical!=input.logical ||
           (input.prefix && !RecoveredPostCreateSelect::valid_prefix(*input.prefix)))
            throw std::invalid_argument("TW native selection requires the complete exact original input");
        const auto token=input.token();
        if(token>3 || (created && !*created))throw std::invalid_argument("TW native selection scope is invalid");
        const auto selection=session.recovered_server_selection();
        const auto advertisement=selection && selection->advertisement?
            RecoveredTaiwanServerAdvertisement::parse(selection->advertisement->wire):std::nullopt;
        Scope scope{session.id(),session.account_id,session.state(),token,created,selection,advertisement,input,{}};
        if(selection && !advertisement)
            throw std::invalid_argument("TW native selection has malformed observed advertisement, not absent source");
        if(!scope.session || !scope.account || !owner->session_current(session,scope))
            throw std::invalid_argument("TW native selection lacks the actual independently owned authenticated input");
        auto link=owner->links(session,scope);
        if(!link || !link->issued || !link->current || !link->issued->active_ ||
           link->issued->owner_.lock()!=std::static_pointer_cast<const void>(owner) ||
           !owner->session_current(session,scope))
            throw std::invalid_argument("TW native selection lacks this actual issued-list source link");
        scope.issued=link->issued;
        if(!link->current(session,scope) || !owner->session_current(session,scope))
            throw std::invalid_argument("TW native selection link changed before source read");
        const auto observation=owner->read(session,scope);
        const auto& issued=*scope.issued;
        if(issued.snapshot_!=observation.snapshot || issued.snapshot_.account!=scope.account ||
           issued.roots_.size()!=observation.roots.size() || !issued.delivery_ ||
           issued.delivery_->account!=scope.account || issued.delivery_->selection!=issued.issuer_scope_.selection)
            throw std::invalid_argument("TW native selection differs from the actually issued full source");
        for(std::size_t i=0;i<issued.roots_.size();++i)
            if(!NativeWorldEntrySnapshot::same_root(issued.roots_[i],observation.roots[i]))
                throw std::invalid_argument("TW native selection issued common roots changed");
        std::optional<std::uint64_t> selected;
        for(std::size_t i=0;i<observation.snapshot.rows.size();++i)
            if((observation.snapshot.record[3+36*i+19]&7)==token)selected=observation.snapshot.rows[i].character;
        if(!selected || (created && *selected!=*created) ||
           !owner->qualify(session,scope,observation.target,observation.snapshot,observation.roots,Check::Select) ||
           !owner->current(session,scope,observation) || !link->current(session,scope) ||
           !owner->current(session,scope,observation))throw std::invalid_argument("TW native issued-token character/phase source rejected");
        const auto actual_session=session.weak_from_this();
        if(actual_session.expired())throw std::invalid_argument("TW native selected provenance lacks actual Session lifetime");
        SelectedPtr receipt(new Selected{owner,*selected,scope,observation.snapshot,observation.roots});
        owner->selections.emplace(scope.session,State::SelectionRecord{receipt,observation,*link,actual_session});
        return *selected; // Full common ID; never common slot or masked native actor alias.
    };
    result.selected=[state](std::uint64_t session,std::uint64_t account,std::uint64_t character)
            ->std::optional<SelectedLink> {
        const auto owner=state;State::Guard guard(*owner);
        owner->prune_selections();
        const auto found=owner->selections.find(session);
        if(found==owner->selections.end())return std::nullopt;
        const auto record=found->second; // No map borrow crosses any external Current.
        const auto receipt=record.selected;
        if(receipt->scope().session!=session || receipt->scope().account!=account ||
           receipt->character()!=character || !owner->selected_current(record))return std::nullopt;
        const auto weak=std::weak_ptr<State>(owner);
        return SelectedLink{receipt,[weak,receipt] {
            const auto held=weak.lock();if(!held)return false;
            State::Guard guard(*held);
            const auto found=held->selections.find(receipt->scope().session);
            if(found==held->selections.end() || found->second.selected!=receipt)return false;
            const auto record=found->second;
            return held->selected_current(record);
        }};
    };
    return result;
}
}
