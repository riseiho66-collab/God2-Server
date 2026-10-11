# 目前原生 C2S 6B 共用控制：欄位順序修正與各 lane 邊界

2026-10-06，嚴格限用已封存且verified=true的目前mapped image
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
(base 400000)；完整選取bytes、RVA、SHA與指令保存在
`artifacts/integration/packet-connections-20261006/companion-control6b-static-v2.json`。
本輪只做有界靜態反組譯與來源編輯，沒有測試、build、原生函式執行、
客戶端啟動、socket交握、SQLite寫入或正式服務部署。舊
`beast-panel-static-contract.json` 的V1錯誤排列表仍保留作歷史證據，
不偷偷替換；本V2只修正6B欄位順序。

## 原始發送與更正

兩個原生發送函式 `972F0..9731F` 與 `8FAF0..8FB25` 都呼叫
`4132E0(opcode 6B, payload pointer, length3)`。它們從**三個正式
參數反向**填入三個連續payload位元組：formal arg3、arg2、arg1。
所以實際 C2S logical4-byte佈局是：

| byte | 來源 | 已知用途 |
|---|---|---|
| 0 | 常數6B | C2S opcode |
| 1 | formal arg3 | 該caller的 inventory／拖曳格位 BYTE |
| 2 | formal arg2 | 該caller的選取selector BYTE |
| 3 | formal arg1 | 已見常數 lane 0、1、2、3、4 |

獸類面板`A0470..A04AD`控制11（ProgramMsg96食物）依序push
`slot, selector, 0`，因此是`6B | slot | selector | 00`。
先前V1文件／`RecoveredBeastPanel` codec把lane0放在byte1，與原始
producer的`[ESP+0C]`／`[ESP+0D]`／`[ESP+1A]`寫入順序不合；
本輪codec已改用共用`RecoveredCompanionControl6B`的原始bytes位置。

已定位literal lane呼叫：`A04A8` lane0、`A394A`及`84245` lane1、
`D71D1` lane2、`8421F`與`A5FD7` lane3、`843AC`與`8F870`
lane4。部分caller source欄位屬不同UI/owner物件；不能因同一
發送函式就把lane1..4解成獸類面板食物、同一pet generation或
相同消耗規則。其他未追caller及其lane仍保留為原始BYTE，不由
codec授權功能。

S2C opcode6B在目前長度表是**21 logical bytes**，world dispatcher
`6AABE..6AAD6`讀取自身body並呼叫`4CC910`。這個consumer和
C2S6B的4-byte producer不同方向／長度，不能只依同號自動當作
食物成功回覆。現有研究還未證明真正food/活動的S2C回覆及其
payload／狀態關聯。

## 來源接線狀態與仍缺

新純格式codec保留`inventory_slot,selector,lane`；
`RecoveredWorldRecords`有獨立`companion_controls6b` opt-in parser，
`Session`同名flag預設false，正式`Application`不設定、不處理。
獸類lane0 helper也只做格式解析。沒有任何食物效果或狀態變更，
因此**6B列入未接通的功能**，不增加已接來源分支41的計數。

接下來必須分別追各lane actor／owner／選取狀態、原生食物類別、
既有實例與背包的全欄readset、消耗及成長公式或明示CUSTOM規則、
原子存檔，以及真正的原生S2C回覆。PFD描述只說疲勞／忠誠／EXP
文字類別，不能直接填目前4C/4D面板欄位或扣物件。後續必須有
正式Application、C++/SQLite、Lua與原生consumer串接才能改列完成。

## V3：直接 caller census 與獨立 S2C6B 文字 consumer

後續在同一 verified mapped image 的 PE `.text` 節對兩個 C2S6B
發送函式 `972F0`、`8FAF0` 做相對 E8 直呼掃描，找出**10 個**
直呼位置。這是該節的直呼 census，未排除間接呼叫或其他模式；
原始 bytes、各切片雜湊及反組譯在
`artifacts/integration/packet-connections-20261006/companion-control6b-static-v3.json`。
V2 未列的 `97349` 與 `97370` 分別以 lane1／lane3 發送，兩者
formal selector 固定為 `0x2C`，slot 讀自 UI `+85602`。V2 所列
lane0..4及 `6B,slot,selector,lane` 順序不變。此 selector 仍不是
服務端物品／技能權限。

