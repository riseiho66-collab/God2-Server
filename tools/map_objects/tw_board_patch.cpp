// CUSTOM-0151: fixed map decoration reconstructed from pinned Taiwan resources.
// This is NOT a recovered server NPC spawn, coordinate table or collision rule.
// Offline staging only; never opens a game DB or modifies the source client.
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <cwctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace fs = std::filesystem;
using Bytes = std::vector<unsigned char>;
[[noreturn]] static void fail(const std::string& s) { throw std::runtime_error(s); }
static void need(bool b, const std::string& s) { if (!b) fail(s); }
static std::string sha(const Bytes& b) {
    BCRYPT_ALG_HANDLE a{}; BCRYPT_HASH_HANDLE h{};
    need(BCryptOpenAlgorithmProvider(&a, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0, "SHA provider");
    struct Close { BCRYPT_ALG_HANDLE a; ~Close() { BCryptCloseAlgorithmProvider(a, 0); } } close{a};
    DWORD size{}, used{};
    need(BCryptGetProperty(a, BCRYPT_OBJECT_LENGTH, reinterpret_cast<PUCHAR>(&size), sizeof(size), &used, 0) >= 0, "SHA size");
    Bytes object(size), digest(32);
    need(BCryptCreateHash(a, &h, object.data(), size, nullptr, 0, 0) >= 0, "SHA create");
    struct Destroy { BCRYPT_HASH_HANDLE h; ~Destroy() { BCryptDestroyHash(h); } } destroy{h};
    need(b.size() <= std::numeric_limits<ULONG>::max(), "SHA input size");
    need(BCryptHashData(h, const_cast<PUCHAR>(b.data()), static_cast<ULONG>(b.size()), 0) >= 0, "SHA input");
    need(BCryptFinishHash(h, digest.data(), 32, 0) >= 0, "SHA finish");
    static constexpr char hex[] = "0123456789abcdef";
    std::string s; for (auto c : digest) { s += hex[c >> 4]; s += hex[c & 15]; } return s;
}
static Bytes read(const fs::path& p) {
    need(fs::is_regular_file(p) && fs::file_size(p) <= 64 * 1024 * 1024, "Missing/oversize source: " + p.generic_string());
    std::ifstream f(p, std::ios::binary); need(bool(f), "Source open");
    Bytes b(static_cast<std::size_t>(fs::file_size(p)));
    f.read(reinterpret_cast<char*>(b.data()), static_cast<std::streamsize>(b.size()));
    need(bool(f), "Source short read"); return b;
}
static void write(const fs::path& p, const Bytes& b) {
    fs::create_directories(p.parent_path()); std::ofstream f(p, std::ios::binary | std::ios::trunc);
    need(bool(f), "Staging open"); f.write(reinterpret_cast<const char*>(b.data()), static_cast<std::streamsize>(b.size()));
    f.close(); need(bool(f), "Staging write"); need(sha(read(p)) == sha(b), "Staging verify");
}
static std::uint32_t little(const Bytes& b, std::size_t i) {
    return std::uint32_t(b.at(i)) | (std::uint32_t(b.at(i+1)) << 8) | (std::uint32_t(b.at(i+2)) << 16) | (std::uint32_t(b.at(i+3)) << 24);
}
static Bytes decode(const Bytes& b) {
    need(b.size() >= 7 && b[0] == 5 && b[1] == 22, "Native 0516 header");
    auto declared = little(b, 2); need(declared && declared <= 8 * 1024 * 1024, "Decoded size bound");
    Bytes out; out.reserve(declared); std::array<unsigned char,4096> ring{}; ring.fill(32);
    std::array<bool,4096> valid{}; std::fill_n(valid.begin(), 0xfee, true);
    std::size_t pos=7, cursor=0xfee; unsigned flags=0;
    auto put = [&](unsigned char c) { need(out.size() < declared, "LZSS overflow"); out.push_back(c); ring[cursor]=c; valid[cursor]=true; cursor=(cursor+1)&4095; };
    while (pos < b.size()) {
        flags >>= 1; if (!(flags & 0x100)) flags = unsigned(b[pos++]) | 0xff00;
        if (flags & 1) { if (pos == b.size()) break; put(b[pos++]); }
        else {
            need(pos+2 <= b.size(), "LZSS pair truncated"); auto low=b[pos++]; auto high=b[pos++];
            unsigned offset=low|((high&0xf0)<<4);
            for (unsigned n=0; n<unsigned(high&15)+3; ++n) { auto i=(offset+n)&4095; need(valid[i], "LZSS uninitialized dictionary"); put(ring[i]); }
        }
    }
    need(out.size() == declared, "LZSS size mismatch"); return out;
}
static Bytes encode(const Bytes& b, unsigned char originalHeader6) {
    need(b.size() <= UINT32_MAX, "Encode size"); Bytes out{5,22}; auto n=static_cast<std::uint32_t>(b.size());
    for (int i=0;i<4;++i) out.push_back(static_cast<unsigned char>(n>>(i*8)));
    out.push_back(originalHeader6); // Unknown source header field is preserved, not invented.
    for (std::size_t i=0;i<b.size();) { out.push_back(255); for (int j=0;j<8 && i<b.size();++j) out.push_back(b[i++]); }
    need(decode(out)==b, "Literal-only 0516 roundtrip"); return out;
}
struct Line { std::string body, ending; };
static std::vector<Line> split(const Bytes& b) {
    std::vector<Line> out; std::string text(b.begin(),b.end()); std::size_t at=0;
    while (at<text.size()) { auto end=text.find('\n',at); if(end==std::string::npos){out.push_back({text.substr(at),""});break;}
        auto len=end-at; bool cr=len && text[end-1]=='\r'; out.push_back({text.substr(at,len-(cr?1:0)),cr?"\r\n":"\n"}); at=end+1; }
    need(!out.empty(), "Empty MDL"); return out;
}
static std::vector<std::string> tokens(std::string_view s) {
    std::istringstream in{std::string(s)}; std::vector<std::string> out; std::string v; while(in>>v) out.push_back(v); return out;
}
static int integer(const std::string& s) {
    int n{}; auto r=std::from_chars(s.data(),s.data()+s.size(),n); need(r.ec==std::errc{} && r.ptr==s.data()+s.size(), "MDL integer"); return n;
}
static std::vector<int> ints(const std::string& s, std::size_t count) {
    auto t=tokens(s); need(t.size()==count,"MDL field count"); std::vector<int> n; for(auto& v:t)n.push_back(integer(v)); return n;
}
static int countAt(const std::vector<Line>& l,std::size_t at,const std::string& label) {
    auto t=tokens(l.at(at).body); need(t.size()==2 && t[0]==label,"MDL section "+label); int n=integer(t[1]); need(n>=0 && n<=100000,"MDL count bound");return n;
}
struct Tile { int type,width,height,rom,action; };
struct Model { std::array<std::array<int,3>,3> layer; };
struct Block { int x,y,count; std::size_t line,end; };
struct Place { std::size_t line,block; std::array<int,9> f; int palette; };
struct Mdl {
    std::vector<Line> lines; std::vector<std::string> refs; std::vector<Tile> tiles; std::vector<Model> models;
    std::vector<Block> blocks; std::vector<Place> places; std::size_t romLine{},tileLine{},modelLine{},placementLine{};
};
static Mdl parse(const Bytes& b) {
    Mdl m; m.lines=split(b); auto& l=m.lines; need(l[0].body=="MDL v1.6","MDL version"); std::size_t at=1;
    m.romLine=at; int rc=countAt(l,at++,"ROMFILE"); for(int i=0;i<rc;++i) m.refs.push_back(l.at(at++).body);
    m.tileLine=at; int tc=countAt(l,at++,"TileModel"); for(int i=0;i<tc;++i) {
        auto t=tokens(l.at(at++).body); need(t.size()==6,"MDL tile shape");
        Tile v{integer(t[1]),integer(t[2]),integer(t[3]),integer(t[4]),integer(t[5])};
        need(v.rom>=0 && v.rom<rc,"MDL tile ROM range"); m.tiles.push_back(v);
    }
    m.modelLine=at; int mc=countAt(l,at++,"ModelDat"); for(int i=0;i<mc;++i) {
        Model model{}; for(auto& layer:model.layer){auto n=ints(l.at(at++).body,3); std::copy(n.begin(),n.end(),layer.begin()); need(n[0]>=-1 && n[0]<tc,"MDL layer tile range");}
        auto frame=tokens(l.at(at++).body); need(!frame.empty(),"MDL frame"); int fc=integer(frame[0]); need(fc>0&&fc<=4096&&frame.size()==std::size_t(1+fc*2),"MDL frame size"); for(auto& t:frame)integer(t);
        ints(l.at(at++).body,8); need(l.at(at++).body=="Pass","MDL pass label");
        for(int f=0;f<fc;++f) { auto dim=ints(l.at(at++).body,2); need(dim[0]>=0&&dim[1]>=0&&dim[0]<=4096&&dim[1]<=4096,"MDL Pass bound");
            for(int y=0;y<dim[1];++y) ints(l.at(at++).body,static_cast<std::size_t>(dim[0])); }
        m.models.push_back(model);
    }
    m.placementLine=at; need(l.at(at++).body=="Model","MDL Model label");
    while(at<l.size()) { if(tokens(l[at].body).empty()){++at;continue;} auto n=ints(l.at(at).body,3);
        need(n[2]>=0&&n[2]<=100000,"MDL block count"); Block block{n[0],n[1],n[2],at,0}; auto bi=m.blocks.size(); ++at;
        for(int i=0;i<n[2];++i) { Place p{}; p.line=at; p.block=bi; auto t=tokens(l.at(at++).body); need(t.size()>=10,"MDL placement shape");
            for(int j=0;j<9;++j)p.f[j]=integer(t[j]); p.palette=integer(t.back()); need(p.f[0]>=0&&p.f[0]<mc,"MDL placement model range"); m.places.push_back(p); }
        block.end=at; m.blocks.push_back(block);
    } return m;
}
static std::string replaceToken(const Line& l,std::size_t ordinal,int value) {
    auto s=l.body; std::size_t at=0,n=0,end=0;
    for(std::size_t i=0;i<=ordinal;++i) {n=s.find_first_not_of(" \t",at);need(n!=std::string::npos,"Count token");end=s.find_first_of(" \t",n);if(end==std::string::npos)end=s.size();at=end;}
    s.replace(n,end-n,std::to_string(value));return s;
}
static std::string countLine(const Line& l,int value) {return replaceToken(l,1,value);}
struct Pair { int first,second; bool reverse; };
struct Spec { std::string path,hash,frameFile,frameHash; int firstAction; std::vector<Pair> pairs; };
static const std::string panelHash="151033be38448d6f1dabbc1314caad3546f8da80a9be3bab4c754cd85d74b2ed";
static const std::vector<Spec> specs{
    {"Data2/map/island01/cityi1/cityi1.mdlZ","bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618","Data2/map/island01/cityi1/npcad.ROMZ","5cd0a3d02f870e5b9b073f6bebf109632650e587cb8f1290a6db464e894687e5",1001,{{135,138,false}}},
    {"Data2/map/south002/citys02/citys02.mdlZ","cf97d0114f636da64d01069b020e9bd290a13e3f13d74960255987d36807e306","Data2/map/south002/citys02/OTH.ROMZ","3d322bc65ddca49a8e950a3d703849bb3d3614e964e406f88f86956d8a223cb7",1026,{{311,321,false},{350,353,false},{549,550,false},{348,351,true},{426,407,true}}},
    {"Data2/map/south002/citys09/citys09.mdlZ","cdc85743f2b0364c6edb83898a10e01872b97e6e9dd92cc6085a6dba19276aa8","Data2/map/south002/OTH.ROMZ","3d322bc65ddca49a8e950a3d703849bb3d3614e964e406f88f86956d8a223cb7",1026,{{211,212,true}}}
};
static std::wstring folded(fs::path p);
static bool inside(const fs::path& p,const fs::path& root);
static std::pair<int,int> global(const Mdl& m,const Place& p) {
    auto b=m.blocks.at(p.block); int x=p.f[1]+840*(b.x+b.y), y=p.f[2]+420*(b.y-b.x)-400;
    need(x==40*(p.f[3]+p.f[4]) && y==20*(p.f[4]-p.f[3]),"Selected MDL grid/pixel disagreement"); return {x,y};
}
static const Tile& post(const Mdl& m,const Place& p,const Spec& s,int act) {
    auto model=m.models.at(p.f[0]); need(model.layer[0][1]==0&&model.layer[0][2]==0,"Post layer offset");
    auto& t=m.tiles.at(model.layer[0][0]); need(t.type==23&&t.action==act,"Source post ACT/type mismatch");
    auto name=fs::path(m.refs.at(t.rom)).filename().string(); auto expectedPath=fs::path(s.frameFile).filename();expectedPath.replace_extension(".ROM");auto expected=expectedPath.string();
    need(name==expected,"Source post ROM reference mismatch"); need(p.f[5]==0&&p.f[8]==0&&p.palette==0,"Post flags/attachment/palette");
    global(m,p); return t;
}
static void verifyFrameSource(const fs::path& client,const Spec& s,const Mdl& m,const Tile& tile) {
    // ROMFILE tokens are relative to the MDL directory, including legitimate '..'.
    // Preserve that token for compressed lookup; do not assume a local duplicate.
    auto token=fs::path(m.refs.at(tile.rom));
    need(!token.is_absolute()&&!token.has_root_name()&&!token.has_root_directory(),"Absolute ROMFILE token rejected");
    token+=L"Z";
    auto resolved=fs::canonical((client/fs::path(s.path)).parent_path()/token);
    need(inside(resolved,client),"ROMFILE target escaped the client root");
    auto pinned=fs::canonical(client/fs::path(s.frameFile));
    need(inside(pinned,client)&&folded(resolved)==folded(pinned),"ROMFILE target differs from pinned TW source path");
    need(sha(read(resolved))==s.frameHash,"TW frame source pin mismatch");
}
static std::string quote(const std::string& s) {
    std::string out="\""; static constexpr char h[]="0123456789abcdef";
    for(unsigned char c:s) { if(c=='"'||c=='\\'){out+='\\';out+=char(c);} else if(c<32){out+="\\u00";out+=h[c>>4];out+=h[c&15];} else out+=char(c); }return out+'"';
}
struct Candidate { fs::path relative; Bytes before,after; std::string detail; };
static Candidate prepare(const fs::path& client,const Spec& s) {
    Candidate c{fs::path(s.path),read(client/fs::path(s.path)),{}, {}}; need(sha(c.before)==s.hash,"TW MDL source pin mismatch: "+s.path);
    auto plain=decode(c.before); auto m=parse(plain); auto newline=m.lines.at(m.romLine).ending; need(!newline.empty(),"MDL section newline");
    std::map<std::size_t,std::vector<std::string>> insert; std::map<std::size_t,std::string> replace; std::map<std::size_t,int> addedPerBlock;
    insert[m.tileLine].push_back("npcboard.ROM"); // Short native ROM token; compressed file is npcboard.ROMZ.
    replace[m.romLine]=countLine(m.lines[m.romLine],static_cast<int>(m.refs.size())+1);
    std::vector<bool> directions; for(auto p:s.pairs) if(std::find(directions.begin(),directions.end(),p.reverse)==directions.end())directions.push_back(p.reverse);
    auto tileBase=static_cast<int>(m.tiles.size()), modelBase=static_cast<int>(m.models.size());
    for(std::size_t i=0;i<directions.size();++i) {
        bool rev=directions[i]; int act=rev?1701:1101; // Original TW ACT codes, not direction ordinal 6 or invented 1107.
        insert[m.modelLine].push_back(std::string(rev?"god2_board_reverse":"god2_board_forward")+" 23 80 "+(rev?"141":"150")+" "+std::to_string(m.refs.size())+" "+std::to_string(act));
        for(auto line:std::vector<std::string>{std::to_string(tileBase+int(i))+" 0 0","-1 0 0","-1 0 0","1 0 0","-1 -1 -1 -1 -1 -1 -1 -1","Pass","0 0"}) insert[m.placementLine].push_back(line);
    }
    replace[m.tileLine]=countLine(m.lines[m.tileLine],tileBase+static_cast<int>(directions.size()));
    replace[m.modelLine]=countLine(m.lines[m.modelLine],modelBase+static_cast<int>(directions.size()));
    std::ostringstream detail; detail<<"["; bool first=true;
    for(auto pair:s.pairs) {
        auto p=m.places.at(pair.first), q=m.places.at(pair.second); int act=s.firstAction+(pair.reverse?3:0);
        auto& firstTile=post(m,p,s,act);auto& secondTile=post(m,q,s,act+1);
        verifyFrameSource(client,s,m,firstTile);verifyFrameSource(client,s,m,secondTile);
        auto a=global(m,p),b=global(m,q);
        need(b.first-a.first==(pair.reverse?-160:160)&&b.second-a.second==(pair.reverse?80:40),"Post pair edge geometry");
        int dx=pair.reverse?-80:160,dy=160,gx=pair.reverse?-5:-2,gy=pair.reverse?3:6;
        auto idx=std::find(directions.begin(),directions.end(),pair.reverse)-directions.begin(); auto sourceBlock=m.blocks.at(p.block);
        int x=p.f[3]+gx,y=p.f[4]+gy;
        auto floorBlock=[](int n){return n/21-((n<0&&n%21!=0)?1:0);};
        int ownerX=floorBlock(x),ownerY=floorBlock(y);std::size_t ownerIndex=0,owners=0;
        for(std::size_t i=0;i<m.blocks.size();++i) if(m.blocks[i].x==ownerX&&m.blocks[i].y==ownerY){ownerIndex=i;++owners;}
        need(owners==1,"New anchor must have exactly one existing natural owner block");
        auto block=m.blocks[ownerIndex];
        // Native activation uses owner blocks; retain the derived global anchor
        // while expressing its raw pixel coordinates in floor(grid/21)'s block.
        int globalX=a.first+dx,globalY=a.second+dy;
        int px=globalX-840*(block.x+block.y),py=globalY-420*(block.y-block.x)+400;
        need(px+840*(block.x+block.y)==40*(x+y)&&py+420*(block.y-block.x)-400==20*(y-x),"New anchor projection");
        insert[block.end].push_back(std::to_string(modelBase+idx)+" "+std::to_string(px)+" "+std::to_string(py)+" "+std::to_string(x)+" "+std::to_string(y)+" 0 -1 -1 0 0"); ++addedPerBlock[ownerIndex];
        if(!first)detail<<",";first=false;
        detail<<"{\"sourcePostOrders\":["<<pair.first<<","<<pair.second<<"],\"orientation\":\""<<(pair.reverse?"reverse":"forward")<<"\",\"sourceBlock\":["<<sourceBlock.x<<","<<sourceBlock.y<<"],\"block\":["<<block.x<<","<<block.y<<"],\"ownerBlockRule\":\"FLOOR_GRID_OVER_21_EXISTING_UNIQUE\",\"grid\":["<<x<<","<<y<<"],\"rawPixel\":["<<px<<","<<py<<"],\"globalPixel\":["<<globalX<<","<<globalY<<"],\"actionCode\":"<<(pair.reverse?1701:1101)<<"}";
    }
    detail<<"]";c.detail=detail.str();
    for(auto [bi,extra]:addedPerBlock) {auto b=m.blocks.at(bi);replace[b.line]=replaceToken(m.lines[b.line],2,b.count+extra);}
    std::string output;
    for(std::size_t i=0;i<=m.lines.size();++i) {
        for(auto& line:insert[i]) {need(output.empty()||output.back()=='\n',"Insertion after unterminated MDL line");output+=line+newline;}
        if(i<m.lines.size()){auto it=replace.find(i);output+=(it==replace.end()?m.lines[i].body:it->second)+m.lines[i].ending;}
    }
    Bytes modified(output.begin(),output.end()); auto checked=parse(modified);
    need(checked.places.size()==m.places.size()+s.pairs.size()&&checked.models.size()==m.models.size()+directions.size(),"Patched MDL structure");
    c.after=encode(modified,c.before[6]);return c;
}
static std::wstring folded(fs::path p) { auto s=p.lexically_normal().native(); std::transform(s.begin(),s.end(),s.begin(),[](wchar_t c){return std::towlower(c);});return s; }
static bool inside(const fs::path& p,const fs::path& root) {auto a=folded(p),b=folded(root);return a==b||(a.size()>b.size()&&a.compare(0,b.size(),b)==0&&(a[b.size()]=='\\'||a[b.size()]=='/'));}
int wmain(int argc,wchar_t** argv) {
    fs::path pending;bool pendingOwned=false;
    try {
        fs::path client,out;
        for(int i=1;i<argc;++i){std::wstring a=argv[i]; if(a==L"--client-root"&&i+1<argc)client=argv[++i];else if(a==L"--output-root"&&i+1<argc)out=argv[++i];else fail("Usage: god2-tw-map-objects --client-root ABSOLUTE --output-root ABSOLUTE_NEW_STAGING");}
        need(client.is_absolute()&&out.is_absolute(),"Both roots must be absolute");client=fs::canonical(client);
        need(fs::is_directory(client)&&fs::is_directory(out.parent_path()),"Existing client/output parent required");out=fs::canonical(out.parent_path())/out.filename();
        need(!inside(out,client)&&!inside(client,out)&&!fs::exists(out),"Output must be new staging outside the client");
        auto panel=read(client/"Data2/Rom/Npc/npc2584.ROMZ");need(sha(panel)==panelHash,"TW panel ROM pin mismatch");
        std::vector<Candidate> candidates; for(auto& s:specs)candidates.push_back(prepare(client,s)); // Validate the WHOLE candidate before output.
        std::ostringstream manifest;
        manifest<<"{\n  \"schema\":\"god2-tw-fixed-board-staging/1\",\"designId\":\"CUSTOM-0151\",\n  \"origin\":\"CUSTOM_DESIGNED_FROM_PINNED_TW_MDL_AND_ROM\",\"nativeAcceptance\":\"NOT_RUN\",\n  \"collision\":\"EMPTY_PASS_CUSTOM_DECORATION_UNVERIFIED_IN_CLIENT\",\"sourceClientModified\":false,\"npcCreated\":false,\"databaseModified\":false,\"executableModified\":false,\n  \"panelSourceSHA256\":"<<quote(panelHash)<<",\"panelFilename\":\"npcboard.ROMZ\",\"maps\":[\n";
        for(std::size_t i=0;i<candidates.size();++i){auto& c=candidates[i];if(i)manifest<<",\n";manifest<<"    {\"path\":"<<quote(c.relative.generic_string())<<",\"oldSHA256\":"<<quote(sha(c.before))<<",\"newSHA256\":"<<quote(sha(c.after))<<",\"preservedHeader6\":"<<int(c.before[6])<<",\"oldBytes\":"<<c.before.size()<<",\"newBytes\":"<<c.after.size()<<",\"originalLinesPreservedExceptCounts\":true,\"placements\":"<<c.detail<<"}";}
        manifest<<"\n  ]\n}\n";
        pending=out;pending+=L".pending-"+std::to_wstring(GetCurrentProcessId());need(!fs::exists(pending),"Staging temporary path already exists");
        need(fs::create_directory(pending),"Create staging temporary root");pendingOwned=true;
        for(auto& c:candidates){write(pending/c.relative,c.after);write(pending/c.relative.parent_path()/"npcboard.ROMZ",panel);}
        auto text=manifest.str();write(pending/"manifest.json",Bytes(text.begin(),text.end()));
        fs::rename(pending,out);pendingOwned=false;pending.clear();std::cout<<"Prepared 3 maps / 7 fixed decorations. Native-client acceptance NOT RUN.\n";return 0;
    } catch(const std::exception& e) {
        // pending is a freshly created tool-owned directory outside the source client.
        if(pendingOwned&&!pending.empty()&&fs::exists(pending)){std::error_code ec;fs::remove_all(pending,ec);}
        std::cerr<<"No successful staging publication: "<<e.what()<<"\n";return 1;
    }
}
