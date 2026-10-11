# CityI1 佈告欄 action／互動身份邊界（2026-09-27）

## 結論

**沒有新增可授權生成的 world NPC 配置。** 三筆 CityI1 `npcad.ROM`
placement 現在已追到完整原生 action render 初始化返回；它們的 source
ROM action key 1001／1002／1003 不會在這條鏈中註冊 NPC 點擊物件，
也不會產生 C2S37。新證據是原生執行和兩套 handle 的讀寫鏈，並非名稱搜尋。

另已確認：

- MDL raw type `0x17` 在 `0044C52D` 被 `and eax,0xF` 取為 action tile
  type7；不能拿高 nibble1 當 NPC 類型或面向。
- placement **零起算 field9** 經 instance+38 傳入 `0041E070`，是 palette
  index。三筆來源皆0；負值／超過 ROM palette count 原生回退0。
  不是 NPC facing。這沒有解釋其他 domain 的 direction。
- 原生互動序號、render handle、ROM action key、world NPC identity
  是不同欄位。即使數值碰巧相同，也沒有足夠的 join authority。

未修改伺服器 runtime、DB、EXE 或桌面；未使用 Classic／XJZ／退役來源。
先前模型 geometry setter 不重跑。本輪沒有聲稱畫面或真實滑鼠驗收。

## 可重現驗證

```powershell
$env:PYTHONPATH='artifacts/tooling/crypto-oracle-python'
python -m tools.strike_lab.current_npc_model_interaction_20260927 --output artifacts/research/npc-model-interaction-20260927/evidence.json
python -O -m tools.strike_lab.current_npc_model_interaction_20260927 --output artifacts/research/npc-model-interaction-20260927/optimized.json
```

兩種 interpreter 結果相同：

| 測試 | 數量 | 邊界 |
|---|---:|---|
|三原始模型 × palette0/-1/1/255|12|完整4421F0以及全部已走 game callees 返回；非像素繪製|
|action key／ordinal查找|14|完整41AE20返回，含不存在鍵|
|互動 registry → NPC pool gate|7|完整50AA20、CAD10等返回；明確合成互動註冊正／負控制|
|原始 world caller block|4|466D3F..466E20精確slice及其完整callees；距離0、3、4邊界|
|可授權的 source NPC placements|0|沒有world identity／NPC定義與三模型的來源join|

所有執行到的原生 instruction 都逐條驗證 current PE 與 pinned native image
bytes 相同，且VM代碼未被改寫；另驗證預算、EIP停止點、ESP清理、來源SHA、
原始資料與結果。沒有 Python `assert` gate。完成全部檢查後才原子替換 receipt。

### 原始檔 pins

| 來源 | SHA256 |
|---|---|
|現用God2.exe|`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`|
|pinned mapped image|`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`|
|CityI1/cityI1.mdlZ|`bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618`|
|decoded MDL|`59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef`|
|CityI1/npcad.ROMZ|`5cd0a3d02f870e5b9b073f6bebf109632650e587cb8f1290a6db464e894687e5`|
|decoded ROM|`2de80c9ad04f3f46d5af5b38272d31036960b9c8273fae1fbde654ef5ee62a32`|

ROM29171壓縮bytes／45098解碼bytes，1 palette、10 PCX images、6 ACT_DATA。
JSON保留每個48byte action header、offset、hash和CP950名字，以及三筆MDL
原始record bytes／行號／全部十欄。下列地址皆VA，RVA須减400000。

## 來源模型 → 原生 render graph

| placement／來源行 | model | source action | source field9 | 初始action image尺寸 |
|---|---:|---:|---:|---:|
|134／3478|163|1003|0|46×84|
|135／3479|161|1001|0|80×133|
|138／3482|162|1002|0|44×126|

三者仍是先前已資格化的block4,3佈告欄；這裡不把來源幾何欄再命名為NPC
坐標。ROM六個 action header 的第一DWORD依序1001..1006；native41AE20
對這些鍵線性查表取得ordinal0..5；另允許小於257且小於actioncount的
ordinal直接取用。因此其返回值是資源表位置，不是NPC template或actor。

完整已执行鏈：

```text
4421F0 instance
  instance+2C -> model; instance+30 -> frame; instance+38 -> field9
  441EC0 model -> model+8 body tile (tile+14 must equal7)
    44A0F0 tile
      449DF0 clipping RECT
      41AFE0 renderer (bank, x, y, action key, loopmode, sort, flags, RECT)
        41B290 -> 425B60 allocates graph/sprite handles
        41AE20 resolves ACT_DATA ordinal
        41B9C0 -> 425DC0 / 4270E0 / 41C360 initializes first animation state
      41E070(render handle, field9)
  instance+3C <- render handle
```

`4421F0`原始尾端為`ret 0x10`，第四stack參數在此函式未讀；工具供0並
驗完整16byte清理，沒有只相信反編譯的三參數signature。

Palette寫入位置：rendernode=`renderer+10+handle*290`；+34是ROM bank，
`bank+4`是palette count。`0041E070`校驗index，將其寫到node+2C WORD，
將`bank+8+4*index`的palette pointer寫到node+44及
`spriteManager+12EC+spriteID*200`。source只有一個palette，四組index均
落在palette0。每次原生返回後，另驗證NPC pool全bytes不變、interaction
registry count仍0、C2S queue length仍0。

### 渲染資格邊界

ACT_DATA／ACT_STEP／ACT_POOL和palette使用原始ROM bytes重新定位。
Image採**明確的header-only fixture**：寬高取原始PCX header，palette pointer
取原始palette；沒有假稱已執行PCX解碼或像素device blit。`0044A800`使用
這些source尺寸與原始tile寬高完整返回，實際推導tile frame count=1；不把
action1003的五個動畫steps誤當tile分片frame數。

