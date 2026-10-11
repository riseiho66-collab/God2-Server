#include "cn/world/SharedWorldGameplay.h"
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedWorldGameplay::SharedWorldGameplay(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    std::shared_ptr<SharedActorVisibility> visibility,Sources sources,bool mode)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),
     visibility_(std::move(visibility)),sources_(std::move(sources)),native_mode_(mode) {}
SharedWorldGameplay::~SharedWorldGameplay() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    if(inline_role_release_)try {inline_role_release_();}catch(...) {}
    if(skill_book_release_)try {skill_book_release_();}catch(...) {}
    if(battle_skill_release_)try {battle_skill_release_();}catch(...) {}
    if(battle_command_release_)try {battle_command_release_();}catch(...) {}
    if(spectator_release_)try {spectator_release_();}catch(...) {}
}
void SharedWorldGameplay::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN gameplay game owner mismatch");
}
bool SharedWorldGameplay::current() const {
    const auto connection=connection_.lock();
    if(!connection || connection->closing() || connection->world_session_id()!=lease_.session ||
       connection->verified_account_id()!=lease_.account || !connection->world_character_offered(lease_.character) ||
       !presence_->ready(lease_))return false;
    const auto source=connection->world_offer_source();if(!source)return false;
    const auto summary=god2cn::CnCharacterSummary::read(source->adapter_record);
    return summary && summary->native_mode_bit0()==native_mode_;
}
std::shared_ptr<SharedWorldReady> SharedWorldGameplay::compose(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    std::shared_ptr<SharedActorVisibility> visibility,Sources sources) {
    if(!connection || !presence || !visibility || !visibility->owns_presence(presence) ||
       (sources.world_transports && !sources.world_transports->owns_presence(presence)) ||
       !sources.bootstrap || !sources.entered || !sources.background || !sources.movement_rules ||
       (bool(sources.movement)==bool(sources.prepare_movement)) || !sources.directory ||
       !sources.chat || !sources.chat_text)return {};
    if(sources.preborn_choices && sources.preborn_windows)return {};
    if(sources.subject_roster && (sources.subject_status || sources.subject_skills))return {};
    if(sources.inline_role_counters && (!sources.world_transports ||
       !sources.inline_role_counters->owns_source(presence,sources.world_transports)))return {};
    if(sources.spectator && (!sources.world_transports || !sources.spectator_budgets.max_reply_records ||
       !sources.spectator_budgets.max_reply_logical_bytes))return {};
    if(sources.spectator_publication && (!sources.world_transports ||
       !sources.spectator_publication->owns_source(presence,sources.world_transports)))return {};
    if(sources.spectator_targets && (!sources.spectator_publication ||
       !sources.spectator_targets->owns_source(presence,sources.world_transports,sources.spectator_publication)))return {};
    if(sources.spectator_close_owner && (!sources.spectator || !sources.spectator_publication))return {};
    if(sources.battle_skill_publication && (!sources.world_transports ||
       !sources.battle_skill_publication->owns_source(presence,sources.world_transports)))return {};
    if(bool(sources.skill_books)!=bool(sources.skill_book_source) ||
       bool(sources.skill_books)!=bool(sources.stored_skill_book_source) ||
       bool(sources.skill_books)!=bool(sources.skill_book_catalog))return {};
    if(sources.skill_books &&
       (!sources.skill_book_source->uses_shared_catalog(*sources.skill_book_catalog) ||
        !sources.stored_skill_book_source->uses_native_books(*sources.skill_book_source)))return {};
    if((sources.skill_books || sources.item_control) && (!sources.world_transports ||
       !sources.skill_book_budgets.max_reply_records || sources.skill_book_budgets.max_reply_records>256 ||
       !sources.skill_book_budgets.max_reply_logical_bytes))return {};
    if(unsigned(bool(sources.battle_commands))+unsigned(bool(sources.grouped_battle_commands))+
       unsigned(bool(sources.battle_command_data))>1)return {};
    if((sources.battle_commands || sources.grouped_battle_commands || sources.battle_command_data) && (!sources.world_transports ||
       !sources.battle_command_budgets.max_reply_records ||
       sources.battle_command_budgets.max_reply_records>256 ||
       !sources.battle_command_budgets.max_reply_logical_bytes))return {};
    if((sources.grouped_battle_commands || sources.battle_command_data) && (!sources.battle_command_group_budgets.max_request_records ||
       sources.battle_command_group_budgets.max_request_logical_bytes<god2cn::CnBattleCommand35::logical_size))return {};
    if(sources.battle_command_data) {
        const auto& data=*sources.battle_command_data;
        if(!data.catalog.skills || !data.catalog.shared_reader || !data.catalog.actual_store_lifetime ||
           !data.inventory || !data.authority || !data.budgets.max_requests || !data.budgets.max_inventory_records)return {};
        if(data.skill_selection && (!data.skill_selection->source || !data.skill_selection->read ||
           !data.skill_selection->source->owns_catalog(data.catalog.skills)))return {};
        if(sources.battle_skill_publication && !sources.battle_skill_publication->owns_catalog(data.catalog))return {};
    }
    const auto offer=connection->world_offer_source();if(!offer)return {};
    const auto summary=god2cn::CnCharacterSummary::read(offer->adapter_record);if(!summary)return {};
    const auto mode=summary->native_mode_bit0();
    if(!mode && (!sources.generic_directory || !sources.special_directory))return {};
    auto self=std::shared_ptr<SharedWorldGameplay>(new SharedWorldGameplay(connection,presence,lease,visibility,
        std::move(sources),mode));
    self->owner();
    // Ready retains this gameplay composition. Same lease/generation/registry
    // and cleanup are installed by the existing readiness owner, not duplicated.
    auto ready=SharedWorldReady::attach(connection,std::move(presence),lease,std::move(visibility),
        self->sources_.bootstrap,self->sources_.entered,
        [self] {self->owner();return self->initialize();},
        [self](god2cn::Bytes bytes,Connection::Transport::Completion done) {
            self->receive(std::move(bytes),std::move(done));
        },self->sources_.release_world,self->sources_.world_transports);
    if(!ready)return {};
    self->release_native_transport_=[weak=std::weak_ptr<SharedWorldReady>(ready)] {
        if(const auto ready=weak.lock())ready->release_native_transport();
    };
    return ready;
}
bool SharedWorldGameplay::initialize() {
    if(!current())return false;
    if(initialized_)return true;
    const auto connection=connection_.lock();
    auto movement_owner=sources_.movement?sources_.movement:sources_.prepare_movement();
    if(!movement_owner || !current())return false;
    prepared_movement_=movement_owner;
    auto movement=SharedMovement::attach(connection,presence_,lease_,*sources_.movement_rules,visibility_,*movement_owner);
    auto directory=SharedDirectory::attach(connection,presence_,lease_,*sources_.directory);
    auto chat=SharedNativeChat::attach(connection,presence_,lease_,visibility_,sources_.chat,sources_.chat_text,sources_.world_transports);
    if(!movement || !directory || !chat)return false;
    Connection::Ingress generic,special;
    if(!native_mode_) {
        auto g=SharedGenericDirectory::attach(connection,presence_,lease_,*sources_.generic_directory);
        auto s=SharedSpecialDirectory::attach(connection,presence_,lease_,*sources_.special_directory);
        if(!g || !s)return false;
        generic=g->ingress();special=s->ingress();
    }
    movement_=movement->ingress();directory_=directory->ingress();
    chat_=chat->ingress();
    chat_invalidate_=[chat]{chat->invalidate_active();};
    generic_directory_=std::move(generic);special_directory_=std::move(special);
    if(sources_.post_world_exit) {
        auto exit=SharedPostWorldExit::attach(connection,presence_,lease_,sources_.post_world_exit);
        if(!exit)return false;post_world_exit_=exit->ingress();
    }
    if(sources_.preborn_choices || sources_.preborn_windows) {
        auto choices=sources_.preborn_windows?
            SharedPrebornChoices::attach_window(connection,presence_,lease_,*sources_.preborn_windows):
            SharedPrebornChoices::attach(connection,presence_,lease_,*sources_.preborn_choices);
        if(!choices)return false;preborn_choices_=choices->ingress();
        if(sources_.preborn_windows && !sources_.preborn_windows->bind(choices,lease_))return false;
    }
    if(sources_.subject_skills && !sources_.subject_skills->bind(connection,presence_,lease_))return false;
    if(sources_.subject_status && !sources_.subject_status->bind(connection,presence_,lease_))return false;
    if(sources_.subject_roster && !sources_.subject_roster->bind(connection,presence_,lease_))return false;
    if(sources_.inline_role_counters) {
        const auto source=sources_.inline_role_counters;
        if(!source->bind(connection,lease_))return false;
        inline_role_invalidate_=[source]{source->invalidate_active();};
        inline_role_release_=[source]{source->release();};
    }
    if(sources_.battle_skill_publication) {
        const auto source=sources_.battle_skill_publication;
        if(!source->bind(connection,lease_))return false;
        // Initial readiness has not yet bound the native transport registry.
        // The actual committed-event publisher acquires its private Token on
        // first ready publication. Retire only its own pending operation.
        battle_skill_invalidate_=[source]{source->invalidate_active();};
        battle_skill_release_=[source]{source->release();};
    }
    if(sources_.spectator) {
        auto binding=SharedNativeSpectatorSource::create(connection,presence_,lease_,sources_.world_transports,
            sources_.spectator,sources_.spectator_budgets,sources_.spectator_publication,sources_.spectator_targets,
            sources_.spectator_close_owner);
        if(!binding.ingress || !binding.invalidate_active || !binding.release ||
           (bool(binding.close_ingress)!=bool(sources_.spectator_close_owner)))return false;
        // Initial1C has not yet bound the ready transport registry. The real
        // child captures only this connection/lease and acquires its exact
        // private registration lazily on the first actual ready request.
        spectator_=std::move(binding.ingress);
        spectator_close_=std::move(binding.close_ingress);
        spectator_invalidate_=std::move(binding.invalidate_active);
        spectator_release_=std::move(binding.release);
    }
    auto battle_owner=sources_.battle_commands;
    auto grouped_authority=sources_.grouped_battle_commands;
    if(sources_.battle_command_data) {
        grouped_authority=SharedNativeBattleCommandData::create(connection,lease_,sources_.world_transports,
            *sources_.battle_command_data);
        if(!grouped_authority)return false;
    }
    if(grouped_authority) {
        battle_owner=SharedNativeBattleCommandGroups::create(connection,lease_,sources_.world_transports,
            std::move(grouped_authority),sources_.battle_command_group_budgets);
        if(!battle_owner)return false;
    }
    if(battle_owner) {
        auto binding=SharedNativeBattleCommandSource::create(connection,presence_,lease_,sources_.world_transports,
            std::move(battle_owner),sources_.battle_command_budgets);
        if(!binding.ingress || !binding.invalidate_active || !binding.release)return false;
        // Initial readiness has not yet registered this transport. The child
        // captures the exact ready registration on its first actual command.
        battle_commands_=std::move(binding.ingress);
        battle_command_invalidate_=std::move(binding.invalidate_active);
        battle_command_release_=std::move(binding.release);
    }
    if(sources_.skill_books || sources_.item_control) {
        auto binding=SharedNativeSkillBookUseSource::create(connection,presence_,lease_,sources_.world_transports,
            sources_.skill_book_source,sources_.stored_skill_book_source,sources_.skill_books,
            sources_.skill_book_budgets,sources_.item_control);
        if(bool(binding.ingress)!=bool(sources_.skill_books) ||
           bool(binding.control_ingress)!=bool(sources_.item_control) ||
           !binding.invalidate_active || !binding.release)return false;
        skill_books_=std::move(binding.ingress);item_control_=std::move(binding.control_ingress);
        skill_book_invalidate_=std::move(binding.invalidate_active);
        skill_book_release_=std::move(binding.release);
    }
    initialized_=true;return current();
}
bool SharedWorldGameplay::split(std::span<const std::uint8_t> bytes,std::vector<Record>& records) const {
    if(bytes.empty() || bytes.size()>god2cn::CnTransport::max_logical)return false;
    for(std::size_t offset=0;offset<bytes.size();) {
        const auto rest=bytes.subspan(offset);
        std::size_t size=0;Target target;
        switch(rest[0]) {
        case god2cn::CnBattleCommand35::opcode: {
            size=god2cn::CnBattleCommand35::logical_size;target=Target::BattleCommand;
            if(!battle_commands_ || rest.size()<size ||
               !god2cn::CnBattleCommand35::decode(rest.first(size)))return false;
            // Copy all17 bytes before any effect. Padding/type/target field
            // are raw native fields, not grant or authority qualifications.
            break;
        }
        case 0xa3:case 0xcb: {
            size=god2cn::CnSpectatorClose::logical_size;target=Target::SpectatorClose;
            if(!spectator_close_ || rest.size()<size ||
               !god2cn::CnSpectatorClose::decode(rest.first(size)))return false;
            break;
        }
        case god2cn::CnSpectator6E::opcode: {
            size=god2cn::CnSpectator6E::logical_size;target=Target::Spectator;
            if(!spectator_ || rest.size()<size)return false;
            const auto request=god2cn::CnSpectator6E::decode(rest.first(size));
            if(!request || !god2cn::CnSpectator6E::observed_producer_shape(*request))return false;
            break;
        }
        case 0x81:case 0x83: {
            if(!preborn_choices_)return false;
            const auto length=god2cn::CnPrebornChoices::request_size(rest);
            if(!length || !god2cn::CnPrebornChoices::read_request(rest.first(*length)))return false;
            size=*length;target=Target::PrebornChoices;break;
        }
        case 0x25:
            size=god2cn::CnSkillBookUse25::logical_size;target=Target::SkillBookUse;
            if(!skill_books_ || rest.size()<size ||
               !god2cn::CnSkillBookUse25::decode(rest.first(size)))return false;
            break;
        case 0x1f:
            size=2;target=Target::ItemControl;
            if(!item_control_ || rest.size()<size ||
               !god2cn::CnSkillBookUse25::read_control1f(rest.first(size)))return false;
            break;
        case 0x02:
            size=2;target=Target::PostWorldExit;
            //Terminal record must be LAST. Shape-qualify complete aggregate
            //before any prefix effect; later requests never run after drain.
            if(!post_world_exit_ || rest.size()!=size ||
               !god2cn::CnPostWorldExitControl::read(rest.first(size)))return false;
            break;
        case 0x2f:
            if(rest.size()<3)return false;
            size=std::size_t(rest[1])+256u*rest[2];target=Target::Chat;
            if(size>rest.size() || !SharedNativeChat::supported_request(rest.first(size)))return false;
            break;
        case 0x2e:
            size=7;target=Target::Movement;
            if(rest.size()<size || !god2cn::CnMovement::parse_step(rest.first(size)))return false;
            break;
        case 0x94:
            size=god2cn::CnDirectoryWire::request_size;
            if(rest.size()<size)return false;
            if(god2cn::CnDirectoryWire::read_request(rest.first(size)))target=Target::Directory;
            else if(!native_mode_ && god2cn::CnGenericDirectoryWire::read_request(rest.first(size)))
                target=Target::GenericDirectory;
            else return false; // Remaining B0/94 and D1+94 variants need their actual owner.
            break;
        case 0xa4:
            size=god2cn::CnDirectoryWire::page_request_size;target=Target::Directory;
            if(rest.size()<size || !god2cn::CnDirectoryWire::read_request(rest.first(size)))return false;
            break;
        case 0xd1:
            size=god2cn::CnSpecialDirectoryWire::request_size;target=Target::SpecialDirectory;
            if(native_mode_ || rest.size()<size || !god2cn::CnSpecialDirectoryWire::read_request(rest.first(size)))return false;
            break;
        case 0x30:
            size=2;target=Target::Background30;
            if(rest.size()<size || rest[1]!=0)return false;
            break;
        case 0x36:
            size=9;target=Target::Background36;
            if(rest.size()<size)return false; // Preserve all eight opaque bytes.
            break;
        default:return false; // No skip, guessed length, same-opcode reply or success fallback.
        }
        records.push_back({target,god2cn::Bytes(rest.begin(),rest.begin()+size)});offset+=size;
    }
    return true;
}
void SharedWorldGameplay::receive(god2cn::Bytes bytes,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN gameplay completion required");
    if(active_) {
        // Transport normally serializes logical ingress. A second outstanding
        // batch is not permitted to race this lease's state or output order.
        // Terminalize the actual ongoing chat operation before requesting
        // transport close. Its close-request flag is immediately visible;
        // socket/OnClosed cleanup is asynchronous. This owner fence remains
        // independent when a provider catches the rejected outer ingress.
        if(inline_role_invalidate_)try {inline_role_invalidate_();}catch(...) {}
        if(skill_book_invalidate_)try {skill_book_invalidate_();}catch(...) {}
        if(battle_skill_invalidate_)try {battle_skill_invalidate_();}catch(...) {}
        if(battle_command_invalidate_)try {battle_command_invalidate_();}catch(...) {}
        if(spectator_invalidate_)try {spectator_invalidate_();}catch(...) {}
        if(chat_invalidate_)chat_invalidate_();
        if(const auto connection=connection_.lock())connection->close();
        done(false);return;
    }
    active_=true;
    auto batch=std::make_shared<Batch>();batch->done=std::move(done);
    try {
        // Shape-qualify the entire known aggregate before any gameplay effect.
        // This is neither an atomic multi-request transaction nor native proof.
        // Actual1C publication installed these owners before native output.
        // A later gameplay record must not substitute for that initial handoff.
        if(!current() || !initialized_ || !split(bytes,batch->records)){finish(batch,false);return;}
        pump(batch);
    }catch(...) {finish(batch,false);}
}
void SharedWorldGameplay::dispatch(const Record& record,Connection::Transport::Completion done) {
    switch(record.target) {
    case Target::Movement:movement_(record.bytes,std::move(done));return;
    case Target::Directory:directory_(record.bytes,std::move(done));return;
    case Target::GenericDirectory:generic_directory_(record.bytes,std::move(done));return;
    case Target::SpecialDirectory:special_directory_(record.bytes,std::move(done));return;
    case Target::Chat:chat_(record.bytes,std::move(done));return;
    case Target::PostWorldExit:post_world_exit_(record.bytes,std::move(done));return;
    case Target::PrebornChoices:preborn_choices_(record.bytes,std::move(done));return;
    case Target::Spectator:spectator_(record.bytes,std::move(done));return;
    case Target::SpectatorClose:spectator_close_(record.bytes,std::move(done));return;
    case Target::BattleCommand:battle_commands_(record.bytes,std::move(done));return;
    case Target::SkillBookUse:skill_books_(record.bytes,std::move(done));return;
    case Target::ItemControl:item_control_(record.bytes,std::move(done));return;
    case Target::Background30:case Target::Background36:
        sources_.background(record.target==Target::Background30?SharedWorldReady::Request::Background30:
            SharedWorldReady::Request::Background36,record.bytes,std::move(done));return;
    }
    done(false);
}
void SharedWorldGameplay::pump(const std::shared_ptr<Batch>& batch) {
    owner();if(!batch->done || batch->pumping || batch->waiting)return;
    batch->pumping=true;
    try {
        while(batch->done && !batch->waiting) {
            if(!current()){finish(batch,false);break;}
            if(batch->cursor==batch->records.size()){finish(batch,true);break;}
            const auto index=batch->cursor++;batch->waiting=true;
            auto once=std::make_shared<bool>(false);
            const auto terminal=batch->records[index].target==Target::PostWorldExit;
            auto complete=[self=shared_from_this(),batch,once,terminal](bool accepted) {
                self->owner();if(std::exchange(*once,true) || !batch->done)return;
                batch->waiting=false;
                try {
                    //A successful terminal completion is local write/drain,
                    //with transport closing/cleanup possibly already complete.
                    if(terminal){self->finish_terminal(batch,accepted);return;}
                    if(!accepted || !self->current()){self->finish(batch,false);return;}
                    // Inline completion resumes the loop; deferred completion
                    // starts a fresh pump. No per-record recursive stack growth.
                    if(!batch->pumping)self->pump(batch);
                }catch(...) {self->finish(batch,false);}
            };
            try {dispatch(batch->records[index],complete);}catch(...) {complete(false);}
        }
    }catch(...) {finish(batch,false);}
    batch->pumping=false;
}
void SharedWorldGameplay::finish(const std::shared_ptr<Batch>& batch,bool accepted) {
    owner();if(!batch->done)return;
    auto done=std::move(batch->done);active_=false;
    if(!accepted) {
        if(inline_role_invalidate_)try {inline_role_invalidate_();}catch(...) {}
        if(inline_role_release_)try {inline_role_release_();}catch(...) {}
        if(skill_book_invalidate_)try {skill_book_invalidate_();}catch(...) {}
        if(skill_book_release_)try {skill_book_release_();}catch(...) {}
        if(battle_skill_invalidate_)try {battle_skill_invalidate_();}catch(...) {}
        if(battle_skill_release_)try {battle_skill_release_();}catch(...) {}
        if(battle_command_invalidate_)try {battle_command_invalidate_();}catch(...) {}
        if(battle_command_release_)try {battle_command_release_();}catch(...) {}
        // Stop only this actual child's pending operation before common
        // cleanup. It owns no common/token release and retries no prefix.
        if(spectator_invalidate_)try {spectator_invalidate_();}catch(...) {}
        if(spectator_release_)try {spectator_release_();}catch(...) {}
        // Preserve any already committed movement/storage, as existing owners
        // do. Generation-qualified cleanup cannot evict another incarnation.
        if(release_native_transport_)try {release_native_transport_();}catch(...) {}
        visibility_->release(lease_);presence_->release(lease_);
        if(const auto connection=connection_.lock())connection->close();
    }
    done(accepted); // Source processing/queue acceptance only.
}
void SharedWorldGameplay::finish_terminal(const std::shared_ptr<Batch>& batch,bool written) {
    owner();if(!batch->done)return;
    if(!written){finish(batch,false);return;}
    auto done=std::move(batch->done);active_=false;
    if(inline_role_release_)try {inline_role_release_();}catch(...) {}
    if(skill_book_release_)try {skill_book_release_();}catch(...) {}
    if(battle_skill_release_)try {battle_skill_release_();}catch(...) {}
    if(battle_command_release_)try {battle_command_release_();}catch(...) {}
    if(spectator_release_)try {spectator_release_();}catch(...) {}
    //No further gameplay/pump or obsolete current check. Same connection's
    //existing OnClosed releases admission/lease/visibility/reservation exactly.
    done(true); //Local native03 write/drain only, not client acceptance.
}
}
