from pathlib import Path
import json,hashlib,struct,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server')
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013')
D=A/'round359-common-skill-definition-implementation'
R=A/'round358-skills-raw-three-source-audit'
H=lambda b:hashlib.sha256(b).hexdigest()
def writej(p,v): p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
existing=['src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/scripting/LuaEngine.h','src/scripting/LuaEngine.cpp','src/core/Application.cpp','src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp','src/cn/world/CnPrebornSkillChoiceSource.h','src/cn/world/CnPrebornSkillChoiceSource.cpp']
newpaths=['src/db/NativeSkillSource.h','src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp']
before={p:(S/p).read_bytes() for p in existing}
for p,b in before.items():
 head=subprocess.run(['git','show','8520e6330e32631df630fecc46204f040a6f911a:'+p],cwd=S,capture_output=True,check=True).stdout
 assert b==head,(p,'baseline differs')
 q=D/'before'/p; q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(b)
for p in newpaths: assert not (S/p).exists(),p
plans=dict(before); changes=[]
def edit(p,old,new,count=1):
 b=plans[p]; old=old.replace('\r\n','\n'); new=new.replace('\r\n','\n')
 pairs=[]
 for nl in ['\r\n','\n']:
  x=old.replace('\n',nl).encode(); y=new.replace('\n',nl).encode()
  if not any(prior[0]==x for prior in pairs): pairs.append((x,y))
 found=[(x,y,b.count(x)) for x,y in pairs if b.count(x)]
 assert sum(z for x,y,z in found)==count,(p,old[:90],[(z) for x,y,z in found])
 for x,y,z in found:
  plans[p]=plans[p].replace(x,y); changes.append({'path':p,'old_hex':x.hex(),'new_hex':y.hex(),'count':z})
def add(p,text): assert p not in plans; plans[p]=text.encode('utf-8')

