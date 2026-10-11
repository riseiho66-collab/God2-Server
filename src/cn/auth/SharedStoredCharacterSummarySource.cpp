#include "cn/auth/SharedStoredCharacterSummarySource.h"
#include "cn/protocol/CnCharacterSummary.h"
#include <algorithm>
#include <stdexcept>
#include <thread>

namespace god2::cn {
namespace {
constexpr std::string_view client="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";
bool origin(std::string_view digest,std::string_view record) {
    return digest.size()==64 && std::all_of(digest.begin(),digest.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    }) && !record.empty() && record.size()<=2048 && record.find('\0')==record.npos;
}
struct Preparing {
    bool& busy;
    explicit Preparing(bool& value):busy(value){busy=true;}
    ~Preparing(){busy=false;}
};
}
SharedStoredCharacterSummarySource::Common::Prepare SharedStoredCharacterSummarySource::create(
    AccountRepository& accounts,RecoveredCharacterRepository& characters,Config config) {
    if(!config.authority || !config.snapshots.get().owns_sources(accounts,characters))
        throw std::invalid_argument("CN stored summary requires same account/characters and actual authority");
    struct State {
        AccountRepository& accounts;
        RecoveredCharacterRepository& characters;
        NativeCharacterSummarySnapshotRepository& snapshots;
        Authority authority;
        const std::thread::id owner=std::this_thread::get_id();
        bool busy=false;
        State(AccountRepository& a,RecoveredCharacterRepository& c,Config source)
            :accounts(a),characters(c),snapshots(source.snapshots.get()),authority(std::move(source.authority)) {}
    };
    auto state=std::make_shared<State>(accounts,characters,std::move(config));
    return [state=std::move(state)](Common::Scope scope,const std::vector<RecoveredCharacter>& roots)
        ->std::optional<Common::NativeMetadata> {
        if(state->owner!=std::this_thread::get_id())throw std::logic_error("CN stored summary game owner mismatch");
        if(state->busy || !scope.account || scope.target.group>=64 || scope.target.server>=10 ||
           !state->snapshots.owns_sources(state->accounts,state->characters))return std::nullopt;
        Preparing active(state->busy);
        auto value=state->snapshots.load(scope.account,scope.target.group,scope.target.server,client);
        if(!value || value->account!=scope.account || value->group!=scope.target.group || value->server!=scope.target.server ||
           value->client_sha256!=client || !value->revision || !origin(value->source_sha256,value->source_record))return std::nullopt;
        const auto native=god2cn::CnCharacterSummary::read(value->record);
        if(!native || value->rows.size()!=native->count())return std::nullopt;
        std::vector<Common::Row> rows;rows.reserve(value->rows.size());
        for(const auto& binding:value->rows) {
            const auto common=std::find_if(roots.begin(),roots.end(),[&](const auto& row) {
                return row.id==binding.character && row.account_id==scope.account;
            });
            if(common==roots.end())return std::nullopt;
            Common::NameSource mode;
            switch(binding.name_source) {
                case Snapshot::NameSource::CommonIdentity:mode=Common::NameSource::CommonIdentity;break;
                case Snapshot::NameSource::NativePromptMarker:mode=Common::NameSource::NativePromptMarker;break;
                default:return std::nullopt;
            }
            if(binding.role) {
                if(!origin(binding.role->source_sha256,binding.role->source_record))return std::nullopt;
                const auto level=Common::RoleLevel::from_native22(binding.role->record,binding.role->revision);
                if(!level)return std::nullopt; //Exact actual25B22; no CUSTOM role or FF narrowing.
                rows.emplace_back(binding.character,mode,*level);
            }else rows.emplace_back(binding.character,mode); //Retain actual07 level, no default.
        }
        const auto snapshot=std::make_shared<const Snapshot>(std::move(*value));
        if(state->snapshots.load(scope.account,scope.target.group,scope.target.server,client)!=std::optional{*snapshot})
            return std::nullopt;
        Common::NativeMetadata::Current current=[state,snapshot,scope](const Common::Scope& actual,
            std::uint64_t revision,Common::Summary::Check check,const Common::NativeMetadata::Observation& observation) {
            if(state->owner!=std::this_thread::get_id() || state->busy || actual!=scope || revision!=snapshot->revision ||
               !state->snapshots.owns_sources(state->accounts,state->characters))return false;
            Preparing active(state->busy);
            if(state->snapshots.load(scope.account,scope.target.group,scope.target.server,client)!=std::optional{*snapshot})return false;
            // Real observer sees complete original/projected07, explicit rows/
            // optional native22 and full common roots at each original stage.
            // Existing Common/selection also retain/recheck the whole roots.
            if(!state->authority(*snapshot,actual,check,observation))return false;
            return state->snapshots.owns_sources(state->accounts,state->characters) &&
                state->snapshots.load(scope.account,scope.target.group,scope.target.server,client)==std::optional{*snapshot};
        };
        return Common::NativeMetadata::from_source(scope,snapshot->revision,snapshot->record,std::move(rows),std::move(current));
    };
}
}
