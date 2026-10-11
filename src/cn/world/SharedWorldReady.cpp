#include "cn/world/SharedWorldReady.h"
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedWorldReady::BootstrapResult::BootstrapResult(std::vector<god2cn::Bytes> replies,Current current)
    :replies_(std::move(replies)),current_(std::move(current)) {}
std::optional<SharedWorldReady::BootstrapResult> SharedWorldReady::BootstrapResult::without_output(Current current) {
    if(!current)return std::nullopt;
    return BootstrapResult({},std::move(current));
}
std::optional<SharedWorldReady::BootstrapResult> SharedWorldReady::BootstrapResult::with_output(
    std::vector<god2cn::Bytes> replies,Current current) {
    if(!current || replies.empty() || replies.size()>256)return std::nullopt;
    for(const auto& bytes:replies)
        if(bytes.empty() || bytes.size()>god2cn::CnTransport::max_logical)return std::nullopt;
    // Bounds belong to the existing transport. Complete native formats/rules
    // and request/reply causality remain the actual issuer's obligation.
    return BootstrapResult(std::move(replies),std::move(current));
}
std::optional<SharedWorldReady::BootstrapResult> SharedWorldReady::BootstrapResult::with_initial_visibility(
    std::vector<god2cn::Bytes> replies,Current current,std::shared_ptr<SharedActorVisibility::InitialPublication> initial,
    std::vector<ActorSlice> slices,std::vector<SharedActorVisibility::OutwardRecipient> outward,
    SharedActorVisibility::OutwardCurrent outward_current) {
    if(!current || !initial || !outward_current || outward.size()>256 || replies.size()>256)return std::nullopt;
    for(const auto& bytes:replies)
        if(bytes.empty() || bytes.size()>god2cn::CnTransport::max_logical)return std::nullopt;
    const auto records=initial->records();
    const auto supplied=initial->supplied_records();
    if(slices.size()!=records.size() || supplied.size()!=records.size())return std::nullopt;
    for(std::size_t i=0;i<slices.size();++i) {
        const auto at=slices[i];
        if(at.aggregate>=replies.size() || at.offset>replies[at.aggregate].size() ||
           records[i].size()!=god2cn::CnRemoteActor::logical_size || supplied[i].size()!=records[i].size() ||
           records[i].size()>replies[at.aggregate].size()-at.offset ||
           (!std::equal(supplied[i].begin(),supplied[i].end(),replies[at.aggregate].begin()+at.offset) &&
            !std::equal(records[i].begin(),records[i].end(),replies[at.aggregate].begin()+at.offset)))return std::nullopt;
        if(i && (at.aggregate<slices[i-1].aggregate ||
           (at.aggregate==slices[i-1].aggregate && at.offset<slices[i-1].offset+records[i-1].size())))return std::nullopt;
    }
    // Every slice exactly matches full supplied81B or this prepared source
    // projection (an issuer may have built its aggregate from records()).
    // Same-sized projected records preserve every other native field/offset.
    for(std::size_t i=0;i<slices.size();++i)
        std::copy(records[i].begin(),records[i].end(),replies[slices[i].aggregate].begin()+slices[i].offset);
    BootstrapResult result(std::move(replies),std::move(current));result.initial_=std::move(initial);
    result.outward_=std::move(outward);result.outward_current_=std::move(outward_current);return result;
}
SharedWorldReady::SharedWorldReady(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    std::shared_ptr<SharedActorVisibility> visibility,Bootstrap bootstrap,Entered entered,Install install,Connection::Ingress gameplay,
    std::shared_ptr<SharedNativeWorldTransports> world_transports)
    :connection_(connection),presence_(std::move(presence)),visibility_(std::move(visibility)),
     world_transports_(std::move(world_transports)),lease_(lease),
     bootstrap_(std::move(bootstrap)),entered_(std::move(entered)),install_(std::move(install)),gameplay_(std::move(gameplay)) {}
