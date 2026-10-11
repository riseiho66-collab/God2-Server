# CN 實際群組設定來源（2026-10-08）

本輪 `20261008-cn-client-group-configuration-source`，仍為第一階段靜態恢復與來源串接。前輪已保存實際監聽器／選服目錄來源、catalog117 及 66 檔封存，屬於具體進度。修改前保留 28 個來源／帳本／凍結 context；不覆寫前輪或原生基準。

## 原生檔案選擇

原生唯一 EXE 為釘定 CN God2_opt.exe，SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。0047C990 接收 initial-host 字串，先比前八個 bytes 是否為 `192.168.`，再依 008AEEC0 的實際字串比較決定設定路徑。008AEEC0 的當前執行值與完整上游仍未取得，不把 PE 字面值當成當前程序值。

|原生選擇|設定檔|
|---|---|
|initial-host 前綴符合，008AEEC0 等於 007F1500 字串|Data3/config2_2.ini|
|initial-host 前綴符合，該字串不等|Data3/config2.ini|
|initial-host 前綴不符合，008AEEC0 等於 007F1554 字串|Data3/config_2.ini|
|initial-host 前綴不符合，該字串不等|Data3/config.ini|

本 build 的 00405A30 是完整三個 bytes `xor eax,eax; ret`，所以此 caller 的兩個 `_gb.ini` 分支無法由該 helper 選中；這不是所有其他 build／caller 都無 GB 分支的宣稱。不得以繁簡顯示偏好或 Windows 語系改選設定或協定。0053FF40 解析相對於實際工作目錄的原生路徑；服務端來源要求明確的對應 client_root，不讀服務端自己的隨意工作目錄。

0047CBC0 呼叫 0045B270；後者先將 `Z` 附加到請求檔名，以 `rb` 打開，檢查 05／16。符合時經 0045A060 靜態已知 LZSS，再以 text mode 讀解碼暫存；不符合／不存在才回到 plain。同名 `.ini` 的位址皆為回環，但四個有效 `.iniZ` 都存在；因此本輪不能使用 plain 的回環內容冒稱原生實際選定資料或官方拓撲。

四份 `.iniZ` 的原始／解碼雜湊、同名 plain 八份精確輸入、檔案位置及差異各自保留在新 artifact。未修改客戶端或任一設定檔，也沒有連線至其中的任何地址。這些是目前安裝資源的資料，不能僅憑存在就認定為未改動的官方原始配置。

## EOF 差異的實際恢復

先前嚴格 TW 靜態 `decode_csvz` 在本輪實際 CN 設定上拒絕「最後一個 back-reference 缺 byte2」。此失敗不能被隱藏，亦沒有修改原工具或重新封存舊證據。原生 0045A060 明確將 EOF／缺 operand 導向已輸出檔案長度與 header 的比較：長度相同則成功。現有 CnResourceBytes.cpp 已保存相同 EOF 規則，無須改動。

本輪使用有 2KB 上限的 Python 檔案資料恢復，沿上述原生分支解碼真實四份設定；不執行原生函式、C++ resource reader、客戶端、codec、loader 或測試。每份輸出 452 bytes，EOF 位置／原始 hash／解碼 hash／文字 bytes 一起保存。函式 metadata envelope、指令與字面資料區亦另存；沒有把 metadata 範圍當成已封闭全部 CFG 或所有資源格式。

## 群組順序與槽位

0047CBC0 初始化 64 個群組指標；每個群組分配並清零 0x1804 bytes。名稱由 `[` 起複製，group+40 保存實际槽位數；最多 10 個 0x260 bytes 槽位。槽位左名稱在 +44，右側第一個 `%s` token 在 +84；它們是 narrow 原始文字，不自動轉為共用 ID、世界端點、權益或怪物欄位。

行首 spaces／tabs 略過，`;`／`#` 註解不增加槽位。組內空白行結束，下一個 `[` 保留為下一組；無 `=` 的普通行仍增加槽位、名稱／token 維持清零。到第十槽位後，原生外層繼續尋找下一組。不能把有位址的列數、05 node 個數或 04 enable bits 當成實際槽位數。

四份實際選定資源都是三個群組，槽位依次 **3／3／1**。前兩組同名仍占兩個不同 ordinal，禁止依群組字串去重。0047C970 讀 group+40；00443FA0／00443E80 以此值約束登入選服 UI。這補上先前只要求 caller 明確提供 configured slots 的來源缺口，沒有恢復 group billing、node load 或 06 raw 位置的業務含義。

## 已接入來源程式

新增 `CnClientGroupConfiguration`，由明確的兩個 selection operands、client_root 及資源預算讀取實際選定檔案，沿既有 `read_cn_preferred_resource`／`decode_cn_resource` 恢復。constructor 私有、factory 回傳 shared_ptr<const>，保留原始 selected path／encoded bytes／decoded bytes／群組／槽位及選擇輸入，沒有公開變更或任意建構 snapshot。Selection 無預設建構；已知的空字串可明確提供，embedded NUL 拒絕。

解析器只接入明確的安全形式：text-mode CRLF、127 bytes fgets 邊界、64 bytes 名稱／token、64 群組／10 槽位，保留原始順序與 bytes。過長 chunk、未終止 group、內嵌 NUL、text-mode EOF marker、lone CR 及會使原生倒退讀取越界的空左名稱不假裝恢復，不重現原生未定義寫入。這些未資格化形式仍留待後續，不代表對任何 INI 都完整相容。

`SharedAccountDirectorySource::from_source` 不再接 caller 所選槽位數，直接從該實際設定 snapshot 的 group ordinal 取得。既有 full catalog 則要求配置槽位精確相同，沒有改寫其原生資料。Plan 保留相同 immutable client config 與實際 listener snapshot；現有完整目錄發行／發布檢查沿用。`SharedLoginSources` 的實際 native composition 現在必需這份來源，缺少時不會以猜值或默認資料登入。

這是條件式正式來源程式中的實際檔案 producer，尚未執行。current runtime selection operands、對應客戶端部署／固定 profile 與正式 Application 配置仍未接入；不能聲稱所有 session 已選對變體或重新載入中的客戶端已與服務同步。單一 immutable profile 只適用明列的配置形式，混合或切換 profile 的原生規則仍需追查。

## 剩餘與計數

本輪新增實際 client config supplier 1、原生選擇形式 4、既有目錄 slots 來源串接 1；新 opcode／phase binding／完整 owner chain／完整雙向路徑都是 0，全遊戲分母與百分比維持 unknown/null。

native profile40／billing16／權益／revision／期限／完整07摘要，group billing／load／location，world bootstrap／equipment／scene／ACT、TW／PC／web／WSS、全部玩法與數值擴充仍未完成。未建置、測試、原生／C++ 執行、讀 DB、遷移或部署；原生客戶端、資源、存檔、帳號、認證、聊天、IME、字體、文字轉換、等級和共用資料表保持。