src=before['src/db/NativeSkillCatalog.h'].decode('utf-8')
start=src.index('struct NativeSkillSource {'); end=src.index('\n\r\nstruct NativeSkillRecord',start) if '\n\r\nstruct NativeSkillRecord' in src[start:] else src.index('\n\nstruct NativeSkillRecord',start)
source_struct=src[start:end].rstrip('\r\n')
edit('src/db/NativeSkillCatalog.h',source_struct+'\n\n','// Source value moved unchanged to NativeSkillSource.h.\n\n')
edit('src/db/NativeSkillCatalog.h','#pragma once\n','#pragma once\n\n#include "db/NativeSkillSource.h"\n#include "db/SharedSkillDefinition.h"\n')
add('src/db/NativeSkillSource.h','#pragma once\n#include <cstdint>\n#include <string>\n\nnamespace god2 {\n'+source_struct.replace('\r\n','\n')+'\n}\n')
add('src/db/SharedSkillDefinition.h',r'''#pragma once
#include "db/NativeSkillSource.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace god2 {
enum class SharedSkillRegion { Taiwan, China };
enum class SharedSkillRowQualification { MetadataSnapshotOnly, OriginalRowPinned, OwnerRowPinned };
enum class SharedSkillStatus {
    SingleProfile, VerifiedEqualPayload, BorrowedCNReserve, CNPopulatedTWEmpty,
    OwnerSelectedTWCompleteConflict, UnresolvedRegionalProfiles, OwnerCustom
};
// Owning definition data, never a native Current/learning/casting capability.
// row_digest_verified records the explicit reader's recomputed110-byte digest;
// only the resolver's exact per-row pin comparison promotes row qualification.
struct SharedSkillNativeBinding {
    SharedSkillRegion region;
    NativeSkillSource source;
    std::int64_t source_record_index=0,source_offset=0;
    std::string record_sha256;
    std::array<std::uint8_t,110> raw{};
    bool row_digest_verified=false;
    SharedSkillRowQualification qualification=SharedSkillRowQualification::MetadataSnapshotOnly;
    bool operator==(const SharedSkillNativeBinding&) const=default;
};
struct SharedSkillTextProjection {
    std::optional<std::size_t> profile_index;
    std::uint16_t offset=0,limit_exclusive=0;
    std::string encoding;
    std::vector<std::uint8_t> bounded_raw;
    std::string source_utf8,traditional_utf8;
    // A bounded pinned source literal, not a recovered native UI field width.
    bool pinned_literal=false;
    bool operator==(const SharedSkillTextProjection&) const=default;
};
struct SharedSkillDefinition {
    // Stable registry/native-binding key. A common identity does not assert
    // equal native effects. Original regional keys and full records remain.
    std::uint16_t canonical_key=0;
    SharedSkillStatus status=SharedSkillStatus::UnresolvedRegionalProfiles;
    std::vector<SharedSkillNativeBinding> profiles;
    // Owner-selected complete parameter base only; not a damage formula,
    // native eligibility, server debit, bank population or entitlement.
    std::optional<std::size_t> chosen_profile;
    SharedSkillTextProjection name,short_text;
    bool operator==(const SharedSkillDefinition&) const=default;
};
const char* shared_skill_status_name(SharedSkillStatus) noexcept;
const char* shared_skill_qualification_name(SharedSkillRowQualification) noexcept;
// Pure owning value composition. Selected-row pins do not attest a loaded
// whole file or observed native bank. Unknown source snapshots stay explicit.
SharedSkillDefinition resolve_shared_skill_definition(std::uint8_t kind,std::uint8_t id,
    std::optional<SharedSkillNativeBinding> taiwan,std::optional<SharedSkillNativeBinding> china);
}
''')
edit('src/db/NativeSkillCatalog.h','// Original definition identities/raw bytes and a verified client-only MP threshold.',r'''// New explicit result only. Original NativeSkillRecord/equality and all old
// lookups are unchanged; absence of the requested TW raw row remains visible.
struct SharedSkillLookup {
    std::optional<NativeSkillRecord> requested_native;
    SharedSkillDefinition definition;
    bool operator==(const SharedSkillLookup&) const=default;
};

// Original definition identities/raw bytes and a verified client-only MP threshold.''')
edit('src/db/NativeSkillCatalog.h','private:\n    std::optional<NativeSkillRecord> lookup_impl',r'''    // One main-schema DB read view over both original dataset selectors.
    // Missing counterparts remain missing; no import, grant or native Current.
    std::optional<SharedSkillLookup> lookup_shared_definition_main(
        std::int64_t kind,std::int64_t definition_id) const;

private:
    std::optional<NativeSkillRecord> lookup_impl''')
# Independently read only already-sealed raw sources; never import a product decoder.
refs=json.loads((R/'source-references.json').read_text(encoding='utf-8'))
sources={}
for ref in refs:
 b=(R/ref['retained']).read_bytes(); assert len(b)==ref['bytes'] and H(b)==ref['sha256']
 sources[ref['label']]=(b,ref)
# Source-only Traditional display projection uses the existing retained OpenCC
# dictionaries' literal longest-match mappings; does not execute ChineseText.
dicts={}; dictrefs=[]
for name in ['STPhrases.txt','STCharacters.txt']:
 p=S/'resources/opencc'/name; b=p.read_bytes()
 dictrefs.append({'actual_path':str(p).replace('\\','/'),'bytes':len(b),'sha256':H(b)})
 for line in b.decode('utf-8').splitlines():
  if not line:continue
  key,value=line.split('\t',1); value=value.split(' ',1)[0]
  dicts.setdefault(key,value)
keys=sorted(dicts,key=len,reverse=True)
by_first={}
for key in keys:by_first.setdefault(key[0],[]).append(key)
def traditional(t):
 out=[]; at=0
 while at<len(t):
  found=next((k for k in by_first.get(t[at],[]) if t.startswith(k,at)),None)
  if found: out.append(dicts[found]);at+=len(found)
  else:out.append(t[at]);at+=1
 return ''.join(out)
