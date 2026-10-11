#include "cn/assets/CnRomCommandReferences.h"
#include "cn/assets/CnAppearanceCacheSnapshot.h"
#include <utility>

namespace god2cn {
namespace {
bool known(const CnRomBankSlotSource& slot) {
    return (slot.kind==CnRomBankSlotSource::Kind::InitializedEmpty && !slot.metadata) ||
        (slot.kind==CnRomBankSlotSource::Kind::Loaded && slot.metadata);
}
std::uint16_t word(const std::vector<std::uint8_t>& bytes,std::size_t at) {
    return static_cast<std::uint16_t>(bytes[at]|(std::uint16_t(bytes[at+1])<<8));
}
void put_word(std::vector<std::uint8_t>& bytes,std::size_t at,std::uint16_t value) {
    bytes[at]=static_cast<std::uint8_t>(value);bytes[at+1]=static_cast<std::uint8_t>(value>>8);
}
}
std::optional<CnRomCommandProjection> CnRomCommandReferences::project(const CnRomAsset& source,
    const CnRomBankSourceView& bank,const CnAppearanceCacheSnapshot& cache) {
    if(!cache.selected_bank_current(bank.native_context,bank.native_bank_source_word,bank.owner_revision))return std::nullopt;
    auto result=project(source,bank);
    if(!result || !cache.selected_bank_current(bank.native_context,bank.native_bank_source_word,bank.owner_revision))return std::nullopt;
    return result;
}
std::optional<CnRomCommandProjection> CnRomCommandReferences::project(const CnRomAsset& source,const CnRomBankSourceView& bank) {
    if(!bank.owner_revision || bank.native_context>1 || bank.current_slot>=bank.slots.size() || !bank.current)
        return std::nullopt;
    const auto& own=bank.slots[bank.current_slot];
    if(own.kind!=CnRomBankSlotSource::Kind::Loaded || own.metadata!=&source || !bank.current())return std::nullopt;
    CnRomCommandProjection result{bank.owner_revision,bank.native_context,bank.current_slot,{}};
    const auto& actions=source.actions();
    for(std::size_t action=0;action<actions.size();++action) {
        for(std::size_t step=0;step<actions[action].steps.size();++step) {
            const auto raw=source.raw_record(actions[action].steps[step]);
            if(raw.empty() || raw.size()%10)return std::nullopt;
            CnRomCommandStepProjection output{action,step,{raw.begin(),raw.end()}};
            bool terminated=false;
            for(std::size_t at=0;at<output.bytes.size();at+=10) {
                if(output.bytes[at]==0) {terminated=true;break;}
                if(output.bytes[at]!=10)continue;
                const auto reference=word(output.bytes,at+2);
                auto slot=reference;
                if(reference==source.native_rom_identity())slot=bank.current_slot;
                else if(reference>1000) {
                    for(std::size_t index=0;index<bank.slots.size();++index) {
                        const auto& candidate=bank.slots[index];
                        if(!known(candidate))return std::nullopt; // Earlier unknown might be first matching ID.
                        if(candidate.kind==CnRomBankSlotSource::Kind::Loaded && candidate.metadata->native_rom_identity()==reference) {
                            slot=static_cast<std::uint16_t>(index);break;
                        }
                    }
                }
                put_word(output.bytes,at+2,slot);
                if(slot<bank.slots.size()) {
                    const auto& target=bank.slots[slot];if(!known(target))return std::nullopt;
                    const auto action_ref=word(output.bytes,at+4);
                    const auto projected=target.kind==CnRomBankSlotSource::Kind::Loaded?
                        target.metadata->native_action_index_operand(action_ref):
                        (action_ref<=256?action_ref:std::uint16_t{0xffff});
                    put_word(output.bytes,at+4,projected);
                }
            }
            if(!terminated)return std::nullopt;
            result.steps.push_back(std::move(output));
        }
    }
    if(!bank.current())return std::nullopt;
    return result; // Qualified source projection only, never executed ACT/gameplay.
}
}
