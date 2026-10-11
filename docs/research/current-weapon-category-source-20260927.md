# 當前 WPN／TWP column1 原始分類宣告

## 結論

**本輪補上了column1的原始欄位名稱與分類清單。** 它在當前來源中明確名為
「類別代碼」，並非完全未宣告欄位。可將此名稱、來源分類文字及raw code納入
來源catalog。先前`current-weapon-mapping-fields-20260926.md`中「意義尚未證實」
須縮小為「未找到轉成DA selector的原生consumer」；不能再說來源沒有名稱。

**仍未補上item→DA外觀映射。** 後段分類包含取得來源／裝備世代，會跨刀、劍、斧；
即使前八項是武器型態，也不能據此給任意item建立DA binary／ordinal／variant。
未改正式client、DB或共用runtime，未讀退役來源。

## 原文與精確行號

來源：`God2/Data2/Patch/Comm/gamedata.csvZ`。以下是解碼後以LF計數的1-based實體行；
工具保留每行原始hex，CP950解碼只供閱讀。

- line1：`GameData,1,2,38106`。不把這些數值當作已知server版本語義。
- line2：`RowDesc,1`。
- line3開頭：`ITEM_ID,類別代碼,道具編號,圖碼(同圖檔名檔),名稱`。
  因此zero-based column1的確切原文是「類別代碼」，column2是「道具編號」。
  本行只有25個欄位名稱；不可延伸成32欄WPN所有尾欄都有原始名稱。
- line10：`ItemType,46`。
- line11完整原文：

```
1,1000,WPN,武器,刀,劍,斧,杖,槍,鞭,弓,飛刀,任務武器,新手包裝備,封測獎勵裝備
```

- line46完整原文：

```
19001,20000,TWP,精粹武器,刀,劍,斧,杖,槍,鞭,弓,飛刀,超精粹武器,測試用武器,神裝類,二代裝類
```

清單按原生loader的zero-based子類slot順序列出；數量是當前實際item rows的column1計數。

| code | WPN分類原文 | WPN rows | TWP分類原文 | TWP rows |
|---:|---|---:|---|---:|
|0|刀|68|刀|60|
|1|劍|71|劍|60|
|2|斧|68|斧|60|
|3|杖|68|杖|60|
|4|槍|69|槍|60|
|5|鞭|68|鞭|60|
|6|弓|68|弓|60|
|7|飛刀|68|飛刀|60|
|8|任務武器|50|超精粹武器|80|
|9|新手包裝備|8|測試用武器|0|
|10|封測獎勵裝備|24|神裝類|8|
|11|未宣告|0|二代裝類|61|

WPN共有630行，TWP629行；全部code都落在各自宣告清單內。
這是source分類資格，尚未動態證明item row column1驅動任何world appearance consumer。

## WPN組前30行及TWP組前30行

WPN header為line4803 `WPN,630`。前30行4773..4802全屬於line4613宣告的
`NPCItemList,189`尾端，沒有緊鄰的武器selector欄名。前一section是商店／NPC物品清單，
不能把其column1套用到WPN。

TWP header為line15477 `TWP,629`。前30行15447..15476屬於line15420宣告的
`MED03,56`尾端，也沒有另一套武器外觀欄位宣告。
工具JSON保存上述60行完整原文及原始hex。

## 不需suffix推算的反例

下列都是item row自己的column1及描述，不使用tag尾碼或圖示ROM順序：

- line4880，WPN key92「新菜刀」，code9，說明`武器-刀-第1階`。
- line4959，WPN key192「新匕首」，同code9，說明`武器-劍-第1階`。
- line5040，WPN key292「新短斧」，同code9，說明`武器-斧-第1階`。
- line15646，TWP key19171「神裝-通天神劍」，code10，說明`神裝-物攻-劍-第10階`。
- line15745，TWP key19271「神裝-滅天魔斧」，同code10，說明`神裝-物攻-斧-第10階`。

因此「column1是來源類別」與「column1等於唯一世界武器art類型」是不同命題；
後者不能從這份欄位清單成立。

## 當前原生consumer核對

使用當前重建pseudocode並核對相關code spans與現用PE一致。以下屬靜態證據，
本輪沒有聲稱完整loader原生執行；此前16組definition差分仍是獨立既有動態證據。

1. `456130` source dispatcher先讀section名稱column0、section row count column1。
   `ItemType`分支在`456212`附近呼叫`459150`。
2. `459150`每個ItemType record長`0x642`：column0/1分別存WORD `+63E/+640`
   （例如WPN 1/1000，是該ItemType列的ID範圍）；column2 tag存`+0`，
   column3整組名稱存`+26`。column4開始依序讀取名稱，count從0增加，
   第i個子類名稱存`+(i+2)*0x26`，最多40格；count在`+63C`。
   這確立原始分類清單從slot0起，不需對Wpn01001作字串算術。
3. `459380`只把section tag與上述ItemType tag比對，回傳ItemType row ordinal
   及`+63D`的native family selector；它沒有讀某一WPN item的column1。
4. `456130`匹配WPN／TWP後進`4599B0`，其逐item讀column0作key，再進`459420`。
   既有差分已證實item的column1改值不改396-byte metadata，且token accessor未讀該欄。
5. `RowDesc`分支`4567A3`附近僅跳過宣告行數，未建立world selector映射。

針對`D2AA4/D2AA8`（ItemType table/count）的literal xref查找只找到初始化、
`459150`載入、`459380`section lookup及`455AE0`釋放。
這不是對間接pointer alias的全域不存在證明；它沒有提供另一個item-column1 consumer。

同名column1的其他讀取不能混用：`459EF0`在RomMaps分支讀的是icon ID區間；
`458ED0`在NPCItemList分支讀它自己的DWORD欄位；`459A80`屬Map_City_Coordniate。
它們不是WPN row解析器。這些section由`456130`各自明確分派。

## 可整合範圍與下一條確切缺口

可以補入來源catalog：column1原名「類別代碼」、ItemType分類原文、raw code、來源行號與hash，
以及WPN／TWP不同的特殊分類清單。不要把「精粹」改成「精淬」後當原文保存；來源兩處拼法不同。

下一個能改變world實裝資格的證據仍是：

- 另一個真正保留／消費WPN row類別碼的當前原生路徑，並把它與其他欄位組成DA；或
- 當前原服相同owned key與20-byte instance的裝備前後DA（需actor/body/binary/ordinal/variant
  全部對齊），特別比較同code9或10下不同武器型態，不能只取得一筆刀類樣本。

HeroDoll已有刀／劍resource名稱只提供接收端art分類；本輪没有建立兩個表之間的權威join。
本有界lane到此停止，不新增server mapping。

## 工具與驗證

`tools/strike_lab/current_weapon_category_source_20260927.py`

```
python -X utf8 -B -m tools.strike_lab.current_weapon_category_source_20260927 --output artifacts/research/current-weapon-category-source-20260927/source.json
python -O -X utf8 -B -m tools.strike_lab.current_weapon_category_source_20260927 --output artifacts/research/current-weapon-category-source-20260927/source-optimized.json
```

兩次exit0，輸出完全一致：SHA256
`c203bae5b84cbd0aae3611d52d9a82236d0e3917fb040fcf0a287616ab9597cd`。
狀態明確是`SOURCE_DECLARATION_QUALIFIED_DA_MAPPING_UNRESOLVED`。

- EXE：`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`
- gamedata壓縮來源：`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`
- decoded：`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`
- 現存current-native映像：`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`

工具釘選以上hash、核對來源清單及全部1259 row的code界線，並比對四段loader code與目前PE。
不包含完整native parser執行或圖形驗收。