def cstr(s): return json.dumps(s,ensure_ascii=True)
pins=[]; pinproof=[]
for label,region,encoding in [('tw_original','Taiwan','cp950'),('cn_original','China','cp936')]:
 b,ref=sources[label]; counts=ref['counts']; ordinal=0
 for k,n in enumerate(counts):
  for i in range(1,n+1):
   off=8+k*0x6e04+(i-1)*110; raw=b[off:off+110];assert len(raw)==110 and raw[:2]==bytes([i,k])
   names=[]
   for lo,hi in [(2,32),(32,62)]:
    field=raw[lo:hi];assert 0 in field
    text=field.split(b'\0',1)[0].decode(encoding,errors='strict'); names.extend([text,text if region=='Taiwan' else traditional(text)])
   pins.append((region,k,i,ordinal,off,H(raw),ref['sha256'],sum(counts),names))
   pinproof.append({'source':label,'kind':k,'id':i,'ordinal':ordinal,'offset':off,'sha256':H(raw),'name':names[0],'traditional_name':names[1],'short':names[2],'traditional_short':names[3]})
   ordinal+=1
assert len(pins)==901
# Five installed owner-added records have separate owner provenance.
b,ref=sources['tw_installed']
for i in range(122,127):
 raw=b[8+(i-1)*110:8+i*110];names=[]
 for lo,hi in [(2,32),(32,62)]:
  text=raw[lo:hi].split(b'\0',1)[0].decode('cp950');names.extend([text,text])
 pins.append(('Taiwan',0,i,i-1,8+(i-1)*110,H(raw),ref['sha256'],453,names))
# Existing CUSTOM0059 candidate is a separate source, never installed/CN453.
candidate=json.loads((A/'round359-native-skill-text-common-source-plan/custom150-candidate-fullrecord-reference.json').read_text(encoding='utf-8'))
raw150=(A/'round359-native-skill-text-common-source-plan/retained-custom150-record.bin').read_bytes()
assert len(raw150)==110 and raw150[:2]==bytes([150,0])
names=[]
for lo,hi in [(2,32),(32,62)]:
 text=raw150[lo:hi].split(b'\0',1)[0].decode('cp950');names.extend([text,text])
pins.append(('Taiwan',0,150,149,8+149*110,H(raw150),'f159b61f0aeacc46e71519cd6e98910381eda22336ad07487b2cf7213ec6297d',477,names))
table=[]
for reg,k,i,ordinal,off,sha,source,count,names in pins:
 table.append('    {SharedSkillRegion::'+reg+','+str(k)+','+str(i)+','+str(ordinal)+','+str(off)+','+cstr(sha)+','+cstr(source)+','+str(count)+','+','.join(cstr(x) for x in names)+'},')
