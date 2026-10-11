#pragma once
#include "db/SqliteBeastSnapshotRepository.h"
#include "game/RecoveredPosition.h"
#include "protocol/RecoveredWorldRecords.h"
#include <map>
namespace god2 {
// CUSTOM-0085 owned exploration presentation only. Native9D ->C5 pairing is
// custom, not an observed original-server exchange. No activity/economy effect.
class OwnedBeastExplorationService {
public:
    using Operation=std::variant<RecoveredBeastPanel::Request,RecoveredBeastExploration::Close>;
    struct View {
        std::uint64_t account{},character{};
        RecoveredPosition position;
        SqliteBeastSnapshotRepository::Selected selected;
        RecoveredBeastExploration::Snapshot snapshot;
    };
    static bool handles(std::span<const RecoveredWorldRecords::Record> records){
        return std::any_of(records.begin(),records.end(),[](const auto& row){return std::holds_alternative<RecoveredBeastPanel::Request>(row)||std::holds_alternative<RecoveredBeastExploration::Close>(row);});
    }
    static std::optional<Operation> request(std::span<const RecoveredWorldRecords::Record> records){
        std::optional<Operation> use;
        for(std::size_t i=0;i<records.size();++i){
            if(const auto* open=std::get_if<RecoveredBeastPanel::Request>(&records[i])){
                if(use||open->control!=RecoveredBeastPanel::Control::Eight)return {};use=*open;
            }else if(const auto* close=std::get_if<RecoveredBeastExploration::Close>(&records[i])){
                if(use)return {};use=*close;
            }else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!use||i+1!=records.size()||!std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return {};
        }
        return use;
    }
    std::optional<std::vector<std::uint8_t>> open(std::uint64_t session,std::uint64_t account,std::uint64_t character,
        const RecoveredPosition& position,const RecoveredBeastPanel::Request& request,
        const SqliteBeastSnapshotRepository::Selected& selected){
        const auto& beast=selected.instance;
        if(!session||account!=beast.account||character!=beast.character||!selected.revision||
           request.control!=RecoveredBeastPanel::Control::Eight||request.metadata_key!=beast.panel.metadata_key()||request.selector!=beast.panel.selector()||
           beast.panel.kind_display_raw2()!=2||beast.panel.control8_alternate()||!beast.exploration)return {};
        const auto& snapshot=*beast.exploration;
        // Present only the exact separately acquired snapshot, with a native
        // state0..3 UI branch. State4 is close; never fabricate an empty menu.
        if(snapshot.metadata_key()!=request.metadata_key||snapshot.selector()!=request.selector||snapshot.state_raw()>3)return {};
        auto wire=RecoveredWorldFrame::encode(snapshot.bytes);
        views_.insert_or_assign(session,View{account,character,position,selected,snapshot});return wire;
    }
    bool close(std::uint64_t session,std::uint64_t account,std::uint64_t character,const RecoveredBeastExploration::Close& request){
        const auto at=views_.find(session);
        if(at==views_.end()||at->second.account!=account||at->second.character!=character||at->second.snapshot.context()!=request.context)return false;
        // Native closes locally and sends the OLD context. Permit cleanup even
        // after25 changed the selected beast; never grant a current action lease.
        views_.erase(at);return true;
    }
    void disconnect(std::uint64_t session){views_.erase(session);}
private:
    std::map<std::uint64_t,View> views_;
};
}