S2C6B 有 21 個 logical bytes：opcode、**原樣 LE32 pool identity**、
16-byte 文字區。世界 dispatcher `6AABE` 將 DWORD identity 與
`logical+5` 指標傳給 `4CC910`；其 `4CCF80` 在 256 筆、stride
`0x1D8` 的既有 pool 中比對完整 DWORD，找不到就不寫。
找到後傳 pool 記錄的 WORD `+0x7C` 和文字指標給 `509E70`，
更新次級 overhead 文字緩衝。`509E70` 使用無界 NUL 字串掃描，
所以服務端編碼器必須在16-byte欄位內提供終止零位，並把尾部清零。
新增 `RecoveredWorldPoolText6B` 只保留這個格式；沒有原生權威文字
資料、建立既有 pool 身分及發包時序，因此沒有啟用世界投影。

同一 `4CC910` 還由**另一條 S2CEC** 在 `6B4EF..6B508`
呼叫，把 owner 低 WORD 的高位 OR `0x8000`，處理隨行同伴名稱。
這可證明共用 renderer，**不能**把 S2C6B 當 C2S6B 食物回覆，
也不能把 S2CEC 的 owner|8000 規則套到 S2C6B 的原樣 DWORD。
本輪只做靜態反組譯和來源格式編輯；沒有 build、測試、客戶端執行、
正式資料庫寫入或部署。完整 C2S6B 遊戲效果及 S2C6B 發送路徑仍 OPEN。

## V4：lane0 目標位元組與背包格的條件關係

釘定同一 mapped image 的四段原生指令，原始 bytes、範圍 SHA256 和
反組譯見 `companion6b-panel-slot-link-v1.json`。`A0470..A04AD` 的餵食
控制11把拖曳背包格 `UI+855F0` 和目前面板位元組 `UI+85ABD` 分別送入
`6B | food_slot | selector | 00`。S2C `4C` 接收端 `A0840..A0879`
從快照 byte3 寫入 `85ABD`；S2C `4B` 接收端 `9FB40..9FBC9` 也從
其 byte1 參數寫入相同位置。S2C `41` 接收端 `992A9..992BD` 在背包格
變化時，比較其實體 slot 與 `85ABD`，相等才呼叫 `49FBD0` 關閉面板。

因此 `85ABD` 同時是 lane0 的選取目標與 41 的關閉比較值；後者**不能**
單獨證明所有持久神獸 selector 必定等於實體背包格。目前伺服器
`CUSTOM-0085` 的持有記錄把 `inventory_slot` 與 `panel.selector()` 分開
保存，`open_owned_panel` 會把後者透過 4B 傳給客戶端；移動持有物後兩者
可以不同。既有捨棄來源在送 41 清格前刻意以 4B 重設面板位元組為
實體格，屬明示 CUSTOM 配對，不能推廣為原始餵食服務端規則。

本輪沒有新增完整串接：要接餵食仍需伺服器以正式 owner/selection
readset 確認 selector、拖曳食物格及物品類別，取得消耗／效果規則和
真正的 S2C 回覆。PFD 的 65 筆描述不是可直接執行的效果公式。
未進行 build、測試、原生客戶端執行、正式資料寫入或部署。

## V5：PFD 原始宣告與 lane0 所需的持有讀集

本輪沿原生 `A0470..A04C8`、`499A60..499AD1` 做有界靜態追蹤；
完整原 bytes 與雜湊保存於 `beast-food-prequeue-gate-v1.json`。
控制11只檢查本地拖曳格非負、旗標 `0x20`，並把格位和目前
`85ABD` 送入 lane0。直接呼叫的 `499A60` 讀 UI 狀態並呼叫介面
訊息函式；此有界函式本身沒有驗明 PFD 食物類別或效果。不能
把本地 UI 門檻當成服務端的持有、物品或成長授權。