cpp=r'''#include "db/SharedSkillDefinition.h"
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
// Independently retained original TW448/CN453 row digests and literal text.
// Owner-added TW records are separate pins, never original native rows.
// Name2..20h / short20h..3Eh is bounded source policy, not UI-width proof.
struct Pin {
    SharedSkillRegion region;std::uint8_t kind,id;
    std::int64_t ordinal,offset;
    const char* digest;const char* source_digest;std::int64_t row_count;
    const char* name;const char* traditional_name;const char* short_text;const char* traditional_short;
};
const Pin pins[]={
'''+'\n'.join(table)+r'''
};
const Pin* qualify(SharedSkillNativeBinding& b,std::uint8_t kind,std::uint8_t id) {
    if(!b.row_digest_verified || b.raw[0]!=id || b.raw[1]!=kind ||
       b.source.source_sha256!=b.source.decoded_sha256)return nullptr;
    for(const auto& p:pins) {
        if(p.region!=b.region || p.kind!=kind || p.id!=id ||
           b.source.source_sha256!=p.source_digest || b.record_sha256!=p.digest ||
           b.source.row_count!=p.row_count || b.source_record_index!=p.ordinal ||
           b.source_offset!=p.offset)continue;
        const bool original=b.source.source_sha256==
            (b.region==SharedSkillRegion::Taiwan?
            "7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51":
            "857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004");
        if(original && b.source.native_image_sha256!=
            (b.region==SharedSkillRegion::Taiwan?
            "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763":
            "582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8"))return nullptr;
        b.qualification=original?SharedSkillRowQualification::OriginalRowPinned:
            SharedSkillRowQualification::OwnerRowPinned;
        return &p;
    }
    return nullptr;
}
bool pinned(const SharedSkillNativeBinding& b) {
    return b.qualification!=SharedSkillRowQualification::MetadataSnapshotOnly;
}
SharedSkillTextProjection text(const SharedSkillDefinition& d,std::size_t n,
    const Pin* pin,bool short_text) {
    const auto& b=d.profiles[n];SharedSkillTextProjection value;
    value.profile_index=n;value.offset=short_text?32:2;value.limit_exclusive=short_text?62:32;
    value.encoding=b.region==SharedSkillRegion::Taiwan?"CP950":"CP936";
    value.bounded_raw.assign(b.raw.begin()+value.offset,b.raw.begin()+value.limit_exclusive);
    // Unknown snapshots are retained but never decoded using a guessed width.
    if(pin) {
        value.pinned_literal=true;
        value.source_utf8=short_text?pin->short_text:pin->name;
        value.traditional_utf8=short_text?pin->traditional_short:pin->traditional_name;
    }
    return value;
}
}
const char* shared_skill_status_name(SharedSkillStatus s) noexcept {
    switch(s) {
    case SharedSkillStatus::SingleProfile:return "SingleProfile";
    case SharedSkillStatus::VerifiedEqualPayload:return "VerifiedEqualPayload";
    case SharedSkillStatus::BorrowedCNReserve:return "BorrowedCNReserve";
    case SharedSkillStatus::CNPopulatedTWEmpty:return "CNPopulatedTWEmpty";
    case SharedSkillStatus::OwnerSelectedTWCompleteConflict:return "OwnerSelectedTWCompleteConflict";
    case SharedSkillStatus::OwnerCustom:return "OwnerCustom";
    default:return "UnresolvedRegionalProfiles";
    }
}
const char* shared_skill_qualification_name(SharedSkillRowQualification q) noexcept {
    switch(q) {
    case SharedSkillRowQualification::OriginalRowPinned:return "OriginalRowPinned";
    case SharedSkillRowQualification::OwnerRowPinned:return "OwnerRowPinned";
    default:return "MetadataSnapshotOnly";
    }
}
SharedSkillDefinition resolve_shared_skill_definition(std::uint8_t kind,std::uint8_t id,
    std::optional<SharedSkillNativeBinding> tw,std::optional<SharedSkillNativeBinding> cn) {
    if(kind>3 || !id)throw std::invalid_argument("Invalid shared skill selector");
    SharedSkillDefinition d;d.canonical_key=static_cast<std::uint16_t>((unsigned(kind)<<8)|id);
    std::optional<std::size_t> t,c;std::vector<const Pin*> matched;
    if(tw) {t=d.profiles.size();matched.push_back(qualify(*tw,kind,id));d.profiles.push_back(std::move(*tw));}
    if(cn) {c=d.profiles.size();matched.push_back(qualify(*cn,kind,id));d.profiles.push_back(std::move(*cn));}
    const bool tp=t && pinned(d.profiles[*t]),cp=c && pinned(d.profiles[*c]);
    if(kind==0 && id>=122 && id<=125 && cp &&
       (!t || (tp && d.profiles[*t].qualification==SharedSkillRowQualification::OwnerRowPinned))) {
        d.status=SharedSkillStatus::BorrowedCNReserve;d.chosen_profile=c;
    } else if(kind==1 && id==83 && tp && cp) {
        // Explicit independently pinned owner selection, not a zero heuristic.
        d.status=SharedSkillStatus::CNPopulatedTWEmpty;d.chosen_profile=c;
    } else if(kind==0 && (id==126 || id==150) && tp &&
              d.profiles[*t].qualification==SharedSkillRowQualification::OwnerRowPinned) {
        d.status=SharedSkillStatus::OwnerCustom;d.chosen_profile=t;
    } else if(tp && cp) {
        d.chosen_profile=t; // Owner: TW complete common base, original CN retained.
        if((kind==0 && id==95) || (kind==1 && id==129))
            d.status=SharedSkillStatus::OwnerSelectedTWCompleteConflict;
        else if(std::equal(d.profiles[*t].raw.begin()+62,d.profiles[*t].raw.end(),
                           d.profiles[*c].raw.begin()+62))
            d.status=SharedSkillStatus::VerifiedEqualPayload; // Physical50 only, not formula equality.
        else d.status=SharedSkillStatus::UnresolvedRegionalProfiles;
    } else if(tp || cp) {
        d.status=SharedSkillStatus::SingleProfile;d.chosen_profile=tp?t:c;
    } else d.status=d.profiles.size()==1?SharedSkillStatus::SingleProfile:
        SharedSkillStatus::UnresolvedRegionalProfiles;
    // Text selection is independent of common numeric selection: nonempty
    // pinned Traditional TW first; then pinned CN literal converted for display.
    for(bool short_text:{false,true}) {
        std::optional<std::size_t> selected;
        for(const auto candidate:{t,c})
            if(candidate && matched[*candidate] &&
               *(short_text?matched[*candidate]->short_text:matched[*candidate]->name)) {
                selected=candidate;break;
            }
        if(!selected)selected=t?t:c;
        if(selected) {
            auto value=text(d,*selected,matched[*selected],short_text);
            if(short_text)d.short_text=std::move(value);else d.name=std::move(value);
        }
    }
    return d;
}
}
'''
add('src/db/SharedSkillDefinition.cpp',cpp)
# New read snapshot only on explicit common API.
edit('src/db/NativeSkillCatalog.cpp','}\n\nNativeSkillCatalog::NativeSkillCatalog',r'''struct SharedReadScope {
    sqlite3* db;bool owned,finished=false;
    explicit SharedReadScope(sqlite3* value):db(value),owned(sqlite3_get_autocommit(db)!=0) {
        if(owned)sqlite_detail::execute(db,"BEGIN");
    }
    SharedReadScope(const SharedReadScope&)=delete;
    SharedReadScope& operator=(const SharedReadScope&)=delete;
    ~SharedReadScope(){if(owned && !finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owned)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
SharedSkillNativeBinding shared_binding(const NativeSkillRecord& r,SharedSkillRegion region) {
    if(r.raw_record.size()!=110)throw DatabaseError("Invalid shared skill raw record");
    SharedSkillNativeBinding b;b.region=region;b.source=r.source;
    b.source_record_index=r.source_record_index;b.source_offset=r.source_offset;
    b.record_sha256=r.record_sha256;std::copy(r.raw_record.begin(),r.raw_record.end(),b.raw.begin());
    b.row_digest_verified=record_digest_matches(r);return b;
}
}

NativeSkillCatalog::NativeSkillCatalog''')
edit('src/db/NativeSkillCatalog.cpp','std::optional<NativeSkillSource> NativeSkillCatalog::lookup_main_source',r'''std::optional<SharedSkillLookup> NativeSkillCatalog::lookup_shared_definition_main(
    std::int64_t kind,std::int64_t definition_id) const {
    // Existing joined reads validate selectors and corrupt rows even on this
    // explicit path. A missing CN counterpart never drops a valid TW snapshot.
    SharedReadScope scope(db_);
    auto tw=lookup_main(current_dataset_id,kind,definition_id);
    auto cn=lookup_main("cn-native-cbspec2-582f2695-857b52e3-v1",kind,definition_id);
    if(!tw && !cn){scope.finish();return std::nullopt;}
    std::optional<SharedSkillNativeBinding> t,c;
    if(tw)t=shared_binding(*tw,SharedSkillRegion::Taiwan);
    if(cn)c=shared_binding(*cn,SharedSkillRegion::China);
    SharedSkillLookup value{tw,resolve_shared_skill_definition(
        static_cast<std::uint8_t>(kind),static_cast<std::uint8_t>(definition_id),std::move(t),std::move(c))};
    scope.finish();return value;
}
std::optional<NativeSkillSource> NativeSkillCatalog::lookup_main_source''')
edit('src/cn/assets/CnSharedSkillCatalog.h','    std::optional<Record> lookup(std::uint8_t kind,std::uint8_t id) const;',r'''    std::optional<Record> lookup(std::uint8_t kind,std::uint8_t id) const;
    // Actual private native/source qualification first; same common resolver
    // then supplies owning definition metadata. Original lookups stay exact.
    std::optional<SharedSkillLookup> lookup_shared(std::uint8_t kind,std::uint8_t id) const;''')
