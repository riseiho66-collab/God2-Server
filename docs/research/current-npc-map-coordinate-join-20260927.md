# 當前 NPC／地圖座標 join：2026-09-27

## 本輪新增結論

仍是 **0 筆可授權生成的完整 area/scene/world-NPC/x/y/direction 記錄**。
這次有三項新的具體證據，不是重做名字搜尋：

1. 完整執行 `004C3EA0 → 00459D80`，證明 Map_City_Coordniate packed XY
   在這條路徑寫入地圖 UI 投影基準，而且會依 metadata 分支改取面板尺寸。
   不能因 packed 位元配置與72相同，就把它當 NPC 出生座標。
2. 將唯一 `npcad.ROM` 引用連到 **佈告欄** TileModel、ModelDat 和三筆
   實際 placement；完整執行其 geometry setter。它們是地圖模型位置，
   沒有 world-NPC 身份、面向或互動任務 join。
3. 精確定位另一種 mapmarker 為 role 名單的 actor WORD／網路座標消費路徑；
   另留下 CityI2 原生 `0044C980` 零寬 Pass grid 的具體 loader 邊界，
   不把既有 Python parser 拒絕當成原始檔損壞或自行補值。

已先讀全 NPC 審計、map-section omission、town-guide 與崑崙44–50報告。
未使用退役來源，未啟動遊戲、操作桌面、截圖或修改共用程式／正式資料。
MBD cell 語義由另一條研究線處理，本輪沒有重做。

## 工具、來源與驗證

```powershell
$env:PYTHONPATH='artifacts/tooling/crypto-oracle-python'
python -m tools.strike_lab.current_npc_map_coordinate_join_20260927 --output artifacts/research/npc-map-coordinate-join-20260927/evidence.json
python -O -m tools.strike_lab.current_npc_map_coordinate_join_20260927 --output artifacts/research/npc-map-coordinate-join-20260927/optimized.json
```

兩次 PASS：145 map lookups（144原始鍵＋1不存在鍵）、10次完整 UI anchor
函式返回、3次原始 model setter 返回；6 tiles／6 models／3 placements。
工具採 explicit checks、指令预算、正常 EIP／ESP 返回與寫入位置檢查；
結果只在完成後原子替換。沒有代替原生 game callee 的 stub。

| 來源 | SHA256 |
|---|---|
|現用 God2.exe|`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`|
|gamedata.csvZ|`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`|
|decoded gamedata|`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`|
|CityI1/cityI1.mdlZ|`bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618`|
|decoded CityI1 MDL|`59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef`|
|island03/cityi2/cityi2.mdlZ|`cb36dbf46adc611620e1bd7c9b0093955c846f33a849ebf88f6ce57f426813cc`|
|decoded CityI2 MDL|`bed2f89dcdb30ed6d7b30c5625423f8bd007ca30eea32ec5406a7ebb7932dd5f`|

JSON另外保留當前 PE code spans/hash、原始 map rows/line/hash、MDL placement
原文 bytes/line/hash，以及重建反編譯精確 caller 檔名與行號。下文地址皆為
VA；減00400000才是 RVA。

## Map_City_Coordniate：真實 reader 的用途

既有 `00459A80` loader 將每筆存成1A4 bytes：+F0是area低6位／scene，
+F4是kind低2位／x15位／y15位；+F8/+FA是來源欄11/12，+1A0指向額外
地圖資源 metadata。完整原生 CSV loader 已由 owner-map-metadata 研究
驗證，本輪不重複載入器；VM中的測試 records 是依這個 schema 從釘定來源
投影，metadata分支鍵是明確合成操作數。

`004C3EA0(area,scene)` 完整呼叫 `00459D80(area,0)` 和
`00459D80(area,scene)`：

- 若兩筆 metadata 都存在且 WORD(metadata+24)不同，將當前scene的
  signed WORD +F8/+FA寫入 UI+8AA30/+8AA34。
- 其他已測分支（metadata缺失、相同鍵、scene不存在），則把area/0的
  packed XY寫入同一對欄位。area/0缺失會走assert，未假造正常結果。

| 來源列／area/scene | packed XY | +F8/+FA | 同鍵／空metadata結果 | 不同鍵結果 |
|---|---:|---:|---:|---:|
|21078，2/0|735,777|735,777|area基準|—|
|21082，2/4 CityI1|477,209|189,189|735,777|189,189|
|21091，4/0|420,1092|420,1092|area基準|—|
|21097，4/3 CityI2|318,363|252,252|420,1092|252,252|

每次完整返回的 **非stack寫入恰好只有 UI+8AA30與+8AA34兩個DWORD**；
沒有 NPC pool 或封包佇列寫入。本測試沒有把所有metadata都設為真實運行
值，故證明的是原生分支與來源選擇，不是某次實機必走哪個分支。

相鄰消費鏈的靜態原生證據：

- `00465E00` 查當前area/scene，從來源+F4或world+224/+228取得位置，
  再呼叫`004C3E30`。
- `004C3E30`將輸入和UI+8AA30/+8AA34、比例+8AA44交給`004C2510`，
  最後`00507570`移動UI+232DA8所指widget的control0，並扣除+8AA38/+8AA3C。
