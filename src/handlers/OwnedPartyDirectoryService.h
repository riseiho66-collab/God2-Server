#pragma once
#include "game/OwnedPartyDirectory.h"
#include "protocol/RecoveredWorldFrame.h"
#include "text/LegacyChineseCodec.h"
#include "text/ChineseText.h"
#include <algorithm>
#include <stdexcept>
namespace god2 {
// Concrete bounded COW planner. Application reobserves every supplied owner and
// scene plus exact private initialization before publishing this prepared state.
struct OwnedPartyDirectoryService {
    struct Prepared {OwnedPartyDirectory::Snapshot state;std::vector<std::uint8_t> logical;};
    struct Delivery {OwnedPartyDirectory::Actor recipient;std::vector<std::uint8_t> logical;};
    struct WatchPlan {OwnedPartyDirectory::Snapshot state;std::vector<Delivery> deliveries;};
    // Read-only recorded-game-owner qualification. Equal serialized entry
    // bytes cannot renew an old private permission or issued-AB receipt.
    static bool captured_entry_current(const OwnedPartyDirectory::Actor& actor) {
        const auto peer=actor.session.lock();
        return peer && actor.initialization.entry_written() &&
            peer->normal_world_initialization_current_on_game(actor.initialization);
    }
    static bool description_valid(const std::array<std::uint8_t,24>& raw) {
        const auto end=std::find(raw.begin()+2,raw.end(),0);
        if(end==raw.end() || end-(raw.begin()+2)>20)return false;
        const std::string bytes(reinterpret_cast<const char*>(raw.data()+2),end-(raw.begin()+2));
        if(bytes.empty())return true;
        try {
            const auto utf8=LegacyChineseCodec::decode(bytes,false);
            return ChineseText::valid_utf8(utf8) && utf8.find('\0')==utf8.npos && LegacyChineseCodec::encode(utf8,false)==bytes;
        } catch(const std::invalid_argument&) {return false;}
    }
    static std::optional<Prepared> prepare(const OwnedPartyDirectory::Snapshot& before,
        const OwnedPartyDirectory::Actor& owner,const TaiwanNativePartyMenu::Request& request,
        const std::vector<OwnedPartyDirectory::Actor>& live,std::size_t capacity) {
        if(!before || !capacity || !TaiwanNativePartyMenu::decode(request.logical))return {};
        if(request.opcode()==0x90 || request.opcode()==0x91)return {};
        if(request.opcode()==0x8f && !description_valid(request.query()))return {};
        auto next=std::make_shared<OwnedPartyDirectory::State>(*before);
        const auto find=[&](const auto& actor)->const OwnedPartyDirectory::Actor* {
            for(const auto& current:live)if(actor.same_owner(current))return &current;return nullptr;
        };
        for(auto at=next->listings.begin();at!=next->listings.end();) {
            const auto current=find(at->second.actor);
            if(!current)at=next->listings.erase(at);else {at->second.actor=*current;++at;}
        }
        for(auto at=next->queries.begin();at!=next->queries.end();) {
            if(at->second.actor.session.expired())at=next->queries.erase(at);else ++at;
        }
        auto query=next->queries.find(owner.session_id);
        if(query!=next->queries.end() && !query->second.actor.same_owner(owner))return {};
        const auto op=request.opcode();
        if(op==0x8d) {
            next->queries.erase(owner.session_id); // Both native close modes retire issued mappings.
            if(request.logical[1]==2)if(const auto at=next->listings.find(owner.session_id);at!=next->listings.end() && at->second.actor.same_owner(owner))next->listings.erase(at);
            // No guessed close/delist ACK. Other watchers refresh by query.
            return Prepared{std::move(next),{}};
        }
        if(op==0x8e || op==0x8f) {
            if(!next->queries.contains(owner.session_id) && next->queries.size()>=capacity)return {};
            // Re-query retains its issued identity mapping until explicit close.
            auto issued=query==next->queries.end()?std::map<std::uint16_t,OwnedPartyDirectory::Actor>{}:query->second.issued;
            next->queries.insert_or_assign(owner.session_id,OwnedPartyDirectory::Query{owner,request.query(),0,std::move(issued)});
            if(op==0x8f) {
                if(!next->listings.contains(owner.session_id) && next->listings.size()>=capacity)return {};
                next->listings.insert_or_assign(owner.session_id,OwnedPartyDirectory::Listing{owner,request.query()});
            }
        } else if(query==next->queries.end())return {};
        auto& q=next->queries.at(owner.session_id);q.actor=owner;
        q.detail.reset();q.last_join_request.clear();q.presentation.reset();q.visible.clear(); // Actual full A7 clears native AB and private permission.
        std::vector<const OwnedPartyDirectory::Listing*> entries;
        std::map<std::uint16_t,const OwnedPartyDirectory::Actor*> unique;
        for(const auto& [id,listing]:next->listings) {
            if(listing.actor.position.area!=owner.position.area || listing.actor.position.scene!=owner.position.scene)continue;
            if(listing.actor.native_actor==owner.native_actor && !listing.actor.same_owner(owner))return {};
            if(!unique.emplace(listing.actor.native_actor,&listing.actor).second)return {};
            if(const auto old=q.issued.find(listing.actor.native_actor);old!=q.issued.end() && !old->second.same_owner(listing.actor))return {};
            entries.push_back(&listing);
        }
        // CUSTOM-0097 stable full session ordering, six rows per page; raw
        // selectors/text do not filter, authorize, or change party membership.
        const auto last=entries.empty()?0:(entries.size()-1)/6;
        if(op==0x92) {if(request.logical[1]==0xff){if(q.page)--q.page;}else if(q.page<last)++q.page;}
        q.page=std::min(q.page,last);
        std::vector<TaiwanNativePartyMenu::Row> rows;
        for(std::size_t i=q.page*6;i<entries.size() && i<q.page*6+6;++i) {
            const auto& entry=*entries[i];if(!description_valid(entry.raw))return {};
            std::array<std::uint8_t,22> description{};
            std::copy_n(entry.raw.begin()+2,22,description.begin());
            rows.push_back({entry.actor.native_actor,entry.actor.level,entry.actor.profession,description,entry.actor.name});
            if(!q.issued.contains(entry.actor.native_actor) && q.issued.size()>=capacity)return {};
            q.issued.insert_or_assign(entry.actor.native_actor,entry.actor);
            q.visible.push_back(entry.actor.native_actor);
            q.descriptions.insert_or_assign(entry.actor.native_actor,description);
        }
        const auto reply=TaiwanNativePartyMenu::list(rows);if(!reply)return {};
        return Prepared{std::move(next),*reply};
    }
    // CUSTOM-0099/0101 read-only bounded planner: actual live observations and
    // private receipt checks are requalified before Application publishes COW.
    static std::optional<WatchPlan> watch(const OwnedPartyDirectory::Snapshot& before,
        const OwnedPartyDirectory::Snapshot& mutation,const std::vector<OwnedPartyDirectory::Actor>& live,
        const NativeParty& parties,std::size_t capacity,std::uint64_t skip_recipient=0,
        const Session* retired=nullptr) {
        if(!before || !mutation || !capacity || mutation->queries.size()>capacity || mutation->listings.size()>capacity)return {};
        auto next=std::make_shared<OwnedPartyDirectory::State>(*mutation);
        const auto find=[&](const auto& actor)->const OwnedPartyDirectory::Actor* {
            if(retired && actor.session.lock().get()==retired)return nullptr;
            for(const auto& current:live)if(actor.same_owner(current))return &current;
            return nullptr;
        };
        for(auto at=next->listings.begin();at!=next->listings.end();) {
            if(const auto current=find(at->second.actor)){at->second.actor=*current;++at;}
            else at=next->listings.erase(at);
        }
        for(auto at=next->queries.begin();at!=next->queries.end();) {
            if(const auto current=find(at->second.actor)){at->second.actor=*current;++at;}
            else at=next->queries.erase(at);
        }
        WatchPlan result;
        for(auto& [id,destination]:next->queries) {
            if(id==skip_recipient)continue; // Caller already has its exact prepared A7.
            const auto old_at=before->queries.find(id);
            if(old_at==before->queries.end())return {};
            const auto& old=old_at->second;
            if(!old.actor.same_owner(destination.actor))return {};
            // CUSTOM-0102 stage one query separately. Native WORD tombstones,
            // row/cache preparation and permission changes cannot leak from
            // a rejected projection into the conservative empty-A7 fallback.
            auto q=destination;
            const auto project=[&]()->std::optional<std::vector<std::uint8_t>> {
            bool invalid_detail=false;
            // CUSTOM-0101: C91 may already have consumed private permission
            // while the native AB bank still displays its previously issued
            // group. Compare that presentation independently of permission.
            if(q.presentation) {
                const auto& p=*q.presentation;
                const auto target=find(p.target);
                // The read-only planner also qualifies each retained private
                // receipt on its recorded game owner. Equal entry bytes do
                // not establish that an old issued-AB epoch is still current.
                invalid_detail=!captured_entry_current(p.owner) || !captured_entry_current(p.target) ||
                    !p.owner.same_detail_identity(q.actor) || !target ||
                    !p.target.same_detail_identity(*target) ||
                    p.participants!=parties.participants(p.target.session_id) ||
                    p.party_size!=parties.party_size(p.target.session_id) ||
                    !next->listings.contains(p.target.session_id);
                for(const auto& member:p.members) {
                    const auto current=find(member);
                    if(!captured_entry_current(member) || !current || !member.same_detail_identity(*current))invalid_detail=true;
                }
            }
            if(q.detail) {
                const auto& d=*q.detail;
                const auto target=find(d.target);
                invalid_detail=invalid_detail || !d.party || !captured_entry_current(d.owner) || !captured_entry_current(d.target) ||
                    !d.owner.same_detail_identity(q.actor) || !target ||
                    !d.target.same_detail_identity(*target) ||
                    d.party->participants(d.target.session_id)!=parties.participants(d.target.session_id) ||
                    d.party->party_size(d.target.session_id)!=parties.party_size(d.target.session_id) ||
                    !next->listings.contains(d.target.session_id);
                for(const auto& member:d.members) {
                    const auto current=find(member);
                    if(!captured_entry_current(member) || !current || !member.same_detail_identity(*current))invalid_detail=true;
                }
            }
            std::vector<const OwnedPartyDirectory::Listing*> entries;
            std::map<std::uint16_t,std::uint64_t> unique;
            for(const auto& [owner,listing]:next->listings) {
                if(listing.actor.position.area!=q.actor.position.area || listing.actor.position.scene!=q.actor.position.scene)continue;
                if((listing.actor.native_actor==q.actor.native_actor && !listing.actor.same_owner(q.actor)) ||
                   !unique.emplace(listing.actor.native_actor,owner).second)return {};
                if(const auto previous=q.issued.find(listing.actor.native_actor);previous!=q.issued.end() && !previous->second.same_owner(listing.actor))return {};
                entries.push_back(&listing);
            }
            const auto last=entries.empty()?0:(entries.size()-1)/6;
            q.page=std::min(q.page,last);
            std::vector<TaiwanNativePartyMenu::Row> rows;
            std::vector<std::uint16_t> visible;
            for(std::size_t i=q.page*6;i<entries.size() && i<q.page*6+6;++i) {
                const auto& listing=*entries[i];if(!description_valid(listing.raw))return {};
                std::array<std::uint8_t,22> desc{};std::copy_n(listing.raw.begin()+2,22,desc.begin());
                rows.push_back({listing.actor.native_actor,listing.actor.level,listing.actor.profession,desc,listing.actor.name});
                visible.push_back(listing.actor.native_actor);
            }
            bool stable=old.page==q.page;
            std::vector<std::size_t> changed;
            for(std::size_t i=0;i<rows.size();++i) {
                const auto& row=rows[i];const auto issued=old.issued.find(row.native_actor);const auto desc=old.descriptions.find(row.native_actor);
                if(issued==old.issued.end() || desc==old.descriptions.end() ||
                   issued->second.name!=row.name || issued->second.level!=row.level || issued->second.profession!=row.profession)stable=false;
                else if(desc->second!=row.description)changed.push_back(i);
            }
            std::vector<std::uint8_t> logical;
            bool emit=invalid_detail;
            if(old.visible==visible && stable && !invalid_detail) {
                bool delta=!old.detail && !old.presentation && old.last_join_request.empty();
                for(const auto index:changed) {
                    const auto& row=rows[index];const auto& prior=old.descriptions.at(row.native_actor);
                    const auto end=std::find(row.description.begin(),row.description.end(),0);
                    // strcpy writes through NUL only. Full desired bytes after that
                    // position must equal the actual previously issued destination.
                    if(end==row.description.end() || !std::equal(end+1,row.description.end(),prior.begin()+(end-row.description.begin())+1))delta=false;
                }
                if(!changed.empty()) {
                    emit=true;
                    if(delta)for(const auto index:changed) {
                        const auto update=TaiwanNativePartyMenu::description(rows[index].native_actor,rows[index].description);if(!update)return {};
                        logical.insert(logical.end(),update->begin(),update->end());
                    }
                }
            } else {
                emit=true;
                // A8 only for exact visible withdrawals with no refill, reorder,
                // other row changes or live AB detail needing the A7 clear.
                std::vector<std::uint16_t> survivors;
                for(const auto key:old.visible)if(std::find(visible.begin(),visible.end(),key)!=visible.end())survivors.push_back(key);
                if(stable && changed.empty() && survivors==visible && visible.size()<old.visible.size() && !old.detail && !old.presentation && old.last_join_request.empty() && !invalid_detail) {
                    for(const auto key:old.visible)if(std::find(visible.begin(),visible.end(),key)==visible.end()) {
                        const auto issued=old.issued.find(key);if(issued==old.issued.end())return {};
                        // No replacement owner may inherit a previously issued WORD.
                        const auto remaining=unique.find(key);if(remaining!=unique.end() && remaining->second!=issued->second.session_id)return {};
                        const auto remove=TaiwanNativePartyMenu::withdrawn(key);if(!remove)return {};
                        logical.insert(logical.end(),remove->begin(),remove->end());
                    }
                }
            }
            if(emit && logical.empty()) {
                const auto full=TaiwanNativePartyMenu::list(rows);if(!full)return {};logical=*full;
            }
            for(std::size_t i=0;i<visible.size();++i) {
                const auto key=visible[i];const auto listing=entries[q.page*6+i];
                if(!q.issued.contains(key) && q.issued.size()>=capacity)return {};
                q.issued.insert_or_assign(key,listing->actor);q.descriptions.insert_or_assign(key,rows[i].description);
            }
            q.visible=std::move(visible);
            if(emit) {
                q.detail.reset();q.last_join_request.clear();q.presentation.reset();
            }
            if(logical.size()>RecoveredWorldFrame::max_logical_size)return {};
            return logical;
            };
            auto logical=project();
            if(!logical) {
                // The intended rows did not qualify. Clear only this current
                // recipient's visible native banks; issued owner tombstones
                // remain EXACTLY as before the failed attempt. No ID rebind,
                // replacement permission or successful intended-list claim.
                q=destination;
                // An already recorded empty native baseline needs no repeated
                // clear on every ordinary packet. A previous AB/private join
                // or nonempty cache always requires the first real empty A7.
                const bool already_empty=q.page==0 && q.visible.empty() && q.descriptions.empty() &&
                    !q.detail && !q.presentation && q.last_join_request.empty();
                const auto empty=TaiwanNativePartyMenu::list(std::span<const TaiwanNativePartyMenu::Row>{});
                if(!empty)return {}; // Global inability to prepare even qualified empty A7.
                q.page=0;q.visible.clear();q.descriptions.clear();
                q.detail.reset();q.presentation.reset();q.last_join_request.clear();
                logical=already_empty?std::vector<std::uint8_t>{}:*empty;
            }
            destination=std::move(q);
            if(!logical->empty())result.deliveries.push_back({destination.actor,std::move(*logical)});
        }
        if(result.deliveries.size()>capacity)return {};
        result.state=std::move(next);return result;
    }

};
}
