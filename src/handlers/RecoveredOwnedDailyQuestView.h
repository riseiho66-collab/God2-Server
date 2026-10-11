#pragma once
#include "db/NativeQuestCatalog.h"
#include "protocol/RecoveredWorldRecords.h"
namespace god2 {
// CUSTOM-0049: owner-bound display and audit of unresolved NPC-transport /
// daily-claim intents. Original destination, ticket cost and awards are OPEN.
struct RecoveredOwnedDailyQuestView {
    using Request=std::variant<RecoveredWorldRecords::DailyPanelOpen,RecoveredDailyQuestRequest::Request>;
    static std::optional<Request> request(std::span<const RecoveredWorldRecords::Record> records) {
        std::optional<Request> value;
        for(std::size_t i=0;i<records.size();++i) {
            if(const auto* open=std::get_if<RecoveredWorldRecords::DailyPanelOpen>(&records[i])) {
                if(value)return std::nullopt;value=*open;
            } else if(const auto* action=std::get_if<RecoveredDailyQuestRequest::Request>(&records[i])) {
                if(value)return std::nullopt;value=*action;
            } else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!value || i+1!=records.size() || !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return std::nullopt;
        }
        return value;
    }
    static std::optional<NativeDailyQuestDisplay> binding(const OwnedDailyQuestList& list,
        const RecoveredDailyQuestRequest::Selection& selection,std::span<const NativeDailyQuestDisplay> source) {
        if(!RecoveredDailyQuestRequest::valid_list(list.logical))return std::nullopt;
        const auto row=std::find_if(source.begin(),source.end(),[&](const auto& r){return r.index==selection.index && r.branch==selection.branch;});
        if(row==source.end())return std::nullopt;
        for(std::size_t i=0;i<list.logical[164];++i) {
            const auto at=4+4*i;const auto flags=list.logical[at+3];
            if((flags&0xc0)!=0x40)continue;
            const RecoveredDailyQuestRequest::Binding bound{list.logical[at],list.logical[at+1],row->start_npc(),row->end_npc(),flags};
            if(RecoveredDailyQuestRequest::matches(selection,bound))return *row;
        }
        return std::nullopt;
    }
    // Issued FD daily-claim presentation gate only; no claim transaction.
    static bool auxiliary(const OwnedDailyQuestList& list) {
        return RecoveredDailyQuestRequest::valid_list(list.logical) &&
            (list.logical[165]>>4)==1 && (list.logical[170] || list.logical[171]);
    }
    // Native dialog32's BF bytes must match the same actually issued FD list.
    // This recognizes the presentation request only; displayed amount is not
    // a price or wallet authority and no item may be granted from this match.
    static std::optional<RecoveredBFRequest::DailyPurchase> purchase(
        const OwnedDailyQuestList& list,const RecoveredBFRequest::Request& request) {
        if(!RecoveredDailyQuestRequest::valid_list(list.logical) || (list.logical[165]&0x0f)!=1)return {};
        const auto shaped=RecoveredBFRequest::daily_purchase_shape(request);
        const auto item=static_cast<std::uint16_t>(list.logical[166] | (std::uint16_t{list.logical[167]}<<8));
        const auto amount=static_cast<std::uint32_t>(list.logical[168] | (std::uint16_t{list.logical[169]}<<8));
        if(!shaped || !item || shaped->item!=item || shaped->displayed_amount!=amount)return {};
        return shaped;
    }
};
}
