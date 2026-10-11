#include "cn/world/SharedMonsterPublication.h"
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
struct Operation {bool& busy;explicit Operation(bool& value):busy(value){busy=true;}~Operation(){busy=false;}};
bool valid(const SharedMonsterPublication::Source& source) {
    return source.common_monster && source.incarnation && source.revision;
}
bool same_entity(const SharedMonsterPublication::Source& a,const SharedMonsterPublication::Source& b) {
    return a.common_monster==b.common_monster && a.incarnation==b.incarnation && a.area==b.area && a.scene==b.scene;
}
}
SharedMonsterPublication::Binding::Binding(std::shared_ptr<const Identity> identity,Source source,Lease recipient,
    std::uint16_t instance,std::uint64_t generation)
    :identity_(std::move(identity)),source_(source),recipient_(recipient),instance_(instance),generation_(generation){}
SharedMonsterPublication::SharedMonsterPublication(std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<WorldOwner> world):presence_(std::move(presence)),world_(std::move(world)) {
    if(!presence_ || !world_)throw std::invalid_argument("Common monster publication owners required");
}
void SharedMonsterPublication::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Common monster publication game owner mismatch");
}
bool SharedMonsterPublication::matches(const Binding& binding,const Entry& entry) const {
    return binding.identity_==identity_ && binding.identity_==entry.binding.identity_ &&
        binding.source_==entry.binding.source_ && binding.recipient_==entry.binding.recipient_ &&
        binding.instance_==entry.binding.instance_ && binding.generation_==entry.binding.generation_;
}
bool SharedMonsterPublication::recipient_bound(const Lease& recipient,const Source& source,
    const std::shared_ptr<Connection>& connection) const {
    if(!connection || connection->closing() || !presence_->ready(recipient) ||
       connection->role()!=Connection::Transport::Role::World || connection->world_session_id()!=recipient.session ||
       connection->verified_account_id()!=recipient.account || !connection->world_character_offered(recipient.character))return false;
    const auto position=presence_->saved_position(recipient);
    return position && position->area==source.area && position->scene==source.scene;
}
void SharedMonsterPublication::failed_output(const Entry& entry) {
    // Unknown submission state forces real owner recovery, never reuse token.
    const auto connection=entry.connection.lock();
    if(recipient_bound(entry.binding.recipient_,entry.latest,connection))connection->close();
}
std::optional<SharedMonsterPublication::Binding> SharedMonsterPublication::show(Source source,
    const Lease& recipient,std::weak_ptr<Connection> output,god2cn::CnWorldMonster::Record record,
    god2cn::CnCurrentEnemyDisplayCatalog::Resource catalog,Display::Resources resources) {
    owner();if(busy_)return std::nullopt;Operation operation(busy_);
    const auto connection=output.lock();const Key key{recipient.session,record.instance()};
    if(!valid(source) || !recipient_bound(recipient,source,connection) || entries_.contains(key) ||
       generation_==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    // Only a bookkeeping upper bound: native shared pool occupancy also needs
    // mandatory actual qualification (NPCs/other owners can occupy the pool).
    std::size_t count=0;
    for(const auto& [k,e]:entries_)if(k.first==recipient.session) {
        ++count;
        if(e.binding.recipient_!=recipient || same_entity(e.latest,source))return std::nullopt;
    }
    if(count>=256)return std::nullopt;
    try {
        if(!world_->current(source))return std::nullopt;
        auto projection=Display::prepare(record,catalog,resources);
        if(!projection || !world_->qualify_spawn(source,recipient,*projection) ||
           !world_->current(source) || !resources.current(catalog,resources.revision) ||
           !recipient_bound(recipient,source,connection))return std::nullopt;
        const auto raw=god2cn::CnWorldMonster::encode_logical(record);
        std::vector<std::uint8_t> bytes(raw.begin(),raw.end());
        Binding binding(identity_,source,recipient,record.instance(),generation_+1);
        const auto inserted=entries_.emplace(key,Entry{binding,source,output,
            ExpectedMotion{record.x(),record.y(),record.state_raw(),std::nullopt}});
        if(!inserted.second)return std::nullopt;
        ++generation_; // No71 replacement: existing native IDs keep old appearance.
        try {
            connection->send(std::move(bytes));
            if(!recipient_bound(recipient,source,connection)) {
                const auto entry=inserted.first->second;entries_.erase(inserted.first);failed_output(entry);return std::nullopt;
            }
        }catch(...) {
            const auto entry=inserted.first->second;entries_.erase(inserted.first);failed_output(entry);return std::nullopt;
        }
        return binding; // Expected send submission, not receipt/render/acceptance.
    }catch(...) {return std::nullopt;}
}
bool SharedMonsterPublication::level(const Binding& binding,Source source,const Level::Record& level_record) {
    owner();if(busy_)return false;Operation operation(busy_);
    const Key key{binding.recipient_.session,binding.instance_};const auto found=entries_.find(key);
    if(found==entries_.end() || !matches(binding,found->second) || !valid(source) ||
       !same_entity(source,found->second.latest) || level_record.instance()!=binding.instance_)return false;
    const auto connection=found->second.connection.lock();
    try {
        if(!recipient_bound(binding.recipient_,source,connection) || !world_->current(source) ||
           !world_->qualify_level(source,binding.recipient_,level_record) || !world_->current(source) ||
           !recipient_bound(binding.recipient_,source,connection))return false;
        const auto raw=Level::encode_logical(level_record);std::vector<std::uint8_t> bytes(raw.begin(),raw.end());
        found->second.latest=source;
        try {
            connection->send(std::move(bytes));
            if(recipient_bound(binding.recipient_,source,connection))return true;
        }catch(...) {}
        const auto entry=found->second;entries_.erase(found);failed_output(entry);return false;
    }catch(...) {return false;}
}
bool SharedMonsterPublication::hide(const Binding& binding,std::uint64_t publication_revision,const Remove::Record& removal) {
    owner();if(busy_)return false;Operation operation(busy_);
    const Key key{binding.recipient_.session,binding.instance_};const auto found=entries_.find(key);
    if(!publication_revision || found==entries_.end() || !matches(binding,found->second) ||
       removal.instance()!=binding.instance_)return false;
    const auto entry=found->second;const auto connection=entry.connection.lock();
    try {
        if(!recipient_bound(binding.recipient_,entry.latest,connection) ||
           !world_->qualify_removal(entry.latest,binding.recipient_,publication_revision,removal) ||
           !recipient_bound(binding.recipient_,entry.latest,connection))return false;
        const auto raw=Remove::encode_logical(removal);std::vector<std::uint8_t> bytes(raw.begin(),raw.end());
        entries_.erase(found); // Old incarnation invalidated before wire submission.
        try {
            connection->send(std::move(bytes));
            if(recipient_bound(binding.recipient_,entry.latest,connection))return true;
        }catch(...) {}
        failed_output(entry);return false;
    }catch(...) {return false;}
}
bool SharedMonsterPublication::motion(const Binding& binding,Source source,const Motion::Record& motion_record) {
    owner();if(busy_)return false;Operation operation(busy_);
    const Key key{binding.recipient_.session,binding.instance_};const auto found=entries_.find(key);
    if(found==entries_.end() || !matches(binding,found->second) || !valid(source) ||
       !same_entity(source,found->second.latest) || motion_record.instance()!=binding.instance_)return false;
    const auto connection=found->second.connection.lock();
    // Snapshot all prior source/expected movement for the real authority's
    // transition qualification; no inferred path, cadence or stored position.
    const auto previous=found->second.latest;const auto expected=found->second.motion;
    try {
        if(!recipient_bound(binding.recipient_,source,connection) || !world_->current(source) ||
           !world_->qualify_motion(previous,source,binding.recipient_,expected,motion_record) ||
           !world_->current(source) || !recipient_bound(binding.recipient_,source,connection))return false;
        const auto raw=Motion::encode_logical(motion_record);std::vector<std::uint8_t> bytes(raw.begin(),raw.end());
        found->second.latest=source;
        found->second.motion=ExpectedMotion{motion_record.target_x(),motion_record.target_y(),
            motion_record.state_raw(),motion_record};
        try {
            connection->send(std::move(bytes));
            if(recipient_bound(binding.recipient_,source,connection))return true;
        }catch(...) {}
        const auto entry=found->second;entries_.erase(found);failed_output(entry);return false;
    }catch(...) {return false;}
}
bool SharedMonsterPublication::reset_recipient(const Lease& recipient) {
    owner();if(busy_)return false;Operation operation(busy_);
    for(auto i=entries_.begin();i!=entries_.end();) {
        if(i->second.binding.recipient_==recipient)i=entries_.erase(i);else ++i;
    }
    return true; // Exact old lease only; a stale disconnect cannot clear a successor.
}
}
