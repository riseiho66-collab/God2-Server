#include "native_dialog.h"
#include <windows.h>
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <string>
#include <iostream>

using Json = nlohmann::json;
static std::wstring wide(const std::string& s) {
    int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s.data(),static_cast<int>(s.size()),nullptr,0);
    std::wstring r(n,L'\0');
    MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s.data(),static_cast<int>(s.size()),r.data(),n);
    return r;
}
static std::string utf8(const std::wstring& s) {
    int n=WideCharToMultiByte(CP_UTF8,0,s.data(),static_cast<int>(s.size()),nullptr,0,nullptr,nullptr);
    std::string r(n,'\0');
    WideCharToMultiByte(CP_UTF8,0,s.data(),static_cast<int>(s.size()),r.data(),n,nullptr,nullptr);
    return r;
}
static std::wstring text(HWND h) {
    wchar_t b[2048]{}; DWORD_PTR result=0;
    if (!SendMessageTimeoutW(h,WM_GETTEXT,2048,reinterpret_cast<LPARAM>(b),SMTO_ABORTIFHUNG|SMTO_BLOCK,200,&result)) return L"";
    return b;
}
static bool classIs(HWND h,const wchar_t* expected) {
    wchar_t b[64]{}; GetClassNameW(h,b,64); return std::wstring(b)==expected;
}
struct NativeDialogController {
    DWORD pid{},tid{};
    std::wstring title,warning;
    HWND found{};
    HWND soleOk{}; unsigned buttons{};
    Json result;
    static BOOL CALLBACK child(HWND h,LPARAM p) {
        auto& pair=*reinterpret_cast<std::pair<NativeDialogController*,bool>*>(p);
        wchar_t name[64]{};GetClassNameW(h,name,64);
        pair.first->result["children"].push_back({{"id",GetDlgCtrlID(h)},{"class",utf8(name)},{"text",utf8(text(h))}});
        if(classIs(h,L"Button")) {
            ++pair.first->buttons;
            auto label=text(h);
            if(label==L"\u78ba\u5b9a" || label==L"OK" || label==L"&OK") pair.first->soleOk=h;
        }
        if (classIs(h,L"Static") && text(h)==pair.first->warning) pair.second=true;
        return TRUE;
    }
    static BOOL CALLBACK window(HWND h,LPARAM p) {
        auto& c=*reinterpret_cast<NativeDialogController*>(p);
        DWORD pid=0; DWORD tid=GetWindowThreadProcessId(h,&pid);
        if (pid!=c.pid || tid!=c.tid || !IsWindowVisible(h) || !classIs(h,L"#32770")) return TRUE;
        auto title=text(h);
        std::pair<NativeDialogController*,bool> match{&c,false};
        c.result["children"]=Json::array();
        c.soleOk=nullptr;c.buttons=0;
        EnumChildWindows(h,child,reinterpret_cast<LPARAM>(&match));
        c.result["candidate"]={{"hwnd",reinterpret_cast<uintptr_t>(h)},{"pid",pid},{"tid",tid},
            {"title",utf8(title)},{"text_matched",match.second},{"match",title==c.title && match.second}};
        if (title==c.title && match.second) { c.found=h; return FALSE; }
        return TRUE;
    }
    static void CALLBACK event(HWINEVENTHOOK,DWORD,HWND,LONG,LONG,DWORD,DWORD) {}
    Json run() {
        result={{"matched",false},{"ok_sent",false},{"closed",false},{"pid",pid},{"tid",tid},
            {"expected_title",utf8(title)},{"expected_text",utf8(warning)},{"started_tick_ms",GetTickCount64()}};
        const std::wstring accepted=L"\u7cfb\u7d71\u865b\u64ec\u8a18\u61b6\u9ad4\u4e0d\u8db3\uff0c\u53ef\u80fd\u9020\u6210\u904a\u6232\u7121\u6cd5\u6b63\u5e38\u904b\u4f5c\uff0c\u8acb\u78ba\u4fdd\u7cfb\u7d71\u865b\u64ec\u8a18\u61b6\u9ad4\u5728700MB\u4ee5\u4e0a";
        if(warning!=accepted || title!=L"\u932f\u8aa4") { result["status"]="WARNING_NOT_WHITELISTED";return result; }
        HANDLE process=OpenProcess(SYNCHRONIZE|PROCESS_QUERY_LIMITED_INFORMATION,FALSE,pid);
        if (!process) { result["win32_error"]=GetLastError(); result["status"]="DIALOG_UI_ACCESS_DENIED"; return result; }
        wchar_t path[32768]{}; DWORD length=32768;
        const auto expected=L"C:\\Users\\risei\\Desktop\\God2\\God2-Server\\artifacts\\capture_work\\host-20260918-1430\\client\\God2.exe";
        bool identity=QueryFullProcessImageNameW(process,0,path,&length) && _wcsicmp(path,expected)==0;
        if (!identity) { CloseHandle(process);result["status"]="TARGET_IDENTITY_REFUSED";return result; }
        result["image"]=utf8(path);
        return control(process);
    }
    Json control(HANDLE process) {
        auto dialogHook=SetWinEventHook(EVENT_SYSTEM_DIALOGSTART,EVENT_SYSTEM_DIALOGSTART,nullptr,event,pid,tid,WINEVENT_OUTOFCONTEXT);
        auto showHook=SetWinEventHook(EVENT_OBJECT_SHOW,EVENT_OBJECT_SHOW,nullptr,event,pid,tid,WINEVENT_OUTOFCONTEXT);
        auto deadline=GetTickCount64()+12000;
        while (!found && GetTickCount64()<deadline && WaitForSingleObject(process,0)==WAIT_TIMEOUT) {
            MSG msg; while(PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)) { TranslateMessage(&msg);DispatchMessageW(&msg); }
            EnumWindows(window,reinterpret_cast<LPARAM>(this));
            if (!found) Sleep(25);
        }
        if (dialogHook) UnhookWinEvent(dialogHook);
        if (showHook) UnhookWinEvent(showHook);
        result["status"]="DIALOG_NOT_MATCHED";
        if(found) {
            result["matched"]=true;
            HWND button=nullptr; DWORD buttonPid=0;
            auto ready=GetTickCount64()+1000;
            do {
                button=GetDlgItem(found,IDOK);
                if(!button && buttons==1 && soleOk) button=soleOk;
                if(button && IsWindowEnabled(button)) break;
                Sleep(25);
            } while(GetTickCount64()<ready);
            GetWindowThreadProcessId(button,&buttonPid);
            result["button_pid"]=buttonPid;
            result["button_found"]=button!=nullptr;
            result["button_enabled"]=IsWindowEnabled(button)!=0;
            if (button && buttonPid==pid && classIs(button,L"Button") && IsWindowEnabled(button)) {
                result["button_hwnd"]=reinterpret_cast<uintptr_t>(button);
                result["button_id"]=GetDlgCtrlID(button);
                DWORD_PTR reply=0;SetLastError(0);
                auto sent=SendMessageTimeoutW(button,BM_CLICK,0,0,SMTO_ABORTIFHUNG|SMTO_BLOCK,1000,&reply);
                auto error=sent?0:GetLastError();
                result["ok_sent"]=sent!=0;result["win32_error"]=error;
                result["action"]="BM_CLICK";result["action_tick_ms"]=GetTickCount64();
                // A timeout is ambiguous: never duplicate an already delivered click.
                auto until=GetTickCount64()+3000;
                while(IsWindow(found) && GetTickCount64()<until) Sleep(25);
                result["closed"]=!IsWindow(found);
                result["status"]=error==ERROR_ACCESS_DENIED?"DIALOG_UI_ACCESS_DENIED":
                    !IsWindow(found)?"MEMORY_WARNING_CLOSED":"MEMORY_WARNING_ACK_FAILED";
            } else result["status"]="IDOK_VALIDATION_FAILED";
        }
        result["finished_tick_ms"]=GetTickCount64();CloseHandle(process);return result;
    }
};

