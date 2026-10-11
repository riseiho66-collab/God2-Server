#include "RelationsRepositoryDraft.h"
#include "RelationsSchemaDraft.h"
#include "db/GuildSuccessionSqliteMigrationsDraft.h"
#include "db/SqliteSupport.h"
#include "db/SqliteMigrationManager.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>
#include <set>
namespace god2 {
namespace {
// Same exclusive trusted WORLD callback contract as sealed lifecycle.inc.
void immutable_world(sqlite3* db,const std::function<void()>& callback);
using Q=sqlite_detail::Statement;
constexpr const char* source="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool v,const char* m){if(!v)throw DatabaseError(m);}
#include "preservation.inc"
struct Read {
    sqlite3* db;bool own;bool done=false;
    explicit Read(sqlite3* d):db(d),own(sqlite3_get_autocommit(d)!=0){if(own)sqlite_detail::execute(db,"BEGIN");}
    void finish(){if(own)sqlite_detail::execute(db,"COMMIT");done=true;}
    ~Read(){if(own&&!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
};
void provenance(const Q& q,int n){require(q.text(n)=="CUSTOM_DESIGNED"&&q.text(n+1)=="CUSTOM-0084"&&q.text(n+2)==source,"Relation84 provenance denied");}
std::array<std::uint64_t,6> owners(const RelationsRepositoryDraft::Lease& l){
    return {l.low.owner.account_id,l.low.owner.character_id,l.low.owner.ownership_revision,l.high.owner.account_id,l.high.owner.character_id,l.high.owner.ownership_revision};
}
std::string request_name(const native_relation_private::Name& raw,bool cn){
    auto end=std::find(raw.begin(),raw.end(),0);require(end!=raw.end()&&end!=raw.begin(),"Relation name requires1..15bytes and NUL");
    std::string bytes(raw.begin(),end);auto text=LegacyChineseCodec::decode(bytes,cn);
    require(LegacyChineseCodec::encode(text,cn)==bytes,"Relation name exact legacy roundtrip denied");return text;
}
std::string fold(std::string s){for(auto& c:s)if(static_cast<unsigned char>(c)>='A'&&static_cast<unsigned char>(c)<='Z')c+=32;return s;}
void names(sqlite3* db){
    std::set<std::string> unique[2];Q q(db,"SELECT g.name_utf8 FROM owned_guilds g JOIN owned_guild_governance_0078 v ON v.guild_id=g.id ORDER BY g.id");
    while(q.row())for(unsigned cn=0;cn<2;++cn){const auto text=q.text(0);auto b=LegacyChineseCodec::encode(text,cn!=0);
        require(!b.empty()&&b.size()<=15&&b.find('\0')==std::string::npos&&LegacyChineseCodec::decode(b,cn!=0)==text,"Guild name not lossless in both locales");
        require(unique[cn].insert(fold(b)).second,"Ambiguous native relation guild names");}
}
Guard migration_preserved52(sqlite3* db){
    // Only our four new53 tables and the new journal row are excluded. Every
    // old opaque column/table/index/trigger remains a typed commit condition.
    auto result=guard(db,{{"schema_migrations","version<=52"}});
    for(const auto name:{"owned_guild_relation_catalog_0084","owned_guild_relation_wire_ids_0084","owned_guild_relations_0084","owned_guild_relation_events_0084"}){
        result.erase(name);result.erase(std::string(name)+":schema");
    }
    auto& objects=result[":sqlite_master"];objects.clear();
    Q schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master WHERE tbl_name NOT IN('owned_guild_relation_catalog_0084','owned_guild_relation_wire_ids_0084','owned_guild_relations_0084','owned_guild_relation_events_0084') ORDER BY type,name");
    while(schema.row()){
        std::vector<std::uint8_t> row;for(int i=0;i<4;++i){const auto value=schema.text(i);append_number(row,value.size());row.insert(row.end(),value.begin(),value.end());}objects.push_back(std::move(row));
    }
    return result;
}
}
void RelationsRepositoryDraft::migrate53_private(sqlite3* db){
    // Qualify actual strict52 factory first, including migration history and
    // strict51/52 objects. Existing opaque<=50 saves remain supported.
    require(db&&sqlite3_get_autocommit(db)!=0,"Migration53 must own its transaction");
    sqlite_detail::Transaction tx(db);
    const auto old=owned_guild_succession_migrations_draft();
    GuildSuccessionRepositoryFactoryDraft factory(db,old,{true,true,true,false});
    std::vector<std::uint64_t> guilds;
    Q live(db,"SELECT guild_id FROM owned_guild_governance_0078 ORDER BY guild_id");
    while(live.row()){const auto id=live.number<std::uint64_t>(0);(void)factory.effective_owner().effective_snapshot(id);guilds.push_back(id);}
    names(db);
    const auto preserved=migration_preserved52(db);const auto sql=relation53_migration();
    sqlite_detail::execute(db,sql);
    Q append(db,"INSERT INTO schema_migrations(version,name,sql_text) VALUES(53,'owned_guild_relations_private',?)");append.bind(1,sql);append.done();
    SqliteOwnedGuildMembershipRepository original(db);RelationsRepositoryDraft verified(db,original,false);
    require(guilds.size()<=4294967295ULL,"Initial immutable wire allocator exhausted");
    Q maps(db,"SELECT guild_id,wire_id,allocated_revision,origin,design_id,source_sha256 FROM owned_guild_relation_wire_ids_0084 ORDER BY guild_id");
    std::size_t index=0;while(maps.row()){
        require(index<guilds.size()&&maps.number<std::uint64_t>(0)==guilds[index]&&maps.number<std::uint64_t>(1)==index+1&&maps.number<std::uint64_t>(2)==0,"Exact initial wire map readback mismatch");provenance(maps,3);++index;
    }
    require(index==guilds.size()&&verified.catalog()==std::pair<std::uint64_t,std::uint64_t>{0,static_cast<std::uint64_t>(guilds.size())+1},"Initial catalog readback mismatch");
    for(const auto table:{"owned_guild_relations_0084","owned_guild_relation_events_0084"}){const auto query=std::string("SELECT 1 FROM ")+table+" LIMIT 1";Q empty(db,query.c_str());require(!empty.row(),"Migration53 must not grant relationships/events");}
    Q history(db,"SELECT typeof(version),typeof(name),typeof(sql_text),typeof(applied_at),name,sql_text FROM schema_migrations WHERE version=53");
    require(history.row()&&history.text(0)=="integer"&&history.text(1)=="text"&&history.text(2)=="text"&&history.text(3)=="text"&&history.text(4)=="owned_guild_relations_private"&&history.text(5)==sql&&!history.row(),"Exact typed new53 history mismatch");
    Q fk(db,"PRAGMA foreign_key_check");require(!fk.row(),"Migration53 foreign key check failed");Q integrity(db,"PRAGMA quick_check");require(integrity.row()&&integrity.text(0)=="ok"&&!integrity.row(),"Migration53 integrity check failed");
    require(migration_preserved52(db)==preserved,"Migration53 changed existing whole typed rows/schema before COMMIT");tx.commit();
}
RelationsRepositoryDraft::RelationsRepositoryDraft(sqlite3* db,SqliteOwnedGuildMembershipRepository& original,bool enabled)
    :db_(db),effective_(db,original),original_(original),enabled_(enabled){exact();}
void RelationsRepositoryDraft::exact(){
    // Reader validates immutable1..53 and exact strict51/52/53 schema objects.
    effective_.require_exact_schema53();
    Q q(db_,"SELECT guild_id FROM owned_guild_governance_0078 ORDER BY guild_id");
    while(q.row()){const auto id=q.number<std::uint64_t>(0);(void)effective_.effective_snapshot(id);(void)wire(id);}
    names(db_);validate_relations();
}
std::pair<std::uint64_t,std::uint64_t> RelationsRepositoryDraft::catalog(){
    Q q(db_,"SELECT singleton,revision,next_wire_id,origin,design_id,source_sha256 FROM owned_guild_relation_catalog_0084");
    require(q.row()&&q.integer(0)==1,"Missing relation catalog");const auto r=q.number<std::uint64_t>(1),next=q.number<std::uint64_t>(2);provenance(q,3);
    require(!q.row()&&r<=maximum&&next>=1&&next<=4294967296ULL,"Invalid relation catalog");
    return {r,next};
}
std::uint32_t RelationsRepositoryDraft::wire(std::uint64_t id){
    Q q(db_,"SELECT wire_id,allocated_revision,origin,design_id,source_sha256 FROM owned_guild_relation_wire_ids_0084 WHERE guild_id=?");q.bind_id(1,id);
    require(q.row(),"Missing immutable relation wire ID");const auto n=q.number<std::uint32_t>(0);const auto rev=q.number<std::uint64_t>(1);provenance(q,2);
    require(n&&rev<=catalog().first&&!q.row(),"Invalid wire ID");return n;
}
std::optional<RelationsRepositoryDraft::Pair> RelationsRepositoryDraft::pair(std::uint64_t a,std::uint64_t b){
    const auto lo=std::min(a,b),hi=std::max(a,b);require(lo&&hi>lo,"Invalid relation pair");
    Q q(db_,"SELECT guild_low,guild_high,revision,state,inviter_guild,low_owner_account,low_owner_character,low_ownership_revision,high_owner_account,high_owner_character,high_ownership_revision,origin,design_id,source_sha256 FROM owned_guild_relations_0084 WHERE guild_low=? AND guild_high=?");
    q.bind_id(1,lo);q.bind_id(2,hi);if(!q.row())return std::nullopt;
    Pair p{q.number<std::uint64_t>(0),q.number<std::uint64_t>(1),q.number<std::uint64_t>(2),0,q.number<std::uint8_t>(3),{}};
    if(p.state==1)p.inviter=q.number<std::uint64_t>(4);
    else {Q n(db_,"SELECT inviter_guild IS NULL FROM owned_guild_relations_0084 WHERE guild_low=? AND guild_high=?");n.bind_id(1,lo);n.bind_id(2,hi);require(n.row()&&n.integer(0)==1,"Unexpected relation inviter");}
    for(unsigned i=0;i<6;++i)p.owners[i]=q.number<std::uint64_t>(static_cast<int>(i+5));
    provenance(q,11);require(!q.row()&&p.low==lo&&p.high==hi&&p.revision&&p.revision<=catalog().first&&p.state<=2&&(p.state!=1||p.inviter==lo||p.inviter==hi),"Malformed relation pair");return p;
}
void RelationsRepositoryDraft::validate_relations(){
    const auto [rev,next]=catalog();Q maps(db_,"SELECT guild_id,wire_id,allocated_revision,origin,design_id,source_sha256 FROM owned_guild_relation_wire_ids_0084 ORDER BY wire_id");
    std::uint64_t last=0;while(maps.row()){require(maps.number<std::uint64_t>(0)>0,"Invalid mapped guild");const auto id=maps.number<std::uint64_t>(1);
        require(id>last&&id<next&&id<=4294967295ULL&&maps.number<std::uint64_t>(2)<=rev,"Immutable wire allocator corrupt");last=id;provenance(maps,3);}
    Q pairs(db_,"SELECT guild_low,guild_high FROM owned_guild_relations_0084");
    while(pairs.row()){
        const auto p=*pair(pairs.number<std::uint64_t>(0),pairs.number<std::uint64_t>(1));(void)wire(p.low);(void)wire(p.high);
        if(p.state!=0){(void)effective_.effective_snapshot(p.low);(void)effective_.effective_snapshot(p.high);}
        Q events(db_,"SELECT revision,previous_pair_revision,before_state,after_state,origin,design_id,source_sha256 FROM owned_guild_relation_events_0084 WHERE guild_low=? AND guild_high=? ORDER BY revision");events.bind_id(1,p.low);events.bind_id(2,p.high);
        std::uint64_t previous=0;std::uint8_t state=0;while(events.row()){
            const auto r=events.number<std::uint64_t>(0);require(r>previous&&r<=rev&&events.number<std::uint64_t>(1)==previous&&events.number<std::uint8_t>(2)==state,"Broken relation history");
            state=events.number<std::uint8_t>(3);require(state<=2,"Unknown relation state");previous=r;provenance(events,4);}
        require(previous==p.revision&&state==p.state,"Relation history/pair mismatch");
    }
    Q highest(db_,"SELECT COALESCE(MAX(revision),0) FROM owned_guild_relation_events_0084");require(highest.row()&&highest.number<std::uint64_t>(0)==rev,"Catalog/event revision mismatch");
}
RelationsRepositoryDraft::Lease RelationsRepositoryDraft::capture(const Authority& a,std::span<const std::uint8_t> raw){
    require(enabled_&&a.explicit_help_accepted&&a.publication_epoch&&a.session&&a.world_generation&&a.position_revision&&a.slot<=1&&(a.codepage==950||a.codepage==936),"Relation explicit current world authority required");
    const auto action=native_relation_private::decode76(raw);require(action.has_value()&&(action->subtype==1||action->subtype==8),"War/unknown relation business OPEN");
    Read read(db_);exact();Lease l;l.actor=a;l.raw=*action;
    const auto actor=effective_.effective_leader(a.account,a.character);require(actor.owner.account_slot==a.slot,"Actor account slot mismatch");
    Q battle(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");battle.bind_id(1,a.character);require(!battle.row(),"Relation actor has durable active battle");
    const auto name=request_name(action->name,a.codepage==936);
    Q target(db_,"SELECT g.id FROM owned_guilds g JOIN owned_guild_governance_0078 v ON v.guild_id=g.id WHERE g.name_utf8=? COLLATE BINARY");target.bind(1,name);
    require(target.row(),"Unknown live target guild");const auto id=target.number<std::uint64_t>(0);require(!target.row()&&id!=actor.guild.id,"Ambiguous/self relation target");
    const auto other=effective_.effective_snapshot(id);
    l.low=actor.guild.id<id?actor:other;l.high=actor.guild.id<id?other:actor;
    (void)wire(l.low.guild.id);(void)wire(l.high.guild.id);
    l.pair=pair(l.low.guild.id,l.high.guild.id);const auto state=l.pair?l.pair->state:0;
    if(action->subtype==1){
        if(state==0){
            for(const auto gid:{l.low.guild.id,l.high.guild.id}){Q n(db_,"SELECT COUNT(*) FROM owned_guild_relations_0084 WHERE state<>0 AND (guild_low=? OR guild_high=?)");n.bind_id(1,gid);n.bind_id(2,gid);require(n.row()&&n.integer(0)<50,"Relation native50 custom capacity");}
            l.action="propose";
        }else {require(state==1&&l.pair->inviter!=actor.guild.id&&l.pair->owners==owners(l),"Only unchanged reciprocal invitation may accept");l.action="accept";}
    }else {require(state!=0,"No live relation to remove");l.action=state==2?"remove":l.pair->inviter==actor.guild.id?"withdraw":"decline";}
    const auto [revision,next]=catalog();l.catalog_revision=revision;l.next_wire_id=next;l.whole_typed=guard(db_,{});read.finish();return l;
}
RelationsRepositoryDraft::Committed RelationsRepositoryDraft::apply(const Lease& l,const SqliteOwnedGuildMembershipRepository::Proof& proof){
    require(enabled_&&bool(proof.before_write)&&bool(proof.after_write),"Enabled relation and paired immutable world proofs required");
    sqlite_detail::Transaction tx(db_);const auto raw=native_relation_private::encode76(l.raw);
    const auto current=capture(l.actor,raw);require(current.whole_typed==l.whole_typed&&current.low==l.low&&current.high==l.high&&current.pair==l.pair&&current.action==l.action,"Stale complete two-guild relation lease");
    require(l.catalog_revision<maximum,"Relation revision exhausted");const auto revision=l.catalog_revision+1;
    const Pair old=l.pair.value_or(Pair{l.low.guild.id,l.high.guild.id,0,0,0,{}});Pair after=old;after.revision=revision;after.owners=owners(l);
    after.state=l.action=="propose"?1:l.action=="accept"?2:0;
    const auto actor_gid=l.low.owner.character_id==l.actor.character&&l.low.owner.account_id==l.actor.account?l.low.guild.id:l.high.guild.id;
    after.inviter=after.state==1?actor_gid:0;
    const auto condition="NOT(guild_low="+std::to_string(after.low)+" AND guild_high="+std::to_string(after.high)+")";
    const Exclusions allowed{{"owned_guild_relation_catalog_0084","singleton<>1"},{"owned_guild_relations_0084",condition},{"owned_guild_relation_events_0084","revision<>"+std::to_string(revision)}};
    const auto preserved=guard(db_,allowed);immutable_world(db_,proof.before_write);require(guard(db_,{})==l.whole_typed,"PreSQL world proof mutated captured SQL");
    Q clock(db_,"UPDATE owned_guild_relation_catalog_0084 SET revision=? WHERE singleton=1 AND revision=? AND next_wire_id=?");clock.bind_id(1,revision);clock.bind_id(2,l.catalog_revision);clock.bind_id(3,l.next_wire_id);clock.done();require(sqlite3_changes(db_)==1,"Relation catalog CAS conflict");
    Q write(db_,"INSERT INTO owned_guild_relations_0084(guild_low,guild_high,revision,state,inviter_guild,low_owner_account,low_owner_character,low_ownership_revision,high_owner_account,high_owner_character,high_ownership_revision,origin,design_id,source_sha256) VALUES(?,?,?,?,CASE WHEN ?=0 THEN NULL ELSE ? END,?,?,?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0084',?) ON CONFLICT(guild_low,guild_high) DO UPDATE SET revision=excluded.revision,state=excluded.state,inviter_guild=excluded.inviter_guild,low_owner_account=excluded.low_owner_account,low_owner_character=excluded.low_owner_character,low_ownership_revision=excluded.low_ownership_revision,high_owner_account=excluded.high_owner_account,high_owner_character=excluded.high_owner_character,high_ownership_revision=excluded.high_ownership_revision");
    write.bind_id(1,after.low);write.bind_id(2,after.high);write.bind_id(3,revision);write.bind(4,after.state);write.bind_id(5,after.inviter);write.bind_id(6,after.inviter);
    for(unsigned i=0;i<6;++i)write.bind_id(static_cast<int>(i+7),after.owners[i]);write.bind(13,std::string(source));write.done();require(sqlite3_changes(db_)==1,"Relation pair write failed");
    Q event(db_,"INSERT INTO owned_guild_relation_events_0084(revision,guild_low,guild_high,previous_pair_revision,before_state,after_state,action,actor_guild,actor_account,actor_character,actor_slot,actor_session,actor_world_generation,actor_position_revision,actor_battle_generation,actor_codepage,low_guild_revision,low_ownership_revision,high_guild_revision,high_ownership_revision,request_subtype,request_name16,origin,design_id,source_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0084',?)");
    event.bind_id(1,revision);event.bind_id(2,after.low);event.bind_id(3,after.high);event.bind_id(4,old.revision);event.bind(5,old.state);event.bind(6,after.state);event.bind(7,l.action);event.bind_id(8,actor_gid);event.bind_id(9,l.actor.account);event.bind_id(10,l.actor.character);event.bind(11,l.actor.slot);event.bind_id(12,l.actor.session);event.bind_id(13,l.actor.world_generation);event.bind_id(14,l.actor.position_revision);event.bind_id(15,l.actor.battle_generation);event.bind(16,l.actor.codepage);event.bind_id(17,l.low.guild.revision);event.bind_id(18,l.low.owner.ownership_revision);event.bind_id(19,l.high.guild.revision);event.bind_id(20,l.high.owner.ownership_revision);event.bind(21,l.raw.subtype);event.bind_blob(22,l.raw.name);event.bind(23,std::string(source));event.done();require(sqlite3_changes(db_)==1,"Relation event append failed");
    const auto verify=[&]{
        exact();require(pair(after.low,after.high)==std::optional{after}&&catalog()==std::pair{revision,l.next_wire_id},"Relation exact readback failed");
        require(effective_.effective_snapshot(after.low)==l.low&&effective_.effective_snapshot(after.high)==l.high,"Relation changed effective52 resources");
        Q written(db_,"SELECT revision,guild_low,guild_high,previous_pair_revision,before_state,after_state,action,actor_guild,actor_account,actor_character,actor_slot,actor_session,actor_world_generation,actor_position_revision,actor_battle_generation,actor_codepage,low_guild_revision,low_ownership_revision,high_guild_revision,high_ownership_revision,request_subtype,request_name16,origin,design_id,source_sha256 FROM owned_guild_relation_events_0084 WHERE revision=?");
        written.bind_id(1,revision);require(written.row(),"Missing new relation event");
        require(written.number<std::uint64_t>(0)==revision&&written.number<std::uint64_t>(1)==after.low&&written.number<std::uint64_t>(2)==after.high&&written.number<std::uint64_t>(3)==old.revision&&written.number<std::uint8_t>(4)==old.state&&written.number<std::uint8_t>(5)==after.state&&written.text(6)==l.action,"Exact new relation transition event mismatch");
        const std::array<std::uint64_t,14> fields{actor_gid,l.actor.account,l.actor.character,l.actor.slot,l.actor.session,l.actor.world_generation,l.actor.position_revision,l.actor.battle_generation,l.actor.codepage,l.low.guild.revision,l.low.owner.ownership_revision,l.high.guild.revision,l.high.owner.ownership_revision,l.raw.subtype};
        for(unsigned i=0;i<fields.size();++i)require(written.number<std::uint64_t>(static_cast<int>(i+7))==fields[i],"Exact relation actor/owner/action audit mismatch");
        const auto bytes=written.blob(21,16,16);require(std::equal(bytes.begin(),bytes.end(),l.raw.name.begin()),"Exact relation raw name16 audit mismatch");
        provenance(written,22);require(!written.row(),"Duplicate new relation event");unchanged(db_,preserved,allowed);
    };
    verify();
    // The append exclusion allows OUR SQL only. The after-write callback is
    // immutable WORLD proof and may not mutate even this action's new rows.
    const auto post_write=guard(db_,{});
    immutable_world(db_,proof.after_write);require(guard(db_,{})==post_write,"After-write world proof mutated exact postSQL snapshot");
    verify();tx.commit();return {old,after,revision,l.action};
}
std::vector<native_relation_private::Row> RelationsRepositoryDraft::projection(std::uint64_t id,bool cn){
    Read read(db_);exact();(void)effective_.effective_snapshot(id);std::vector<native_relation_private::Row> result;
    Q q(db_,"SELECT guild_low,guild_high FROM owned_guild_relations_0084 WHERE state<>0 AND (guild_low=? OR guild_high=?)");q.bind_id(1,id);q.bind_id(2,id);
    while(q.row()){const auto p=*pair(q.number<std::uint64_t>(0),q.number<std::uint64_t>(1));const auto other=p.low==id?p.high:p.low;const auto target=effective_.effective_snapshot(other);
        native_relation_private::Row r;r.opaque_id=wire(other);
        const auto display=p.state==2?native_relation_private::DisplayKind::alliance:
            p.inviter==id?native_relation_private::DisplayKind::alliance_invitation:
                         native_relation_private::DisplayKind::invited_to_alliance;
        r.raw_type=static_cast<native_relation_private::Byte>(display);
        const auto b=LegacyChineseCodec::encode(target.guild.name_utf8,cn);require(!b.empty()&&b.size()<=15,"Invalid relation projection name");std::copy(b.begin(),b.end(),r.name.begin());result.push_back(r);}
    require(result.size()<=50,"Relation projection capacity corrupt");std::sort(result.begin(),result.end(),[](const auto& a,const auto& b){return a.opaque_id<b.opaque_id;});read.finish();return result;
}
#include "lifecycle.inc"

RelationsRepositoryDraft::View RelationsRepositoryDraft::view(std::uint64_t guild,bool simplified){Read read(db_);exact();View v{effective_.effective_snapshot(guild),effective_.applications(guild),projection(guild,simplified),guard(db_,{})};read.finish();return v;}

}
