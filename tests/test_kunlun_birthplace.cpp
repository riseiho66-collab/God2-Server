#include "handlers/RecoveredMovementService.h"
#include "handlers/RecoveredCharacterService.h"
#include "db/SqliteDatabase.h"
#include "protocol/RecoveredWorldFrame.h"
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
namespace { void require(bool value,const char* message){if(!value)throw std::runtime_error(message);} }
int main() {
    try {
        using namespace god2;const auto root=std::filesystem::path(GOD2_SOURCE_DIR);
        const auto navigation=root/"artifacts/world-atlas/kunlun-4-3.json";
        RecoveredKunlunNavigation grid(navigation);std::ifstream file(navigation);const auto source=nlohmann::json::parse(file);
        std::size_t known=0;for(int y=0;y<252;++y)for(int x=0;x<252;++x)if(grid.consistent_cell(x,y))++known;
        require(known==source.at("cross_window").at("consistent_coordinates"),"Kunlun consensus count changed");
        for(const auto& conflict:source.at("cross_window").at("conflicts"))
            require(!grid.consistent_cell(conflict.at("x"),conflict.at("y")),"Conflicting map cell admitted");
        for(int y=124;y<=128;++y)for(int x=124;x<=128;++x)require(grid.consistent_cell(x,y)==1,"Lab candidate not walkable");
        SqliteDatabase db(":memory:");db.initialize();db.migrate();const auto owner=db.accounts().create("birth-owner","hash").id;
        RecoveredCharacterService characters(db.recovered_characters());RecoveredCharacterCreate create{};
        create.payload[0]='A';create.payload[29]=1;create.payload[31]=1;create.payload[40]=4;
        const auto fresh=characters.create(owner,create);create.payload[0]='B';const auto old=characters.create(owner,create);
        const auto saved=db.recovered_characters().commit_position(owner,old,std::nullopt,2,4,63,64);
        RecoveredMovementService::TownDiagnostic config{root/"artifacts/world-atlas/town-2-4.json",{3,3},63,64,true,
            root/"artifacts/world-atlas/indoor-2-15.json",{},navigation,126,126};
        RecoveredMovementService service(db.recovered_characters(),config);
        const auto frame=RecoveredWorldFrame::decode(service.prepare(1,owner,fresh));require(frame && frame->size()==37,"World record missing");
        const auto& logical=*frame;const auto map=logical[25]+256u*logical[26];
        require((map&63)==4 && (map>>6)==3 && (logical[29]&3)==0,"Fresh character did not enter Kunlun");
        service.bind(1,owner,fresh);require(service.current_location(1,owner,fresh)==RecoveredPosition{4,3,126,126,0},"Fresh location wrong");
        const std::array step{RecoveredMovement::Request{127,126,1,0}};
        const auto result=service.move_committed(1,owner,fresh,step);
        require(result.after==RecoveredPosition{4,3,127,126,1},"Kunlun move not saved to area4/3");
        service.remove(1);service.prepare(2,owner,fresh);service.bind(2,owner,fresh);
        require(service.current_location(2,owner,fresh)==result.after,"Kunlun reconnect lost position");
        service.prepare(3,owner,old);service.bind(3,owner,old);
        require(service.current_location(3,owner,old)==saved,"Existing town character relocated");
        require(db.recovered_characters().load_position(owner,old)==saved,"Existing save overwritten");
        bool rejected=false;try{service.begin_indoor_transfer(2,owner,fresh,result.after,18,12);}catch(const std::exception&){rejected=true;}
        require(rejected && db.recovered_characters().load_position(owner,fresh)==result.after,"Town door moved Kunlun character");
        std::cout<<"PASS Kunlun source consensus, fresh spawn, move/reconnect and saved-town preservation\n";return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
