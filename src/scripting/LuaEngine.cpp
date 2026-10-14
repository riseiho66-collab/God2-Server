#include "scripting/LuaEngine.h"
#include "scripting/LuaInstructionBudget.h"
#include "scripting/LuaLog.h"
#include "scripting/ScriptBindings.h"
#include "game/NativeSkillTargeting.h"
#include "game/FixtureBattle.h"
#include "game/ExtendedCoinAmount.h"

#include <nlohmann/json.hpp>
#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <limits>
#include <set>
#include <stdexcept>

namespace god2 {
namespace {
std::filesystem::path contained_path(const std::filesystem::path& root,
                                     const std::filesystem::path& candidate) {
    const auto path = std::filesystem::weakly_canonical(candidate);
    auto r = root.begin();
    auto p = path.begin();
    for (; r != root.end(); ++r, ++p) {
        if (p == path.end() || *p != *r)
            throw std::runtime_error("Lua path escapes script root: " + candidate.string());
    }
    return path;
}

[[noreturn]] void script_error(const std::string& message) {
    detail::lua_logger()->error("{}", message);
    throw std::runtime_error(message);
}

template<class... Args>
sol::protected_function_result invoke(sol::protected_function callback, Args&&... args) {
    detail::LuaInstructionBudget budget(callback.lua_state());
    if (budget.exhausted()) script_error(detail::LuaInstructionBudget::error_message);
    auto result = callback(std::forward<Args>(args)...);
    // A Lua pcall may catch the hook error; exhaustion still fails the host call.
    if (budget.exhausted()) script_error(detail::LuaInstructionBudget::error_message);
    if (!result.valid()) {
        const sol::error error = result;
        script_error(error.what());
    }
    return result;
}

template<class Map, class Key>
auto& lookup(Map& map, const Key& key, const char* kind) {
    auto it = map.find(key);
    if (it == map.end()) script_error(std::string("unavailable Lua ") + kind);
    return it->second;
}

std::string dialogue_string(const sol::object& value) {
    if (value.get_type() != sol::type::string)
        throw std::runtime_error("dialogue text must be a string");
    auto text = value.as<std::string>();
    if (text.size() > 16384) throw std::runtime_error("dialogue text exceeds 16384 bytes");
    return text;
}

std::int64_t catalog_selector(const sol::object& value, double minimum, double maximum,
                              const char* catalog = "native_map_catalog") {
    if (value.get_type() != sol::type::number)
        throw std::runtime_error(std::string(catalog) + " selectors must be integral numbers");
    const auto number = value.as<double>();
    if (!std::isfinite(number) || std::floor(number) != number ||
        number < minimum || number > maximum)
        throw std::runtime_error(std::string(catalog) + " selector out of bounds");
    return static_cast<std::int64_t>(number);
}

// CUSTOM-0090: exact owner-authorized calculation boundary, not a native rule.
// Unlike catalog selectors, wide HP/damage must never pass through double.
std::uint64_t exact_calculation_integer(const sol::object& value,
        std::uint64_t minimum,std::uint64_t maximum,const char* field) {
    static_assert(LUA_VERSION_NUM==504);
    static_assert(std::numeric_limits<lua_Integer>::is_signed &&
                  std::numeric_limits<lua_Integer>::digits==63);
    constexpr auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    if(minimum>maximum || maximum>limit || value.get_type()!=sol::type::number)
        throw std::runtime_error(std::string(field)+" requires an exact Lua integer");
    auto* lua=value.lua_state();
    const auto top=lua_gettop(lua);
    value.push();
    const bool integer=lua_isinteger(lua,-1)!=0;
    const lua_Integer number=integer?lua_tointeger(lua,-1):0;
    lua_settop(lua,top);
    if(!integer || number<0)
        throw std::runtime_error(std::string(field)+" requires an exact nonnegative Lua integer");
    const auto exact=static_cast<std::uint64_t>(number);
    if(exact<minimum || exact>maximum)
        throw std::runtime_error(std::string(field)+" integer out of bounds");
    return exact;
}

template<class Source>
sol::table catalog_provenance(sol::state_view lua, const Source& source) {
    return lua.create_table_with(
        "dataset_id", source.dataset_id, "source_path", source.source_path,
        "source_sha256", source.source_sha256, "decoded_sha256", source.decoded_sha256,
        "native_image_sha256", source.native_image_sha256, "source_section", source.source_section,
        "loader_rva", source.loader_rva, "lookup_rva", source.lookup_rva, "row_count", source.row_count);
}

sol::table catalog_snapshot(sol::state_view lua, const NativeMapRecord& record) {
    return lua.create_table_with(
        "source", catalog_provenance(lua, record.source), "source_record_index", record.source_record_index,
        "source_line", record.source_line, "record_sha256", record.record_sha256,
        "raw_record", std::string(record.raw_record.begin(), record.raw_record.end()),
        "area", record.area, "scene", record.scene, "kind", record.kind);
}

sol::table catalog_snapshot(sol::state_view lua, const NativeSkillRecord& record) {
    return lua.create_table_with(
        "source", catalog_provenance(lua, record.source), "source_record_index", record.source_record_index,
        "source_offset", record.source_offset, "record_sha256", record.record_sha256,
        "raw_record", std::string(record.raw_record.begin(), record.raw_record.end()),
        "kind", record.kind, "definition_id", record.definition_id,
        "client_mp_threshold", record.client_mp_threshold());
}

sol::table common_skill_snapshot(sol::state_view lua,const SharedSkillLookup& value) {
    const auto& d=value.definition;
    auto profiles=lua.create_table();
    for(std::size_t n=0;n<d.profiles.size();++n) {
        const auto& b=d.profiles[n];
        profiles[n+1]=lua.create_table_with(
            "region",b.region==SharedSkillRegion::Taiwan?"TW":"CN",
            "source",catalog_provenance(lua,b.source),
            "source_record_index",b.source_record_index,"source_offset",b.source_offset,
            "record_sha256",b.record_sha256,"row_qualification",shared_skill_qualification_name(b.qualification),
            "raw_record",std::string(b.raw.begin(),b.raw.end()),
            "raw_word_42",unsigned(b.raw[0x42])|(unsigned(b.raw[0x43])<<8));
    }
    const auto text=[&](const SharedSkillTextProjection& t) {
        auto result=lua.create_table_with("offset",t.offset,"limit_exclusive",t.limit_exclusive,
            "encoding",t.encoding,"bounded_raw",std::string(t.bounded_raw.begin(),t.bounded_raw.end()),
            "source_utf8",t.source_utf8,"traditional_utf8",t.traditional_utf8,
            "bounded_source_literal",t.pinned_literal,"native_ui_width_qualified",false);
        if(t.profile_index)result["profile_index"]=*t.profile_index+1;return result;
    };
    auto result=lua.create_table_with("canonical_key",d.canonical_key,
        "status",shared_skill_status_name(d.status),"profiles",profiles,
        "name",text(d.name),"short_text",text(d.short_text),"gameplay_authority",false,
        "requested_native_present",value.requested_native.has_value());
    // Owner display metadata is separate from the native bounded projection;
    // an absent profile has no invented CP950/CP936 bytes or native offset.
    result["display_name"]=d.owner_rule?d.owner_rule->traditional_name:d.name.traditional_utf8;
    if(d.owner_rule) {
        const auto& r=*d.owner_rule;
        result["owner_rule"]=lua.create_table_with("design_id",r.design_id,"key",r.key,
            "physical_power_percent",r.physical_power_percent,"mp_cost",r.mp_cost,
            "max_targets",r.max_targets,"all_living_opponents",r.all_living_opponents,
            "traditional_name",r.traditional_name,"source_type","existing_owner_rule_constants",
            "gameplay_authority",false,"native_source",false);
    }
    if(value.requested_native)result["requested_native"]=catalog_snapshot(lua,*value.requested_native);
    if(d.chosen_profile) {
        result["chosen_profile"]=*d.chosen_profile+1;
        const auto& raw=d.profiles[*d.chosen_profile].raw;
        result["common_raw_profile"]=std::string(raw.begin(),raw.end());
        result["physical_parameter_tail"]=std::string(raw.begin()+62,raw.end());
    }
    return result;
}

sol::table catalog_snapshot(sol::state_view lua, const NativeSkillBookRecord& record) {
    return lua.create_table_with(
        "source", catalog_provenance(lua, record.source),
        "source_record_index", record.source_record_index, "source_line", record.source_line,
        "decoded_offset", record.decoded_offset, "item_id", record.item_id,
        "kind", record.kind, "definition_id", record.definition_id,
        "record_sha256", record.record_sha256,
        "raw_record", std::string(record.raw_record.begin(), record.raw_record.end()),
        "parsed_sha256", record.parsed_sha256,
        "parsed_record", std::string(record.parsed_record.begin(), record.parsed_record.end()));
}

constexpr const char* target_api = "native_skill_target_setup";

void validate_fixture_combatant(const FixtureCombatant& value) {
    for (const auto field : {value.hp, value.max_hp, value.mp, value.max_mp,
                            value.physical_attack, value.magical_attack,
                            value.physical_defense, value.magical_defense}) {
        if (field > 1'000'000)
            throw std::runtime_error("fixture combat snapshot out of bounds");
    }
    if (value.hp > value.max_hp || value.mp > value.max_mp)
        throw std::runtime_error("fixture combat snapshot exceeds maximum HP/MP");
}

sol::table fixture_snapshot(sol::state_view lua, const FixtureCombatant& value) {
    return lua.create_table_with("hp", value.hp, "max_hp", value.max_hp,
        "mp", value.mp, "max_mp", value.max_mp,
        "physical_attack", value.physical_attack, "magical_attack", value.magical_attack,
        "physical_defense", value.physical_defense, "magical_defense", value.magical_defense);
}

sol::table target_array(const sol::object& value, int count) {
    if (value.get_type() != sol::type::table)
        throw std::runtime_error("native_skill_target_setup requires explicit state arrays");
    auto table = value.as<sol::table>();
    int actual = 0;
    for (const auto& entry : table) {
        catalog_selector(entry.first, 1, count, target_api);
        if (++actual > count)
            throw std::runtime_error("native_skill_target_setup state array length rejected");
    }
    if (actual != count)
        throw std::runtime_error("native_skill_target_setup state array length rejected");
    return table;
}

NativeSkillTargeting::State target_state(const sol::object& value) {
    if (value.get_type() != sol::type::table)
        throw std::runtime_error("native_skill_target_setup requires explicit state");
    auto table = value.as<sol::table>();
    int count = 0;
    for (const auto& entry : table) {
        if (entry.first.get_type() != sol::type::string)
            throw std::runtime_error("native_skill_target_setup unknown state field");
        const auto key = entry.first.as<std::string>();
        if (key != "masks" && key != "saved_masks" && key != "entity_words")
            throw std::runtime_error("native_skill_target_setup unknown state field");
        if (++count > 3) throw std::runtime_error("native_skill_target_setup unknown state field");
    }
    if (count != 3) throw std::runtime_error("native_skill_target_setup incomplete state");
    const auto masks = target_array(table.raw_get<sol::object>("masks"), 2);
    const auto saved = target_array(table.raw_get<sol::object>("saved_masks"), 2);
    const auto words = target_array(table.raw_get<sol::object>("entity_words"), 28);
    NativeSkillTargeting::State state;
    for (int i = 0; i < 2; ++i) {
        state.masks[i] = static_cast<std::uint32_t>(catalog_selector(
            masks.raw_get<sol::object>(i + 1), 0, 4294967295.0, target_api));
        state.saved_masks[i] = static_cast<std::uint32_t>(catalog_selector(
            saved.raw_get<sol::object>(i + 1), 0, 4294967295.0, target_api));
    }
    for (int i = 0; i < 28; ++i) {
        const auto word = words.raw_get<sol::object>(i + 1);
        if (word.get_type() == sol::type::boolean && !word.as<bool>())
            state.entity_words[i] = std::nullopt;
        else state.entity_words[i] = static_cast<std::int16_t>(
            catalog_selector(word, -32768, 32767, target_api));
    }
    return state;
}
}

struct LuaEngine::Vm {
    // Destruction order is intentional: Lua references die before the VM.
    sol::state lua;
    LuaRegistry registry;
    std::map<std::filesystem::path, sol::object> loaded;
    std::set<std::filesystem::path> loading;
    std::filesystem::path root;

