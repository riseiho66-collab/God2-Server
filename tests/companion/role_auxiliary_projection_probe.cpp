#include "protocol/RecoveredRoleAuxiliaryProjection.h"
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

int main(){
    using P=god2::RecoveredRoleAuxiliaryProjection;
    try{
        std::string line;
        while(std::getline(std::cin,line)){
            std::istringstream input(line);std::string hex;input>>hex;
            std::vector<std::uint8_t> raw;
            if(hex.size()%2)throw std::runtime_error("odd hex");
            for(std::size_t i=0;i<hex.size();i+=2){
                const auto part=hex.substr(i,2);std::size_t consumed{};
                const auto value=std::stoul(part,&consumed,16);
                if(consumed!=2)throw std::runtime_error("invalid hex");
                raw.push_back(static_cast<std::uint8_t>(value));
            }
            const auto saved=P::parse(raw);
            if(!saved){std::cout<<"reject\n";continue;}
            auto next=*saved;std::string operation;input>>operation;
            if(operation=="modifiers"){
                std::array<std::int16_t,4> values{};
                for(auto& value:values){int parsed{};if(!(input>>parsed)||parsed<-32768||parsed>32767)throw std::runtime_error("modifier range");value=static_cast<std::int16_t>(parsed);}
                next=P::with_modifiers(next,values);
            }else if(operation=="combat"){
                P::Combat values;std::array<std::uint32_t*,4> fields{&values.physical_attack,&values.physical_defense,&values.magical_attack,&values.magical_defense};
                for(auto* field:fields){std::uint64_t value{};if(!(input>>value)||value>0xffffffffULL)throw std::runtime_error("combat range");*field=static_cast<std::uint32_t>(value);}
                next=P::with_combat(next,values);
            }else if(operation!="read")throw std::runtime_error("operation");
            for(const auto byte:next.raw())std::cout<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(byte);
            for(const auto value:next.displayed_modifiers())std::cout<<' '<<std::dec<<value;
            const auto combat=next.combat();
            for(const auto value:{combat.physical_attack,combat.physical_defense,combat.magical_attack,combat.magical_defense})std::cout<<' '<<value;
            for(const auto value:next.elements())std::cout<<' '<<value;
            std::cout<<' '<<next.nonnegative_combat_display()<<'\n';
        }
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
