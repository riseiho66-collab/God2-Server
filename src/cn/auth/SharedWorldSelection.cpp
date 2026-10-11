#include "cn/auth/SharedWorldSelection.h"
#include "cn/protocol/CnCharacterEnter.h"
#include "cn/protocol/CnWorldEntry.h"
#include "cn/protocol/CnWorldCharacterList.h"
#include "cn/protocol/CnWorldSelectionStatus.h"
#include "cn/world/SharedSceneIdentity.h"
#include "cn/world/SharedInitialScene.h"
#include <algorithm>
#include <set>
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
struct Wipe {
    std::span<std::uint8_t> bytes;
    ~Wipe(){volatile std::uint8_t* p=bytes.data();for(std::size_t i=0;i<bytes.size();++i)p[i]=0;}
};
void project(std::string_view value,std::array<std::uint8_t,16>& output) {
    // Native strncpy(...,16), followed by explicit byte15=0.
    const auto nul=value.find('\0');
    if(nul!=std::string_view::npos)value=value.substr(0,nul);
    std::copy_n(value.begin(),std::min<std::size_t>(value.size(),15),output.begin());
}
std::string_view text(const std::array<std::uint8_t,16>& value) {
    const auto end=std::find(value.begin(),value.end(),0);
    return {reinterpret_cast<const char*>(value.data()),static_cast<std::size_t>(end-value.begin())};
}
}
SharedWorldSelection::CredentialAlias::CredentialAlias(std::string_view account,std::string_view credential) {
    project(account,account_);project(credential,credential_);
}
SharedWorldSelection::CredentialAlias::~CredentialAlias() {
    Wipe account{account_},credential{credential_};
}
bool SharedWorldSelection::CredentialAlias::matches(std::string_view account,std::string_view credential) const {
    return account==text(account_) && credential==text(credential_);
}
std::optional<SharedWorldSelection::NativeOffer> SharedWorldSelection::NativeOffer::from_native(
    Path path,const god2cn::CnCharacterSummary& summary,std::vector<std::uint64_t> ids,
    god2cn::Bytes list,std::vector<CredentialAlias> aliases) {
    if(path!=Path::Normal && path!=Path::Transfer)return std::nullopt;
    const auto world_list=god2cn::CnWorldCharacterList::read(list);
    if(!world_list || ids.size()!=summary.count() || aliases.empty())return std::nullopt;
    NativeOffer result(path);
    std::set<std::uint8_t> slots;
    std::set<std::uint64_t> unique_ids;
    for(unsigned index=0;index<summary.count();++index) {
        const auto row=summary.character(index);
        if(!row || !ids[index] || !unique_ids.insert(ids[index]).second)return std::nullopt;
        std::uint8_t raw_slot;
        switch(path) {
        case Path::Normal:raw_slot=row->native_slot();break;
        case Path::Transfer: {
            const auto selection=world_list->transfer_selection(summary,index);
            if(!selection)return std::nullopt;
            raw_slot=selection->world_list_slot;break;
        }
        default:return std::nullopt;
        }
        // A clamped0 from an out-of-range advertised slot cannot establish
        // the original server's character mapping. Leave these native
        // variants open instead of inventing a slot0 permission. Never clamp
        // an incoming1A. Duplicate advertised choices are also ambiguous.
        if(raw_slot>=4 || !slots.insert(raw_slot).second)return std::nullopt;
        result.bindings.push_back({raw_slot,ids[index]});
    }
    const auto raw_summary=summary.record_bytes();
    result.summary_record.assign(raw_summary.begin(),raw_summary.end());
    result.source_character_ids=std::move(ids);
    result.list=std::move(list);result.credential_aliases=std::move(aliases);
    return result;
}
void SharedWorldSelection::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN world-selection game owner mismatch");
}
SharedWorldSelection::SharedWorldSelection(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<Admission> admission,
    RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,
    NativeOffer offer,Selected selected,TerminalSource terminal_source,
    SharedCharacterCreateOperation::Sources creation_sources,SharedCharacterDeleteOperation::Sources deletion_sources)
    :connection_(connection),admission_(std::move(admission)),characters_(characters),maps_(maps),account_(connection->verified_account_id()),
     offer_(std::move(offer)),selected_(std::move(selected)),terminal_source_(std::move(terminal_source)),
     creation_sources_(std::move(creation_sources)),deletion_sources_(std::move(deletion_sources)) {
    if(!account_ || !admission_ || connection->role()!=Connection::Transport::Role::World || !selected_ ||
       offer_.list.size()!=125 || offer_.list[0]!=0x1f ||
       offer_.bindings.size()>2 || offer_.credential_aliases.empty())
        throw std::invalid_argument("CN world-selection requires verified world identity/native offer/controller");
    std::set<std::uint8_t> slots;
    std::set<std::uint64_t> ids;
    for(const auto binding:offer_.bindings)
        if(binding.enter_slot>=4 || !binding.character || !slots.insert(binding.enter_slot).second ||
           !ids.insert(binding.character).second)
            throw std::invalid_argument("CN world-selection requires unambiguous qualified slot associations");
}
bool SharedWorldSelection::owns(std::uint64_t character) const {
    const auto connection=connection_.lock();
    if(!connection || connection->closing() || connection->verified_account_id()!=account_ ||
       !connection->world_character_offered(character))return false;
    const auto rows=characters_.list_for_account(account_);
    return std::any_of(rows.begin(),rows.end(),[this,character](const auto& row) {
        return row.id==character && row.account_id==account_;
    });
}
bool SharedWorldSelection::qualify_offer() const {
    const auto connection=connection_.lock();
    if(!connection)return false;
    const auto source=connection->world_offer_source();
    if(!source || source->adapter_record!=offer_.summary_record ||
       source->character_ids!=offer_.source_character_ids)return false;
    for(const auto binding:offer_.bindings)if(!owns(binding.character))return false;
    return true;
}
std::shared_ptr<SharedWorldSelection> SharedWorldSelection::attach(
    const std::shared_ptr<Connection>& connection,std::shared_ptr<Admission> registry,
    std::uint64_t session,Admission::Target endpoint,
    RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,NativeOffer offer,Selected selected,
    Admission::Clock::time_point now,Connection::Transport::Completion queued,TerminalSource terminal_source,
    SharedCharacterCreateOperation::Sources creation_sources,SharedCharacterDeleteOperation::Sources deletion_sources) {
    if(!queued)throw std::invalid_argument("CN world offer queue continuation required");
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(queued));
    const auto finish=[completion](bool accepted) {
        if(!*completion)return;auto done=std::move(*completion);*completion={};done(accepted);
    };
    if(!connection){finish(false);return {};}
    try {
        // This initial1F belongs to the exact fresh World00 verification.
        // Retain only until the held queue publication, not through gameplay.
        // Account04's token/claimed DWORD alone cannot qualify World00.
        const auto request=connection->retain_verified_login_for_publication();
        const auto credentials=connection->retain_verified_credentials(request);
        if(!credentials){finish(false);return {};}
        auto result=std::shared_ptr<SharedWorldSelection>(new SharedWorldSelection(
            connection,registry,characters,maps,std::move(offer),std::move(selected),std::move(terminal_source),
            std::move(creation_sources),std::move(deletion_sources)));
        if(!connection->install_world_ingress(std::move(registry),session,endpoint,
            [result](god2cn::Bytes bytes,Connection::Transport::Completion done) {
                result->receive(std::move(bytes),std::move(done));
            },now)){finish(false);return {};}
        if(!result->qualify_offer()) {connection->close();finish(false);return {};}
        std::vector<god2cn::Bytes> sequence;sequence.push_back(result->offer_.list);
        const auto weak=result->weak_from_this();
        const auto published=std::make_shared<bool>(false);
        const auto account=result->account_,world_session=connection->world_session_id();
        connection->send_world_batch_with_publication(std::move(sequence),
            [weak,published,request,credentials] {
                const auto self=weak.lock();if(!self)return false;self->owner();
                const auto connection=self->connection_.lock();
                if(self->offer_queued_ || self->started_ || self->terminal_started_ ||
                   self->selected_publication_pending_ || self->selected_ingress_ || !self->qualify_offer() ||
                   !connection || !connection->verified_credentials_current(credentials,request))return false;
                self->offer_queued_=true;*published=true;return true;
            },
            [weak,published,account,world_session,finish](bool accepted) {
                const auto self=weak.lock();const auto connection=self?self->connection_.lock():nullptr;
                const bool valid=accepted && *published && self && self->offer_queued_ && connection &&
                    !connection->closing() && connection->verified_account_id()==account &&
                    connection->world_session_id()==world_session;
                // Qualified exact1F was published before IO. No late old-offer
                // root/lease veto after a valid fast selection or mutation.
                if(!valid && connection)connection->close();finish(valid);
            });
        return result;
    }catch(...) {connection->close();finish(false);throw;}
}
std::shared_ptr<SharedWorldSelection::Connection> SharedWorldSelection::connection_for_choice(const Choice& choice,
    const RecoveredCharacterRepository& characters,const NativeMapCatalog& maps) const {
    owner();
    if(&characters_!=&characters || &maps_!=&maps || !started_ || selected_ingress_ || selected_publication_pending_ ||
       pending_character_!=choice.character || account_!=choice.account ||
       offer_.path_!=choice.path || !std::any_of(offer_.bindings.begin(),offer_.bindings.end(),[&](const auto& row) {
           return row.character==choice.character && row.enter_slot==choice.enter_slot;
       }) || !owns(choice.character))return {};
    return connection_.lock();
}
std::optional<SharedCharacterDeleteIdentity> SharedWorldSelection::resolve_deletion_identity(
    std::span<const std::uint8_t> record) {
    owner();
    if(!offer_queued_ || started_ || terminal_started_ || pending_character_ || selected_ingress_ ||
       creation_operation_ || deletion_operation_)return std::nullopt;
    const auto request=god2cn::CnCharacterDelete::read(record);
    const auto connection=connection_.lock();
    if(!request || !connection)return std::nullopt;
    const auto weak=weak_from_this();
    return SharedCharacterDeleteIdentity::resolve(connection,characters_,*request,
        [weak](std::string_view account,std::string_view credential) {
            const auto self=weak.lock();if(!self)return false;self->owner();
            return std::any_of(self->offer_.credential_aliases.begin(),self->offer_.credential_aliases.end(),
                [account,credential](const auto& alias) {return alias.matches(account,credential);});
        },
        [weak] {
            const auto self=weak.lock();if(!self)return false;self->owner();
            return self->offer_queued_ && !self->started_ && !self->terminal_started_ && !self->pending_character_ &&
                !self->selected_ingress_ && !self->creation_operation_ && self->qualify_offer();
        });
}
bool SharedWorldSelection::terminal_scope_current(const SharedPreWorldCloseReply::Scope& scope) const {
    owner();
    const auto connection=connection_.lock();
    using MutationKind=SharedPreWorldCloseReply::MutationKind;
    if(creation_operation_ && deletion_operation_)return false;
    const auto kind=creation_operation_ ? MutationKind::CharacterCreation :
        deletion_operation_ ? MutationKind::CharacterDeletion : MutationKind::None;
    const auto operation=creation_operation_ ? std::static_pointer_cast<const void>(creation_operation_) :
        deletion_operation_ ? std::static_pointer_cast<const void>(deletion_operation_) : std::shared_ptr<const void>{};
    if(scope.mutation_kind!=kind || scope.mutation_owner!=operation)return false;
    // Real committed deletion can invalidate the old offer, while this exact
    // world ticket must remain usable for terminal drain/release. Do not require
    // qualify_offer() or reinterpret an invalidated native07 snapshot here.
    return terminal_started_ && offer_queued_ && !started_ && !pending_character_ && !selected_ingress_ &&
        connection && !connection->closing() && account_==scope.account &&
        connection->verified_account_id()==scope.account && connection->world_session_id()==scope.world_session &&
        connection->world_admission_current();
}
bool SharedWorldSelection::create_scope_current(const SharedCharacterCreateOperation::Scope& scope) const {
    owner();const auto connection=connection_.lock();
    // Creation may invalidate an old07 offer. Actual post-commit continuation
    // uses this exact world-owned ticket and designated request, not old slots.
    return offer_queued_ && !started_ && !terminal_started_ && !pending_character_ && !selected_ingress_ &&
        !deletion_operation_ && creation_operation_ && creation_operation_->scope()==scope && connection && !connection->closing() &&
        account_==scope.account && connection->verified_account_id()==scope.account &&
        connection->world_session_id()==scope.world_session && connection->world_admission_current();
}
bool SharedWorldSelection::delete_scope_current(const SharedCharacterDeleteOperation::Scope& scope) const {
    owner();const auto connection=connection_.lock();
    // SQL can remove this common row and invalidate the retained07. The exact
    // designated attempt/current world ticket survive for02 ->0204 ->03.
    return offer_queued_ && !started_ && !terminal_started_ && !pending_character_ && !selected_ingress_ &&
        !creation_operation_ && deletion_operation_ && deletion_operation_->scope()==scope &&
        connection && !connection->closing() && account_==scope.account &&
        connection->verified_account_id()==scope.account && connection->world_session_id()==scope.world_session &&
        connection->world_admission_current();
}
void SharedWorldSelection::receive_delete(std::optional<SharedCharacterDeleteIdentity> identity,
    Connection::Transport::Completion done) {
    owner();const auto connection=connection_.lock();
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    const auto weak=weak_from_this();
    const auto finish=[weak,completion](bool accepted) {
        if(!*completion)return;
        const auto self=weak.lock();
        // A whole nonzero02 completed without mutation. Release only that
        // attempt; a later native request resolves a fresh current identity.
        // This does not qualify every native error/recovery UI branch.
        if(accepted && self && self->deletion_operation_ && self->deletion_operation_->failure_reply_complete())
            self->deletion_operation_.reset();
        auto callback=std::move(*completion);*completion={};callback(accepted);
    };
    try {
        if(!connection || !identity || !deletion_sources_ || creation_operation_ || deletion_operation_ ||
           !offer_queued_ || started_ || terminal_started_ || pending_character_ || selected_ingress_ ||
           !identity->current() || !qualify_offer()) {
            if(connection)connection->close();finish(false);return;
        }
        auto operation=SharedCharacterDeleteOperation::prepare(connection,characters_,admission_,
            std::move(*identity),deletion_sources_,[weak](const SharedCharacterDeleteOperation::Scope& scope) {
                const auto self=weak.lock();return self && self->delete_scope_current(scope);
            });
        if(!operation || !qualify_offer()) {connection->close();finish(false);return;}
        deletion_operation_=std::move(operation);
        deletion_operation_->start(finish);
    }catch(...) {if(connection)connection->close();finish(false);}
}
void SharedWorldSelection::receive_create(god2cn::CnCharacterCreate request,
    Connection::Transport::Completion done) {
    owner();const auto connection=connection_.lock();
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[completion](bool accepted) {
        if(!*completion)return;auto callback=std::move(*completion);*completion={};callback(accepted);
    };
    // No wire name, opaque tuple or client-only filter grants permission. The
    // required sources perform actual native rules/common transactions/replay.
    try {
        if(!connection || !creation_sources_ || !offer_queued_ || started_ || terminal_started_ ||
           pending_character_ || selected_ingress_ || deletion_operation_ || !qualify_offer() ||
           (creation_operation_ && !creation_operation_->retry_available())) {
            if(connection)connection->close();finish(false);return;
        }
        const auto weak=weak_from_this();
        auto operation=SharedCharacterCreateOperation::prepare(connection,characters_,
            std::make_shared<const god2cn::CnCharacterCreate>(std::move(request)),creation_sources_,
            [weak](const SharedCharacterCreateOperation::Scope& scope) {
                const auto self=weak.lock();return self && self->create_scope_current(scope);
            });
        if(!operation || !qualify_offer()) {connection->close();finish(false);return;}
        // Designate before invoking the writer so synchronous callback/re-entry
        // cannot get another request's scope or reuse a previous retry result.
        creation_operation_=std::move(operation);
        creation_operation_->start(finish);
    }catch(...) {if(connection)connection->close();finish(false);}
}
void SharedWorldSelection::receive_close(god2cn::CnPreWorldCloseControl control,
    Connection::Transport::Completion done) {
    owner();
    const auto connection=connection_.lock();
    if(!connection || !terminal_source_ || !offer_queued_ || started_ || terminal_started_ ||
       pending_character_ || selected_ingress_ || !connection->world_admission_current() ||
       (creation_operation_ && deletion_operation_) ||
       (creation_operation_ && !creation_operation_->terminal_quiescent()) ||
       (deletion_operation_ && !deletion_operation_->terminal_quiescent())) {
        if(connection)connection->close();done(false);return;
    }
    using MutationKind=SharedPreWorldCloseReply::MutationKind;
    const auto kind=creation_operation_ ? MutationKind::CharacterCreation :
        deletion_operation_ ? MutationKind::CharacterDeletion : MutationKind::None;
    const auto operation=creation_operation_ ? std::static_pointer_cast<const void>(creation_operation_) :
        deletion_operation_ ? std::static_pointer_cast<const void>(deletion_operation_) : std::shared_ptr<const void>{};
    const SharedPreWorldCloseReply::Scope scope{account_,connection->world_session_id(),control.form,kind,operation};
    // Take the exclusive terminal stage before invoking any source callback.
    // Transport keeps this ingress suspended until local drain completion.
    terminal_started_=true;
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[completion](bool written) {
        if(!*completion)return;
        auto acknowledge=std::move(*completion);*completion={};acknowledge(written);
    };
    try {
        auto supplied=terminal_source_(scope);
        if(!supplied || !terminal_scope_current(scope) || !supplied->current(scope)) {
            connection->close();finish(false);return;
        }
        auto reply=std::make_shared<const SharedPreWorldCloseReply>(std::move(*supplied));
        const auto record=reply->record_bytes();
        const auto weak=weak_from_this();
        offer_.credential_aliases.clear();
        god2cn::Bytes native(record.begin(),record.end());
        connection->close_after_native_world_reply(std::move(native),
            [weak,scope,reply] {
                const auto self=weak.lock();
                return self && self->terminal_scope_current(scope) && reply->current(scope);
            },finish);
        // Completion intentionally does not recheck closing/ticket after drain:
        // the existing transport is closing and cleanup may already have run.
        // Its boolean is local TCP write completion, never native acceptance.
    }catch(...) {connection->close();finish(false);}
}
bool SharedWorldSelection::install_selected_ingress(std::uint64_t character,
    const RecoveredPosition& position,
    const std::optional<RecoveredPosition>& previous,
    god2cn::Bytes status,god2cn::Bytes begin,const std::shared_ptr<SharedWorldReady>& ready,
    const std::shared_ptr<SharedInitialScene>& scene,Publication current_preparation,
    Connection::Transport::Completion queued) {
    owner();
    if(!queued)throw std::invalid_argument("CN selected world queue continuation required");
    const auto connection=connection_.lock();
    if(!started_ || !pending_character_ || character!=pending_character_ || selected_ingress_ ||
       selected_publication_pending_ || !current_preparation ||
       !connection || connection->closing() || !ready || !owns(character) ||
       ((offer_.path_==NativeOffer::Path::Transfer)!=previous.has_value()))return false;
    const auto result=god2cn::CnWorldSelectionStatus::read(status);
    const auto entry=god2cn::CnWorldEntry::read_begin_play(begin);
    if(!result || result->status!=0 || !entry || !ready->matches(connection,character,position,entry->actor_handle()))return false;
    const auto map=maps_.lookup(NativeMapCatalog::current_dataset_id,position.area,position.scene);
    if(!map || !SharedSceneIdentity::matches(*map,position,*entry,previous))return false;
    if(offer_.path_==NativeOffer::Path::Normal) {
        if(!scene || !scene->matches(connection,ready,character,position,begin))return false;
    } else if(scene)return false; // Initial load-flag1 is not transfer lifecycle evidence.
    // 0047E4D0 consumes02 first; its receiver cursor clear preserves the
    // transport aggregate remainder subsequently consumed by00481190.
    // Complete records only: never split a native record across aggregates.
    status.insert(status.end(),begin.begin(),begin.end());
    auto ingress=ready->ingress(); // Allocate BEFORE publication, retain exact ready.
    std::vector<god2cn::Bytes> sequence;sequence.push_back(std::move(status));
    const auto published=std::make_shared<bool>(false);
    const auto account=account_,session=connection->world_session_id();
    const auto current=[weak=weak_from_this(),character,position,previous,ready,scene,begin,account,session,
                        handle=entry->actor_handle()] {
        const auto self=weak.lock();if(!self)return false;self->owner();
        const auto connection=self->connection_.lock();
        if(!self->selected_publication_pending_ || !self->started_ || self->terminal_started_ ||
           self->pending_character_!=character || self->selected_ingress_ || !connection || connection->closing() ||
           connection->verified_account_id()!=account || connection->world_session_id()!=session ||
           !self->owns(character) || !ready->matches(connection,character,position,handle))return false;
        const auto native=god2cn::CnWorldEntry::read_begin_play(begin);
        const auto map=self->maps_.lookup(NativeMapCatalog::current_dataset_id,position.area,position.scene);
        if(!native || !map || !SharedSceneIdentity::matches(*map,position,*native,previous))return false;
        return self->offer_.path_==NativeOffer::Path::Normal?
            scene && scene->matches(connection,ready,character,position,begin):!scene;
    };
    selected_publication_pending_=true;
    if(!current() || !current_preparation(PublicationCheck::BeforePublish) || !current()) {
        selected_publication_pending_=false;return false;
    }
    connection->send_world_batch_with_publication(std::move(sequence),
        [weak=weak_from_this(),current,current_preparation=std::move(current_preparation),
         ingress=std::move(ingress),ready,scene,published]() mutable {
            const auto self=weak.lock();if(!self || !current() ||
                !current_preparation(PublicationCheck::QueueAccepted) || !current())return false;
            // Publish this exact ready/scene dispatcher BEFORE IO release.
            // Move preallocated ingress; no callback/allocation after transition.
            self->selected_ingress_=std::move(ingress);self->selected_ready_=ready;self->normal_scene_=scene;
            self->selected_publication_pending_=false;*published=true;return true;
        },
        [weak=weak_from_this(),ready,scene,published,account,session,queued=std::move(queued)](bool accepted) mutable {
            const auto self=weak.lock();const auto connection=self?self->connection_.lock():nullptr;
            const bool valid=accepted && *published && self && self->selected_ingress_ &&
                self->selected_ready_==ready && self->normal_scene_==scene && connection && !connection->closing() &&
                connection->verified_account_id()==account && connection->world_session_id()==session;
            // Initial-ready may already have progressed. Never recheck its
            // pre-entry stage/position or revoke a valid active incarnation.
            if(!valid && self) {
                self->selected_publication_pending_=false;
                if(self->selected_ready_==ready) {
                    self->selected_ingress_={};self->selected_ready_.reset();self->normal_scene_.reset();
                }
                if(connection)connection->close();
            }
            queued(valid);
        });
    return true;
}
void SharedWorldSelection::receive(god2cn::Bytes bytes,Connection::Transport::Completion done) {
    owner();
    if(!done)throw std::invalid_argument("CN world-selection completion required");
    const auto connection=connection_.lock();
    if(!connection || connection->closing()) {Wipe clear{bytes};done(false);return;}
    if(selected_ingress_) {selected_ingress_(std::move(bytes),std::move(done));return;}
    Wipe clear{bytes};
    if(started_ || terminal_started_) {done(false);return;}
    if(const auto control=god2cn::CnPreWorldCloseControl::read(bytes)) {
        receive_close(*control,std::move(done));return;
    }
    if(!bytes.empty() && bytes[0]==0x19) {
        auto identity=resolve_deletion_identity(bytes);
        // Resolver's native19 temporary is already destroyed. Erase ingress
        // credentials before the actual rule/storage supplier is called.
        volatile std::uint8_t* raw=bytes.data();
        for(std::size_t i=0;i<bytes.size();++i)raw[i]=0;
        receive_delete(std::move(identity),std::move(done));return;
    }
    // Successful removal awaits its actual native terminal source. Repeated19,
    // creation and1A cannot reuse a committed attempt or an invalidated07.
    if(deletion_operation_) {done(false);return;}
    if(!bytes.empty() && bytes[0]==0x17) {
        const auto request=god2cn::CnCharacterCreate::read(bytes);
        if(!request) {done(false);return;}
        receive_create(*request,std::move(done));return;
    }
    if(creation_operation_) {
        // Retain the original17 owner through18. Special1B, repeated18 and
        // unrelated1A cannot borrow this operation or replace its common ID.
        // Ordinary0043D280 success18 closes world(0200/03) and account(0A),
        // then00440CA0 reauthenticates/reselects on fresh connections. A new
        // role must not borrow the old grant merely to accept1A here. Other
        // callers, including standalone0043D580, remain separately qualified.
        creation_operation_->receive_choice(bytes,std::move(done));return;
    }
    const auto request=god2cn::CnCharacterEnter::read(bytes);
    if(!request || !std::any_of(offer_.credential_aliases.begin(),offer_.credential_aliases.end(),
        [&request](const auto& alias) {return alias.matches(request->account(),request->credential());})) {
        done(false);return;
    }
    const auto binding=std::find_if(offer_.bindings.begin(),offer_.bindings.end(),[&request](const auto& row) {
        return row.enter_slot==request->slot();
    });
    if(binding==offer_.bindings.end()) {done(false);return;}
    try {if(!owns(binding->character)) {done(false);return;}}
    catch(...) {done(false);return;}
    started_=true;pending_character_=binding->character;
    // The selected callback receives only owned common IDs. The truncated
    // echo never reauthenticates, resolves an account or changes its password.
    offer_.credential_aliases.clear();
    const auto weak=weak_from_this();
    // The real preparation owner may finish asynchronously. Share the single
    // completion across its copy and the synchronous exception path.
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[weak,completion](bool accepted) mutable {
        if(!*completion)return;
        auto acknowledge=std::move(*completion);*completion={};
        const auto self=weak.lock();
        if(!self){acknowledge(false);return;}
        self->owner();
        bool valid=false;
        try {
            const auto connection=self->connection_.lock();
            valid=accepted && self->selected_ingress_ && self->selected_ready_ && connection && !connection->closing() &&
                connection->verified_account_id()==self->account_ && connection->world_session_id();
        }
        catch(...) {valid=false;}
        acknowledge(valid);
    };
    try {selected_(shared_from_this(),Choice{account_,binding->character,binding->enter_slot,offer_.path_},finish);}
    catch(...) {finish(false);}
}
}