    Vm(std::filesystem::path script_root, bool fixture_mode,
       std::shared_ptr<const NativeMapLookup> native_map_lookup,
       std::shared_ptr<const NativeSkillLookup> native_skill_lookup,
       std::shared_ptr<const NativeSkillBookLookup> native_skill_book_lookup,
       std::shared_ptr<const NativeWeaponLookup> native_weapon_lookup,
       std::shared_ptr<const NativeArmorLookup> native_armor_lookup,
       std::shared_ptr<const SharedSkillLookupFunction> common_skill_lookup) : root(std::move(script_root)) {
        lua.set_exception_handler([](lua_State* state, sol::optional<const std::exception&>, sol::string_view what) {
            detail::lua_logger()->error("{}", std::string(what.data(), what.size()));
            return sol::stack::push(state, what);
        });
        lua.open_libraries(sol::lib::base, sol::lib::table, sol::lib::string,
                           sol::lib::math, sol::lib::utf8);
        // No package, native modules, filesystem, OS, debug, or dynamic code loaders.
        for (const auto* name : {"dofile", "loadfile", "load", "collectgarbage", "print"})
            lua[name] = sol::nil;
        bind_scripts(lua, registry);
        lua["GOD2_FIXTURE_MODE"] = fixture_mode;
        // Capture ownership, never a reference to a constructor argument or retired VM.
        lua.set_function("native_map_catalog", [lookup = std::move(native_map_lookup)](
                sol::this_state state, sol::variadic_args args) -> sol::object {
            if (args.size() != 2)
                throw std::runtime_error("native_map_catalog requires exactly area and scene");
            const auto area = catalog_selector(args.get<sol::object>(0), 1, 16);
            const auto scene = catalog_selector(args.get<sol::object>(1), 0, 1023);
            if (!*lookup) throw std::runtime_error("native_map_catalog unavailable");
            const auto record = (*lookup)(area, scene);
            sol::state_view lua(state);
            if (!record) return sol::make_object(lua, sol::nil);
            return sol::make_object(lua, catalog_snapshot(lua, *record));
        });
        lua.set_function("native_skill_catalog", [lookup = native_skill_lookup](
                sol::this_state state, sol::variadic_args args) -> sol::object {
            if (args.size() != 2)
                throw std::runtime_error("native_skill_catalog requires exactly kind and definition_id");
            const auto kind = catalog_selector(args.get<sol::object>(0), 0, 3, "native_skill_catalog");
            const auto id = catalog_selector(args.get<sol::object>(1), 1, 255, "native_skill_catalog");
            if (!*lookup) throw std::runtime_error("native_skill_catalog unavailable");
            const auto record = (*lookup)(kind, id);
            sol::state_view lua(state);
            if (!record) return sol::make_object(lua, sol::nil);
            return sol::make_object(lua, catalog_snapshot(lua, *record));
        });
        lua.set_function("common_skill_definition",[lookup=std::move(common_skill_lookup)](
                sol::this_state state,sol::variadic_args args)->sol::object {
            if(args.size()!=2)throw std::runtime_error("common_skill_definition requires kind and definition_id");
            const auto kind=catalog_selector(args.get<sol::object>(0),0,3,"common_skill_definition");
            const auto id=catalog_selector(args.get<sol::object>(1),1,255,"common_skill_definition");
            if(!*lookup)throw std::runtime_error("common_skill_definition unavailable");
            const auto value=(*lookup)(kind,id);sol::state_view lua(state);
            if(!value)return sol::make_object(lua,sol::nil);
            return sol::make_object(lua,common_skill_snapshot(lua,*value));
        });
        lua.set_function("native_skill_book_catalog", [lookup = std::move(native_skill_book_lookup)](
                sol::this_state state, sol::variadic_args args) -> sol::object {
            if (args.size() != 2)
                throw std::runtime_error("native_skill_book_catalog requires exactly kind and definition_id");
            const auto kind = catalog_selector(args.get<sol::object>(0), 0, 3, "native_skill_book_catalog");
            const auto id = catalog_selector(args.get<sol::object>(1), 1, 255, "native_skill_book_catalog");
            if (!*lookup) throw std::runtime_error("native_skill_book_catalog unavailable");
            const auto record = (*lookup)(kind, id);
            sol::state_view lua(state);
            if (!record) return sol::make_object(lua, sol::nil);
            return sol::make_object(lua, catalog_snapshot(lua, *record));
        });
        lua.set_function("native_weapon_catalog", [lookup=std::move(native_weapon_lookup)](sol::this_state state,sol::variadic_args args)->sol::object {
            if(args.size()!=1)throw std::runtime_error("native_weapon_catalog requires exactly item_id");
            const auto item=catalog_selector(args.get<sol::object>(0),1,32767,"native_weapon_catalog");
            if(!*lookup)throw std::runtime_error("native_weapon_catalog unavailable");
            const auto record=(*lookup)(static_cast<std::uint16_t>(item));sol::state_view lua(state);
            if(!record)return sol::make_object(lua,sol::nil);
            const auto bytes=[](const std::vector<std::uint8_t>& value){return std::string(value.begin(),value.end());};
            return sol::make_object(lua,lua.create_table_with("item_id",record->item_id,"family",record->family,
                "source_record_index",record->source_record_index,"source_line",record->source_line,"decoded_offset",record->decoded_offset,
                "record_sha256",record->record_sha256,"parsed_sha256",record->parsed_sha256,"raw_record",bytes(record->raw_record),
                "parsed_record",bytes(record->parsed_record),"authority","NATIVE_PARSED_DEFINITION_ONLY"));
        });
        lua.set_function("native_armor_catalog", [lookup=std::move(native_armor_lookup)](sol::this_state state,sol::variadic_args args)->sol::object {
            if(args.size()!=1)throw std::runtime_error("native_armor_catalog requires exactly item_id");
            const auto item=catalog_selector(args.get<sol::object>(0),1,32767,"native_armor_catalog");
            if(!*lookup)throw std::runtime_error("native_armor_catalog unavailable");
            const auto record=(*lookup)(static_cast<std::uint16_t>(item));sol::state_view lua(state);
            if(!record)return sol::make_object(lua,sol::nil);
            const auto bytes=[](const std::vector<std::uint8_t>& value){return std::string(value.begin(),value.end());};
            return sol::make_object(lua,lua.create_table_with("item_id",record->item_id,"family",record->family,
                "source_record_index",record->source_record_index,"source_line",record->source_line,"decoded_offset",record->decoded_offset,
                "record_sha256",record->record_sha256,"parsed_sha256",record->parsed_sha256,"raw_record",bytes(record->raw_record),
                "parsed_record",bytes(record->parsed_record),"authority","NATIVE_PARSED_DEFINITION_ONLY"));
        });
        lua.set_function(target_api, [lookup = std::move(native_skill_lookup)](
                sol::this_state state, sol::variadic_args args) -> sol::object {
            if (args.size() != 4)
                throw std::runtime_error("native_skill_target_setup requires kind, id, actor and state");
            const auto kind = catalog_selector(args.get<sol::object>(0), 0, 3, target_api);
            const auto id = catalog_selector(args.get<sol::object>(1), 1, 255, target_api);
            const auto actor = catalog_selector(args.get<sol::object>(2), 0, 13, target_api);
            const auto input = target_state(args.get<sol::object>(3));
            if (!*lookup) throw std::runtime_error("native_skill_target_setup unavailable");
            const auto record = (*lookup)(kind, id);
            sol::state_view lua(state);
            if (!record) return sol::make_object(lua, sol::nil);
            const auto fields = NativeSkillTargeting::from_record(record->raw_record);
            if (fields.kind != kind || fields.definition_id != id ||
                record->kind != kind || record->definition_id != id)
                throw std::runtime_error("native_skill_target_setup definition identity mismatch");
            const auto result = NativeSkillTargeting::evaluate(fields, static_cast<unsigned>(actor), input);
            auto output = lua.create_table_with(
                "masks", lua.create_table_with(1, result.masks[0], 2, result.masks[1]),
                "saved_masks", lua.create_table_with(1, result.saved_masks[0], 2, result.saved_masks[1]),
                "stored_mode", result.stored_mode, "passes_kind_gate", result.passes_kind_gate,
                "setup_valid", result.setup.has_value(), "source", catalog_provenance(lua, record->source),
                "record_sha256", record->record_sha256);
            if (result.setup) {
                output["setup_value"] = result.setup->first;
                output["setup_flag"] = result.setup->second;
            }
            return sol::make_object(lua, output);
        });
        lua.set_function("require", [this](const std::string& module) {
            if (module.empty() || module.size() > 256)
                throw std::runtime_error("invalid Lua module name");
            std::string relative;
            bool component_start = true;
            for (const char c : module) {
                if (c == '.') {
                    if (component_start) throw std::runtime_error("invalid Lua module name");
                    relative += '/';
                    component_start = true;
                } else {
                    const bool letter = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_';
                    if (!letter && (component_start || c < '0' || c > '9'))
                        throw std::runtime_error("invalid Lua module name");
                    relative += c;
                    component_start = false;
                }
            }
            if (component_start) throw std::runtime_error("invalid Lua module name");
            return execute(contained_path(root, root / (relative + ".lua")));
        });
    }

