#include "game/TaiwanNativeHmdBundleSource.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <charconv>
#include <limits>
#include <map>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
using Bytes=std::vector<std::uint8_t>;
using Source=TaiwanNativeHmdBundleSource;
using Selection=TaiwanNativeResourceSelection;
using Scene=SharedTaiwanNativeMovementScene;
bool digest_text(std::string_view s){return s.size()==64&&s.find_first_not_of("0123456789abcdef")==s.npos;}
bool entry_matches(const Session::NormalWorldInitialization& initial,const RecoveredWorldEntryView& frame,const Scene::Lease& lease){
    // The original issued entry identifies this reservation. Its coordinates
    // do not become the saved position again after a committed ordinary walk.
    // 500180 selects46C5A0 ->448300 HMD only for the actual entry kind2.
    // Other entry kinds use a different native loader, not this HMD bundle.
    return frame.kind==2&&initial.qualified_scene_identity()&&initial.entry_written()&&initial.entry_frame()==frame.wire&&
        initial.entry_logical().size()==frame.logical.size()&&
        std::equal(initial.entry_logical().begin(),initial.entry_logical().end(),frame.logical.begin())&&
        frame.actor_handle==lease.actor_handle&&frame.area==lease.position.area&&
        frame.scene==lease.position.scene&&frame.x==lease.position.x&&frame.y==lease.position.y;
}
Bytes ascii_path(const std::filesystem::path& path){
    Bytes out;for(const auto c:path.wstring()){
        if(c<0x20||c>=0x7f)throw std::invalid_argument("HMD root needs qualified ASCII byte paths");
        out.push_back(static_cast<std::uint8_t>(c=='/'?'\\':c));
    }return out;
}
std::filesystem::path byte_path(const Bytes& bytes){
    std::wstring wide;for(const auto c:bytes)wide.push_back(static_cast<wchar_t>(c));return std::filesystem::path(wide);
}
bool same_component(const std::filesystem::path& a,const std::filesystem::path& b){
    auto x=a.wstring(),y=b.wstring();
#ifdef _WIN32
    const auto lower=[](wchar_t c){return c>=L'A'&&c<=L'Z'?static_cast<wchar_t>(c+(L'a'-L'A')):c;};
    std::transform(x.begin(),x.end(),x.begin(),lower);std::transform(y.begin(),y.end(),y.begin(),lower);
#endif
    return x==y;
}
bool contained(const std::filesystem::path& root,const std::filesystem::path& path){
    const auto full=std::filesystem::weakly_canonical(path);auto i=full.begin();
    for(auto r=root.begin();r!=root.end();++r,++i)if(i==full.end()||!same_component(*r,*i))return false;
    return true;
}
bool safe_reference(std::span<const std::uint8_t> bytes,bool catalog=false){
    if(bytes.empty()||bytes.back()=='\\'||bytes.back()=='/'||
       (!catalog&&(bytes.front()=='\\'||bytes.front()=='/')))return false;
    std::string part;
    const auto component=[&]{
        if(part.empty()||part=="."||part=="..")return true; // Physical containment checked before any file open.
        if(part.back()=='.'||part.back()==' ')return false;
        auto base=part.substr(0,part.find('.'));
        for(auto& c:base)if(c>='a'&&c<='z')c=static_cast<char>(c-'a'+'A');
        if(base=="CON"||base=="PRN"||base=="AUX"||base=="NUL")return false;
        return !(base.size()==4&&(base.starts_with("COM")||base.starts_with("LPT"))&&base[3]>='1'&&base[3]<='9');
    };
    for(const auto c:bytes){
        if(c<0x20||c>=0x7f||c==':'||c=='*'||c=='?'||c=='"'||c=='<'||c=='>'||c=='|')return false;
        if(c=='\\'||c=='/'){if(!component())return false;part.clear();}else part.push_back(static_cast<char>(c));
    }return component();
}
Bytes directory_prefix(const Bytes& request){
    const auto at=std::find(request.rbegin(),request.rend(),static_cast<std::uint8_t>('\\'));
    return at==request.rend()?Bytes{}:Bytes(request.begin(),at.base());
}
bool same_sources(const TaiwanNativeSceneResourceOwner::Sources& a,const TaiwanNativeSceneResourceOwner::Sources& b){
    if(&a.hmd.encoded_bytes()!=&b.hmd.encoded_bytes()||a.actual_hmd_generation!=b.actual_hmd_generation||
       a.actual_rom_prefix!=b.actual_rom_prefix||a.roms.size()!=b.roms.size())return false;
    for(std::size_t i=0;i<a.roms.size();++i)
        if(a.roms[i].ordinal!=b.roms[i].ordinal||a.roms[i].actual_resource_generation!=b.roms[i].actual_resource_generation||
           &a.roms[i].selected.encoded_bytes()!=&b.roms[i].selected.encoded_bytes())return false;
    return true;
}
std::int64_t number(std::span<const std::uint8_t> field){
    if(field.empty())return 0;std::int64_t out=0;
    const auto* first=reinterpret_cast<const char*>(field.data());const auto result=std::from_chars(first,first+field.size(),out);
    if(result.ec!=std::errc{}||result.ptr!=first+field.size())throw std::invalid_argument("Map selector raw field malformed");return out;
}
Bytes base_mdt(const NativeMapRecord& row,const NativeMapSource& expected,std::uint16_t area){
    if(row.source!=expected||row.area!=area||row.scene!=0||!TaiwanNativeCanAsset::matches_sha256(row.raw_record,row.record_sha256))
        throw std::invalid_argument("CAN base map source or raw digest mismatch");
    const auto& raw=row.raw_record;std::vector<std::span<const std::uint8_t>> fields;std::size_t at=0;
    for(std::size_t i=0;i<=raw.size();++i){
        if(i<raw.size()&&(raw[i]==0||raw[i]=='\r'||raw[i]=='\n'))throw std::invalid_argument("Map row contains a control delimiter");
        if(i==raw.size()||raw[i]==','){fields.emplace_back(raw.data()+at,i-at);at=i+1;}
    }
    if(fields.size()<14||fields.size()>24||number(fields[3])!=row.area||number(fields[4])!=row.kind||number(fields[5])!=row.scene||
       fields[10].size()>=64||!safe_reference(fields[10],true))throw std::invalid_argument("Map raw selectors/path disagree with the typed row");
    return Bytes(fields[10].begin(),fields[10].end());
}
std::optional<Selection> select_resource(const Selection::Request& request,std::size_t limit,const std::filesystem::path& tree){
    Bytes name=request.native_prefix;name.insert(name.end(),request.original_reference.begin(),request.original_reference.end());
    if(name.empty()||!byte_path(name).is_absolute()||!contained(tree,byte_path(name)))return {};
    const bool suffix=request.kind==Selection::Kind::TextFile||(name.size()>=4&&name[name.size()-4]=='.');
    if(suffix){auto candidate=name;candidate.push_back('Z');if(!contained(tree,byte_path(candidate)))return {};}
    auto selected=Selection::select(request,limit);
    if(!selected||!contained(tree,selected->actual_source())||!contained(tree,selected->candidate_source()))return {};
    return selected;
}
}
struct TaiwanNativeHmdBundleSource::State:std::enable_shared_from_this<State> {
    using Key=std::pair<std::uint16_t,std::uint16_t>;
    struct Area {
        NativeMapRecord base;
        AreaConfiguration configuration;
        TaiwanNativeCanAsset can;
        Bytes logical_directory,logical_can;
        std::uint64_t epoch;
    };
    struct Bundle {
        std::shared_ptr<const Area> area;
        Key key;
        TaiwanNativeSceneResourceOwner::Sources sources;
        TaiwanNativeMapAsset::RomBound binding;
        TaiwanNativeGrid grid;
        std::uint64_t epoch;
    };
    struct Version {
        Configuration configuration;
        std::filesystem::path tree;
        std::uint64_t epoch;
        std::map<std::uint16_t,std::shared_ptr<const Area>> areas;
        std::map<Key,std::shared_ptr<const Bundle>> cache;
    };
    struct Entry {
        const std::weak_ptr<Session> session;
        const Scene::Lease lease;
        const Session::NormalWorldInitialization initialization;
        const RecoveredWorldEntryView entry_view;
        const std::uint64_t battle;
        const std::shared_ptr<Version> version;
        const std::shared_ptr<const Bundle> bundle;
        const InitialPose pose;
        const std::shared_ptr<TaiwanNativeSceneSourceLifetime> token;
        const std::shared_ptr<const TaiwanNativeHmdPreparedBundle> prepared;
    };
    const std::thread::id thread=std::this_thread::get_id();
    const NativeMapCatalog& maps;
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::size_t capacity;
    const PoseSource pose_source;
    std::shared_ptr<Version> version;
    std::map<std::uint64_t,std::weak_ptr<Entry>> entries;
    std::weak_ptr<Entry> affected;
    std::uint64_t next_epoch=1;
    bool busy=false,reentered=false,closed=false;
    State(const NativeMapCatalog& catalog,std::shared_ptr<SharedWorldPresence> common,std::size_t limit,PoseSource pose)
        :maps(catalog),presence(std::move(common)),capacity(limit),pose_source(std::move(pose)){}
    void owner()const{if(thread!=std::this_thread::get_id())throw std::logic_error("HMD bundle game owner mismatch");}
    struct Operation {
        State& state;
        explicit Operation(State& s):state(s){
            s.owner();if(s.busy){s.reentered=true;if(auto e=s.affected.lock())e->token->revoke();throw std::logic_error("HMD bundle source reentered");}
            if(s.closed)throw std::logic_error("HMD bundle source stopped");s.busy=true;s.reentered=false;
        }
        ~Operation(){state.affected.reset();state.busy=false;}
    };
    std::uint64_t epoch(){
        if(next_epoch==std::numeric_limits<std::uint64_t>::max())throw std::overflow_error("HMD source epoch exhausted");return next_epoch++;
    }
    bool retained_ready(Session& session,const Scene::Lease& lease)const{
        if(closed||reentered||session.closing()||session.id()!=lease.session||session.account_id!=lease.account||
           session.character_id!=lease.character||session.state()!=SessionState::InWorld||!session.recovered_world_ready()||
           !session.common_world_delivery_current(lease.account,lease.character,lease.generation)||
           session.common_world_entry_current(lease.account,lease.character,lease.generation))return false;
        return presence->retained_ready_current(lease);
    }
    bool ready(Session& session,const Scene::Lease& lease)const{
        if(!retained_ready(session,lease))return false;
        const auto current=presence->ready_lease(session.id(),session.account_id,session.character_id);return current&&*current==lease;
    }
    std::shared_ptr<Version> stage(Configuration config){
        const auto p=config.expected_catalog;const auto& n=config.limits;
        if(p.dataset_id!=NativeMapCatalog::current_dataset_id||p.source_section!="Map_City_Coordniate"||p.loader_rva!="0x59a80"||
           p.lookup_rva!="0x59d80"||!digest_text(p.source_sha256)||!digest_text(p.decoded_sha256)||!digest_text(p.native_image_sha256)||
           p.source_path.empty()||p.row_count<1||config.areas.empty()||config.areas.size()>16||!config.actual_client_directory.is_absolute()||
           !n.hmd_encoded||!n.hmd_plain||!n.rom_encoded||!n.rom_plain||!n.max_cached_maps)
            throw std::invalid_argument("HMD source requires complete explicit catalog/root/limits");
        auto out=std::make_shared<Version>();out->configuration=std::move(config);out->epoch=epoch();
        const auto& root=out->configuration.actual_client_directory;
        out->tree=std::filesystem::weakly_canonical(root/"Data2"/"map");
        auto prefix=ascii_path(root);if(prefix.empty()||prefix.back()!='\\')prefix.push_back('\\');
        constexpr std::string_view map_root="Data2\\map\\";prefix.insert(prefix.end(),map_root.begin(),map_root.end());
        for(const auto& configured:out->configuration.areas){
            if(configured.area<1||configured.area>16||!configured.actual_can_file.is_absolute()||
               !digest_text(configured.expected_can_sha256)||out->areas.contains(configured.area))throw std::invalid_argument("HMD area publication incomplete/duplicate");
            auto base=maps.lookup(p.dataset_id,configured.area,0);if(!base)throw std::invalid_argument("HMD area lacks its actual saved catalog base row");
            auto mdt=base_mdt(*base,p,configured.area);Bytes full=prefix;full.insert(full.end(),mdt.begin(),mdt.end());
            const auto dot=std::find(full.rbegin(),full.rend(),static_cast<std::uint8_t>('.'));
            if(dot==full.rend())throw std::invalid_argument("Map base has no native CAN extension boundary");
            Bytes can_name(full.begin(),dot.base()-1);constexpr std::string_view suffix=".can";can_name.insert(can_name.end(),suffix.begin(),suffix.end());
            auto directory=directory_prefix(full);
            const auto logical_can=byte_path(can_name);
            if(directory.empty()||!contained(out->tree,logical_can)||!contained(out->tree,configured.actual_can_file)||
               !std::filesystem::equivalent(logical_can,configured.actual_can_file))throw std::invalid_argument("Configured CAN is not the base row's exact selected file");
            auto can=TaiwanNativeCanAsset::load_file(configured.actual_can_file,configured.expected_can_sha256);
            if(!can)throw std::invalid_argument("CAN full file/digest/record table rejected");
            auto area=std::make_shared<const Area>(Area{std::move(*base),configured,std::move(*can),std::move(directory),std::move(can_name),epoch()});
            out->areas.emplace(configured.area,std::move(area));
        }
        return out;
    }
    std::shared_ptr<const Bundle> load(const std::shared_ptr<Version>& v,Key key){
        const auto a=v->areas.find(key.first);if(a==v->areas.end())return {};
        const auto area=a->second;const auto* row=area->can.scene(key.second);
        if(!row||(area->configuration.expected_hmd_tag&&row->tag!=*area->configuration.expected_hmd_tag)||!safe_reference(row->reference))return {};
        const auto& limits=v->configuration.limits;const auto& cwd=v->configuration.actual_client_directory;
        auto hmd=select_resource({Selection::Kind::TextFile,row->reference,area->logical_directory,cwd,0},limits.hmd_encoded,v->tree);
        if(!hmd)return {};
        auto asset=TaiwanNativeMapAsset::from_selected_resource(hmd->actual_source(),hmd->encoded_bytes(),limits.hmd_plain);
        if(!asset||asset->rom_references().size()>128)return {};
        auto prefix=directory_prefix(hmd->request_bytes());
        TaiwanNativeSceneResourceOwner::Sources sources{*hmd,epoch(),prefix,{}};
        std::vector<TaiwanNativeMapAsset::RomSlot> roms;
        for(std::size_t i=0;i<asset->rom_references().size();++i){
            const auto& name=asset->rom_references()[i];Bytes raw(name.begin(),name.end());if(!safe_reference(raw))return {};
            auto selected=select_resource({Selection::Kind::RomBinary,raw,prefix,cwd,static_cast<std::uint32_t>(i)},limits.rom_encoded,v->tree);
            if(!selected)return {};
            auto rom=TaiwanNativeRomAsset::from_selected_resource(selected->actual_source(),selected->encoded_bytes(),limits.rom_plain);if(!rom)return {};
            const auto generation=epoch();roms.push_back({i,name,generation,std::move(*rom)});sources.roms.push_back({i,generation,std::move(*selected)});
        }
        auto binding=asset->bind_rom_sources(std::move(roms));if(!binding)return {};
        auto material=binding->compose_material();if(!material)return {};
        auto grid=TaiwanNativeGrid::compose(std::move(*material));if(!grid)return {};
        return std::make_shared<const Bundle>(Bundle{area,key,std::move(sources),std::move(*binding),std::move(*grid),epoch()});
    }
    void prune(){
        for(auto i=entries.begin();i!=entries.end();)if(auto e=i->second.lock();!e||!e->token->current())i=entries.erase(i);else ++i;
    }
    bool in_use(const std::shared_ptr<const Bundle>& b)const{
        for(const auto& [id,weak]:entries)if(auto e=weak.lock();e&&e->token->current()&&e->bundle==b)return true;return false;
    }
    std::shared_ptr<const Bundle> cached(const std::shared_ptr<Version>& v,Key key){
        if(const auto found=v->cache.find(key);found!=v->cache.end())return found->second;
        auto bundle=load(v,key);if(!bundle)return {};
        if(v->cache.size()>=v->configuration.limits.max_cached_maps){
            const auto unused=std::find_if(v->cache.begin(),v->cache.end(),[&](const auto& row){return !in_use(row.second);});
            if(unused==v->cache.end())return {};v->cache.erase(unused);
        }
        v->cache.emplace(key,bundle);return bundle;
    }
    void revoke_all(){for(const auto& [id,weak]:entries)if(auto e=weak.lock())e->token->revoke();entries.clear();}
    bool publish(Configuration config){
        Operation operation(*this);const auto old=version;
        try{
            auto next=stage(std::move(config));
            if(old){
                if(old->cache.size()>next->configuration.limits.max_cached_maps)return false;
                for(const auto& [key,bundle]:old->cache){auto fresh=load(next,key);if(!fresh)return false;next->cache.emplace(key,std::move(fresh));}
            }
            if(closed||reentered||version!=old)return false;
            revoke_all();version=std::move(next);return true;
        }catch(const std::invalid_argument&){return false;}
         catch(const std::filesystem::filesystem_error&){return false;}
    }
    bool current(const std::shared_ptr<Entry>& entry,Scene::Check check,const Scene::Scope& scope,
                 const Scene::Resources& images,const TaiwanNativeSceneResourceOwner::Sources& supplied){
        owner();if(closed)return false;
        Operation operation(*this);affected=entry;const auto peer=entry->session.lock();
        const auto local=[&]{
            const auto at=entries.find(entry->lease.session);const auto map=entry->version->cache.find(entry->bundle->key);
            return peer&&retained_ready(*peer,entry->lease)&&entry->token->current()&&entry->token->owned_by(*peer,entry->lease)&&
                version==entry->version&&at!=entries.end()&&at->second.lock()==entry&&map!=entry->version->cache.end()&&map->second==entry->bundle&&
                peer->battle_generation()==entry->battle&&peer->normal_world_initialization_current_on_game(entry->initialization)&&
                entry_matches(entry->initialization,entry->entry_view,entry->lease)&&scope.lease==entry->lease&&scope.position.area==entry->bundle->key.first&&
                scope.position.scene==entry->bundle->key.second&&scope.direction<=7&&images.complete()&&images.composed_grid&&
                images.actual_resource_generation==entry->prepared->resources().actual_resource_generation&&
                images.actual_initial_scene_generation==entry->prepared->resources().actual_initial_scene_generation&&
                &images.composed_grid->bytes()==&entry->prepared->resources().composed_grid->bytes()&&
                &images.composed_grid->material()==&entry->prepared->resources().composed_grid->material()&&same_sources(supplied,entry->bundle->sources);
        };
        if(!local())return false;
        if(check==Scene::Check::Adopt){
            const Scene::FactoryScope initial{entry->lease,entry->pose.position};
            if(scope.position!=entry->pose.position||scope.direction!=entry->pose.direction||
               !entry->pose.current(*peer,initial,entry->pose.position,entry->pose.direction)||!local())return false;
        }
        // Dynamic pending/saved-after/pose qualification belongs to the actual
        // ResourceOwner and its sole position CAS. BeforePublish is not a new
        // pose supplier or permission grant here.
        return local();
    }
    std::optional<Input> read(Session& session,const Scene::FactoryScope& scope,
                             const std::shared_ptr<TaiwanNativeSceneSourceLifetime>& token){
        Operation operation(*this);prune();const auto v=version;const auto peer=session.weak_from_this().lock();
        if(!v||!peer||!ready(session,scope.lease)||scope.saved_position.area!=scope.lease.position.area||
           scope.saved_position.scene!=scope.lease.position.scene||presence->saved_position(scope.lease)!=std::optional{scope.saved_position})return {};
        const auto found=entries.find(session.id());const auto previous=found==entries.end()?std::shared_ptr<Entry>{}:found->second.lock();affected=previous;
        if(!previous&&entries.size()>=capacity)return {};
        const auto initial=session.normal_world_initialization_on_game();if(!initial)return {};
        const auto entry_view=RecoveredWorldEntryView::read(initial->entry_frame());
        if(!entry_view||!entry_matches(*initial,*entry_view,scope.lease))return {};
        const auto battle=session.battle_generation();
        auto pose=pose_source(session,scope);
        const auto local=[&]{return !closed&&!reentered&&version==v&&ready(session,scope.lease)&&token->current()&&
            token->owned_by(session,scope.lease)&&session.battle_generation()==battle&&session.normal_world_initialization_current_on_game(*initial)&&
            presence->saved_position(scope.lease)==std::optional{scope.saved_position};};
        if(!pose||pose->position!=scope.saved_position||pose->direction>7||!pose->current||!local()||
           !pose->current(session,scope,pose->position,pose->direction)||!local())return {};
        const Key key{scope.saved_position.area,scope.saved_position.scene};auto bundle=cached(v,key);
        if(!bundle||!local()||!pose->current(session,scope,pose->position,pose->direction)||!local())return {};
        const auto scene_epoch=epoch();
        Scene::Resources images{{0,{}},{},{},bundle->epoch,scene_epoch,bundle->grid};
        auto prepared=TaiwanNativeHmdBundleSource::prepared(bundle->sources,bundle->binding,std::move(images),token,v->configuration.limits);
        auto entry=std::make_shared<Entry>(Entry{peer,scope.lease,*initial,*entry_view,battle,v,bundle,std::move(*pose),token,prepared});affected=entry;
        Input input{bundle->sources,v->configuration.limits.hmd_plain,v->configuration.limits.rom_plain,bundle->epoch,scene_epoch,
            scope.saved_position,entry->pose.direction,{},{},{},token,prepared};
        const auto self=shared_from_this();input.current=[self,entry](auto check,const auto& supplied_scope,const auto& resources,const auto& sources){
            return self->current(entry,check,supplied_scope,resources,sources);
        };
        // Preallocate publication before retiring any existing supply.
        std::map<std::uint64_t,std::weak_ptr<Entry>> staging;staging.emplace(session.id(),entry);auto node=staging.extract(session.id());
        if(!local())return {};
        if(previous)previous->token->revoke();entries.erase(session.id());entries.insert(std::move(node));
        return input;
    }
    void shutdown(){
        owner();closed=true;if(busy)reentered=true;revoke_all();version.reset();
    }
    ~State(){if(thread!=std::this_thread::get_id())std::terminate();}
};
TaiwanNativeHmdBundleSource::TaiwanNativeHmdBundleSource(std::shared_ptr<State> state):state_(std::move(state)){}
TaiwanNativeHmdBundleSource::PoseSource TaiwanNativeHmdBundleSource::initial_entry_pose_source(
        std::shared_ptr<SharedWorldPresence> presence){
    if(!presence)throw std::invalid_argument("Initial entry pose requires actual common presence");
    const auto thread=std::this_thread::get_id();
    return [presence=std::move(presence),thread](Session& session,const Scene::FactoryScope& scope)->std::optional<InitialPose>{
        if(thread!=std::this_thread::get_id())throw std::logic_error("Initial entry pose game owner mismatch");
        const auto peer=session.weak_from_this().lock();const auto initial=session.normal_world_initialization_on_game();
        if(!peer||!initial||scope.saved_position!=scope.lease.position||!initial->original_entry_battle_phase())return {};
        const auto view=RecoveredWorldEntryView::read(initial->entry_frame());
        if(!view||!entry_matches(*initial,*view,scope.lease))return {};
        const auto direction=view->entry_movement_direction();
        const auto weak=std::weak_ptr<Session>(peer);const auto lease=scope.lease;const auto position=scope.saved_position;
        const auto retained=[presence,weak,thread,initial=*initial,view=*view,lease,position,direction](
                Session& actual,const Scene::FactoryScope& current,const RecoveredPosition& saved,std::uint8_t facing){
            if(thread!=std::this_thread::get_id())throw std::logic_error("Initial entry pose Current owner mismatch");
            return weak.lock().get()==&actual&&current.lease==lease&&current.saved_position==position&&saved==position&&facing==direction&&
                actual.id()==lease.session&&actual.account_id==lease.account&&actual.character_id==lease.character&&!actual.closing()&&
                actual.state()==SessionState::InWorld&&actual.recovered_world_ready()&&initial.original_entry_battle_phase()&&
                actual.normal_world_initialization_current_on_game(initial)&&entry_matches(initial,view,lease)&&
                actual.common_world_delivery_current(lease.account,lease.character,lease.generation)&&
                !actual.common_world_entry_current(lease.account,lease.character,lease.generation)&&presence->retained_ready_current(lease);
        };
        // Only supply performs a real saved-position read. Held Current never
        // calls ready_lease/saved_position, which may enter the repository.
        if(!retained(session,scope,position,direction)||presence->saved_position(lease)!=std::optional{position}||
           !retained(session,scope,position,direction))return {};
        return InitialPose{position,direction,retained};
    };
}
std::shared_ptr<TaiwanNativeHmdBundleSource> TaiwanNativeHmdBundleSource::create(const NativeMapCatalog& maps,
        std::shared_ptr<SharedWorldPresence> presence,std::size_t capacity,Configuration config,PoseSource pose){
    if(!presence||!capacity||!pose)throw std::invalid_argument("HMD bundle requires actual common host, capacity and pose supplier");
    auto state=std::make_shared<State>(maps,std::move(presence),capacity,std::move(pose));
    if(!state->publish(std::move(config)))throw std::invalid_argument("HMD bundle initial whole publication rejected");
    return std::shared_ptr<TaiwanNativeHmdBundleSource>(new TaiwanNativeHmdBundleSource(std::move(state)));
}
TaiwanNativeHmdBundleSource::~TaiwanNativeHmdBundleSource(){state_->shutdown();}
std::shared_ptr<TaiwanNativeSceneSourceLifetime> TaiwanNativeHmdBundleSource::lifetime(const std::shared_ptr<Session>& peer,const Scene::Lease& lease){
    return std::shared_ptr<TaiwanNativeSceneSourceLifetime>(new TaiwanNativeSceneSourceLifetime(peer,lease));
}
std::shared_ptr<const TaiwanNativeHmdPreparedBundle> TaiwanNativeHmdBundleSource::prepared(
        TaiwanNativeSceneResourceOwner::Sources sources,TaiwanNativeMapAsset::RomBound binding,Scene::Resources images,
        std::shared_ptr<TaiwanNativeSceneSourceLifetime> token,const Limits& limits){
    return std::shared_ptr<const TaiwanNativeHmdPreparedBundle>(new TaiwanNativeHmdPreparedBundle(
        std::move(sources),std::move(binding),std::move(images),std::move(token),limits.hmd_plain,limits.rom_plain));
}
std::optional<TaiwanNativeHmdBundleSource::Input> TaiwanNativeHmdBundleSource::read(Session& session,const Scene::FactoryScope& scope){
    const auto state=state_;state->owner();const auto peer=session.weak_from_this().lock();if(!peer)return {};
    auto token=lifetime(peer,scope.lease);
    try{auto out=state->read(session,scope,token);if(!out)token->revoke();return out;}catch(...){token->revoke();throw;}
}
SharedTaiwanNativeMovementHost::InputSource TaiwanNativeHmdBundleSource::input_source(){
    const auto self=shared_from_this();state_->owner();return [self](Session& session,const Scene::FactoryScope& scope){return self->read(session,scope);};
}
bool TaiwanNativeHmdBundleSource::publish(Configuration config){return state_->publish(std::move(config));}
void TaiwanNativeHmdBundleSource::stop(){state_->shutdown();}
}
