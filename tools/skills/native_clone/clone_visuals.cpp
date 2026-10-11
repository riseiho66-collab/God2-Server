#include "clone_visuals.h"
#include "clone_particles.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <vector>
#include <cstdio>
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#if !defined(_M_IX86) && !defined(SHUNYING_CLONE_TEST)
#error This native bridge is specific to the verified 32-bit God2 client.
#endif

#if defined(SHUNYING_CLONE_TEST)
extern std::uintptr_t clone_test_native(unsigned rva);
extern unsigned clone_test_milliseconds();
#endif

namespace shunying_clone {
namespace {
using Byte = unsigned char;
constexpr unsigned kSlots = 14, kLayers = 4, kMaxTargets = 3;
constexpr unsigned kNoHandle = 0xffff;
std::uintptr_t base = 0;
unsigned milliseconds() {
#if defined(SHUNYING_CLONE_TEST)
    return clone_test_milliseconds();
#else
    return GetTickCount();
#endif
}
constexpr float kPreviewScale = 1.28f;
constexpr float kPi = 3.14159265358979323846f;

template<class T> T read(const void* p, unsigned offset) {
    T value{};
    std::memcpy(&value, static_cast<const Byte*>(p) + offset, sizeof(value));
    return value;
}
template<class T> void write(void* p, unsigned offset, T value) {
    std::memcpy(static_cast<Byte*>(p) + offset, &value, sizeof(value));
}
template<class T> T native(unsigned rva) {
#if defined(SHUNYING_CLONE_TEST)
    return reinterpret_cast<T>(clone_test_native(rva));
#else
    return reinterpret_cast<T>(base + rva);
#endif
}
Byte* actor(void* war, unsigned side, unsigned slot, unsigned layer = 0) {
    if (!war || side > 1 || slot >= kSlots || layer >= 6) return nullptr;
    return read<Byte*>(war, 0x38 + ((side * kSlots + slot) * 6 + layer) * 4);
}
struct Vec { float x{}, y{}; };
Vec home(const Byte* a) {
    return {float(read<short>(a, 0x1d4)), float(read<short>(a, 0x1d6))};
}
struct Layer {
    unsigned handle{kNoHandle};
    std::array<unsigned short,256> palette{};
    std::array<Byte,32> scaled_header{};
    std::vector<Byte> scaled_pixels;
    std::vector<unsigned short> scaled_spans;
};
struct EffectLayer {
    unsigned handle{kNoHandle};
    std::array<int,4> secondary_clip{};
};
struct EmittedAction {
    const Byte* manager{};
    unsigned handle{};
};
struct PositionOverride {
    unsigned handle{kNoHandle};short x{},y{},z{};
};
struct Cast {
    void* war{};
    void* display{};
    unsigned side{}, slot{}, count{};
    bool running{};
    bool returning{}, warped{}, reported{};
    unsigned start_ms{}, warp_ms{}, return_ms{};
    unsigned clone_count{};
    std::array<unsigned,2> clone_targets{};
    Vec cast_frame_anchor{};
    std::array<Vec,2> attack_points{};
    std::array<std::array<Byte,200>,kLayers> cast_frames{};
    std::array<unsigned, kMaxTargets> targets{};
    std::array<Vec, 2> flank{};
    std::array<std::array<Layer, kLayers>, 2> images{};
    std::vector<PositionOverride> originals;
    std::array<std::vector<EffectLayer>,2> effects{};
    bool effects_reported{};
    unsigned effects_max_reported{};
    std::vector<EmittedAction> emitted;
};
std::array<Cast, 2 * kSlots> casts{};

Byte* display_entry(void* manager, unsigned handle) {
    return static_cast<Byte*>(manager) + 0x1258 + handle * 200;
}
template<class Visual> void release_layer(Cast& cast, Visual& layer) {
    if (cast.display && layer.handle < 5000) {
        native<void(__thiscall*)(void*, unsigned)>(0x26a30)(cast.display, layer.handle);
    }
    layer.handle = kNoHandle;
}
void restore_positions(Cast& cast) {
    if(!cast.display)return;
    for(auto& saved:cast.originals){
        if(saved.handle<5000 && display_entry(cast.display,saved.handle)[0]==2){
            native<void(__thiscall*)(void*,unsigned,int,int)>(0x26e80)(cast.display,saved.handle,saved.x,saved.y);
            const auto option=display_entry(cast.display,saved.handle)[2];
            native<void(__thiscall*)(void*,unsigned,int)>(0x26cf0)(cast.display,saved.handle,saved.z);
            display_entry(cast.display,saved.handle)[2]=option;
        }
    }
    cast.originals.clear();
}
void release(Cast& cast) {
    restore_positions(cast);
    if(cast.war)particles::release_cast(cast.side*kSlots+cast.slot);
    for (auto& image : cast.images)
        for (auto& layer : image) release_layer(cast, layer);
    for(auto& effect:cast.effects)for(auto& layer:effect)release_layer(cast,layer);
    cast = Cast{};
}

Vec choose_flank(void* war, unsigned side, unsigned slot, unsigned clone) {
    const Vec origin = home(actor(war, side, slot));
    // Close perpendicular flanks, not spare battle formation slots. Choose the
    // nearest useful gap without moving any real teammate or changing targets.
    const float sign = clone == 0 ? -1.0f : 1.0f;
    Vec best{72.0f / kPreviewScale * sign, 0.0f};
    float best_clearance = -1.0f;
    constexpr float depths[]{0,18,-18,36,-36};
    for (unsigned candidate = 0; candidate < 5; ++candidate) {
        Vec v{72.0f / kPreviewScale * sign, depths[candidate] / kPreviewScale};
        float clearance = 100000.0f;
        for (unsigned peer = 0; peer < kSlots; ++peer) {
            if (peer == slot) continue;
            const auto a = actor(war, side, peer);
            if (!a || read<unsigned short>(a, 0x1a) >= 4096) continue;
            const Vec p = home(a);
            const float dx = origin.x + v.x - p.x, dy = origin.y + v.y - p.y;
            clearance = std::min(clearance, dx * dx + dy * dy);
        }
        if (clearance > best_clearance) { best = v; best_clearance = clearance; }
        if (clearance >= 50.0f * 50.0f) break;
    }
    return best;
}

// Copy only borrowed visual values, never linked-list pointers, text handles,
// child objects, ACT events, or ownership fields. Each clone owns its display
// allocation; bitmap/palette remain owned by the original loaded asset bank.
unsigned shift(unsigned mask) { unsigned n=0; while(mask && !(mask&1)){mask>>=1;++n;}return n; }
void* shadow_palette(Cast& cast,Layer& layer,const Byte* source) {
    auto image=read<Byte*>(source,0x8c);
    auto palette=read<unsigned short*>(source,0x94);
    if(!image || (read<Byte>(image,6)!=0 && read<Byte>(image,6)!=3 && read<Byte>(image,6)!=4))return palette;
    if(!palette && image)palette=read<unsigned short*>(image,8);
    if(!palette)return nullptr;
    unsigned masks[3]{read<unsigned short>(cast.display,0x1210),read<unsigned short>(cast.display,0x1212),read<unsigned short>(cast.display,0x1214)};
    if(!masks[0] || !masks[1] || !masks[2])return palette;
    // 00424520 copies 0x80 DWORDs and 004245B0 processes 0x100 colors;
    // a native display palette is always the renderer's full 256-entry table.
    for(unsigned i=0;i<256;++i){
        float channel[3]{};unsigned shifts[3]{},maxima[3]{};
        for(unsigned c=0;c<3;++c){shifts[c]=shift(masks[c]);maxima[c]=masks[c]>>shifts[c];channel[c]=float((palette[i]&masks[c])>>shifts[c])/float(maxima[c]);}
        const float luminance=.2126f*channel[0]+.7152f*channel[1]+.0722f*channel[2];
        unsigned pixel=0;
        for(unsigned c=0;c<3;++c){float value=(luminance+.15f*(channel[c]-luminance))*.72f;pixel|=(unsigned(std::lround(value*maxima[c]))<<shifts[c])&masks[c];}
        layer.palette[i]=static_cast<unsigned short>(pixel);
    }
    return layer.palette.data();
}
void* shrink_image(Layer& layer,Byte* image,float scale) {
    if(!image || read<Byte>(image,6)!=0)return image;
    if(scale>=.999f && read<void*>(image,0x10))return image;
    const int w=read<unsigned short>(image,0),h=read<unsigned short>(image,2);
    const Byte* pixels=read<Byte*>(image,0x14);
    const auto spans=read<const unsigned short*>(image,0x10);
    if(!pixels || w<1 || h<1 || w>2048 || h>2048)return image;
    const unsigned nw=unsigned(std::max(1,int(std::lround(w*scale)))),nh=unsigned(std::max(1,int(std::lround(h*scale))));
    // 00423820 computes pixels + y*width + x even when the row spans exist;
    // the spans only bound drawing, and do not encode or pack the pixel rows.
    layer.scaled_pixels.resize(nw*nh);layer.scaled_spans.resize(nh*2);
    for(unsigned y=0;y<nh;++y){
        const unsigned sy=std::min(unsigned(h-1),unsigned(float(y)/scale));
        for(unsigned x=0;x<nw;++x){const unsigned sx=std::min(unsigned(w-1),unsigned(float(x)/scale));layer.scaled_pixels[y*nw+x]=pixels[sy*unsigned(w)+sx];}
        // Native +10 stores inclusive left/exclusive right; preserve trimmed
        // rows rather than turning transparent padding into opaque rectangles.
        const unsigned left=spans?std::min(unsigned(w),unsigned(spans[sy*2])):0;
        const unsigned right=spans?std::max(left,std::min(unsigned(w),unsigned(spans[sy*2+1]))):unsigned(w);
        layer.scaled_spans[y*2]=static_cast<unsigned short>(std::min(nw,unsigned(std::ceil(left*scale))));
        layer.scaled_spans[y*2+1]=static_cast<unsigned short>(std::min(nw,unsigned(std::ceil(right*scale))));
    }
    // Borrowed bitmap header values only. The new pixels/spans are owned here;
    // native bitmap destructors are never called on this display-only image.
    std::memcpy(layer.scaled_header.data(),image,24);
    write<unsigned short>(layer.scaled_header.data(),0,static_cast<unsigned short>(nw));
    write<unsigned short>(layer.scaled_header.data(),2,static_cast<unsigned short>(nh));
    write<void*>(layer.scaled_header.data(),0x10,layer.scaled_spans.data());
    write<void*>(layer.scaled_header.data(),0x14,layer.scaled_pixels.data());
    return layer.scaled_header.data();
}
void report(Cast& cast,const Byte* source){
#if !defined(SHUNYING_CLONE_TEST)
    if(cast.reported || !source || !read<void*>(source,0x8c))return;cast.reported=true;
    char text[192]{};auto image=read<Byte*>(source,0x8c);
    sprintf_s(text,"CLONE STYLE imageType=%u spans=%u masks=%04x/%04x/%04x alpha=0.42 saturation=0.15 brightness=0.72\r\n",unsigned(read<Byte>(image,6)),unsigned(read<void*>(image,0x10)!=nullptr),unsigned(read<unsigned short>(cast.display,0x1210)),unsigned(read<unsigned short>(cast.display,0x1212)),unsigned(read<unsigned short>(cast.display,0x1214)));
    HANDLE file=CreateFileA("shunying-clone.log",FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file!=INVALID_HANDLE_VALUE){DWORD written{};WriteFile(file,text,DWORD(std::strlen(text)),&written,nullptr);CloseHandle(file);}
#else
    (void)cast;(void)source;
#endif
}
// Copy native blade3 RTB tracks as visual-only display entries. These are not
// character shadows: preserve native bitmap, palette, opacity and render flags.
void update_effect(Cast& cast,EffectLayer& layer,const Byte* source,Vec delta) {
    if(!source || source[0]!=2 || !read<void*>(source,0x8c)){release_layer(cast,layer);return;}
    const int x=int(read<short>(source,4))+int(std::lround(delta.x));
    const int y=int(read<short>(source,6))+int(std::lround(delta.y));
    const int z=int(read<short>(source,8))+int(std::lround(delta.y));
    if(layer.handle==kNoHandle){
        layer.handle=native<unsigned(__thiscall*)(void*)>(0x25b60)(cast.display)&0xffff;
        if(layer.handle>=5000){layer.handle=kNoHandle;return;}
        native<void(__thiscall*)(void*,unsigned,int,int,void*,unsigned,int,void*,void*)>(0x25dc0)(
            cast.display,layer.handle,x,y,read<void*>(source,0x8c),source[1],z,
            read<void*>(source,0x94),read<void*>(source,0xb8));
    }
    Byte* destination=display_entry(cast.display,layer.handle);
    for(unsigned i=1;i<=3;++i)destination[i]=source[i];
    write<void*>(destination,0x8c,read<void*>(source,0x8c));
    write<float>(destination,0x90,read<float>(source,0x90));
    write<void*>(destination,0x94,read<void*>(source,0x94));
    // 00422540 intersects these with [0,width]x[0,height] before screen
    // clipping. B8/BC are bitmap-local crops, so target translation must NOT
    // translate them. 00426B30 draws BC immediately after the B8 crop width.
    if(const void* clip=read<void*>(source,0xb8)){
        std::memcpy(destination+0x98,clip,16);write<void*>(destination,0xb8,destination+0x98);
    }else write<void*>(destination,0xb8,nullptr);
    if(const void* clip=read<void*>(source,0xbc)){
        std::memcpy(layer.secondary_clip.data(),clip,16);write<void*>(destination,0xbc,layer.secondary_clip.data());
    }else write<void*>(destination,0xbc,nullptr);
    native<void(__thiscall*)(void*,unsigned,int,int)>(0x26e80)(cast.display,layer.handle,x,y);
    native<void(__thiscall*)(void*,unsigned,int)>(0x26cf0)(cast.display,layer.handle,z);
    // 00426CF0 reinitializes entries when depth changes; reapply the native
    // render option afterward because 00425DC0 resets byte +2 to zero.
    for(unsigned i=1;i<=3;++i)destination[i]=source[i];
}
// A native ACT frame is a composite: root display, up to 106 follow displays,
// 17 attached ACTs and six emitted ACTs. 0041AD30 initializes both the +AC and
// +180 arrays to 106 words (the latter stores follow IDs, NOT display handles).
void collect_effect_action(void* display,const Byte* actions,unsigned handle,
                           std::array<bool,4096>& visited,std::array<bool,5000>& visible,
                           bool include_detached_emissions=true) {
    std::vector<unsigned> pending{handle};
    while(!pending.empty()){
        const unsigned current=pending.back();pending.pop_back();
        if(current>=visited.size() || visited[current])continue;
        visited[current]=true;
        const Byte* action=actions+0x10+current*0x290;
        if(action[0]!=2)continue;
        const auto add_display=[&](unsigned image){
            if(image<visible.size()){
                const Byte* entry=display_entry(display,image);
                if(entry[0]==2 && read<void*>(entry,0x8c))visible[image]=true;
            }
        };
        add_display(read<unsigned short>(action,0xe));
        const int followers=read<short>(action,0x254);
        if(followers>=0 && followers<=106)
            for(unsigned i=0;i<unsigned(followers);++i)add_display(read<unsigned short>(action,0xac+i*2));
        for(unsigned i=0;i<17;++i){const unsigned child=read<unsigned short>(action,0x256+i*2);if(child<4096 && !visited[child])pending.push_back(child);}
        // 0041C360 stores these children when either generation flag is set.
        if(action[9] || (include_detached_emissions && action[10]))
            for(unsigned i=0;i<6;++i){const unsigned child=read<unsigned short>(action,0x27a+i*2);if(child<4096 && !visited[child])pending.push_back(child);}
    }
}
void update_effects(Cast& cast,void* war,unsigned primary_target) {
    std::array<bool,5000> visible{};
    std::array<bool,4096> visited{};
    std::vector<const Byte*> sources;
    const Byte* effect_actor=actor(war,cast.side,cast.slot,5);
    const unsigned handle=effect_actor?read<unsigned short>(effect_actor,0x1a):kNoHandle;
    const auto rtg=read<Byte*>(war,0x20);
    int track_count=0;
    unsigned active_roots=0;
    if(!cast.returning && rtg && handle<80){
        // 00521400 reads CWar+20; 0042F6A0 creates 0x2034 runtime records,
        // and 0042DE30 frees ACT handles at record+40+i*20 using this layout.
        const Byte* record=rtg+handle*0x2034;
        const int index=read<short>(record,0x28),loaded=read<int>(rtg,0xa6540);
        const auto actions=read<Byte*>(rtg,0xa654c);
        if(read<unsigned>(record,0)==2 && index>=0 && index<loaded && index<80 &&
           actions && read<void*>(actions,4)==cast.display){
            const int count=read<short>(rtg,0xa1042+unsigned(index)*0x110);
            if(count>=0 && count<=256){
                track_count=count;
                for(const auto& emitted:cast.emitted)if(emitted.manager==actions)
                    collect_effect_action(cast.display,actions,emitted.handle,visited,visible);
                for(unsigned i=0;i<unsigned(count);++i){
                    if(read<unsigned>(record,0x34+i*0x20)!=2)continue;
                    ++active_roots;
                    collect_effect_action(cast.display,actions,read<unsigned short>(record,0x40+i*0x20),visited,visible);
                }
            }
        }
    }
    // Preserve the source compositor's order for overlapping equal-depth blue
    // arcs, red crosses and flashes. Only read this list before native drawing;
    // allocation of the translated copies happens after collection is finished.
    const Byte* next=read<Byte*>(cast.display,0xf555c);
    const auto begin=reinterpret_cast<std::uintptr_t>(display_entry(cast.display,0));
    std::array<bool,5000> linked{};
    while(next){
        const auto address=reinterpret_cast<std::uintptr_t>(next);
        if(address<begin || address>=begin+5000*200 || (address-begin)%200)break;
        const unsigned image=unsigned((address-begin)/200);
        if(linked[image])break;linked[image]=true;
        if(visible[image]){sources.push_back(next);visible[image]=false;}
        next=read<Byte*>(next,0xc4);
    }
    // The native list normally includes all visible entries. This bounded
    // fallback also makes a partially constructed frame safe to inspect.
    for(unsigned image=0;image<visible.size();++image)if(visible[image])sources.push_back(display_entry(cast.display,image));
#if !defined(SHUNYING_CLONE_TEST)
    if(!sources.empty() && (!cast.effects_reported || sources.size()>cast.effects_max_reported)){
        cast.effects_reported=true;cast.effects_max_reported=unsigned(sources.size());char message[192]{};
        sprintf_s(message,"CLONE NATIVE BLADE3 compositeRTG=%u tracks=%d roots=%u ACTs=%u displays=%u clones=%u emitted=%u render-final\r\n",handle,track_count,active_roots,
                  unsigned(std::count(visited.begin(),visited.end(),true)),unsigned(sources.size()),cast.clone_count,unsigned(cast.emitted.size()));
        HANDLE file=CreateFileA("shunying-clone.log",FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(file!=INVALID_HANDLE_VALUE){DWORD written{};WriteFile(file,message,DWORD(std::strlen(message)),&written,nullptr);CloseHandle(file);}
    }
#else
    (void)track_count;(void)active_roots;
#endif
    const Byte* target=actor(war,primary_target/kSlots,primary_target%kSlots);
    for(unsigned clone=0;clone<cast.effects.size();++clone){
        const unsigned other_index=cast.clone_targets[clone];
        const Byte* other=clone<cast.clone_count?actor(war,other_index/kSlots,other_index%kSlots):nullptr;
        Vec delta{};if(target && other){const Vec a=home(target),b=home(other);delta={b.x-a.x,b.y-a.y};}
        auto& layers=cast.effects[clone];const unsigned required=target&&other?unsigned(sources.size()):0;
        for(unsigned i=required;i<layers.size();++i)release_layer(cast,layers[i]);
        layers.resize(required);
        for(unsigned i=0;i<required;++i)update_effect(cast,layers[i],sources[i],delta);
    }
}

void capture_frame(std::array<Byte,200>& frame,const Byte* source){
    if(!source || source[0]!=2){frame[0]=0;return;}
    for(unsigned i=0;i<4;++i)frame[i]=source[i];
    std::memcpy(frame.data()+4,source+4,6);
    for(unsigned off:{0x8cu,0x90u,0x94u})std::memcpy(frame.data()+off,source+off,4);
    const void* clip=read<void*>(source,0xb8);
    if(clip){std::memcpy(frame.data()+0x98,clip,16);write<void*>(frame.data(),0xb8,frame.data()+0x98);}else write<void*>(frame.data(),0xb8,nullptr);
}
void update_layer(Cast& cast, Layer& layer, const Byte* source, Vec source_anchor,Vec destination_anchor,float alpha,float scale) {
    if (!source || read<Byte>(source, 0) != 2 || !read<void*>(source, 0x8c)) {
        release_layer(cast, layer);
        return;
    }
    report(cast,source);
    const short x=short(std::lround(destination_anchor.x+(read<short>(source,4)-source_anchor.x)*scale));
    const short y=short(std::lround(destination_anchor.y+(read<short>(source,6)-source_anchor.y)*scale));
    const short z=short(std::lround(destination_anchor.y));
    if (layer.handle == kNoHandle) {
        const unsigned allocated = native<unsigned(__thiscall*)(void*)>(0x25b60)(cast.display);
        layer.handle = allocated & 0xffff;
        if (layer.handle >= 5000) { layer.handle = kNoHandle; return; }
        native<void(__thiscall*)(void*, unsigned, int, int, void*, unsigned, int, void*, void*)>(0x25dc0)(
            cast.display, layer.handle, x, y, read<void*>(source, 0x8c),
            read<Byte>(source, 1), z, read<void*>(source, 0x94), read<void*>(source, 0xb8));
    }
    Byte* destination = display_entry(cast.display, layer.handle);
    write<Byte>(destination, 1, read<Byte>(source, 1)); // orientation/render flags
    write<Byte>(destination, 2, read<Byte>(source, 2));
    write<Byte>(destination, 3, read<Byte>(source, 3)); // viewport layer
    write<void*>(destination, 0x8c, shrink_image(layer,read<Byte*>(source,0x8c),scale));
    // 00425700 -> 004245B0/00423820 implements source*alpha + dest*(1-alpha).
    write<float>(destination, 0x90, read<float>(source, 0x90)*.42f*std::clamp(alpha,0.0f,1.0f));
    write<void*>(destination, 0x94, shadow_palette(cast,layer,source));
    // The source clip may move. Its rectangle is copied into OUR entry.
    const void* source_clip = read<void*>(source, 0xb8);
    if (source_clip) {
        std::memcpy(destination + 0x98, source_clip, 16);
        write<void*>(destination, 0xb8, destination + 0x98);
    } else write<void*>(destination, 0xb8, nullptr);
    write<void*>(destination, 0xbc, nullptr); // never borrow a secondary clip
    native<void(__thiscall*)(void*, unsigned, int, int)>(0x26e80)(cast.display, layer.handle, x, y);
    native<void(__thiscall*)(void*, unsigned, int)>(0x26cf0)(cast.display, layer.handle, z);
    write<Byte>(destination,2,read<Byte>(source,2));
    particles::silhouette(cast.side*kSlots+cast.slot,read<void*>(destination,0x8c),float(x),float(y),
                          read<Byte>(destination,1),read<float>(destination,0x90));
}
}

void initialize(std::uintptr_t image_base) { base = image_base; particles::initialize(image_base); }

void before_action_release(void* manager,const void* action) {
    if(!manager || !action)return;
    const auto begin=reinterpret_cast<std::uintptr_t>(manager)+0x10;
    const auto address=reinterpret_cast<std::uintptr_t>(action);
    if(address<begin || address>=begin+4096*0x290 || (address-begin)%0x290)return;
    const unsigned handle=unsigned((address-begin)/0x290);
    for(auto& cast:casts){
        auto& list=cast.emitted;
        list.erase(std::remove_if(list.begin(),list.end(),[&](const EmittedAction& e){return e.manager==manager && e.handle==handle;}),list.end());
    }
}

void on_action_initializing(void* manager,const void* parent,unsigned child_handle) {
    if(!base || !manager || child_handle>=4096)return;
    // This also covers reuse without a preceding release, including unrelated
    // native UI/HP ACTs. Pending attribution is published before native init,
    // whose final 0041C360 call can synchronously emit grandchildren.
    before_action_release(manager,static_cast<Byte*>(manager)+0x10+child_handle*0x290);
    const auto begin=reinterpret_cast<std::uintptr_t>(manager)+0x10;
    const auto address=reinterpret_cast<std::uintptr_t>(parent);
    if(!parent || address<begin || address>=begin+4096*0x290 || (address-begin)%0x290)return;
    const unsigned parent_handle=unsigned((address-begin)/0x290);
    for(auto& cast:casts){
        if(!cast.war || !cast.display || cast.returning || cast.count<2)continue;
        bool belongs=std::any_of(cast.emitted.begin(),cast.emitted.end(),[&](const EmittedAction& e){return e.manager==manager && e.handle==parent_handle;});
        if(!belongs){
            const Byte* owner=actor(cast.war,cast.side,cast.slot,5);
            const unsigned h=owner?read<unsigned short>(owner,0x1a):kNoHandle;
            const Byte* rtg=read<Byte*>(cast.war,0x20);
            if(!rtg || h>=80 || read<void*>(rtg,0xa654c)!=manager)continue;
            const Byte* record=rtg+h*0x2034;
            const int index=read<short>(record,0x28),loaded=read<int>(rtg,0xa6540);
            if(read<unsigned>(record,0)!=2 || index<0 || index>=loaded || index>=80)continue;
            const int count=read<short>(rtg,0xa1042+unsigned(index)*0x110);
            if(count<0 || count>256)continue;
            std::array<bool,4096> visited{};std::array<bool,5000> visible{};
            for(unsigned i=0;i<unsigned(count) && !visited[parent_handle];++i)
                if(read<unsigned>(record,0x34+i*0x20)==2)
                    collect_effect_action(cast.display,static_cast<Byte*>(manager),read<unsigned short>(record,0x40+i*0x20),visited,visible);
            belongs=visited[parent_handle];
        }
        if(belongs && cast.emitted.size()<4096)cast.emitted.push_back({static_cast<Byte*>(manager),child_handle});
    }
}

void on_result(void* war, unsigned source_side, unsigned source_slot,
               unsigned target_side, unsigned target_slot, bool is_custom) {
    if (!base || !war || source_side > 1 || source_slot >= kSlots) return;
    auto& cast = casts[source_side * kSlots + source_slot];
    Byte* caster = actor(war, source_side, source_slot);
    if (!caster) return;
    if (!is_custom) { if (cast.war) release(cast); return; }
    if (target_side > 1 || target_side == source_side || target_slot >= kSlots) return;
    if (!cast.war || cast.war != war || read<Byte>(caster, 0x239) == 0) {
        if (cast.war) release(cast);
        cast.war = war;
        cast.side = source_side;
        cast.slot = source_slot;
        auto manager = read<void*>(war, 0xc);
        if (!manager) { cast = Cast{}; return; }
        cast.display = read<void*>(manager, 4);
        if (!cast.display) { cast = Cast{}; return; }
        cast.flank[0] = choose_flank(war, source_side, source_slot, 0);
        cast.flank[1] = choose_flank(war, source_side, source_slot, 1);
    }
    const unsigned encoded = target_side * kSlots + target_slot;
    for (unsigned i = 0; i < cast.count; ++i) if (cast.targets[i] == encoded) return;
    if (cast.count < kMaxTargets) cast.targets[cast.count++] = encoded;
}

void before_frame(void* war) {
    for(auto& cast:casts)if(cast.war==war)restore_positions(cast);
}

void after_frame(void* war) {
    if (!base || !war) return;
    const auto manager = read<Byte*>(war, 0xc);
    if (!manager) return;
    for (auto& cast : casts) {
        if (cast.war != war) continue;
        const Byte* caster = actor(war, cast.side, cast.slot);
        if (!caster) {
            release(cast);
            continue;
        }
        const unsigned now=milliseconds();
        const bool native_active=read<Byte>(caster,0x239)!=0 && read<Byte>(caster,0x1ea)==0x13;
        if (!native_active && !cast.returning) {
            // Results can be staged before the native turn scheduler activates
            // this caster. Do not discard an unstarted cast; no display handles
            // exist until its first real native skill frame.
            if (!cast.running) continue;
            if(cast.count<=1 || !cast.warped){release(cast);continue;}
            cast.returning=true;cast.return_ms=now;
        }
        if(!cast.running){cast.running=true;cast.start_ms=now;}
        if (cast.count <= 1) continue; // native blade3: no visual clones
        const float age=float(now-cast.start_ms)*.03f;
        const float return_age=cast.returning?float(now-cast.return_ms)*.03f:0.0f;
        const float return_progress=std::clamp(return_age/20.0f,0.0f,1.0f);
        if(cast.returning && return_age>=30.0f){release(cast);continue;}
        const auto primary_handle = read<unsigned short>(caster, 0x1a);
        if (primary_handle >= 4096) { release(cast); continue; }
        const Byte* primary = manager + 0x10 + primary_handle * 0x290;
        const Vec origin = home(caster);
        const Vec current{float(read<short>(primary, 0x12)), float(read<short>(primary, 0x14))};
        // Native 005224C0 uses first target +23A for skill commands 3/17.
        // +235 holds the latest result and is only the movement target for the
        // normal-attack branch; it must not select the clone's primary anchor.
        const Byte native_target = read<Byte>(caster, 0x23a);
        const unsigned primary_target = (native_target >> 7) * kSlots + (native_target & 0xf);
        if(!cast.returning){
            cast.clone_count=0;bool primary_selected=false;
            for(unsigned i=0;i<cast.count;++i){
                if(cast.targets[i]==primary_target)primary_selected=true;
                else if(cast.clone_count<cast.clone_targets.size())cast.clone_targets[cast.clone_count++]=cast.targets[i];
            }
            if((native_target&0xf)>=kSlots || !primary_selected || cast.clone_count+1!=cast.count){release(cast);continue;}
        }
        std::array<const Byte*,kLayers> frames{};
        for(unsigned i=0;i<kLayers;++i){
            const Byte* source_layer=actor(war,cast.side,cast.slot,i);
            const unsigned handle=source_layer?read<unsigned short>(source_layer,0x1a):kNoHandle;
            if(handle<4096){const Byte* action=manager+0x10+handle*0x290;unsigned image=read<unsigned short>(action,0xe);
                if(action[0]==2 && image<5000)frames[i]=display_entry(cast.display,image);}
        }
        const unsigned stage=read<Byte>(caster,0x233);
        if(!cast.warped && !cast.returning && (stage==5 || stage==4 || stage==6)){
            cast.warped=true;cast.warp_ms=now;
        }
        if(!cast.warped){
            cast.cast_frame_anchor=current;
            for(unsigned i=0;i<kLayers;++i)capture_frame(cast.cast_frames[i],frames[i]);
        }
        const float warp_age=cast.warped?float(now-cast.warp_ms)*.03f:0.0f;
        const bool freeze_cast=cast.warped && !cast.returning && warp_age<4.0f && cast.cast_frames[0][0]==2;
        const unsigned key=cast.side*kSlots+cast.slot;
        const unsigned viewport=frames[0]?frames[0][3]:0;
        particles::begin_frame(cast.display,key,viewport);
        if(cast.returning){particles::burst(key,origin.x,origin.y,return_age,9);particles::burst(key,origin.x,origin.y,return_age-17,13);}
        else if(cast.warped){
            const auto target_actor=actor(war,primary_target/kSlots,primary_target%kSlots);
            if(target_actor){const Vec target_home=home(target_actor);const float sign=cast.side==0?1.0f:-1.0f;
                particles::burst(key,origin.x,origin.y,warp_age,9);
                particles::burst(key,target_home.x+sign*78.0f/kPreviewScale,target_home.y+sign*76.0f/kPreviewScale,warp_age,10);}
        }
        if(age<6.0f && !cast.warped){particles::end_frame(key);continue;}
        const float summon_alpha=cast.warped?1.0f:std::clamp((age-6.0f)/9.0f,0.0f,1.0f);
        for (unsigned clone = 0; clone < cast.clone_count; ++clone) {
            const unsigned target_index = cast.clone_targets[clone];
            const Byte* other = actor(war, target_index / kSlots, target_index % kSlots);
            if (!other) continue;
            const Vec other_home = home(other);
            const float sign=cast.side==0?1.0f:-1.0f;
            if(!cast.returning)cast.attack_points[clone]={other_home.x+sign*78.0f/kPreviewScale,other_home.y+sign*76.0f/kPreviewScale};
            Vec point=cast.warped?cast.attack_points[clone]:Vec{origin.x+cast.flank[clone].x,origin.y+cast.flank[clone].y};
            if(cast.returning){
                const Vec from=cast.attack_points[clone];const float arc=std::sin(return_progress*kPi);
                point={from.x+(origin.x-from.x)*return_progress+arc*(clone==0?-45.0f:45.0f)/kPreviewScale,
                       from.y+(origin.y-from.y)*return_progress-arc*75.0f/kPreviewScale};
                particles::return_stream(key,from.x,from.y,origin.x,origin.y,return_progress,clone==0?-1.0f:1.0f);
                particles::burst(key,from.x,from.y,return_age,8);
            } else if(cast.warped){
                particles::burst(key,origin.x+cast.flank[clone].x,origin.y+cast.flank[clone].y,warp_age,9);
                particles::burst(key,point.x,point.y,warp_age,10);
            } else {
                particles::burst(key,point.x,point.y,age-6.0f,14);
            }
            for (unsigned i = 0; i < kLayers; ++i) {
                if(cast.returning && return_progress>=1.0f){release_layer(cast,cast.images[clone][i]);continue;}
                const Byte* source=freeze_cast?cast.cast_frames[i].data():frames[i];
                update_layer(cast,cast.images[clone][i],source,freeze_cast?cast.cast_frame_anchor:current,point,
                             cast.returning?1.0f-return_progress:summon_alpha,cast.returning?1.0f-.6f*return_progress:1.0f);
            }
        }
        particles::end_frame(key);
        // Match the visual ownership walked by native 0041D9E0: body roots,
        // follow displays, attached ACTs and moving emissions (+9, not +10).
        // Root-only relocation strands attached ground visuals at the old feet.
        // Preserve relative depth (including visuals behind the body) and the
        // render option cleared by 00426CF0. Never copy these into the clones.
        // Native ACT positions/events stay untouched; restore before each tick.
        if(cast.warped && !cast.returning){
            const auto target_actor=actor(war,primary_target/kSlots,primary_target%kSlots);
            if(target_actor){
                const Vec target_home=home(target_actor);const float sign=cast.side==0?1.0f:-1.0f;
                const Vec point{target_home.x+sign*78.0f/kPreviewScale,target_home.y+sign*76.0f/kPreviewScale};
                std::array<bool,4096> visited{};
                std::array<bool,5000> visible{};
                for(unsigned i=0;i<kLayers;++i){
                    const auto source=actor(war,cast.side,cast.slot,i);
                    if(source)collect_effect_action(cast.display,manager,read<unsigned short>(source,0x1a),visited,visible,false);
                }
                for(unsigned handle=0;handle<visible.size();++handle){
                    if(!visible[handle])continue;
                    const auto frame=display_entry(cast.display,handle);
                    const PositionOverride saved{handle,read<short>(frame,4),read<short>(frame,6),read<short>(frame,8)};
                    cast.originals.push_back(saved);
                    const int x=int(std::lround(point.x+saved.x-current.x));
                    const int y=int(std::lround(point.y+saved.y-current.y));
                    const auto option=frame[2];
                    native<void(__thiscall*)(void*,unsigned,int,int)>(0x26e80)(cast.display,handle,x,y);
                    native<void(__thiscall*)(void*,unsigned,int)>(0x26cf0)(cast.display,handle,int(std::lround(point.y+saved.z-current.y)));
                    frame[2]=option;
                }
            }
        }
    }
}

void before_render(void* display) {
    if(!base || !display)return;
    for(auto& cast:casts){
        if(!cast.war || cast.display!=display || !cast.running || cast.count<=1)continue;
        const Byte* caster=actor(cast.war,cast.side,cast.slot);
        const unsigned encoded=caster?read<Byte>(caster,0x23a):0xff;
        const unsigned primary=(encoded>>7)*kSlots+(encoded&0xf);
        update_effects(cast,cast.war,primary);
    }
}

void reset(void* war) {
    for (auto& cast : casts) if (cast.war && (!war || cast.war == war)) release(cast);
}
void before_display_reset(void* display) {
    if (!display) return;
    for (auto& cast : casts) if (cast.war && cast.display == display) release(cast);
    particles::reset_display(display);
}
bool has_tail(void* war){
    for(const auto& cast:casts)if(cast.war==war && cast.returning)return true;
    return false;
}
}

