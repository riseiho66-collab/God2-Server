#include "db/OwnedBankCapacityProvision.h"
#include "db/Database.h"
#include <algorithm>
#include <limits>
#include <set>
#include <tuple>
namespace god2 {
namespace {
using Json=nlohmann::json;
Json root(const RecoveredCharacter& r) {
    return {{"account_id",r.account_id},{"character_id",r.id},{"slot",r.slot},
        {"profile",r.profile},{"created_at",r.created_at},{"name_codepage",r.name_codepage},
        {"streamer_privilege",r.streamer_privilege}};
}
bool token(std::string_view value) {
    return !value.empty()&&value.size()<=64&&value.find_first_not_of(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")==value.npos;
}
void require(bool value,const char* message){if(!value)throw DatabaseError(message);}
void exact_tree(const Json& value,unsigned depth=0) {
    require(depth<=32&&!value.is_number_float()&&!value.is_discarded()&&!value.is_binary(),"Capacity requires an exact bounded JSON tree");
    if(value.is_structured())for(const auto& child:value)exact_tree(child,depth+1);
}
}
nlohmann::json OwnedBankCapacityProvision::complete_material(const Tx::State& state) {
    Json cells=Json::array();
    for(const auto& cell:state.inventory.cells) {
        Json item=nullptr;
        if(cell.instance) {
            const auto& i=*cell.instance;Json aliases=Json::array();
            for(const auto& a:i.aliases)aliases.push_back({{"client_sha256",a.client_sha256},
                {"profile",a.profile},{"source_sha256",a.source_sha256},{"source_record",a.source_record},
                {"native_key",a.native_key},{"native_slot",a.native_slot},{"revision",a.revision},{"record",a.record}});
            item={{"id",i.id},{"definition_key",i.definition_key},{"quantity",i.quantity},
                {"revision",i.revision},{"stackable",i.stackable},{"acquisition_sha256",i.acquisition_sha256},
                {"acquisition_record",i.acquisition_record},{"aliases",std::move(aliases)}};
        }
        cells.push_back({{"location_kind",cell.location_kind},{"location_index",cell.location_index},{"instance",std::move(item)}});
    }
    const auto& i=state.inventory;const auto& e=state.equipment;const auto& p=e.position;
    return {{"inventory",{{"root",root(i.root)},{"revision",i.revision},
        {"source_sha256",i.source_sha256},{"source_record",i.source_record},{"cells",std::move(cells)}}},
        {"equipment",{{"root",root(e.root)},{"position",{{"area",p.area},{"scene",p.scene},{"x",p.x},{"y",p.y},{"revision",p.revision}}},
        {"client_sha256",e.client_sha256},{"record_kind",e.record_kind},{"source_sha256",e.source_sha256},
        {"source_record",e.source_record},{"record",e.record},{"revision",e.revision},{"actor_handle",e.actor_handle}}}};
}
nlohmann::json OwnedBankCapacityProvision::draft(const Tx::State& state,std::string_view identity) {
    return {{"format","god2-owned-bank-capacity-v1"},{"design_id","CUSTOM-0163"},
        {"database_identity",identity},{"account_id",state.inventory.root.account_id},{"character_id",state.inventory.root.id},
        {"expected_material",complete_material(state)},{"new_bank_indices",Json::array()},
        {"approved",false},{"permit_id",""},{"operator_note",""}};
}
OwnedBankCapacityProvision::Plan OwnedBankCapacityProvision::plan(
    const Json& manifest,const Tx::Before& before,std::string_view identity) {
    preflight(manifest);
    require(before.inventory&&before.equipment,"Capacity requires BOTH existing complete material sources; first import is not authorized");
    const Tx::State old{*before.inventory,*before.equipment};
    exact_tree(manifest);
    require(manifest.is_object()&&manifest.size()==10,"Invalid capacity manifest fields");
    for(const auto* key:{"format","design_id","database_identity","account_id","character_id","expected_material",
        "new_bank_indices","approved","permit_id","operator_note"})require(manifest.contains(key),"Missing capacity manifest field");
    require(manifest.at("format")=="god2-owned-bank-capacity-v1"&&manifest.at("design_id")=="CUSTOM-0163",
        "Capacity policy must explicitly select CUSTOM-0163");
    require(manifest.at("approved").is_boolean()&&manifest.at("approved").get<bool>(),"Capacity manifest has no explicit operator approval");
    require(manifest.at("database_identity").is_string()&&manifest.at("database_identity")==identity,
        "Capacity manifest database file identity mismatch");
    const auto exact_id=[&](const char* key,std::uint64_t id){const auto& v=manifest.at(key);
        return v.is_number_unsigned()&&v.get<std::uint64_t>()==id&&id>0;};
    require(exact_id("account_id",old.inventory.root.account_id)&&exact_id("character_id",old.inventory.root.id),
        "Capacity manifest full owner mismatch");
    require(manifest.at("expected_material")==complete_material(old),"Capacity manifest COMPLETE before material changed");
    require(manifest.at("permit_id").is_string()&&token(manifest.at("permit_id").get_ref<const std::string&>()),"Capacity permit_id must be a bounded ASCII operator token");
    const auto& note=manifest.at("operator_note");
    require(note.is_string()&&!note.get_ref<const std::string&>().empty()&&note.get_ref<const std::string&>().size()<=2048&&
        note.get_ref<const std::string&>().find('\0')==std::string::npos,"Capacity requires bounded operator provenance note");
    const auto& requested=manifest.at("new_bank_indices");
    require(requested.is_array()&&!requested.empty()&&requested.size()<=300,"Capacity must explicitly enumerate new cells");
    Plan result{before,old,manifest.at("permit_id").get<std::string>()};
    std::set<std::uint32_t> banks;
    for(const auto& cell:old.inventory.cells)if(cell.location_kind=="bank") {
        require(cell.location_index<300&&banks.insert(cell.location_index).second,"Existing bank namespace is not qualified");
    }
    for(const auto& index:requested) {
        require(index.is_number_unsigned(),"Capacity index must be an unsigned integer");
        const auto v=index.get<std::uint64_t>();
        require(v<300&&banks.insert(static_cast<std::uint32_t>(v)).second,"Capacity repeats/replaces an existing cell or exceeds six backing pages");
        result.next.inventory.cells.push_back({"bank",static_cast<std::uint32_t>(v),std::nullopt});
    }
    require(banks.size()==300,"Current whole-bank owner requires exactly300 explicit cells; enumerate every missing cell in the approved manifest");
    require(result.next.inventory.cells.size()<=4096,"Capacity exceeds existing complete population bound");
    std::sort(result.next.inventory.cells.begin(),result.next.inventory.cells.end(),[](const auto& a,const auto& b){
        return std::tie(a.location_kind,a.location_index)<std::tie(b.location_kind,b.location_index);});
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    require(old.inventory.revision>0&&old.inventory.revision<limit&&old.equipment.revision>0&&old.equipment.revision<limit,
        "Capacity revision cannot advance");
    ++result.next.inventory.revision;++result.next.equipment.revision;
    const auto marker=";CUSTOM-0163:capacity:"+result.permit_id;
    require(result.next.inventory.source_record.size()+marker.size()<=2048&&result.next.equipment.source_record.size()+marker.size()<=2048,
        "Capacity provenance exceeds existing storage bound");
    result.next.inventory.source_record+=marker;result.next.equipment.source_record+=marker;
    return result;
}
void OwnedBankCapacityProvision::preflight(const Json& manifest) {
    exact_tree(manifest);
    require(manifest.is_object()&&manifest.size()==10,"Invalid capacity manifest fields");
    for(const auto* key:{"format","design_id","database_identity","account_id","character_id","expected_material",
        "new_bank_indices","approved","permit_id","operator_note"})require(manifest.contains(key),"Missing capacity manifest field");
    require(manifest.at("format")=="god2-owned-bank-capacity-v1"&&manifest.at("design_id")=="CUSTOM-0163"&&
        manifest.at("database_identity").is_string()&&!manifest.at("database_identity").get_ref<const std::string&>().empty()&&
        manifest.at("database_identity").get_ref<const std::string&>().size()<=128,"Invalid capacity format/policy/file identity");
    require(manifest.at("approved").is_boolean()&&manifest.at("approved").get<bool>(),"Capacity requires explicit operator approval");
    for(const auto* key:{"account_id","character_id"}) {
        const auto& v=manifest.at(key);require(v.is_number_unsigned()&&v.get<std::uint64_t>()>0&&
            v.get<std::uint64_t>()<=0x7fffffffffffffffULL,"Capacity requires a positive full64 owner");
    }
    require(manifest.at("expected_material").is_object(),"Capacity requires complete expected material");
    require(manifest.at("permit_id").is_string()&&token(manifest.at("permit_id").get_ref<const std::string&>()),"Invalid capacity permit_id");
    const auto& note=manifest.at("operator_note");
    require(note.is_string()&&!note.get_ref<const std::string&>().empty()&&note.get_ref<const std::string&>().size()<=2048&&
        note.get_ref<const std::string&>().find('\0')==std::string::npos,"Capacity requires bounded operator provenance note");
    const auto& requested=manifest.at("new_bank_indices");
    require(requested.is_array()&&!requested.empty()&&requested.size()<=300,"Capacity must explicitly enumerate new cells");
    std::set<std::uint64_t> indices;
    for(const auto& v:requested)require(v.is_number_unsigned()&&v.get<std::uint64_t>()<300&&
        indices.insert(v.get<std::uint64_t>()).second,"Capacity has a duplicate/out-of-range/noninteger cell");
}
nlohmann::json OwnedBankCapacityProvision::parse(std::string_view text) {
    require(!text.empty()&&text.size()<=64u*1024u*1024u,"Capacity manifest exceeds bounded input");
    std::vector<std::set<std::string>> keys;
    auto callback=[&](int depth,Json::parse_event_t event,Json& value) {
        require(depth<=32,"Capacity manifest exceeds bounded nesting");
        if(event==Json::parse_event_t::object_start)keys.emplace_back();
        if(event==Json::parse_event_t::key)require(!keys.empty()&&keys.back().insert(value.get<std::string>()).second,"Capacity manifest duplicate key");
        if(event==Json::parse_event_t::object_end)keys.pop_back();
        require(!(event==Json::parse_event_t::value&&value.is_number_float()),"Capacity manifest forbids floating point numbers");
        return true;
    };
    auto manifest=Json::parse(text,callback,true,false);preflight(manifest);return manifest;
}
}
