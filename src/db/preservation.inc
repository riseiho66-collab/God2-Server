using Rows=std::vector<std::vector<std::uint8_t>>;
using Guard=std::map<std::string,Rows>;
using Exclusions=std::map<std::string,std::string>;
std::string quoted(const std::string& value) {
    std::string result="\"";for(auto c:value){result+=c;if(c=='\"')result+=c;}return result+'\"';
}
void append_number(std::vector<std::uint8_t>& bytes,std::uint64_t value) {
    const auto at=bytes.size();bytes.resize(at+8);
    for(unsigned i=0;i<8;++i)bytes[at+i]=static_cast<std::uint8_t>(value>>(i*8));
}
Guard guard(sqlite3* db,const Exclusions& exclusions,const Guard* capacity_hint=nullptr) {
    Guard result;
    // Capture indexes/triggers as well as tables. Paired proofs cannot silently
    // install a future mutation through a schema side effect.
    sqlite_detail::Statement schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    while(schema.row()) {
        std::vector<std::uint8_t> bytes;
        for(int column=0;column<4;++column) {
            const auto value=schema.text(column);append_number(bytes,value.size());bytes.insert(bytes.end(),value.begin(),value.end());
        }
        result[":sqlite_master"].push_back(std::move(bytes));
    }
    sqlite_detail::Statement tables(db,"SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0),definition=tables.text(1);
        auto& rows=result[name+":schema"];rows.push_back({definition.begin(),definition.end()});
        const auto found=exclusions.find(name);
        const auto sql="SELECT * FROM "+quoted(name)+(found==exclusions.end()?"":" WHERE "+found->second);
        sqlite3_stmt* statement=nullptr;
        sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&statement,nullptr));
        struct Finalize {sqlite3_stmt* statement;~Finalize(){sqlite3_finalize(statement);}} finalize{statement};
        auto& data=result[name];
        if(capacity_hint) {
            const auto hint=capacity_hint->find(name);
            if(hint!=capacity_hint->end())data.reserve(hint->second.size());
        }
        // SQLite values/pointers are valid until the next step/reset. Cache each
        // cell once, then allocate exactly one typed row without vector growth.
        // Hints reserve capacity only: every actual row/column is still read on
        // each of the baseline and both post-write preservation comparisons.
        struct Cell {int type=SQLITE_NULL,size=0;std::uint64_t number=0;const std::uint8_t* bytes=nullptr;};
        const auto column_count=sqlite3_column_count(statement);
        std::vector<Cell> cells(static_cast<std::size_t>(column_count));int rc;
        while((rc=sqlite3_step(statement))==SQLITE_ROW) {
            std::size_t row_size=static_cast<std::size_t>(column_count);
            for(int column=0;column<column_count;++column) {
                auto& cell=cells[static_cast<std::size_t>(column)];cell.type=sqlite3_column_type(statement,column);
                std::size_t extra=0;
                if(cell.type==SQLITE_INTEGER) {cell.number=static_cast<std::uint64_t>(sqlite3_column_int64(statement,column));extra=8;}
                else if(cell.type==SQLITE_FLOAT) {cell.number=std::bit_cast<std::uint64_t>(sqlite3_column_double(statement,column));extra=8;}
                else if(cell.type==SQLITE_TEXT || cell.type==SQLITE_BLOB) {
                    cell.size=sqlite3_column_bytes(statement,column);
                    // Preserve the original bytes-before-blob conversion order:
                    // TEXT in a UTF-16 database must be normalized to the same
                    // UTF-8 byte representation before obtaining its pointer.
                    cell.bytes=static_cast<const std::uint8_t*>(sqlite3_column_blob(statement,column));
                    require(cell.size>=0 && (!cell.size || cell.bytes!=nullptr),"Cannot preserve database row");
                    extra=8+static_cast<std::size_t>(cell.size);
                }
                require(extra<=std::numeric_limits<std::size_t>::max()-row_size,"Preserved database row size overflow");
                row_size+=extra;
            }
            std::vector<std::uint8_t> row(row_size);auto* write=row.data();
            const auto number=[&write](std::uint64_t value) {
                if constexpr(std::endian::native==std::endian::little)std::memcpy(write,&value,8);
                else for(unsigned i=0;i<8;++i)write[i]=static_cast<std::uint8_t>(value>>(i*8));
                write+=8;
            };
            for(const auto& cell:cells) {
                *write++=static_cast<std::uint8_t>(cell.type);
                if(cell.type==SQLITE_INTEGER || cell.type==SQLITE_FLOAT)number(cell.number);
                else if(cell.type==SQLITE_TEXT || cell.type==SQLITE_BLOB) {
                    number(static_cast<std::uint64_t>(cell.size));
                    if(cell.size){std::memcpy(write,cell.bytes,static_cast<std::size_t>(cell.size));write+=cell.size;}
                }
            }
            require(write==row.data()+row.size(),"Preserved database row encoding mismatch");
            data.push_back(std::move(row));
        }
        require(rc==SQLITE_DONE,"Cannot preserve database rows");std::sort(data.begin(),data.end());
    }
    return result;
}
void unchanged(sqlite3* db,const Guard& before,const Exclusions& exclusions) {
    require(guard(db,exclusions,&before)==before,"Guild operation changed unrelated saved rows/schema");
}
