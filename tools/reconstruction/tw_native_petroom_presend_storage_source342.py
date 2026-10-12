from pathlib import Path
import json,hashlib
S=Path('C:/Users/risei/Desktop/God2/God2-Server')
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
D=A/'round342-petroom-presend-storage-implementation'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,indent=2)+'\n').encode())
for name in ['tw-native-petroom-presend-context-source-342','tw-native-petegg-selected-child-source-342']:
    root=A/name
    for r in json.loads((root/'seal.json').read_bytes())['members']:
        p=root/r['path']
        if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Outside root')
        b=p.read_bytes()
        if len(b)!=r['bytes'] or sha(b)!=r['sha256']:raise ValueError('Upstream differs')
header='''#pragma once
#include <array>
#include <cstdint>
#include <optional>

namespace god2 {
// Historical TW149c source, actual zero-input49B820 -> selected4B5BE0 ->
// same-U4BC2E0/4BC2A0. Descriptions only; no native addresses are dereferenced.
struct RecoveredPetRoomPresendStorageSource {
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    static constexpr char source_image_sha256[]=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr char source_original_pe_sha256[]=
        "5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde";
    static constexpr char qualification[]="CONDITIONAL_SELECTED_CLIENT_ABSOLUTE_WRITE_SOURCE";
    static constexpr char required_entry[]=
        "Actual selected callers4D69AC/4DA73F/4DC891 pass six zero DWORDs "
        "and canonical U=Main+A7F2F6C to49B820; its arguments to4B5BE0 are "
        "(0,0,12h,0,0,0). Only this selected path is described; whole large "
        "4B5BE0, other callers and its nonzero-input branches are not qualified";
    static constexpr char required_storage_and_stage[]=
        "Valid fault-free ordinary native storage, actual same U, correct "
        "calling frame; opaque547B50 establishes1184h frame and preserves "
        "arguments, returns normally; REP string direction/state valid; "
        "no unmodeled register/storage interference along selected instructions. "
        "live_handle is the actual signed WORD read at4BC2A0 after wrapper "
        "store; that global FFFF is stable until the child's comparison. "
        "Actual native context/operands and these premises are unobserved";
    static constexpr char scope_limit[]=
        "Absolute global storage semantics remain unknown: no pending request, "
        "request ID, issued lease, ownership, B1/F4 causality or server rule. "
        "Opaque505230 effects remain open; its normal-return overwrite is a "
        "separate event, not a final-state or U8/inventory preservation claim. "
        "No native pointer, UI API, inventory, packet or SQL mutation occurs";
    enum class NativeWidth : std::uint8_t { word=2,dword=4 };
    struct AbsoluteWriteSource {
        std::uint32_t source_instruction_va,absolute_storage_va;
        NativeWidth width;
        std::uint32_t value;
        bool operator==(const AbsoluteWriteSource&) const=default;
    };
    struct OpaqueUiCallSource {
        std::uint32_t source_instruction_va,target_va;
        std::int64_t canonical_U_context_offset;
        std::uint32_t pushed_DWORD_argument;
        // Applicable only after opaque505230 returns normally.
        AbsoluteWriteSource direct_write_after_normal_return;
        bool operator==(const OpaqueUiCallSource&) const=default;
    };
    struct SelectedProjection {
        std::array<AbsoluteWriteSource,10> ordered_direct_writes_before_ui_call;
        std::optional<OpaqueUiCallSource> delegated_ui_call;
        bool operator==(const SelectedProjection&) const=default;
    };
    static constexpr std::optional<SelectedProjection> project_selected_zero_prefix(
        const std::array<std::uint32_t,6>& incoming_formals,
        std::int16_t live_handle_at_child_read) noexcept {
        // A strict source-domain restriction, not a native all-caller guard.
        for(const auto value:incoming_formals)if(value!=0)return {};
        SelectedProjection result{};
        result.ordered_direct_writes_before_ui_call={{
            {0x004b5c11u,0x005926b0u,NativeWidth::word,0x0012u},
            {0x004bc0dau,0x005b7838u,NativeWidth::dword,0u},
            {0x004bc0e0u,0x005926b2u,NativeWidth::word,0xffffu},
            {0x004bc0e6u,0x005b783cu,NativeWidth::dword,0u},
            {0x004bc0ecu,0x005926b4u,NativeWidth::word,0xffffu},
            {0x004bc0f2u,0x005b7840u,NativeWidth::dword,0u},
            {0x004bc0f8u,0x005b7830u,NativeWidth::word,0u},
            {0x004bc101u,0x005b7844u,NativeWidth::dword,0u},
            {0x004bc107u,0x005b7848u,NativeWidth::dword,0u},
            {0x004bc2e2u,0x005926b0u,NativeWidth::word,0xffffu}
        }};
        // Wrapper supplies -1 and stores FFFF; under the explicit stable-read
        // premise the child's comparison matches. Signed handle<0 returns.
        if(live_handle_at_child_read>=0) {
            // Composed path OR EAX,FFFFFFFF at4BC0D7 has no intervening call
            // before wrapper; wrapper/child preserve upper16 until PUSH EAX.
            // Generic4BC2A0 alone does not initialize that upper16.
            const auto low_word=static_cast<std::uint16_t>(live_handle_at_child_read);
            result.delegated_ui_call=OpaqueUiCallSource{
                0x004bc2c6u,0x00505230u,0xe2170,
                0xffff0000u|static_cast<std::uint32_t>(low_word),
                {0x004bc2cbu,0x005926b0u,NativeWidth::word,0xffffu}
            };
        }
        return result;
    }
};
}
'''
b=header.encode();target=S/'src/protocol/RecoveredPetRoomPresendStorageSource.h'
if target.exists() or D.exists():raise ValueError('Exclusive outputs exist')
D.mkdir();write(target,b);write(D/target.name,b)
write(D/'generate-presend-storage342.py',Path(__file__).read_bytes())
js(D/'source-manifest.json',dict(actual_path=target.as_posix(),bytes=len(b),sha256=sha(b),existed_before=False,
    native_pointer_or_API_or_SQL_execution=False,source_generation_only=True))
write(D/'REPORT.md',b'# Round342 selected presend storage C++ source\n\nStandalone source description retains ten ordered absolute writes before optional opaque UI call. Selected six-zero incoming formals, exact adapter argument mapping, opaque stack-frame/direction/ordinary storage conditions and same-U stage premises are explicit. The composed path supplies FFFF upper EAX before live WORD replacement; generic child alone does not. Optional post-call WORD overwrite is conditional on normal return and distinct from final state. No authoritative gameplay supplier or runtime call is added; old C++/catalog/importers unchanged. Header was generated as text only, never compiled or executed.\n')
rows=[]
for p in sorted(D.rglob('*')):
    if p.is_file():
        raw=p.read_bytes();rows.append(dict(path=p.relative_to(D).as_posix(),bytes=len(raw),sha256=sha(raw)))
js(D/'seal.json',dict(members=rows,member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows)))
print(json.dumps(dict(header_bytes=len(b),header_sha256=sha(b),members=len(rows),member_bytes=sum(r['bytes'] for r in rows),seal_sha256=sha((D/'seal.json').read_bytes()))))
