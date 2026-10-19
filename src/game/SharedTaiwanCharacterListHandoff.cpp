#include "game/SharedTaiwanCharacterListHandoff.h"
#include "db/NativeWorldEntrySnapshotRepository.h"
#include <algorithm>
#include <limits>
#include <map>
#include <stdexcept>
#include <thread>

namespace god2 {
namespace {
using Source=SharedTaiwanNativeCharacterListSource;
using AuthPtr=std::shared_ptr<const Session::NativeAuthenticatedInput>;
using InputPtr=std::shared_ptr<const Session::NativeCharacterSelectionInput>;
bool auth_valid(const AuthPtr& auth,ProtocolMode mode,std::uint8_t opcode) {
    if(!auth || !auth->account || !auth->session || auth->mode!=mode)return false;
    const auto parsed=RecoveredC2S0002::parse(auth->input.raw,opcode);
    return parsed && parsed->logical==auth->input.logical && parsed->consumed==auth->input.consumed;
}
// Native547B80 is a bounded string copy: first NUL zero-fills the remainder.
// 14C50 copies16 then forces byte15 NUL. Auth permits post-NUL raw bytes, so
// copying the first16 verbatim would not recover the actual native projection.
std::array<std::uint8_t,16> project(std::span<const std::uint8_t> value) {
    std::array<std::uint8_t,16> result{};
    for(std::size_t i=0;i<15 && i<value.size() && value[i];++i)result[i]=value[i];
    return result;
}
bool projects(const AuthPtr& auth,const RecoveredPostCreateSelect::Selection& input) {
    if(!auth)return false;
    const auto credentials=std::span<const std::uint8_t>(auth->input.logical);
    const auto first=project(credentials.subspan(1,24)),second=project(credentials.subspan(25,132));
    return std::equal(first.begin(),first.end(),input.logical.begin()+1) &&
        std::equal(second.begin(),second.end(),input.logical.begin()+17);
}
}
struct SharedTaiwanCharacterListHandoff::State {
    AccountRepository& accounts;
    RecoveredCharacterRepository& characters;
    NativeCharacterSummarySnapshotRepository& snapshots;
    std::string client;
    std::size_t capacity;
    const std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration;
    Live live;
    Authority authority;
    const std::thread::id thread=std::this_thread::get_id();
    bool busy=false,reentered=false;
    // Pure immutable data only; no Session/DB/Target callback in a record.
    struct Record {std::uint64_t epoch;Source::IssuedPtr ticket;AuthPtr issuer;};
    std::map<std::uint64_t,Record> records;
    std::uint64_t epoch=0;
    struct Match {
        Record record;Current current;
        RecoveredTaiwanServerAdvertisement::Table table;
        RecoveredTaiwanServerAdvertisement::Destination destination;
    };
    State(AccountRepository& a,RecoveredCharacterRepository& c,NativeCharacterSummarySnapshotRepository& s,
        std::string build,std::size_t bound,std::shared_ptr<const TaiwanNativeClientGroupConfiguration> config,Live l,Authority q)
        :accounts(a),characters(c),snapshots(s),client(std::move(build)),capacity(bound),
         configuration(std::move(config)),live(std::move(l)),authority(std::move(q)) {}
    ~State(){if(std::this_thread::get_id()!=thread)std::terminate();}
    void check() const {
        if(std::this_thread::get_id()!=thread || reentered)
            throw std::logic_error("TW list handoff owner mismatch or reentry");
    }
    struct Guard {
        State& state;
        explicit Guard(State& s):state(s) {
            state.check();
            if(state.busy){state.reentered=true;throw std::logic_error("TW list handoff reentered");}
            state.busy=true;
        }
        ~Guard(){state.busy=false;state.reentered=false;}
    };
    bool retained(const Record& record) const {
        check();const auto found=records.find(record.epoch);
        return found!=records.end() && found->second.ticket==record.ticket && found->second.issuer==record.issuer;
    }
    bool tuple_current(const Record& record) {
        check();
        if(!record.ticket || !record.ticket->source_alive() ||
           !auth_valid(record.issuer,ProtocolMode::God2LegacyCharacterListCandidate,4) ||
           !snapshots.owns_sources(accounts,characters))return false;
        const auto& ticket=*record.ticket;
        const auto delivery=ticket.delivery();
        if(!delivery || delivery->account!=record.issuer->account || delivery->session!=record.issuer->session ||
           delivery->selection!=ticket.issuer_scope().selection || ticket.snapshot().client_sha256!=client ||
           ticket.snapshot().account!=delivery->account || ticket.issuer_scope().account!=delivery->account ||
           ticket.issuer_scope().session!=delivery->session)return false;
        const auto account=accounts.find_by_id(delivery->account);check();
        if(!account || account->id!=delivery->account)return false;
        const auto snapshot=snapshots.load(delivery->account,ticket.snapshot().group,ticket.snapshot().server,client);check();
        if(!snapshot || *snapshot!=ticket.snapshot())return false;
        const auto roots=characters.list_for_account(delivery->account);check();
        if(roots.size()!=ticket.roots().size())return false;
        for(std::size_t i=0;i<roots.size();++i)
            if(!NativeWorldEntrySnapshot::same_root(roots[i],ticket.roots()[i]))return false;
        const auto result=live(ticket,*record.issuer);check();return result;
    }
    bool peer_current(Session& session,const Source::Scope& scope,const AuthPtr& auth,const InputPtr& input) {
        check();
        if(!session.native_channel_binding_current())return false;
        const auto local=session.recovered_native_local_endpoint();
        return auth_valid(auth,ProtocolMode::God2CharacterConnection,0) && input && scope.input &&
            local && local->session==session.id() && local->mode==ProtocolMode::God2CharacterConnection && local->port &&
            session.recovered_native_authenticated_input()==auth && session.recovered_native_selection_input()==input &&
            auth->session==session.id() && auth->account==session.account_id &&
            input->session==session.id() && input->account==session.account_id &&
            input->input==*scope.input && input->created==scope.created &&
            scope.token && *scope.token==scope.input->token() &&
            scope.session==session.id() && scope.account==session.account_id &&
            scope.selection==session.recovered_server_selection() &&
            scope.state==SessionState::Authenticated && session.state()==scope.state &&
            !session.closing() && !session.character_id && projects(auth,*scope.input);
    }
    std::optional<RecoveredTaiwanServerAdvertisement::Destination> destination_current(
            Session& session,const Source::Scope& scope,const Record& record,
            RecoveredTaiwanServerAdvertisement::Table table) {
        check();
        const auto& issuer=record.ticket->issuer_scope();
        const auto local=session.recovered_native_local_endpoint();
        const auto configured=configuration->configured_slots(table.group);
        if(!issuer.selection || !issuer.advertised_rows || !scope.token || !local ||
           !configured || !*configured || table.configured_subgroups!=*configured || table.subgroup>=*configured ||
           issuer.selection->request.selector_bytes()!=std::array<std::uint8_t,2>{table.group,table.subgroup} ||
           local->session!=session.id() || local->mode!=ProtocolMode::God2CharacterConnection||
           !session.native_channel_allows_destination(table.group,table.subgroup))return std::nullopt;
        const auto actual=issuer.advertised_rows->primary_destination(table,*scope.token,record.ticket->snapshot().record);
        if(!actual || actual->address()!=local->address || actual->port()!=local->port || !local->port)return std::nullopt;
        return actual;
    }
    void prune() {
        // No iterator/reference survives a repository/provider callback.
        std::vector<Record> values;values.reserve(records.size());
        for(const auto& [key,value]:records)values.push_back(value);
        for(const auto& value:values) {
            const bool keep=value.ticket && value.ticket->active() && tuple_current(value);check();
            if(!keep && retained(value))records.erase(value.epoch);
        }
    }
    std::optional<Match> resolve(Session& session,const Source::Scope& scope,const AuthPtr& auth,const InputPtr& input) {
        if(!peer_current(session,scope,auth,input))return std::nullopt;
        prune();
        std::vector<Record> values;values.reserve(records.size());
        for(const auto& [key,value]:records)values.push_back(value);
        std::optional<Match> match;
        for(const auto& value:values) {
            if(!value.ticket->active() || value.issuer->account!=scope.account ||
               !projects(value.issuer,*scope.input) || !retained(value) || !tuple_current(value))continue;
            auto probe=scope;probe.issued=value.ticket;
            auto qualified=authority(session,probe,*value.ticket,*value.issuer,*auth);check();
            if(!peer_current(session,scope,auth,input))return std::nullopt;
            if(!qualified || !qualified->current)continue;
            const auto count=configuration->configured_slots(qualified->group);
            if(!count || !*count || qualified->subgroup>=*count)continue;
            const RecoveredTaiwanServerAdvertisement::Table table{qualified->group,qualified->subgroup,*count};
            const auto destination=destination_current(session,probe,value,table);
            if(!destination)continue;
            const bool current=qualified->current(session,probe);check();
            if(!peer_current(session,scope,auth,input))return std::nullopt;
            if(!current || !retained(value) || !value.ticket->active() || !tuple_current(value) ||
               destination_current(session,probe,value,table)!=destination)continue;
            if(match)return std::nullopt; // Ambiguity never selects newest/first.
            match=Match{value,std::move(qualified->current),table,*destination};
        }
        if(match && (!retained(match->record) || !match->record.ticket->active() ||
                     !tuple_current(match->record) ||
                     destination_current(session,scope,match->record,match->table)!=match->destination))return std::nullopt;
        if(!peer_current(session,scope,auth,input))return std::nullopt;
        return match;
    }
    bool publish(Session& session,const Source::IssuedPtr& ticket) {
        Guard guard(*this);
        const auto issued=ticket;
        const auto auth=session.recovered_native_authenticated_input();
        if(!issued || issued->active() || !auth_valid(auth,ProtocolMode::God2LegacyCharacterListCandidate,4))return false;
        Record value{0,issued,auth};
        auto issuer_current=[&] {
            check();return !session.closing() && session.state()==SessionState::Authenticated && !session.character_id &&
                session.id()==auth->session && session.account_id==auth->account &&
                session.recovered_native_authenticated_input()==auth &&
                session.recovered_native_character_list_written()==issued->delivery() &&
                session.recovered_server_selection()==issued->issuer_scope().selection;
        };
        if(!issuer_current() || !tuple_current(value))return false;
        prune();
        if(records.size()>=capacity || epoch==std::numeric_limits<std::uint64_t>::max())return false;
        for(const auto& [key,old]:records)if(old.ticket==issued)return false;
        if(!tuple_current(value) || !issuer_current())return false;
        value.epoch=++epoch;records.emplace(value.epoch,std::move(value));
        // Source activates only after this returns and its own full Current.
        return true;
    }
};
std::shared_ptr<SharedTaiwanCharacterListHandoff> SharedTaiwanCharacterListHandoff::create(
    AccountRepository& accounts,RecoveredCharacterRepository& characters,NativeCharacterSummarySnapshotRepository& snapshots,
    std::string client,std::size_t capacity,std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration,
    Live live,Authority authority) {
    if(!configuration || client!=TaiwanNativeClientGroupConfiguration::client_sha256 ||
       !capacity || !live || !authority || !snapshots.owns_sources(accounts,characters) || client.size()!=64 ||
       !std::all_of(client.begin(),client.end(),[](char c){return (c>='0' && c<='9') || (c>='a' && c<='f');}))
        throw std::invalid_argument("TW handoff requires actual readers/build/capacity and lifecycle/selection authority");
    return std::shared_ptr<SharedTaiwanCharacterListHandoff>(new SharedTaiwanCharacterListHandoff(
        std::make_shared<State>(accounts,characters,snapshots,std::move(client),capacity,
            std::move(configuration),std::move(live),std::move(authority))));
}
SharedTaiwanCharacterListHandoff::Binding SharedTaiwanCharacterListHandoff::binding() {
    state_->check();auto state=state_;
    return Binding{[state](Session& session,const Source::IssuedPtr& ticket){
            const auto owner=state;return owner->publish(session,ticket);
        },
        [state](Session& session,const Source::Scope& actual_scope)->std::optional<Source::Link> {
            const auto owner=state;
            const auto scope=actual_scope;
            State::Guard guard(*owner);
            const auto auth=session.recovered_native_authenticated_input();
            const auto input=session.recovered_native_selection_input();
            auto match=owner->resolve(session,scope,auth,input);
            if(!match)return std::nullopt;
            const auto value=match->record;
            return Source::Link{value.ticket,[weak=std::weak_ptr<State>(owner),value,auth,input,
                    table=match->table,destination=match->destination,
                    current=std::move(match->current)](Session& peer,const Source::Scope& actual_probe) {
                auto owner=weak.lock();if(!owner)return false;
                // Providers may drop the caller's facade during invocation.
                // Keep every later-used capture and real Current locally owned.
                const auto record=value;
                const auto authentication=auth;
                const auto selection=input;
                const auto qualified=current;
                const auto probe=actual_probe;
                const auto native_table=table;
                const auto native_destination=destination;
                State::Guard guard(*owner);
                if(probe.issued!=record.ticket || !owner->retained(record) ||
                   !owner->peer_current(peer,probe,authentication,selection))return false;
                const bool accepted=qualified(peer,probe);owner->check();
                if(!accepted || !owner->peer_current(peer,probe,authentication,selection))return false;
                // Re-evaluate all actual candidates, including tickets activated
                // since Link. Checking the old slot alone misses new ambiguity.
                auto fresh=owner->resolve(peer,probe,authentication,selection);
                return fresh && fresh->record.epoch==record.epoch && fresh->record.ticket==record.ticket &&
                    fresh->table==native_table && fresh->destination==native_destination &&
                    owner->retained(record) && owner->peer_current(peer,probe,authentication,selection);
            }};
        }};
}
bool SharedTaiwanCharacterListHandoff::matches_sources(const AccountRepository& accounts,
    const RecoveredCharacterRepository& characters,const NativeCharacterSummarySnapshotRepository& snapshots,
    std::string_view client,std::size_t capacity) const {
    state_->check();return &state_->accounts==&accounts && &state_->characters==&characters &&
        &state_->snapshots==&snapshots && state_->client==client && state_->capacity==capacity;
}
void SharedTaiwanCharacterListHandoff::retire(const Source::IssuedPtr& ticket) {
    State::Guard guard(*state_);
    for(auto it=state_->records.begin();it!=state_->records.end();) {
        if(it->second.ticket==ticket)it=state_->records.erase(it);else ++it;
    }
}
}
