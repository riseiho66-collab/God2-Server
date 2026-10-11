# 全量實際記憶體：NPC／怪物顯示目錄

日期：2026-09-27。這次涵蓋 **全部 4,043 筆已載入來源 NPC，以及全部 7,815 筆 EnyName arena 記錄**，不是四個任務 NPC 的抽樣。本報告重新分析既有 ReadProcessMemory 擷取；未另開遊戲、未寫遊戲記憶體、未改 DB／客戶端。

## 擷取與重現

- 輸入：`artifacts/research/live-memory-references-20260927-02/memory-result.json`。
- 輸入 SHA256：`1f3de6e0f62c340b20447c3b868907103b01caa64074688ebf47e9b5c725930a`。
- 當前 EXE：`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`。
- gamedata.csvZ：`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`。
- 解碼來源：`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`。
- 擷取 accepted=true、登入次數 0、外部連線 0、記憶體寫入 0、截圖 0；原擷取已關閉 owned client，桌面未切換。

在 server 根目錄執行：

```powershell
python artifacts/research/all-live-memory-npcs-monsters-20260927/analyze.py
```

輸出同目錄 `summary.json`，包含全部 NPC 逐筆 prefix、拆解 component、來源行／hash、全部 EnyName 逐筆記錄、96 個實際 descriptor 與全部 24 筆 orphan。檢查使用明確例外，不依賴 Python assert。普通模式及 `-O` 均執行成功。

## 全量覆蓋

| 對象 | 此次實讀／重算 | 結果 |
|---|---:|---|
| NPC source records | 4,043 × 94 = 380,042 bytes | 4,043 筆 source-written name／flags／code／適用 components 全部一致 |
| NPC source prefix | 4,043 × 28 = 113,204 bytes | 501 筆 composite；其餘 3,542 筆非 composite |
| NPC tail | 4,043 × 66 = 266,838 bytes | 非零記錄 0、非零 byte 0，全部偏移皆為零 |
| EnyName arena | 7,815 × 26 = 203,190 bytes | 全部 source-written fields 一致 |
| EnyName composite | 3,109 | 全部 8 component bytes 與來源 token 打包結果一致 |
| EnyName ordinary | 4,706 | 8 component bytes 此次皆為零；不表示這些未寫欄位存在通用遊戲預設 |
| 最終 descriptor | 96 groups | 7,791 筆可達，無重疊／越界 |
| arena orphan | 24 | 來源早期 area7／scene13，arena index229..252，source line21957..21980 |

NPC highwater=6,224、constructor capacity=7,000、source count=4,043 是不同數字。有效來源含 4,041 筆九欄與兩筆五欄（1156、3472），沒有丟棄短記錄。其餘 2,957 個非來源 allocation slots 未包含在本次來源逐筆擷取內，不能宣稱全部 allocation bytes 已讀。所有來源 NPC 的 66-byte tail 為零，是**登入前這一次記憶體觀察**，不是原生 NPC 屬性全為零。

## NPC 94 bytes 的欄位來源

實際 owner `C=005E053C`；record=`C+121EA+selector*5E`，selector 直接索引。`4570F0` 的來源欄位（zero-based）：

| Record offset（hex） | 來源／用途 |
|---|---|
| 00..0F | column1 原始 CP950 名稱，最多15byte可見文字 |
| 10 WORD low14 | column3；`4C79C0` 用於 NpcHead portrait selector，不是戰鬥數值 |
| 10 WORD bit14 | column4&1；保留旗標來源，不擴充任務功能含義 |
| 10 WORD bit15 | code5001..5003 的 composite discriminator |
| 12 WORD | column2 appearance code；不是 instance identity，也不是座標 |
| 14／16／18／1A | body／face／head／weapon pair，columns7／6／5／8 |
| 1C..5D | 66byte 後段；此次全部零；已知 F8 可寫 server cache，不能當本地完整定義 |

