# 99/A9 原生傳送接線前置審查 — 2026-09-30

## 結論與範圍

本次只讀當前客戶端、當前資源、既有研究與凍結候選的程式碼，沒有修改 runtime、
protocol、CMake、測試、設定、客戶端或資料庫；沒有新增測試執行、原生函式注入、
遊戲程序或桌面操作。本檔是本次唯一新增檔案。未以退休語料作為來源。

`S2C6D → UI選擇 → C2S99/A9` 的資料結構、選項標籤和 state gate 可以與目前
`9be...` 客戶端對齊。現有 `RecoveredTeleport` codec 已表達這個契約。
**仍沒有可直接啟用的完整原生傳送目的地權威**：只找到五個標籤中的三個地圖名稱
關聯，沒有原生到達座標、開啟NPC/道具與context的可靠配對、收費及冷卻規則。

另外有兩個實裝限制必須先處理：

- 選項2「昆吾」對應 area5/scene27；它不是已接好的「崑崙仙界」area4/scene3。
- 最新 `RecoveredMovementService::begin_transfer` 仍要求來源與目的地使用同一
  area。現在的 area4 房間與 parent route 並不使五城跨區傳送可直接使用。

## 當前 build 與原生程式資格

| 輸入 | SHA256 |
| --- | --- |
| `../God2/God2.exe` | `9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336` |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| `../God2/Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| `../God2/Data2/Patch/Comm/gamedata-gb.csvZ` | `66c296fa27ebfbaa9434cb3e3707e23b79828b37ce7a0129d439b393ff00a7ff` |
| `../God2/Data2/Patch/Comm/message.csvZ` | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` |
| `../God2/Data2/Patch/Comm/message-gb.csvZ` | `1237a95833717de89306985d39458af1806849a627abc73e38ad7595810b4067` |

本次以 PE RVA 讀取下列11個完整entry..end連續範圍，逐byte與上述mapped image比較，
全部一致。這是靜態build相符檢查，不是新一次執行測試。

| 原生VA | bytes | 用途 |
| --- | ---: | --- |
| `004F6360` | 105 | 收取28-byte menu body |
| `004F6410` | 61 | 關閉視窗 |
| `004F6450` | 585 | 初始化與標籤資源ID |
| `004F6A00` | 52 | 取消時發出86 |
| `004F6A40` | 155 | 視窗事件/按鈕分派 |
| `004F6B30` | 548 | 開啟視窗與衝突條件 |
| `004F6DA0` | 75 | 特殊context判斷 |
| `004F6DF0` | 670 | header與列表刷新 |
| `004F7090` | 205 | 標籤、費用、row enable |
| `004F7160` | 322 | 選擇row、保存destination ID |
| `004F72B0` | 134 | 發出99或A9並清除menu body |

另確認 RVA `19A5F0` 的message-ID表，以及length table `1324+6D*4`、
world dispatch table `6B5D4+6D*4` 都與mapped image一致。

分析來源在 `C:/Users/risei/Desktop/God2-解殼EXE原始碼重建/decompiled/functions/`，
其中已命名的兩個檔案是
`004f6360_reconstructed_receive_teleport_menu.c` 和
`004f72b0_reconstructed_submit_teleport_destination.c`；反編譯文字是分析資料。

### 舊報告狀態修正

`docs/research/current-teleport-ui-20260926.md` 保留了「differential尚未完成」的
早期描述；重建目錄 `reconstructed/teleport-ui/native-verification.json` 實際記錄
9246 vectors PASS，完成時間 `2026-09-26T01:18:37.622174+00:00`，輸入是舊
`6bf75e...` 客戶端。其renderer呼叫被record/stub，沒有live client/server acceptance。
本次沒有重跑或改寫該結果。當前11個相關程式範圍一致，不能因此把整個新EXE或
真實傳送玩法標示成已驗收。

## 可接線的精確wire與state契約

S2C6D是29 logical bytes，opcode後的body有28bytes；`4F6360` 複製到
`UI+790EC`。下表offset以logical record起點為0：

