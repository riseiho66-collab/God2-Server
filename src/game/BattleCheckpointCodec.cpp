#include "game/BattleCheckpointCodec.h"
#include <nlohmann/json.hpp>
#include <limits>

namespace god2 {
namespace {
using Json=nlohmann::json;
std::string runtime() {
#if defined(_MSVC_STL_VERSION)
    return "mt19937-msvc-"+std::to_string(_MSVC_STL_VERSION)+"-"+std::to_string(_MSVC_STL_UPDATE);
#elif defined(__GLIBCXX__)
    return "mt19937-libstdcxx-"+std::to_string(__GLIBCXX__);
#elif defined(_LIBCPP_VERSION)
    return "mt19937-libcxx-"+std::to_string(_LIBCPP_VERSION);
#else
    throw std::invalid_argument("Unqualified checkpoint runtime");
#endif
}
template<class T> T number(const Json& value) {
    if(!value.is_number_integer() || (value.is_number_integer() && !value.is_number_unsigned() && value.get<std::int64_t>()<0))
        throw std::invalid_argument("Checkpoint requires unsigned integer");
    const auto n=value.get<std::uint64_t>();
    if(n>std::numeric_limits<T>::max()) throw std::invalid_argument("Checkpoint integer overflow");
    return static_cast<T>(n);
}
}
std::string BattleCheckpointCodec::encode(const BattleCheckpoint& checkpoint) {
    (void)Battle::restore(checkpoint);
    const auto& state=checkpoint.snapshot;
    const bool extended=checkpoint.version==2;
    Json actors=Json::array();
    for(const auto& slot:state.actors) {
        if(!slot) {actors.push_back(nullptr);continue;}
        const auto& a=*slot;
        actors.push_back(Json::array({a.position,a.controller,a.hp,a.max_hp,a.mp,a.max_mp,
            a.physical_attack,a.magical_attack,a.physical_defense,a.magical_defense}));
    }
    Json document{{"version",checkpoint.version},{"design_id","CUSTOM-0007"},{"engine",runtime()},
        {"id",state.id},{"revision",state.revision},{"state",state.state==BattleState::Active?"active":"finished"},
        {"winner",state.victorious_side?Json(*state.victorious_side):Json(nullptr)},
        {"actors",std::move(actors)},{"rng",checkpoint.random_state}};
    // Version1 keeps its original nine keys and original-width actor values.
    // Version2 is an explicit server storage profile, not a native wire format.
    if(extended)document["numeric_profile"]="extended-health64";
    return document.dump();
}
BattleCheckpoint BattleCheckpointCodec::decode(std::string_view text) {
    if(text.empty() || text.size()>32768) throw std::invalid_argument("Checkpoint size limit");
    const auto data=Json::parse(text,[](int depth,Json::parse_event_t,Json&) {
        if(depth>5) throw std::invalid_argument("Checkpoint nesting limit");
        return true;
    });
    if(!data.is_object())throw std::invalid_argument("Checkpoint requires an object");
    const auto version=number<std::uint32_t>(data.at("version"));
    const bool extended=version==2;
    if((version!=1 && !extended) || data.size()!=(extended?10u:9u))
        throw std::invalid_argument("Checkpoint version or shape mismatch");
    // Validate the entire versioned key set before reading any actor. Size
    // alone must not let an unknown key substitute for a required field.
    for(const auto* key:{"version","design_id","engine","id","revision","state","winner","actors","rng"})
        if(!data.contains(key))throw std::invalid_argument("Checkpoint field missing");
    if(extended && (!data.contains("numeric_profile") || data.at("numeric_profile")!="extended-health64"))
        throw std::invalid_argument("Checkpoint numeric profile mismatch");
    if(data.at("design_id")!="CUSTOM-0007" || data.at("engine")!=runtime())
        throw std::invalid_argument("Checkpoint schema or runtime mismatch");
    BattleCheckpoint result{};
    result.version=version;
    auto& state=result.snapshot;
    state.numeric_profile=extended?BattleNumericProfile::ExtendedHealth64:BattleNumericProfile::LegacyCustom;
    state.id=number<std::uint64_t>(data.at("id"));state.revision=number<std::uint64_t>(data.at("revision"));
    if(data.at("state")=="active") state.state=BattleState::Active;
    else if(data.at("state")=="finished") state.state=BattleState::Finished;
    else throw std::invalid_argument("Checkpoint state tag");
    if(!data.at("winner").is_null()) state.victorious_side=number<std::uint8_t>(data.at("winner"));
    const auto& actors=data.at("actors");
    if(!actors.is_array() || actors.size()!=28) throw std::invalid_argument("Checkpoint actor slots");
    for(std::size_t i=0;i<28;++i) if(!actors[i].is_null()) {
        const auto& a=actors[i];
        if(!a.is_array() || a.size()!=10) throw std::invalid_argument("Checkpoint actor record");
        const auto hp=extended?number<std::uint64_t>(a[2]):number<std::uint32_t>(a[2]);
        const auto max_hp=extended?number<std::uint64_t>(a[3]):number<std::uint32_t>(a[3]);
        state.actors[i]=BattleActor{number<std::uint8_t>(a[0]),number<std::uint64_t>(a[1]),
            hp,max_hp,number<std::uint32_t>(a[4]),number<std::uint32_t>(a[5]),
            number<std::uint32_t>(a[6]),number<std::uint32_t>(a[7]),number<std::uint32_t>(a[8]),number<std::uint32_t>(a[9])};
    }
    result.random_state=data.at("rng").get<std::string>();
    // Equality also rejects duplicate keys, extra fields and lossy numeric spellings.
    if(encode(result)!=text) throw std::invalid_argument("Noncanonical checkpoint document");
    return result;
}
}