edit('src/cn/assets/CnSharedSkillCatalog.cpp','std::optional<std::vector<CnSharedSkillCatalog::Record>> CnSharedSkillCatalog::lookup_words',r'''std::optional<SharedSkillLookup> CnSharedSkillCatalog::lookup_shared(
    std::uint8_t kind,std::uint8_t id) const {
    Operation operation(*this);
    auto actual=retained_lookup(kind,id);
    if(!actual || !observe())return std::nullopt;
    auto common=shared_.lookup_shared_definition_main(kind,id);
    if(!observe()){terminal_=true;return std::nullopt;}
    if(!common){terminal_=true;return std::nullopt;}
    const auto found=std::find_if(common->definition.profiles.begin(),common->definition.profiles.end(),
        [](const auto& b){return b.region==SharedSkillRegion::China;});
    if(found==common->definition.profiles.end() || found->source!=actual->source ||
       found->source_record_index!=actual->source_record_index || found->source_offset!=actual->source_offset ||
       found->record_sha256!=actual->record_sha256 ||
       !std::equal(found->raw.begin(),found->raw.end(),actual->raw_record.begin(),actual->raw_record.end())) {
        terminal_=true;return std::nullopt;
    }
    // Requested native remains the exact qualified CN original, never the
    // selected common TW parameter profile or an invented TW source row.
    common->requested_native=std::move(actual);
    if(!observe()){terminal_=true;return std::nullopt;}return common;
}
std::optional<std::vector<CnSharedSkillCatalog::Record>> CnSharedSkillCatalog::lookup_words''')
edit('src/cn/world/CnPrebornSkillChoiceSource.h','        std::vector<Entry> entries;\n',r'''        std::vector<Entry> entries;
        // Owning same-registry metadata for actual apply/qualify callbacks.
        // Original raw definitions and native permission facts stay separate;
        // these snapshots survive commit without calling obsolete Current.
        std::vector<SharedSkillDefinition> common_definitions;
''')
edit('src/cn/world/CnPrebornSkillChoiceSource.cpp','    if(subject) {\n',r'''    result.facts.common_definitions.reserve(result.definitions.size());
    for(const auto& original:result.definitions) {
        auto common=catalog.lookup_shared(static_cast<std::uint8_t>(original.kind),
            static_cast<std::uint8_t>(original.definition_id));
        if(!common || !common->requested_native || *common->requested_native!=original)return std::nullopt;
        result.facts.common_definitions.push_back(std::move(common->definition));
    }
    if(subject) {
''')
# Lua optional provider last, including active and reload VMs.
edit('src/scripting/LuaEngine.h','    using NativeArmorLookup',r'''    using SharedSkillLookupFunction=std::function<std::optional<SharedSkillLookup>(
        std::int64_t kind,std::int64_t definition_id)>;
    using NativeArmorLookup''')
