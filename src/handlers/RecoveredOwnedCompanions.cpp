#include "handlers/RecoveredOwnedCompanions.h"
#include "db/DbTypes.h"
#include <spdlog/spdlog.h>
#include <stdexcept>
namespace god2 {
struct RecoveredOwnedCompanions::PrefixRead {
    RecoveredOwnedCompanions& owner;
    explicit PrefixRead(RecoveredOwnedCompanions& value):owner(value) {
        if(owner.prefix_thread_!=std::this_thread::get_id())
            throw std::logic_error("TW roster prefix game owner mismatch");
        if(owner.prefix_reading_) {
            owner.prefix_reentered_=true;
            throw std::logic_error("TW roster prefix read reentry rejected");
        }
        owner.prefix_reading_=true;owner.prefix_reentered_=false;
    }
    ~PrefixRead(){owner.prefix_reading_=false;}
};
std::vector<std::vector<std::uint8_t>> RecoveredOwnedCompanions::restore(std::uint64_t account,std::uint64_t character) {
    const auto deities=repository_.load_deities(account,character);
    const auto selection=repository_.load_deity_selection(account,character);
    return restore_rows(account,character,deities,selection,repository_.deity_template_keys());
}
RecoveredOwnedCompanions::Restoration RecoveredOwnedCompanions::restore_with_source(
        std::uint64_t account,std::uint64_t character) {
    auto roster=repository_.load_deity_roster(account,character);
    auto batches=restore_rows(account,character,roster.rows(),roster.selection(),roster.template_keys());
    // Pet readers/projection are separate observers. Retain an actual complete
    // deity readset that is still current after them, not just selected/key35.
    if(!repository_.deity_roster_current(roster))throw DatabaseError("Owned deity restoration source changed");
    return Restoration(std::move(roster),std::move(batches));
}
RecoveredOwnedCompanions::Restoration RecoveredOwnedCompanions::restore_with_source(
        std::uint64_t account,std::uint64_t character,SqliteSkillBookLearningRepository& learning) {
    if(!learning.owns_companions(repository_))throw DatabaseError("Skill learning companion repository mismatch");
    auto source=learning.restore(account,character);
    auto roster=source.roster();
    auto batches=restore_rows(account,character,roster.rows(),roster.selection(),roster.template_keys());
    std::vector<RecoveredDeityActivation::Record> activations;activations.reserve(source.activations().size());
    for(const auto& event:source.activations()) {
        const auto raw=RecoveredDeityActivation::encode(event.subject,event.kind,event.definition_id);
        activations.push_back(*RecoveredDeityActivation::parse(raw));
    }
    // Validate against the SAME private roster; append35 only, after the one
    // existing deity+pet projection. The temporary projection issues nothing.
    if(!RecoveredOwnedCompanions::restore(roster,activations))
        throw DatabaseError("Skill activation restoration has no exact saved identity");
    for(const auto& activation:activations) {
        const auto& raw=activation.encode();
        if(batches.empty() || batches.back().size()+raw.size()>RecoveredWorldFrame::max_logical_size)batches.emplace_back();
        batches.back().insert(batches.back().end(),raw.begin(),raw.end());
    }
    if(!repository_.deity_roster_current(roster)||!learning.restoration_current(source))
        throw DatabaseError("Skill activation restoration source changed");
    return Restoration(std::move(roster),std::move(batches),std::move(source),learning);
}
RecoveredOwnedCompanions::Restoration RecoveredOwnedCompanions::restore_deities_with_source(
        std::uint64_t account,std::uint64_t character,SqliteSkillBookLearningRepository& learning) {
    if(!learning.owns_companions(repository_))throw DatabaseError("Skill learning companion repository mismatch");
    auto source=learning.restore(account,character);
    auto roster=source.roster();
    std::vector<RecoveredDeityActivation::Record> activations;activations.reserve(source.activations().size());
    for(const auto& event:source.activations()) {
        const auto raw=RecoveredDeityActivation::encode(event.subject,event.kind,event.definition_id);
        const auto activation=RecoveredDeityActivation::parse(raw);
        if(!activation)throw DatabaseError("Invalid saved skill activation record");
        activations.push_back(*activation);
    }
    auto batches=RecoveredOwnedCompanions::restore(roster,activations);
    if(!batches)throw DatabaseError("Skill activation restoration has no exact saved identity");
    if(!learning.restoration_current(source))throw DatabaseError("Skill activation restoration source changed");
    return Restoration(std::move(roster),std::move(*batches),std::move(source),learning);
}
bool RecoveredOwnedCompanions::restoration_current(const Restoration& restoration) {
    if(restoration.learning_source()) {
        // The actual learning source includes the SAME full roster, inventory,
        // witness and activation headers. No partial observer after this cut.
        return restoration.learning_repository_ &&
            restoration.learning_repository_->owns_companions(repository_) &&
            restoration.learning_repository_->restoration_current(*restoration.learning_source());
    }
    return repository_.deity_roster_current(restoration.deity_roster());
}
std::optional<TaiwanNativeDeityRosterPrefix> RecoveredOwnedCompanions::normal_entry_prefix(
        const Restoration& restoration,const NativeSkillCatalog& catalog) {
    PrefixRead read(*this);
    const auto owned=restoration; // Own input before any SQL observation.
    return normal_entry_prefix_impl(owned,catalog);
}
bool RecoveredOwnedCompanions::normal_entry_prefix_current(const Restoration& restoration,
        const TaiwanNativeDeityRosterPrefix& expected,const NativeSkillCatalog& catalog) {
    PrefixRead read(*this);
    const auto saved=restoration;
    const auto owned=expected; // Retain caller material before SQL observers.
    const auto actual=normal_entry_prefix_impl(saved,catalog);
    return actual && !prefix_reentered_ && actual->rows()==owned.rows() &&
        actual->roster_count()==owned.roster_count() && actual->selected_row()==owned.selected_row() &&
        actual->catalog_records()==owned.catalog_records() && actual->actual_batches()==owned.actual_batches();
}
std::optional<TaiwanNativeDeityRosterPrefix> RecoveredOwnedCompanions::normal_entry_prefix_impl(
        const Restoration& restoration,const NativeSkillCatalog& catalog) {
    // These sequential observations are not an atomic cross-source readset or
    // future CAS. No callbacks, imported rows, learned rights or writes added.
    if(!restoration_current(restoration) || prefix_reentered_)return std::nullopt;
    std::vector<NativeSkillRecord> definitions;
    for(const auto& row:restoration.deity_roster().rows()) {
        for(const auto& skill:row.snapshot.skills) {
            const auto& raw=skill.encode();
            if(std::any_of(definitions.begin(),definitions.end(),[&](const auto& record) {
                return record.kind==raw[2] && record.definition_id==raw[3];
            }))continue;
            auto definition=catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,raw[2],raw[3]);
            if(prefix_reentered_ || !definition)return std::nullopt;
            definitions.push_back(std::move(*definition));
        }
    }
    auto model=TaiwanNativeDeityRosterPrefix::from_reset_and_records(restoration.batches(),definitions,
        bool(restoration.learning_source()));
    if(!model || prefix_reentered_)return std::nullopt;
    for(const auto& expected:model->catalog_records()) {
        const auto actual=catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,expected.kind,expected.definition_id);
        if(prefix_reentered_ || !actual || *actual!=expected)return std::nullopt;
    }
    if(!restoration_current(restoration) || prefix_reentered_)return std::nullopt;
    return model;
}
std::vector<std::vector<std::uint8_t>> RecoveredOwnedCompanions::restore_rows(
        std::uint64_t account,std::uint64_t character,std::span<const StoredDeity> deities,
        const std::optional<StoredDeitySelection>& selection,std::span<const std::uint8_t> template_keys) {
    std::vector<RecoveredDeityState::Snapshot> rows;
    for(const auto& deity:deities) rows.push_back(deity.snapshot);
    const auto deity_bytes=RecoveredDeityState::restore(rows,selection?std::optional{selection->key}:std::nullopt,
        template_keys);
    if(!deity_bytes) throw DatabaseError("Owned deity restore preflight rejected");
    const auto pets=repository_.load_pet2_slots(account,character);
    std::vector<std::uint8_t> logical=*deity_bytes;
    for(const auto& slot:pets) {
        if(slot.pet) {
            if(slot.display_category) spdlog::info("OWNED_PET2_CATEGORY_RESTORED character_id={} slot={} group={} index={} NATIVE_PARSED_DISPLAY_ONLY",
                character,slot.slot,slot.display_category->group,slot.display_category->index);
            const auto restored=RecoveredPet2Lifecycle::restore({{account,character},true,false},*slot.pet,
                [&](auto key){return repository_.resolves_pet2(key);});
            if(!restored) throw DatabaseError("Owned pet2 restore preflight rejected");
            logical.insert(logical.end(),restored->begin(),restored->end());
        } else if(slot.pet1) {
            if(!RecoveredPet1Lifecycle::valid({{account,character},true,false},*slot.pet1,[&](auto key){return repository_.resolves_pet1(key);}))
                throw DatabaseError("Owned pet1 restore preflight rejected");
            RecoveredPet2Lifecycle::clear(logical,slot.slot);
            RecoveredPet1Lifecycle::append(logical,*slot.pet1,slot.slot);
            spdlog::info("OWNED_PET1_RESTORED character_id={} slot={} key={} NATIVE_E3_SNAPSHOT_ONLY",character,slot.slot,slot.pet1->stats.metadata_key());
        } else RecoveredPet2Lifecycle::clear(logical,slot.slot);
    }
    std::vector<std::vector<std::uint8_t>> batches;
    for(std::size_t at=0;at<logical.size();) {
        std::size_t size=0;
        switch(logical[at]) {
        case 0x30:size=19;break;
        case 0x31:size=29;break;
        case 0x34:size=4;break;
        case 0x41:size=5;break;
        case 0x3b:size=25;break;
        case 0xfb:size=73;break;
        case 0xe3:size=53;break;
        default:throw DatabaseError("Unexpected owned companion projection record");
        }
        if(at+size>logical.size()) throw DatabaseError("Truncated owned companion projection");
        if(batches.empty() || batches.back().size()+size>RecoveredWorldFrame::max_logical_size) batches.emplace_back();
        batches.back().insert(batches.back().end(),logical.begin()+static_cast<std::ptrdiff_t>(at),
            logical.begin()+static_cast<std::ptrdiff_t>(at+size));at+=size;
    }
    return batches;
}
std::optional<std::vector<std::vector<std::uint8_t>>> RecoveredOwnedCompanions::restore(
        const OwnedDeityRosterReadset& roster,std::span<const RecoveredDeityActivation::Record> activations) {
    std::vector<RecoveredDeityState::Snapshot> rows;
    for(const auto& row:roster.rows())rows.push_back(row.snapshot);
    auto logical=RecoveredDeityState::restore(rows,roster.selection()?std::optional{roster.selection()->key}:std::nullopt,
        roster.template_keys());
    if(!logical)return std::nullopt;
    for(std::size_t i=0;i<activations.size();++i) {
        const auto& raw=activations[i].encode();
        const auto row=std::find_if(rows.begin(),rows.end(),[&](const auto& value){return value.status.key_raw()==raw[1];});
        if(row==rows.end() || std::none_of(row->skills.begin(),row->skills.end(),[&](const auto& skill){
            const auto& identity=skill.encode();return identity[1]==raw[1] && identity[2]==raw[2] && identity[3]==raw[3];
        }))return std::nullopt;
        for(std::size_t j=0;j<i;++j)if(activations[j].encode()==raw)return std::nullopt;
        logical->insert(logical->end(),raw.begin(),raw.end());
    }
    // All actual identities precede activation; no old S34 gets a default35.
    std::vector<std::vector<std::uint8_t>> batches;
    for(std::size_t at=0;at<logical->size();) {
        const auto opcode=(*logical)[at];
        const std::size_t size=opcode==0x30?19:opcode==0x31?29:(opcode==0x34||opcode==0x35)?4:0;
        if(!size || size>logical->size()-at)return std::nullopt;
        if(batches.empty() || batches.back().size()+size>RecoveredWorldFrame::max_logical_size)batches.emplace_back();
        batches.back().insert(batches.back().end(),logical->begin()+static_cast<std::ptrdiff_t>(at),
            logical->begin()+static_cast<std::ptrdiff_t>(at+size));at+=size;
    }
    return batches;
}
struct RecoveredOwnedCompanions::SelectionPublication::Data {
    std::vector<std::uint8_t> wire;
    std::optional<SqliteCompanionRepository::CommittedDeitySelection> committed;
    explicit Data(const std::vector<std::uint8_t>& value):wire(value) {}
};
const SqliteCompanionRepository::CommittedDeitySelection&
RecoveredOwnedCompanions::SelectionPublication::committed() const noexcept {return *data_->committed;}
const std::vector<std::uint8_t>& RecoveredOwnedCompanions::SelectionPublication::wire() const noexcept {return data_->wire;}
std::optional<RecoveredOwnedCompanions::SelectionResult> RecoveredOwnedCompanions::select_deity_with_source(
        std::uint64_t account,std::uint64_t character,const RecoveredDeitySelection::Request& request) {
    const auto key=request.key;
    const auto rows=repository_.load_deities(account,character);
    const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.snapshot.status.key_raw()==key;});
    if(found==rows.end()) return std::nullopt;
    const auto projection=RecoveredDeityState::selection_response(key,found->snapshot,repository_.deity_template_keys());
    if(!projection) return std::nullopt;
    // Encode before COMMIT; mutable ownership avoids the old const-vector copy
    // after a successful selection. The repository compares this full row.
    auto wire=RecoveredWorldFrame::encode(projection->encode());
    const auto selected=repository_.load_deity_selection(account,character);
    // CUSTOM-0147: second original frame and its holder allocate PRECOMMIT.
    // Installing the private commit and returning both owners only move.
    auto retained=std::make_shared<SelectionPublication::Data>(wire);
    auto committed=repository_.select_deity_with_source(account,character,key,selected,*found);
    retained->committed.emplace(std::move(committed));
    return SelectionResult(SelectionPublication(std::move(retained)),std::move(wire));
}
std::optional<std::vector<std::uint8_t>> RecoveredOwnedCompanions::select_deity(std::uint64_t account,std::uint64_t character,
        const RecoveredDeitySelection::Request& request) {
    auto result=select_deity_with_source(account,character,request);
    if(!result) return std::nullopt;
    return std::move(*result).take_wire();
}
std::optional<std::vector<std::uint8_t>> RecoveredOwnedCompanions::select_pet2(std::uint64_t account,std::uint64_t character,
        const RecoveredSelectionItemRequest::Request& request) {
    const auto native=RecoveredPet2Lifecycle::decode(RecoveredSelectionItemRequest::encode(request));
    if(!native) return std::nullopt;
    const auto slots=repository_.load_pet2_slots(account,character);
    const auto source=std::find_if(slots.begin(),slots.end(),[&](const auto& row){return row.slot==native->source;});
    if(source==slots.end() || !source->occupied()) return std::nullopt;
    // CUSTOM-0039: native request has no destination. Reserve selection always
    // targets44; return picks first explicitly empty reserve42, then43.
    const auto destination=std::find_if(slots.begin(),slots.end(),[&](const auto& row){
        return native->intent==RecoveredPet2Lifecycle::Intent::SelectReserve ? row.slot==44 :
            row.slot>=42 && row.slot<=43 && !row.occupied();
    });
    if(destination==slots.end()) return std::nullopt;
    const RecoveredPet2Lifecycle::Context context{{account,character},true,false};
    const auto valid=[&](const StoredPet2Slot& row) {
        if(row.pet && row.pet1)return false;
        return row.pet?RecoveredPet2Lifecycle::valid(context,*row.pet,[&](auto key){return repository_.resolves_pet2(key);}):
            (row.pet1?RecoveredPet1Lifecycle::valid(context,*row.pet1,[&](auto key){return repository_.resolves_pet1(key);}):true);
    };
    if(!valid(*source) || !valid(*destination))return std::nullopt;
    const bool accepted=source->pet?
        RecoveredPet2Lifecycle::accepts(context,*native,*source->pet,[&](auto key){return repository_.resolves_pet2(key);}):
        RecoveredPet1Lifecycle::accepts(context,*native,*source->pet1,[&](auto key){return repository_.resolves_pet1(key);});
    if(!accepted)return std::nullopt;
    std::vector<std::uint8_t> logical;
    // Clear BOTH previous families before replacing metadata: A2C90 selects
    // its52/72-byte cache using the old retained inventory type32/34.
    RecoveredPet2Lifecycle::clear(logical,source->slot);RecoveredPet2Lifecycle::clear(logical,destination->slot);
    const auto append=[&](const StoredPet2Slot& row,std::uint8_t slot) {
        if(row.pet)RecoveredPet2Lifecycle::append(logical,*row.pet,slot);
        else if(row.pet1)RecoveredPet1Lifecycle::append(logical,*row.pet1,slot);
    };
    append(*destination,source->slot);append(*source,destination->slot);
    const auto wire=RecoveredWorldFrame::encode(logical);
    const auto committed=repository_.transfer_pet2(account,character,*source,*destination);
    if(committed.destination.display_category) spdlog::info("OWNED_PET2_CATEGORY_TRANSFERRED character_id={} slot={} group={} index={} NATIVE_PARSED_DISPLAY_ONLY",
        character,committed.destination.slot,committed.destination.display_category->group,committed.destination.display_category->index);
    return wire;
}
}
