#include <windows.h>
#include <dbgeng.h>
#include <bcrypt.h>
#include <nlohmann/json.hpp>
#include <algorithm>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <string>
#include "packet_codec.h"
#include "brute_candidate_engine.h"

extern "C" __declspec(dllexport) int __cdecl God2DecodePacket(
    const unsigned char* wire,unsigned length,const unsigned char* key,unsigned key_length,
    unsigned feedback,unsigned char* plain,unsigned capacity) {
    if(!wire || !key || !plain) return -6;
    if(length<4 || length>god2_probe::max_frame) return -1;
    if(key_length!=256 || feedback>255) return -2;
    if(capacity<length) return -6;
    const auto decoded=god2_probe::decode({wire,length},{key,key_length},feedback);
    if(decoded.status>0) std::copy_n(decoded.plain.begin(),length,plain);
    return decoded.status;
}

// Recovered inverse at VA0x410690; framing/checksum must already be valid.
extern "C" __declspec(dllexport) int __cdecl God2EncodePacket(
    const unsigned char* plain,unsigned length,const unsigned char* key,unsigned key_length,
    unsigned feedback,unsigned char* wire,unsigned capacity) {
    if(!plain || !key || !wire) return -6;
    if(length<4 || length>god2_probe::max_frame) return -1;
    if(key_length!=256 || feedback>255) return -2;
    if(capacity<length) return -6;
    const unsigned declared=plain[0]+256U*plain[1];
    if(declared&0x8000U) return -3;
    if(declared!=length) return -4;
    unsigned checksum=0;
    for(unsigned i=0;i<length-1;++i) checksum+=plain[i]+0x3c;
    if((checksum&255)!=plain[length-1]) return -5;
    std::array<unsigned char,god2_probe::max_frame> encoded{};
    encoded[0]=plain[0];encoded[1]=plain[1];
    for(unsigned i=2;i<length;++i) {
        encoded[i]=static_cast<unsigned char>((plain[i]^key[i-2])+feedback-3);
        feedback=plain[i];
    }
    std::copy_n(encoded.begin(),length,wire);
    return static_cast<int>(length);
}

namespace {
std::string hex_bytes(std::span<const std::uint8_t> bytes) {
    constexpr char digits[]="0123456789abcdef";
    std::string result;result.reserve(bytes.size()*2);
    for(auto byte:bytes) { result+=digits[byte>>4];result+=digits[byte&15]; }
    return result;
}
int json_result(const nlohmann::json& value,char* output,unsigned capacity) {
    const auto report=value.dump();
    const auto required=static_cast<unsigned>(report.size()+1);
    if(output && capacity>=required) std::copy_n(report.c_str(),required,output);
    return static_cast<int>(required);
}
std::string key_id(std::span<const std::uint8_t> key) {
    BCRYPT_ALG_HANDLE provider=nullptr;
    if(BCryptOpenAlgorithmProvider(&provider,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)
        throw std::runtime_error("SHA256 provider unavailable");
    std::array<std::uint8_t,32> digest{};
    const auto status=BCryptHash(provider,nullptr,0,const_cast<PUCHAR>(key.data()),
        static_cast<ULONG>(key.size()),digest.data(),static_cast<ULONG>(digest.size()));
    BCryptCloseAlgorithmProvider(provider,0);
    if(status<0) throw std::runtime_error("key identity hash failed");
    return hex_bytes(digest);
}
void save_new(const std::filesystem::path& path,std::span<const std::uint8_t> bytes) {
    const auto file=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,
        FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE) throw std::runtime_error("cannot create new packet evidence");
    DWORD written=0;
    const bool ok=WriteFile(file,bytes.data(),static_cast<DWORD>(bytes.size()),&written,nullptr)!=FALSE;
    CloseHandle(file);
    if(!ok || written!=bytes.size()) throw std::runtime_error("incomplete packet evidence write");
}
}

// Returns required JSON buffer size including NUL; insufficient buffers are untouched.
extern "C" __declspec(dllexport) int __cdecl God2BrutePacket(
    const unsigned char* wire,unsigned length,const unsigned char* key,unsigned key_length,
    char* output,unsigned capacity) {
    if(!wire || !key || (!output && capacity)) return -6;
    if(length<4 || length>god2_probe::max_frame) return -1;
    if(key_length!=256) return -2;
    try {
        return json_result({{"status","RECOVERY_MANIFEST_REQUIRED"},{"tested",0},
            {"verified",false},{"CRYPTO_RECOVERED",false},
            {"reason","Use --recover-crypto with session-global multi-packet constraints"}},output,capacity);
    } catch(...) { return -7; }
}

extern "C" __declspec(dllexport) int __cdecl God2RecoverCrypto(
    const char* request,char* output,unsigned capacity) {
    if(!request || (!output && capacity)) return -6;
    try {
        // Bounded request parsing; never echo key material or input in an error.
        const auto size=strnlen_s(request,1024*1024+1);
        if(size>1024*1024) return -1;
        const auto parsed=nlohmann::json::parse(request,request+size);
        return json_result(god2_probe::recover_candidates(parsed),output,capacity);
    } catch(...) { return -7; }
}

