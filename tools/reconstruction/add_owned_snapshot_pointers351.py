"""Source-only corrective successor; preserve original candidate/generator unchanged."""
from pathlib import Path
import hashlib
import json
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(n,b):
 p=OUT/n
 if p.exists():raise RuntimeError('Refusing overwrite '+n)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
paths=['src/db/SqliteOwnedBlacklistRepository.h','src/db/SqliteOwnedBlacklistRepository.cpp','src/handlers/OwnedBlacklistService.cpp']
original={p:(ROOT/p).read_bytes() for p in paths}
old={p:b.decode().replace('\r\n','\n') for p,b in original.items()}
new=dict(old);edits=[]
def edit(p,a,b):
 if new[p].count(a)!=1:raise RuntimeError('Nonunique correction '+p)
 new[p]=new[p].replace(a,b,1);edits.append({'path':p,'original':a,'replacement':b})
h,c,s=paths
edit(h,'#include <utility>\n','#include <utility>\n#include <memory>\n')
start=new[h].index('        const Snapshot& before() const noexcept')
end=new[h].index('    };\n    std::optional<CommittedChange> add_committed',start)
edit(h,new[h][start:end],'''        const Snapshot& before() const noexcept{return data_->before;}
        const Snapshot& after() const noexcept{return data_->after;}
        // Aliases the already-owned pre-COMMIT Data; refcount only, no allocation.
        std::shared_ptr<const Snapshot> before_ptr() const noexcept{return {data_,&data_->before};}
        std::shared_ptr<const Snapshot> after_ptr() const noexcept{return {data_,&data_->after};}
        const Row& row() const noexcept{return data_->row;}
        const std::vector<std::uint8_t>& logical() const noexcept{return data_->logical;}
        bool changed() const noexcept{return data_->changed;}
    private:
        friend class SqliteOwnedBlacklistRepository;
        friend class OwnedBlacklistService;
        struct Data {
            const Snapshot before,after;
            Row row;
            std::vector<std::uint8_t> logical;
            const bool changed;
            Data(Snapshot b,Snapshot a,Row r,std::vector<std::uint8_t> l,bool c) noexcept
                :before(std::move(b)),after(std::move(a)),row(std::move(r)),logical(std::move(l)),changed(c) {}
        };
        explicit CommittedChange(std::shared_ptr<Data> data) noexcept:data_(std::move(data)) {}
        std::shared_ptr<Data> data_;
''')
edit(c,'    return CommittedChange(before,Snapshot{true,std::move(after)},std::move(row),std::move(*logical),changed);\n','''    return CommittedChange(std::make_shared<CommittedChange::Data>(
        before,Snapshot{true,std::move(after)},std::move(row),std::move(*logical),changed));
''')
edit(c,'return std::optional<Row>(std::move(result->row_));','return std::optional<Row>(std::move(result->data_->row));') if new[c].count('return std::optional<Row>(std::move(result->row_));')==1 else None
# The two legacy row adapters have intentionally identical private extraction.
a='return std::optional<Row>(std::move(result->row_));'
b='return std::optional<Row>(std::move(result->data_->row));'
if new[c].count(a)!=2:raise RuntimeError('Expected two legacy row adapters')
new[c]=new[c].replace(a,b);edits.append({'path':c,'original':a,'replacement':b,'count':2})
edit(s,'return std::optional<std::vector<std::uint8_t>>(std::move(result->logical_));','return std::optional<std::vector<std::uint8_t>>(std::move(result->data_->logical));')
for p in paths:
 inverse=new[p]
 for e in reversed(edits):
  if e['path']==p:
   count=e.get('count',1)
   if inverse.count(e['replacement'])!=count:raise RuntimeError('Correction inverse nonunique')
   inverse=inverse.replace(e['replacement'],e['original'])
 ending='\r\n' if b'\r\n' in original[p] else '\n'
 if inverse.replace('\n',ending).encode()!=original[p]:raise RuntimeError('Correction inverse mismatch')
 if (ROOT/p).read_bytes()!=original[p]:raise RuntimeError('Candidate source changed')
 data=new[p].replace('\n',ending).encode();(ROOT/p).write_bytes(data);emit('owned-pointers-candidate/'+p,data)
emit('owned-pointer-correction.json',(json.dumps({'edits':edits,'inverse_to_original_candidate_byte_equal':True,
 'reason':'Actual Main needs owning whole snapshots without allocation/copy after COMMIT. One private Data/control block and both immutable Snapshot values allocated inside operation transaction before COMMIT.',
 'preserved_original_generator':'generate_blacklist_committed351.py',
 'files':[{'path':p,'before_bytes':len(original[p]),'before_sha256':sha(original[p]),'after_bytes':len((ROOT/p).read_bytes()),'after_sha256':sha((ROOT/p).read_bytes())} for p in paths]},indent=2)+'\n').encode())
print(json.dumps({'files':[{'path':p,'bytes':len((ROOT/p).read_bytes()),'sha256':sha((ROOT/p).read_bytes())} for p in paths]}))
