from pathlib import Path
import hashlib,json
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round341-petegg-local-counter-source-implementation')
PRIOR=OUT.parent/'tw-native-petroom-action-context-source-341'
sha=lambda b:hashlib.sha256(b).hexdigest()
sealbytes=(PRIOR/'seal.json').read_bytes()
assert sha(sealbytes)=='d332146cfe45293f0231480c00f182e27b17ad55bef78c3b8df7092cc82fa018'
seal=json.loads(sealbytes);verified=[]
for member in seal['members']:
    raw=(PRIOR/member['path']).read_bytes();assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
    verified.append(dict(path=member['path'],bytes=len(raw),sha256=sha(raw)))
assert len(verified)==seal['member_count'] and sum(m['bytes'] for m in verified)==seal['retained_member_bytes']
(OUT/'upstream-individual-verification.json').write_text(json.dumps(dict(package=str(PRIOR),seal_sha256=sha(sealbytes),member_count=len(verified),total_member_bytes=sum(m['bytes'] for m in verified),members=verified),indent=2)+'\n',encoding='utf8',newline='\n')
code='''#pragma once
#include <array>
#include <cstdint>
#include <optional>

namespace god2 {
// Pinned TW149c client4D7230, selected4D76E0..4D773A direct local writes.
// This is staged source arithmetic, not a server timer/Lua rule, native S2C
// issuer, gameplay mutation, current item observation or ownership predicate.
struct RecoveredPetEggLocalCounterSource {
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    static constexpr char source_image_sha256[]=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr char source_original_pe_sha256[]=
        "5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde";
    static constexpr char qualification[]="CONDITIONAL_CLIENT_DIRECT_LOCAL_WRITE_SOURCE";
    static constexpr char required_entry[]=
        "Actual same U=Main+A7F2F6C reaches4D76E0 in full4D7230 after its "
        "earlier live-row and opaque-child paths; no fault and valid native storage; "
        "these earlier conditions and current native context are not observed";
    static constexpr char required_stage_operands[]=
        "Each input is captured at its actual native read/call stage: WORDA6D4; "
        "first timeGetTime result then current DWORD8C; first live DWORD4C; "
        "second timeGetTime result then re-read live DWORD4C before storing8C; "
        "signed live BYTE8 re-read after storing8C; same U throughout, valid "
        "fault-free calls/reads/writes, no unmodeled modification between each "
        "specified read and its direct write; opaque effects between stages are "
        "represented by fresh operands, not assumed absent";
    static constexpr char scope_limit[]=
        "Only the three ordered direct DWORD writes are projected; no clock "
        "monotonicity, real elapsed time, stable whole-record snapshot, post-child "
        "final state, native allocation/padding, request lease or server rule "
        "is supplied; no actual native pointer, API or inventory write occurs";
    static constexpr std::uint32_t low18_mask=0x0003ffffu;
    static constexpr std::uint32_t native_gate_threshold=60000u;
    static constexpr std::uint32_t native_addend=60u;
    struct NativeStageOperands {
        std::uint16_t gate_word_a6d4;
        std::uint32_t first_clock_result,current_dword8c;
        std::uint32_t first_live_dword4c;
        std::uint32_t second_clock_result,second_live_dword4c;
        std::int8_t second_live_signed_byte8;
    };
    struct DirectDwordWrite {
        std::uint32_t source_instruction_va;
        std::int64_t object_relative_offset; // mathematical offset, no pointer arithmetic
        std::uint32_t value;
        bool operator==(const DirectDwordWrite&) const=default;
    };
    struct DirectWriteProjection {
        std::uint32_t native_difference_after_cdq_xor_sub;
        std::array<DirectDwordWrite,3> ordered_direct_writes;
        bool operator==(const DirectWriteProjection&) const=default;
    };
    // EAX=(clock-current8C) mod2^32; CDQ gives allones iff EAX bit31 is set.
    // XOR/SUB are also mod2^32. In particular80000000h remains80000000h;
    // no signed overflow, std::abs(INT_MIN) or monotonic-clock assumption.
    static constexpr std::uint32_t native_difference(
        std::uint32_t first_clock_result,std::uint32_t current_dword8c) noexcept {
        const std::uint32_t delta=first_clock_result-current_dword8c;
        const std::uint32_t cdq_mask=0u-(delta>>31u);
        return (delta^cdq_mask)-cdq_mask;
    }
    static constexpr std::optional<DirectWriteProjection> project(
        const NativeStageOperands& input) noexcept {
        // Exact WORD gate4D76E0 and unsigned CMP/JB gate4D7701/7706.
        if(input.gate_word_a6d4!=0)return {};
        const auto difference=native_difference(input.first_clock_result,input.current_dword8c);
        if(difference<native_gate_threshold)return {};
        // Native LEA/XOR/AND/XOR changes low18 only. Keep this first write
        // independent of the live4C re-read after the second opaque clock call.
        const std::uint32_t first_sum=input.first_live_dword4c+native_addend;
        const std::uint32_t first_write=
            ((first_sum^input.first_live_dword4c)&low18_mask)^input.first_live_dword4c;
        // MOVSX BYTE8 and LEA*3 then addressing*8: preserve every signedBYTE
        // value, including negative/outside ordinary bag slots. No new guard.
        const std::int64_t row_offset=0x85618+
            24*static_cast<std::int64_t>(input.second_live_signed_byte8);
        DirectWriteProjection result{};
        result.native_difference_after_cdq_xor_sub=difference;
        result.ordered_direct_writes[0]={0x004d7718u,0x4c,first_write};
        result.ordered_direct_writes[1]={0x004d7720u,0x8c,input.second_clock_result};
        // The row is24 bytes; +85618 is row+8/full20-relative+4. This value
        // comes from second_live4C, not first_write or the entry selected row.
        result.ordered_direct_writes[2]={0x004d7733u,row_offset,
                                       input.second_live_dword4c&low18_mask};
        return result;
    }
};
}
'''
path=ROOT/'src/protocol/RecoveredPetEggLocalCounterSource.h'
assert not path.exists()
path.write_text(code,encoding='utf8',newline='\n')
raw=path.read_bytes();assert raw==code.encode()
(OUT/'RecoveredPetEggLocalCounterSource.h').write_bytes(raw)
(OUT/'source-manifest.json').write_text(json.dumps(dict(path=str(path),existed_before=False,bytes=len(raw),sha256=sha(raw),generator='generate_local_counter_source341.py',scope='New standalone header only; no product/API/SQL/native/CRT/codec/compilation/tests execution'),indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(bytes=len(raw),sha256=sha(raw),upstream_members=len(verified),upstream_total=sum(m['bytes'] for m in verified))))
