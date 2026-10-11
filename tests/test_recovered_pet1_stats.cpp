#include "protocol/RecoveredPet1Stats.h"
#include <iostream>
#include <string>
#include <vector>
#include <type_traits>
using Codec=god2::RecoveredPet1Stats;
static_assert(!std::is_default_constructible_v<Codec::Record>);
int main() {
    const std::string digits="0123456789abcdef";std::string line;
    while(std::getline(std::cin,line)) {
        if(line.size()%2 || line.size()>8192)return 2;
        std::vector<std::uint8_t> bytes;
        for(std::size_t i=0;i<line.size();i+=2) {
            const auto a=digits.find(line[i]),b=digits.find(line[i+1]);if(a>=16 || b>=16)return 2;
            bytes.push_back(static_cast<std::uint8_t>(a*16+b));
        }
        const auto r=Codec::parse_logical(bytes);if(!r){std::cout<<"reject\n";continue;}
        const auto before=bytes;std::fill(bytes.begin(),bytes.end(),std::uint8_t{0});
        const auto encoded=Codec::encode_logical(*r);
        if(!std::equal(encoded.begin(),encoded.end(),before.begin(),before.end()))return 3;
        for(auto v:encoded)std::cout<<digits[v>>4]<<digits[v&15];
        const auto v=r->vitals();const auto c=r->combat_values();const auto a=r->attributes();
        const auto b=r->allocation_bonuses();const auto e=r->elements();
        std::cout<<' '<<r->metadata_key()<<' '<<static_cast<unsigned>(r->slot())
            <<' '<<v.current_hp<<' '<<v.current_mp<<' '<<v.maximum_hp<<' '<<v.maximum_mp
            <<' '<<static_cast<unsigned>(r->level())<<' '<<static_cast<unsigned>(r->life_display_raw())
            <<' '<<c.physical_attack<<' '<<c.physical_defense<<' '<<c.magical_attack<<' '<<c.magical_defense
            <<' '<<a.strength<<' '<<a.constitution<<' '<<a.intelligence<<' '<<a.speed
            <<' '<<b.strength<<' '<<b.constitution<<' '<<b.intelligence<<' '<<b.speed
            <<' '<<r->remaining_points()<<' '<<e.metal<<' '<<e.wood<<' '<<e.water<<' '<<e.fire<<' '<<e.earth
            <<' '<<static_cast<unsigned>(r->rebirth_count())<<' '<<r->progress_display_raw14()<<' '<<r->fusion_expiry_raw()<<'\n';
    }
    return std::cin.eof()?0:4;
}
