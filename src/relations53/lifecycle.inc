// PRIVATE CUSTOM84: all methods below own ONE BEGIN IMMEDIATE transaction.
// Internal53 owner cores cannot commit, and cannot be called outside this class.
namespace {
// Pinned Application uses no permanent SQLite authorizer. This NEW port
// reserves it during WORLD callbacks and forbids ALL SQL, including COMMIT.
// A future connection owner with its own authorizer must explicitly compose
// this guard, never overwrite an unknown callback. This is not an untrusted
// C++ sandbox: callbacks still must not manipulate SQLite APIs directly.
void immutable_world(sqlite3* db,const std::function<void()>& callback){
    require(sqlite3_get_autocommit(db)==0,"WORLD callback requires owned active transaction");
    bool denied=false;
    const auto auth=[](void* state,int,const char*,const char*,const char*,const char*)->int{*static_cast<bool*>(state)=true;return SQLITE_DENY;};
    sqlite_detail::check(db,sqlite3_set_authorizer(db,auth,&denied));
    try{callback();}catch(...){sqlite3_set_authorizer(db,nullptr,nullptr);throw;}
    sqlite_detail::check(db,sqlite3_set_authorizer(db,nullptr,nullptr));
    require(!denied&&sqlite3_get_autocommit(db)==0,"WORLD callback attempted SQLite or changed transaction");
}
void lifecycle_actor(sqlite3* db,const RelationsRepositoryDraft::Authority& a,bool accepted){
    require(accepted&&a.publication_epoch&&a.session&&a.account&&a.character&&a.world_generation&&a.position_revision&&a.slot<=1&&(a.codepage==950||a.codepage==936),"Lifecycle accepted native world identity required");
    Q q(db,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");q.bind_id(1,a.character);require(!q.row(),"Lifecycle durable actor battle");
}
std::string relation_predicate(const std::vector<RelationsRepositoryDraft::Pair>& rows){
    std::string sql="1";for(const auto& p:rows)sql+=" AND NOT(guild_low="+std::to_string(p.low)+" AND guild_high="+std::to_string(p.high)+")";return sql;
}
void retired_event(sqlite3* db,const RelationsRepositoryDraft::LifecycleLease& l,const RelationsRepositoryDraft::Pair& before,const RelationsRepositoryDraft::Pair& after,const char* action){
    const auto find=[&](std::uint64_t id)->const Succession53ReaderDraft::EffectiveLeader&{
        if(id==l.owner.guild.id)return l.owner;
        const auto at=std::find_if(l.counterpart_owners.begin(),l.counterpart_owners.end(),[&](const auto& v){return v.guild.id==id;});require(at!=l.counterpart_owners.end(),"Missing captured relation counterpart");return *at;
    };
    const auto& low=find(before.low);const auto& high=find(before.high);
    Q q(db,"INSERT INTO owned_guild_relation_events_0084(revision,guild_low,guild_high,previous_pair_revision,before_state,after_state,action,actor_guild,actor_account,actor_character,actor_slot,actor_session,actor_world_generation,actor_position_revision,actor_battle_generation,actor_codepage,low_guild_revision,low_ownership_revision,high_guild_revision,high_ownership_revision,request_subtype,request_name16,origin,design_id,source_sha256) VALUES(?,?,?,?,?,0,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,NULL,'CUSTOM_DESIGNED','CUSTOM-0084',?)");
    q.bind_id(1,after.revision);q.bind_id(2,before.low);q.bind_id(3,before.high);q.bind_id(4,before.revision);q.bind(5,before.state);q.bind(6,std::string(action));q.bind_id(7,l.owner.guild.id);q.bind_id(8,l.actor.account);q.bind_id(9,l.actor.character);q.bind(10,l.actor.slot);q.bind_id(11,l.actor.session);q.bind_id(12,l.actor.world_generation);q.bind_id(13,l.actor.position_revision);q.bind_id(14,l.actor.battle_generation);q.bind(15,l.actor.codepage);q.bind_id(16,low.guild.revision);q.bind_id(17,low.owner.ownership_revision);q.bind_id(18,high.guild.revision);q.bind_id(19,high.owner.ownership_revision);q.bind(20,std::string(source));q.done();require(sqlite3_changes(db)==1,"Lifecycle relation event insertion failed");
}
void verify_retired_event(sqlite3* db,const RelationsRepositoryDraft::LifecycleLease& l,const RelationsRepositoryDraft::Committed& c){
    const auto find=[&](std::uint64_t id)->const Succession53ReaderDraft::EffectiveLeader&{if(id==l.owner.guild.id)return l.owner;const auto at=std::find_if(l.counterpart_owners.begin(),l.counterpart_owners.end(),[&](const auto& v){return v.guild.id==id;});require(at!=l.counterpart_owners.end(),"Missing captured event counterpart");return *at;};
    const auto& lo=find(c.before.low);const auto& hi=find(c.before.high);
    Q q(db,"SELECT revision,guild_low,guild_high,previous_pair_revision,before_state,after_state,action,actor_guild,actor_account,actor_character,actor_slot,actor_session,actor_world_generation,actor_position_revision,actor_battle_generation,actor_codepage,low_guild_revision,low_ownership_revision,high_guild_revision,high_ownership_revision,request_subtype IS NULL,request_name16 IS NULL,origin,design_id,source_sha256 FROM owned_guild_relation_events_0084 WHERE revision=?");q.bind_id(1,c.revision);require(q.row(),"Missing lifecycle event");
    const std::array<std::uint64_t,6> head{c.revision,c.before.low,c.before.high,c.before.revision,c.before.state,0};for(unsigned i=0;i<head.size();++i)require(q.number<std::uint64_t>(static_cast<int>(i))==head[i],"Lifecycle event transition exact readback");require(q.text(6)==c.action,"Lifecycle event action readback");
    const std::array<std::uint64_t,13> fields{l.owner.guild.id,l.actor.account,l.actor.character,l.actor.slot,l.actor.session,l.actor.world_generation,l.actor.position_revision,l.actor.battle_generation,l.actor.codepage,lo.guild.revision,lo.owner.ownership_revision,hi.guild.revision,hi.owner.ownership_revision};for(unsigned i=0;i<fields.size();++i)require(q.number<std::uint64_t>(static_cast<int>(i+7))==fields[i],"Lifecycle event exact actor/owner readback");require(q.integer(20)==1&&q.integer(21)==1,"Lifecycle event must not invent native raw request");provenance(q,22);require(!q.row(),"Duplicate lifecycle event");
}
}
RelationsRepositoryDraft::LifecycleLease RelationsRepositoryDraft::capture_lifecycle(const Authority& a,LifecycleKind kind){
    require(enabled_,"Lifecycle53 disabled");lifecycle_actor(db_,a,a.explicit_help_accepted);Read read(db_);exact();LifecycleLease l;l.actor=a;l.kind=kind;l.owner=effective_.effective_leader(a.account,a.character);require(l.owner.owner.account_slot==a.slot,"Lifecycle exact owner slot mismatch");l.applications=effective_.applications(l.owner.guild.id);
    Q q(db_,"SELECT guild_low,guild_high FROM owned_guild_relations_0084 WHERE state<>0 AND (guild_low=? OR guild_high=?) ORDER BY guild_low,guild_high");q.bind_id(1,l.owner.guild.id);q.bind_id(2,l.owner.guild.id);
    while(q.row()){const auto p=*pair(q.number<std::uint64_t>(0),q.number<std::uint64_t>(1));l.affected_pairs.push_back(p);const auto id=p.low==l.owner.guild.id?p.high:p.low;l.counterpart_owners.push_back(effective_.effective_snapshot(id));}
    const auto [rev,next]=catalog();l.catalog_revision=rev;l.next_wire_id=next;l.whole_typed=guard(db_,{});read.finish();return l;
}
RelationsRepositoryDraft::LifecycleLease RelationsRepositoryDraft::capture_transfer(const Authority& a,const Effective::Original::Identity& target,const StoredGuildMembership& join){
    Read read(db_);auto l=capture_lifecycle(a,LifecycleKind::Transfer);require(target.character_id!=a.character&&!target.membership_revision&&original_.identity(target.account_id,target.character_id)==target,"Lifecycle target identity stale");require(SqliteGuildRepository(db_).load(target.account_id,target.character_id)==std::optional{join}&&join.guild_id==l.owner.guild.id,"Lifecycle target join stale");auto row=target;row.membership_revision=join.membership_revision;const auto role=Effective::effective_display_role(l.owner,row);require(role==1||role==2,"Lifecycle target accepted role1/2 required");l.target=target;l.target_join=join;read.finish();return l;
}
RelationsRepositoryDraft::LifecycleLease RelationsRepositoryDraft::capture_disband(const Authority& a){return capture_lifecycle(a,LifecycleKind::Disband);}
RelationsRepositoryDraft::LifecycleCommitted RelationsRepositoryDraft::apply_lifecycle(const LifecycleLease& l,const Effective::Original::Proof& proof){
    require(enabled_&&bool(proof.before_write)&&bool(proof.after_write),"Lifecycle paired immutable WORLD proof required");sqlite_detail::Transaction tx(db_);
    LifecycleLease now;if(l.kind==LifecycleKind::Transfer){require(l.target.has_value()&&l.target_join.has_value(),"Missing lifecycle transfer target");now=capture_transfer(l.actor,*l.target,*l.target_join);}else{require(l.kind==LifecycleKind::Disband&&!l.target&&!l.target_join,"Invalid lifecycle kind/target");now=capture_disband(l.actor);}
    require(now.whole_typed==l.whole_typed&&now.owner==l.owner&&now.applications==l.applications&&now.affected_pairs==l.affected_pairs&&now.counterpart_owners==l.counterpart_owners&&now.catalog_revision==l.catalog_revision&&now.next_wire_id==l.next_wire_id,"Stale entire lifecycle owner/relations lease");
    std::vector<Pair> retiring;for(const auto& p:l.affected_pairs)if(l.kind==LifecycleKind::Disband||p.state==1)retiring.push_back(p);
    require(retiring.size()<=maximum-l.catalog_revision,"Lifecycle relation clock exhausted");
    const auto id=std::to_string(l.owner.guild.id);Exclusions allowed{{"owned_guilds","id<>"+id},{"owned_guild_relation_catalog_0084","singleton<>1"},{"owned_guild_relations_0084",relation_predicate(retiring)},{"owned_guild_relation_events_0084","revision<="+std::to_string(l.catalog_revision)}};
    if(l.kind==LifecycleKind::Transfer)allowed.emplace("owned_guild_successions_0083","guild_id<>"+id+" OR revision<="+std::to_string(l.owner.owner.ownership_revision));
    else for(const auto* t:{"owned_guild_members","owned_guild_governance_0078","owned_guild_applications_0078"})allowed.emplace(t,"guild_id<>"+id);
    const auto preserved=guard(db_,allowed);immutable_world(db_,proof.before_write);require(guard(db_,{})==l.whole_typed,"Lifecycle beforeWORLD callback wrote SQL");
    LifecycleCommitted result{l.kind,l.owner.guild,{},std::nullopt};const Effective::Original::Proof pure{[]{},[]{}};
    if(l.kind==LifecycleKind::Transfer){result.transfer=effective_.coordinated_transfer(l.owner,l.applications,*l.target,*l.target_join,pure);result.guild=result.transfer->after.guild;}
    else{LifecycleCore53 core(db_,original_,effective_);result.guild=core.disband(l.owner,l.applications,pure).retired;}
    // The owner core checked its own exact readback and all unrelated rows.
    // Relation writes must not touch even those newly written owner resources.
    const Exclusions relation_only{{"owned_guild_relation_catalog_0084","singleton<>1"},{"owned_guild_relations_0084",relation_predicate(retiring)},{"owned_guild_relation_events_0084","revision<="+std::to_string(l.catalog_revision)}};
    const auto owner_protected=guard(db_,relation_only);std::uint64_t rev=l.catalog_revision;
    for(const auto& p:retiring){const auto next=rev+1;Q clock(db_,"UPDATE owned_guild_relation_catalog_0084 SET revision=? WHERE singleton=1 AND revision=? AND next_wire_id=?");clock.bind_id(1,next);clock.bind_id(2,rev);clock.bind_id(3,l.next_wire_id);clock.done();require(sqlite3_changes(db_)==1,"Lifecycle relation clock CAS");
        auto after=p;after.revision=next;after.state=0;after.inviter=0;Q q(db_,"UPDATE owned_guild_relations_0084 SET revision=?,state=0,inviter_guild=NULL WHERE guild_low=? AND guild_high=? AND revision=? AND state=? AND inviter_guild IS (CASE WHEN ?=0 THEN NULL ELSE ? END)");q.bind_id(1,next);q.bind_id(2,p.low);q.bind_id(3,p.high);q.bind_id(4,p.revision);q.bind(5,p.state);q.bind_id(6,p.inviter);q.bind_id(7,p.inviter);q.done();require(sqlite3_changes(db_)==1,"Lifecycle exact pair retirement CAS");
        const auto action=l.kind==LifecycleKind::Transfer?"transfer_retire":"disband_retire";retired_event(db_,l,p,after,action);result.retirements.push_back({p,after,next,action});rev=next;
    }
    const auto verify=[&]{exact();require(catalog()==std::pair{rev,l.next_wire_id},"Lifecycle catalog readback");for(const auto& c:result.retirements){require(pair(c.before.low,c.before.high)==std::optional{c.after},"Lifecycle pair readback");verify_retired_event(db_,l,c);}for(const auto& other:l.counterpart_owners)require(effective_.effective_snapshot(other.guild.id)==other,"Lifecycle foreign owner changed");unchanged(db_,preserved,allowed);unchanged(db_,owner_protected,relation_only);};
    verify();const auto post=guard(db_,{});immutable_world(db_,proof.after_write);require(guard(db_,{})==post,"Lifecycle afterWORLD callback wrote SQL");verify();tx.commit();return result;
}
RelationsRepositoryDraft::CreationLease RelationsRepositoryDraft::capture_create(const Authority& a,bool accepted,const std::string& name,const Effective::Original::Policy& policy){
    require(enabled_,"Create53 disabled");lifecycle_actor(db_,a,accepted);Read read(db_);exact();CreationLease l;l.actor=a;l.native_creation_prompt_accepted=accepted;l.identity=original_.nonmember(a.account,a.character);require(l.identity.slot==a.slot&&!original_.pending(a.account,a.character),"Create53 exact nonmember/slot required");const auto wallet=SqliteTradeRepository(db_).load_wallet(a.account,a.character);require(wallet.has_value(),"Create53 wallet unavailable");l.wallet=*wallet;l.name=name;l.policy=policy;
    LifecycleCore53 core(db_,original_,effective_);const auto c=core.creation_snapshot();l.next_guild_id=c.next_id;l.next_guild_revision=c.next_revision;l.guild_rows=c.guild_rows;const auto [rev,next]=catalog();require(next<=4294967295ULL,"Create53 immutable wire namespace exhausted");l.catalog_revision=rev;l.next_wire_id=next;l.whole_typed=guard(db_,{});read.finish();return l;
}
RelationsRepositoryDraft::Created53 RelationsRepositoryDraft::create53(const CreationLease& l,const Effective::Original::Proof& proof){
    require(enabled_&&bool(proof.before_write)&&bool(proof.after_write),"Create53 paired immutable WORLD proof required");sqlite_detail::Transaction tx(db_);const auto now=capture_create(l.actor,l.native_creation_prompt_accepted,l.name,l.policy);require(now.whole_typed==l.whole_typed&&now.identity==l.identity&&now.wallet==l.wallet&&now.next_guild_id==l.next_guild_id&&now.next_guild_revision==l.next_guild_revision&&now.guild_rows==l.guild_rows&&now.catalog_revision==l.catalog_revision&&now.next_wire_id==l.next_wire_id,"Create53 full captured state stale");immutable_world(db_,proof.before_write);require(guard(db_,{})==l.whole_typed,"Create53 beforeWORLD callback wrote SQL");
    LifecycleCore53 core(db_,original_,effective_);const auto created=core.create52(l.identity,l.wallet,l.name,l.policy,{l.next_guild_id,l.next_guild_revision,l.guild_rows},{[]{},[]{}});
    const Exclusions own_wire{{"owned_guild_relation_catalog_0084","singleton<>1"},{"owned_guild_relation_wire_ids_0084","guild_id<>"+std::to_string(l.next_guild_id)}};const auto protected_rows=guard(db_,own_wire);
    Q clock(db_,"UPDATE owned_guild_relation_catalog_0084 SET next_wire_id=? WHERE singleton=1 AND revision=? AND next_wire_id=?");clock.bind_id(1,l.next_wire_id+1);clock.bind_id(2,l.catalog_revision);clock.bind_id(3,l.next_wire_id);clock.done();require(sqlite3_changes(db_)==1,"Create53 wire allocator CAS");
    Q q(db_,"INSERT INTO owned_guild_relation_wire_ids_0084(guild_id,wire_id,allocated_revision,origin,design_id,source_sha256) VALUES(?,?,?,'CUSTOM_DESIGNED','CUSTOM-0084',?)");q.bind_id(1,l.next_guild_id);q.bind_id(2,l.next_wire_id);q.bind_id(3,l.catalog_revision);q.bind(4,std::string(source));q.done();require(sqlite3_changes(db_)==1,"Create53 immutable wire insertion");
    const auto verify=[&]{exact();require(wire(l.next_guild_id)==l.next_wire_id&&catalog()==std::pair{l.catalog_revision,l.next_wire_id+1}&&effective_.effective_snapshot(l.next_guild_id)==created.leader,"Create53 effectiveowner/wire exact readback");Q row(db_,"SELECT guild_id,wire_id,allocated_revision,origin,design_id,source_sha256 FROM owned_guild_relation_wire_ids_0084 WHERE guild_id=?");row.bind_id(1,l.next_guild_id);require(row.row()&&row.number<std::uint64_t>(0)==l.next_guild_id&&row.number<std::uint64_t>(1)==l.next_wire_id&&row.number<std::uint64_t>(2)==l.catalog_revision,"Create53 complete wire row readback");provenance(row,3);require(!row.row(),"Create53 duplicate wire");unchanged(db_,protected_rows,own_wire);};
    verify();const auto post=guard(db_,{});immutable_world(db_,proof.after_write);require(guard(db_,{})==post,"Create53 afterWORLD callback wrote SQL");verify();tx.commit();return {created.leader,created.wallet,static_cast<std::uint32_t>(l.next_wire_id)};
}
