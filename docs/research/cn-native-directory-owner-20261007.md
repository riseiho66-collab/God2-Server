# CN 原生清單94／A4／AE／B0資料鏈（2026-10-07）

本輪新增三個來源檔：`CnDirectoryWire.h`、`SharedDirectory.h/.cpp`。
已接入的條件式來源鏈為：同一個已登入世界的共用角色 lease →完整94／A4
請求 →必要的權威資料來源 →完整AE／B0原始回覆 →同一CN transport。
正式資料來源、業務規則、一般世界分派器及正式啟用仍未完成，不能計為完整遊戲路徑。
只處理selector19／23／24；原生其他清單、模式和變體仍保留未完成。

唯一CN主證據是釘定God2_opt.exe，SHA256
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
新證據獨立保存在`cn-native-directory-owner-01`，先前catalog31及原始證據不覆寫。
全程靜態來源／指令／資料表分析，沒有建置、測試、執行遊戲、讀正式DB或部署。

## 實際資料與方向

全部偏移以下均從含opcode的完整logical record起算。

|方向／封包|完整長度|已恢復欄位|
|---|---:|---|
|C2S94|9|byte1 selector；byte2..4為此producer未寫入的原始padding；DWORD5..8是清單owner游標|
|C2SA4|3|byte1 selector；byte2為翻頁方向FF／01|
|S2CAE|25|byte1 subtype；其餘23bytes不命名、不填值；consumer複製完整24byte payload|
|S2CB0|9+40×count|WORD1 total BlockSize；byte3 selector；byte4 count；DWORD5 cursor；byte9起40byte rows|

`0048FCC0`的AE branch從`004901D6`開始，先檢查payload subtype1的額外
00538F50分支，再把record+1交给00511620。B0 branch `0049022B`把record+1
交给005118E0。以上primary branch只保存明確入口至共用dispatch exit的有限區塊，
不以任意窗口內的線性解碼當作完整dispatcher。

005118E0的實際row迴圈把payload+8的32bytes及payload+40的8bytes複製到
`base+40*row[32]`。byte32是目標列索引，不是批次內的順序；byte33未命名。
005137B0把row0..15及16..31作兩個字串區域顯示，並讀WORD34、36、38；
這些字串的業務種類與三個數字的業務意思仍未知，不能當角色ID、雙攻雙防或技能資料。
檢查40byte row及BlockSize只證明結構，沒有證明每個索引皆能安全写入原生陣列。
權威來源仍須具體提供原生容量、字串終止及每個opaque欄位的合格資料。

## 同一個owner欄位的對應，沒有按opcode猜配對

|94／A4 selector|B0 selector|AE subtype|資料base|B0寫入／94讀回cursor|
|---|---|---|---|---|
|19|19|08|player+30E74|player+30E80|
|23|23|0B|player+36D4C|player+36D58|
|24|24|0C|[player+1C85A8]+469C|[player+1C85A8]+46A8|

AE更新的是base+16起的24bytes，不是cursor；B0更新cursor與索引式清單列。
0050E3B0取相同cursor放入94payload4。前輪已追明`player+4308C`是同一world
network，且mode來自真正Account07flags bit0，不能把它命名成GM／付費／權限。
mode1與本輪三個selector對應清楚；mode0其他分支仍未一併資格化。

WORLD S2C94的consumer00524E10是不同的小型狀態更新，WORLD S2CD1也沒有
因此成為目錄94的回覆。AE/B0與94/A4具有同owner欄位的資料關聯，但客户端單獨
不能證明官方服務端的請求因果、回覆順序、權限、拒絕格式或持久化規則。

## 翻頁原生路徑

00515680從`player+4308C`取得同一world network。UIcontrol52方向-1，其餘
經原生UI入口的53方向+1。先限制候選page不小於0且不超過pages-1。
若`candidate_page*25+1 <= cached_last_index`則僅更新本地page並00512C50刷新；
未載入時經00515E3F→00515E4C送A4，payload兩個byte為selector與有號方向。
因此不把每次翻頁都計成網路請求，也不將A4第二byte當頁碼。
其他D1與mode0分支的primary指令亦保存，但不加入本輪handler適用範圍。

## 來源實作與明確邊界

`CnDirectoryWire`保存94原始padding、B0全部rows/游標及AE完整payload；不把
opaque文字轉成共用ID，也不合成成功／空清單。94游標不強迫等於先前回覆，因為
正式佇列／競態規則尚未恢復。A4僅接本輪已知的FF／01方向，不援用S2C長度拆C2S。

`SharedDirectory`從當前world ticket的完整07讀mode，並以同connection/session/
account/character/generation的ready presence確認來源。權威resolve及
qualify_delivery均為必需；後者須確認真正資料版本、權限、原生索引容量與欄位，
本輪沒有假定它們已實作。完整批次先作格式分割，各個請求再交權威來源。
輸出僅允許同清單channel的完整AE/B0且保持資料來源順序；結構對應是本輪有限
source contract，沒有宣稱官方一定回這兩種或一定同selector。未處理的交叉清單、
推播、多回覆規則仍由後續原生研究接續。傳輸失敗沿既有關閉／cleanup。

沒有增加或複製資料表；真實目錄／社交／排行內容預設來自共用權威資料。
沒有改動凍結TW、聊天、IME、認證、字體、客戶端或文字轉換。

## 計數

新增條件式partial owner chain1；phase source associations4（WORLD C2S94/A4，
S2CAE/B0），不是新增opcode、一般階段等價或已完成路徑。
本輪六個C2S分支（2種請求×3selector）與六個S2C投影分支（2種回覆×3channel）
僅限明列範圍，沒有當成全遊戲分母。
完整路徑本輪新增0；全遊戲總數、已完成總數、百分比維持unknown/null。

## 後續

追查實際業務名稱／資料來源與原生row容量，補上具體共用權威實作；再接入一般
ready-world分派器及完整登入／世界值供應。未恢復因果、交易、權限、變體前不啟用。
同時保留前輪94未賦值padding/DWORD特殊分支及07來源約束，不能用零補齊。
