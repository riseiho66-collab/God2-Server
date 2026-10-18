#include "game/TaiwanWorldIdentityWriteFence.h"
#include <array>
#include <iostream>
#include <stdexcept>
#include <type_traits>
#include <vector>

namespace {
using namespace god2;
using Fence=TaiwanWorldIdentityWriteFence;
using Bytes=std::vector<std::uint8_t>;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
Bytes record(std::uint8_t opcode,std::size_t length){
    Bytes bytes(length,0);bytes[0]=opcode;return bytes;
}
template<class Range>void append(Bytes& bytes,const Range& part){bytes.insert(bytes.end(),part.begin(),part.end());}
void monotone_original_write(){
    static_assert(!std::is_copy_constructible_v<Fence>);
    Fence success;
    require(success.state()==Fence::State::Unbound&&!success.eligible(),"Unissued original qualified sender");
    require(success.admit_original()&&success.state()==Fence::State::BaselineQueued&&!success.eligible(),
        "Enqueue alone qualified original sender");
    require(success.complete_original(true)&&success.eligible(),"Exact original full write did not qualify sender");
    success.revoke();success.revoke();
    require(!success.complete_original(true)&&!success.admit_original()&&!success.eligible()&&
        success.state()==Fence::State::Revoked,"Late original completion resurrected revoked custody");
    for(const unsigned event:{0u,1u,2u}){
        Fence pending;require(pending.admit_original(),"Original admission failed");
        if(event==0)pending.revoke(); // Conflict while the original is still pending.
        else if(event==1)require(!pending.complete_original(false),"Failed write became Written");
        else require(!pending.admit_original(),"A second original replaced the first occurrence");
        require(!pending.complete_original(true)&&!pending.eligible()&&pending.state()==Fence::State::Revoked,
            "Cancellation/conflict followed by late full write revived custody");
    }
    Fence orphan;require(!orphan.complete_original(true)&&orphan.state()==Fence::State::Revoked,
        "Completion without original admission became eligible");
    Fence duplicate;require(duplicate.admit_original()&&duplicate.complete_original(true),"Original fixture failed");
    require(!duplicate.complete_original(true)&&!duplicate.eligible(),"Duplicate completion retained stale custody");
}
void complete_record_boundaries(){
    auto actor=record(0x1c,45);actor[11]=0x2a;actor[12]=0xcf;
    auto grant=record(0x86,17);grant[1]=5;grant[3]=1;grant[4]=2;grant[10]=0x2a;grant[11]=0xcf;
    const auto actor_wire=RecoveredWorldFrame::encode(actor);
    require(!Fence::conflicts_with_world_identity(actor_wire),"Opaque actor bytes were scanned as world opcodes");
    Bytes safe=actor;append(safe,grant);
    auto bulk=record(0x88,121);bulk[1]=1;append(safe,bulk);
    auto context=record(0x82,9);append(safe,context);
    const auto safe_wire=RecoveredWorldFrame::encode(safe);
    require(!Fence::conflicts_with_world_identity(safe_wire),"Normal1C/86-5 or complete PK records revoked R0 custody");
    auto multiple=safe_wire;append(multiple,actor_wire);
    require(!Fence::conflicts_with_world_identity(multiple),"Safe multi-envelope output revoked custody");
    for(const auto conflict:{record(0x2a,37),record(0xcf,177),record(0xfe,1)}){
        const auto wire=RecoveredWorldFrame::encode(conflict);
        require(Fence::conflicts_with_world_identity(wire),"World identity/unknown record did not conflict");
        auto one_frame=actor;append(one_frame,conflict);append(one_frame,grant);
        require(Fence::conflicts_with_world_identity(RecoveredWorldFrame::encode(one_frame)),
            "Conflict hidden after the first record was ignored");
        auto many_frames=actor_wire;append(many_frames,wire);append(many_frames,safe_wire);
        require(Fence::conflicts_with_world_identity(many_frames),"Conflict hidden in a later envelope was ignored");
    }
    auto unknown_suffix=safe;unknown_suffix.push_back(0xff);
    require(Fence::conflicts_with_world_identity(RecoveredWorldFrame::encode(unknown_suffix)),
        "Unparseable suffix was skipped after safe records");
    for(std::size_t length=0;length<safe_wire.size();++length)
        require(Fence::conflicts_with_world_identity(std::span(safe_wire).first(length)),
            "Truncated envelope admitted R0 custody");
    auto bad_checksum=safe_wire;bad_checksum.back()^=1;
    require(Fence::conflicts_with_world_identity(bad_checksum),"Corrupt envelope admitted custody");
    const std::array<std::uint8_t,4> invalid_length{3,0,0,0};
    require(Fence::conflicts_with_world_identity(invalid_length),"Invalid envelope size admitted custody");
    auto truncated_record=record(0xcf,176);
    require(Fence::conflicts_with_world_identity(RecoveredWorldFrame::encode(truncated_record)),
        "Complete envelope concealed an incomplete CF record");
    auto variable=Bytes{0x19,3,0};
    require(!Fence::conflicts_with_world_identity(RecoveredWorldFrame::encode(variable)),
        "Complete known variable record was treated as unknown");
    variable[1]=4;
    require(Fence::conflicts_with_world_identity(RecoveredWorldFrame::encode(variable)),
        "Truncated variable record admitted custody");
}
}
int main(){try{monotone_original_write();complete_record_boundaries();}
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