    sol::object execute(const std::filesystem::path& path) {
        if (auto it = loaded.find(path); it != loaded.end()) return it->second;
        if (!loading.insert(path).second)
            throw std::runtime_error("cyclic Lua require: " + path.string());
        try {
            auto chunk = lua.load_file(path.string(), sol::load_mode::text);
            if (!chunk.valid()) {
                const sol::error error = chunk;
                throw std::runtime_error(error.what());
            }
            sol::protected_function callback = chunk;
            auto result = invoke(callback);
            sol::object value = sol::make_object(lua, true);
            if (result.return_count() > 0) {
                sol::object returned = result.get<sol::object>();
                if (returned.valid() && returned.get_type() != sol::type::nil) value = returned;
            }
            loaded.emplace(path, value);
            loading.erase(path);
            return value;
        } catch (...) {
            loading.erase(path);
            throw;
        }
    }

    sol::table player(const ScriptPlayer& value) {
        // Decimal strings preserve every uint64 value on all Lua numeric builds.
        return lua.create_table_with("id", std::to_string(value.id), "name", value.name);
    }
    sol::table monster(const ScriptMonster& value) {
        if (!value.hp) script_error("monster HP is unavailable");
        return lua.create_table_with("id", std::to_string(value.id),
                                     "template_id", value.template_id, "hp", *value.hp);
    }
};

LuaEngine::LuaEngine(std::filesystem::path script_root, bool fixture_mode,
                     NativeMapLookup native_map_lookup, NativeSkillLookup native_skill_lookup,
                     NativeSkillBookLookup native_skill_book_lookup,NativeWeaponLookup native_weapon_lookup,
                     NativeArmorLookup native_armor_lookup,
                     SharedSkillLookupFunction common_skill_lookup)
    : root_(std::filesystem::weakly_canonical(std::filesystem::absolute(script_root))),
      fixture_mode_(fixture_mode),
      native_map_lookup_(std::make_shared<const NativeMapLookup>(std::move(native_map_lookup))),
      native_skill_lookup_(std::make_shared<const NativeSkillLookup>(std::move(native_skill_lookup))),
      native_skill_book_lookup_(std::make_shared<const NativeSkillBookLookup>(std::move(native_skill_book_lookup))),
      native_weapon_lookup_(std::make_shared<const NativeWeaponLookup>(std::move(native_weapon_lookup))),
      native_armor_lookup_(std::make_shared<const NativeArmorLookup>(std::move(native_armor_lookup))),
      common_skill_lookup_(std::make_shared<const SharedSkillLookupFunction>(std::move(common_skill_lookup))) {}
LuaEngine::~LuaEngine() = default;

void LuaEngine::check_thread() const {
    if (owner_ != std::thread::id{} && owner_ != std::this_thread::get_id())
        throw std::runtime_error("LuaEngine must run on its initialization thread");
}

LuaEngine::Vm& LuaEngine::vm() {
    check_thread();
    if (!vm_) script_error("LuaEngine is not initialized");
    return *vm_;
}

bool LuaEngine::initialize() {
    check_thread();
    if (vm_) return true;
    owner_ = std::this_thread::get_id();
    try {
        vm_ = std::make_unique<Vm>(root_, fixture_mode_, native_map_lookup_, native_skill_lookup_,
                                   native_skill_book_lookup_,native_weapon_lookup_,native_armor_lookup_,common_skill_lookup_);
        return true;
    } catch (const std::exception& error) {
        detail::lua_logger()->error("initialization failed: {}", error.what());
        return false;
    }
}

std::filesystem::path LuaEngine::resolve(const std::filesystem::path& path) const {
    if (path.empty()) throw std::runtime_error("empty Lua script path");
    if (path.is_absolute()) return contained_path(root_, path);
    // Accept root-relative paths and existing CWD paths such as scripts/bootstrap.lua.
    if (std::filesystem::exists(path)) {
        const auto absolute = std::filesystem::weakly_canonical(path);
        try { return contained_path(root_, absolute); }
        catch (const std::runtime_error&) { /* Try the explicit script root below. */ }
    }
    return contained_path(root_, root_ / path);
}

bool LuaEngine::rebuild(const std::vector<Entry>& entries) {
    check_thread();
    if (!vm_) { detail::lua_logger()->error("load requires initialize()"); return false; }
    try {
        auto staged = std::make_unique<Vm>(root_, fixture_mode_, native_map_lookup_, native_skill_lookup_,
                                           native_skill_book_lookup_,native_weapon_lookup_,native_armor_lookup_,common_skill_lookup_);
        for (const auto& entry : entries) {
            const auto path = contained_path(root_, entry.path);
            if (!entry.directory) {
                staged->execute(path);
            } else {
                std::vector<std::filesystem::path> files;
                for (const auto& file : std::filesystem::recursive_directory_iterator(path)) {
                    if (file.is_regular_file() && file.path().extension() == ".lua")
                        files.push_back(contained_path(root_, file.path()));
                }
                std::sort(files.begin(), files.end());
                for (const auto& file : files) staged->execute(file);
            }
        }
        // Allocate the entry list before committing either piece of active state.
        auto committed_entries = entries;
        vm_.swap(staged);
        entries_.swap(committed_entries);
        return true;
    } catch (const std::exception& error) {
        detail::lua_logger()->error("script transaction failed; previous VM retained: {}", error.what());
        return false;
    }
}

bool LuaEngine::load_script(const std::filesystem::path& path) {
    check_thread();
    try {
        const auto file = resolve(path);
        auto entries = entries_;
        if (std::none_of(entries.begin(), entries.end(), [&](const Entry& e) {
                return !e.directory && e.path == file;
            })) entries.push_back({file, false});
        return rebuild(entries);
    } catch (const std::exception& error) {
        detail::lua_logger()->error("load_script: {}", error.what());
        return false;
    }
}

bool LuaEngine::load_directory(const std::filesystem::path& path) {
    check_thread();
    try {
        const auto directory = resolve(path);
        if (!std::filesystem::is_directory(directory))
            throw std::runtime_error("Lua script directory does not exist");
        auto entries = entries_;
        if (std::none_of(entries.begin(), entries.end(), [&](const Entry& e) {
                return e.directory && e.path == directory;
            })) entries.push_back({directory, true});
        return rebuild(entries);
    } catch (const std::exception& error) {
        detail::lua_logger()->error("load_directory: {}", error.what());
        return false;
    }
}

bool LuaEngine::reload_all() { return rebuild(entries_); }

bool LuaEngine::has_npc(std::uint32_t npc_id) const {
    check_thread();
    return vm_ && vm_->registry.npcs.contains(npc_id);
}

FixtureDamage LuaEngine::fixture_damage(const FixtureCombatant& attacker,
                                       const FixtureCombatant& defender,
                                       std::uint8_t skill, std::uint32_t roll) {
    auto& state = vm();
    if (!fixture_mode_) throw std::runtime_error("fixture combat requires fixture mode");
    if (skill < 1 || skill > 3 || roll >= 10'000)
        throw std::runtime_error("fixture combat skill or roll out of bounds");
    validate_fixture_combatant(attacker);
    validate_fixture_combatant(defender);
    const auto module = state.execute(contained_path(root_, root_ / "fixtures/combat.lua"));
    if (module.get_type() != sol::type::table)
        throw std::runtime_error("fixture combat module must return a table");
    const auto callback = module.as<sol::table>().raw_get<sol::object>("damage");
    if (callback.get_type() != sol::type::function)
        throw std::runtime_error("fixture combat module must provide a damage function");
    auto result = invoke(callback.as<sol::protected_function>(),
                         fixture_snapshot(state.lua, attacker), fixture_snapshot(state.lua, defender),
                         skill, roll);
    if (result.return_count() != 1 || result.get_type() != sol::type::table)
        throw std::runtime_error("fixture combat damage must return one table");
    const auto output = result.get<sol::table>();
    FixtureDamage damage{};
    damage.damage = static_cast<std::uint32_t>(catalog_selector(
        output.raw_get<sol::object>("damage"), 1, 1'000'000, "fixture combat damage"));
    damage.mp_cost = static_cast<std::uint32_t>(catalog_selector(
        output.raw_get<sol::object>("mp_cost"), 0, 1'000'000, "fixture combat mp_cost"));
    const auto critical = output.raw_get<sol::object>("critical");
    if (critical.get_type() != sol::type::boolean)
        throw std::runtime_error("fixture combat critical must be a boolean");
    damage.critical = critical.as<bool>();
    return damage;
}

CombatRuleResult LuaEngine::combat_damage(const CombatRuleInput& input) {
    if(input.numeric_profile!=BattleNumericProfile::LegacyCustom &&
       input.numeric_profile!=BattleNumericProfile::ExtendedHealth64)
        throw std::invalid_argument("Unknown combat numeric profile");
    if(input.numeric_profile==BattleNumericProfile::ExtendedHealth64) {
        // CUSTOM-0090 keeps CUSTOM-0006 coefficients and rounding order. The
        // full uint32 stat representation fits signed64 products under these
        // original percent bounds; only the legacy 1m clipping is absent.
        static_assert(LUA_VERSION_NUM==504);
        static_assert(std::numeric_limits<lua_Integer>::is_signed &&
                      std::numeric_limits<lua_Integer>::digits==63);
        if(input.power_percent>10'000 || input.defense_percent>100 ||
           input.mp_cost>1'000'000 || input.available_mp>1'000'000 ||
           input.mp_cost>input.available_mp || input.critical_chance_bp>10'000 ||
           input.critical_multiplier_percent<100 || input.critical_multiplier_percent>1'000 ||
           input.roll>=10'000)
            throw std::invalid_argument("Extended combat rule input exceeds explicit bounds or available MP");
        auto& state=vm();
        const auto module=state.execute(contained_path(root_,root_/"gameplay/combat_health64.lua"));
        if(module.get_type()!=sol::type::table)
            throw std::runtime_error("Extended combat module must return a table");
        const auto callback=module.as<sol::table>().raw_get<sol::object>("damage");
        if(callback.get_type()!=sol::type::function)
            throw std::runtime_error("Extended combat module must provide damage");
        auto snapshot=state.lua.create_table();
        snapshot["attack"]=static_cast<lua_Integer>(input.attack);
        snapshot["defense"]=static_cast<lua_Integer>(input.defense);
        snapshot["power_percent"]=static_cast<lua_Integer>(input.power_percent);
        snapshot["defense_percent"]=static_cast<lua_Integer>(input.defense_percent);
        snapshot["mp_cost"]=static_cast<lua_Integer>(input.mp_cost);
        snapshot["available_mp"]=static_cast<lua_Integer>(input.available_mp);
        snapshot["critical_chance_bp"]=static_cast<lua_Integer>(input.critical_chance_bp);
        snapshot["critical_multiplier_percent"]=static_cast<lua_Integer>(input.critical_multiplier_percent);
        snapshot["roll"]=static_cast<lua_Integer>(input.roll);
        auto result=invoke(callback.as<sol::protected_function>(),snapshot);
        if(result.return_count()!=1 || result.get_type()!=sol::type::table)
            throw std::runtime_error("Extended combat damage must return one table");
        const auto output=result.get<sol::table>();
        constexpr auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
        CombatRuleResult value{};
        value.damage=exact_calculation_integer(output.raw_get<sol::object>("damage"),1,limit,"extended combat damage");
        value.mp_cost=static_cast<std::uint32_t>(exact_calculation_integer(
            output.raw_get<sol::object>("mp_cost"),0,1'000'000,"extended combat MP"));
        const auto critical=output.raw_get<sol::object>("critical");
        if(critical.get_type()!=sol::type::boolean || value.mp_cost!=input.mp_cost)
            throw std::runtime_error("Extended combat result changed explicit cost or critical type");
        value.critical=critical.as<bool>();
        return value;
    }
    auto& state = vm();
    // CUSTOM-0006 stays the existing bounded formula. Its largest integer
    // intermediate is at most 100,000,000,000 under the unchanged input gates.
    // A wider result field does not authorize rounded wide Lua calculations.
    static_assert(std::numeric_limits<lua_Number>::radix==2 &&
                  std::numeric_limits<lua_Number>::digits>=53);
    static_assert(std::numeric_limits<double>::radix==2 &&
                  std::numeric_limits<double>::digits>=53);
    if (input.attack > 1'000'000 || input.defense > 1'000'000 ||
        input.power_percent > 10'000 || input.defense_percent > 100 ||
        input.mp_cost > 1'000'000 || input.available_mp > 1'000'000 ||
        input.mp_cost > input.available_mp || input.critical_chance_bp > 10'000 ||
        input.critical_multiplier_percent < 100 || input.critical_multiplier_percent > 1'000 ||
        input.roll >= 10'000)
        throw std::invalid_argument("Custom combat rule input exceeds bounds or available MP");
    const auto module = state.execute(contained_path(root_, root_ / "gameplay/combat.lua"));
    if (module.get_type() != sol::type::table)
        throw std::runtime_error("Combat module must return a table");
    const auto callback = module.as<sol::table>().raw_get<sol::object>("damage");
    if (callback.get_type() != sol::type::function)
        throw std::runtime_error("Combat module must provide damage");
    auto snapshot = state.lua.create_table();
    snapshot["attack"] = input.attack;
    snapshot["defense"] = input.defense;
    snapshot["power_percent"] = input.power_percent;
    snapshot["defense_percent"] = input.defense_percent;
    snapshot["mp_cost"] = input.mp_cost;
    snapshot["available_mp"] = input.available_mp;
    snapshot["critical_chance_bp"] = input.critical_chance_bp;
    snapshot["critical_multiplier_percent"] = input.critical_multiplier_percent;
    snapshot["roll"] = input.roll;
    auto result = invoke(callback.as<sol::protected_function>(), snapshot);
    if (result.return_count() != 1 || result.get_type() != sol::type::table)
        throw std::runtime_error("Combat damage must return one table");
    const auto output = result.get<sol::table>();
    CombatRuleResult value{};
    // The selector checks finite, integral and the original [1,1m] bounds
    // before conversion; every admitted integer is exactly representable.
    value.damage = static_cast<std::uint64_t>(catalog_selector(
        output.raw_get<sol::object>("damage"), 1, 1'000'000, "combat damage"));
    value.mp_cost = static_cast<std::uint32_t>(catalog_selector(
        output.raw_get<sol::object>("mp_cost"), 0, 1'000'000, "combat mp_cost"));
    const auto critical = output.raw_get<sol::object>("critical");
    if (critical.get_type() != sol::type::boolean || value.mp_cost != input.mp_cost)
        throw std::runtime_error("Combat result changed explicit cost or critical type");
    value.critical = critical.as<bool>();
    return value;
}

ProgressionResult LuaEngine::progression(const ProgressionInput& input) {
    auto& state=vm();
    constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    const auto& thresholds=input.cumulative_thresholds;
    if(input.total_experience>maximum || thresholds.empty() || thresholds.size()>255 || thresholds.front()!=0 ||
       !input.unlocked_level || input.unlocked_level>thresholds.size())
        throw std::invalid_argument("Invalid explicit progression policy");
    for(std::size_t i=1;i<thresholds.size();++i)
        if(thresholds[i]<=thresholds[i-1] || thresholds[i]-thresholds[i-1]>maximum/10000)
            throw std::invalid_argument("Progression thresholds unsorted or interval exceeds exact arithmetic range");
    if(thresholds.back()>maximum) throw std::invalid_argument("Progression threshold overflow");
    const auto module=state.execute(contained_path(root_,root_/"gameplay/progression.lua"));
    if(module.get_type()!=sol::type::table) throw std::runtime_error("Progression module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("project");
    if(callback.get_type()!=sol::type::function) throw std::runtime_error("Progression module requires project");
    auto snapshot=state.lua.create_table();
    auto table=state.lua.create_table();
    for(std::size_t i=0;i<thresholds.size();++i) table[i+1]=static_cast<std::int64_t>(thresholds[i]);
    snapshot["thresholds"]=table;
    snapshot["total"]=static_cast<std::int64_t>(input.total_experience);
    snapshot["unlocked_level"]=input.unlocked_level;
    auto result=invoke(callback.as<sol::protected_function>(),snapshot);
    if(result.return_count()!=1 || result.get_type()!=sol::type::table)
        throw std::runtime_error("Progression must return one table");
    const auto output=result.get<sol::table>();
    ProgressionResult value{
        static_cast<std::uint16_t>(catalog_selector(output.raw_get<sol::object>("level"),1,input.unlocked_level,"progression level")),
        static_cast<std::uint16_t>(catalog_selector(output.raw_get<sol::object>("progress_display"),0,10000,"progression display"))};
    if(thresholds[value.level-1]>input.total_experience)
        throw std::runtime_error("Progression returned unearned level");
    return value;
}

CharacterGrowthResult LuaEngine::character_growth(const CharacterGrowthInput& input) {
    auto& state=vm();
    const auto profession=static_cast<unsigned>(input.profession);
    if(profession<1 || profession>4 || input.previous_level<1 || input.next_level<input.previous_level ||
       input.next_level>255)
        throw std::invalid_argument("Invalid trusted character growth input");
    const auto module=state.execute(contained_path(root_,root_/"gameplay/character_growth.lua"));
    if(module.get_type()!=sol::type::table) throw std::runtime_error("Character growth module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("project");
    if(callback.get_type()!=sol::type::function) throw std::runtime_error("Character growth requires project");
    auto attributes=state.lua.create_table();
    for(unsigned i=0;i<4;++i) attributes[i+1]=input.attributes[i];
    auto snapshot=state.lua.create_table_with("profession",profession,"previous_level",input.previous_level,
        "next_level",input.next_level,"attributes",attributes,"unspent_points",input.unspent_points);
    auto result=invoke(callback.as<sol::protected_function>(),snapshot);
    if(result.return_count()!=1 || result.get_type()!=sol::type::table)
        throw std::runtime_error("Character growth must return one table");
    const auto output=result.get<sol::table>();
    const auto values=output.raw_get<sol::object>("attributes");
    if(values.get_type()!=sol::type::table) throw std::runtime_error("Character growth requires attributes");
    CharacterGrowthResult value;
    for(unsigned i=0;i<4;++i) value.attributes[i]=static_cast<std::uint16_t>(catalog_selector(
        values.as<sol::table>().raw_get<sol::object>(i+1),input.attributes[i],65535,"character attribute"));
    value.unspent_points=static_cast<std::uint16_t>(catalog_selector(output.raw_get<sol::object>("unspent_points"),
        input.unspent_points,32767,"character unspent points"));
    // Native status displays the points WORD as signed. Refuse overflow rather than wrap.
    if(static_cast<unsigned>(value.unspent_points-input.unspent_points)!=
       4u*static_cast<unsigned>(input.next_level-input.previous_level))
        throw std::runtime_error("Character growth manual budget mismatch");
    return value;
}

CharacterGrowthResult LuaEngine::allocate_attribute(const CharacterAllocationInput& input) {
    if(input.selector<1 || input.selector>4 || input.unspent_points<1 || input.unspent_points>32767)
        throw std::invalid_argument("Invalid trusted allocation budget or selector");
    constexpr std::array<unsigned,4> indices{2,0,1,3};
    const auto selected=indices[input.selector-1];
    if(input.attributes[selected]==65535)throw std::invalid_argument("Allocation exceeds native snapshot width");
    auto& state=vm();
    const auto module=state.execute(contained_path(root_,root_/"gameplay/character_growth.lua"));
    if(module.get_type()!=sol::type::table)throw std::runtime_error("Allocation module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("allocate");
    if(callback.get_type()!=sol::type::function)throw std::runtime_error("Allocation requires allocate");
    auto attributes=state.lua.create_table();
    for(unsigned i=0;i<4;++i)attributes[i+1]=input.attributes[i];
    auto snapshot=state.lua.create_table_with("selector",input.selector,"attributes",attributes,"unspent_points",input.unspent_points);
    auto result=invoke(callback.as<sol::protected_function>(),snapshot);
    if(result.return_count()!=1 || result.get_type()!=sol::type::table)throw std::runtime_error("Allocation must return table");
    const auto output=result.get<sol::table>();const auto values=output.raw_get<sol::object>("attributes");
    if(values.get_type()!=sol::type::table)throw std::runtime_error("Allocation requires attributes");
    CharacterGrowthResult value;
    for(unsigned i=0;i<4;++i) {
        const auto expected=static_cast<unsigned>(input.attributes[i])+(i==selected?1:0);
        value.attributes[i]=static_cast<std::uint16_t>(catalog_selector(values.as<sol::table>().raw_get<sol::object>(i+1),
            expected,expected,"allocated attribute"));
    }
    value.unspent_points=static_cast<std::uint16_t>(catalog_selector(output.raw_get<sol::object>("unspent_points"),
        input.unspent_points-1,input.unspent_points-1,"allocation budget"));
    return value;
}

SupplyResult LuaEngine::supply(const SupplyInput& input) {
    if(input.numeric_profile!=BattleNumericProfile::LegacyCustom &&
       input.numeric_profile!=BattleNumericProfile::ExtendedHealth64)
        throw std::invalid_argument("Unknown supply numeric profile");
    if(input.numeric_profile==BattleNumericProfile::ExtendedHealth64) {
        // CUSTOM-0091 extends exact representation of the unchanged
        // CUSTOM-0016 headroom/non-revival policy, not item recovery amounts.
        constexpr auto hp_limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
        constexpr auto mp_limit=static_cast<std::uint32_t>(std::numeric_limits<std::int32_t>::max());
        if(!input.max_hp || input.hp>input.max_hp || input.mp>input.max_mp ||
           input.hp>hp_limit || input.max_hp>hp_limit || input.restore_hp>hp_limit ||
           input.max_mp>mp_limit || input.restore_mp>mp_limit ||
           (!input.restore_hp && !input.restore_mp))
            throw std::invalid_argument("Invalid extended supply snapshot or explicit recovery amount");
        auto& state=vm();
        const auto module=state.execute(contained_path(root_,root_/"gameplay/supply.lua"));
        if(module.get_type()!=sol::type::table)
            throw std::runtime_error("Supply module must return table");
        const auto callback=module.as<sol::table>().raw_get<sol::object>("project");
        if(callback.get_type()!=sol::type::function)
            throw std::runtime_error("Supply module requires project");
        // Every admitted field is an exact signed64 Lua integer. The module
        // adds only min(restore,maximum-current), so neither sum overflows.
        auto snapshot=state.lua.create_table_with(
            "hp",static_cast<lua_Integer>(input.hp),
            "max_hp",static_cast<lua_Integer>(input.max_hp),
            "mp",static_cast<lua_Integer>(input.mp),
            "max_mp",static_cast<lua_Integer>(input.max_mp),
            "restore_hp",static_cast<lua_Integer>(input.restore_hp),
            "restore_mp",static_cast<lua_Integer>(input.restore_mp));
        auto result=invoke(callback.as<sol::protected_function>(),snapshot);
        if(result.return_count()!=1 || result.get_type()!=sol::type::table)
            throw std::runtime_error("Supply must return one table");
        const auto output=result.get<sol::table>();
        SupplyResult value{
            exact_calculation_integer(output.raw_get<sol::object>("hp"),input.hp,input.max_hp,"extended supply HP"),
            static_cast<std::uint32_t>(exact_calculation_integer(
                output.raw_get<sol::object>("mp"),input.mp,input.max_mp,"extended supply MP")),false};
        const auto consume=output.raw_get<sol::object>("consume");
        if(consume.get_type()!=sol::type::boolean)
            throw std::runtime_error("Supply consumption must be boolean");
        value.consume=consume.as<bool>();
        if(value.hp-input.hp>input.restore_hp || value.mp-input.mp>input.restore_mp ||
           value.consume!=(value.hp!=input.hp || value.mp!=input.mp) ||
           (!input.hp && (value.hp || value.mp!=input.mp || value.consume)))
            throw std::runtime_error("Supply result violates recovery or consumption bounds");
        return value;
    }
    auto& state = vm();
    constexpr auto limit = static_cast<std::uint32_t>(std::numeric_limits<std::int32_t>::max());
    if (!input.max_hp || input.hp > input.max_hp || input.mp > input.max_mp ||
        input.max_hp > limit || input.max_mp > limit || input.restore_hp > limit ||
        input.restore_mp > limit || (!input.restore_hp && !input.restore_mp))
        throw std::invalid_argument("Invalid supply snapshot or explicit recovery amount");
    // Wide C++ fields enter the retained legacy Lua/selector path only after
    // the original signed32 bounds; no implicit narrowing supplies its inputs.
    const auto legacy_hp=static_cast<std::uint32_t>(input.hp);
    const auto legacy_max_hp=static_cast<std::uint32_t>(input.max_hp);
    const auto legacy_restore_hp=static_cast<std::uint32_t>(input.restore_hp);
    const auto module = state.execute(contained_path(root_, root_ / "gameplay/supply.lua"));
    if (module.get_type() != sol::type::table)
        throw std::runtime_error("Supply module must return table");
    const auto callback = module.as<sol::table>().raw_get<sol::object>("project");
    if (callback.get_type() != sol::type::function)
        throw std::runtime_error("Supply module requires project");
    auto snapshot = state.lua.create_table_with(
        "hp", legacy_hp, "max_hp", legacy_max_hp, "mp", input.mp, "max_mp", input.max_mp,
        "restore_hp", legacy_restore_hp, "restore_mp", input.restore_mp);
    auto result = invoke(callback.as<sol::protected_function>(), snapshot);
    if (result.return_count() != 1 || result.get_type() != sol::type::table)
        throw std::runtime_error("Supply must return one table");
    const auto output = result.get<sol::table>();
    SupplyResult value{
        static_cast<std::uint64_t>(catalog_selector(output.raw_get<sol::object>("hp"), legacy_hp, legacy_max_hp, "supply HP")),
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("mp"), input.mp, input.max_mp, "supply MP")), false};
    const auto consume = output.raw_get<sol::object>("consume");
    if (consume.get_type() != sol::type::boolean)
        throw std::runtime_error("Supply consumption must be boolean");
    value.consume = consume.as<bool>();
    if (value.hp - input.hp > input.restore_hp || value.mp - input.mp > input.restore_mp ||
        value.consume != (value.hp != input.hp || value.mp != input.mp) ||
        (!input.hp && (value.hp || value.mp != input.mp || value.consume)))
        throw std::runtime_error("Supply result violates recovery or consumption bounds");
    return value;
}

std::optional<std::uint8_t> LuaEngine::beast_equipment_destination(std::uint8_t source,
        const std::vector<std::uint8_t>& empty_slots){
    auto& state=vm();
    if(source>=30&&source!=37)throw std::invalid_argument("Beast equipment source outside bag/37");
    std::array<bool,30> seen{};
    for(const auto slot:empty_slots){
        if(slot>=30||seen[slot])throw std::invalid_argument("Beast equipment empty capacity duplicated/outside bag");
        seen[slot]=true;
    }
    const auto module=state.execute(contained_path(root_,root_/"gameplay/beast_equipment.lua"));
    if(module.get_type()!=sol::type::table)throw std::runtime_error("Beast equipment module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("destination");
    if(callback.get_type()!=sol::type::function)throw std::runtime_error("Beast equipment module requires destination");
    auto slots=state.lua.create_table();
    for(std::size_t i=0;i<empty_slots.size();++i)slots[i+1]=empty_slots[i];
    auto snapshot=state.lua.create_table_with("source_slot",source,"owned_empty_slots",slots);
    auto result=invoke(callback.as<sol::protected_function>(),snapshot);
    if(result.return_count()!=1)throw std::runtime_error("Beast equipment rule must return one destination or nil");
    if(result.get_type()==sol::type::nil)return {};
    const auto selected=static_cast<std::uint8_t>(catalog_selector(result.get<sol::object>(),0,49,"beast equipment destination"));
    if((source<30&&selected!=37)||(source==37&&(selected>=30||!seen[selected])))throw std::runtime_error("Beast equipment rule escapes explicitly owned destination");
    return selected;
}

bool LuaEngine::beast_discard_allowed(std::uint8_t source,std::uint8_t quantity,
        bool exploring,bool alternate7,bool alternate8){
    if(source>=30||quantity!=1)return false;
    auto& state=vm();
    const auto module=state.execute(contained_path(root_,root_/"gameplay/beast_discard.lua"));
    if(module.get_type()!=sol::type::table)throw std::runtime_error("Beast discard module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("allowed");
    if(callback.get_type()!=sol::type::function)throw std::runtime_error("Beast discard module requires allowed");
    auto result=invoke(callback.as<sol::protected_function>(),state.lua.create_table_with(
        "source_slot",source,"quantity",quantity,"native_exploring",exploring,
        "alternate_control7",alternate7,"alternate_control8",alternate8));
    if(result.return_count()!=1||result.get_type()!=sol::type::boolean)
        throw std::runtime_error("Beast discard policy must return one boolean");
    // A script cannot override the independently admitted presentation domain.
    return result.get<bool>()&&!exploring&&!alternate7&&!alternate8;
}

bool LuaEngine::beast_transfer_allowed(std::uint8_t source,std::uint8_t quantity,
        bool exploring,bool alternate7,bool alternate8){
    if(source>=30||quantity!=1)return false;
    auto& state=vm();
    const auto module=state.execute(contained_path(root_,root_/"gameplay/beast_transfer.lua"));
    if(module.get_type()!=sol::type::table)throw std::runtime_error("Beast transfer module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("allowed");
    if(callback.get_type()!=sol::type::function)throw std::runtime_error("Beast transfer module requires allowed");
    auto result=invoke(callback.as<sol::protected_function>(),state.lua.create_table_with(
        "source_slot",source,"quantity",quantity,"native_exploring",exploring,
        "alternate_control7",alternate7,"alternate_control8",alternate8));
    if(result.return_count()!=1||result.get_type()!=sol::type::boolean)throw std::runtime_error("Beast transfer rule must return one boolean");
    return result.get<bool>()&&!exploring&&!alternate7&&!alternate8;
}

bool LuaEngine::beast_bank_allowed(std::uint8_t operation,std::uint8_t page,std::uint8_t quantity,
        bool exploring,bool alternate7,bool alternate8){
    if(operation<0x63||operation>0x65||page>=3||quantity!=1)return false;
    auto& state=vm();
    const auto module=state.execute(contained_path(root_,root_/"gameplay/beast_bank.lua"));
    if(module.get_type()!=sol::type::table)throw std::runtime_error("Beast bank module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("allowed");
    if(callback.get_type()!=sol::type::function)throw std::runtime_error("Beast bank module requires allowed");
    auto result=invoke(callback.as<sol::protected_function>(),state.lua.create_table_with(
        "operation",operation,"page",page,"quantity",quantity,"native_exploring",exploring,
        "alternate_control7",alternate7,"alternate_control8",alternate8));
    if(result.return_count()!=1||result.get_type()!=sol::type::boolean)throw std::runtime_error("Beast bank rule must return one boolean");
    return result.get<bool>()&&!exploring&&!alternate7&&!alternate8;
}

bool LuaEngine::pk_invitation_allowed(bool challenger_ready,bool recipient_ready,
        bool same_scene,bool distinct_characters,bool challenger_blocked,bool recipient_blocked){
    if(!challenger_ready||!recipient_ready||!same_scene||!distinct_characters||challenger_blocked||recipient_blocked)return false;
    auto& state=vm();
    const auto module=state.execute(contained_path(root_,root_/"gameplay/pk_invitation.lua"));
    if(module.get_type()!=sol::type::table)throw std::runtime_error("PK invitation module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("allowed");
    if(callback.get_type()!=sol::type::function)throw std::runtime_error("PK invitation module requires allowed");
    auto result=invoke(callback.as<sol::protected_function>(),state.lua.create_table_with(
        "challenger_ready",challenger_ready,"recipient_ready",recipient_ready,"same_scene",same_scene,
        "distinct_characters",distinct_characters,"challenger_blocked",challenger_blocked,"recipient_blocked",recipient_blocked));
    if(result.return_count()!=1||result.get_type()!=sol::type::boolean)throw std::runtime_error("PK invitation rule must return one boolean");
    return result.get<bool>();
}

RevivalResult LuaEngine::revival(const RevivalInput& input) {
    if(input.numeric_profile!=BattleNumericProfile::LegacyCustom &&
       input.numeric_profile!=BattleNumericProfile::ExtendedHealth64)
        throw std::invalid_argument("Unknown revival numeric profile");
    if(input.numeric_profile==BattleNumericProfile::ExtendedHealth64) {
        // CUSTOM-0090 only extends exact representation. The unchanged
        // CUSTOM-0017 Lua provider still owns its HP1/MP66 result.
        static_assert(LUA_VERSION_NUM==504);
        static_assert(std::numeric_limits<lua_Integer>::is_signed &&
                      std::numeric_limits<lua_Integer>::digits==63);
        constexpr auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
        if(!input.target_max_hp || input.target_max_hp>limit)
            throw std::invalid_argument("Invalid extended revival resource bounds");
        auto& state=vm();
        const auto module=state.execute(contained_path(root_,root_/"gameplay/revival.lua"));
        if(module.get_type()!=sol::type::table)
            throw std::runtime_error("Revival module must return table");
        const auto callback=module.as<sol::table>().raw_get<sol::object>("project");
        if(callback.get_type()!=sol::type::function)
            throw std::runtime_error("Revival module requires project");
        auto result=invoke(callback.as<sol::protected_function>(),state.lua.create_table_with(
            "target_max_hp",static_cast<lua_Integer>(input.target_max_hp)));
        if(result.return_count()!=1 || result.get_type()!=sol::type::table)
            throw std::runtime_error("Revival must return one table");
        const auto output=result.get<sol::table>();
        return {exact_calculation_integer(output.raw_get<sol::object>("hp"),1,input.target_max_hp,"extended revival HP"),
                static_cast<std::uint32_t>(exact_calculation_integer(
                    output.raw_get<sol::object>("mp_cost"),1,1'000'000,"extended revival MP"))};
    }
    auto& state=vm();
    // CUSTOM-0017 remains a legacy bounded Lua rule, even when its C++ HP
    // input/result are wide. Reject a wide input before any legacy conversion.
    static_assert(std::numeric_limits<lua_Number>::radix==2 &&
                  std::numeric_limits<lua_Number>::digits>=53);
    static_assert(std::numeric_limits<double>::radix==2 &&
                  std::numeric_limits<double>::digits>=53);
    if(!input.target_max_hp || input.target_max_hp>1'000'000)
        throw std::invalid_argument("Invalid revival resource bounds");
    const auto legacy_max_hp=static_cast<std::uint32_t>(input.target_max_hp);
    const auto module=state.execute(contained_path(root_,root_/"gameplay/revival.lua"));
    if(module.get_type()!=sol::type::table)
        throw std::runtime_error("Revival module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("project");
    if(callback.get_type()!=sol::type::function)
        throw std::runtime_error("Revival module requires project");
    auto result=invoke(callback.as<sol::protected_function>(),
                       state.lua.create_table_with("target_max_hp",legacy_max_hp));
    if(result.return_count()!=1 || result.get_type()!=sol::type::table)
        throw std::runtime_error("Revival must return one table");
    const auto output=result.get<sol::table>();
    return {static_cast<std::uint64_t>(catalog_selector(output.raw_get<sol::object>("hp"),1,legacy_max_hp,"revival HP")),
            static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("mp_cost"),1,1'000'000,"revival MP"))};
}

TownGuidePlan LuaEngine::town_guide(const TownGuideInput& input) {
    auto& state=vm();
    if(input.stage>3 || (input.npc!=1606 && input.npc!=1607))
        throw std::invalid_argument("Invalid town guide stage or target");
    const auto module=state.execute(contained_path(root_,root_/"gameplay/town_guide.lua"));
    if(module.get_type()!=sol::type::table)
        throw std::runtime_error("Town guide module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("plan");
    if(callback.get_type()!=sol::type::function)
        throw std::runtime_error("Town guide module requires plan");
    auto result=invoke(callback.as<sol::protected_function>(),
                       state.lua.create_table_with("stage",input.stage,"npc",input.npc));
    if(result.return_count()!=1 || result.get_type()!=sol::type::table)
        throw std::runtime_error("Town guide must return one table");
    const auto output=result.get<sol::table>();
    TownGuidePlan value{
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("text_key"),894,901,"guide text")),
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("confirmed_stage"),input.stage,
            std::min(3U,input.stage+1),"guide stage")),
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("journal_description"),0,2,"guide journal")),false};
    const auto reward=output.raw_get<sol::object>("requires_reward");
    if(reward.get_type()!=sol::type::boolean)
        throw std::runtime_error("Guide reward requirement must be boolean");
    value.requires_reward=reward.as<bool>();
    if(value.requires_reward!=(input.stage==2 && value.confirmed_stage==3) ||
       value.journal_description!=(value.confirmed_stage==1?1U:value.confirmed_stage==2?2U:0U))
        throw std::runtime_error("Guide plan violates completion/reward or journal contract");
    return value;
}

std::optional<DiagnosticDoorPlan> LuaEngine::diagnostic_door(const DiagnosticDoorInput& input) {
    auto& state=vm();
    if(input.area>63 || input.scene>1023 || input.before_x>=0x4000 || input.x>=0x4000 ||
       input.before_y>0x7fff || input.y>0x7fff)
        throw std::invalid_argument("Diagnostic door input outside protocol bounds");
    const auto module=state.execute(contained_path(root_,root_/"gameplay/diagnostic_door.lua"));
    if(module.get_type()!=sol::type::table) throw std::runtime_error("Door module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("plan");
    if(callback.get_type()!=sol::type::function) throw std::runtime_error("Door module requires plan");
    auto result=invoke(callback.as<sol::protected_function>(),state.lua.create_table_with(
        "area",input.area,"scene",input.scene,"before_x",input.before_x,"before_y",input.before_y,
        "x",input.x,"y",input.y,"allow_island",input.allow_island,
        "allow_all_town_doors",input.allow_all_town_doors,
        "allow_kunlun_doors",input.allow_kunlun_doors,
        "allow_kunlun_parent",input.allow_kunlun_parent));
    if(result.return_count()!=1) throw std::runtime_error("Door plan must return one value");
    if(result.get_type()==sol::type::nil) return std::nullopt;
    if(result.get_type()!=sol::type::table) throw std::runtime_error("Door plan must be table or nil");
    const auto output=result.get<sol::table>();
    DiagnosticDoorPlan plan{
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("area"),0,63,"door area")),
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("scene"),0,1023,"door scene")),
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("x"),0,0x3fff,"door x")),
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("y"),0,0x7fff,"door y"))};
    if(input.before_x==input.x && input.before_y==input.y)
        throw std::runtime_error("Door plan cannot originate from stationary restoration");
    return plan;
}

