#include "game/SharedTaiwanNativeCharacterOfferSource.h"
#include "game/TaiwanNativeClientGroupConfiguration.h"
#include "db/NativeWorldEntrySnapshotRepository.h"
#include "text/OwnedCharacterNameText.h"
#include <algorithm>
#include <set>
#include <stdexcept>
#include <thread>

namespace god2 {
namespace {
using OfferSource=SharedTaiwanNativeCharacterOfferSource;
bool origin(std::string_view hash,std::string_view row) {
    return hash.size()==64 && std::all_of(hash.begin(),hash.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    }) && !row.empty() && row.size()<=2048 && row.find('\0')==row.npos;
}
bool shape(const OfferSource::Snapshot& snapshot) {
    if(!snapshot.account || !snapshot.revision || snapshot.client_sha256!=TaiwanNativeClientGroupConfiguration::client_sha256 ||
       !origin(snapshot.source_sha256,snapshot.source_record) || snapshot.record.size()!=75 ||
       snapshot.record[0]!=7 || snapshot.rows.size()>2 || snapshot.record[1]!=snapshot.rows.size())return false;
    std::set<std::uint64_t> ids;std::set<std::uint8_t> tokens;
    for(std::size_t i=0;i<snapshot.rows.size();++i) {
        const auto& row=snapshot.rows[i];const auto at=3+36*i;
        const auto end=std::find(snapshot.record.begin()+at,snapshot.record.begin()+at+16,0);
        const auto token=static_cast<std::uint8_t>(snapshot.record[at+19]&7);
        if(!row.character || !ids.insert(row.character).second || row.role ||
           row.name_source!=NativeCharacterSummarySnapshot::NameSource::CommonIdentity ||
           end==snapshot.record.begin()+at || end==snapshot.record.begin()+at+16 ||
           token>3 || !tokens.insert(token).second)return false;
    }
    return true;
}
bool same_roots(std::span<const RecoveredCharacter> a,std::span<const RecoveredCharacter> b,std::uint64_t account) {
    if(a.size()!=b.size())return false;
    std::set<std::uint64_t> ids;
    for(std::size_t i=0;i<a.size();++i)
        if(!a[i].id || a[i].account_id!=account || !ids.insert(a[i].id).second ||
           !NativeWorldEntrySnapshot::same_root(a[i],b[i]))return false;
    return true;
}
bool names(const OfferSource::Snapshot& snapshot,std::span<const RecoveredCharacter> roots) {
    for(std::size_t i=0;i<snapshot.rows.size();++i) {
        const auto id=snapshot.rows[i].character;
        const auto root=std::find_if(roots.begin(),roots.end(),[&](const auto& row){return row.id==id;});
        if(root==roots.end() || root->account_id!=snapshot.account)return false;
        const auto end=std::find(root->profile.begin(),root->profile.begin()+15,0);
        if(end==root->profile.begin() || end==root->profile.begin()+15)return false;
        const auto original=OwnedCharacterNameText::from_encoded(std::string(root->profile.begin(),end),root->name_codepage);
        const auto tw=original?OwnedCharacterNameText::from_utf8(original->original_utf8(),950):std::nullopt;
        if(!tw)return false; // page0 ASCII only; never infer950 for unbound names.
        const auto at=snapshot.record.begin()+3+36*i;
        const auto finish=std::find(at,at+16,0);
        if(std::string(at,finish)!=tw->encoded_bytes())return false;
    }
    return true;
}
struct State {
    SqliteNativeCharacterSummarySnapshotRepository& writer;
    AccountRepository& accounts;
    RecoveredCharacterRepository& characters;
    const std::string client;
    OfferSource::Supply supply;
    const std::thread::id thread=std::this_thread::get_id();
    bool busy=false,reentered=false;
    void check() const {
        if(thread!=std::this_thread::get_id() || reentered)
            throw std::logic_error("TW offer source owner/reentry mismatch");
    }
    struct Guard {
        State& state;
        explicit Guard(State& s):state(s) {
            state.check();if(state.busy){state.reentered=true;throw std::logic_error("TW offer source reentered");}
            state.busy=true;
        }
        ~Guard(){state.busy=false;state.reentered=false;}
    };
};
}
std::optional<SharedTaiwanNativeCharacterOfferSource::Offer>
SharedTaiwanNativeCharacterOfferSource::Offer::from_actual_source(Snapshot next,Issuer current) {
    if(!current || !shape(next))return std::nullopt;
    return Offer(std::move(next),std::move(current));
}
SharedTaiwanNativeCharacterListSource::Prepare SharedTaiwanNativeCharacterOfferSource::create(
    SqliteNativeCharacterSummarySnapshotRepository& writer,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,std::string client,Supply supply) {
    if(!writer.owns_sources(accounts,characters) || client!=TaiwanNativeClientGroupConfiguration::client_sha256 || !supply)
        throw std::invalid_argument("TW offer source requires exact shared writer/readers/build and actual issuer");
    auto state=std::make_shared<State>(State{writer,accounts,characters,std::move(client),std::move(supply)});
    return [state](Session& session,const Source::Scope& input,const Source::Target& destination,
                  std::span<const RecoveredCharacter> input_roots,const std::function<bool()>& parent_current) {
        const auto owner=state;State::Guard guard(*owner);
        const auto scope=input;const auto target=destination;const auto current=parent_current;
        const std::vector<RecoveredCharacter> roots(input_roots.begin(),input_roots.end());
        const auto ready=[&] {
            owner->check();
            if(!current || !owner->writer.owns_sources(owner->accounts,owner->characters) ||
               !scope.session || !scope.account || scope.session!=session.id() || scope.account!=session.account_id ||
               scope.state!=SessionState::Authenticated || session.state()!=scope.state || session.closing() || session.character_id ||
               !same_roots(roots,owner->characters.list_for_account(scope.account),scope.account))return false;
            const bool accepted=current();owner->check();
            return accepted && same_roots(roots,owner->characters.list_for_account(scope.account),scope.account);
        };
        if(!ready())return false;
        auto expected=owner->writer.load(scope.account,target.group,target.server,owner->client);
        if(!ready())return false;
        auto supplied=owner->supply(session,scope,target,roots,expected);owner->check();
        if(!supplied || !ready())return false;
        const auto offer=std::make_shared<Offer>(std::move(*supplied));
        const auto next=offer->next_;
        if(!shape(next) || next.account!=scope.account || next.group!=target.group || next.server!=target.server ||
           next.client_sha256!=owner->client || (expected && next.revision<=expected->revision) || !names(next,roots))return false;
        // All captures are owned for this synchronous transaction. In staged
        // BeforeCommit the parent guard observes session/roots/target/poison,
        // not snapshots.load==expected. The writer owns fulltuple CAS checks.
        auto committed=owner->writer.replace_from_issuer(std::move(expected),next,
            [&](const std::optional<Snapshot>& before,const Snapshot& actual,
                SqliteNativeCharacterSummarySnapshotRepository::WriteCheck check,
                std::span<const RecoveredCharacter> actual_roots) {
                if(actual!=next || !same_roots(roots,actual_roots,scope.account) || !names(actual,actual_roots) || !ready())return false;
                const auto issuer=offer->current_; // Keep callable alive across external callbacks.
                const bool accepted=issuer(before,actual,check,actual_roots);owner->check();
                return accepted && ready();
            });
        // No post-COMMIT provider/reload/retry: later List Current can fail,
        // which suppresses publication but cannot undo a durable replacement.
        return committed && *committed==next;
    };
}
}
