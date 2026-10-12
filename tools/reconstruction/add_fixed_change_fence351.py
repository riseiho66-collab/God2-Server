"""Source-only second correction; preserve both previous successful stages unchanged."""
from pathlib import Path
import hashlib
import json
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
paths=['src/db/SqliteOwnedBlacklistRepository.h','src/db/SqliteOwnedBlacklistRepository.cpp']
oldbytes={p:(ROOT/p).read_bytes() for p in paths}
old={p:b.decode().replace('\r\n','\n') for p,b in oldbytes.items()};new=dict(old);edits=[]
def edit(p,a,b,count=1):
 if new[p].count(a)!=count:raise RuntimeError('Unexpected correction count '+p+' '+a[:50])
 new[p]=new[p].replace(a,b);edits.append({'path':p,'original':a,'replacement':b,'count':count})
def emit(name,b):
 p=OUT/name
 if p.exists():raise RuntimeError('Refusing overwrite '+name)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
h,c=paths
edit(h,'''            const bool changed;
            Data(Snapshot b,Snapshot a,Row r,std::vector<std::uint8_t> l,bool c) noexcept
                :before(std::move(b)),after(std::move(a)),row(std::move(r)),logical(std::move(l)),changed(c) {}
''','''            const bool changed;
            const sqlite3_int64 staged_changes;
            Data(Snapshot b,Snapshot a,Row r,std::vector<std::uint8_t> l,bool c,sqlite3_int64 changes) noexcept
                :before(std::move(b)),after(std::move(a)),row(std::move(r)),logical(std::move(l)),changed(c),staged_changes(changes) {}
''')
edit(h,'    CommittedChange prepare_committed_change(const Snapshot&,Row,bool,Operation&,const Root&,const Root*);\n','''    CommittedChange prepare_committed_change(const Snapshot&,Row,bool,Operation&,const Root&,const Root*);
    void check_committed_change(const CommittedChange&);
''')
edit(c,'''        const Snapshot& before,Row row,bool changed,Operation& operation,const Root& root,const Root* target) {
    const auto target_root''','''        const Snapshot& before,Row row,bool changed,Operation& operation,const Root& root,const Root* target) {
    const auto changes=sqlite3_total_changes64(db_); // Fixed after the intended write, including no-op.
    if(sqlite3_get_autocommit(db_))throw DatabaseError("Blacklist committed material lost transaction");
    const auto target_root''')
edit(c,'''    return CommittedChange(std::make_shared<CommittedChange::Data>(
        before,Snapshot{true,std::move(after)},std::move(row),std::move(*logical),changed));
}
''','''    CommittedChange result(std::make_shared<CommittedChange::Data>(
        before,Snapshot{true,std::move(after)},std::move(row),std::move(*logical),changed,changes));
    check_committed_change(result);return result;
}
void SqliteOwnedBlacklistRepository::check_committed_change(const CommittedChange& result) {
    if(sqlite3_get_autocommit(db_) || sqlite3_total_changes64(db_)!=result.data_->staged_changes)
        throw DatabaseError("Blacklist committed material transaction/storage changed");
}
''')
edit(c,'        operation.roots(root);transaction.commit();return result;\n','        operation.roots(root);check_committed_change(*result);transaction.commit();return result;\n')
edit(c,'    operation.roots(root,target_root);transaction.commit();return result;\n','    operation.roots(root,target_root);check_committed_change(*result);transaction.commit();return result;\n')
edit(c,'''    std::optional<CommittedChange> result(prepare_committed_change(before,std::move(selected),changed,operation,root,nullptr));
    operation.roots(root);transaction.commit();return result;
''','''    std::optional<CommittedChange> result(prepare_committed_change(before,std::move(selected),changed,operation,root,nullptr));
    operation.roots(root);check_committed_change(*result);transaction.commit();return result;
''')
for p in paths:
 inverse=new[p]
 for e in reversed(edits):
  if e['path']==p:
   if inverse.count(e['replacement'])!=e['count']:raise RuntimeError('Inverse count mismatch')
   inverse=inverse.replace(e['replacement'],e['original'])
 ending='\r\n' if b'\r\n' in oldbytes[p] else '\n'
 if inverse.replace('\n',ending).encode()!=oldbytes[p]:raise RuntimeError('Inverse mismatch')
 if (ROOT/p).read_bytes()!=oldbytes[p]:raise RuntimeError('Candidate changed')
 data=new[p].replace('\n',ending).encode();(ROOT/p).write_bytes(data);emit('fixed-fence-candidate/'+p,data)
emit('fixed-change-fence-correction.json',(json.dumps({'edits':edits,'inverse_to_owned_pointer_candidate_byte_equal':True,
 'reason':'Fixed intended-write change count/autocommit must span actual after row reads, SQL root observers, wire/Data preparation and final root reads through the immediate preCOMMIT check. Current alone fences only each callback, not the full material interval.',
 'files':[{'path':p,'before_bytes':len(oldbytes[p]),'before_sha256':sha(oldbytes[p]),'after_bytes':len((ROOT/p).read_bytes()),'after_sha256':sha((ROOT/p).read_bytes())} for p in paths]},indent=2)+'\n').encode())
print(json.dumps({'files':[{'path':p,'bytes':len((ROOT/p).read_bytes()),'sha256':sha((ROOT/p).read_bytes())} for p in paths]}))
