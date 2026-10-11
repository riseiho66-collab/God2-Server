#include "db/NativeMultiMessageCatalog.h"
#include <sqlite3.h>
#include <iostream>
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    sqlite3* db=nullptr;
    if(sqlite3_open_v2(argv[1],&db,SQLITE_OPEN_READONLY,nullptr)!=SQLITE_OK){sqlite3_close(db);return 3;}
    int result=0;
    try {god2::NativeMultiMessageCatalog catalog(db);std::cout<<catalog.knowledge_menu_count()<<'\n';}
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';result=1;}
    sqlite3_close(db);return result;
}
