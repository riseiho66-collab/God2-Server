#include "cn/world/SharedSubjectSkillPublication.h"
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedSubjectSkillPublication::SharedSubjectSkillPublication(std::shared_ptr<const CnSharedSkillCatalog> catalog,
    Qualify qualify,QualifyNative native)
    :catalog_(std::move(catalog)),qualify_(std::move(qualify)),qualify_native_(std::move(native)) {}
void SharedSubjectSkillPublication::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN skill publication game owner mismatch");
}
std::shared_ptr<SharedSubjectSkillPublication> SharedSubjectSkillPublication::create(
    std::shared_ptr<const CnSharedSkillCatalog> catalog,Qualify qualify,QualifyNative native) {
    if(!catalog || !qualify || !catalog->current())return {};
    return std::shared_ptr<SharedSubjectSkillPublication>(new SharedSubjectSkillPublication(
        std::move(catalog),std::move(qualify),std::move(native)));
}
bool SharedSubjectSkillPublication::current() const {
    owner();const auto connection=connection_.lock();
    return bound_ && presence_ && connection && !connection->closing() &&
        connection->role()==Connection::Transport::Role::World &&
        connection->verified_account_id()==lease_.account && connection->world_session_id()==lease_.session &&
        connection->world_character_offered(lease_.character) && connection->world_admission_current() &&
        presence_->ready(lease_) && catalog_->current();
}
bool SharedSubjectSkillPublication::bind(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease) {
    owner();if(bound_ || !connection || !presence || !lease.account || !lease.session || !lease.character)return false;
    connection_=connection;presence_=std::move(presence);lease_=lease;bound_=true;
    if(current())return true;
    bound_=false;connection_.reset();presence_.reset();lease_={};return false;
}
void SharedSubjectSkillPublication::publish(Plan supplied,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN skill publication completion required");
    if(active_) {if(const auto connection=connection_.lock())connection->close();done(false);return;}
    active_=true;
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[self=shared_from_this(),completion](bool queued) {
        self->owner();if(!*completion)return;
        auto done=std::move(*completion);*completion={};self->active_=false;
        if(!queued)if(const auto connection=self->connection_.lock())connection->close();
        done(queued); // Local transport acceptance, never a native ACK or client acceptance.
    };
    try {
        if(!current() || supplied.recipient!=lease_ || !supplied.actual_event_id ||
           !supplied.actual_committed_revision || supplied.actual_records.empty() ||
           (last_attempt_ && *last_attempt_==supplied.actual_event_id)) {finish(false);return;}
        if(bool(qualify_native_)!=bool(supplied.optional_native_source)){finish(false);return;}
        std::vector<god2cn::Bytes> bytes;
        auto definitions=std::make_shared<std::vector<NativeSkillRecord>>();
        std::size_t size=0;
        for(const auto& record:supplied.actual_records) {
            const auto parsed=Wire::read(record.raw);
            if(!parsed || parsed->form!=record.form || record.raw.size()>god2cn::CnTransport::max_logical-size) {
                finish(false);return;
            }
            auto definition=CnPrebornSkillReferences::resolve_update_definition(*parsed,*catalog_);
            if(!definition) {finish(false);return;}
            definitions->push_back(std::move(*definition));size+=record.raw.size();
            bytes.emplace_back(record.raw.begin(),record.raw.end());
        }
        std::optional<NativeSource::Projection> observed;
        if(supplied.optional_native_source) {
            observed=supplied.optional_native_source->project_updates(supplied.actual_records);
            if(!observed || observed->steps.size()!=definitions->size()){finish(false);return;}
            for(std::size_t n=0;n<definitions->size();++n) {
                const auto& step=observed->steps[n];const auto& actual=(*definitions)[n];
                const auto& native=step.definition;
                if(step.record.form!=supplied.actual_records[n].form || step.record.raw!=supplied.actual_records[n].raw ||
                   actual.source!=CnSharedSkillCatalog::expected_source() || actual.kind!=native.kind ||
                   actual.definition_id!=native.definition_id || actual.source_offset!=native.file_offset ||
                   actual.record_sha256!=native.record_sha256 || actual.raw_record.size()!=native.raw.size() ||
                   !std::equal(actual.raw_record.begin(),actual.raw_record.end(),native.raw.begin())){finish(false);return;}
            }
        }
        const auto projection=std::make_shared<const std::optional<NativeSource::Projection>>(std::move(observed));
        auto plan=std::make_shared<const Plan>(std::move(supplied));
        if(!current() || !qualify_(*plan,*definitions,Check::BeforeQueue) || !current()) {finish(false);return;}
        if(plan->optional_native_source && (!plan->optional_native_source->current() ||
           !qualify_native_(*plan,*definitions,**projection,Check::BeforeQueue) ||
           !plan->optional_native_source->current() || !current())){finish(false);return;}
        // Only this connection's immediate attempt is designated here. Actual
        // committed event and durable replay state belong to the common owner.
        last_attempt_=plan->actual_event_id;
        const auto connection=connection_.lock();if(!connection){finish(false);return;}
        connection->send_world_batch_with_publication(std::move(bytes),
            [weak=weak_from_this(),plan,definitions,projection] {
                const auto self=weak.lock();if(!self)return false;
                self->owner();
                return self->active_ && self->last_attempt_==plan->actual_event_id && self->current() &&
                    self->qualify_(*plan,*definitions,Check::QueueAccepted) && self->current() &&
                    (!plan->optional_native_source || (plan->optional_native_source->current() &&
                     self->qualify_native_(*plan,*definitions,**projection,Check::QueueAccepted) &&
                     plan->optional_native_source->current() && self->current()));
            },finish);
    }catch(...) {finish(false);}
}
}