void SharedWorldReady::NativeTransportState::release(const std::shared_ptr<SharedNativeWorldTransports>& registry) {
    // Revoke before any further work; an interrupted bind cannot resurrect a
    // disconnect. Never look up a newer token by a reused lease/name/session.
    released=true;
    auto saved=std::move(token);token.reset();
    if(registry && saved)registry->release(*saved);
}
void SharedWorldReady::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN readiness game owner mismatch");
}
bool SharedWorldReady::current() const {
    const auto connection=connection_.lock();
    return (!world_transports_ || !native_transport_->released) &&
        connection && !connection->closing() && connection->world_session_id()==lease_.session &&
        connection->verified_account_id()==lease_.account && connection->world_character_offered(lease_.character) &&
        (stage_==Stage::InWorld?presence_->ready(lease_):presence_->preparation_current(lease_));
}
std::shared_ptr<SharedWorldReady> SharedWorldReady::attach(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    std::shared_ptr<SharedActorVisibility> visibility,Bootstrap bootstrap,Entered entered,Install install,Connection::Ingress gameplay,
    std::function<void()> release_world,std::shared_ptr<SharedNativeWorldTransports> world_transports) {
    if(!connection || !presence || !visibility || !visibility->owns_presence(presence) ||
       (world_transports && !world_transports->owns_presence(presence)) ||
       !bootstrap || !entered || !install || !gameplay)return {};
    auto result=std::shared_ptr<SharedWorldReady>(new SharedWorldReady(connection,
        std::move(presence),lease,std::move(visibility),std::move(bootstrap),std::move(entered),std::move(install),std::move(gameplay),
        std::move(world_transports)));
    result->owner();
    if(!result->current() || result->presence_->ready(lease))return {};
    if(!connection->install_world_cleanup([registry=result->presence_,visibility=result->visibility_,lease,
                                          transports=result->world_transports_,token=result->native_transport_,
                                          release_world=std::move(release_world)] {
        // Optional actual scene reservation accompanies the same transport's
        // cleanup. Existing users without one preserve their original behavior.
        try {token->release(transports);}catch(...) {}
        visibility->release(lease);registry->release(lease);
        if(release_world)try {release_world();}catch(...) {}
    }))return {};
    return result;
}
bool SharedWorldReady::matches(const std::shared_ptr<Connection>& connection,std::uint64_t character,
    const RecoveredPosition& position,std::uint16_t handle) const {
    owner();return connection_.lock()==connection && stage_==Stage::First1F && lease_.character==character && lease_.position==position &&
        lease_.actor_handle==handle && current();
}
SharedWorldReady::Connection::Ingress SharedWorldReady::ingress() {
    owner();return [self=shared_from_this()](god2cn::Bytes bytes,Connection::Transport::Completion done) {
        self->receive(std::move(bytes),std::move(done));
    };
}
bool SharedWorldReady::matches_preparation(const std::shared_ptr<Connection>& connection,
    const std::shared_ptr<SharedWorldPresence>& presence,const Lease& lease) const {
    owner();return presence_==presence && lease_==lease &&
        matches(connection,lease.character,lease.position,lease.actor_handle);
}
void SharedWorldReady::fail(const std::shared_ptr<Batch>& batch) {
    if(!batch->done)return; // A completed batch cannot tear down its successor.
    stage_=Stage::Failed;
    try {release_native_transport();}catch(...) {}
    try {visibility_->release(lease_);}catch(...) {}
    try {presence_->release(lease_);}catch(...) {}
    if(active_.lock()==batch)active_.reset();
    if(const auto connection=connection_.lock())connection->close();
    if(batch->done){auto done=std::move(batch->done);done(false);}
}
void SharedWorldReady::release_native_transport() {
    owner();native_transport_->release(world_transports_);
}
bool SharedWorldReady::bind_native_transport(const std::shared_ptr<Batch>& batch) {
    owner();if(!world_transports_)return true;
    const auto state=native_transport_;
    if(state->released || state->binding || state->token)return false;
    state->binding=true;
    struct EndBinding {bool& binding;~EndBinding(){binding=false;}} end{state->binding};
    const auto connection=connection_.lock();
    const auto endpoint=[&] {
        return !state->released && batch->done && active_.lock()==batch && stage_==Stage::InWorld &&
            connection && connection_.lock()==connection &&
            !connection->closing() && connection->role()==Connection::Transport::Role::World &&
            connection->world_admission_current();
    };
    const auto pending=[&] {
        return endpoint() && current() && presence_->ready(lease_) && endpoint();
    };
    if(!pending())return false;
    auto token=world_transports_->bind(lease_,connection);
    if(!token)return false;
    if(state->released || state->token) {
        world_transports_->release(*token);return false;
    }
    state->token=std::move(token);
    // Own the token across actual registry/presence observers. Nested cleanup
    // may reset the capsule; no borrowed optional element survives that read.
    const auto retained=*state->token;
    // Registry Current performs the final full ready-root observation and its
    // private incarnation fence. Do not append another repository callback
    // after that check; finish with our callback-free batch/endpoint fence.
    if(!pending() || !world_transports_->current(retained) || !endpoint()) {
        release_native_transport();return false;
    }
    return true;
}
void SharedWorldReady::receive(god2cn::Bytes bytes,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN readiness completion required");
    if(const auto pending=active_.lock();pending && pending->done) {
        if(const auto connection=connection_.lock())connection->close();
        done(false);return; // An outstanding source/publication owns the aggregate.
    }
    auto batch=std::make_shared<Batch>();batch->bytes=std::move(bytes);batch->done=std::move(done);
    active_=batch;
    try {consume(batch);}catch(...) {fail(batch);}
}
void SharedWorldReady::dispatch(const std::shared_ptr<Batch>& batch,Request request,std::size_t size,Stage next) {
    god2cn::Bytes record(batch->bytes.begin()+batch->cursor,batch->bytes.begin()+batch->cursor+size);
    batch->cursor+=size;
    auto once=std::make_shared<bool>(false);
    const auto expected=stage_;
    auto finish=[self=shared_from_this(),batch,once,expected,next](std::optional<BootstrapResult> result) {
        self->owner();if(std::exchange(*once,true))return;
        self->publish(batch,std::move(result),expected,next,std::nullopt);
    };
    try {bootstrap_(request,std::move(record),finish);}catch(...) {finish(std::nullopt);}
}
void SharedWorldReady::publish(const std::shared_ptr<Batch>& batch,std::optional<BootstrapResult> result,
    Stage expected,Stage next,std::optional<std::uint16_t> activate_handle) {
    owner();
    try {
        if(!batch->done)return;
        const auto connection=connection_.lock();
        if(!result || !connection){fail(batch);return;}
        auto source=std::make_shared<BootstrapResult>(std::move(*result));
        // Bootstrap cannot carry initial models, and initial1C cannot silently
        // omit its explicit actual scene actor set, including the empty case.
        if(bool(activate_handle)!=bool(source->initial_) ||
           bool(activate_handle)!=bool(source->outward_current_)){fail(batch);return;}
        const auto pending=[self=shared_from_this(),batch,expected,connection,activate_handle,source] {
            return batch->done && self->active_.lock()==batch && self->connection_.lock()==connection &&
                self->stage_==expected && self->current() &&
                (!activate_handle || (*activate_handle==self->lease_.actor_handle && !self->presence_->ready(self->lease_))) &&
                (!source->initial_ || self->visibility_->initial_current(source->initial_,connection,self->lease_,false)) &&
                connection->role()==Connection::Transport::Role::World && connection->world_admission_current();
        };
        if(!pending() || !source->current_(PublicationCheck::BeforePublish) || !pending()) {fail(batch);return;}
        auto published=std::make_shared<bool>(false);
        const auto publish=[self=shared_from_this(),batch,source,pending,published,next,expected,connection,activate_handle] {
            self->owner();
            if(*published || !pending() || !source->current_(PublicationCheck::QueueAccepted) || !pending())return false;
            if(activate_handle) {
                // The exact initial1C cannot expose ready presence before the
                // actual scene issuer has qualified the held publication.
                bool installed=false;
                try {
                    installed=self->presence_->activate(self->lease_,*activate_handle) && self->install_() &&
                        self->stage_==expected && self->connection_.lock()==connection && self->current() &&
                        self->presence_->ready(self->lease_) && connection->world_admission_current() &&
                        self->visibility_->publish_initial(source->initial_,connection,self->lease_);
                }catch(...) {}
                if(!installed) {
                    // Clear active common presence on this game turn, before
                    // any other owner can observe a failed entry as ready.
                    self->fail(batch);return false;
                }
            }
            self->stage_=next;*published=true;return true;
        };
        const auto queued=[self=shared_from_this(),batch,source,published](bool accepted) {
            self->owner();if(!batch->done)return;
            try {
                // Issuer qualified before release; do not reread its obsolete
                // prepared-stage snapshot after valid ready/gameplay progress.
                if(!accepted || !*published || !self->current()) {self->fail(batch);return;}
                if(source->initial_) {
                    // This connection's incoming held aggregate has released.
                    // Its source remains pinned while the actual complete
                    // observer set publishes full6F through both transports.
                    // No gameplay remainder may move this source midway.
                    self->visibility_->publish_outward_initial(self->lease_,std::move(source->outward_),
                        std::move(source->outward_current_),[self,batch](std::optional<std::vector<SharedActorVisibility::Binding>> bindings) {
                            self->owner();if(!batch->done)return;
                            try {
                                if(!bindings || !self->current()){self->fail(batch);return;}
                                // Incoming held output and every real outward
                                // queue have now succeeded. Register this exact
                                // native transport before any gameplay remainder.
                                if(!self->bind_native_transport(batch)){self->fail(batch);return;}
                                self->consume(batch);
                            }catch(...) {self->fail(batch);}
                        });
                } else self->consume(batch);
            }catch(...) {self->fail(batch);}
        };
        if(source->replies_.empty()) {queued(publish());return;}
        connection->send_world_batch_with_publication(std::move(source->replies_),publish,queued);
    }catch(...) {fail(batch);}
}
void SharedWorldReady::consume(const std::shared_ptr<Batch>& batch) {
    owner();
    if(!batch->done)return;
    if(stage_==Stage::Failed || !current()){fail(batch);return;}
    if(batch->cursor==batch->bytes.size()) {auto done=std::move(batch->done);active_.reset();done(true);return;}
    if(stage_==Stage::InWorld) {
        // The real gameplay dispatcher owns every later record/variant. Preserve
        // the complete remainder; do not interpret native scene-change1C here.
        god2cn::Bytes rest(batch->bytes.begin()+batch->cursor,batch->bytes.end());
        active_.reset(); // The actual gameplay owner serializes its own remainder.
        gameplay_(std::move(rest),std::move(batch->done));return;
    }
    const auto records=std::span<const std::uint8_t>(batch->bytes).subspan(batch->cursor);
    if(++batch->steps>128){fail(batch);return;}
    const auto opcode=records.front();
    if(opcode==0x30 || opcode==0x36) {
        const std::size_t size=opcode==0x30?2:9;
        if(records.size()<size || (opcode==0x30 && records[1]!=0)){fail(batch);return;}
        // 0047B810:30 has an explicitly zero high stack byte,36 copies eight
        // bytes from timer+84. Neither is player identity or reply authority.
        dispatch(batch,opcode==0x30?Request::Background30:Request::Background36,size,stage_);return;
    }
    if(stage_==Stage::First1F || stage_==Stage::Then23) {
        const auto expected=stage_==Stage::First1F?0x1f:0x23;
        if(records.size()<2 || opcode!=expected || records[1]!=0){fail(batch);return;}
        dispatch(batch,stage_==Stage::First1F?Request::Initial1F:Request::Initial23,2,
            stage_==Stage::First1F?Stage::Then23:Stage::Then1C);return;
    }
    if(stage_!=Stage::Then1C || records.size()<5){fail(batch);return;}
    const auto ready=god2cn::CnWorldEntry::parse_ready(records.first(5));
    if(!ready || ready->native_language_value!=0 || ready->claimed_actor_handle!=lease_.actor_handle ||
       presence_->ready(lease_)){fail(batch);return;}
    god2cn::Bytes record(records.begin(),records.begin()+5);
    batch->cursor+=5;stage_=Stage::Entering;
    auto once=std::make_shared<bool>(false);
    auto finish=[self=shared_from_this(),batch,once,handle=ready->claimed_actor_handle](std::optional<EnteredResult> result) {
        self->owner();if(std::exchange(*once,true))return;
        self->publish(batch,std::move(result),Stage::Entering,Stage::InWorld,handle);
    };
    try {entered_(lease_,std::move(record),finish);}catch(...) {finish(std::nullopt);}
}
}
