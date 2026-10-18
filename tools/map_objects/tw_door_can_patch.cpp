// CUSTOM-0152: custom CityI1 door selector joins using existing Taiwan assets.
// This does not recover an original-server scene join or create a server route.
// Native CAN reader 00444F70 reads 64-byte records followed by u16 indices.
// Native indoor consumer 0050069F..00500747 selects record[index] + 1 as path.
// Offline staging only: no game DB, EXE modification, client write or game launch.
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cwctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace fs = std::filesystem;
using Bytes = std::vector<unsigned char>;
[[noreturn]] static void fail(const std::string& text) { throw std::runtime_error(text); }
static void need(bool value, const std::string& text) { if (!value) fail(text); }
static std::string sha(const Bytes& bytes) {
    BCRYPT_ALG_HANDLE algorithm{};
    need(BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0, "SHA provider");
    struct Close { BCRYPT_ALG_HANDLE value; ~Close() { BCryptCloseAlgorithmProvider(value, 0); } } close{algorithm};
    DWORD size{}, used{};
    need(BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH, reinterpret_cast<PUCHAR>(&size), sizeof(size), &used, 0) >= 0, "SHA object size");
    Bytes object(size), digest(32);
    BCRYPT_HASH_HANDLE hash{};
    need(BCryptCreateHash(algorithm, &hash, object.data(), size, nullptr, 0, 0) >= 0, "SHA create");
    struct Destroy { BCRYPT_HASH_HANDLE value; ~Destroy() { BCryptDestroyHash(value); } } destroy{hash};
    need(bytes.size() <= std::numeric_limits<ULONG>::max(), "SHA input bound");
    need(BCryptHashData(hash, const_cast<PUCHAR>(bytes.data()), static_cast<ULONG>(bytes.size()), 0) >= 0, "SHA input");
    need(BCryptFinishHash(hash, digest.data(), static_cast<ULONG>(digest.size()), 0) >= 0, "SHA finish");
    static constexpr char hex[] = "0123456789abcdef";
    std::string result;
    for (auto byte : digest) { result += hex[byte >> 4]; result += hex[byte & 15]; }
    return result;
}
static std::wstring folded(const fs::path& path) {
    auto result = path.lexically_normal().native();
    std::transform(result.begin(), result.end(), result.begin(), [](wchar_t c) { return std::towlower(c); });
    return result;
}
static bool inside(const fs::path& path, const fs::path& root) {
    auto a = folded(path), b = folded(root);
    return a == b || (a.size() > b.size() && a.compare(0, b.size(), b) == 0 && (a[b.size()] == L'\\' || a[b.size()] == L'/'));
}
static Bytes read(const fs::path& path, std::uintmax_t maximum) {
    need(fs::is_regular_file(path), "Missing source: " + path.generic_string());
    auto size = fs::file_size(path);
    need(size > 0 && size <= maximum, "Source size bound: " + path.generic_string());
    std::ifstream stream(path, std::ios::binary);
    need(bool(stream), "Source open");
    Bytes bytes(static_cast<std::size_t>(size));
    stream.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    need(bool(stream) && stream.peek() == std::char_traits<char>::eof(), "Source changed or short read");
    return bytes;
}
static Bytes source(const fs::path& client, const fs::path& relative, std::uintmax_t maximum) {
    auto resolved = fs::canonical(client / relative);
    need(inside(resolved, client), "Source escaped client subtree");
    return read(resolved, maximum);
}
static void write(const fs::path& path, const Bytes& bytes) {
    fs::create_directories(path.parent_path());
    need(!fs::exists(path), "Staging file already exists");
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    need(bool(stream), "Staging open");
    stream.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    stream.close();
    need(bool(stream) && read(path, 64 * 1024) == bytes, "Staging verification");
}
static std::uint32_t u32(const Bytes& bytes, std::size_t at) {
    need(at <= bytes.size() && bytes.size() - at >= 4, "CAN u32 bounds");
    return std::uint32_t(bytes[at]) | (std::uint32_t(bytes[at + 1]) << 8) |
        (std::uint32_t(bytes[at + 2]) << 16) | (std::uint32_t(bytes[at + 3]) << 24);
}
static std::uint16_t u16(const Bytes& bytes, std::size_t at) {
    need(at <= bytes.size() && bytes.size() - at >= 2, "CAN u16 bounds");
    return static_cast<std::uint16_t>(unsigned(bytes[at]) | (unsigned(bytes[at + 1]) << 8));
}
struct Can {
    std::uint32_t fileCount{}, sceneCount{};
    std::size_t indices{};
    std::vector<std::string> paths;
    std::vector<unsigned char> tags;
};
static Can parse(const Bytes& bytes) {
    need(bytes.size() >= 16 && bytes.size() <= 16 + 256 * 64 + 256 * 2, "CAN length");
    static constexpr std::string_view magic = "CAN v1.0";
    need(std::equal(magic.begin(), magic.end(), bytes.begin()), "CAN magic");
    Can result;
    result.fileCount = u32(bytes, 8);
    need(result.fileCount > 0 && result.fileCount <= 256, "CAN file count");
    auto sceneCountAt = 12 + std::size_t(result.fileCount) * 64;
    result.sceneCount = u32(bytes, sceneCountAt);
    need(result.sceneCount > 0 && result.sceneCount <= 256, "CAN scene count");
    result.indices = sceneCountAt + 4;
    need(bytes.size() == result.indices + 2 * std::size_t(result.sceneCount), "CAN exact length");
    for (std::size_t index = 0; index < result.fileCount; ++index) {
        auto at = 12 + index * 64;
        result.tags.push_back(bytes[at]); // Opaque native tag, not the network kind.
        auto first = bytes.begin() + static_cast<std::ptrdiff_t>(at + 1);
        auto end = bytes.begin() + static_cast<std::ptrdiff_t>(at + 64);
        auto nul = std::find(first, end, 0);
        need(nul != end && nul != first, "CAN NUL-terminated path");
        result.paths.emplace_back(first, nul);
    }
    for (std::size_t scene = 0; scene < result.sceneCount; ++scene)
        need(u16(bytes, result.indices + scene * 2) < result.fileCount, "CAN record index bounds");
    return result;
}
static std::string quote(const std::string& text) {
    std::string result = "\"";
    static constexpr char hex[] = "0123456789abcdef";
    for (unsigned char c : text) {
        if (c == '"' || c == '\\') { result += '\\'; result += char(c); }
        else if (c < 32) { result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15]; }
        else result += char(c);
    }
    return result + '"';
}
struct Join {
    std::uint16_t scene, before, after;
    const char* recordPath;
    const char* sourcePath;
    const char* sourceHash;
    const char* attachment;
};
static constexpr std::string_view canPath = "Data2/map/island01/Island01.can";
static constexpr std::string_view canHash = "f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97";
static constexpr std::array<Join, 3> joins{{
    {10, 1, 34, "indoor\\tp_nor_l.hmd", "Data2/map/island01/indoor/TP_Nor_L.hmdZ", "b5201259f272c6039069d0dbc7f4bc404ae61d59899c508b6e81e913ba24efaa", "..\\indoor\\TP_Nor_L.hmd"},
    {12, 1, 33, "indoor\\tp_nor_r.hmd", "Data2/map/island01/indoor/TP_Nor_R.hmdZ", "cce0a099d4264b73a7db54df6c5ee7d159b52c8f0df4c4966d2f4c37a578ec82", "..\\indoor\\TP_Nor_R.hmd"},
    {22, 17, 29, "indoor\\hotel01.hmd", "Data2/map/island01/indoor/hotel01.hmdZ", "07aa9bf3df4ef93508a175b92f98f8c4cbf4ed6896b8faa6f488fc8e7ca6c184", "..\\indoor\\hotel01.hmd"}
}};
struct Candidate { Bytes before, after; std::string manifest; };
static Candidate prepare(const fs::path& client) {
    Candidate candidate;
    candidate.before = source(client, fs::path(canPath), 64 * 1024);
    need(sha(candidate.before) == canHash, "Pinned Taiwan CAN changed");
    auto original = parse(candidate.before);
    need(candidate.before.size() == 2580 && original.fileCount == 36 && original.sceneCount == 130 && original.indices == 2320, "Pinned CAN shape");
    candidate.after = candidate.before;
    std::array<std::size_t, 3> sourceSizes{};
    std::vector<bool> allowed(candidate.before.size(), false);
    for (std::size_t ordinal = 0; ordinal < joins.size(); ++ordinal) {
        const auto& join = joins[ordinal];
        auto at = original.indices + 2 * std::size_t(join.scene);
        need(u16(candidate.before, at) == join.before, "Pinned previous scene record");
        need(original.paths.at(join.after) == join.recordPath && original.tags.at(join.after) == 1, "Pinned target record path/tag");
        auto hmd = source(client, fs::path(join.sourcePath), 64 * 1024);
        need(sha(hmd) == join.sourceHash, "Pinned Taiwan HMD changed");
        need(hmd.size() >= 7 && hmd[0] == 5 && hmd[1] == 22 && u32(hmd, 2) > 0 && u32(hmd, 2) <= 1024 * 1024, "Pinned HMD compressed header");
        sourceSizes[ordinal] = hmd.size();
        candidate.after[at] = static_cast<unsigned char>(join.after & 255);
        candidate.after[at + 1] = static_cast<unsigned char>(join.after >> 8);
        allowed[at] = allowed[at + 1] = true;
    }
    auto checked = parse(candidate.after);
    need(checked.fileCount == 36 && checked.sceneCount == 130 && checked.indices == original.indices, "Candidate CAN shape");
    need(std::equal(candidate.before.begin(), candidate.before.begin() + static_cast<std::ptrdiff_t>(original.indices), candidate.after.begin()), "CAN header/records changed");
    std::size_t different = 0;
    for (std::size_t at = 0; at < candidate.before.size(); ++at) {
        if (candidate.before[at] != candidate.after[at]) { need(allowed[at], "Unexpected CAN byte change"); ++different; }
    }
    need(different == 3, "Expected three changed low bytes in three WORD fields");
    need(sha(candidate.after) == "73156f4c2060f92e1be59fa9c2df30841b3df204121491a765c1ca21e68796ad", "Pinned CUSTOM-0152 candidate hash");
    for (std::size_t scene = 0; scene < original.sceneCount; ++scene) {
        auto found = std::find_if(joins.begin(), joins.end(), [scene](const auto& join) { return join.scene == scene; });
        auto expected = found == joins.end() ? u16(candidate.before, original.indices + 2 * scene) : found->after;
        need(u16(candidate.after, checked.indices + 2 * scene) == expected, "Candidate scene index mismatch");
    }
    std::ostringstream manifest;
    manifest << "{\n  \"schema\":\"god2-tw-town-door-can-staging/1\",\"designId\":\"CUSTOM-0152\",\n"
        << "  \"origin\":\"CUSTOM_SCENE_JOINS_USING_EXISTING_PINNED_TW_CAN_RECORDS_AND_MDL_ATTACHMENT_EVIDENCE\",\n"
        << "  \"originalServerJoinRecovered\":false,\"nativeAcceptance\":\"NOT_RUN\",\"serverRoutesInstalled\":false,\n"
        << "  \"attachmentEvidence\":{\"source\":\"ORIGINAL_TW_CITYI1_MDL_BASELINE\",\"sourceSHA256\":\"bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618\",\"decodedSHA256\":\"59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef\",\"placementOffsets\":[35492,36598,39351],\"previouslyQualifiedReadOnly\":true,\"readByThisTool\":false},\n"
        << "  \"sourceClientModified\":false,\"databaseModified\":false,\"executableModified\":false,\n"
        << "  \"path\":" << quote(std::string(canPath)) << ",\"oldSHA256\":" << quote(sha(candidate.before)) << ",\"newSHA256\":" << quote(sha(candidate.after)) << ",\n"
        << "  \"oldBytes\":2580,\"newBytes\":2580,\"fileCount\":36,\"sceneCount\":130,\"originalRecordsByteExact\":true,\n"
        << "  \"indexFieldBytes\":6,\"actualChangedBytes\":" << different << ",\"otherSceneIndicesByteExact\":true,\"scene28Unchanged\":true,\n"
        << "  \"recordTagMeaning\":\"OPAQUE_NATIVE_BYTE_NOT_NETWORK_KIND\",\"joins\":[\n";
    for (std::size_t ordinal = 0; ordinal < joins.size(); ++ordinal) {
        const auto& join = joins[ordinal];
        if (ordinal) manifest << ",\n";
        manifest << "    {\"scene\":" << join.scene << ",\"oldRecord\":" << join.before << ",\"newRecord\":" << join.after
            << ",\"indexOffset\":" << original.indices + 2 * std::size_t(join.scene) << ",\"indexBytes\":2,\"actualChangedBytes\":1"
            << ",\"recordPath\":" << quote(join.recordPath) << ",\"recordTag\":1,\"recordBytesPreserved\":true"
            << ",\"sourceHMD\":" << quote(join.sourcePath) << ",\"sourceHMDSHA256\":" << quote(join.sourceHash)
            << ",\"sourceHMDBytes\":" << sourceSizes[ordinal] << ",\"originalMDLAttachment\":" << quote(join.attachment) << "}";
    }
    manifest << "\n  ]\n}\n";
    candidate.manifest = manifest.str();
    return candidate;
}
int wmain(int argc, wchar_t** argv) {
    fs::path pending;
    bool pendingOwned = false;
    try {
        fs::path client, output;
        bool clientSeen = false, outputSeen = false;
        for (int index = 1; index < argc; ++index) {
            std::wstring option = argv[index];
            if (option == L"--client-root" && index + 1 < argc && !clientSeen) { client = argv[++index]; clientSeen = true; }
            else if (option == L"--output-root" && index + 1 < argc && !outputSeen) { output = argv[++index]; outputSeen = true; }
            else fail("Usage: god2-tw-town-door-can --client-root ABSOLUTE --output-root ABSOLUTE_NEW_STAGING");
        }
        need(clientSeen && outputSeen && client.is_absolute() && output.is_absolute(), "Both roots must be absolute");
        client = fs::canonical(client);
        need(fs::is_directory(client) && fs::is_directory(output.parent_path()), "Existing client/output parent required");
        need(!output.filename().empty() && output.filename() != L"." && output.filename() != L"..", "Output directory name");
        output = fs::canonical(output.parent_path()) / output.filename();
        need(!inside(output, client) && !inside(client, output) && !fs::exists(output), "Output must be new staging outside client");
        auto candidate = prepare(client); // Validate the entire candidate and all source pins before any output.
        need(source(client, fs::path(canPath), 64 * 1024) == candidate.before, "CAN changed during candidate preparation");
        for (const auto& join : joins) need(sha(source(client, fs::path(join.sourcePath), 64 * 1024)) == join.sourceHash, "HMD changed during candidate preparation");
        pending = output;
        pending += L".pending-" + std::to_wstring(GetCurrentProcessId());
        need(!inside(pending, client) && !fs::exists(pending), "Staging temporary path rejected");
        need(fs::create_directory(pending), "Create staging temporary root");
        pendingOwned = true;
        write(pending / fs::path(canPath), candidate.after);
        write(pending / "manifest.json", Bytes(candidate.manifest.begin(), candidate.manifest.end()));
        fs::rename(pending, output);
        pendingOwned = false;
        std::cout << "Prepared one CAN: 3 scene WORD fields / 3 actual changed bytes. Native acceptance NOT RUN; server routes not installed.\n";
        return 0;
    } catch (const std::exception& error) {
        // Only the freshly created, external, tool-owned pending subtree is removed.
        if (pendingOwned && !pending.empty() && fs::exists(pending)) { std::error_code ignored; fs::remove_all(pending, ignored); }
        std::cerr << "No successful staging publication: " << error.what() << '\n';
        return 1;
    }
}
