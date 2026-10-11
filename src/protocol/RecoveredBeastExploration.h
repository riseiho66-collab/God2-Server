#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current mapped image149c1b45...: C5 ->469D7E ->4D8490 copies308 bytes;
// C6 ->469D90 ->4A0A90 updates the context DWORD and state byte, or closes.
// C2S9E/9F are distinct from unrelated S2C9E/9F. Exact native widths only:
// this is not an exploration/reward/timer rule or an Application handler.
struct RecoveredBeastExploration {
    static constexpr std::uint8_t snapshot_opcode=0xc5, state_opcode=0xc6;
    static constexpr std::uint8_t action_opcode=0x9e, close_opcode=0x9f;
    static constexpr std::size_t snapshot_size=309,state_size=7,action_size=7,close_size=5;
    static constexpr std::size_t message_capacity=50;
    using Context=std::array<std::uint8_t,4>;
    using SnapshotBytes=std::array<std::uint8_t,snapshot_size>;
    using StateBytes=std::array<std::uint8_t,state_size>;
    struct Action {
        Context context;
        // 4D8810 emits0 from state0 or1 from state2, with one-based selected
        // index. 4D8780 emits2 and a zero-based selected index (FF if none).
        // No gameplay verbs are inferred from these numeric branches.
        std::uint8_t operation,selection;
    };
    struct Close {Context context;};
    struct Snapshot {
        SnapshotBytes bytes;
        bool operator==(const Snapshot&) const=default;
        Context context() const noexcept {return get_context(bytes);}
        std::uint16_t metadata_key() const noexcept {return word(bytes,1);}
        std::uint8_t selector() const noexcept {return bytes[3];}
        std::uint8_t context_tail_raw() const noexcept {return bytes[4];}
        std::uint8_t state_raw() const noexcept {return bytes[5];}
        // 4D8B70 clamps the message template count to50 before reading both
        // WORD arrays. Preserve the transmitted byte independently.
        std::uint8_t message_count_raw() const noexcept {return bytes[6];}
        std::size_t displayed_message_count() const noexcept {return std::min<std::size_t>(message_count_raw(),message_capacity);}
        std::optional<std::uint16_t> message_key(std::size_t index) const noexcept {
            if(index>=message_capacity)return {};return word(bytes,7+2*index);
        }
        std::optional<std::uint16_t> item_argument_key(std::size_t index) const noexcept {
            if(index>=message_capacity)return {};return word(bytes,107+2*index);
        }
        std::uint8_t selected_raw() const noexcept {return bytes[207];}
        // Independent from message template count. Do not assume this is
        // bounded by50: the original formatter can produce multiple lines.
        std::uint8_t option_count_raw() const noexcept {return bytes[208];}
        std::optional<std::uint8_t> argument1_raw(std::size_t index) const noexcept {
            if(index>=message_capacity)return {};return bytes[209+index];
        }
        std::optional<std::uint8_t> argument2_raw(std::size_t index) const noexcept {
            if(index>=message_capacity)return {};return bytes[259+index];
        }
    };
    struct State {
        StateBytes bytes;
        Context context() const noexcept {return get_context(bytes);}
        std::uint8_t state_raw() const noexcept {return bytes[5];}
        bool closes_panel() const noexcept {return state_raw()==4;}
        // BYTE6 is unconsumed by4A0A90 but remains part of logical7.
        std::uint8_t opaque_tail() const noexcept {return bytes[6];}
    };
    static std::optional<Action> decode_action(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=action_size || bytes[0]!=action_opcode)return {};
        // Keep raw widths even outside the proven producer branches. Structural
        // decode is not authority to execute a new operation or chosen index.
        return Action{get_context(bytes),bytes[5],bytes[6]};
    }
    static std::array<std::uint8_t,action_size> encode_action(const Action& action) noexcept {
        return {action_opcode,action.context[0],action.context[1],action.context[2],action.context[3],action.operation,action.selection};
    }
    static std::optional<Close> decode_close(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=close_size || bytes[0]!=close_opcode)return {};return Close{get_context(bytes)};
    }
    static std::array<std::uint8_t,close_size> encode_close(const Close& close) noexcept {
        return {close_opcode,close.context[0],close.context[1],close.context[2],close.context[3]};
    }
    static std::optional<Snapshot> decode_snapshot(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=snapshot_size || bytes[0]!=snapshot_opcode)return {};
        Snapshot result{};std::copy(bytes.begin(),bytes.end(),result.bytes.begin());return result;
    }
    static std::optional<State> decode_state(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=state_size || bytes[0]!=state_opcode)return {};
        State result{};std::copy(bytes.begin(),bytes.end(),result.bytes.begin());return result;
    }
    // Projection only. Native state4 closes before copying its context: the
    // old open context can consequently generate a native9F close record.
    static std::optional<Snapshot> apply_state(Snapshot before,const State& state) noexcept {
        if(state.closes_panel())return {};
        std::copy_n(state.bytes.begin()+1,5,before.bytes.begin()+1);return before;
    }
private:
    static Context get_context(std::span<const std::uint8_t> bytes) noexcept {return {bytes[1],bytes[2],bytes[3],bytes[4]};}
    static std::uint16_t word(std::span<const std::uint8_t> bytes,std::size_t at) noexcept {
        return static_cast<std::uint16_t>(bytes[at]|(std::uint16_t{bytes[at+1]}<<8));
    }
};
}
