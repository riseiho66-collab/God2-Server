#include "cn/scripting/CnMovementRules.h"
#include <sol/sol.hpp>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace god2cn {
struct CnMovementRules::Vm {sol::state state;sol::table rules;};
namespace {
void budget(lua_State* state,lua_Debug*) {luaL_error(state,"CN Lua instruction budget exceeded");}
struct Limit {
    lua_State* state;
    explicit Limit(lua_State* s):state(s){lua_sethook(s,budget,LUA_MASKCOUNT,100000);}
    ~Limit(){lua_sethook(state,nullptr,0,0);}
};
}
CnMovementRules::CnMovementRules(const std::filesystem::path& path):vm_(std::make_unique<Vm>()) {
    vm_->state.open_libraries(sol::lib::base);
    for(const char* name:{"dofile","loadfile","load","collectgarbage","print"})vm_->state[name]=sol::nil;
    std::ifstream input(path,std::ios::binary);
    if(!input)throw std::runtime_error("CN movement rules missing");
    std::ostringstream buffer;buffer<<input.rdbuf();
    Limit limit(vm_->state.lua_state());
    auto result=vm_->state.safe_script(buffer.str(),sol::script_pass_on_error);
    if(!result.valid())throw std::runtime_error("CN movement rules failed to load");
    vm_->rules=result.get<sol::table>();
    sol::object rule=vm_->rules["step_direction"];
    if(rule.get_type()!=sol::type::function)throw std::runtime_error("CN movement direction entry point missing");
    sol::object passable=vm_->rules["native_neighbor_passable"];
    if(passable.get_type()!=sol::type::function)throw std::runtime_error("CN movement cell entry point missing");
}
CnMovementRules::~CnMovementRules()=default;
std::optional<CnPreparedStep> CnMovementRules::prepare_native_step(
    std::span<const std::uint8_t> record,CnMovement::Point origin,std::uint8_t previous_direction) {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN movement Lua ownership violation");
    if(previous_direction>7)throw std::invalid_argument("CN actor direction out of range");
    const auto step=CnMovement::parse_step(record);
    if(!step)return std::nullopt;
    Limit limit(vm_->state.lua_state());
    sol::protected_function function=vm_->rules["step_direction"];
    auto result=function(origin.x,origin.y,step->destination.x,step->destination.y,previous_direction);
    if(!result.valid())throw std::runtime_error("CN movement direction rule failed");
    if(result.return_count()!=1)throw std::runtime_error("CN movement direction result shape mismatch");
    sol::object value=result.get<sol::object>();
    if(value.get_type()==sol::type::nil)return std::nullopt;
    if(!value.is<lua_Integer>())throw std::runtime_error("CN movement direction must be integer");
    const auto direction=value.as<lua_Integer>();
    if(direction<0 || direction>7)throw std::runtime_error("CN movement direction result out of range");
    // Deliberately excludes opaque native stack storage from Lua and output.
    // This returned value does not authorize a move or acknowledge the client.
    return CnPreparedStep{step->destination,step->client_ring_index,static_cast<std::uint8_t>(direction)};
}
std::optional<CnMapPreparedStep> CnMovementRules::prepare_native_map_step(
    std::span<const std::uint8_t> record, CnMovement::Point origin,
    std::uint8_t previous_direction, const CnMapPassability& map) {
    const auto step=prepare_native_step(record,origin,previous_direction);
    if(!step)return std::nullopt;
    const auto cell=map.cell_at(step->destination.x,step->destination.y);
    Limit limit(vm_->state.lua_state());
    sol::protected_function function=vm_->rules["native_neighbor_passable"];
    auto result=function(cell);
    if(!result.valid())throw std::runtime_error("CN movement cell rule failed");
    if(result.return_count()!=1)throw std::runtime_error("CN movement cell result shape mismatch");
    sol::object value=result.get<sol::object>();
    if(value.get_type()!=sol::type::boolean)throw std::runtime_error("CN movement cell result must be boolean");
    if(!value.as<bool>())return std::nullopt;
    return CnMapPreparedStep{*step,cell};
}
}