| offset | 寬度 | 已知用途與界線 |
| --- | ---: | --- |
| 0 | 1 | `6D` |
| 1 | 2 | LE context，選擇時回送；不能自行解讀為NPC或item ID |
| 3 | 2 | SystemMessage ID；必須在當前資源可查得 |
| 5 | 1 | low7=count，high1=row enabled；server安全界線count≤5 |
| 6 | 1 | 顯示分鐘值，0..255；不是已知冷卻計算公式 |
| 7 | 1 | 顯示level，unsigned `<10`顯示免費，10起顯示數字價格 |
| 8 | 1 | 未解讀opaque |
| 9+4*i | 1 | destination/label ID：0空白、1..5有名稱 |
| 10+4*i | 1 | 未解讀opaque |
| 11+4*i | 2 | LE顯示費用，0..65535；顯示值不等於支付權威 |

原生迴圈没有count≤5防護；收到body只容納5個完整row，因此這個上限是server安全
資格。原生page renderer用`page*10`，選擇用`page*6`，所以不要開第二頁。

選擇producer `4F72B0` 發出固定5bytes：

`99/A9 | context_u16 | destination_id_u8 | opaque_stack_u8`

- `context=061E..0622`（十進位1566..1570）選A9；其他context選99。
- destination來自被點row的第一byte，**不是row位置或1-based點選序號**。
  `4F7160` 把它存入`UI+790E0`，producer只檢查該signed DWORD大於0。
- 最後byte由producer之前的`PUSH ECX`遺留，是owner地址最高byte，不能要求零，
  也不能作destination高byte或權限資料。
- server的可用選項應限1..5，而且必須屬於同一owned offer；只檢查1..5並不足夠。
- 成功queue後清空28-byte menu並關窗，不是客戶端已確認傳送成功。

### 原生UI gate

`UI+232E38` 必須有非負dialog index，其flag必須含10。
其他有效dialog的08 flag不得存在，檢查offset為
`232DDC,232DC8,232E26,232E16,232DAA,232DC0,232E28`。
只有成功open path才把selected DWORD清為-1。
body highbit未設時，`50CAA0`會停用row，`50D8A0`跳過它；但producer本身不重新
驗證這個flag，因此server不能信任UI gate。

callback control3送出選擇；0/4及cancel bit2走`4F6A00`，發出logical86+4byte。
低WORD取`**(UI+8688C)`，高WORD是UI指標殘值；它不是99/A9的context。
現有 `RecoveredQuestClose` 形狀已接受這5bytes，但新增teleport offer需自行辨識
當前session的取消生命週期，不能把cancel解釋成費用扣除或成功選擇。

## 來源映射：名稱、scene selector與缺失落點

原生 `4F6450` 由VA `0059A5F0` 讀ProgramMsg IDs `9,15,16,17,18,506`。
繁/簡體message兩檔有相同numeric IDs，逐行已查：

| destination ID | ProgramMsg / line | 名稱 | 當前gamedata map row | 可確認的scene metadata |
| --- | --- | --- | --- | --- |
| 0 | 9 / 2035 | 空 | 無 | 非可送出目的地 |
| 1 | 15 / 2041 | 葛城 | 21021 | area1, kind0, scene12, `cityS01`；selector `0301` |
| 2 | 16 / 2042 | 昆吾 | 21030 | 名稱為昆吾鎮/昆吾镇，area5, kind0, scene27, `cityS02`；selector `06C5` |
| 3 | 17 / 2043 | 韋城/韦城 | 無 | 兩份144-row map catalog沒有此名稱 |
| 4 | 18 / 2044 | 南巢 | 無 | 兩份144-row map catalog沒有此名稱 |
| 5 | 506 / 2532 | 楓華鎮/枫华镇 | 21082 | area2, kind0, scene4, `CityI1`；selector `0102` |

selector是既有native map packing `area | (scene<<6)` 對上述metadata的表示，
不是在傳送routine中找到的menuID→selector lookup。名稱關聯不等於路線權威。
這三個資源相對路徑分別為：

- `South001\cityS01\cityS01.mdt`，layer294×294。
- `South002\cityS02\cityS02.mdt`，layer252×252。
- `Island01\CityI1\cityi1.mdt`，layer189×189。

catalog欄6/7是atlas位置，不得當角色落點。例：昆吾695/185超出本地layer252寬；
楓華477/209超出本地layer189×189。**本次沒有挑選或推測任一arrival coordinate。**
當前崑崙仙界是獨立row21097：`CityI2, area4, kind0, scene3`，與label2不同。

