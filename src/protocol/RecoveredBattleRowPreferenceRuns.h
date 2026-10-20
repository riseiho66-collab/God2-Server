#pragma once
#include "protocol/RecoveredWorldRecords.h"
#include <optional>
#include <span>
#include <vector>
namespace god2 {
// Synchronous only: Session's actual GAME post owns original records until
// callback return. Keep their exact addresses for movement/C28/terminal
// receipts. Only our B4 request values and run boundaries are copied.
struct RecoveredBattleRowPreferenceRuns {
    using Record=RecoveredWorldRecords::Record;
    struct Step {
        std::size_t begin,count;
        std::optional<RecoveredBattleRowPreference::Request> choice;
    };
    class Plan {
    public:
        bool has_row() const noexcept {return has_row_;}
        template<class Forward,class Choose> bool dispatch(Forward&& forward,Choose&& choose) const {
            for(const auto& step:steps_) {
                if(step.choice) {if(!choose(*step.choice))return false;}
                else if(!forward(original_.subspan(step.begin,step.count)))return false;
            }
            return true;
        }
    private:
        friend struct RecoveredBattleRowPreferenceRuns;
        explicit Plan(std::span<const Record> original):original_(original) {}
        std::span<const Record> original_;
        std::vector<Step> steps_;
        bool has_row_=false;
    };
    static std::optional<Plan> prepare(std::span<const Record> original) {
        Plan plan(original);
        for(const auto& value:original)if(const auto* row=std::get_if<RecoveredBattleRowPreference::Request>(&value)) {
            if(row->row>1)return {};
            plan.has_row_=true;
        }
        if(!plan.has_row_) {
            // Includes empty and unrelated C28/terminal input. One exact
            // original span, never a value-equal copied vector.
            plan.steps_.push_back({0,original.size(),{}});return plan;
        }
        for(const auto& value:original)if(!std::holds_alternative<RecoveredBattleRowPreference::Request>(value) &&
            !std::holds_alternative<RecoveredMovement::Request>(value) &&
            !std::holds_alternative<RecoveredWorldRecords::Tick>(value))return {};
        for(std::size_t i=0;i<original.size();) {
            if(const auto* row=std::get_if<RecoveredBattleRowPreference::Request>(&original[i])) {
                plan.steps_.push_back({i,1,*row});++i;continue;
            }
            const auto begin=i;
            while(i<original.size() && !std::holds_alternative<RecoveredBattleRowPreference::Request>(original[i]))++i;
            plan.steps_.push_back({begin,i-begin,{}});
        }
        return plan;
    }
};
}
