#include "game/TaiwanBattleSelfViewWriteFence.h"
#include <array>
#include <iostream>
#include <stdexcept>
#include <type_traits>
#include <vector>
namespace {
using namespace god2;
using Fence=TaiwanBattleSelfViewWriteFence;
using Bytes=std::vector<std::uint8_t>;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class Range>void append(Bytes& out,const Range& part){out.insert(out.end(),part.begin(),part.end());}
Bytes record(std::uint8_t opcode,std::size_t length){Bytes out(length);out[0]=opcode;return out;}
Bytes primary(std::uint8_t slot=0,std::uint8_t flags=1){auto out=record(0x86,17);out[1]=5;out[3]=flags;out[4]=slot;return out;}
Fence::Analysis inspect(const Bytes& logical){return Fence::inspect(RecoveredWorldFrame::encode(logical));}
void epoch_and_completion(){
    static_assert(!std::is_copy_constructible_v<Fence::Occurrence>);
    Fence fence;require(!fence.current(0)&&!fence.current(UINT64_MAX),"Unissued/exhausted view epoch was current");
    const auto first=fence.advance();Fence::Occurrence pending;
    require(fence.current(first)&&!pending.written(),"Prepared primary view was already Written");
    const auto second=fence.advance();Fence::Occurrence next;
    require(!fence.current(first)&&fence.current(second),"A later writer preserved the old view epoch");
    require(pending.complete(true)&&pending.written()&&!fence.current(first),
        "A late complete old write revived its view epoch");
    require(next.complete(true)&&next.written()&&fence.current(second),"Current exact whole write failed qualification");
    require(!next.complete(true)&&!next.written(),"Duplicate completion remained an eligible occurrence");
    Fence::Occurrence failed;require(!failed.complete(false)&&!failed.complete(true)&&!failed.written(),
        "Failed occurrence was revived by a later Written callback");
    Fence::Occurrence cancelled;cancelled.revoke();
    require(!cancelled.complete(true)&&!cancelled.written(),"Cancelled occurrence was revived");
}
void pending_writer_intents(){
    Fence intents,queued;
    const auto original_ticket=intents.advance();
    const auto newer_pending=intents.advance();
    // The older original may reach append/whole-write after a newer API call
    // has posted its writer. A fresh FIFO epoch cannot repair that old ticket.
    const auto older_append=queued.advance();Fence::Occurrence older;
    require(older.complete(true)&&queued.current(older_append)&&!intents.current(original_ticket)&&
        intents.current(newer_pending),"An old original append regained qualification across pending intent");
    const auto fresh_ticket=intents.advance(),fresh_append=queued.advance();Fence::Occurrence fresh;
    require(fresh.complete(true)&&intents.current(fresh_ticket)&&queued.current(fresh_append),
        "A later genuine original source could not qualify its new intent and whole Write");
    (void)intents.advance();
    require(fresh.written()&&!intents.current(fresh_ticket),"A pending newer writer left its old Written source current");
}
void ordered_writer_boundaries(){
    for(const std::uint8_t slot:{0,1,13}){
        const auto view=inspect(primary(slot));
        require(view.changes_view&&view.primary_slot==slot,"Primary setter lost its exact slot");
        const auto logical_view=Fence::inspect_logical(primary(slot));
        require(logical_view.changes_view==view.changes_view&&logical_view.primary_slot==view.primary_slot,
            "Pre-handoff logical classifier disagreed with complete wire records");
        require(inspect(primary(static_cast<std::uint8_t>(0xa0|slot),3)).primary_slot==slot,
            "Primary low nibble was confused with the secondary selector");
    }
    auto bootstrap=record(0x82,9);append(bootstrap,record(0x1c,45));append(bootstrap,primary(0));
    require(inspect(bootstrap).primary_slot==0,"Complete bootstrap preceding1C/reset blocked its final primary setter");
    append(bootstrap,record(0x1c,45));
    require(inspect(bootstrap).changes_view&&!inspect(bootstrap).primary_slot,
        "Later identity writer failed to retire the earlier primary");
    auto reset_after=primary();append(reset_after,record(0x82,9));
    require(!inspect(reset_after).primary_slot,"Later battle reset preserved an earlier primary");
    auto last_primary=primary(1);append(last_primary,primary(2));
    require(inspect(last_primary).primary_slot==2,"The first primary won over a later setter");
    require(!inspect(primary(2,2)).changes_view,"Secondary-only notification was treated as a primary setter");
    for(const auto alias:{record(0x2a,37),record(0xcf,177),primary(14),primary(15)}){
        require(inspect(alias).changes_view&&!inspect(alias).primary_slot,"Ambiguous/invalid setter became a view");
        auto before=alias;append(before,primary());
        require(!inspect(before).primary_slot,"Later grant hid an unqualified world phase/invalid setter");
        auto after=primary();append(after,alias);
        require(!inspect(after).primary_slot,"A later ambiguous writer preserved an old candidate");
        auto separate=RecoveredWorldFrame::encode(alias);
        append(separate,RecoveredWorldFrame::encode(primary()));
        require(!Fence::inspect(separate).primary_slot,
            "A later envelope repaired a whole-Write poison boundary");
    }
    auto opaque=record(0x86,17);opaque[1]=4;opaque[4]=0x82;opaque[5]=0x1c;opaque[6]=0xcf;
    require(!inspect(opaque).changes_view,"Opaque appearance bytes were scanned for opcodes");
    const auto first=RecoveredWorldFrame::encode(record(0x1c,45));
    auto multiple=first;append(multiple,RecoveredWorldFrame::encode(primary(13)));
    require(Fence::inspect(multiple).primary_slot==13,"Complete later envelope lost the last primary setter");
    append(multiple,RecoveredWorldFrame::encode(record(0x1c,45)));
    require(!Fence::inspect(multiple).primary_slot,"Later-envelope identity writer was skipped");
    auto unknown=primary();unknown.push_back(0xfe);
    require(!inspect(unknown).primary_slot&&inspect(unknown).changes_view,"Unknown suffix retained a candidate");
    const auto valid=RecoveredWorldFrame::encode(primary());
    for(std::size_t length=0;length<valid.size();++length){
        const auto result=Fence::inspect(std::span(valid).first(length));
        require(result.changes_view&&!result.primary_slot,"Truncated envelope qualified a view");
    }
    auto corrupt=valid;corrupt.back()^=1;
    require(!Fence::inspect(corrupt).primary_slot&&Fence::inspect(corrupt).changes_view,
        "Corrupt envelope qualified a view");
    auto malformed=primary();malformed.pop_back();
    require(!inspect(malformed).primary_slot,"Truncated native control record qualified a view");
}
}
int main(){try{epoch_and_completion();pending_writer_intents();ordered_writer_boundaries();}
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
