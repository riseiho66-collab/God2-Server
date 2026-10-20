#include "protocol/RecoveredWorldRecords.h"
#include "protocol/RecoveredBattleRowPreferenceRuns.h"
#include <array>
#include <iostream>
#include <stdexcept>
namespace {
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
auto parse(std::span<const std::uint8_t> bytes) {
    return god2::RecoveredWorldRecords::decode(bytes,nullptr,
        false,false,false,false,false, // guild/beast/pk/companion/activity
        false,false,false,false,false, // E4/BF/spectator/map/C2
        false,false,false,false,false, // close/skill/blacklist/party/options
        false,false,false,true);       // world-skill/preborn/selection/row
}
}
int main()try {
    using Row=god2::RecoveredBattleRowPreference;
    using World=god2::RecoveredWorldRecords;
    std::optional<World::UnsupportedRecord> unsupported;
    const std::array<std::uint8_t,2> first{0xb4,0};
    require(!World::decode(first,&unsupported) && unsupported && unsupported->opcode==0xb4,"No real host must retain default-off ingress");
    for(unsigned raw=0;raw<256;++raw) {
        const std::array<std::uint8_t,2> input{0xb4,static_cast<std::uint8_t>(raw)};
        const auto decoded=parse(input);
        require(decoded.has_value()==(raw<2),"B4 must preserve exact native 0/1 grammar");
        if(decoded) {
            require(decoded->size()==1 && std::get<Row::Request>(decoded->front()).row==raw,"B4 body byte changed");
            const auto projection=Row::projection(static_cast<std::uint8_t>(raw));
            require(projection && (*projection)[0]==0xe8 && (*projection)[1]==raw,"E8 display projection changed");
        } else require(!Row::projection(static_cast<std::uint8_t>(raw)),"Invalid row projected");
    }
    require(!parse(std::array<std::uint8_t,1>{0xb4}),"Truncated B4 escaped");
    require(!parse(std::array<std::uint8_t,4>{0xb4,0,0xb4,2}),"Valid prefix escaped malformed whole batch");
    require(!parse(std::array<std::uint8_t,3>{0xb4,1,0x30}),"Truncated following tick escaped");
    const std::array<std::uint8_t,13> mixed{0xb4,1,0x2e,0x34,0x12,0x78,0x56,0x9a,0xbc,0x30,0,0xb4,0};
    const auto batch=parse(mixed);
    require(batch && batch->size()==4,"Native shared movement/tick/B4 flush rejected");
    const auto& move=std::get<god2::RecoveredMovement::Request>((*batch)[1]);
    require(move.x==0x1234 && move.y==0x5678 && move.sequence==0x9a && move.opaque_tail==0xbc,"Mixed movement custody changed");
    require(std::get<Row::Request>((*batch)[0]).row==1 && std::get<Row::Request>((*batch)[3]).row==0,"Multiple B4 ordering changed");
    using Runs=god2::RecoveredBattleRowPreferenceRuns;
    const auto plan=Runs::prepare(*batch);require(plan && plan->has_row(),"Actual run plan missing");
    unsigned original_calls=0,choice_calls=0;
    require(plan->dispatch([&](std::span<const World::Record> run) {
        ++original_calls;
        require(run.data()==batch->data()+1 && run.size()==2,"Movement/Tick run lost exact Session record occurrence");
        require(&run[0]==&(*batch)[1] && &run[1]==&(*batch)[2],"Run values were copied");return true;
    },[&](Row::Request choice) {
        require(choice.row==(choice_calls?0:1),"Owned B4 choice order changed");++choice_calls;return true;
    }) && original_calls==1 && choice_calls==2,"Actual run dispatch changed");
    // No B4 must preserve the exact complete original span for every unrelated
    // old receipt path, including empty input; copying equal values is wrong.
    std::vector<World::Record> unrelated{World::Tick{},god2::RecoveredMovement::Request{1,2,3,4},
        god2::RecoveredSelectionItemRequest::Request{0x1234,7},World::ContextNotification{{0,0}}};
    const auto unchanged=Runs::prepare(unrelated);require(unchanged && !unchanged->has_row(),"No-row plan changed");
    require(unchanged->dispatch([&](std::span<const World::Record> run) {
        require(run.data()==unrelated.data() && run.size()==unrelated.size(),"No-B4 callback lost original span identity");
        require(std::get_if<god2::RecoveredSelectionItemRequest::Request>(&run[2])==
            std::get_if<god2::RecoveredSelectionItemRequest::Request>(&unrelated[2]),"C28 private occurrence lost");
        require(std::get_if<World::ContextNotification>(&run[3])==
            std::get_if<World::ContextNotification>(&unrelated[3]),"PK C1C private occurrence lost");return true;
    },[](Row::Request){return false;}),"No-row forwarding failed");
    const std::span<const World::Record> empty;
    const auto empty_plan=Runs::prepare(empty);unsigned empty_calls=0;
    require(empty_plan && empty_plan->dispatch([&](auto run){++empty_calls;return run.data()==empty.data() && run.empty();},
        [](Row::Request){return false;}) && empty_calls==1,"Empty no-B4 callback not forwarded exactly once");
    std::vector<World::Record> invalid{Row::Request{0},World::ClientOptionsNotification{{0,0}}};
    require(!Runs::prepare(invalid),"Unsupported mixed mutation escaped prevalidation");
    invalid={Row::Request{0},god2::RecoveredMovement::Request{1,2,3,4},Row::Request{2}};
    require(!Runs::prepare(invalid),"Invalid later B4 escaped whole-batch prevalidation");
    std::cout<<"B4 grammar/projection regression source\n";
    return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
