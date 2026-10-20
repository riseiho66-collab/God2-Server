# 台服原生材料、換排／回合與返回續接：pass6

狀態：PHASE1／SOURCE_STATIC_ONLY。本輪沒有編譯、執行回歸測試、原版遊戲、
VM、codec、遊戲資料庫 SQL／schema 或部署。回歸案例是未執行的源碼；源碼審查
不是原服規則恢復、Windows 相容性或原版客戶端驗收。

## 本輪追到的原生證據

目標仍為台服 `God2.exe`，SHA-256
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
REA 的地址、原始證據、分析輸入來源、兩個 session 正常關閉與工具退出收據，見
[逐函數研究](tw-native-role-timeout-k-pulse-20261021.md)。沒有執行或改寫原版 EXE。

- `5129C0 → 518E50` 可在同次 logical flush 依序送出主角、戰寵 action2。
  每筆使用自己的角色位置與 one-hot self mask，opaque BYTE／DWORD 不能要求零。
  隨後的自動 0B 可保留戰寵 mask，actor 仍是主角 B51；不能把它當新輸出的 ACK。
- K 的來源已追到 `5109D0` 所建 manager 及 `52AEA0` 的模式脈衝寫入，包含
  reset、首次效果清除、無操作佇列閒置設置及主迴圈消費。這更新 pass5 的未知項；
  K 不是 entry context_b。原服如何產生 S88 counter 仍未知。
- 戰寵操作列 WORD map 為 `[1,2,3,6,9]`，action9 走同一原生 builder。
  此路徑不證明原服配對、死亡／空端點授權及先後順序政策。
- S1C／86／4 接收及顯示函數只能證明欄位用途，不能產生原服完整材料。
  局部怪物外觀 builder 不等於已證 WORLD 或 E3／FB 到戰鬥身份的完整轉換。

## 材料來源及安全投影

| 材料 | 本輪可直接使用的實際來源 | 仍缺少的部分 |
| --- | --- | --- |
| 主角等級、目前／最大 HP、MP | 真正 role／resources／canonical checkpoint 全值及 owner 核對 | 等級成長／原始能力公式 |
| 戰寵等級、目前／最大 HP、MP | 真正 active44 完整 Pet1 E3 或 Pet2 FB 保存實例 | 成長、其他能力、種族／名稱／狀態的 producer |
| 完整戰鬥身份／外觀 | 既有精確 native 原型；保留所有未知位元及來源 | 原服全套生成材料；不能由名稱或技能表合成 |
| 入場／返回世界材料 | 角色專屬完整 root40、2A、世界 spawn／remove／move | 尚未提供的角色／寵物完整版本，不能套第一筆 |
| 配對、回合、計時 counter | 已恢復客戶端 consumer／builder 契約 | 原服服務端配對與排程 producer |

`OwnedPveWorldCatalog` 對主角只替換已證等級及資源欄位；HP DWORD 溢位拒絕，
不截斷。戰寵省略政策仍沿用嚴格的完整來源比對；明選
`owned_saved_vitals_level_v1` 才排除已保存目前／最大 HP、MP 與等級並投影當前值。
Pet2 兩個 packed DWORD 的高7位仍精確保留；metadata、family/key/slot、來源及
其他 stats 都不放寬。嚴格／投影材料的比對域重疊會拒絕整份版本，與列順序無關。
完整英文欄位及單位見 [資料表中文說明](../database/tables/owned_pve_world_catalog.txt)。

這是 CUSTOM-0161 的明示保存值投影，減少正常保存值改變後重填相同原型的需求；
沒有假造原服 producer，沒有安裝或填入實際 DB，也沒有把 PK 的 CUSTOM 原型
重標為 native。完整資料缺少時仍精確拒絕，不補零或建立寵物。

## 雙角色逾時及回合邊界

`OwnedPveTimeoutPair` 先分類整個原始 batch，拒絕混合 mutation、重複角色、
超過兩筆 action2、錯誤角色次序／context／self mask。Host 再核對真正成員、
兩個存活 owner、同 grant epoch／assignment 及兩項可信 control policy。
這裡 action2 解作 pass 仍是 CUSTOM-0161，不宣稱恢復防禦公式。