- `004C3F60`綁地圖metadata、圖像、比例與偏移；`004C3C20`依actor位置
  重算視窗。這些完整renderer路徑本輪未執行，沒有宣稱實機圖像驗收。

因此CityI2來源318/363既不是已恢復NPC位置，也不宜用來補出生點。

## npcAD 的可重現原始模型鏈

CityI1的ROMFILE索引15是`npcad.ROM`。它被TileModel161..166引用，CP950
原始名稱`a747a769c4e6`確為「佈告欄」，完整名稱為佈告欄01#a..f。
每筆type23（0x17，low nibble7），ROM action1001..1006。
原生`0044C420`的type7分支進普通圖塊／模型资源流程；這不是NPCAppearData
模板ID。

ModelDat161..166的首層分別引用同號tile，其餘兩層為-1，八個extra整數
全為-1。只有以下三筆實際placement引用其中的模型：

| placement index | model／action | block | 原始幾何第一對 | 原始grid對 | 附加資產 |
|---|---|---|---:|---:|---|
|134|163／1003|4,3|680,420|92,72|無|
|135|161／1001|4,3|720,400|93,72|無|
|138|162／1002|4,3|880,440|94,75|無|

原始完整欄依序為
`[model,a,b,c,d,0,-1,-1,0,0]`，保留在JSON；沒有把其中任一0改名為NPC
方向。MDL同時保存圖塊Pass資料，原始位置的圖塊／投影單位也不自動等於
可互動NPC spawn座標。

精確原生路徑：`0043D420 → 0044D750`讀ROM／TileModel／ModelDat；
placement則`0043EE20 → 0044C6F0`按model index取模型，再
`00438920 → 00441FC0`建立幾何實例。原始`00441FC0`完整執行三組來源值，
只寫object+C/+10/+14/+18和model pointer+2C，與測試預期逐欄一致。
此处model pointer是標記為合成的sentinel；沒有偽造已完成ROM載入。

原始`0043EE20`另依MDL版本處理block×21與attachment。本輪保留v1.6原值，
未重做完整流／配置器／渲染，更沒有把setter返回稱為成功生成NPC。

這條join確實提供三個原始地圖模型位置；**佈告欄是否另有伺服器互動，
此資料沒有證明**。不能把檔名含npc當成可綁1606/1607或崑崙NPC的依據。

## Mapmarker 不是本地 NPC 擺放目錄

另一組標記使用role+3F98 count、role+3F9C開始的18-byte身份／名稱記錄，
及role+3FFC開始的6-byte位置記錄。`004E9B50(actorWORD,x,y)`先查名單，
找到才存+2/+4並呼叫`004C2660`；找不到直接返回，不從MDL建立NPC。

`004C2660`使用UI+232DA8的control(index+1)，以及UI+232DA6的
control(index+6)，再經`004C2510`投影。`004C2580`重設四組座標為7FFF並
隱藏控制項。當前world dispatcher可見55→E9BC0、56→EA140、57→E9EB0，
5E／6F→E9B50；資料是收到的身份／位置，沒有本地map×NPC座標表。

73→`004C25F0`確實會依actorWORD隱藏這個名單的標記，但它同時由world
despawn分支呼叫，不能倒推「名單標記就是72的本地生成来源」。
72仍進`004CC380`，从输入记录读取selector、方向和packed位置。
這裡採精確caller／field審計，沒有新增未驗證55–57封包codec或遊戲規則。

## 具體剩餘邊界

後續更新：以下第1點的零寬Pass與ROM路徑解析限制已沿原生程式資格化並修復，
完整142份MDL來源解析結果見
[MDL修復報告](current-mdl-zero-pass-20260927.md)。保留以下文字作為發現時的
追查記錄；該解析缺口不再是未處理事項，完整NPC身份／面向關係仍未恢復。

1. **CityI2 ModelDat零寬Pass格**：釘定檔的實體第5012行為`0 2`，
   既有嚴格`parse_mdl`在此回報`MDL Pass dimensions`。這是解析器原先只
   資格化正寬度的限制；不證明原始檔壞掉。下一個原生目標是`0044C980`
   讀ModelDat／Pass的0×2分支、其allocation/loop與後續`00441730`，再
   決定是否擴充parser。不能用略過整列的方式聲稱已解析所有崑崙模型。
2. **靜態模型互動**：若要知道這三個佈告欄是否被點擊選中，精確後續
   caller為`00437250`、`004445C0`、`00449740`、`00449870`的model lookup
   及hit路徑。需證明從這個模型實例到C2S身份欄的完整鏈；目前沒有。
3. **World NPC身份與放置**：需原服72輸入或原始server配置，綁完整
   area/scene/instance/template/x/y/direction；本輪本地圖資沒有補出這組
   缺失鍵。Mission文字、模型名或actor標記不提供這項授權。

可採用成果是source-backed地圖UI／模型審計資料和精確原生讀寫契約。
沒有新增或推薦任何NPC擺放，既有native-only政策不應因本輪解除。
