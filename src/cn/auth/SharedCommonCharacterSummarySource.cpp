#include "cn/auth/SharedCommonCharacterSummarySource.h"
#include "cn/protocol/CnCharacterSummary.h"
#include "text/OwnedCharacterNameText.h"
#include <algorithm>
#include <set>
#include <stdexcept>
#include <thread>

namespace god2::cn {
std::optional<SharedCommonCharacterSummarySource::RoleLevel>
SharedCommonCharacterSummarySource::RoleLevel::from_native22(
    std::span<const std::uint8_t> record,std::uint64_t revision) {
    const auto status=god2cn::CnRoleStatus::read(record);
    if(!revision || !status || !status->exact_selection_level_byte())return std::nullopt;
    return RoleLevel(*status,revision);
}
SharedCommonCharacterSummarySource::NativeMetadata::NativeMetadata(Scope scope,std::uint64_t revision,
    god2cn::Bytes record,std::vector<Row> rows,Current current)
    :scope_(scope),revision_(revision),record_(std::move(record)),rows_(std::move(rows)),current_(std::move(current)) {}
std::optional<SharedCommonCharacterSummarySource::NativeMetadata>
SharedCommonCharacterSummarySource::NativeMetadata::from_source(Scope scope,std::uint64_t revision,
    god2cn::Bytes record,std::vector<Row> rows,Current current) {
    const auto native=god2cn::CnCharacterSummary::read(record);
    if(!scope.account || scope.target.group>=64 || scope.target.server>=10 || !revision ||
       !current || !native || rows.size()!=native->count())return std::nullopt;
    std::set<std::uint64_t> ids;
    std::set<std::uint8_t> slots;
    for(unsigned index=0;index<rows.size();++index) {
        const auto row=native->character(index);
        if(!rows[index].character || !ids.insert(rows[index].character).second ||
           !slots.insert(row->native_slot()).second)return std::nullopt;
        if(rows[index].name_source==NameSource::NativePromptMarker) {
            if(!row->native_name_prompt_marker())return std::nullopt;
        } else if(rows[index].name_source!=NameSource::CommonIdentity)return std::nullopt;
    }
    return NativeMetadata(scope,revision,std::move(record),std::move(rows),std::move(current));
}
namespace {
bool same_roots(const std::vector<RecoveredCharacter>& before,const std::vector<RecoveredCharacter>& after,
    std::uint64_t account) {
    if(before.size()!=after.size())return false;
    std::set<std::uint64_t> seen;
    for(const auto& row:after) {
        if(!row.id || row.account_id!=account || !seen.insert(row.id).second)return false;
        const auto old=std::find_if(before.begin(),before.end(),[&row](const auto& value){return value.id==row.id;});
        if(old==before.end() || old->account_id!=row.account_id || old->slot!=row.slot ||
           old->profile!=row.profile || old->created_at!=row.created_at ||
           old->name_codepage!=row.name_codepage || old->streamer_privilege!=row.streamer_privilege)return false;
    }
    return true;
}
struct Preparing {
    bool& busy;
    explicit Preparing(bool& value):busy(value){busy=true;}
    ~Preparing(){busy=false;}
};
}
SharedAccountSelection::SummarySource SharedCommonCharacterSummarySource::create(
    RecoveredCharacterRepository& characters,Config config) {
    if(!config.prepare)throw std::invalid_argument("CN common summary requires actual native metadata source");
    struct State {
        RecoveredCharacterRepository& characters;
        Prepare prepare;
        const std::thread::id owner=std::this_thread::get_id();
        bool busy=false;
        State(RecoveredCharacterRepository& repository,Prepare source):characters(repository),prepare(std::move(source)) {}
    };
    auto state=std::make_shared<State>(characters,std::move(config.prepare));
    return [state=std::move(state)](std::uint64_t account,SharedWorldAdmission::Target target)
        ->std::optional<Summary> {
        if(state->owner!=std::this_thread::get_id())throw std::logic_error("CN common summary game owner mismatch");
        if(state->busy || !account || target.group>=64 || target.server>=10)return std::nullopt;
        Preparing active(state->busy);
        const Scope scope{account,target};
        auto roots=state->characters.list_for_account(account);
        if(!same_roots(roots,roots,account))return std::nullopt;
        auto supplied=state->prepare(scope,roots);
        if(!supplied || supplied->scope_!=scope)return std::nullopt;
        auto record=supplied->record_;
        std::vector<std::uint64_t> ids;
        ids.reserve(supplied->rows_.size());
        for(unsigned index=0;index<supplied->rows_.size();++index) {
            const auto& mapping=supplied->rows_[index];
            const auto common=std::find_if(roots.begin(),roots.end(),[&mapping](const auto& value) {
                return value.id==mapping.character;
            });
            if(common==roots.end())return std::nullopt;
            ids.push_back(common->id);
            if(mapping.role_level) {
                const auto level=mapping.role_level->native_status().exact_selection_level_byte();
                if(!level)return std::nullopt;
                record[3+index*god2cn::CnCharacterSummary::character_stride+16]=*level;
            }
            if(mapping.name_source==NameSource::NativePromptMarker)continue;
            const auto end=std::find(common->profile.begin(),common->profile.begin()+15,0);
            if(end==common->profile.begin() || end==common->profile.begin()+15)return std::nullopt;
            const std::string_view original(reinterpret_cast<const char*>(common->profile.data()),
                static_cast<std::size_t>(end-common->profile.begin()));
            const auto name=OwnedCharacterNameText::from_encoded(original,common->name_codepage);
            const auto encoded=name?OwnedCharacterNameText::from_utf8(name->original_utf8(),936):std::nullopt;
            if(!encoded)return std::nullopt; // Exact identity; no display conversion or replacement.
            const auto bytes=encoded->encoded_bytes();
            const auto start=record.begin()+3+index*god2cn::CnCharacterSummary::character_stride;
            std::copy(bytes.begin(),bytes.end(),start);
            start[bytes.size()]=0; // Only the qualified name and its terminator; retain the rest.
        }
        const auto projected=god2cn::CnCharacterSummary::read(record);
        if(!projected)return std::nullopt;
        for(unsigned index=0;index<supplied->rows_.size();++index)
            if(supplied->rows_[index].name_source==NameSource::CommonIdentity &&
               projected->character(index)->native_name_prompt_marker())return std::nullopt;
        const std::shared_ptr<const NativeMetadata> native=std::make_shared<NativeMetadata>(std::move(*supplied));
        const auto retained_roots=std::make_shared<const std::vector<RecoveredCharacter>>(roots);
        const auto retained_record=std::make_shared<const god2cn::Bytes>(record);
        Summary::Current current=[native,retained_roots,retained_record,scope,owner=state->owner](
            const Scope& actual,Summary::Check check) {
            if(owner!=std::this_thread::get_id() || actual!=scope)return false;
            const NativeMetadata::Observation observation{native->record_,*retained_record,native->rows_,*retained_roots};
            return native->current_(scope,native->revision_,check,observation);
        };
        // Source preparation and observing issuer cannot replace the roots
        // used for encoding. Real selection repeats full-root checks before
        // publication/queue acceptance and name submission, not just here.
        if(!same_roots(roots,state->characters.list_for_account(account),account) ||
           !current(scope,Summary::Check::Prepared) ||
           !same_roots(roots,state->characters.list_for_account(account),account))return std::nullopt;
        return Summary::from_native(scope,std::move(record),std::move(ids),std::move(roots),std::move(current));
    };
}
}