int nativeDialogMain(int argc,wchar_t** argv) {
    if(argc==2 && std::wstring(argv[1])==L"--dialog-fixture")
        return MessageBoxW(nullptr,L"virtual memory should be at least 700 MB",L"GOD2 Test",MB_OK|MB_ICONWARNING)==IDOK?0:1;
    if(argc==2 && std::wstring(argv[1])==L"--dialog-selftest") {
        wchar_t path[32768]{};GetModuleFileNameW(nullptr,path,32768);
        std::wstring command=L"\""+std::wstring(path)+L"\" --dialog-fixture";
        STARTUPINFOW si{};si.cb=sizeof(si);PROCESS_INFORMATION pi{};
        if(!CreateProcessW(path,command.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW,nullptr,nullptr,&si,&pi))return 2;
        NativeDialogController c;c.pid=pi.dwProcessId;c.tid=pi.dwThreadId;
        c.title=L"GOD2 Test";c.warning=L"virtual memory should be at least 700 MB";
        c.result={{"test",true},{"pid",c.pid},{"tid",c.tid}};
        auto ready=GetTickCount64()+3000;
        while(!c.found && GetTickCount64()<ready) { EnumWindows(NativeDialogController::window,reinterpret_cast<LPARAM>(&c));Sleep(25); }
        bool fixtureSeen=c.found!=nullptr;c.found=nullptr;
        c.title=L"NOT GOD2 Test";EnumWindows(NativeDialogController::window,reinterpret_cast<LPARAM>(&c));
        bool wrongTitleRejected=!c.found;c.found=nullptr;c.title=L"GOD2 Test";
        c.warning=L"unrelated warning";EnumWindows(NativeDialogController::window,reinterpret_cast<LPARAM>(&c));
        bool wrongTextRejected=!c.found;c.found=nullptr;c.warning=L"virtual memory should be at least 700 MB";
        c.pid=0;EnumWindows(NativeDialogController::window,reinterpret_cast<LPARAM>(&c));
        bool wrongPidRejected=!c.found;c.found=nullptr;c.pid=pi.dwProcessId;
        c.result["negative_matches_passed"]=fixtureSeen&&wrongTitleRejected&&wrongTextRejected&&wrongPidRejected;
        auto r=c.control(pi.hProcess);CloseHandle(pi.hThread);
        HANDLE child=OpenProcess(SYNCHRONIZE|PROCESS_TERMINATE,FALSE,pi.dwProcessId);
        if(child) { if(WaitForSingleObject(child,3000)==WAIT_TIMEOUT)TerminateProcess(child,2);CloseHandle(child); }
        std::cout<<r.dump()<<'\n';return r.value("negative_matches_passed",false)&&r.value("closed",false)&&r.value("ok_sent",false)?0:1;
    }
    if(argc==4 && std::wstring(argv[1])==L"--native-dialog") {
        Json request;std::ifstream in{std::filesystem::path(argv[2])};in>>request;
        NativeDialogController c;c.pid=request.at("pid");c.tid=request.at("tid");
        c.title=wide(request.at("title"));c.warning=wide(request.at("text"));
        auto result=c.run();std::ofstream out{std::filesystem::path(argv[3])};out<<result.dump(2);out.close();
        return result.value("closed",false)?0:1;
    }
    return -1;
}
