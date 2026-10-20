# 台服身份與外觀材料的實際來源：pass7

本輪只做靜態 REA、唯讀來源檢查及文件審查，沒有建置、測試、遊戲／VM、
codec、遊戲 SQL／schema、匯入或部署；沒有修改 Catalog、核心或原版檔案。
以下「本機產生」是客戶端記憶體結構的來源，不代表原服服務端封包產生規則。

## 分析輸入與來源邊界

原始 `God2.exe` SHA256 為
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
外部證據位於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass7/native-material`。
獨立分析副本先沿用 pass6 的 `e447ed...` CALL seed，之後只增加 `45A1A0`
的分析入口，得到 `f42f71f20cc7c4d05cbe4b2bc3d3f51c3b942b1c4f7323f46db41776d881e52f`。
兩份副本均逐一驗證原始13個 PE section 位元組完全相同；合成 caller 不是原生 caller。

目前客戶端 `Data2/Patch/Comm/gamedata.csvZ` 的唯讀 SHA256 是
`ef297a84e828537c4a18c5cf0be3d1c15bc26d5d2f25850ce9f2f030bdb58fa2`。
它不同於既有 `NativeEnemyDisplayCatalog` 所要求的舊來源 `70a4e7...`。
目前 `45A1A0..45A55F` 原始碼區間 SHA256 是
`3af149d9e91ff827f2671cdf9a9da880ba7bfd46245029e4b8b90a4d8f97b4da`，
也不同於舊報告區間的 `41a48f...`。本輪重新取得現行函數證據；沒有把149c
資料表、舊解碼資料或舊映像直接升格為本版材料，亦未解碼目前 csvZ。
這只能證明 byte pin不相符、不能證明同一來源；沒有證明解碼列的語義不同。
同樣，函數區間 hash不同不代表公式改變，可能包括指令／位址／重定位差異；
本輪沒有做完整舊版逐指令等價性判定。

## 世界文字來源會進戰鬥 UI，但不會產生完整 S1C

現行 `468AE0` 的 case6F（分派槽 `46B790` 指向 `4695C8`）經
`4FB460 → 4FC1C0` 建立世界角色快取。變身分支可能先改外觀材料，因此不把
傳入快取的完整外觀視為原封包全部原樣；這不影響下列已觀測的文字複製來源。

`4FC1C0` 找一個空槽，將身分保存為傳入 DWORD 的低12位；從6F body 的
十進位28、44、60（`0x1C/0x2C/0x3C`）偏移複製三段 NUL 字串，目的為 manager 的
`0x18 + index*0x268` 記錄內 `+0x04/+0x14/+0x24`，即 manager 相對
`0x1C/0x2C/0x3C + index*0x268`。本機此處使用無界字串複製，不能因固定欄寬便略過
來源終止檢查。快取 lookup `4FC960` 比較完整傳入 DWORD，不再代呼叫端取 mask。

`4FAC70` 將這三串複製到呼叫者 buffer；`4FAD20` 另讀 manager
`0x93 + index*0x268` 的一個狀態 BYTE。`515C90` 處理普通 player1C 時，確有
`51626F/5162E4` 兩個實際呼叫，為戰鬥側邊文字及旗標提供世界快取來源；
找不到快取時有空字串分支，自己則另以既存 Battle `+0x78/+0x88` 覆蓋側欄文字。

這條路**不是** root40 或世界快取到45-byte S1C 的 serializer。S1C 自己的
9..40文字仍先拷進 actor descriptor，之後 `52CCD0` 另用它們設定 renderer。
世界側欄字串與 S1C renderer 字串不能被宣稱必定相同。世界6F快取低12位身分、
2A／戰鬥 WORD 的其他位元，以及完整 account／character／Session 身分也不能互換。

## 戰寵 reference 可以解碼，但沒有唯一原服逆映射

`515C90` 將 wire WORD7 保存到 normalized descriptor `+0C`。
pet variant4000 在 normalized 後是8000分支。`52CCD0` 對非零 reference `w`
先取 `n = w & 3FFF`，再依以下優先順序查 `459A60`：

| 條件，依表列順序判定 | metadata key 的解碼 | `515C90 → 45A0A0` 的顯示定義 |
| --- | --- | --- |
| `w & 8000` 非零 | `n + 5DC0`（24000） | area0、scene3、ordinal n |
| 否則 `w & 4000` 非零 | `n + 6D60`（28000） | area0、scene13、ordinal n |
| 兩旗標都沒有 | `n + 3390`（13200） | area0、scene2、ordinal n |

`C000` 先符合8000分支，所以與同 low14 的8000 reference 等價。除此以外，
不同 flag／ordinal 也能解出同一 key，例如 key24001 可由 `8001`、`C001`
或無旗標的 `2A31` 解出；但三者所選的 EnyName scene／ordinal 不全相同，
各自仍須真的存在該顯示定義。零 reference 會略過 metadata 查詢；
非零但 low14 為零時，`45A0A0` 會拒 ordinal0。不能只比 key 便稱完整外觀相等。

`459A60` 接收 unsigned WORD，只在 key小於 `7F58` 時回傳 metadata 指標。
Pet1 保存入口 `4A29A0` 檢查 `3391..3778` 或 `5DC1..6D60`，且查表須非空。
Pet2 `4A5090` 的初步上界雖允許 `7F58`，但查表隨後拒該值，實際仍需
`6D61..7F57` 且存在 metadata。這些是保存／顯示 consumer 的限制，不是
「每份戰鬥 reference 必須等於原出戰寵 key」的原服授權證據。

E3／FB 真正接收函數 `4A2B70/4A52A0` 保存完整 instance，再刷新 panel；
panel `4A1CF0/4A40C0` 查相同 metadata。這條有界路徑沒有產生或送出
S1C／86/4。沒有取得變身／替身與保存實例的原生 producer lineage，故本輪
沒有對 `owned_saved_vitals_level_v1` 強加 reference==saved key，也沒有把
reference 改寫為某個自選 canonical flag。可用成果是精確解碼、alias／定義
檢查 recipe；若未來建立「正常保存種族」的 CUSTOM 來源，必須另外明示其範圍。

## EnyName26B：確有本機完整來源的條件式 recipe

新增入口後完整取得 `45A1A0`。它先清除17組 area root，分配26-byte記錄 arena，
再按 area／scene group 建立12-byte descriptor。`45A000/45A0A0` 的查詢順序是
area0..16、精確 scene WORD及一基 ordinal；原 source label 不是位址或全域怪物 ID。
重複 group 的 root 更新與 arena 記錄序列也不能被名稱去重取代。

arena 及 descriptor 都呼叫 `547E23(size,count)`。成功的小塊分支明確
`memset(dst,0,size*count)`；大塊分支用 `HeapAlloc(...,8,...)`，即
HEAP_ZERO_MEMORY。這證明有效、非空成功分配的未改欄位從零開始，與任填服務端
opaque 預設不同。allocator 可失敗回 null；loader 不在每個後續使用前檢查 null。
無效 count、乘法溢位、配置失敗都不屬於可安全重建輸入。

| 26B offset（十進位） | Native 寫入來源與邊界 |
| --- | --- |
| 0 | col2低4位寫高 nibble；col3低1位寫 bit0；col5低3位寫 bits1..3 |
| 1 | col4 resource code 取低 BYTE |
| 2..17 | col1 `strncpy(...,15)`，offset17強制NUL；不做語言轉換 |
| 18..19 | 符合下列條件時讀 col8 的 `b` component token |
| 20..21 | 符合條件時讀 col7 的 `f` component token |
| 22..23 | 符合條件時讀 col6 的 `h` component token |
| 24..25 | 符合條件時讀 col9 的 `w` component token |

component 寫入須同時滿足原始 resource code為5001..5003、col3 bit0非零、
token非空且 token[1] 等於該 component字母。令 r為原始resource code，第一個
BYTE 的 low4 是 `r-5001`，high4 是 token[2]低4；第二個 BYTE 的 high3 是
token[0]低3，low5 是 token+3 經 `%d` 轉換所得整數的低5。這是 BYTE 寫入結果，
沒有另創分類／階級語義。不進入該 token分支的 pair 保持 allocator 的零值。

`5823B4` 的實際格式位元組為 `25 64 00`（`%d`）。loader未檢查 sscanf 回傳值；
因此 malformed decimal token可能沿用先前／未初始化的 stack temporary，不能
被規定為「原生轉換失敗時補零」。安全的來源 recipe 必須拒絕畸形 count／token、
確認每個所需轉換成功並保存整份來源 pin；本輪沒有執行這個 parser。

以上提供**顯示定義26B**的完整本機來源，沒有 HP、雙攻雙防、世界位置、掉落、
遇敵權限或原服種族與 instance映射。既有 `NativeEnemyDisplayCatalog` 保存的是
來源 raw列及全目錄 pin，也明說不是 synthesized26B bank；它的舊149c／舊csvZ
來源資格必須另外處理，不能改一個 SHA字串便借給目前客戶端。

## 17-byte appearance 與完整身份仍缺甚麼

`515C90` 對部分 EnyName composite 或固定5E定義，取定義中的兩個完整 DWORD
component，設 mode1、reserved BYTE及 transform WORD，直接呼叫 `5177C0`。
這是內部 stack輸入，並沒有證明產生完整網路17-byte record 的 opcode、
subtype及所有尾端位元組。`5177C0` 自己亦包含 ordinary／transform／GodDoll
不同路徑；不能把某個內部零欄位擴為所有 wire原型的零預設。

World2A／DA 及 battle ordinary appearance 都能觀測到四個 packed component
及 variant的消費，但解析資源的函數不同：world `461270` 包含 mounted／Drv
特例，battle `5177C0 → 454F60/454E50` 以 Fight資源選擇。它們不是完整
item key到HeroDoll的 producer；本輪沒有恢復已裝備武器 key到 selector的關係。

| 待生成材料 | 已有精確來源 | 仍必須保留／下一個具體缺口 |
| --- | --- | --- |
| player level與HP/MP | 真正 role／resources／canonical checkpoint；沿用pass6 adapter | 成長公式及其他native identity位元 |
| pet level與HP/MP | 完整active44 E3／FB保存值；沿用明示policy | 其他stats、metadata、status、變身與reference lineage |
| EnyName26B | 本輪 loader＋零初始化＋完整有效來源recipe | 目前csvZ完整來源資格；不可借舊dataset |
| player／pet S1C WORD7 | 解碼與兩套lookup完整追到 | 原服唯一producer不存在於此證據；aliases保留 |
| player S1C strings | wire到descriptor／renderer已證；世界快取另供側欄 | root／secondary／guild與各receiver編碼的實際私有來源，不假定兩者相同 |
| identity WORD5／DWORD41 | variant及status被消費；bit0令status歸1 | 服務端選旗標／palette／特殊status規則；不由HP／技能表補 |
| battle86/4 | 完整原型＋已知component／transform consumer | native完整wire producer、所有opaque／尾端來源及裝備映射 |

下一個有界 trace 是 current csvZ 的合法來源建立與 `45A1A0` 上游 parser來源，
以及變身 producer如何選擇寵物 reference；若追 WPN，則追 metadata／已裝備
slot到 component選擇的實際 writer，不能再只重讀 DA／5177C0 consumer。
本輪不因找到本機顯示定義便移除 Catalog 的完整1C／外觀／來源要求。

## 收尾與審查

首個 non-TTY helper只有完成 open metadata，exec拒絕寫入stdin；沒有成功
graceful close，已保留該失敗及自有 process清理紀錄，不能算正常 close收據。
後續兩個有TTY分析 session均已 close_binary，helper及CLI自然退出0，沒有執行目標。
完整原件、矩陣、SHA與作者／獨立文件審查分別留在本輪外部證據根。
沒有可玩、Windows相容性、動畫或原服材料完整恢復的驗收宣稱。