Host 在第一筆保存前保留原始第二筆，防止第一個輸出重新開放已提交的戰寵控制。
第一筆經現有 canonical pass／保存／真 Written 與進度邊界後，才處理第二筆；
不合併成一次無邊界保存，不更新 RNG 或假造新回合。合併到達的 0B 只可能觀測
既有 edge，不能替剛建立的兩個 edge 作證，也不複製到第二筆繼續執行。
換排前的舊角色 pair 不重標為新位置；durable／recovery 失敗保留 claim 並拒絕重試。

原生 0B 沒有 nonce，socket Written 不是 renderer 完成。固定完整 profile counter、
明示配對、敵方次序及服務端 grant 政策仍屬 CUSTOM，不能標作原服完整還原。

## 返回後戰寵與技能的等價入口

原有返回 lineage、全員保存、逐人 C1C／Written／新 private INIT 及 active44
增量刷新維持 [返回續接來源](tw-pve-return-continuation-source-20261021.md) 的限制。
本輪再檢查真正宿主 wrapper、交易、回覆與失敗流程，而非只補直接 handler。
逐項接線與回歸來源的限制另見 [換寵／首次技能書續接](tw-return-pet-book-source-followup-20261021.md)。

合法 C28 的 42..44 戰寵來源由完整 batch 精確分類，直接接回真正 companion
handler；不借一般物品 0092 的 slot0..29 權限。混合移動／道具／其他 mutation
在任何保存前拒絕。交易完整核對實例、版本、分類、來源及未動到的其他 cell；
最後核對實際 INIT、phase、battle generation、movement owner／位置及現任來源。
保存前拒絕既有 PK／PvE claim、同連線跨 facade 重入及來源 TEMP shadow／trigger；
已覆蓋的晚期資料寫入由完整 readback／change counter／來源 fence 判定失效。
COMMIT 後失去來源明列 durable，不成功回覆，也不把舊操作當 rollback 重試。

同類的 C24 備用格 42／43 重排也走精確原始 batch 分類，與一般物品移動分開。
它和 C28 共用單一 `swap_pet_cells` 保存實作、同連線 guard、完整 cell CAS、
PK／PvE claim 及最終來源檢查；不留兩套可互相重入的交易保護。回覆在保存前
完整準備，空／同格維持不變，不建立寵物；出戰格44不冒充備用重排入口。
此獨立寵物操作不發假 joint-inventory edge，不退休無關的 deity／learning 圖。
owner、metadata、分類、實例讀取及寫入明確限定 main，TEMP 偽資料不作證據。
此保護不宣稱能抵抗任意受信 SQL callback 主動改寫 schema 的所有情況。

首次 C25／C26 可在返回後尚未有 learning Entry、也沒先送 idle Tick 時到達。
宿主先發送必要的真正 bootstrap；Session 的私有 friend 入口只保留同一個
原始 GAME work、records、ticket 與 input lease 一次，等該原回覆真正 Written
及 Released 後再接續。沒有複製請求、假造 Written、重設期限或新收包事件。
service release／stop、close、新 INIT／battle、失效 material 或二次 defer 都
不能恢復舊工作。空 bootstrap 只有在真正 current graph 下才同 callback 繼續。

分類物件沒有 equality operator 的欄位改為逐欄精確比對，保留 group、index、
source_line 與 name；不放寬任一來源值。

## 審查與驗證邊界

每項修改均附作者及獨立修改後源碼審查；相關 callback／交易／保存／回覆／失敗
流程一併核對。外部證據根為
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-material-rules-continuation-pass6`，
保留最終 SHA、審查收據及本輪唯一正式靜態封包報告。

新增案例源碼包括真 parser 的雙 action2／非零 0B、opaque 保留、混包拒絕、
兩次保存邊界；嚴格／投影材料交集及數值溢位；同原始 C25／C26 工作的兩階段
接續、release／重複 defer；C24／C28 換寵的晚期 observer、claim、交叉重入及保存守恆。
以上全部未執行。真正 Host／多人動畫、返回後實際學習與寵物 UI、Windows 及
原版客戶端聯合驗收仍待後續執行階段，不宣稱本輪達到完整可玩或100%。
