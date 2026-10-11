# CN 原生 22 角色狀態與 07 等級來源

本輪為 PHASE1 靜態檔案恢復與來源串接；未建置、測試、執行 C++／原生／codec／Windows API／客戶端／服務，未開 DB、遷移或部署。前輪共用名字 → CN07 的 producer 與不可變證據保留。角色等級規則、位寬、經驗曲線與存檔不變。

## 真正可用的來源與診斷資料區別

現有 `SqliteRecoveredCharacterRepository::load_role` 只接受 `CUSTOM-0013` 的 diagnostic role snapshot；它具有完整 25-byte TW22、revision 與 design_id，但此格式相同不能讓值或成長規則成為 CN 原生權威。一般 Character 的 CUSTOM 預設等級也不是來源。本輪保留該 reader 與全部資料表，不把它們接進 CN producer。名字仍來自同一共用角色 repository；等級的新增來源則需要實際 native CN22 及其 revision，由同一 native metadata owner 明確綁定 common character ID。

## 實際世界與戰鬥接收鏈

世界接收函式 0048FCC0 的直接表 cell00492A60 對應 opcode22，實際 target00491295。00491295..004912A8 以 payload 起點 `EDI+1` 呼叫00519590；ECX 是 `main+89B26C` 的 UI owner。戰鬥接收005485F0 的 selector 表00548D98 在22處值為5；jump cell00548CB0 指向0054875F。該 branch 傳入 `ESI+1`，ECX 是 battle owner 的實際 member+20。兩者不能只因 opcode 相同就推成相同連線／階段 owner；這兩個 primary branch 明確共用同一角色更新函式。

保留世界 opcode cell、battle selector／jump cell、兩個實際 branch 到其終端 jump 的 bytes／assembly、battle entry 的 actual selector dispatch 前段，以及三個 metadata envelope：00519590（170B）、00519640（867B）、00443640（1040B）。005485F0 的 metadata Size 僅254B，包含不了選中的 branch，故另外按實際 primary table 取得 branch，沒有把 metadata extent 冒稱整個 CFG。原有兩個22 phase 項目與 length25證據保留，另保存實際 length table cell 與長度25的 return bytes，沒有新增 opcode 或階段。

## 已定位的 25-byte record

下表採 logical offsets，包含 opcode；00519590 的參數指向 payload，故其讀取偏移比 logical 小1。UI+430A8 是實際 retained role pointer。程式只讀原始數字，不推算成長、戰鬥或怪物能力公式。

|logical offset|原生操作|角色目的地|
|---|---|---|
|1 BYTE|原樣複製；00519700 zero-extend 後 `%d`|role+26 等級|
|3 WORD|16-bit 原樣複製|role+90|
|5／7／9／11 WORD|unsigned zero-extend 成 DWORD|role+78／7C／80／84|
|13 WORD|16-bit 原樣複製|role+58|
|17／21 DWORD|32-bit 原樣複製|role+60／68|
|2／15／16 BYTE|這個00519590沒有讀取|保留原始 bytes，不稱 padding／零|

新 `CnRoleStatus` 保留全部25 bytes，提供原始等級、WORD／DWORD getters 與未讀取 bytes。它不變更數值、不執行 UI、不把客戶端記憶體當作資料庫，不以相同 layout 證明來源或規則。它亦不擴充原生16／32-bit欄位；使用者要求的64-bit數值路徑仍為獨立完整工作。

## 255 的兩種面板行為

角色面板00519700使用 unsigned BYTE，可格式化255，這不等於官方最高等級。選角面板004438BE若看到 row level FF，就在004438C8把本地值改成1，然後再以 unsigned BYTE格式化。既有 CnCharacterSummary 已保留這個 local normalization，本輪重新保存 primary bytes作來源投影依據。

`CnRoleStatus::read` 仍保留任意原始 level BYTE，包括FF。`exact_selection_level_byte` 在FF時回傳缺失，因它不能在這個已定位的選角面板表達相同顯示等級。這不是把255改成1／254、修改進程等級、拒絕所有既有FF native07 或宣告新的遊戲上限。未選新的 role-level source 時，07原有字節仍原樣保留。level0的格式值也不自行認定為可遊玩等級；真正 native owner 必須決定狀態／規則是否有效。

## 接入現有摘要 producer

新增 move-only來源中的可選 `RoleLevel`：`from_native22` 要求完整 CN22、非零實際 revision，以及能精確投影的選角 level。Row 的現有兩參數 constructor 保留實際 native07 等級；新的明確三參數形式綁定 common ID、name mode 與此實際 role snapshot。沒有 level1 預設或 common40 offset猜測。

既有 `SharedCommonCharacterSummarySource` 在實際 common ID 對應後，只把選定來源的 BYTE level 寫到 active row 的 logical19／55。名字或 NativePromptMarker 分支照舊；包括提示名字的 row 也不因此略過明確的 level 來源。完整 native22與 revision 保留在 Row，原有 mandatory observing Current 可以檢查同一角色的實際來源、全部字節、revision、可見性與完整 outgoing07。該 owner 必須真正檢查新的依賴；非零 revision 或格式正確本身沒有權限。原本 roots／BeforePublish／QueueAccepted／NameSubmission 的檢查及 IO barrier 繼續。

flags、native slot、row18、職業、轉生、portrait、appearance、location、inactive row 和其他 native bytes保持來源值。沒有命名查表、全部角色可見、角色等級提升、共同 stats／HP／經驗結算或新成功回覆。正式 Application與 native07／22 metadata owner仍未配置。

本輪新增完整 CN22 reader **1**、既有07 producer 的明確原生等級來源投影 **1**；primary consumer evidence 附到原有 WORLD／BATTLE22兩個端點，未計為 gameplay source binding。新 opcode／phase binding／完整 owner chain／完整雙向路徑均為0；全遊戲總數、完成數與百分比仍null。

後續需要實際 native role state／revision／權益及 native07其餘資料 producer、profile40／billing16／期限與 group欄位、世界／戰鬥權威 handlers、交易／Lua／回覆、所有玩法與TW／CN／PC／web／WSS共同服務。存檔、認證、聊天、IME、頭像、字體、繁簡轉換、客戶端及全部凍結功能保持；完成全部來源串接後才集中全面測試、修復與發布。