edit('src/scripting/LuaEngine.h','                       NativeArmorLookup native_armor_lookup = {});','                       NativeArmorLookup native_armor_lookup = {},\n                       SharedSkillLookupFunction common_skill_lookup = {});')
edit('src/scripting/LuaEngine.h','    const std::shared_ptr<const NativeArmorLookup> native_armor_lookup_;','    const std::shared_ptr<const NativeArmorLookup> native_armor_lookup_;\n    const std::shared_ptr<const SharedSkillLookupFunction> common_skill_lookup_;')
edit('src/scripting/LuaEngine.cpp','sol::table catalog_snapshot(sol::state_view lua, const NativeSkillBookRecord& record)',r'''sol::table common_skill_snapshot(sol::state_view lua,const SharedSkillLookup& value) {
    const auto& d=value.definition;
    auto profiles=lua.create_table();
    for(std::size_t n=0;n<d.profiles.size();++n) {
        const auto& b=d.profiles[n];
        profiles[n+1]=lua.create_table_with(
            "region",b.region==SharedSkillRegion::Taiwan?"TW":"CN",
            "source",catalog_provenance(lua,b.source),
            "source_record_index",b.source_record_index,"source_offset",b.source_offset,
            "record_sha256",b.record_sha256,"row_qualification",shared_skill_qualification_name(b.qualification),
            "raw_record",std::string(b.raw.begin(),b.raw.end()),
            "raw_word_42",unsigned(b.raw[0x42])|(unsigned(b.raw[0x43])<<8));
    }
    const auto text=[&](const SharedSkillTextProjection& t) {
        auto result=lua.create_table_with("offset",t.offset,"limit_exclusive",t.limit_exclusive,
            "encoding",t.encoding,"bounded_raw",std::string(t.bounded_raw.begin(),t.bounded_raw.end()),
            "source_utf8",t.source_utf8,"traditional_utf8",t.traditional_utf8,
            "bounded_source_literal",t.pinned_literal,"native_ui_width_qualified",false);
        if(t.profile_index)result["profile_index"]=*t.profile_index+1;return result;
    };
    auto result=lua.create_table_with("canonical_key",d.canonical_key,
        "status",shared_skill_status_name(d.status),"profiles",profiles,
        "name",text(d.name),"short_text",text(d.short_text),"gameplay_authority",false,
        "requested_native_present",value.requested_native.has_value());
    if(value.requested_native)result["requested_native"]=catalog_snapshot(lua,*value.requested_native);
    if(d.chosen_profile) {
        result["chosen_profile"]=*d.chosen_profile+1;
        const auto& raw=d.profiles[*d.chosen_profile].raw;
        result["common_raw_profile"]=std::string(raw.begin(),raw.end());
        result["physical_parameter_tail"]=std::string(raw.begin()+62,raw.end());
    }
    return result;
}

sol::table catalog_snapshot(sol::state_view lua, const NativeSkillBookRecord& record)''')
edit('src/scripting/LuaEngine.cpp','       std::shared_ptr<const NativeArmorLookup> native_armor_lookup) : root', '       std::shared_ptr<const NativeArmorLookup> native_armor_lookup,\n       std::shared_ptr<const SharedSkillLookupFunction> common_skill_lookup) : root')
edit('src/scripting/LuaEngine.cpp','        lua.set_function("native_skill_book_catalog"',r'''        lua.set_function("common_skill_definition",[lookup=std::move(common_skill_lookup)](
                sol::this_state state,sol::variadic_args args)->sol::object {
            if(args.size()!=2)throw std::runtime_error("common_skill_definition requires kind and definition_id");
            const auto kind=catalog_selector(args.get<sol::object>(0),0,3,"common_skill_definition");
            const auto id=catalog_selector(args.get<sol::object>(1),1,255,"common_skill_definition");
            if(!*lookup)throw std::runtime_error("common_skill_definition unavailable");
            const auto value=(*lookup)(kind,id);sol::state_view lua(state);
            if(!value)return sol::make_object(lua,sol::nil);
            return sol::make_object(lua,common_skill_snapshot(lua,*value));
        });
        lua.set_function("native_skill_book_catalog"''')
