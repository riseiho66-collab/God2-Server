#include "db/SqliteCompanionRepository.h"
#include "db/SqliteSupport.h"
#include <limits>
#include <algorithm>
namespace god2 {
namespace {
std::uint64_t next_revision(std::uint64_t value) {
    if(value>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))
        throw DatabaseError("Companion revision exhausted");
    return value+1;
}
std::vector<std::uint8_t> skills_blob(const RecoveredDeityState::Snapshot& value) {
    std::vector<std::uint8_t> result;
    for(const auto& skill:value.skills) {
        const auto& bytes=skill.encode();result.insert(result.end(),bytes.begin(),bytes.end());
    }
    return result;
}
bool same_deity(const StoredDeity& a,const StoredDeity& b) {
    if(a.revision!=b.revision || a.provenance!=b.provenance ||
       a.snapshot.declaration.encode()!=b.snapshot.declaration.encode() ||
       a.snapshot.status.encode()!=b.snapshot.status.encode() ||
       a.snapshot.skills.size()!=b.snapshot.skills.size()) return false;
    for(std::size_t i=0;i<a.snapshot.skills.size();++i)
        if(a.snapshot.skills[i].encode()!=b.snapshot.skills[i].encode()) return false;
    return true;
}
bool same_pet(const StoredPet2Slot& a,const StoredPet2Slot& b) {
    if(a.slot!=b.slot || a.revision!=b.revision || a.provenance!=b.provenance || bool(a.pet)!=bool(b.pet) || bool(a.pet1)!=bool(b.pet1)) return false;
    if(a.pet1) return RecoveredPet2Lifecycle::same_owner(a.pet1->owner,b.pet1->owner) &&
        a.pet1->inventory==b.pet1->inventory &&
        RecoveredPet1Stats::encode_logical(a.pet1->stats)==RecoveredPet1Stats::encode_logical(b.pet1->stats);
    return !a.pet || (RecoveredPet2Lifecycle::same_owner(a.pet->owner,b.pet->owner) &&
        a.pet->inventory==b.pet->inventory &&
        RecoveredPet2Stats::encode_logical(a.pet->stats)==RecoveredPet2Stats::encode_logical(b.pet->stats));
}
}
struct SqliteCompanionRepository::CommittedDeitySelection::Data {
    const SqliteCompanionRepository* repository;
    std::weak_ptr<const std::uint8_t> identity;
    std::uint64_t account,character;
    StoredDeity deity;
    std::optional<StoredDeitySelection> before;
    StoredDeitySelection after;
    bool changed;
};
std::uint64_t SqliteCompanionRepository::CommittedDeitySelection::account() const noexcept {return data_->account;}
std::uint64_t SqliteCompanionRepository::CommittedDeitySelection::character() const noexcept {return data_->character;}
const StoredDeity& SqliteCompanionRepository::CommittedDeitySelection::deity() const noexcept {return data_->deity;}
const std::optional<StoredDeitySelection>& SqliteCompanionRepository::CommittedDeitySelection::before() const noexcept {return data_->before;}
const StoredDeitySelection& SqliteCompanionRepository::CommittedDeitySelection::after() const noexcept {return data_->after;}
bool SqliteCompanionRepository::CommittedDeitySelection::changed() const noexcept {return data_->changed;}
bool SqliteCompanionRepository::issued_selection(const CommittedDeitySelection& value) const noexcept {
    if(!value.data_ || value.data_->repository!=this)return false;
    const auto identity=value.data_->identity.lock();
    return identity && identity==readset_identity_;
}
std::optional<OwnedDeityRosterReadset> SqliteCompanionRepository::selection_roster_successor(
        const OwnedDeityRosterReadset& before,const CommittedDeitySelection& committed) const {
    const auto identity=before.identity_.lock();
    if(!issued_selection(committed) || before.repository_!=this || !identity ||
       identity!=readset_identity_ || before.account()!=committed.account() ||
       before.character()!=committed.character() || before.selection()!=committed.before())return {};
    const auto& selected=committed.deity();
    const auto key=committed.after().key;
    if(selected.snapshot.status.key_raw()!=key)return {};
    const auto found=std::find_if(before.rows().begin(),before.rows().end(),
        [&](const auto& row){return row.snapshot.status.key_raw()==key;});
    if(found==before.rows().end() || !same_deity(*found,selected) ||
       std::count_if(before.rows().begin(),before.rows().end(),
           [&](const auto& row){return row.snapshot.status.key_raw()==key;})!=1)return {};
    return OwnedDeityRosterReadset(this,readset_identity_,before.account(),before.character(),
        before.rows(),committed.after(),before.template_keys());
}
void SqliteCompanionRepository::require_owner(std::uint64_t account,std::uint64_t character) {
    if(!account || !character) throw DatabaseError("Invalid companion owner");
    sqlite_detail::Statement row(db_,"SELECT 1 FROM recovered_characters WHERE account_id=? AND id=?");
    row.bind_id(1,account);row.bind_id(2,character);
    if(!row.row()) throw DatabaseError("Companion character ownership rejected");
}
void SqliteCompanionRepository::require_no_pending_battle(std::uint64_t character) {
    sqlite_detail::Statement row(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    row.bind_id(1,character);
    if(row.row()) throw DatabaseError("Companion mutation during pending battle");
}
void SqliteCompanionRepository::require_provenance(const CompanionProvenance& p) {
    if(p.source_sha256!=source_sha256 ||
       (p.authority!="NATIVE_VERIFIED" && p.authority!="CUSTOM_DESIGNED" && p.authority!="CUSTOM_TEST_NOT_NATIVE") ||
       p.evidence_id.empty() || p.evidence_id.size()>512 || p.evidence_id.find('\0')!=std::string::npos)
        throw DatabaseError("Unqualified companion instance provenance");
}
std::vector<std::uint8_t> SqliteCompanionRepository::deity_template_keys() {
    sqlite_detail::Statement rows(db_,"SELECT metadata_key,source_sha256 FROM native_companion_metadata WHERE family='GOD' ORDER BY metadata_key");
    std::vector<std::uint8_t> result;
    while(rows.row()) {
        const auto key=rows.number<std::uint16_t>(0);
        if(rows.text(1)!=source_sha256 || key<2801 || key>2834)
            throw DatabaseError("Unqualified current GOD catalog row");
        result.push_back(static_cast<std::uint8_t>(key-2800));
    }
    return result;
}
bool SqliteCompanionRepository::resolves_pet2(std::uint16_t key) {
    sqlite_detail::Statement row(db_,"SELECT source_sha256 FROM native_companion_metadata WHERE family='NCP' AND metadata_key=?");
    row.bind(1,key);
    if(!row.row()) return false;
    if(row.text(0)!=source_sha256 || key<0x6d61 || key>=0x7f58)
        throw DatabaseError("Unqualified current pet2 catalog row");
    return true;
}
bool SqliteCompanionRepository::resolves_pet1(std::uint16_t key) {
    sqlite_detail::Statement row(db_,"SELECT source_sha256 FROM native_pet1_metadata WHERE family='COM' AND metadata_key=?");
    row.bind(1,key);if(!row.row())return false;
    if(row.text(0)!=source_sha256 || key<24001 || key>26070)
        throw DatabaseError("Unqualified current COM catalog row");
    return true;
}
std::vector<StoredDeity> SqliteCompanionRepository::load_deities(std::uint64_t account,std::uint64_t character) {
    require_owner(account,character);
    const auto keys=deity_template_keys();
    sqlite_detail::Statement rows(db_,"SELECT row_key,declaration,status,skills,revision,source_sha256,authority,evidence_id FROM character_deities WHERE character_id=? ORDER BY row_key");
    rows.bind_id(1,character);std::vector<StoredDeity> result;
    while(rows.row()) {
        const auto declaration=RecoveredDeityState::Declaration::parse(rows.blob(1,19,19));
        const auto status=RecoveredDeityState::Status::parse(rows.blob(2,29,29));
        if(!declaration || !status) throw DatabaseError("Malformed saved deity record");
        RecoveredDeityState::Snapshot snapshot{*declaration,*status,{}};
        const auto bytes=rows.blob(3,0,400);
        if(bytes.size()%4) throw DatabaseError("Malformed saved deity skills");
        for(std::size_t at=0;at<bytes.size();at+=4) {
            const auto skill=RecoveredDeityState::Skill::parse(bytes.subspan(at,4));
            if(!skill) throw DatabaseError("Malformed saved deity skill record");
            snapshot.skills.push_back(*skill);
        }
        StoredDeity value{std::move(snapshot),rows.number<std::uint64_t>(4),{rows.text(5),rows.text(6),rows.text(7)}};
        require_provenance(value.provenance);
        if(!value.revision || value.snapshot.status.key_raw()!=rows.number<std::uint8_t>(0) ||
           !RecoveredDeityState::valid(value.snapshot,keys) || result.size()>=RecoveredDeityState::row_capacity)
            throw DatabaseError("Invalid saved owned deity snapshot");
        result.push_back(std::move(value));
    }
    return result;
}
bool SqliteCompanionRepository::selected_deity_has_skill(std::uint64_t account,std::uint64_t character,
        std::uint8_t kind,std::uint8_t skill) {
    const auto selected=load_deity_selection(account,character);
    if(!selected) return false;
    const auto owned=load_deities(account,character);
    for(const auto& deity:owned) if(deity.snapshot.status.key_raw()==selected->key)
        for(const auto& record:deity.snapshot.skills) {
            const auto& bytes=record.encode();
            if(bytes[2]==kind && bytes[3]==skill) return true;
        }
    return false;
}
OwnedDeityRosterReadset SqliteCompanionRepository::load_deity_roster(
        std::uint64_t account,std::uint64_t character) {
    // Share the selected-skill guard: neither observation may nest through the
    // other and turn a caught reentrant call into an apparently current roster.
    if(readset_reading_) {
        readset_reentered_=true;
        throw DatabaseError("Owned deity roster readset reentry rejected");
    }
    readset_reading_=true;readset_reentered_=false;
    struct Exit { bool& active; ~Exit(){active=false;} } exit{readset_reading_};
    if(!db_ || !account || !character || !sqlite3_get_autocommit(db_))
        throw DatabaseError("Owned deity roster requires owner and autocommit connection");
    const auto changes=sqlite3_total_changes64(db_);
    struct Read {
        sqlite3* db;bool committed=false;
        explicit Read(sqlite3* value):db(value){sqlite_detail::execute(db,"BEGIN");}
        ~Read(){if(!committed)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
        void commit(){sqlite_detail::execute(db,"COMMIT");committed=true;}
    } read(db_);
    const auto fence=[&] {
        if(readset_reentered_ || sqlite3_get_autocommit(db_) || sqlite3_total_changes64(db_)!=changes)
            throw DatabaseError("Owned deity roster changed during observation");
    };
    for(const auto* name:{"accounts","recovered_characters","native_companion_metadata",
                         "character_deities","character_deity_selection"}) {
        sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name=? COLLATE NOCASE OR tbl_name=? COLLATE NOCASE LIMIT 1");
        shadow.bind(1,std::string(name));shadow.bind(2,std::string(name));
        if(shadow.row())throw DatabaseError("Owned deity roster TEMP shadow rejected");
        sqlite_detail::Statement base(db_,"SELECT 1 FROM main.sqlite_master WHERE type='table' AND name=? COLLATE NOCASE");
        base.bind(1,std::string(name));
        if(!base.row())throw DatabaseError("Owned deity roster source table missing");
    }
    std::vector<std::uint8_t> keys;
    std::vector<StoredDeity> values;
    std::optional<StoredDeitySelection> selection;
    {
        sqlite_detail::Statement owner(db_,"SELECT 1 FROM main.recovered_characters c JOIN main.accounts a ON a.id=c.account_id WHERE c.account_id=? AND c.id=?");
        owner.bind_id(1,account);owner.bind_id(2,character);
        if(!owner.row() || owner.row())throw DatabaseError("Owned deity roster ownership rejected");
        sqlite_detail::Statement catalog(db_,"SELECT metadata_key,source_sha256 FROM main.native_companion_metadata WHERE family='GOD' ORDER BY metadata_key");
        while(catalog.row()) {
            const auto key=catalog.number<std::uint16_t>(0);
            if(catalog.text(1)!=source_sha256 || key<2801 || key>2834 ||
               (!keys.empty() && key-2800<=keys.back()))
                throw DatabaseError("Owned deity roster GOD source unqualified");
            keys.push_back(static_cast<std::uint8_t>(key-2800));
        }
        sqlite_detail::Statement rows(db_,"SELECT row_key,declaration,status,skills,revision,source_sha256,authority,evidence_id FROM main.character_deities WHERE character_id=? ORDER BY row_key");
        rows.bind_id(1,character);
        while(rows.row()) {
            const auto key=rows.number<std::uint8_t>(0);
            const auto declaration=RecoveredDeityState::Declaration::parse(rows.blob(1,19,19));
            const auto status=RecoveredDeityState::Status::parse(rows.blob(2,29,29));
            if(!declaration || !status)throw DatabaseError("Owned deity roster malformed records");
            RecoveredDeityState::Snapshot snapshot{*declaration,*status,{}};
            const auto bytes=rows.blob(3,0,400);
            if(bytes.size()%4)throw DatabaseError("Owned deity roster malformed skills");
            for(std::size_t at=0;at<bytes.size();at+=4) {
                const auto skill=RecoveredDeityState::Skill::parse(bytes.subspan(at,4));
                if(!skill)throw DatabaseError("Owned deity roster malformed skill");
                snapshot.skills.push_back(*skill);
            }
            StoredDeity value{std::move(snapshot),rows.number<std::uint64_t>(4),{rows.text(5),rows.text(6),rows.text(7)}};
            require_provenance(value.provenance);
            if(!value.revision || value.snapshot.status.key_raw()!=key ||
               !RecoveredDeityState::valid(value.snapshot,keys) ||
               values.size()>=RecoveredDeityState::row_capacity ||
               (!values.empty() && values.back().snapshot.status.key_raw()>=key))
                throw DatabaseError("Owned deity roster invalid saved row");
            values.push_back(std::move(value));
        }
        sqlite_detail::Statement selected(db_,"SELECT row_key,revision FROM main.character_deity_selection WHERE character_id=?");
        selected.bind_id(1,character);
        if(selected.row()) {
            selection=StoredDeitySelection{selected.number<std::uint8_t>(0),selected.number<std::uint64_t>(1)};
            if(!selection->revision || selected.row() ||
               std::none_of(values.begin(),values.end(),[&](const auto& value){return value.snapshot.status.key_raw()==selection->key;}))
                throw DatabaseError("Owned deity roster selection is not owned");
        }
    }
    // Own every returned byte before closing the observation. No external
    // callbacks or old-source checks occur after this read transaction commits.
    OwnedDeityRosterReadset result(this,readset_identity_,account,character,
        std::move(values),selection,std::move(keys));
    fence();read.commit();
    if(readset_reentered_ || !sqlite3_get_autocommit(db_) || sqlite3_total_changes64(db_)!=changes)
        throw DatabaseError("Owned deity roster completion changed");
    return result;
}
bool SqliteCompanionRepository::deity_roster_current(const OwnedDeityRosterReadset& readset) {
    if(readset_reading_) {
        readset_reentered_=true;
        throw DatabaseError("Owned deity roster readset reentry rejected");
    }
    const auto owned=readset;
    const auto identity=owned.identity_.lock();
    if(owned.repository_!=this || !identity || identity!=readset_identity_)return false;
    const auto actual=load_deity_roster(owned.account(),owned.character());
    if(actual.selection()!=owned.selection() || actual.template_keys()!=owned.template_keys() ||
       actual.rows().size()!=owned.rows().size())return false;
    for(std::size_t i=0;i<actual.rows().size();++i) {
        const auto& a=actual.rows()[i];const auto& b=owned.rows()[i];
        if(a.revision!=b.revision || a.provenance!=b.provenance ||
           a.snapshot.declaration.encode()!=b.snapshot.declaration.encode() ||
           a.snapshot.status.encode()!=b.snapshot.status.encode() ||
           skills_blob(a.snapshot)!=skills_blob(b.snapshot))return false;
    }
    return true;
}
bool SqliteCompanionRepository::deity_roster_current_in_transaction(const OwnedDeityRosterReadset& readset) {
    if(readset_reading_){readset_reentered_=true;return false;}
    const auto identity=readset.identity_.lock();
    if(!db_ || sqlite3_get_autocommit(db_) || readset.repository_!=this ||
       !identity || identity!=readset_identity_)return false;
    const auto owned=readset;
    readset_reading_=true;readset_reentered_=false;
    struct Exit{bool& reading;~Exit(){reading=false;}}exit{readset_reading_};
    const auto changes=sqlite3_total_changes64(db_);
    for(const auto* name:{"accounts","recovered_characters","native_companion_metadata",
                         "character_deities","character_deity_selection"}){
        sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name=? COLLATE NOCASE OR tbl_name=? COLLATE NOCASE LIMIT 1");
        shadow.bind(1,std::string(name));shadow.bind(2,std::string(name));
        if(shadow.row())return false;
        sqlite_detail::Statement base(db_,"SELECT 1 FROM main.sqlite_master WHERE type='table' AND name=? COLLATE NOCASE");
        base.bind(1,std::string(name));if(!base.row() || base.row())return false;
    }
    sqlite_detail::Statement owner(db_,"SELECT 1 FROM main.recovered_characters c JOIN main.accounts a ON a.id=c.account_id WHERE c.account_id=? AND c.id=?");
    owner.bind_id(1,owned.account());owner.bind_id(2,owned.character());
    if(!owner.row() || owner.row())return false;
    sqlite_detail::Statement catalog(db_,"SELECT metadata_key,source_sha256 FROM main.native_companion_metadata WHERE family='GOD' ORDER BY metadata_key");
    std::size_t at=0;
    while(catalog.row()){
        if(at>=owned.template_keys().size() ||
           catalog.number<std::uint16_t>(0)!=std::uint16_t(2800+owned.template_keys()[at]) ||
           catalog.text(1)!=source_sha256)return false;
        ++at;
    }
    if(at!=owned.template_keys().size())return false;
    sqlite_detail::Statement rows(db_,"SELECT row_key,declaration,status,skills,revision,source_sha256,authority,evidence_id FROM main.character_deities WHERE character_id=? ORDER BY row_key");
    rows.bind_id(1,owned.character());at=0;
    while(rows.row()){
        if(at>=owned.rows().size())return false;
        const auto& expected=owned.rows()[at++];
        const auto declaration=rows.blob(1,19,19),status=rows.blob(2,29,29),skills=rows.blob(3,0,400);
        const auto expected_skills=skills_blob(expected.snapshot);
        if(rows.number<std::uint8_t>(0)!=expected.snapshot.status.key_raw() ||
           !std::equal(declaration.begin(),declaration.end(),expected.snapshot.declaration.encode().begin()) ||
           !std::equal(status.begin(),status.end(),expected.snapshot.status.encode().begin()) ||
           skills.size()!=expected_skills.size() || !std::equal(skills.begin(),skills.end(),expected_skills.begin()) ||
           rows.number<std::uint64_t>(4)!=expected.revision || rows.text(5)!=expected.provenance.source_sha256 ||
           rows.text(6)!=expected.provenance.authority || rows.text(7)!=expected.provenance.evidence_id)return false;
    }
    if(at!=owned.rows().size())return false;
    sqlite_detail::Statement selection(db_,"SELECT row_key,revision FROM main.character_deity_selection WHERE character_id=?");
    selection.bind_id(1,owned.character());
    if(selection.row()){
        if(!owned.selection() || selection.number<std::uint8_t>(0)!=owned.selection()->key ||
           selection.number<std::uint64_t>(1)!=owned.selection()->revision || selection.row())return false;
    }else if(owned.selection())return false;
    return !readset_reentered_ && !sqlite3_get_autocommit(db_) && sqlite3_total_changes64(db_)==changes;
}
std::optional<SelectedDeitySkillReadset> SqliteCompanionRepository::load_selected_deity_skill(
        std::uint64_t account,std::uint64_t character,std::uint8_t kind,std::uint8_t skill) {
    return read_selected_deity_skill(account,character,kind,skill);
}
bool SqliteCompanionRepository::selected_deity_skill_current(const SelectedDeitySkillReadset& readset) {
    return selected_deity_skill_current_impl(readset,false);
}
bool SqliteCompanionRepository::selected_deity_skill_current_in_transaction(const SelectedDeitySkillReadset& readset) {
    return selected_deity_skill_current_impl(readset,true);
}
bool SqliteCompanionRepository::selected_deity_skill_current_impl(const SelectedDeitySkillReadset& readset,bool borrowed) {
    if(readset_reading_) {
        readset_reentered_=true;
        throw DatabaseError("Selected deity readset reentry rejected");
    }
    const auto owned=readset;
    const auto identity=owned.identity_.lock();
    if(owned.repository_!=this || !identity || identity!=readset_identity_) return false;
    const auto actual=read_selected_deity_skill(owned.account(),owned.character(),owned.kind(),owned.definition_id(),borrowed);
    return actual && actual->selection()==owned.selection() &&
        actual->deity().revision==owned.deity().revision &&
        actual->deity().provenance==owned.deity().provenance &&
        actual->deity().snapshot.declaration.encode()==owned.deity().snapshot.declaration.encode() &&
        actual->deity().snapshot.status.encode()==owned.deity().snapshot.status.encode() &&
        skills_blob(actual->deity().snapshot)==skills_blob(owned.deity().snapshot) &&
        actual->skill().encode()==owned.skill().encode();
}
std::optional<SelectedDeitySkillReadset> SqliteCompanionRepository::read_selected_deity_skill(
        std::uint64_t account,std::uint64_t character,std::uint8_t kind,std::uint8_t skill,bool borrowed) {
    if(readset_reading_) {
        readset_reentered_=true;
        throw DatabaseError("Selected deity readset reentry rejected");
    }
    readset_reading_=true;readset_reentered_=false;
    struct Exit { bool& active; ~Exit(){active=false;} } exit{readset_reading_};
    if(!db_ || !account || !character || bool(sqlite3_get_autocommit(db_))==borrowed)
        throw DatabaseError("Selected deity readset requires owner and matching transaction scope");
    const auto changes=sqlite3_total_changes64(db_);
    // Explicit main qualification prevents an attached/TEMP table from being
    // mistaken for the actual same-connection saved-state source.
    struct Read {
        sqlite3* db;bool borrowed,committed=false;
        Read(sqlite3* value,bool borrow):db(value),borrowed(borrow){if(!borrowed)sqlite_detail::execute(db,"BEGIN");}
        ~Read(){if(!borrowed && !committed)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
        void commit(){if(!borrowed)sqlite_detail::execute(db,"COMMIT");committed=true;}
    } read(db_,borrowed);
    const auto fence=[&] {
        if(readset_reentered_ || sqlite3_get_autocommit(db_) || sqlite3_total_changes64(db_)!=changes)
            throw DatabaseError("Selected deity readset changed during observation");
    };
    for(const auto* name:{"accounts","recovered_characters","native_companion_metadata",
                         "character_deities","character_deity_selection"}) {
        sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name=? COLLATE NOCASE OR tbl_name=? COLLATE NOCASE LIMIT 1");
        shadow.bind(1,std::string(name));shadow.bind(2,std::string(name));
        if(shadow.row()) throw DatabaseError("Selected deity readset TEMP shadow rejected");
        sqlite_detail::Statement base(db_,"SELECT 1 FROM main.sqlite_master WHERE type='table' AND name=? COLLATE NOCASE");
        base.bind(1,std::string(name));
        if(!base.row()) throw DatabaseError("Selected deity readset source table missing");
    }
    std::optional<SelectedDeitySkillReadset> result;
    {
        sqlite_detail::Statement owner(db_,"SELECT 1 FROM main.recovered_characters c JOIN main.accounts a ON a.id=c.account_id WHERE c.account_id=? AND c.id=?");
        owner.bind_id(1,account);owner.bind_id(2,character);
        if(!owner.row()) throw DatabaseError("Selected deity readset ownership rejected");
        sqlite_detail::Statement selected(db_,"SELECT row_key,revision FROM main.character_deity_selection WHERE character_id=?");
        selected.bind_id(1,character);
        if(selected.row()) {
            const StoredDeitySelection selection{selected.number<std::uint8_t>(0),selected.number<std::uint64_t>(1)};
            if(!selection.revision || selected.row()) throw DatabaseError("Selected deity readset selection invalid");
            std::vector<std::uint8_t> keys;
            sqlite_detail::Statement catalog(db_,"SELECT metadata_key,source_sha256 FROM main.native_companion_metadata WHERE family='GOD' ORDER BY metadata_key");
            while(catalog.row()) {
                const auto key=catalog.number<std::uint16_t>(0);
                if(catalog.text(1)!=source_sha256 || key<2801 || key>2834)
                    throw DatabaseError("Selected deity readset GOD source unqualified");
                keys.push_back(static_cast<std::uint8_t>(key-2800));
            }
            sqlite_detail::Statement row(db_,"SELECT row_key,declaration,status,skills,revision,source_sha256,authority,evidence_id FROM main.character_deities WHERE character_id=? AND row_key=?");
            row.bind_id(1,character);row.bind(2,selection.key);
            if(!row.row()) throw DatabaseError("Selected deity readset selected row not owned");
            const auto declaration=RecoveredDeityState::Declaration::parse(row.blob(1,19,19));
            const auto status=RecoveredDeityState::Status::parse(row.blob(2,29,29));
            if(!declaration || !status) throw DatabaseError("Selected deity readset malformed records");
            RecoveredDeityState::Snapshot snapshot{*declaration,*status,{}};
            const auto bytes=row.blob(3,0,400);
            if(bytes.size()%4) throw DatabaseError("Selected deity readset malformed skills");
            for(std::size_t at=0;at<bytes.size();at+=4) {
                const auto saved=RecoveredDeityState::Skill::parse(bytes.subspan(at,4));
                if(!saved) throw DatabaseError("Selected deity readset malformed skill");
                snapshot.skills.push_back(*saved);
            }
            StoredDeity deity{std::move(snapshot),row.number<std::uint64_t>(4),{row.text(5),row.text(6),row.text(7)}};
            require_provenance(deity.provenance);
            if(!deity.revision || row.number<std::uint8_t>(0)!=selection.key ||
               deity.snapshot.status.key_raw()!=selection.key || !RecoveredDeityState::valid(deity.snapshot,keys))
                throw DatabaseError("Selected deity readset invalid saved snapshot");
            if(row.row()) throw DatabaseError("Selected deity readset duplicate selected row");
            for(const auto& saved:deity.snapshot.skills) {
                if(saved.encode()[2]==kind && saved.encode()[3]==skill) {
                    const auto exact=saved;
                    result=SelectedDeitySkillReadset(this,readset_identity_,account,character,selection,std::move(deity),exact);
                    break;
                }
            }
        }
    }
    fence();read.commit();
    if(readset_reentered_ || bool(sqlite3_get_autocommit(db_))==borrowed || sqlite3_total_changes64(db_)!=changes)
        throw DatabaseError("Selected deity readset completion changed");
    return result;
}
std::optional<StoredDeitySelection> SqliteCompanionRepository::load_deity_selection(std::uint64_t account,std::uint64_t character) {
    require_owner(account,character);
    sqlite_detail::Statement row(db_,"SELECT row_key,revision FROM character_deity_selection WHERE character_id=?");
    row.bind_id(1,character);
    if(!row.row()) return {};
    StoredDeitySelection value{row.number<std::uint8_t>(0),row.number<std::uint64_t>(1)};
    const auto owned=load_deities(account,character);
    if(!value.revision || std::none_of(owned.begin(),owned.end(),[&](const auto& deity){return deity.snapshot.status.key_raw()==value.key;}))
        throw DatabaseError("Saved deity selection is not owned");
    return value;
}
SqliteCompanionRepository::CommittedDeitySelection SqliteCompanionRepository::select_deity_with_source(
        std::uint64_t account,std::uint64_t character,std::uint8_t key,
        std::optional<StoredDeitySelection> expected,StoredDeity expected_deity) {
    if(readset_reading_) {
        readset_reentered_=true;
        throw DatabaseError("Deity selection source reentry rejected");
    }
    readset_reading_=true;readset_reentered_=false;
    struct Exit {bool& active;~Exit(){active=false;}} exit{readset_reading_};
    if(!db_ || !account || !character || !sqlite3_get_autocommit(db_))
        throw DatabaseError("Deity selection source requires own transaction and owner");
    auto changes=sqlite3_total_changes64(db_);
    sqlite_detail::Transaction transaction(db_);
    const auto fence=[&] {
        if(readset_reentered_ || sqlite3_get_autocommit(db_) || sqlite3_total_changes64(db_)!=changes)
            throw DatabaseError("Deity selection source changed during transaction");
    };
    fence();
    for(const auto* name:{"accounts","recovered_characters","native_companion_metadata",
                         "character_deities","character_deity_selection","battle_reservations","battle_settlements"}) {
        sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name=? COLLATE NOCASE OR tbl_name=? COLLATE NOCASE LIMIT 1");
        shadow.bind(1,std::string(name));shadow.bind(2,std::string(name));
        if(shadow.row()) throw DatabaseError("Deity selection source TEMP shadow rejected");
        sqlite_detail::Statement base(db_,"SELECT 1 FROM main.sqlite_master WHERE type='table' AND name=? COLLATE NOCASE");
        base.bind(1,std::string(name));
        if(!base.row() || base.row()) throw DatabaseError("Deity selection source table missing or ambiguous");
        sqlite_detail::Statement trigger(db_,"SELECT 1 FROM main.sqlite_master WHERE type='trigger' AND tbl_name=? COLLATE NOCASE LIMIT 1");
        trigger.bind(1,std::string(name));
        if(trigger.row()) throw DatabaseError("Deity selection source trigger rejected");
        fence();
    }
    const auto owner_current=[&] {
        sqlite_detail::Statement owner(db_,"SELECT 1 FROM main.recovered_characters c JOIN main.accounts a ON a.id=c.account_id WHERE c.account_id=? AND c.id=?");
        owner.bind_id(1,account);owner.bind_id(2,character);
        if(!owner.row() || owner.row()) throw DatabaseError("Deity selection source ownership rejected");
        require_no_pending_battle(character);
        fence();
    };
    owner_current();
    const auto owned=load_deities(account,character);
    const auto found=std::find_if(owned.begin(),owned.end(),[&](const auto& row){return row.snapshot.status.key_raw()==key;});
    if(expected_deity.snapshot.status.key_raw()!=key || found==owned.end() ||
       std::count_if(owned.begin(),owned.end(),[&](const auto& row){return row.snapshot.status.key_raw()==key;})!=1 ||
       !same_deity(*found,expected_deity))
        throw DatabaseError("Deity selection source full row conflict");
    fence();
    const auto read_selection=[&]() -> std::optional<StoredDeitySelection> {
        sqlite_detail::Statement row(db_,"SELECT row_key,revision FROM main.character_deity_selection WHERE character_id=?");
        row.bind_id(1,character);
        if(!row.row()) return {};
        const StoredDeitySelection value{row.number<std::uint8_t>(0),row.number<std::uint64_t>(1)};
        if(!value.revision || row.row() ||
           std::none_of(owned.begin(),owned.end(),[&](const auto& deity){return deity.snapshot.status.key_raw()==value.key;}))
            throw DatabaseError("Deity selection source malformed selection");
        return value;
    };
    const auto before=read_selection();
    if(before!=expected) throw DatabaseError("Deity selection source selection conflict");
    owner_current();
    const bool changed=!before || before->key!=key;
    const StoredDeitySelection after=changed ? StoredDeitySelection{key,next_revision(before?before->revision:0)} : *before;
    if(changed) {
        if(changes==std::numeric_limits<sqlite3_int64>::max())
            throw DatabaseError("Deity selection source change counter exhausted");
        sqlite_detail::Statement write(db_,before ?
            "UPDATE main.character_deity_selection SET row_key=?,revision=? WHERE character_id=? AND revision=?" :
            "INSERT INTO main.character_deity_selection(row_key,revision,character_id) VALUES(?,?,?)");
        write.bind(1,key);write.bind_id(2,after.revision);write.bind_id(3,character);
        if(before) write.bind_id(4,before->revision);
        write.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Deity selection source CAS rejected");
        ++changes;fence();
    }
    if(read_selection()!=std::optional{after}) throw DatabaseError("Deity selection source readback mismatch");
    const auto saved=load_deities(account,character);
    const auto actual=std::find_if(saved.begin(),saved.end(),[&](const auto& row){return row.snapshot.status.key_raw()==key;});
    if(actual==saved.end() ||
       std::count_if(saved.begin(),saved.end(),[&](const auto& row){return row.snapshot.status.key_raw()==key;})!=1 ||
       !same_deity(*actual,*found) || !same_deity(*actual,expected_deity))
        throw DatabaseError("Deity selection source full row readback mismatch");
    owner_current();
    // Every owning allocation is complete before COMMIT; nothing is observed
    // or validated after the durable selection. Only noexcept moves follow.
    auto data=std::make_shared<const CommittedDeitySelection::Data>(
        CommittedDeitySelection::Data{this,readset_identity_,account,character,
            std::move(expected_deity),before,after,changed});
    CommittedDeitySelection result(std::move(data));
    owner_current();fence();
    transaction.commit();
    return result;
}
StoredDeitySelection SqliteCompanionRepository::select_deity(std::uint64_t account,std::uint64_t character,
        std::uint8_t key,const std::optional<StoredDeitySelection>& expected) {
    sqlite_detail::Transaction transaction(db_);
    const auto owned=load_deities(account,character);
    if(std::none_of(owned.begin(),owned.end(),[&](const auto& deity){return deity.snapshot.status.key_raw()==key;}))
        throw DatabaseError("Requested deity is not owned");
    if(load_deity_selection(account,character)!=expected) throw DatabaseError("Deity selection conflict");
    require_no_pending_battle(character);
    if(expected && expected->key==key) {transaction.commit();return *expected;}
    StoredDeitySelection next{key,next_revision(expected?expected->revision:0)};
    sqlite_detail::Statement write(db_,expected ?
        "UPDATE character_deity_selection SET row_key=?,revision=? WHERE character_id=? AND revision=?" :
        "INSERT INTO character_deity_selection(row_key,revision,character_id) VALUES(?,?,?)");
    write.bind(1,key);write.bind_id(2,next.revision);write.bind_id(3,character);
    if(expected) write.bind_id(4,expected->revision);
    write.done();
    if(sqlite3_changes(db_)!=1 || load_deity_selection(account,character)!=std::optional{next})
        throw DatabaseError("Deity selection readback mismatch");
    transaction.commit();return next;
}
StoredDeity SqliteCompanionRepository::store_deity(std::uint64_t account,std::uint64_t character,
        const RecoveredDeityState::Snapshot& snapshot,std::optional<std::uint64_t> expected_revision,
        const CompanionProvenance& provenance) {
    require_provenance(provenance);
    if(!RecoveredDeityState::valid(snapshot,deity_template_keys())) throw DatabaseError("Invalid deity import snapshot");
    sqlite_detail::Transaction transaction(db_);const auto owned=load_deities(account,character);
    const auto key=snapshot.status.key_raw();
    const auto found=std::find_if(owned.begin(),owned.end(),[&](const auto& value){return value.snapshot.status.key_raw()==key;});
    const auto revision=found==owned.end()?std::optional<std::uint64_t>{}:std::optional{found->revision};
    if(revision!=expected_revision || (!revision && owned.size()>=RecoveredDeityState::row_capacity))
        throw DatabaseError("Deity import revision/capacity rejected");
    require_no_pending_battle(character);const auto next=next_revision(revision.value_or(0));
    sqlite_detail::Statement write(db_,revision ?
        "UPDATE character_deities SET declaration=?,status=?,skills=?,revision=?,source_sha256=?,authority=?,evidence_id=? WHERE character_id=? AND row_key=? AND revision=?" :
        "INSERT INTO character_deities(declaration,status,skills,revision,source_sha256,authority,evidence_id,character_id,row_key) VALUES(?,?,?,?,?,?,?,?,?)");
    write.bind_blob(1,snapshot.declaration.encode());write.bind_blob(2,snapshot.status.encode());
    write.bind_blob(3,skills_blob(snapshot));write.bind_id(4,next);write.bind(5,provenance.source_sha256);
    write.bind(6,provenance.authority);write.bind(7,provenance.evidence_id);write.bind_id(8,character);write.bind(9,key);
    if(revision) write.bind_id(10,*revision);
    write.done();if(sqlite3_changes(db_)!=1) throw DatabaseError("Deity import write rejected");
    const auto after=load_deities(account,character);
    const auto saved=std::find_if(after.begin(),after.end(),[&](const auto& value){return value.snapshot.status.key_raw()==key;});
    if(saved==after.end() || saved->revision!=next || saved->provenance!=provenance ||
       saved->snapshot.declaration.encode()!=snapshot.declaration.encode() || saved->snapshot.status.encode()!=snapshot.status.encode() ||
       skills_blob(saved->snapshot)!=skills_blob(snapshot)) throw DatabaseError("Deity import readback mismatch");
    // CUSTOM-0039: the first explicit acquisition also establishes an owned
    // initial selection. Later acquisitions must not change the player's choice.
    if(!load_deity_selection(account,character)) {
        sqlite_detail::Statement select(db_,"INSERT INTO character_deity_selection(character_id,row_key,revision) VALUES(?,?,1)");
        select.bind_id(1,character);select.bind(2,key);select.done();
        if(sqlite3_changes(db_)!=1 || load_deity_selection(account,character)!=std::optional{StoredDeitySelection{key,1}})
            throw DatabaseError("Initial deity selection readback mismatch");
    }
    auto result=*saved;transaction.commit();return result;
}
std::vector<StoredPet2Slot> SqliteCompanionRepository::load_pet2_slots(std::uint64_t account,std::uint64_t character) {
    require_owner(account,character);
    sqlite_detail::Statement rows(db_,"SELECT slot,metadata,stats,revision,source_sha256,authority,evidence_id FROM character_pet2_slots WHERE character_id=? ORDER BY slot");
    rows.bind_id(1,character);std::vector<StoredPet2Slot> result;
    while(rows.row()) {
        StoredPet2Slot value{rows.number<std::uint8_t>(0),{},rows.number<std::uint64_t>(3),{rows.text(4),rows.text(5),rows.text(6)}};
        require_provenance(value.provenance);
        if(value.slot<42 || value.slot>44 || !value.revision) throw DatabaseError("Invalid saved pet2 slot");
        const auto metadata=rows.blob(1,0,20);const auto bytes=rows.blob(2,0,73);
        if(metadata.empty()!=bytes.empty()) throw DatabaseError("Incomplete pet2 snapshot");
        if(!metadata.empty()) {
            if(bytes.size()==RecoveredPet1Stats::logical_size) {
                const auto stats=RecoveredPet1Stats::parse_logical(bytes);
                if(metadata.size()!=20 || !stats || stats->slot()!=value.slot)throw DatabaseError("Malformed saved pet1 snapshot");
                RecoveredPet1Lifecycle::Metadata inventory;std::copy(metadata.begin(),metadata.end(),inventory.begin());
                value.pet1=RecoveredPet1Lifecycle::Snapshot{{account,character},inventory,*stats};
                if(!RecoveredPet1Lifecycle::valid({{account,character},true,false},*value.pet1,[&](auto key){return resolves_pet1(key);}))
                    throw DatabaseError("Invalid saved owned pet1 metadata");
                result.push_back(std::move(value));continue;
            }
            const auto stats=RecoveredPet2Stats::parse_logical(bytes);
            if(metadata.size()!=20 || !stats || stats->slot()!=value.slot) throw DatabaseError("Malformed saved pet2 snapshot");
            RecoveredPet2Lifecycle::Metadata inventory;std::copy(metadata.begin(),metadata.end(),inventory.begin());
            value.pet=RecoveredPet2Lifecycle::Snapshot{{account,character},inventory,*stats};
            value.display_category=NativePet2CategoryCatalog(db_).lookup(stats->category_selector());
            if(!RecoveredPet2Lifecycle::valid({{account,character},true,false},*value.pet,[&](auto key){return resolves_pet2(key);}))
                throw DatabaseError("Invalid saved owned pet2 metadata");
        }
        result.push_back(std::move(value));
    }
    return result;
}
std::size_t SqliteCompanionRepository::provision_pet2_slots(std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Transaction transaction(db_);require_owner(account,character);require_no_pending_battle(character);
    const auto before=load_pet2_slots(account,character);std::size_t count=0;
    for(std::uint8_t slot=42;slot<=44;++slot) {
        if(std::any_of(before.begin(),before.end(),[&](const auto& value){return value.slot==slot;})) continue;
        sqlite_detail::Statement insert(db_,"INSERT INTO character_pet2_slots(character_id,slot,metadata,stats,revision,source_sha256,authority,evidence_id) VALUES(?,?,X'',X'',1,?,'CUSTOM_DESIGNED','CUSTOM-0039:explicit-empty-capacity')");
        insert.bind_id(1,character);insert.bind(2,slot);insert.bind(3,std::string(source_sha256));insert.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Pet2 allocation failed");
        ++count;
    }
    const auto after=load_pet2_slots(account,character);
    if(after.size()!=3) throw DatabaseError("Incomplete pet2 capacity");
    for(const auto& old:before) {
        const auto found=std::find_if(after.begin(),after.end(),[&](const auto& value){return value.slot==old.slot;});
        if(found==after.end() || !same_pet(*found,old)) throw DatabaseError("Pet2 allocation changed existing instance");
    }
    transaction.commit();return count;
}
StoredPet2Slot SqliteCompanionRepository::store_pet2(std::uint64_t account,std::uint64_t character,std::uint8_t slot,
        const RecoveredPet2Lifecycle::Snapshot& pet,std::uint64_t expected_revision,const CompanionProvenance& provenance) {
    require_provenance(provenance);
    if(slot!=pet.stats.slot() || !RecoveredPet2Lifecycle::valid({{account,character},true,false},pet,[&](auto key){return resolves_pet2(key);}))
        throw DatabaseError("Invalid pet2 import snapshot");
    sqlite_detail::Transaction transaction(db_);const auto before=load_pet2_slots(account,character);
    const auto found=std::find_if(before.begin(),before.end(),[&](const auto& value){return value.slot==slot;});
    if(found==before.end() || found->revision!=expected_revision) throw DatabaseError("Pet2 import revision conflict");
    require_no_pending_battle(character);StoredPet2Slot next{slot,pet,next_revision(expected_revision),provenance};
    sqlite_detail::Statement write(db_,"UPDATE character_pet2_slots SET metadata=?,stats=?,revision=?,source_sha256=?,authority=?,evidence_id=? WHERE character_id=? AND slot=? AND revision=?");
    write.bind_blob(1,pet.inventory);write.bind_blob(2,RecoveredPet2Stats::encode_logical(pet.stats));
    write.bind_id(3,next.revision);write.bind(4,provenance.source_sha256);write.bind(5,provenance.authority);
    write.bind(6,provenance.evidence_id);write.bind_id(7,character);write.bind(8,slot);write.bind_id(9,expected_revision);write.done();
    const auto after=load_pet2_slots(account,character);
    const auto saved=std::find_if(after.begin(),after.end(),[&](const auto& value){return value.slot==slot;});
    if(sqlite3_changes(db_)!=1 || saved==after.end() || !same_pet(*saved,next)) throw DatabaseError("Pet2 import readback mismatch");
    auto result=*saved;transaction.commit();return result;
}
StoredPet2Slot SqliteCompanionRepository::store_pet1(std::uint64_t account,std::uint64_t character,std::uint8_t slot,
        const RecoveredPet1Lifecycle::Snapshot& pet,std::uint64_t expected_revision,const CompanionProvenance& provenance) {
    require_provenance(provenance);
    if(slot!=pet.stats.slot() || !RecoveredPet1Lifecycle::valid({{account,character},true,false},pet,[&](auto key){return resolves_pet1(key);}))
        throw DatabaseError("Invalid pet1 import snapshot");
    sqlite_detail::Transaction transaction(db_);const auto before=load_pet2_slots(account,character);
    const auto found=std::find_if(before.begin(),before.end(),[&](const auto& value){return value.slot==slot;});
    if(found==before.end() || found->revision!=expected_revision)throw DatabaseError("Pet1 import revision conflict");
    require_no_pending_battle(character);StoredPet2Slot next{slot,{},next_revision(expected_revision),provenance,{},pet};
    sqlite_detail::Statement write(db_,"UPDATE character_pet2_slots SET metadata=?,stats=?,revision=?,source_sha256=?,authority=?,evidence_id=? WHERE character_id=? AND slot=? AND revision=?");
    write.bind_blob(1,pet.inventory);write.bind_blob(2,RecoveredPet1Stats::encode_logical(pet.stats));
    write.bind_id(3,next.revision);write.bind(4,provenance.source_sha256);write.bind(5,provenance.authority);
    write.bind(6,provenance.evidence_id);write.bind_id(7,character);write.bind(8,slot);write.bind_id(9,expected_revision);write.done();
    if(sqlite3_changes(db_)!=1)throw DatabaseError("Pet1 import write rejected");
    const auto after=load_pet2_slots(account,character);
    const auto saved=std::find_if(after.begin(),after.end(),[&](const auto& value){return value.slot==slot;});
    if(saved==after.end() || !same_pet(*saved,next))throw DatabaseError("Pet1 import readback mismatch");
    auto result=*saved;transaction.commit();return result;
}
Pet2TransferCommit SqliteCompanionRepository::transfer_pet2(std::uint64_t account,std::uint64_t character,
        const StoredPet2Slot& source,const StoredPet2Slot& destination) {
    if(!source.occupied() || (source.pet && source.pet1) || (destination.pet && destination.pet1) || source.slot==destination.slot ||
       (source.slot==44 ? destination.slot<42 || destination.slot>43 || destination.occupied() :
                         (source.slot<42 || source.slot>43 || destination.slot!=44)))
        throw DatabaseError("Invalid pet2 selection destination");
    sqlite_detail::Transaction transaction(db_);const auto before=load_pet2_slots(account,character);
    const auto current_source=std::find_if(before.begin(),before.end(),[&](const auto& value){return value.slot==source.slot;});
    const auto current_destination=std::find_if(before.begin(),before.end(),[&](const auto& value){return value.slot==destination.slot;});
    if(current_source==before.end() || current_destination==before.end() || !same_pet(*current_source,source) || !same_pet(*current_destination,destination))
        throw DatabaseError("Pet2 transfer version conflict");
    require_no_pending_battle(character);
    Pet2TransferCommit next{destination,source};next.source.slot=source.slot;next.destination.slot=destination.slot;
    next.source.revision=next_revision(source.revision);next.destination.revision=next_revision(destination.revision);
    const auto reroute=[](StoredPet2Slot& value) {
        if(value.pet1) {
            auto bytes=RecoveredPet1Stats::encode_logical(value.pet1->stats);bytes[0x27]=value.slot;
            value.pet1->stats=RecoveredPet1Stats::parse_logical(bytes).value();return;
        }
        if(!value.pet) return;
        auto bytes=RecoveredPet2Stats::encode_logical(value.pet->stats);bytes[3]=value.slot;
        value.pet->stats=RecoveredPet2Stats::parse_logical(bytes).value();
    };
    reroute(next.source);reroute(next.destination);
    const auto write=[&](const StoredPet2Slot& value,std::uint64_t expected) {
        sqlite_detail::Statement update(db_,"UPDATE character_pet2_slots SET metadata=?,stats=?,revision=?,source_sha256=?,authority=?,evidence_id=? WHERE character_id=? AND slot=? AND revision=?");
        if(value.pet1) {update.bind_blob(1,value.pet1->inventory);update.bind_blob(2,RecoveredPet1Stats::encode_logical(value.pet1->stats));}
        else if(value.pet) {update.bind_blob(1,value.pet->inventory);update.bind_blob(2,RecoveredPet2Stats::encode_logical(value.pet->stats));}
        else {update.bind_blob(1,{});update.bind_blob(2,{});}
        update.bind_id(3,value.revision);update.bind(4,value.provenance.source_sha256);update.bind(5,value.provenance.authority);
        update.bind(6,value.provenance.evidence_id);update.bind_id(7,character);update.bind(8,value.slot);update.bind_id(9,expected);update.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Pet2 transfer write rejected");
    };
    write(next.source,source.revision);write(next.destination,destination.revision);
    const auto after=load_pet2_slots(account,character);
    for(const auto* expected:{&next.source,&next.destination}) {
        const auto saved=std::find_if(after.begin(),after.end(),[&](const auto& value){return value.slot==expected->slot;});
        if(saved==after.end() || !same_pet(*saved,*expected)) throw DatabaseError("Pet2 transfer readback mismatch");
    }
    transaction.commit();return next;
}
}
