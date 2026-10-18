// CUSTOM-0157: offline, pinned Taiwan client HTTP name-card failure guards.
// Never executes or modifies the input client; emits a reviewable staging pair.
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
using Bytes=std::vector<unsigned char>;
constexpr const char* pin="99cde6b666101c0702d712a1a15bf4d83f225a1a521a9c601bd32a6e42debe25";
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
static std::string sha(const Bytes& b){
    BCRYPT_ALG_HANDLE a{};need(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"SHA provider");
    struct AC{BCRYPT_ALG_HANDLE a;~AC(){BCryptCloseAlgorithmProvider(a,0);}} ac{a};
    DWORD n{},used{};need(BCryptGetProperty(a,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&n),sizeof n,&used,0)>=0,"SHA size");
    Bytes object(n),digest(32);BCRYPT_HASH_HANDLE h{};
    need(BCryptCreateHash(a,&h,object.data(),n,nullptr,0,0)>=0,"SHA create");
    struct HC{BCRYPT_HASH_HANDLE h;~HC(){BCryptDestroyHash(h);}} hc{h};
    need(b.size()<=std::numeric_limits<ULONG>::max(),"SHA bound");
    need(BCryptHashData(h,const_cast<PUCHAR>(b.data()),static_cast<ULONG>(b.size()),0)>=0,"SHA input");
    need(BCryptFinishHash(h,digest.data(),32,0)>=0,"SHA finish");
    std::ostringstream s;for(auto v:digest)s<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(v);return s.str();
}
static Bytes read(const fs::path& p){
    auto n=fs::file_size(p);need(n>0&&n<=16*1024*1024,"Client file size bound");Bytes b(static_cast<size_t>(n));
    std::ifstream f(p,std::ios::binary);need(bool(f.read(reinterpret_cast<char*>(b.data()),static_cast<std::streamsize>(n))),"Read client");return b;
}
static uint32_t get(const Bytes& b,size_t p,size_t n=4){need(p<=b.size()&&n<=b.size()-p&&n<=4,"PE read bound");uint32_t v=0;for(size_t i=0;i<n;++i)v|=uint32_t(b[p+i])<<(8*i);return v;}
static void put(Bytes& b,size_t p,uint32_t v,size_t n=4){need(p<=b.size()&&n<=b.size()-p&&n<=4,"PE write bound");for(size_t i=0;i<n;++i)b[p+i]=static_cast<unsigned char>(v>>(8*i));}
static uint32_t align(uint32_t v,uint32_t n){need(n&&!(n&(n-1))&&uint64_t(v)+n<=UINT32_MAX,"PE alignment");return (v+n-1)&~(n-1);}
static std::string quote(const std::string& s){std::string r="\"";for(unsigned char c:s){need(c>=32,"JSON control character");if(c=='"'||c=='\\')r+='\\';r+=char(c);}return r+'"';}
static std::string hex(uint32_t v){std::ostringstream s;s<<"0x"<<std::hex<<v;return s.str();}
static std::string byteshex(const Bytes& b){std::ostringstream s;for(auto v:b)s<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(v);return s.str();}
static void write(const fs::path& p,const Bytes& b){std::ofstream f(p,std::ios::binary|std::ios::trunc);need(bool(f),"Create staged file");f.write(reinterpret_cast<const char*>(b.data()),static_cast<std::streamsize>(b.size()));f.close();need(bool(f),"Write staged file");}
struct Image{
    const Bytes& b;size_t pe,opt,table;uint32_t base,sections,headers,fileAlign,sectionAlign,imageSize;
    explicit Image(const Bytes& v):b(v){
        need(get(b,0,2)==0x5a4d,"DOS signature");pe=get(b,60);need(get(b,pe)==0x4550&&get(b,pe+4,2)==0x14c,"x86 PE signature");
        sections=get(b,pe+6,2);opt=pe+24;need(get(b,opt,2)==0x10b&&get(b,pe+20,2)==224,"PE32 optional header");
        table=opt+224;base=get(b,opt+28);sectionAlign=get(b,opt+32);fileAlign=get(b,opt+36);imageSize=get(b,opt+56);headers=get(b,opt+60);
        need(base==0x400000&&sections==12&&headers<=b.size()&&table+(sections+1)*40<=headers,"Pinned PE layout/header room");
        need(sectionAlign==4096&&fileAlign==512&&imageSize<0x1000000,"Pinned PE alignment/size");
    }
    size_t offset(uint32_t va,size_t count)const{
        need(va>=base,"VA base");auto rva=va-base;
        for(uint32_t i=0;i<sections;++i){auto p=table+40*i;auto rv=get(b,p+12),n=get(b,p+16),raw=get(b,p+20);
            if(rva>=rv&&uint64_t(rva)+count<=uint64_t(rv)+n){need(uint64_t(raw)+rva-rv+count<=b.size(),"Section file bound");return raw+rva-rv;}}
        throw std::runtime_error("VA not file-backed");
    }
};
struct Code{
    uint32_t va;Bytes b;
    void emit(std::initializer_list<unsigned char> v){b.insert(b.end(),v);}
    void word(uint32_t v){for(unsigned i=0;i<4;++i)b.push_back(static_cast<unsigned char>(v>>(8*i)));}
    void branch(unsigned char op,uint32_t target){emit({op});word(target-(va+static_cast<uint32_t>(b.size())+4));}
    size_t conditional(){emit({0x0f,0x84});auto p=b.size();word(0);return p;}
    void fix(size_t p,uint32_t target){put(b,p,target-(va+static_cast<uint32_t>(p)+4));}
};
int wmain(int argc,wchar_t** argv){
    fs::path pending;bool pendingOwned=false;
    try{
        fs::path source,out;
        for(int i=1;i<argc;++i){std::wstring a=argv[i];if(a==L"--client-exe"&&i+1<argc)source=argv[++i];else if(a==L"--output-root"&&i+1<argc)out=argv[++i];else throw std::runtime_error("Usage: god2-tw-name-card-guard --client-exe ABS_EXE --output-root ABS_NEW_STAGING");}
        need(source.is_absolute()&&out.is_absolute(),"Absolute input/output paths required");source=fs::canonical(source);
        need(fs::is_directory(out.parent_path()),"Output parent must exist");out=fs::canonical(out.parent_path())/out.filename();
        need(!fs::exists(out)&&!out.filename().empty(),"New staging directory required");
        auto before=read(source);need(sha(before)==pin,"Full Taiwan client SHA256 mismatch; no staging created");Image pe(before);
        uint32_t rawEnd=0,virtualEnd=0;
        for(uint32_t i=0;i<pe.sections;++i){auto p=pe.table+40*i;auto raw=get(before,p+20),n=get(before,p+16),rv=get(before,p+12),vs=get(before,p+8);
            need(uint64_t(raw)+n<=before.size()&&uint64_t(rv)+std::max(vs,n)<=pe.imageSize,"Section bounds");rawEnd=std::max(rawEnd,raw+n);virtualEnd=std::max(virtualEnd,rv+std::max(vs,n));}
        need(rawEnd==before.size()&&align(virtualEnd,pe.sectionAlign)==pe.imageSize,"Overlay/image extent must match pinned layout");
        auto header=pe.table+pe.sections*40;
        need(std::all_of(before.begin()+header,before.begin()+header+40,[](auto c){return c==0;}),"New section header must occupy zero padding");
        auto rva=align(pe.imageSize,pe.sectionAlign),raw=align(rawEnd,pe.fileAlign);
        Code first{pe.base+rva,{}};
        first.emit({0x85,0xc0});auto fail1=first.conditional();
        first.emit({0x83,0x7c,0x24,0x64,0x00});auto fail2=first.conditional();
        first.emit({0x83,0x7c,0x24,0x68,0x00});auto fail3=first.conditional();
        first.emit({0x83,0xbc,0x24,0x80,0x00,0x00,0x00,0x00});auto fail4=first.conditional();
        const Bytes old1{0x8b,0x43,0x08,0x8b,0x3d,0x14,0x07,0x57,0x00};
        first.b.insert(first.b.end(),old1.begin(),old1.end());first.branch(0xe9,0x40ff23);
        auto fail=first.va+static_cast<uint32_t>(first.b.size());
        first.emit({0x31,0xc0,0x5f,0x5e,0x5d,0x5b,0x81,0xc4,0x80,0x00,0x00,0x00,0xc2,0x0c,0x00});
        for(auto p:{fail1,fail2,fail3,fail4})first.fix(p,fail);
        while(first.b.size()%16)first.emit({0x90});
        Code second{first.va+static_cast<uint32_t>(first.b.size()),{}};
        second.emit({0x85,0xc0});auto noReply=second.conditional();second.emit({0x80,0x38,0x00});auto empty=second.conditional();
        const Bytes old2{0x8b,0x15,0xf0,0x4a,0x58,0x00};
        second.b.insert(second.b.end(),old2.begin(),old2.end());second.branch(0xe9,0x40eabb);second.fix(noReply,0x40eb71);second.fix(empty,0x40eb71);
        Bytes code=first.b;code.insert(code.end(),second.b.begin(),second.b.end());need(code.size()<512,"Guard code bound");
        auto after=before;after.resize(raw+align(static_cast<uint32_t>(code.size()),pe.fileAlign));std::copy(code.begin(),code.end(),after.begin()+raw);
        std::set<size_t> allowed;
        auto allow=[&](size_t p,size_t n){for(size_t i=0;i<n;++i)allowed.insert(p+i);};
        put(after,pe.pe+6,pe.sections+1,2);allow(pe.pe+6,2);
        put(after,pe.opt+4,get(before,pe.opt+4)+512);allow(pe.opt+4,4);
        put(after,pe.opt+56,align(rva+static_cast<uint32_t>(code.size()),pe.sectionAlign));allow(pe.opt+56,4);
        const char name[]=".cardfix";std::copy(name,name+8,after.begin()+header);
        put(after,header+8,static_cast<uint32_t>(code.size()));put(after,header+12,rva);put(after,header+16,512);put(after,header+20,raw);put(after,header+36,0x60000020);allow(header,40);
        struct Site{uint32_t va,target;Bytes expected,patched;size_t offset;};
        std::vector<Site> sites{{0x40ff1a,first.va,old1,{},0},{0x40eab5,second.va,old2,{},0}};
        for(auto& s:sites){s.offset=pe.offset(s.va,s.expected.size());need(std::equal(s.expected.begin(),s.expected.end(),before.begin()+s.offset),"Original guard site bytes mismatch");
            Code jump{s.va,{}};jump.branch(0xe9,s.target);while(jump.b.size()<s.expected.size())jump.emit({0x90});s.patched=jump.b;
            std::copy(s.patched.begin(),s.patched.end(),after.begin()+s.offset);allow(s.offset,s.patched.size());}
        size_t changed=0;for(size_t i=0;i<before.size();++i)if(before[i]!=after[i]){need(allowed.contains(i),"Unexpected original byte changed");++changed;}
        need(get(after,pe.opt+16)==get(before,pe.opt+16)&&std::equal(before.begin()+pe.opt+96,before.begin()+pe.opt+224,after.begin()+pe.opt+96),"Entry/import/data-directory preservation");
        std::ostringstream manifest;manifest<<"{\n  \"schema\":\"tw-name-card-guard-staging/1\",\"designId\":\"CUSTOM-0157\",\n  \"source\":"<<quote(source.generic_string())<<",\n  \"sourceSHA256\":"<<quote(pin)<<",\"candidateSHA256\":"<<quote(sha(after))<<",\n  \"beforeBytes\":"<<before.size()<<",\"afterBytes\":"<<after.size()<<",\"changedOriginalBytes\":"<<changed<<",\n  \"newSection\":\".cardfix\",\"newSectionRVA\":"<<quote(hex(rva))<<",\"guardCodeBytes\":"<<code.size()<<",\n  \"checksumPolicy\":\"original optional-header CheckSum retained; not an integrity assertion\",\n  \"unrelatedOriginalBytesPreserved\":true,\"entryAndDataDirectoriesPreserved\":true,\"sourceClientModified\":false,\"databaseOpened\":false,\"nativeAcceptance\":\"NOT_RUN\",\n  \"sites\":[";
        for(size_t i=0;i<sites.size();++i){auto& s=sites[i];if(i)manifest<<',';manifest<<"{\"va\":"<<quote(hex(s.va))<<",\"fileOffset\":"<<s.offset<<",\"target\":"<<quote(hex(s.target))<<",\"before\":"<<quote(byteshex(s.expected))<<",\"after\":"<<quote(byteshex(s.patched))<<"}";}
        manifest<<"]\n}\n";
        pending=out;pending+=L".pending-"+std::to_wstring(GetCurrentProcessId());need(!fs::exists(pending),"Temporary staging already exists");
        need(fs::create_directory(pending),"Create staging");pendingOwned=true;
        write(pending/"God2.before.exe",before);write(pending/"God2.name-card-guard.exe",after);auto text=manifest.str();write(pending/"manifest.json",Bytes(text.begin(),text.end()));
        fs::rename(pending,out);pendingOwned=false;
        std::cout<<"Staged two name-card failure guards; input unchanged. Native acceptance NOT RUN.\nCandidate SHA256 "<<sha(after)<<"\n";return 0;
    }catch(const std::exception& e){if(pendingOwned){std::error_code ec;fs::remove_all(pending,ec);}std::cerr<<"No successful staging publication: "<<e.what()<<'\n';return 1;}
}
