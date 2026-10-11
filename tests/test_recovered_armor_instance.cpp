#include "protocol/RecoveredArmorInstance.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
std::vector<std::uint8_t> unhex(const std::string& text){
 std::vector<std::uint8_t> result;require(text.size()%2==0,"Odd native hex");
 const auto digit=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("Bad native hex");};
 for(std::size_t i=0;i<text.size();i+=2)result.push_back(static_cast<std::uint8_t>(digit(text[i])*16+digit(text[i+1])));return result;
}
}
int main(){try{
 using Armor=god2::RecoveredArmorInstance;
 std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/current-armor-projection-20261002/native.json");require(file.good(),"Missing independent current native execution");
 nlohmann::json native;file>>native;
 require(native["status"]=="PASS"&&native["armor_unpack_full_return_cases"].size()==132,"Native armor vector qualification");
 for(const auto& test:native["armor_unpack_full_return_cases"]){
  const auto bytes=unhex(test["instance_hex"].get<std::string>());const auto before=bytes;
  require(test["full_return"].get<bool>(),"Native original function did not return");
  const auto result=Armor::unpack(bytes);require(result.has_value(),"Native20-byte operand rejected");
  const auto expected=test["values"].get<std::array<std::uint16_t,6>>();
  require((std::array{result->physical_defense,result->magical_defense,result->force,result->constitution,result->intelligence,result->speed}==expected),"C++ operands differ from original formatter call");
  require(bytes==before,"Unpacker modified instance");
 }
 for(std::size_t size=0;size<20;++size)require(!Armor::unpack(std::vector<std::uint8_t>(size)),"Truncated instance accepted");
 require(!Armor::unpack(std::vector<std::uint8_t>(21)),"Oversized instance accepted");
 for(unsigned family=0;family<64;++family)for(unsigned surrounding:{0u,0xC0u}){
  Armor::Instance instance{};instance[2]=static_cast<std::uint8_t>(family|surrounding);instance[3]=255;
  require(Armor::armor_family(instance)==(family==2||family==26),"Family selector differs from native dispatch");
 }
 std::cout<<"PASS132 C++ armor operands matched original function vectors; family/width guards\n";return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