### 可縮小下一輪搜尋的NPC/道具資料

- NPCAppearData沒有ID1566..1570；本次另查NPCList及NPCItemList，也沒有這組
  數字的可用配對。同號EQU資料是裝備，不能拿來綁context。
- NPCList是appearance resource preload表，不是placement表。model3025出現在
  row4182的area1/scene12、row4236的area2/scene4，以及多個其他場景，例如
  row4321的area5/scene0。這能縮小資源搜尋，不能產生NPC位置、方向、實例ID或
  確定opening context。area5/scene0也不是昆吾鎮scene27。
- NPCAppearData 2250/2251（rows1343/1344）是傳送法陣、appearance3025；
  2277/2287/2288（rows1369/1379/1380）為傳送仙童。仍缺世界instance/placement。
- SPI5571、5601、5605、5609對應單一城鎮的文字描述。既有09/27 producer研究
  已區分正常inventory use送25、shortcut部分送26；沒有25/26→6D的server因果證據。
- MIS02 16055、gamedata row13847 是高級傳送珠，原始描述「可選擇想要傳送的地點」
  及「使用10次後自動消失」，比單城寶珠更值得追opening request。但這仍是文字
  lead；未證明其context、destination集合、扣次欄或S2C6D回覆。

## 最新server接線點與authority限制

| 接線點 | 當前狀態 | 下一輪實裝責任 |
| --- | --- | --- |
| `RecoveredWorldRecords.h:222` | exact99/A9 grammar已存在 | 保留opaque tail與context discriminator |
| `RecoveredWorldService.cpp:60` | standalone/world-ready選擇呼叫teleport callback；缺callback即reject | 每個session必須綁previous offer，拒絕未offer、過期、其他owner、其他scene和重播 |
| `Application.cpp:710` | `RecoveredWorldService::Teleport{}`仍空 | 最终放owned offer/selection service，不直接把ID當map |
| `RecoveredMovementService.cpp:249` | `current_location`含ready/owner/saved-baseline/pending檢查 | 作為offer與commit的owned read-set |
| `RecoveredMovementService.cpp:306` | private begin_transfer處理61、position commit和pending | **目前強制same area**；不可直接硬塞area1/5目的地 |
| `RecoveredMovementService.cpp:351` | scene_kind只註冊area2、4及限定area13 | area1/12、area5/27的nav/kind/coldrestore尚未支援 |
| `RecoveredMovementService.cpp:377` | receipt後重置ring與pending | 新路線必須沿用owned baseline並完成scene/presence更新 |
| `SqliteRecoveredCharacterRepository.cpp:943` | commit_position是position交易 | 尚無fee/item/cooldown與position的同一原子交易 |

`begin_transfer` 的area目前同時作source和destination；line312–313檢查expected.area
及active.area都必須相等。新增跨區傳送必須明確拆開兩者，不能用忽略來源驗證的方式
通過。城鎮傳送也不能重用CUSTOM0053 parent route的點作自己的arrival。

收費、level eligibility與cooldown仍是缺失authority。native `<10`只是顯示免費分支，
特殊context的SystemMessage518只是提示；分鐘byte只是server供給的顯示值。
initializer裡的3個sample-like fees123/456/789不可提升為正式價格。

## 下輪有界工作建議

1. **可以直接做的native qualification：** 保留既有codec，補owned offer的presentation
   adapter與cancel/selection lifecycle驗證；一次≤5個唯一可選ID，保留每個完整menu
   raw/source evidence。這只資格化display/selection，不開啟travel或扣費。
2. **最有價值的opening trace：** 先追MIS02 16055的原生inventory/shortcut事件，或已有
   verified placement的傳送NPC；記錄實際request與同connection返回menu的關係。
   不從C2S6D同號、道具說明或NPCList preload推導offer。
3. **可安全接travel的必要條件：** 至少一個qualified opening route、owned context到
   destination mapping、真實arrival cell、nav/kind/coldrestore、source/target area、
   fee/item/cooldown authority及原子交易全部齊全。再接Application callback，通過61
   receipt和重登验收。當前這組資料仍未齊全。

若先做明確CUSTOM travel政策，須另記CUSTOM ID及來源缺口、具體政策與驗收；
不能把零費用、現成parent點、atlas座標或無作用callback稱為原生傳送已接好。