`NativePfdSourceCatalog` 由同一封存原始 `gamedata.csvZ` 的 PFD 區段
生成，保留 **65** 筆 key、原始列位置、資源鍵與逐列 SHA256；當前
同版資產的 PFD 列 bytes 也逐筆吻合。這只證明宣告來源。PFD 中
含特殊變身道具，例如 6970／6971；不能將 65 筆一概列為可餵食，
更不能從描述文字直接算出消耗、疲勞、忠誠或 EXP 變化。

`OwnedBeastFoodReadset` 現在可從完整 C2S frame 擷取唯一 lane0 請求，
並在同一 SQLite 讀取交易內擷取完整持有背包、神獸選取 revision、
panel selector、來源 PFD key 和目標神獸的持有格／revision，再做唯讀
交叉檢查。它**沒有**從網路啟用，
沒有寫資料庫、扣物品、更新 4C／4D 或送回覆。真正接線仍需在同一
交易中重新取得並 CAS 全部讀集、分辨普通食物與特殊物品、確認
Lua 效果／上限與原生 S2C 因果回覆；不能把候選讀集算作完整路徑。
本輪沒有 build、測試、原生客戶端執行、正式資料寫入或部署。

## V6：獨立 S2C 4D 消費器列入方向盤點

先前釘定的 `beast-panel-static-contract.json` 已含 `S2C 4D` 的原生
固定 9-byte 接收端：WORLD `69D64` 進入 `4A0970`。logical byte1
是**目標神獸的實體背包格**，不是 C2S 6B lane0 的食物格；byte2 與
byte4..8 更新選中面板的部分顯示欄位，byte3、byte4、byte7..8
則在原生 class5 條件下更新指定背包格的 metadata。來源
`RecoveredBeastPanel::Delta` 已保留原始欄位和兩種純投影操作。

本輪將 `4D` 從未分類 S2C 非預設分支移入**獨立格式已知**，不列為
已登錄服務端回覆。若將來用於餵食，正式 writer 必須同時確認
`4D.inventory_slot == selected.instance.inventory_slot`、食物格是另一個
持有物品格，且面板、背包、儲存三者在同一交易內一致。現有證據
仍未證明 `C2S 6B → S2C 4D` 的因果，不能自行發送 4D 當成功回覆。
本輪沒有新增完整路徑，亦沒有 build、測試、原生客戶端執行或部署。

## V7：第 44 格第一／第二代戰寵的 6B 分流

同一個 verified mapped image 的 `97320..97378`、`A2980..A29FB`、
`A5070..A50E5` 已釘定原始 bytes、SHA256 與指令。完整紀錄見
`companion6b-generation-dispatch-v1.json`，重現入口為
`tools/reconstruction/companion6b_generation_dispatch.py`（靜態讀取，不執行原生函式）。

`97324` 先讀 owner `+85A30` 的低 WORD；零值直接返回（`test` 後的
`jbe` 在此等於零值分支）。其後以固定
slot `2C` 呼叫 `A29A0`。此 gate 限 slot `2A..2C`、key
`3391..3778` 或 `5DC1..6D60`，並要求 metadata 查表非空；通過後
`97349` 排入 `6B | UI+85602 | 2C | 01`。若第一代 gate 失敗，才以相同
slot/key 呼叫 `A5090`；它限 key `6D61..7F58` 且 metadata 非空，通過後
`97370` 排入 `6B | UI+85602 | 2C | 03`。兩者皆失敗則不排隊。

這證明這個**特定 caller** 的 lane1／lane3 是依兩個戰寵世代的原生
metadata gate 有序分流，且 byte1 是 UI 已選物品格，byte2 固定 `2C`。
不等於全部 lane1／lane3 caller 相同，也沒有證明物品持有、可餵類別、
扣除、成長效果或回覆。服務端不可將 lane1／lane3 送入 lane0 神獸
餵食 readset。此次沒有新增完整路徑、測試、build、客戶端執行或部署。
