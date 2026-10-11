#include "cn/world/CnRosterSkillCheckpointSource.h"
#include <algorithm>

namespace god2::cn {
bool CnRosterSkillCheckpointSource::actual_sources_current(std::span<const Checkpoint> supplied) {
    const std::vector<Checkpoint> checkpoints(supplied.begin(),supplied.end());
    for(const auto& checkpoint:checkpoints)
        if(!checkpoint.actual_source || !checkpoint.actual_source->current())return false;
    return true;
}
std::optional<CnRosterSkillCheckpointSource::Projection> CnRosterSkillCheckpointSource::project_actual_sequence(
    std::span<const Record> supplied,std::span<const std::optional<NativeSkillRecord>> supplied_definitions,
    std::span<const Checkpoint> supplied_checkpoints) {
    const std::vector<Record> records(supplied.begin(),supplied.end());
    const Definitions definitions(supplied_definitions.begin(),supplied_definitions.end());
    const std::vector<Checkpoint> checkpoints(supplied_checkpoints.begin(),supplied_checkpoints.end());
    if(definitions.size()!=records.size())return {};
    using Wire=god2cn::CnWorldSubjectSkillUpdate;
    for(std::size_t n=0;n<records.size();++n)
        if(bool(std::get_if<Wire::Record>(&records[n]))!=bool(definitions[n]))return {};
    Projection projected;std::size_t cursor=0;
    for(const auto& checkpoint:checkpoints) {
        while(cursor<records.size() && !std::get_if<Wire::Record>(&records[cursor]))++cursor;
        if(cursor==records.size() || checkpoint.first_record!=cursor || !checkpoint.actual_source ||
           !checkpoint.record_count || checkpoint.record_count>records.size()-cursor ||
           checkpoint.record_count>NativeSource::max_records_per_projection)return {};
        std::vector<Wire::Record> updates;updates.reserve(checkpoint.record_count);
        for(std::size_t n=0;n<checkpoint.record_count;++n) {
            const auto skill=std::get_if<Wire::Record>(&records[cursor+n]);
            if(!skill)return {}; //No synthetic state across30/31/32/33/39.
            const auto parsed=Wire::read(skill->raw);
            if(!parsed || parsed->form!=skill->form)return {};
            updates.push_back(*skill);
        }
        auto data=checkpoint.actual_source->project_updates(updates);
        if(!data || data->steps.size()!=updates.size())return {};
        for(std::size_t n=0;n<updates.size();++n) {
            const auto& step=data->steps[n];const auto& native=step.definition;
            const auto& actual=*definitions[cursor+n];
            if(step.record.form!=updates[n].form || step.record.raw!=updates[n].raw ||
               actual.source!=CnSharedSkillCatalog::expected_source() || actual.kind!=native.kind ||
               actual.definition_id!=native.definition_id || actual.source_offset!=native.file_offset ||
               actual.record_sha256!=native.record_sha256 || actual.raw_record.size()!=native.raw.size() ||
               !std::equal(actual.raw_record.begin(),actual.raw_record.end(),native.raw.begin()))return {};
        }
        projected.total_skill_records+=checkpoint.record_count;
        projected.segments.push_back(Segment{cursor,checkpoint.record_count,std::move(*data)});
        cursor+=checkpoint.record_count;
    }
    while(cursor<records.size() && !std::get_if<Wire::Record>(&records[cursor]))++cursor;
    if(cursor!=records.size() || !actual_sources_current(checkpoints))return {};
    return projected;
}
}