SkillBookLearningResult LuaEngine::skill_book_learning(const SkillBookLearningInput& input) {
    if(!input.book_count || input.book_count>99 || input.skill_count>100)
        throw std::invalid_argument("Skill book policy requires bounded owned snapshots");
    auto& state=vm();
    const auto module=state.execute(contained_path(root_,root_/"gameplay/skill_book_learning.lua"));
    if(module.get_type()!=sol::type::table)throw std::runtime_error("Skill book module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("policy");
    if(callback.get_type()!=sol::type::function)throw std::runtime_error("Skill book module requires policy");
    auto result=invoke(callback.as<sol::protected_function>(),state.lua.create_table_with(
        "book_count",input.book_count,"skill_count",input.skill_count,
        "already_learned",input.already_learned,"display_valid",input.display_valid));
    if(result.return_count()!=1 || result.get_type()!=sol::type::table)
        throw std::runtime_error("Skill book policy must return one table");
    const auto output=result.get<sol::table>();
    const auto allowed=output.raw_get<sol::object>("allowed");
    const auto duplicate=output.raw_get<sol::object>("duplicate");
    if(allowed.get_type()!=sol::type::boolean || duplicate.get_type()!=sol::type::boolean)
        throw std::runtime_error("Skill book policy requires boolean decisions");
    SkillBookLearningResult value{allowed.as<bool>(),duplicate.as<bool>(),
        static_cast<std::uint8_t>(catalog_selector(output.raw_get<sol::object>("consume"),0,1,"skill book debit"))};
    const bool expected=input.display_valid && input.book_count>=1 &&
        (input.already_learned || input.skill_count<100);
    if(value.allowed!=expected || value.duplicate!=input.already_learned ||
       value.consume!=static_cast<unsigned>(expected && !input.already_learned))
        throw std::runtime_error("Skill book policy exceeded its explicit qualified boundaries");
    return value;
}

OwnedGuildMembershipPolicy LuaEngine::owned_guild_membership(const OwnedGuildMembershipInput& input) {
    static_assert(std::numeric_limits<lua_Integer>::max()>=
        static_cast<std::int64_t>(ExtendedCoinAmount::maximum),"Coin policy requires wide Lua integers");
    auto& state=vm();
    if(!input.level)throw std::invalid_argument("Guild membership requires a qualified level");
    const auto wallet=ExtendedCoinAmount::from(input.wallet);
    if(!wallet)throw std::invalid_argument("Guild membership wallet outside owner coin domain");
    const auto module=state.execute(contained_path(root_,root_/"gameplay/owned_guild_membership.lua"));
    if(module.get_type()!=sol::type::table)throw std::runtime_error("Guild membership module must return table");
    const auto callback=module.as<sol::table>().raw_get<sol::object>("policy");
    if(callback.get_type()!=sol::type::function)throw std::runtime_error("Guild membership requires policy");
    auto result=invoke(callback.as<sol::protected_function>(),state.lua.create_table_with(
        "level",input.level,"wallet",wallet->sqlite_integer()));
    if(result.return_count()!=1 || result.get_type()!=sol::type::table)
        throw std::runtime_error("Guild membership policy must return one table");
    const auto output=result.get<sol::table>();
    OwnedGuildMembershipPolicy policy{
        static_cast<std::uint32_t>(catalog_selector(output.raw_get<sol::object>("creation_fee"),1,4294967295.0,"guild creation fee")),
        static_cast<std::uint8_t>(catalog_selector(output.raw_get<sol::object>("minimum_level"),1,255,"guild creation level")),
        static_cast<std::uint8_t>(catalog_selector(output.raw_get<sol::object>("initial_capacity"),1,50,"guild capacity")),false};
    const auto allowed=output.raw_get<sol::object>("may_create");
    if(allowed.get_type()!=sol::type::boolean)throw std::runtime_error("Guild membership requires boolean admission");
    policy.may_create=allowed.as<bool>();
    if(policy.may_create!=(input.level>=policy.minimum_level && input.wallet>=policy.creation_fee))
        throw std::runtime_error("Guild membership policy admission disagrees with its boundaries");
    return policy;
}

std::string LuaEngine::talk(std::uint32_t npc_id, std::uint64_t player_id,
                            const std::string& player_name) {
    auto& state = vm();
    auto& npc = lookup(state.registry.npcs, npc_id, "NPC");
    try {
        auto result = invoke(npc.on_talk, state.player({player_id, player_name}));
        if (result.return_count() == 0 || result.get_type() != sol::type::table)
            throw std::runtime_error("NPC on_talk must return a dialogue table");
        sol::table dialogue = result.get<sol::table>();
        nlohmann::json output = {{"text", dialogue_string(dialogue.raw_get<sol::object>("text"))},
                                 {"options", nlohmann::json::array()}};
        const auto options_value = dialogue.raw_get<sol::object>("options");
        if (options_value.get_type() != sol::type::nil) {
            if (options_value.get_type() != sol::type::table)
                throw std::runtime_error("dialogue options must be an array");
            auto options = options_value.as<sol::table>();
            std::size_t count = 0;
            for (const auto& pair : options) {
                ++count;
                if (count > 64 || pair.first.get_type() != sol::type::number)
                    throw std::runtime_error("dialogue options must contain at most 64 indexed entries");
                const auto index = pair.first.as<double>();
                if (index < 1 || index > 64 || std::floor(index) != index)
                    throw std::runtime_error("invalid dialogue option index");
            }
            std::set<std::uint32_t> ids;
            for (std::size_t i = 1; i <= count; ++i) {
                auto option_value = options.raw_get<sol::object>(i);
                if (option_value.get_type() != sol::type::table)
                    throw std::runtime_error("dialogue options must be a dense array of tables");
                auto option = option_value.as<sol::table>();
                const auto id = script_id(option.raw_get<sol::object>("id"));
                if (!ids.insert(id).second) throw std::runtime_error("duplicate dialogue option id");
                output["options"].push_back({{"id", id},
                    {"text", dialogue_string(option.raw_get<sol::object>("text"))}});
            }
        }
        auto serialized = output.dump();
        if (serialized.size() > 32768) throw std::runtime_error("serialized dialogue exceeds 32768 bytes");
        return serialized;
    } catch (const std::exception& error) {
        script_error("NPC " + std::to_string(npc_id) + ": " + error.what());
    }
}

void LuaEngine::call_event(const std::string& event_name) {
    auto& state = vm();
    auto found = state.registry.events.find(event_name);
    if (found == state.registry.events.end()) return;
    // Snapshot allows a callback to register another handler for the same event.
    const auto handlers = found->second;
    for (const auto& event : handlers) {
        try { invoke(event.callback); }
        catch (const std::exception& error) {
            detail::lua_logger()->error("event {} failed: {}", event_name, error.what());
        }
    }
}

void LuaEngine::quest_accept(std::uint32_t id, const ScriptPlayer& player) {
    auto& state = vm();
    invoke(lookup(state.registry.quests, id, "quest").on_accept, state.player(player));
}
void LuaEngine::quest_complete(std::uint32_t id, const ScriptPlayer& player) {
    auto& state = vm();
    invoke(lookup(state.registry.quests, id, "quest").on_complete, state.player(player));
}
void LuaEngine::monster_spawn(std::uint32_t id, const ScriptMonster& monster) {
    auto& state = vm();
    invoke(lookup(state.registry.monster_ais, id, "monster AI").on_spawn, state.monster(monster));
}
void LuaEngine::monster_update(std::uint32_t id, const ScriptMonster& monster, double dt) {
    auto& state = vm();
    if (!std::isfinite(dt) || dt < 0) script_error("monster update dt must be finite and nonnegative");
    invoke(lookup(state.registry.monster_ais, id, "monster AI").on_update, state.monster(monster), dt);
}
void LuaEngine::monster_death(std::uint32_t id, const ScriptMonster& monster, const ScriptPlayer& killer) {
    auto& state = vm();
    invoke(lookup(state.registry.monster_ais, id, "monster AI").on_death,
           state.monster(monster), state.player(killer));
}
void LuaEngine::call_gm_command(const std::string& command, const ScriptPlayer& admin,
                               const std::vector<std::string>& args) {
    auto& state = vm();
    auto copied_args = state.lua.create_table();
    for (std::size_t i = 0; i < args.size(); ++i) copied_args[i + 1] = args[i];
    invoke(lookup(state.registry.gm_commands, command, "GM command").callback,
           state.player(admin), copied_args);
}
} // namespace god2
