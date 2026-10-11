#include "scripting/TaiwanMovementRules.h"
#include <sol/sol.hpp>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace god2 {
struct TaiwanMovementRules::Vm {sol::state state;sol::table rules;};
namespace {
void budget(lua_State* state,lua_Debug*) {luaL_error(state,"TW native movement instruction budget exceeded");}
struct Limit {
    lua_State* state;
    explicit Limit(lua_State* s):state(s){lua_sethook(s,budget,LUA_MASKCOUNT,100000);}
    ~Limit(){lua_sethook(state,nullptr,0,0);}
};
}
TaiwanMovementRules::TaiwanMovementRules(const std::filesystem::path& path):vm_(std::make_unique<Vm>()) {
    vm_->state.open_libraries(sol::lib::base);
    for(const char* name:{"dofile","loadfile","load","collectgarbage","print"})vm_->state[name]=sol::nil;
    std::ifstream input(path,std::ios::binary);
    if(!input)throw std::runtime_error("TW native movement rules missing");
    std::ostringstream buffer;buffer<<input.rdbuf();Limit limit(vm_->state.lua_state());
    auto result=vm_->state.safe_script(buffer.str(),sol::script_pass_on_error);
    if(!result.valid())throw std::runtime_error("TW native movement rules failed to load");
    vm_->rules=result.get<sol::table>();
    for(const char* name:{"step_direction","native_cell_qualifies"}) {
        sol::object function=vm_->rules[name];
        if(function.get_type()!=sol::type::function)throw std::runtime_error("TW native movement rule entry missing");
    }
}
TaiwanMovementRules::~TaiwanMovementRules()=default;
std::optional<TaiwanMovementRules::Step> TaiwanMovementRules::prepare(
    const RecoveredMovement::Request& request,const RecoveredPosition& origin,
    std::uint8_t previous_direction,std::uint8_t native_cell) {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW movement Lua owner mismatch");
    if(previous_direction>7 || !RecoveredNativeMovement::ordinary_request(request))return std::nullopt;
    Limit limit(vm_->state.lua_state());sol::protected_function direction_rule=vm_->rules["step_direction"];
    auto result=direction_rule(origin.x,origin.y,request.x,request.y,previous_direction);
    if(!result.valid() || result.return_count()!=1)throw std::runtime_error("TW movement direction result shape invalid");
    sol::object value=result.get<sol::object>();
    if(value.get_type()==sol::type::nil)return std::nullopt;
    if(!value.is<lua_Integer>())throw std::runtime_error("TW movement direction must be an integer");
    const auto direction=value.as<lua_Integer>();
    if(direction<0 || direction>7)throw std::runtime_error("TW movement direction out of range");
    sol::protected_function cell_rule=vm_->rules["native_cell_qualifies"];
    auto cell_result=cell_rule(native_cell);
    if(!cell_result.valid() || cell_result.return_count()!=1)throw std::runtime_error("TW movement cell result shape invalid");
    sol::object cell_value=cell_result.get<sol::object>();
    if(cell_value.get_type()!=sol::type::boolean)throw std::runtime_error("TW movement cell result must be boolean");
    if(!cell_value.as<bool>())return std::nullopt;
    // Full input residue is retained for provenance, excluded from Lua and never
    // interpreted as a flag/direction/permission. No timing/sequence acceptance.
    return Step{request,static_cast<std::uint8_t>(direction),native_cell};
}
}