edit('src/scripting/LuaEngine.cpp','                     NativeArmorLookup native_armor_lookup)\n','                     NativeArmorLookup native_armor_lookup,\n                     SharedSkillLookupFunction common_skill_lookup)\n')
edit('src/scripting/LuaEngine.cpp','      native_armor_lookup_(std::make_shared<const NativeArmorLookup>(std::move(native_armor_lookup))) {}','      native_armor_lookup_(std::make_shared<const NativeArmorLookup>(std::move(native_armor_lookup))),\n      common_skill_lookup_(std::make_shared<const SharedSkillLookupFunction>(std::move(common_skill_lookup))) {}')
edit('src/scripting/LuaEngine.cpp','native_skill_book_lookup_,native_weapon_lookup_,native_armor_lookup_);','native_skill_book_lookup_,native_weapon_lookup_,native_armor_lookup_,common_skill_lookup_);',2)
edit('src/core/Application.cpp','                [&database](std::uint16_t item){return database.native_armor_catalog().lookup(item);});',r'''                [&database](std::uint16_t item){return database.native_armor_catalog().lookup(item);},
                [&database](std::int64_t kind,std::int64_t definition_id) {
                    return database.native_skill_catalog().lookup_shared_definition_main(kind,definition_id);
                });''')

# Preflight every inverse and source plan before the only tracked mutation.
proof=[]
for p in existing:
 value=plans[p]
 for change in reversed([v for v in changes if v['path']==p]):
  old=bytes.fromhex(change['old_hex']);new=bytes.fromhex(change['new_hex'])
  assert value.count(new)==change['count'],(p,'inverse multiplicity',new[:90])
  value=value.replace(new,old)
 assert value==before[p],(p,'inverse failed')