// Debugger-host command only. ReadVirtual is the sole target-memory operation.
static HRESULT packet_command(PDEBUG_CLIENT client,PCSTR args,bool brute) {
    IDebugControl* control=nullptr;IDebugDataSpaces* memory=nullptr;
    IDebugSystemObjects* systems=nullptr;
    HRESULT hr=client->QueryInterface(__uuidof(IDebugControl),reinterpret_cast<void**>(&control));
    if(FAILED(hr)) return hr;
    nlohmann::json report={{"event_type","PACKET_DECODE"},{"decoded",false}};
    try {
        if(brute) throw std::runtime_error("Per-packet brute disabled; use --recover-crypto session manifest");
        std::istringstream input(args?args:"");
        std::array<std::string,3> tokens;std::string extra,base;
        if(!(input>>tokens[0]>>tokens[1]>>tokens[2]))
            throw std::runtime_error("usage: !God2Probe.packet wire_address length codec_address [\"output_base\"]");
        input>>std::ws;
        if(!input.eof() && (!(input>>std::quoted(base)) || (input>>extra)))
            throw std::runtime_error("invalid output base argument");
        std::array<ULONG64,3> values{};
        for(unsigned i=0;i<3;++i) {
            DEBUG_VALUE value{};ULONG remainder=0;
            if(FAILED(control->Evaluate(tokens[i].c_str(),DEBUG_VALUE_INT64,&value,&remainder)) || remainder!=tokens[i].size())
                throw std::runtime_error("invalid address/length expression");
            values[i]=value.I64;
        }
        const auto wire_address=values[0],length=values[1],codec=values[2];
        ULONG machine=0;
        if(FAILED(control->GetEffectiveProcessorType(&machine)) || machine!=IMAGE_FILE_MACHINE_I386)
            throw std::runtime_error("x86 effective target context required");
        if(length<4 || length>god2_probe::max_frame || wire_address==0 ||
           wire_address>0xffffffffULL-length || codec==0 || codec>0xffffffffULL-0x255c)
            throw std::runtime_error("unsupported frame size or x86 address");
        if(FAILED(client->QueryInterface(__uuidof(IDebugDataSpaces),reinterpret_cast<void**>(&memory))) ||
           FAILED(client->QueryInterface(__uuidof(IDebugSystemObjects),reinterpret_cast<void**>(&systems))))
            throw std::runtime_error("debugger read interfaces unavailable");
        auto read=[&](ULONG64 address,void* destination,ULONG count) {
            ULONG actual=0;
            if(FAILED(memory->ReadVirtual(address,destination,count,&actual)) || actual!=count)
                throw std::runtime_error("incomplete target-memory read");
        };
        std::array<std::uint8_t,god2_probe::max_frame> wire{};
        std::array<std::uint8_t,256> key{};std::uint8_t feedback=0;ULONG enabled=0,socket=0;
        read(wire_address,wire.data(),static_cast<ULONG>(length));
        read(codec+0x2420,key.data(),256);read(codec+0x2556,&feedback,1);
        read(codec+8,&enabled,4);
        read(codec+0x2558,&socket,4);
        if(!enabled) throw std::runtime_error("codec cipher disabled; not an encrypted-frame observation");
        const auto decoded=god2_probe::decode({wire.data(),static_cast<std::size_t>(length)},key,feedback);
        ULONG pid=0,tid=0;
        systems->GetCurrentProcessSystemId(&pid);systems->GetCurrentThreadSystemId(&tid);
        report.update({{"pid",pid},{"tid",tid},{"wire_address",wire_address},{"codec_address",codec},
                       {"length",length},{"status",decoded.status},{"key_source","target codec+0x2420"},
                       {"feedback_source","target codec+0x2556"},{"checksum_valid",decoded.status>0},
                       {"crypto_key_id",key_id(key)},{"wire_len",length},
                       {"key_offset_before",0},{"key_offset_after",0},
                       {"feedback_before",feedback},{"feedback_after",feedback},
                       {"cipher_enabled",true},{"crypto_model","packet_reset"},{"socket",socket},
                       {"state_update_qualification","STATIC_INSTRUCTION_PROVEN; no fresh runtime qualification"},
                       {"CRYPTO_RECOVERED",false},{"brute_force_used",false}});
        if(!base.empty()) {
            save_new(std::filesystem::u8path(base+".wire.bin"),{wire.data(),static_cast<std::size_t>(length)});
            report["wire_file"]=base+".wire.bin";
        }
        if(decoded.status<=0) throw std::runtime_error("frame/transform/checksum rejected; no plaintext published");
        const bool sensitive=length==176;
        report["decoded"]=true;report["opcode"]=decoded.plain[2];
        report["payload_length"]=length-4;report["checksum"]=decoded.plain[length-1];
        report["plaintext_redacted"]=sensitive;
        report["plain_len"]=length;
        if(!base.empty()) {
            save_new(std::filesystem::u8path(base+".plain.bin"),{decoded.plain.data(),static_cast<std::size_t>(length)});
            report["plain_file"]=base+".plain.bin";
        }
        report["wire_hex"]=hex_bytes({wire.data(),static_cast<std::size_t>(length)});
        report["plain_frame_hex"]=sensitive?"REDACTED_CREDENTIAL_FRAME":hex_bytes({decoded.plain.data(),static_cast<std::size_t>(length)});
        hr=S_OK;
    } catch(const std::exception& error) { report["error"]=error.what();hr=E_FAIL; }
    control->Output(DEBUG_OUTPUT_NORMAL,"GOD2_PACKET %s\n",report.dump().c_str());
    if(systems) systems->Release();if(memory) memory->Release();control->Release();
    return hr;
}

extern "C" __declspec(dllexport) HRESULT CALLBACK packet(PDEBUG_CLIENT client,PCSTR args) {
    return packet_command(client,args,false);
}
extern "C" __declspec(dllexport) HRESULT CALLBACK brute(PDEBUG_CLIENT client,PCSTR args) {
    return packet_command(client,args,true);
}
