#include "db/SqliteCompanionRepository.h"
#include "db/SqliteSupport.h"
#include <limits>

namespace god2 {
namespace {
bool same_reserve(const StoredPet2Slot& a,const StoredPet2Slot& b) {
    if(a.slot!=b.slot || a.revision!=b.revision || a.provenance!=b.provenance ||
       bool(a.pet)!=bool(b.pet) || bool(a.pet1)!=bool(b.pet1)) return false;
    if(a.pet1) return RecoveredPet2Lifecycle::same_owner(a.pet1->owner,b.pet1->owner) &&
        a.pet1->inventory==b.pet1->inventory &&
        RecoveredPet1Stats::encode_logical(a.pet1->stats)==RecoveredPet1Stats::encode_logical(b.pet1->stats);
    return !a.pet || (RecoveredPet2Lifecycle::same_owner(a.pet->owner,b.pet->owner) &&
        a.pet->inventory==b.pet->inventory &&
        RecoveredPet2Stats::encode_logical(a.pet->stats)==RecoveredPet2Stats::encode_logical(b.pet->stats));
}
bool reserve(std::uint8_t slot) {return slot==42 || slot==43;}
std::uint64_t advance(std::uint64_t revision) {
    if(!revision || revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))
        throw DatabaseError("Pet reserve revision exhausted");
    return revision+1;
}
void reroute(StoredPet2Slot& value) {
    if(value.pet1) {
        auto bytes=RecoveredPet1Stats::encode_logical(value.pet1->stats);bytes[0x27]=value.slot;
        value.pet1->stats=RecoveredPet1Stats::parse_logical(bytes).value();
    } else if(value.pet) {
        auto bytes=RecoveredPet2Stats::encode_logical(value.pet->stats);bytes[3]=value.slot;
        value.pet->stats=RecoveredPet2Stats::parse_logical(bytes).value();
    }
}
}
Pet2TransferCommit SqliteCompanionRepository::move_pet_reserves(std::uint64_t account,
        std::uint64_t character,const StoredPet2Slot& source,const StoredPet2Slot& destination,
        const std::function<void(const Pet2TransferCommit&)>& prepare) {
    if(!reserve(source.slot) || !reserve(destination.slot) || source.slot==destination.slot ||
       !source.occupied() || (source.pet && source.pet1) || (destination.pet && destination.pet1) || !prepare)
        throw DatabaseError("Invalid pet reserve move");
    sqlite_detail::Transaction transaction(db_);
    const auto before=load_pet2_slots(account,character);
    const auto find=[&](const auto& rows,std::uint8_t slot) {
        return std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.slot==slot;});
    };
    const auto current_source=find(before,source.slot),current_destination=find(before,destination.slot);
    if(current_source==before.end() || current_destination==before.end() ||
       !same_reserve(*current_source,source) || !same_reserve(*current_destination,destination))
        throw DatabaseError("Pet reserve version conflict");
    require_no_pending_battle(character);
    // CUSTOM-0039: reorder complete owned instances, preserving all source
    // provenance and opaque data. Only native routing bytes and revisions vary.
    Pet2TransferCommit next{destination,source};
    next.source.slot=source.slot;next.destination.slot=destination.slot;
    next.source.revision=advance(source.revision);next.destination.revision=advance(destination.revision);
    reroute(next.source);reroute(next.destination);
    const auto write=[&](const StoredPet2Slot& value,std::uint64_t expected) {
        sqlite_detail::Statement update(db_,"UPDATE character_pet2_slots SET metadata=?,stats=?,revision=?,source_sha256=?,authority=?,evidence_id=? WHERE character_id=? AND slot=? AND revision=?");
        if(value.pet1) {update.bind_blob(1,value.pet1->inventory);update.bind_blob(2,RecoveredPet1Stats::encode_logical(value.pet1->stats));}
        else if(value.pet) {update.bind_blob(1,value.pet->inventory);update.bind_blob(2,RecoveredPet2Stats::encode_logical(value.pet->stats));}
        else {update.bind_blob(1,{});update.bind_blob(2,{});}
        update.bind_id(3,value.revision);update.bind(4,value.provenance.source_sha256);
        update.bind(5,value.provenance.authority);update.bind(6,value.provenance.evidence_id);
        update.bind_id(7,character);update.bind(8,value.slot);update.bind_id(9,expected);update.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Pet reserve write rejected");
    };
    write(next.source,source.revision);write(next.destination,destination.revision);
    const auto verify=[&] {
        const auto after=load_pet2_slots(account,character);
        if(after.size()!=before.size()) throw DatabaseError("Pet reserve capacity changed");
        for(const auto& old:before) {
            const auto& expected=old.slot==next.source.slot?next.source:
                old.slot==next.destination.slot?next.destination:old;
            const auto saved=find(after,old.slot);
            if(saved==after.end() || !same_reserve(*saved,expected))
                throw DatabaseError("Pet reserve readback mismatch");
        }
    };
    verify();prepare(next);verify();transaction.commit();return next;
}
}
