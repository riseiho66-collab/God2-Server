# 陸服原生技能 catalog 來源與選擇交接

本輪 `20261008-cn-native-skill-catalog-source`，僅靜態 PE／檔案恢復及來源串接。
上一個進度問答沒有新增實作；接續已封存的第 131 輪成果。

## 實際來源

固定 CN EXE SHA256：
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
原生 `00543560` 的 `005437EB` 傳入 `data2\fight\spg\cbspec2.bin`，
經 `0053FF40` 的實際路徑解析及 formatter，把檔名傳給 `00561BB0`。
`0053FF40` 快取目前工作目錄，再依輸入是否以反斜線開始選擇組合格式；
這不是 `.binZ` 解碼或資源 fallback 證據。

`0054358E` 保存 scene this；`00543669` 取 scene，`0054366F` 加 `149DF8`，
`00543676` 把此 component this 存入 `[EBP-330]`。
`00543807` 重新取出該 component 作 ECX，`00543817` 呼叫技能 loader。
因此 loader 的 `[this+888444]` 是 **scene+149DF8+888444 = scene+9D223C**，
接上前輪已恢復的 object+4504／role+4474 技能 bank，沒有另造指標或猜測 memcpy。

`00561BB0` 以原生 rb 模式開啟檔案，讀四位元組，與原生 `1.03` 比較；
相符後在 component+888444 讀取 `1B810` 位元組。
原生未檢查兩次 fread 的回傳值，也沒有 EOF／尾端長度檢查。
本輪自有 supplier 對固定版本要求完整大小及 SHA256，是來源限定政策，
不能宣稱原生 loader 有相同的完整檔案檢查。

實際 CN 檔案：`C:/Users/risei/Desktop/God2-xjz/XJZ-CN/Data2/Fight/Spg/cbspec2.bin`。
大小 **112,660 bytes**，SHA256：
`857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004`。
四組 DWORD count 在 `4+kind*6E04`，為 **125／130／87／111，共 453 筆**。
每筆 110 bytes，檔案 offset `8+kind*6E04+(ID-1)*6E`；
本次靜態檔案盤點的全部宣告記錄皆為 raw[0]=ID、raw[1]=kind。
這與 native A2 的 bank+kind*6E04-6A+ID*6E 算式一致。
未使用 count 外的填充槽，不把 453 當完整遊戲技能分母或玩家可學技能數。

TW catalog 的來源 SHA256 `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`
保留 TW 標籤；沒有把既有 TW dataset、MP threshold 或技能规则提升為 CN 證據。

## 實際來源程式增量

新增 `CnNativeSkillCatalog`，接收實際 plain-file bytes 與實際來源 revision／Current，
先擁有資料副本，再以既有 Windows bcrypt 連結計算 SHA256，限定固定 CN 檔案。
保存 raw 記錄、kind／ID、精確來源 offset、record hash 和來源身份。
查找前後觀察 Current；不讀 DB、不讀玩家記憶體、不解 native pointer。
Windows API 程式僅寫入來源，PHASE1 沒有執行。其他平台尚無 hash provider。

`SharedPrebornWindowSource` 現在要求此實際 CN supplier；在原有選擇流程中把
83 的每個原生 WORD 依 low-byte ID／high-byte kind 查成自有記錄副本，
保持原順序與重複項，交給同一個实际共同操作及 post-commit qualifier。
prepare／queue／selection 使用來源 Current；操作前重新檢查共同 window Current。
退休 issued scope 後只做既有單次共同操作；操作後保留同一份記錄交接，
不使用退休的 window Current 判定新 revision，也不把操作成功當已完成儲存。

這是既有條件式 owner 的實際資源交接增量；正式 Application 尚未配置。
真正共同 subject、技能 ID 映射、可選／已學資格、成本、Lua 規則、交易、存檔、
持久 replay 及實際 initial issuer 仍須接入。原生定義身份不等於伺服器權限。
可選 native Snapshot 仍只是恢復證據；不要求玩家程式位址或虛構 UI／pointer。

## 本輪界線與後續

新增實際 CN catalog supplier 1、既有 preborn 操作的記錄交接補強 1；
新 opcode、phase 關聯、partial owner 與完整雙向玩法均 0。
全遊戲路徑總數／完成量／百分比未知。
接續实际 common skill identity／共同 subject／规则與 save／replay／Application，
及 native84 caller／全 initial timing／其他玩法；台陸 PC／web、64 位數值、背包99
及整體測試修復發布目標保持完整。未建置、測試、原生／API 執行、DB 存取或部署。
