#include "protocol/RecoveredPostCreateSelect.h"
#include "handlers/RecoveredCharacterService.h"
#include "db/SqliteDatabase.h"
#include <algorithm>
#include <stdexcept>
#include <vector>

namespace {
void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }
std::vector<std::uint8_t> frame(std::uint8_t opcode,std::vector<std::uint8_t> payload) {
    const auto length=static_cast<std::uint8_t>(payload.size()+4);
    std::vector<std::uint8_t> plain{length,0,opcode};plain.insert(plain.end(),payload.begin(),payload.end());
    std::uint8_t checksum=0;
    for(auto byte:plain) checksum=static_cast<std::uint8_t>(checksum+byte+0x3c);
    plain.push_back(checksum);auto wire=plain;std::uint8_t previous=0;
    for(std::size_t i=2;i<wire.size();++i) {
        wire[i]=static_cast<std::uint8_t>((plain[i]^god2::recovered_zero_seed_key[i-2])+previous-3);previous=plain[i];
    }
    return wire;
}
std::vector<std::uint8_t> pair(std::vector<std::uint8_t> payload,std::uint8_t first=0x18,std::uint8_t second=0x1a) {
    auto result=frame(first,{0xff});const auto next=frame(second,payload);
    result.insert(result.end(),next.begin(),next.end());return result;
}
template<class F> void rejects(F call) {
    try { call(); } catch(const std::exception&) { return; }
    throw std::runtime_error("Invalid post-create selection accepted");
}
}
void test_post_create_select() {
    using god2::RecoveredPostCreateSelect;
    std::vector<std::uint8_t> payload(37,0xab);payload[15]=0;payload[31]=0;payload[32]=0;payload[33]=4;
    const auto wire=pair(payload);const auto parsed=RecoveredPostCreateSelect::parse(wire);
    require(parsed && parsed->context_byte==255 && parsed->selection_token==0,"Valid pair rejected");
    for(std::size_t i=0;i<wire.size();++i)
        require(!RecoveredPostCreateSelect::parse(std::span(wire).first(i)),"Truncation accepted");
    auto invalid=wire;invalid.push_back(0);
    require(!RecoveredPostCreateSelect::parse(invalid),"Extra frame bytes accepted");
    for(std::size_t i=0;i<wire.size();++i) {
        invalid=wire;invalid[i]^=1;
        require(!RecoveredPostCreateSelect::parse(invalid),"Corruption accepted");
    }
    for(const auto index:{15,31,32,33}) {
        auto bad=payload;bad[index]=index==33?3:4;
        require(!RecoveredPostCreateSelect::parse(pair(bad)),"Known builder constraint ignored");
    }
    require(!RecoveredPostCreateSelect::parse(pair(payload,0x1a)),"Wrong first opcode accepted");
    require(!RecoveredPostCreateSelect::parse(pair(payload,0x18,0x1b)),"Wrong second opcode accepted");
    // Repository/service ownership is independent of the opaque input buffers.
    god2::SqliteDatabase db(":memory:");db.initialize();db.migrate();
    const auto owner=db.accounts().create("owner","test-hash").id;
    const auto other=db.accounts().create("other","test-hash").id;
    god2::RecoveredCharacterService service(db.recovered_characters());
    god2::RecoveredCharacterCreate create{};
    create.payload[0]='A';create.payload[29]=1;create.payload[31]=1;create.payload[40]=4;
    create.payload[32]=6;create.payload[36]=0xa0;
    const auto id=service.create(owner,create);
    require(service.created_slot(owner,id)==0,"Committed slot lookup failed");
    rejects([&]{service.created_slot(other,id);});
    rejects([&]{service.created_slot(owner,id+1);});
    rejects([&]{service.created_slot(0,id);});
    rejects([&]{service.created_slot(owner,0);});
    require(service.select_existing(owner,0)==id,"Existing owned profile not selected");
    rejects([&]{service.select_existing(other,0);});
    rejects([&]{service.select_existing(owner,1);});
    rejects([&]{service.select_existing(owner,4);});
    rejects([&]{service.select_existing(0,0);});
    require(service.select_created(owner,id,0)==id,"Owned committed profile not selected");
    const auto stored=db.recovered_characters().list_for_account(owner).front().profile;
    require(service.world_entry_candidate(owner,id)==god2::RecoveredWorldEntry::wire(id,stored),"Owned world candidate profile lost");
    rejects([&]{service.world_entry_candidate(other,id);});
    rejects([&]{service.world_entry_candidate(owner,id+1);});
    rejects([&]{service.world_entry_candidate(0,id);});
    rejects([&]{service.world_entry_candidate(owner,0);});
    rejects([&]{service.select_created(other,id,0);});
    rejects([&]{service.select_created(owner,id,1);});
    rejects([&]{service.select_created(owner,id+1,0);});
    rejects([&]{service.select_created(0,id,0);});
    rejects([&]{service.select_created(owner,0,0);});
    require(db.characters().list_for_account(owner).empty(),"Profile selection initialized mock world state");
    const auto selection=frame(0x1a,payload);
    require(RecoveredPostCreateSelect::selection_token_from_frame(selection)==0,"Standalone selection token zero lost");
    for(std::size_t i=0;i<selection.size();++i)
        require(!RecoveredPostCreateSelect::selection_token_from_frame(std::span(selection).first(i)),"Selection truncation accepted");
}