component 兩 byte 保留為 base low4、category high4、ordinal low5、variant high3。對適用來源 token，獨立依 `4570F0` 的 byte masks 重算並逐筆相等；不將未由 loader 寫入的 component 零值升格為來源規則。完整 flags／appearance-code／portrait-selector histogram 存於 JSON。

已知 F8 `46AADE→45BA30` 寫 tail：record1C←body0、1D←body4、1E←body78 WORD、20←body34 的16bytes、30←body4D NUL字串、55／59←body45／49 DWORD。`4CDC70` 把 record20 的16bytes當字串，**不是物攻／魔攻／物防／魔防**。詳見 [欄位 writer 證據](current-memory-catalog-layout-20260927.md)。

## EnyName 26 bytes 與全部群組

實讀 arena=`05ABE6B8`。根 `C+D2D9C+area*8` 存 countDWORD／descriptor-pointerDWORD；descriptor 12bytes 存 scene／count／record-pointer。逐個實際 pointer 換算 arena index，獨立得到 7,791 可達記錄，與來源 replacement 結果一致。97 次來源 group occurrence 最後剩96 descriptor。

| Area namespace | arena records | lookup-visible | groups | orphan |
|---:|---:|---:|---:|---:|
| 0 | 6166 | 6166 | 4 | 0 |
| 1 | 30 | 30 | 2 | 0 |
| 2 | 46 | 46 | 5 | 0 |
| 3 | 38 | 38 | 5 | 0 |
| 4 | 35 | 35 | 5 | 0 |
| 5 | 22 | 22 | 3 | 0 |
| 6 | 58 | 58 | 3 | 0 |
| 7 | 182 | 158 | 7 | 24 |
| 8 | 223 | 223 | 13 | 0 |
| 9／10 | 0 | 0 | 0 | 0 |
| 11 | 54 | 54 | 6 | 0 |
| 12 | 706 | 706 | 24 | 0 |
| 13 | 54 | 54 | 4 | 0 |
| 14 | 65 | 65 | 4 | 0 |
| 15 | 63 | 63 | 8 | 0 |
| 16 | 73 | 73 | 3 | 0 |

**Area0 的6,166筆包含 companion/following display namespaces，不能稱為6,166種野怪。** group area／scene 是顯示查找 namespace，不能直接當實際玩家所在場景或完整出生設定。

`45A1A0` 寫 byte0：來源col2 high4、col3 bit0、col5 bits1..3；byte1只存col4 code低8bit。name在 **+2**，不是+0。components位於+12/+14/+16/+18hex，順序 body／face／head／weapon。3,109筆 composite source codes5001..5003被截成低8bit，同時保留適用component8bytes；JSON同時保存完整source code和memory low8，不反推被截斷的原值。

所有24 orphan仍有實際 arena bytes，並且逐筆來源一致；它們沒有當前 descriptor 指向，不得拿來新增可達lookup或spawn。

## 下一次記憶體讀取：場景物件池與來源

本次擷取在登入前，**沒有已登入場景的所有 live object pool 記錄**。下一個確切 root 是當前世界物件 W，不能把 C 靜態 catalog 當 W。

已登入 UI 指標 U 可由既有已資格 harness 取得：`P=DWORD(U+86888)`、`R=P-90`、`W=R-1539683C`。先驗證目前 kind=`DWORD(R+10)`、scene=`DWORD(R+14)`、area=`WORD(R+18)`，且 catalog `DWORD(W+AA36480)`／`DWORD(U+CFF70)`相等、對應當次來源名字。以下數字全為 hex：

