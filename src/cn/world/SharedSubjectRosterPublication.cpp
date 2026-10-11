#include "cn/world/SharedSubjectRosterPublication.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedSubjectRosterPublication::SharedSubjectRosterPublication(Qualify qualify,
    std::shared_ptr<const CnSharedSkillCatalog> skills,std::shared_ptr<const god2cn::CnSubjectTemplateNames> names,
    QualifyNative native)
    :qualify_(std::move(qualify)),qualify_native_(std::move(native)),skills_(std::move(skills)),names_(std::move(names)) {}
void SharedSubjectRosterPublication::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN roster publication game owner mismatch");
}
std::shared_ptr<SharedSubjectRosterPublication> SharedSubjectRosterPublication::create(Qualify qualify,
    std::shared_ptr<const CnSharedSkillCatalog> skills,std::shared_ptr<const god2cn::CnSubjectTemplateNames> names,
    QualifyNative native) {
    if(!qualify || (skills && !skills->current()) || (names && !names->current()))return {};
    return std::shared_ptr<SharedSubjectRosterPublication>(new SharedSubjectRosterPublication(
        std::move(qualify),std::move(skills),std::move(names),std::move(native)));
}
bool SharedSubjectRosterPublication::current() const {
    owner();const auto connection=connection_.lock();
    return bound_ && presence_ && connection && !connection->closing() &&
        connection->role()==Connection::Transport::Role::World &&
        connection->verified_account_id()==lease_.account && connection->world_session_id()==lease_.session &&
        connection->world_character_offered(lease_.character) && connection->world_admission_current() &&
        presence_->ready(lease_) && (!skills_ || skills_->current()) && (!names_ || names_->current());
}
bool SharedSubjectRosterPublication::bind(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease) {
    owner();if(bound_ || !connection || !presence || !lease.account || !lease.session || !lease.character)return false;
    connection_=connection;presence_=std::move(presence);lease_=lease;bound_=true;
    if(current())return true;
    bound_=false;connection_.reset();presence_.reset();lease_={};return false;
}
void SharedSubjectRosterPublication::publish(Plan supplied,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN roster publication completion required");
    if(active_) {if(const auto connection=connection_.lock())connection->close();done(false);return;}
    active_=true;
    struct Retained {
        std::shared_ptr<const Plan> plan;
        std::shared_ptr<Definitions> definitions;
        std::shared_ptr<TemplateNames> names;
        std::shared_ptr<LevelNames> levels;
        std::shared_ptr<const Framing> framing;
        std::shared_ptr<const std::optional<CheckpointSource::Projection>> projection;
    };
    auto retained=std::make_shared<Retained>();
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[self=shared_from_this(),completion,retained](bool queued) {
        self->owner();if(!*completion)return;
        auto done=std::move(*completion);*completion={};self->active_=false;
        if(!queued)if(const auto connection=self->connection_.lock())connection->close();
        done(queued); //Local transport acceptance; no native ACK/client acceptance.
    };
    try {
        if(!current() || supplied.recipient!=lease_ || !supplied.actual_event_id ||
           !supplied.actual_committed_revision || supplied.actual_records.empty() ||
           supplied.actual_records.size()>Framing::max_batch_logical_bytes/Framing::min_record_bytes ||
           (last_attempt_ && *last_attempt_==supplied.actual_event_id)) {finish(false);return;}
        if(bool(qualify_native_)!=supplied.use_actual_native_skill_checkpoints ||
           (!supplied.use_actual_native_skill_checkpoints && !supplied.actual_native_skill_checkpoints.empty())) {
            finish(false);return;
        }
        std::vector<god2cn::Bytes> bytes;
        auto definitions=std::make_shared<Definitions>();auto names=std::make_shared<TemplateNames>();Framing layout;
        auto levels=std::make_shared<LevelNames>();retained->levels=levels;
        retained->definitions=definitions;
        retained->names=names;
        for(const auto& record:supplied.actual_records) {
            god2cn::Bytes raw;std::optional<NativeSkillRecord> definition;
            std::optional<god2cn::CnSubjectTemplateNames::Lookup> template_name;
            std::optional<god2cn::CnSubjectTemplateNames::LevelLookup> level_name;
            if(const auto declaration=std::get_if<god2cn::CnSubjectDeclaration30>(&record)) {
                const auto original=declaration->record_bytes();raw.assign(original.begin(),original.end());
                if(declaration->native_absolute_identifier() && declaration->uses_template_name()) {
                    if(!names_) {finish(false);return;}
                    template_name=names_->lookup_absolute_identifier(declaration->native_absolute_identifier());
                    if(!template_name) {finish(false);return;}
                }
            }else if(const auto status=std::get_if<god2cn::CnSubjectStatus31>(&record)) {
                const auto original=status->record_bytes();raw.assign(original.begin(),original.end());
            }else if(const auto selected=std::get_if<god2cn::CnSelectedSubjectUpdate>(&record)) {
                raw=selected->record_bytes(); //Exact33/39; selection/order belong to actual common owner.
            }else if(const auto title=std::get_if<god2cn::CnSelectedSubjectTitle32>(&record)) {
                if(!names_) {finish(false);return;}
                level_name=names_->lookup_level_selector(title->native_selector());
                if(!level_name || level_name->action==god2cn::CnSubjectTemplateNames::LevelAction::UnresolvedAcceptedString) {
                    finish(false);return; //Open native source branch, never guessed empty text.
                }
                const auto original=title->record_bytes();raw.assign(original.begin(),original.end());
            }else {
                const auto& skill=std::get<god2cn::CnWorldSubjectSkillUpdate::Record>(record);
                const auto parsed=god2cn::CnWorldSubjectSkillUpdate::read(skill.raw);
                if(!parsed || parsed->form!=skill.form || !skills_) {finish(false);return;}
                definition=CnPrebornSkillReferences::resolve_update_definition(*parsed,*skills_);
                if(!definition) {finish(false);return;}
                raw.assign(skill.raw.begin(),skill.raw.end());
            }
            if(raw.empty() || raw.size()>Framing::max_logical_per_frame ||
               raw.size()>Framing::max_batch_logical_bytes-layout.total_logical_bytes) {finish(false);return;}
            if(bytes.empty() || raw.size()>Framing::max_logical_per_frame-bytes.back().size()) {
                if(bytes.size()==Framing::max_frames) {finish(false);return;}
                bytes.emplace_back();bytes.back().reserve(Framing::max_logical_per_frame);
                layout.frames.push_back(Framing::Frame{definitions->size(),0,0});
            }
            //Append whole actual19/29/4/2/17-byte records in their original order.
            //No padding/extra opcodes, no native record spanning frame edges.
            bytes.back().insert(bytes.back().end(),raw.begin(),raw.end());
            ++layout.frames.back().record_count;layout.frames.back().logical_bytes+=raw.size();
            layout.total_logical_bytes+=raw.size();definitions->push_back(std::move(definition));
            names->push_back(std::move(template_name));
            levels->push_back(std::move(level_name));
        }
        std::optional<CheckpointSource::Projection> observed;
        if(supplied.use_actual_native_skill_checkpoints) {
            observed=CheckpointSource::project_actual_sequence(supplied.actual_records,*definitions,
                supplied.actual_native_skill_checkpoints);
            if(!observed){finish(false);return;}
        }
        const auto projection=std::make_shared<const std::optional<CheckpointSource::Projection>>(std::move(observed));
        retained->projection=projection;
        auto plan=std::make_shared<const Plan>(std::move(supplied));
        retained->plan=plan;
        auto framing=std::make_shared<const Framing>(std::move(layout));retained->framing=framing;
        if(!current() || !qualify_(*plan,*definitions,*names,*levels,*framing,Check::BeforeQueue) || !current()) {finish(false);return;}
        if(plan->use_actual_native_skill_checkpoints &&
           (!CheckpointSource::actual_sources_current(plan->actual_native_skill_checkpoints) ||
            !qualify_native_(*plan,*definitions,*names,*levels,*framing,**projection,Check::BeforeQueue) ||
            !CheckpointSource::actual_sources_current(plan->actual_native_skill_checkpoints) || !current())) {finish(false);return;}
        last_attempt_=plan->actual_event_id;
        const auto connection=connection_.lock();if(!connection){finish(false);return;}
        //All real records retain order through one held batch; no prefix can
        //leave before actual authority accepts the same committed aggregate.
        connection->send_world_batch_with_publication(std::move(bytes),
            [weak=weak_from_this(),plan,definitions,names,levels,framing,projection] {
                const auto self=weak.lock();if(!self)return false;self->owner();
                return self->active_ && self->last_attempt_==plan->actual_event_id && self->current() &&
                    self->qualify_(*plan,*definitions,*names,*levels,*framing,Check::QueueAccepted) && self->current() &&
                    (!plan->use_actual_native_skill_checkpoints ||
                     (CheckpointSource::actual_sources_current(plan->actual_native_skill_checkpoints) &&
                      self->qualify_native_(*plan,*definitions,*names,*levels,*framing,**projection,Check::QueueAccepted) &&
                      CheckpointSource::actual_sources_current(plan->actual_native_skill_checkpoints) && self->current()));
            },finish);
    }catch(...) {finish(false);}
}
}
