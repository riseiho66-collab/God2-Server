#include "game/RecoveredTownNavigation.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <limits>
#include <nlohmann/json.hpp>

namespace { void require(bool v) { if(!v) throw std::runtime_error("Town navigation assertion failed"); } }
int main(int argc,char** argv) {
    try {
        const auto path=std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas/town-2-4.json";
        god2::RecoveredTownNavigation navigation(path);
        if(argc==2 && std::string(argv[1])=="--consistent-cells") {
            for(int y=0;y<189;++y) for(int x=0;x<189;++x) {
                const auto value=navigation.consistent_cell(x,y);
                if(value) std::cout<<'0'<<static_cast<unsigned>(*value);
                else std::cout<<"??";
            }
            std::cout<<'\n';return 0;
        }
        if(argc==2 && std::string(argv[1])=="--centers") {
            int x=0,y=0;
            while(std::cin>>x>>y) {
                const auto center=navigation.select_center(x,y);
                if(center) std::cout<<center->x<<' '<<center->y<<'\n';
                else std::cout<<"none\n";
            }
            return std::cin.eof()?0:1;
        }
        require(argc==1);
        require(!navigation.select_center(std::numeric_limits<int>::min(),0));
        require(!navigation.select_center(0,std::numeric_limits<int>::max()));
        require(!navigation.available_center(std::numeric_limits<int>::max(),0));
        std::ifstream file(path);const auto source=nlohmann::json::parse(file);
        std::size_t known=0,unknown=0;
        for(const auto& w:source.at("windows")) {
            const int cx=w.at("block_x"),cy=w.at("block_y");
            const auto hex=w.at("cells_hex").get<std::string>();
            for(int ly=0;ly<63;++ly) for(int lx=0;lx<63;++lx) {
                const int x=cx*21-21+lx,y=cy*21-21+ly;
                const auto actual=navigation.cell(cx,cy,x,y);
                const auto offset=static_cast<std::size_t>((ly*63+lx)*2);
                if(x<0 || y<0 || x>=189 || y>=189 || hex[offset]=='?') { require(!actual);++unknown; }
                else { require(actual && *actual==hex[offset+1]-'0');++known; }
            }
        }
        require(known>0 && unknown>0);
        std::size_t consistent=0,conflicts=0,uncovered=0;
        for(int y=0;y<189;++y) for(int x=0;x<189;++x) {
            unsigned mask=0;
            for(int cy=0;cy<9;++cy) for(int cx=0;cx<9;++cx) {
                if(!navigation.available_center(cx,cy)) continue;
                const auto v=navigation.cell(cx,cy,x,y);
                if(v) mask|=1U<<*v;
            }
            const auto actual=navigation.consistent_cell(x,y);
            if(mask==0) { require(!actual);++uncovered; }
            else if((mask&(mask-1))!=0) { require(!actual);++conflicts; }
            else { require(actual && mask==(1U<<*actual));++consistent; }
        }
        require(conflicts==377 && consistent==27847 && uncovered==7497);
        require(!navigation.consistent_cell(80,35));
        require(!navigation.consistent_cell(82,46)); // byte1/2 remains a conflict
        require(navigation.consistently_walkable(82,46)); // original nonzero consumer
        require(!navigation.consistently_walkable(80,35)); // includes blocked0
        require(!navigation.consistently_walkable(0,0));
        require(!navigation.consistent_cell(std::numeric_limits<int>::max(),0));
        require(!navigation.consistent_cell(0,std::numeric_limits<int>::min()));
        std::cout<<"Cross-window cells: "<<consistent<<" consistent, "<<conflicts
                 <<" conflicting, "<<uncovered<<" uncovered\n";
        require(!navigation.cell(-1,0,0,0) && !navigation.cell(9,0,0,0));
        require(!navigation.cell(0,0,std::numeric_limits<int>::max(),0));
        require(!navigation.cell(0,0,std::numeric_limits<int>::min(),0));
        for(const int value:{std::numeric_limits<int>::min(),-1,9,std::numeric_limits<int>::max()}) {
            require(!navigation.cell(value,0,0,0));
            require(!navigation.cell(0,value,0,0));
        }
        require(!navigation.cell(0,0,63,0));
        require(!navigation.cell(0,0,0,63));
        require(!navigation.cell(8,8,0,0));
        const auto temporary=std::filesystem::temp_directory_path()/
            ("god2-town-corrupt-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".json");
        struct Cleanup { std::filesystem::path p;~Cleanup(){std::error_code e;std::filesystem::remove(p,e);} } cleanup{temporary};
        std::size_t rejected_inputs=0;
        const auto expect_rejected=[&] {
            bool rejected=false;
            try { god2::RecoveredTownNavigation bad(temporary); }
            catch(const std::invalid_argument&) { rejected=true; }
            require(rejected);++rejected_inputs;
        };
        require(!std::filesystem::exists(temporary));
        expect_rejected();
        const auto reject_bytes=[&](const std::string& bytes) {
            {
                std::ofstream out(temporary,std::ios::binary|std::ios::trunc);
                out.write(bytes.data(),static_cast<std::streamsize>(bytes.size()));
                out.close();require(static_cast<bool>(out));
            }
            expect_rejected();
        };
        reject_bytes("");
        reject_bytes("{");
        reject_bytes(std::string(2*1024*1024+1,' '));
        auto corrupt=source;corrupt["windows"][0]["cells_hex"]="00";
        reject_bytes(corrupt.dump());
        corrupt=source;corrupt["area"]=3;reject_bytes(corrupt.dump());
        corrupt=source;corrupt["runtime_validated"]=true;reject_bytes(corrupt.dump());
        corrupt=source;corrupt["dynamic_occupancy_included"]=true;reject_bytes(corrupt.dump());
        corrupt=source;corrupt["windows"][0]["known_cells"]=0;reject_bytes(corrupt.dump());
        // Valid JSON with altered provenance must also fail the full-file pin.
        corrupt=source;corrupt["sources"]=nlohmann::json::array();reject_bytes(corrupt.dump());
        std::cout<<"Town cells checked: "<<known<<" known, "<<unknown<<" unknown/outside\n";
        std::cout<<"Invalid artifacts rejected: "<<rejected_inputs<<'\n';
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