| Root／讀取 | 有界大小／欄位 | 已查來源 |
|---|---|---|
| NPC pool `N=W+1539AED8` | records=`N+70`，256×1D8（120,832 bytes） | 72普通`46AA89→4CC380`／composite`4CBD70`；另本地 marker `467CD0` 必須分開 |
| monster/follower pool `M=W+153B8758` | records=`M+70`，256×1D8 | 71→`4CB120/4CB720`，及 owner-relative follower `46C6A0`，不可全當野怪 |
| 每個 occupied record | +0 DWORD identity（FFFFFFFF空）；+8 WORD facing；+10/+14 DWORD tileXY；+18/+1C float screenXY | received appearance／movement 或既有 owner-relative follower位置 |
| 移動快照 | +180/+184/+188/+18C DWORD；+34起40-entry path queue | NPC60→4CCA50；monster5F→4CCB10；共享4CD8D0／frameupdate |
| 同時保留場景 | W+1539684C kindDWORD、+15396850 sceneDWORD、+15396854 areaWORD | 此 pool record 本身沒有已證 area／scene 字段 |

應完整讀每個pool的256records，再以identity occupancy篩選，保留原始 bytes／當次map root／capture時點；不要僅搜尋名字。名稱字串或模型 handle 不能證明 instance、template join、坐標來源、掉落、屬性或生成條件。若pool空，只能報當次實讀空，不能推論所有場景沒有NPC／怪物。

71 namespace 的確切來源是 `L[5]&3F`、`LE16(L+5)>>6`、`LE16(L+19)>>3`；instance=`LE32(L+1)&FFFF`，兩者不可互換。72 ordinary 資源另取 `L[5]` idx 與 `L[6]&1F` type（`46A9DA..46AA8E`），不會自動把NPC來源code填入缺失封包欄位。此為來源識別界線，不是建議生成封包／新擺NPC。

詳見 [NPC writer census](current-npc-position-writers-20260927.md)、[monster writer census](current-monster-position-writers-20260927.md)。本次 heap pointer候選13 NPC／97enemy／0quest中，沒有一筆可據本JSON直接升格為spawn；enemy候選97筆的原擷取authority仍全是未資格aligned pointer。完整descriptor讀取的96groups是另外的已資格鏈。

## 結論界線

已取得並核對的是**全部已載入來源顯示目錄**，不是全部原服出生實例。新結果沒有提供level、HP/MP、雙攻雙防、掉落率、出生XY、遭遇率、任務條件或獎勵；這些字段仍須對應其真正記憶體owner與native writer。此次沒有建立任何新spawn或推定任務。

## C++ 全目錄完整性 gate

`NativeEnemyDisplayCatalog::counts()` 回傳 `Counts{records,lookup_visible,groups}`。只有 source 與專用目錄表都空時回傳零；有資料時必須完整為 `{7815,7791,96}`，並通過全欄位 SHA256。專用表中改名 dataset、不完整來源、缺24 orphan其中一筆，均拒絕，不能降級成空目錄。這個 API 用於啟動讀取 qualification，不建議每個 frame重算。

Fingerprint 由 `import_native_enemy_display.SOURCE_ROW` 接完整 `pinned_rows()` 的7,815筆13欄建立；每個值採 LE32 byte length + bytes，integer用ASCII decimal，text UTF-8，BLOB原bytes。总長1,679,430bytes，SHA256=`677c274ea71e917914455f5939564fe9080ea584dd3cabbb7d653648a6316e94`。因此 source pins、行號、offset、flags／visibility、原始row及其hash、name、namespace與所有orphan均受同一不可變pin保護；單改raw加上重算該row hash仍會拒絕。

Standalone `tests/test_native_enemy_display_catalog_integrity.cpp` 由以下命令在私有目錄以 MSVC C++20 `/W4 /WX` 編譯，未重編 shared core：

```powershell
python tools/strike_lab/current_enemy_catalog_integrity_20260927.py
```

結果28commands PASS（編譯、empty、完整原來源及25種破壞案例），約6秒。完整／空目錄同時驗外層已有read transaction時不擅自commit；破壞情境驗無read transaction洩漏。所有DB都是臨時獨立fixture，未修改正式來源表或玩家資料。證據：`artifacts/research/enemy-catalog-integrity-20260927/evidence.json`。既有 `lookup()` API 的單筆讀取行為未更動；runtime啟動接線由主線負責，單獨引入此類別不表示startup已啟用本gate。
