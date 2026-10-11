#include <windows.h>
#include <stdio.h>
int main(void) {
    char result[128];
    sprintf_s(result,sizeof(result),"ACP=%u SYSTEM_LANG=%04X USER_LANG=%04X\n",GetACP(),
        GetSystemDefaultLangID(),GetUserDefaultLangID());
    printf("%s",result);
    char path[MAX_PATH];
    if(GetEnvironmentVariableA("GOD2_LOCALE_PROBE_OUTPUT",path,MAX_PATH)>0){
        FILE* output=NULL;
        if(fopen_s(&output,path,"wb")==0){fputs(result,output);fclose(output);}
    }
    return 0;
}
