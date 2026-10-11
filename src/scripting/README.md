# Lua content API

Build LuaEngine.cpp, LuaRegistry.cpp, and ScriptBindings.cpp with C++20,
sol2::sol2, Lua, spdlog, and nlohmann_json::nlohmann_json. Add src to the
include path. Define SOL_ALL_SAFETIES_ON=1 consistently for all sol2 consumers.
Engine diagnostics, sol2 binding exceptions, and Lua log() messages use the
registered spdlog "lua" logger, falling back to default_logger for isolated use.

Construct god2::LuaEngine(script_root), call initialize(), then
load_script("bootstrap.lua"). initialize does not execute content. Absolute
paths must remain within the canonical script root; relative paths resolve
against it (existing CWD paths inside the root are also accepted).

Call every engine operation on the thread that initialized it, and destroy the
engine there after callbacks finish. A strand on a multi-thread pool alone does
not guarantee this affinity: use a dedicated single-thread game executor.
Cross-thread operations throw std::runtime_error before touching Lua.

load_script, load_directory, and reload_all return bool. Every load rebuilds all
registered entry points in a fresh VM; only complete success replaces the old
VM and entry list. Directory loads recurse in sorted path order and are rescanned
on reload. Modules execute once per canonical file per VM, including files loaded
both directly and via require. A successful reload resets Lua-local state and
removes obsolete registrations. Failed staging can still produce log messages.

require("npc.test_npc") loads only root/npc/test_npc.lua; it caches return values,
rejects cycles and traversal, follows canonical paths to reject escaping symlinks,
and accepts text chunks only. Only base/table/string/math/utf8 are opened.
load, loadfile, dofile, collectgarbage, and print are removed. package, io, os,
debug, native modules, networking, databases, and live game objects are absent.
Each outer protected invocation has a 1,000,000 Lua instruction budget, checked
by a count hook every 1,000 instructions. Nested require invocations share the
existing budget without resetting the hook counter. Exhaustion logs an error and
fails the host call even if Lua catches the immediate error and returns normally.
The scoped guard restores the previous hook, mask, count interval, and Lua extra
space on success and exception; Lua cannot expose the previous hook's partial
countdown, so restoring a preexisting count hook restarts its interval.
Events receive a fresh budget for each handler; independent load entry points
also receive fresh budgets. A looping bootstrap fails staging and retains the old VM.

This protects against accidental Lua loops, not hostile scripts or wall-clock
overruns. Parsing, native library/C++ calls, allocation, and VM destruction are
not instruction-metered. A script deliberately catching repeated hook errors in
an endless pcall loop can evade termination. No allocation quota is imposed.

Lua registrations are register_npc, register_quest, register_monster_ai,
register_event, and register_gm_command (see scripts for schemas). IDs are positive
uint32 values. Required callbacks and names are validated. Duplicate NPC/quest/AI/
GM registrations fail the load; events support multiple handlers in registration
order. call_event logs each failure and continues to subsequent handlers. Unknown
events do nothing. Event handlers added during dispatch run on the next dispatch.

has_npc(id) checks availability. talk(npc_id, player_id, player_name) invokes the
protected on_talk callback and returns UTF-8 JSON {"text":...,"options":[...]},
throwing std::runtime_error on missing NPCs, script errors, or malformed output.
The dispatcher must catch these errors. Dialogue text is limited to 16384 bytes,
options to 64 dense entries with unique positive uint32 IDs, and the final JSON
to 32768 bytes. Missing options become an empty array.

quest_accept/quest_complete take (quest_id, ScriptPlayer).
monster_spawn/monster_update/monster_death take (ai_id, ScriptMonster), with an
additional nonnegative finite dt or ScriptPlayer killer as appropriate.
call_gm_command takes (name, ScriptPlayer admin, vector<string> args).
These invocations log and throw std::runtime_error on unavailable registrations
or script errors. The host must authenticate/authorize GM calls and schedule a
requested reload after the current callback returns; the sample reload command
only logs the request.

ScriptPlayer has id and name; ScriptMonster has id, template_id, and hp. Each call
creates fresh copied Lua tables. uint64 entity IDs are decimal strings to preserve
precision; template IDs remain numbers. Mutating a snapshot cannot change host
state. No quest rewards, AI movement, or database mutations are implied by hooks.
