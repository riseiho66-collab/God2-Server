# 瞬影三煞斬正式部署紀錄 — 2026-09-30

使用者確認「目前都正常」，隨後授權「可以更新到正式服務端上了」。
此次已完成正式服務端、正式客戶端與技能登記更新。此紀錄優先於早期候選／隔離狀態。

- 正式服務端：`build-town-visibility/Release/god2-server.exe`，重新啟動後 PID 9232，監聽 2592。
- 服務端 SHA256：`df897ef1798a3080969525599c6ed5138850f6f3990c7cf74bb1b98638c47564`。
- 正式客戶端：`../God2/God2.exe`，SHA256 `c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`。
- 分身 DLL：`../God2/God2ShunyingClone.dll`，SHA256 `8d1ec1c4d31af24fe3ff99f8bc452c714f73b327933049d677d891ea61d4a823`。
- 技能 kind0/id126 登記為 active；122～125 保持 reserved，448 筆原生技能不變。
- 客戶端共九項檔案逐一核對雜湊；沿用使用者接受的分身、完整原生刀3、名稱及背景恢復修正。
- 正式帳號、角色、持有技能、裝備和快捷鍵均未授予或重設；測試資料未搬入。

## 驗證

正式路線的 shunying_sanshazhan、owned_companions、recovered_deity、
recovered_battle_service 四項測試通過，凍結聊天檢查通過。
客戶端封裝五項檢查通過；正式安裝後執行現有 God2LauncherSupport.exe
`/verify-client` 回傳 0。部署工具重新核對服務程序、設定、全部九項客戶端
檔案、資料庫完整性及既有資料表，結果記錄於
`artifacts/releases/shunying-production-20260930/verification.json`。

目前原有正式遭遇仍為單怪，沒有新增取得技能的任務／商店或全員技能授予。
正式施放要求目前選中的自有神仙已持有該技能。核心的雙方 1／2／3 目標、
物理 300% 係數、一次 20MP、非法目標交易回滾與封包收尾已有程式測試；
不將此冒稱為部署後正式服的多人／三目標實機驗收。詳見
`shunying-formal-route-20260930.md`。技能外觀與名稱／背景修正已有使用者實機接受。

此編譯版本附帶 schema40 的空 character_teleport_gem_metadata 表；
其功能開關維持關閉，正式設定未改動。部署核對只允許此明確限定的空表、
該筆追加 migration，以及技能126的登記狀態變更，其餘既有表均相同。

## 備份與部署事件

`artifacts/releases/shunying-production-20260930` 保存 accounts.before.db、
god2-server.before.exe、server-config.before.json、client-before 與完整候選清單。
第一輪因停止程序後執行檔仍被鎖定而回復；已確認舊服務端與資料庫回復成功。
部署工具加入限定程序身分、等待程序結束及檔案獨占開啟確認，第二輪成功。
server-release.json 狀態為 INSTALLED；不變更舊備份。

客戶端引導程式目前綁定這台電腦的正式 DLL 絕對路徑；若要交給其他安裝目錄，
須重新封裝路徑，不能將這份本機 EXE 宣稱為通用可攜套件。