for p,b in plans.items():
 q=D/'candidate'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 proof.append({'path':p,'new_file':p in newpaths,'before_bytes':len(before[p]) if p in before else None,
  'before_sha256':H(before[p]) if p in before else None,'bytes':len(b),'sha256':H(b)})
writej(D/'source-pin-generation-proof.json',{'raw_package':str(R),'original_rows':901,'owner_rows':6,'pins':pinproof,'dictionary_references':dictrefs,'scope':'static raw uncompressed record reads and bounded literal projection; no decoder/native/API/SQL execution'})
writej(D/'scope-amendment.json',{'supersedes':'sealed source-plan optional NativeSkillRecord field / unresolved null-selection recommendation',
 'result':'separate SharedSkillLookup; old native source/raw/equality/defaultlookups unchanged',
 'selection':'owner TW complete default including0/95 and1/129 conflict; CN1/83 and four CN0/122..125 reserve borrows',
 'actual_handoffs':['Main Lua common_skill_definition END provider','CN preborn Facts owning common_definitions'],
 'permissions':'no skill grants/cast rule/MP debit/activation/import'})
writej(D/'exact-edits-and-inverse.json',{'baseline':'8520e6330e32631df630fecc46204f040a6f911a','edits':changes,'files':proof,'inverse_pass':True,'new_files_contained':newpaths})
# Confirm all nine current files remain frozen and all three destinations absent.
for p,b in before.items():assert (S/p).read_bytes()==b,p
for p in newpaths:assert not (S/p).exists(),p
for p,b in plans.items():(S/p).write_bytes(b)
writej(D/'apply-success.json',{'status':'PASS','tracked_files':len(plans),'existing_files':len(existing),'new_files':len(newpaths),'successful_execution_count':1,'files':proof})
print(json.dumps({'status':'PASS','files':len(plans),'original_row_pins':901,'owner_row_pins':6,'cpp_bytes':len(plans['src/db/SharedSkillDefinition.cpp'])},ensure_ascii=True))

