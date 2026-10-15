#include "db/MySql80ExportFormat.h"
#include "db/ServerDataDictionary.h"
#include "db/DbTypes.h"
#include <algorithm>
#include <charconv>
#include <limits>
#include <ostream>
#include <set>
#include <string_view>
namespace god2 {
namespace {
using F=MySql80ExportFormat;
void require(bool ok,const std::string& text){if(!ok)throw DatabaseError("MySQL8 export: "+text);}
std::size_t utf8_count(std::string_view s) {
    std::size_t count=0;
    for(std::size_t i=0;i<s.size();) {
        const auto a=static_cast<unsigned char>(s[i]);std::size_t n=0;std::uint32_t value=0,minimum=0;
        if(a<0x80){n=1;value=a;}
        else if(a>=0xc2&&a<=0xdf){n=2;value=a&31;minimum=0x80;}
        else if(a>=0xe0&&a<=0xef){n=3;value=a&15;minimum=0x800;}
        else if(a>=0xf0&&a<=0xf4){n=4;value=a&7;minimum=0x10000;}
        else throw DatabaseError("MySQL8 export: invalid UTF-8");
        require(n<=s.size()-i,"truncated UTF-8");
        for(std::size_t j=1;j<n;++j) {
            const auto b=static_cast<unsigned char>(s[i+j]);require((b&0xc0)==0x80,"invalid UTF-8 continuation");
            value=(value<<6)|(b&63);
        }
        require(value>=minimum&&value<=0x10ffff&&!(value>=0xd800&&value<=0xdfff),"noncanonical UTF-8");
        i+=n;++count;
    }
    return count;
}
std::string identifier(std::string_view name) {
    require(!name.empty()&&name.size()<=64,"identifier must contain 1..64 ASCII letters/digits/underscores");
    for(const auto c:name)require((c>='a'&&c<='z')||(c>='A'&&c<='Z')||
        (c>='0'&&c<='9')||c=='_', "unsupported identifier");
    const auto quote=static_cast<char>(0x60);
    return std::string(1,quote)+std::string(name)+quote;
}
std::string folded_identifier(std::string_view value) {
    identifier(value);std::string result(value);
    for(auto& c:result)if(c>='A'&&c<='Z')c=static_cast<char>(c-'A'+'a');
    return result;
}
std::string comment(std::string_view value,std::size_t limit) {
    require(!value.empty()&&utf8_count(value)<=limit,"missing or oversized readable comment");
    require(value.find('\0')==std::string_view::npos,"NUL in comment");
    std::string result="'";
    for(const auto c:value){if(c=='\'')result+="''";else result+=c;}
    return result+"'";
}
std::string table_comment(const F::Table& table) {
    if(!table.comment_zh.empty())return table.comment_zh;
    const auto* known=ServerDataDictionary::find_table(table.name);
    require(known!=nullptr,"unclassified table "+table.name+" needs an explicit readable description");
    return std::string(known->title_zh)+"；"+std::string(known->purpose_zh);
}
std::string column_comment(const F::Table& table,const F::Column& column) {
    if(!column.comment_zh.empty())return column.comment_zh;
    const auto* known=ServerDataDictionary::find_column(table.name,column.name);
    require(known!=nullptr,"unclassified column "+table.name+"."+column.name+" needs explicit meaning/unit/source");
    return std::string(known->title_zh)+"；"+std::string(known->purpose_zh);
}
std::string type(const F::Column& c) {
    if(c.kind==F::Kind::Signed64||c.kind==F::Kind::Unsigned64) {
        require(!c.width,"integer width is not a character width");
        return c.kind==F::Kind::Signed64?"BIGINT":"BIGINT UNSIGNED";
    }
    if(c.kind==F::Kind::Utf8Text) {
        if(!c.width)return "LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin";
        require(*c.width&&*c.width<=15000,"text width exceeds supported target row bound");
        return "VARCHAR("+std::to_string(*c.width)+") CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin";
    }
    require(c.kind==F::Kind::Binary,"unknown column kind");
    if(!c.width)return "LONGBLOB";
    require(*c.width&&*c.width<=60000,"binary width exceeds supported target row bound");
    return "VARBINARY("+std::to_string(*c.width)+")";
}
std::string key_columns(const F::Table& t,const std::vector<std::size_t>& columns,bool primary) {
    require(!columns.empty()&&columns.size()<=16,"key must have 1..16 parts");
    std::set<std::size_t> seen;std::uint64_t bytes=0;std::string result="(";
    for(const auto index:columns) {
        require(index<t.columns.size()&&seen.insert(index).second,"invalid/duplicate key column");
        const auto& c=t.columns[index];if(primary)require(!c.nullable,"nullable primary key requires an explicit source mapping");
        if(c.kind==F::Kind::Signed64||c.kind==F::Kind::Unsigned64)bytes+=8;
        else {require(c.width.has_value(),"TEXT/BLOB key needs an explicit lossless reviewed bound, never a prefix");bytes+=std::uint64_t(*c.width)*(c.kind==F::Kind::Utf8Text?4:1);}
        if(seen.size()>1)result+=",";
        result+=identifier(c.name);
    }
    require(bytes<=3072,"key exceeds InnoDB3072-byte bound; prefix truncation is forbidden");
    return result+")";
}
template<class T>std::string decimal(T value) {
    char buffer[32];const auto result=std::to_chars(buffer,buffer+sizeof(buffer),value);
    require(result.ec==std::errc{},"integer formatting failed");
    return std::string(buffer,result.ptr);
}
void hex(std::ostream& out,std::span<const std::uint8_t> bytes) {
    constexpr char digits[]="0123456789abcdef";out<<"X'";
    for(const auto b:bytes){out.put(digits[b>>4]);out.put(digits[b&15]);}
    out.put('\'');
}
void validate_value(const F::Column& c,const F::Value& v) {
    if(std::holds_alternative<std::monostate>(v)){require(c.nullable,"NULL in nonnullable column "+c.name);return;}
    switch(c.kind) {
    case F::Kind::Signed64:require(std::holds_alternative<std::int64_t>(v),"signed64 storage mismatch "+c.name);return;
    case F::Kind::Unsigned64:require(std::holds_alternative<std::uint64_t>(v),"unsigned64 storage mismatch "+c.name);return;
    case F::Kind::Utf8Text:{
        const auto* text=std::get_if<std::string>(&v);require(text!=nullptr,"text storage mismatch "+c.name);
        const auto size=utf8_count(*text);require(!c.width||size<=*c.width,"text exceeds reviewed width "+c.name);return;}
    case F::Kind::Binary:{
        const auto* blob=std::get_if<std::vector<std::uint8_t>>(&v);require(blob!=nullptr,"binary storage mismatch "+c.name);
        require(!c.width||blob->size()<=*c.width,"binary exceeds reviewed width "+c.name);return;}
    }
    throw DatabaseError("MySQL8 export: unknown value kind");
}
void value(std::ostream& out,const F::Value& v) {
    if(std::holds_alternative<std::monostate>(v))out<<"NULL";
    else if(const auto* n=std::get_if<std::int64_t>(&v))out<<decimal(*n);
    else if(const auto* n=std::get_if<std::uint64_t>(&v))out<<decimal(*n);
    else if(const auto* s=std::get_if<std::string>(&v)) {
        out<<"_utf8mb4 ";hex(out,{reinterpret_cast<const std::uint8_t*>(s->data()),s->size()});
    } else hex(out,std::get<std::vector<std::uint8_t>>(v));
}
}
MySql80ExportFormat::Report MySql80ExportFormat::write_snapshot(
        Schema schema,std::vector<TableRows> data,std::ostream& out) {
    require(schema.target_innodb_page_bytes==16384,"this format profile requires an explicit 16KB InnoDB page target");
    require(schema.sqlite_source_version>0,"missing source schema version");
    require(schema.sqlite_source_schema_sha256.size()==64&&
        std::all_of(schema.sqlite_source_schema_sha256.begin(),schema.sqlite_source_schema_sha256.end(),
            [](char c){return(c>='0'&&c<='9')||(c>='a'&&c<='f');}),"invalid source schema digest");
    require(!schema.tables.empty()&&data.size()==schema.tables.size(),"need exactly one row collection per declared table");
    std::set<std::string> names;Report report;
    // Validate the entire caller-owned image before producing any SQL.
    for(const auto& t:schema.tables) {
        identifier(t.name);require(names.insert(folded_identifier(t.name)).second,"case-colliding table");
        require(!t.columns.empty()&&t.columns.size()<=1017,"table must contain 1..1017 columns");
        require(t.unique_keys.size()<=64,"at most64 secondary indexes");
        comment(table_comment(t),2048);
        std::set<std::string> columns,keys;std::uint64_t inline_bytes=0;
        for(const auto& c:t.columns) {
            identifier(c.name);require(columns.insert(folded_identifier(c.name)).second,"case-colliding column");
            type(c);comment(column_comment(t,c),1024);
            if(c.kind==Kind::Signed64||c.kind==Kind::Unsigned64)inline_bytes+=8;
            else if(c.width)inline_bytes+=std::uint64_t(*c.width)*(c.kind==Kind::Utf8Text?4:1)+2;
            else inline_bytes+=20;
        }
        require(inline_bytes<=60000,"target row bound exceeds supported layout; no silent width reduction");
        require(!t.primary_key.empty(),"explicit primary key required for snapshot ordering/identity");
        key_columns(t,t.primary_key,true);
        for(const auto& k:t.unique_keys){const auto name=folded_identifier(k.name);require(name!="primary","reserved primary index name");require(keys.insert(name).second,"case-colliding key name");key_columns(t,k.columns,false);}
        const auto count=std::count_if(data.begin(),data.end(),[&](const auto& x){return x.table==t.name;});
        require(count==1,"missing/duplicate rows for "+t.name);
        const auto& rows=*std::find_if(data.begin(),data.end(),[&](const auto& x){return x.table==t.name;});
        std::vector<std::set<std::vector<Value>>> key_values(1+t.unique_keys.size());
        for(const auto& row:rows.rows) {
            require(row.size()==t.columns.size(),"row width mismatch "+t.name);
            for(std::size_t i=0;i<row.size();++i)validate_value(t.columns[i],row[i]);
            for(std::size_t k=0;k<key_values.size();++k) {
                const auto& parts=k==0?t.primary_key:t.unique_keys[k-1].columns;
                std::vector<Value> tuple;bool any_null=false;
                for(const auto index:parts){tuple.push_back(row[index]);any_null|=std::holds_alternative<std::monostate>(row[index]);}
                // Both target UNIQUE and SQLite treat a tuple with NULL as
                // nonconflicting; primary nullability was rejected above.
                if(!any_null)require(key_values[k].insert(std::move(tuple)).second,"duplicate primary/unique key in "+t.name);
            }
            require(report.rows<std::numeric_limits<std::uint64_t>::max(),"row count overflow");++report.rows;
        }
    }
    out<<"-- GOD2 MySQL8.0.17+ typed snapshot format; fresh empty target only.\n"
          "-- Source history remains SQLite provenance, not MySQL migration authority.\n"
          "-- No complete SQLite schema/snapshot/import validation is claimed by this formatter.\n"
          "-- Caller-reported SQLite source version (not verified): "<<decimal(schema.sqlite_source_version)<<"\n"
          "-- Caller-reported SQLite source schema sha256: "<<schema.sqlite_source_schema_sha256<<"\n"
          "SET @god2_export_saved_sql_mode=@@SESSION.sql_mode;\n"
          "SET SESSION sql_mode=CONCAT_WS(',',@@SESSION.sql_mode,'NO_BACKSLASH_ESCAPES','STRICT_ALL_TABLES');\n"
          "SET NAMES utf8mb4 COLLATE utf8mb4_0900_bin;\n";
    for(const auto& t:schema.tables) {
        out<<"CREATE TABLE "<<identifier(t.name)<<" (\n";
        for(const auto& c:t.columns)
            out<<"  "<<identifier(c.name)<<" "<<type(c)<<(c.nullable?" NULL":" NOT NULL")<<" COMMENT "<<comment("See "+t.name+".txt: "+c.name,1024)<<",\n";
        out<<"  PRIMARY KEY "<<key_columns(t,t.primary_key,true);
        for(const auto& k:t.unique_keys)out<<",\n  UNIQUE KEY "<<identifier(k.name)<<" "<<key_columns(t,k.columns,false);
        out<<"\n) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT="
           <<comment("See "+t.name+".txt",2048)<<";\n";
    }
    out<<"START TRANSACTION;\n";
    for(const auto& t:schema.tables) {
        const auto& rows=*std::find_if(data.begin(),data.end(),[&](const auto& x){return x.table==t.name;});
        std::vector<std::size_t> order;order.reserve(rows.rows.size());
        for(std::size_t i=0;i<rows.rows.size();++i)order.push_back(i);
        std::sort(order.begin(),order.end(),[&](std::size_t a,std::size_t b){
            for(const auto col:t.primary_key){if(rows.rows[a][col]<rows.rows[b][col])return true;if(rows.rows[b][col]<rows.rows[a][col])return false;}
            return false;
        });
        for(const auto index:order) {
            const auto& row=rows.rows[index];
            out<<"INSERT INTO "<<identifier(t.name)<<" (";
            for(std::size_t i=0;i<t.columns.size();++i){if(i)out<<",";out<<identifier(t.columns[i].name);}
            out<<") VALUES (";
            for(std::size_t i=0;i<row.size();++i){if(i)out<<",";value(out,row[i]);}
            out<<");\n";
        }
    }
    out<<"COMMIT;\nSET SESSION sql_mode=@god2_export_saved_sql_mode;\n";
    require(bool(out),"output stream failure");
    report.tables=schema.tables.size();report.typed_snapshot_serialized=true;
    // The source reader and real target-import checks are separate future work.
    return report;
}
}