已执行的render初始化callee完整返回，沒有替換game function。只有Win32
SetRect adapter；全局靜態RECT已初始化位元為explicit fixture。完整ROM檔案
載入、圖像decompress、device呈現及physical鼠標都未驗收。

## 真正 hit → NPC → C2S37 的額外條件

### 1. Hit writer 使用另一套物件

`0050AA20`遍歷的是interaction manager下的物件：

- count=`manager+A7E001C`；object=`manager+1C+ordinal*A7E0`。
- object state DWORD0必須2，object+10指定input-control序號。
- `00418CD0`要求input control在0..BFF且state=1，再返回control+14的hit值。
- `00508780(ordinal,category)`寫object+A7D0。category<7才有hit cache。
- click cache=`manager+A7E005A+12*category`；hover cache在`+A7E0064`。
  這裡寫的是**interaction ordinal**，不是ROM action或rendernode handle。

工具完整執行writer，使用明確合成ordinal2、input control7、category4/5/7。
inputManager+1202C是此分支所需事件flag；本輪不把它冒稱WM某個訊息。
`50A910`的沒有title-renderhandle分支也由原生執行，沒有renderer stub。

### 2. NPC pool 必須保存匹配handle與獨立identity

`004CAD10` selector0讀category4，selector1讀category5。每個NPC record
stride1D8，最多256筆：

| 欄位 | 用途 |
|---|---|
|pool+70+slot*1D8 DWORD|world actor identity；FFFFFFFF代表未使用|
|pool+7C+slot*1D8 signed WORD|interaction handle；與hit cache比較|
|pool+80/+84+slot*1D8 DWORD|world grid坐標，由CD010讀|

沒有identity的pool，即使hit cache有ordinal2也返回FFFFFFFF；存在identity
但handle填1001而hit ordinal2，仍不能匹配。匹配後返回內部action0x37和
**NPC pool slot**，`004CCFE0`才把slot轉成完整identity。

靜態來源註冊路徑亦可區分：`004CAFE0`先經`00508300`建立互動物件，把返回
handle存record+0C（也就是pool+7C）；`004CC380`再經`00508780`指定category4。
這些步驟不在本輪完整4421F0模型初始化trace中。不能僅拿npcad名稱補上它們。

### 3. World caller仍有距離／identity／名稱輪播gate

原始`00466D3F..00466E20` category4 branch要求：

1. CAD10找到pool slot且CD010能取坐標；
2. 相對world+224/+228兩軸各自絕對差≤3；
3. CAD10內部返回值0x37；
4. CCFE0 identity不等FFFF，且CCD80允許（有多段本地名稱時可能先換名稱
   返回0；工具使用無該表的明確fixture分支）；
5. `00496750` identity非負，且timeGetTime距前次大於1000ms。

本輪除獨立完整callee外，**另真執行這段原始caller slice**及所有經過callees。
合成identity12345678、距離0/0和3/3產生`37 78 56 34 12`；4/0、0/-4不產生
record。原生append也完整執行，只有timeGetTime adapter，沒有呼叫socket。
這不是整个466B00世界event pump返回，更不是來源佈告欄獲得了該identity。

Category5分支在`00466F72..00466FFA`不同：即使CAD10也回0x37，仍是選取
狀態／其他流程，沒有直接呼496750；因此本輪category5測試不人工接C2S37。

## 交付給主線的限制與剩餘具體缺口

可直接使用的語義更正：**field9命名palette_index；raw0x17只在目前tile
loader確認low4bits=7；action key與NPC identity分開保存。**

不應新增三筆猜測NPC spawn。要讓來源佈告欄成為可互動NPC，還缺以下一條
有來源的join：MDL model/action → 接收或載入的world actor identity → NPC
pool登錄／category4互動handle。現有S2C72消費與NPC pool登錄可支援已知
actor，卻沒有證據證明其actor是哪一塊佈告欄、是否由原服配置為NPC、提示／
任務事件為何。`CAFE0→508300→508780`是具體缺口另一端；不是理由去捏造ID。

參照先前 `current-npc-map-coordinate-join-20260927.md`（source幾何）、
`current-npc-interaction-20260921.md`（已知S2C72/C2S37契約）。本輪到此停止，
未擴查其他loader或改變正式世界。

### Palette關鍵machine code定位

以下current PE bytes已包含於本輪逐instruction pin gate；VA減400000為RVA：

| VA | bytes | 原生操作 |
|---|---|---|
|00442223|`8b6e38`|從instance+38讀field9到EBP|
|00442242|`55`|將EBP作441EC0的第4參數壓棧|
|00441EE1／00441EEF|`8b442414`／`50`|將palette參數重排為44A0F0第7參數|
|0044A145／0044A14B|`8b4c2428`／`51`|讀第7參數，作41E070的palette index|
|0044A14F|`e81c3ffdff`|call0041E070|
|0041E0B5／0041E0BA|`3b5604`／`33d2`|比較bank palette count；越界index清0|
|0041E0DC|`6689502c`|寫node+2C palette WORD|
|0041E0E0／0041E0E4|`8b549608`／`895044`|從palette指標表取值，寫node+44|
|0041E11D|`8994c1ec120000`|寫spriteManager+12EC+spriteID*200 palette pointer|

本輪最终normal/-O receipts完全相同，SHA256
`2c1f8122ec29549b673c5ec5029fddff669fd7a456421c2493a7135fbbbbc866`。
共1302個不同native instructions經逐條current/pinned bytes核對。
