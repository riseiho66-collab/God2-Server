# CN 啟動參數至實際群組來源（2026-10-08）

本輪 `20261008-cn-native-launch-config-lineage-source`，第一階段靜態恢復／來源串接。前輪已有實際群組資源 producer、目錄配置串接、catalog118 與 118 檔封存，屬具體進度。修改前保存 28 個 context；前輪 3／3／1 槽位及各資源雜湊保留，不覆寫歷史紀錄。

## 008AEEC0 的實際寫入與來源

釘定 CN EXE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。00405A60 的傳入字串是 WinMain argument tail；它用 codepage operand **3** 經 MultiByteToWideChar，再 CommandLineToArgvW，取得第一個已解析 argument，經 WideCharToMultiByte（同樣 operand 3）轉回 narrow。這個 argv[0] 是此 argument tail 的第一個參數，不是完整 EXE 路徑。不得把 server 自己的 argv[0] 或未解析的完整 command line 當成這份輸入。

00404CE0 的實際 callee 是 `__stdio_common_vsnprintf_s`，由 00405A60 將 256-byte local buffer、`%s` 和完整第一參數交入。因此是**格式化複製完整字串**，不是 scanf 的「第一個非空白 token」；不自行割掉引號解析後 argument 內的空白，也不任意截斷。安全完整複製形式至多 255 bytes，加終止 NUL；更長的 CRT error／truncation 分支未資格化。

隨後 byte 迴圈把同一 local buffer（含終止 NUL）複製到 008AEEC0。這發生在 GetSystemDefaultLangID 及 client locale globals 寫入之前；配置 operand 不從 locale 產生。前輪 PE 的 address literals 是比較目標，不能當成當前執行值。此 round 恢復了 normal-startup 的 producer，但沒有執行／讀取某個當前 client process。

## 同一 local buffer 到 initial-host

00405A60 先傳 local buffer 到 00405150，該函式經 00404D50／005413A0 用字串 copy 與初始化處理；本輪保留 metadata 與明確函式來源，不宣稱所有呼叫／重入／callback 已封閉。

接著同一 local buffer 成為 00449F50 的 host 字串；其明確 byte copy 寫入 main+240。00449F50 建立 account controller（main+454）及 world controller（main+458），兩次 0047FA20 的最後參數均為 **main+240**，分別附不同日誌／buffer operands。0047FA20 先將這個字串交給 0047C990。這恢復了普通初始化中 initial-host 與 008AEEC0 的同源关系，不能讓配置 factory 任意為 normal startup 選兩個不相干的值。

0047CBC0 在 009EE1B8 已至少 1 時不重新載入群組。因此第二 controller 不是另一份獨立配置。004059E0 也會從自己的傳入值呼叫 00449F50，卻沒有在此函式寫 008AEEC0；其 caller／重入／cache reset 原生路徑尚未封閉。不能把 normal-startup 同源關係普遍套到這條入口。

在這個普通首次載入形式，initial-host 與 address operand 是同一字串。前綴符合 `192.168.` 時，不可能同時精確等於前輪 007F1500 的另一個比較字串，所以 config2_2 不由該同源形式選中；config2 為這個前綴形式。非該前綴时，config_2／config 仍由 007F1554 的精確比較決定。這是有限入口的可達性限制，未刪除前輪四個低階選擇形式或所有 `_2` 檔案，也沒有聲稱重新初始化一定可達第四形式。

## 來源程式的實際增量

`CnClientGroupConfiguration::read_from_startup_argument` 現在接收**已由原生 argument 解析／narrow 轉換後的完整第一參數 bytes**（不含 NUL）、明確 client_root 與兩個資源預算。它保留 bytes，不自行做 Windows quoting、ACP 選擇或繁簡轉換；拒絕內嵌 NUL 與超過 255 bytes 的未資格化形式。明確已知的空參數仍可提供，缺少 input owner 不以空值默認填入。

這個 factory 從同一 copied argument 派生兩個 Selection operands，再沿前輪實際選檔／native EOF／群組 ordinal／slot parser。沒有合成 IP、權益、billing、目錄負載或任何成功封包，也沒有把啟動字串混入帳密。

`SharedLoginSources::StartupClientGroups` 是明確選用的資料來源組合，要求 client_root、完整 first_native_argument、encoded／plain 預算；沒有預設建構。既有 `compose_native_login` 已接入這條來源，與既有完整 client_groups snapshot 嚴格互斥，兩者都缺少仍由原本 mandatory-source 條件拒絕。產生的同一不可變配置繼續到實際 bound directory、account issue／held publication。這不是只加一個未使用的 parser。

目前尚未在正式 Application 配置這個輸入 owner，也未證明所有 native client profile 的部署／實際 first argument／資源雜湊配對。這不是後續 reconnect、PC／web session 或任何 command-line 的自動識別能力；沒有開 socket／啟動服務。

## 計數與剩餘

新 normal-startup 同源投影 1、既有配置 producer 組合串接 1；普通首次載入配置形式為 3（前輪低階比較仍保留 4）。新 opcode／phase binding／完整 owner chain／完整雙向路徑 0；全遊戲總數／完成率 unknown/null。原始 code／metadata／字面值另外保存，不用文字 search hit 或 metadata 範圍冒稱 whole CFG。

下一步仍需 profile40／billing16／權益／期限／revision／完整07摘要、group billing／load／location、全部世界／裝備／場景／ACT 及玩法來源，TW／CN／PC／web／WSS 正式整合、64 位元數值／背包上限和全路徑分母。先集中完整來源串接，之後才建置／測試／修復／發布。未執行 Windows API／原生／client／C++ reader／codec／server／DB／遷移／部署；存檔、帳號、認證、聊天、IME、字體、文字轉換、頭像、等級、客戶端與共用資料表保持。
