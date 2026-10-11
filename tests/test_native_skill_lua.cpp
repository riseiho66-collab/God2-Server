#include "scripting/LuaEngine.h"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>

namespace {
void require(bool value,const char* message) {
    if(!value) throw std::runtime_error(message);
}
struct Scripts {
    std::filesystem::path root;
    Scripts() {
        const auto seed=std::chrono::steady_clock::now().time_since_epoch().count();
        for(int i=0;i<100;++i) {
            root=std::filesystem::temp_directory_path()/
                ("god2-skill-lua-"+std::to_string(seed)+"-"+std::to_string(i));
            if(std::filesystem::create_directory(root)) return;
        }
        throw std::runtime_error("Temporary script directory unavailable");
    }
    ~Scripts() { std::error_code error;std::filesystem::remove_all(root,error); }
    void write(const std::string& contents) {
        std::ofstream out(root/"bootstrap.lua",std::ios::binary|std::ios::trunc);
        out<<contents;out.close();require(!out.fail(),"Cannot write test script");
    }
};
const std::string script=R"LUA(
assert(not GOD2_FIXTURE_MODE)
assert(native_map_catalog ~= nil)
local retained=native_skill_catalog(0,1)
local retained_book=native_skill_book_catalog(0,1)
assert(retained_book.item_id==6501 and retained_book.kind==0 and retained_book.definition_id==1)
assert(#retained_book.parsed_record==396 and retained_book.source.source_section=='SKB')
assert(retained_book.learned==nil and retained_book.mp_cost==nil and retained_book.damage==nil)
local function check(r)
    assert(r.kind==0 and r.definition_id==1 and r.source_offset==8)
    assert(r.source_record_index==0 and #r.raw_record==110)
    assert(r.raw_record==string.char(1,0,255)..string.rep(string.char(0),107))
    assert(r.record_sha256==string.rep('d',64))
    local s=r.source
    assert(s.dataset_id=='synthetic-skill' and s.source_path=='test-only/unused.bin')
    assert(s.source_sha256==string.rep('a',64) and s.decoded_sha256==string.rep('b',64))
    assert(s.native_image_sha256==string.rep('c',64) and s.source_section=='synthetic')
    assert(s.loader_rva=='0x01' and s.lookup_rva=='0x02' and s.row_count==1)
    assert(r.client_mp_threshold==0)
    assert(r.damage==nil and r.multiplier==nil and r.mp_cost==nil)
end
check(retained)
local function target_state()
    local s={masks={0xffffffff,0x3fff},saved_masks={0x12345678,0x87654321},entity_words={}}
    for i=1,28 do s.entity_words[i]=false end
    return s
end
register_gm_command('verify',function()
    check(retained);check(native_skill_catalog(0.0,1.0))
    assert(native_skill_book_catalog(0,1).item_id==6501)
    local changed_book=native_skill_book_catalog(0,1)
    changed_book.item_id=1;changed_book.source.source_section='changed'
    assert(native_skill_book_catalog(0,1).item_id==6501)
    assert(native_skill_book_catalog(0,68)==nil)
    local changed=native_skill_catalog(0,1)
    changed.raw_record='changed';changed.source.source_sha256='changed'
    check(retained);check(native_skill_catalog(0,1))
    assert(native_skill_catalog(0,2)==nil)
    assert(native_skill_catalog(3,255)==nil)
    local ok,err=pcall(native_skill_catalog,1,1)
    assert(not ok and err:find('synthetic provider error',1,true))
    local s=target_state()
    local target=native_skill_target_setup(0,1,13,s)
    assert(target.masks[1]==0 and target.masks[2]==0 and target.stored_mode==0)
    assert(target.saved_masks[1]==0x12345678 and target.saved_masks[2]==0x87654321)
    assert(target.passes_kind_gate and not target.setup_valid and target.setup_value==nil)
    assert(target.setup_flag==nil and target.damage==nil and target.cast_allowed==nil)
    assert(target.source.dataset_id=='synthetic-skill' and target.record_sha256==string.rep('d',64))
    assert(s.masks[1]==0xffffffff and s.saved_masks[1]==0x12345678 and s.entity_words[28]==false)
    target.saved_masks[1]=99;target.source.dataset_id='changed'
    assert(native_skill_target_setup(0,1,0,s).saved_masks[1]==0x12345678)
    assert(native_skill_target_setup(0,2,0,s)==nil)
    ok,err=pcall(native_skill_target_setup,1,1,0,s)
    assert(not ok and err:find('synthetic provider error',1,true))
    ok,err=pcall(native_skill_target_setup,0,3,0,s)
    assert(not ok and err:find('identity mismatch',1,true))
    s.masks={0,0}
    s.entity_words[1]=0;s.entity_words[2]=-1;s.entity_words[14]=32767
    s.entity_words[15]=0;s.entity_words[28]=-32768
    local expanded=native_skill_target_setup(3,8,0,s)
    assert(expanded.masks[1]==0x2001 and expanded.masks[2]==1)
    assert(expanded.setup_valid and expanded.setup_value==1 and expanded.setup_flag==1)
    assert(s.masks[1]==0 and s.entity_words[1]==0 and s.entity_words[28]==-32768)
end)
register_gm_command('invalid',function()
    for _,args in ipairs({{}, {0}, {0,1,2}, {-1,1}, {4,1}, {0,0}, {0,256},
        {0.5,1}, {0,1.5}, {'0',1}, {0,'1'}}) do
        local ok,err=pcall(native_skill_book_catalog,table.unpack(args))
        assert(not ok and type(err)=='string' and err:find('native_skill_book_catalog',1,true))
    end
    for _,args in ipairs({{}, {0}, {0,1,3}, {-1,1}, {4,1}, {0,0}, {0,256},
        {0.5,1}, {0,1.5}, {'0',1}, {0,'1'}, {false,1}, {{},1},
        {0/0,1}, {math.huge,1}, {0,-math.huge}}) do
        local ok,err=pcall(native_skill_catalog,table.unpack(args))
        assert(not ok and type(err)=='string' and err:find('native_skill_catalog',1,true))
    end
    assert(not pcall(native_skill_catalog,nil,1))
    assert(not pcall(native_skill_catalog,0,nil))
    local function rejected(...)
        local ok,err=pcall(native_skill_target_setup,...)
        assert(not ok and err:find('native_skill_target_setup',1,true))
    end
    rejected();rejected(0,1,0);rejected(0,1,0,target_state(),1)
    rejected('0',1,0,target_state());rejected(0,1,14,target_state())
    rejected(0,1,-1,target_state());rejected(0,1,0.5,target_state())
    rejected(0,1,math.huge,target_state());rejected(0,1,0/0,target_state())
    rejected(0,1,0,false);rejected(0,1,0,{})
    for _,change in ipairs({
        function(s) s.extra=1 end, function(s) s.saved_masks=nil end,
        function(s) s.masks[3]=0 end, function(s) s.masks[0]=0 end,
        function(s) s.masks[1]=nil end, function(s) s.masks[1]=-1 end,
        function(s) s.masks[1]=0x100000000 end, function(s) s.masks[1]='1' end,
        function(s) s.entity_words[28]=nil end, function(s) s.entity_words[29]=false end,
        function(s) s.entity_words[1]=true end, function(s) s.entity_words[1]=32768 end,
        function(s) s.entity_words[1]=-32769 end, function(s) s.entity_words[1]=0.5 end,
        function(s) s.entity_words[1]={} end}) do
        local s=target_state();change(s);rejected(0,1,0,s)
    end
end)
)LUA";
void tests() {
    Scripts files;files.write(script);
    // Explicit synthetic provider, not a native source or SQL record.
    god2::NativeSkillRecord record;
    record.source.dataset_id="synthetic-skill";record.source.source_path="test-only/unused.bin";
    record.source.source_sha256=std::string(64,'a');record.source.decoded_sha256=std::string(64,'b');
    record.source.native_image_sha256=std::string(64,'c');record.source.source_section="synthetic";
    record.source.loader_rva="0x01";record.source.lookup_rva="0x02";record.source.row_count=1;
    record.source_record_index=0;record.source_offset=8;record.record_sha256=std::string(64,'d');
    record.kind=0;record.definition_id=1;record.raw_record.resize(110);
    record.raw_record[0]=1;record.raw_record[2]=255;
    god2::NativeSkillBookRecord book;
    book.source.dataset_id="current-skill-books-v1";
    book.source.source_section="SKB";
    book.kind=0;book.definition_id=1;book.item_id=6501;
    book.source_line=8916;book.decoded_offset=707624;
    book.raw_record={static_cast<std::uint8_t>('6'),static_cast<std::uint8_t>('5'),
                     static_cast<std::uint8_t>('0'),static_cast<std::uint8_t>('1')};
    book.parsed_record.resize(396);
    auto calls=std::make_shared<int>(0);std::weak_ptr<int> weak=calls;
    {
        god2::LuaEngine lua(files.root,false,{},[record,calls](std::int64_t kind,std::int64_t id)
                ->std::optional<god2::NativeSkillRecord> {
            ++*calls;
            if(kind==1) throw std::runtime_error("synthetic provider error");
            if(kind==0 && id==3) { auto invalid=record;invalid.definition_id=3;return invalid; }
            if(kind==3 && id==8) {
                auto special=record;special.kind=3;special.definition_id=8;
                special.raw_record[0]=8;special.raw_record[1]=3;
                special.raw_record[0x44]=255;special.raw_record[0x45]=1;return special;
            }
            if(kind==0 && id==1) return record;
            return std::nullopt;
        },[book](std::int64_t kind,std::int64_t id) -> std::optional<god2::NativeSkillBookRecord> {
            if (kind == 0 && id == 1) return book;
            return std::nullopt;
        });
        calls.reset();
        require(lua.initialize() && lua.load_script("bootstrap.lua"),"Skill Lua initialization failed");
        const god2::ScriptPlayer player{1,"Synthetic"};
        lua.call_gm_command("verify",player,{});
        const auto before=*weak.lock();
        lua.call_gm_command("invalid",player,{});
        require(*weak.lock()==before,"Invalid selectors reached provider");
        require(lua.reload_all(),"Skill callback lost after reload");
        lua.call_gm_command("verify",player,{});
        files.write("error('reject staged skill script')");
        require(!lua.reload_all(),"Invalid staged script accepted");
        lua.call_gm_command("verify",player,{});
        files.write("not valid Lua !");
        require(!lua.reload_all(),"Syntax-invalid reload accepted");
        lua.call_gm_command("verify",player,{});
        bool rejected=false;
        std::thread wrong([&] {
            try { lua.call_gm_command("verify",player,{}); }
            catch(const std::runtime_error&) { rejected=true; }
        });
        wrong.join();require(rejected,"Cross-thread skill query accepted");
    }
    require(weak.expired(),"Skill provider ownership leaked");
    files.write(R"LUA(
local ok,err=pcall(native_skill_catalog,0,1)
assert(not ok and err:find('native_skill_catalog unavailable',1,true))
ok,err=pcall(native_skill_book_catalog,0,1)
assert(not ok and err:find('native_skill_book_catalog unavailable',1,true))
local s={masks={0,0},saved_masks={0,0},entity_words={}}
for i=1,28 do s.entity_words[i]=false end
ok,err=pcall(native_skill_target_setup,0,1,0,s)
assert(not ok and err:find('native_skill_target_setup unavailable',1,true))
)LUA");
    for(bool fixture:{false,true}) {
        god2::LuaEngine unavailable(files.root,fixture);
        require(unavailable.initialize() && unavailable.load_script("bootstrap.lua"),
                "Empty skill provider failed closed incorrectly");
    }
}
}
int main() {
    try { tests();std::cout<<"Native skill Lua synthetic checks passed\n"; }
    catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
}
