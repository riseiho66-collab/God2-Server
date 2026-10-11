# CN 世界71怪物外觀來源串接

輪次：`20261007-cn-world-monster-display-contract`；前輪 catalog45。
階段一：靜態原生恢復、來源整合及來源帳本。沒有建置、測試、執行
客戶端／服務端／Lua、操作正式DB或部署。這裡的 Python 只讀取固定
PE／既有明文資源、產生來源及封存，沒有執行原生 loader 或新C++。

## 原生範圍與來源

CN PE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
WORLD `0048FCC0` 的表 `004929D8[71]` 實際指向 `00491752`；限定分支
至 `004919CB`，193條指令、633bytes，所有外部邊回到已知世界接收
loop `00490AAB`。`world-connection-1` 的71長度21；不延伸為其他階段。

直接來源 `00428500`（分類／群組／序號查表）、`00430A50`（替換）、
`00428490`（顏色表）、`004829D0`／`004828F0`（單模型資源）、
`00483C10`（四部件資源）、`004F92A0`／`004F9A80`（實例池）、
`004F91C0`／`004FA610`（模型初始化／名字title）。
`0042E010`／`0042F870` 為 EnyName／SpecialEnyInfo loader。
每個函式保留 metadata原始路徑、C、固定PE bytes及CFG；calls不當成
已追完callee全圖，metadata長度不當成全程式閉包。

新增 `CnWorldMonster` 保留完整21bytes，讀取以下原生消費欄位：

| logical欄位 | 原生用途 |
|---|---|
| WORD1 | low16實例識別；8000另有場景隱藏條件，不用6F的low12 |
| DWORD1>>29 | 方向0..7 |
| byte3 | 資源替換selector，與單模型3D分支的本地寫入重疊 |
| byte4&1F | 原生state／title狀態，無戰鬥能力語義 |
| WORD5&3F／WORD5>>6 | 分類／群組；分類必須小於17才能查表 |
| DWORD9 | x=(value>>2)&7FFF；y=value>>17；low2保留 |
| WORD19>>3／low3 | 外觀序號／資源pose；pose並非方向 |

WORD7、bytes13..18不補值、不重命名為能力。來源不提供從空白生成
怪物的builder，也不從SQLite ID推定原生實例ID。位置／方向改寫僅
修改已證明的位元；消費端pose／3D改寫另標記為本地預期，不拿改寫
後buffer替代原始S2C。

## 當前資源載入順序

使用catalog41已保留的 `cn-current-npc-name-source-01/inputs/current-gamedata.csv`，
明文SHA256 `16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3`。
現有編碼來源 `Data2/Patch/Comm/gamedata.csvZ` SHA256
`8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a`。
不重跑解碼，不恢復整個歷史資源樹。解析保留raw CSV bytes及行／位移／SHA，
沒有整份CP936 decode或繁簡轉換。

EnyName標頭7935不是 `0042E010` 迴圈上限。loader先讀下一行
EnyNameTotal8076，calloc 8076×26；分類記錄以分類索引覆写群組數與
指標，群組12bytes、逐列26bytes。共16個分類block，15個有效分類。
後段分類7覆寫前段分類7的24列：8,076筆依序資源列，8,052筆有效
查表鍵。這些是外觀列與索引，**不是8,052種怪物／怪物能力表／遊戲路徑**。
群組lookup保留「第一個同group且ordinal在count內」順序。
列首label不參與原生ordinal，也不充當全域怪物ID或地圖ID。

每列header：色selector高4bits、單／四部件bit0、pose bits1..3；
單模型selector byte1。名字從列欄位1取前15原始bytes加NUL，可能
切斷DBCS；忠實保留原生截取，不為美觀修字或改識別。calloc清零
讓這個**基本表**26bytes未寫區域有已知零值。
四部件模型5001..5003按原生token及 `%d` 格式投影，部件順序是
body、face、head、weapon，不是CSV中head、face、body、weapon的列順序。
源碼Rows.inc由固定原始列靜態生成，查表與來源行號同時保留。

當前唯一 SpecialEnyInfo 行是 `1,IGS_SPECIAL,0,0,149,1`。
其loader用未清零allocation，header完整可確定2、selector149、name
前4bytes為0；其他未寫bytes不宣稱為零。`00430A50` 遇空名字會
保留**基本列高4bits＋替換列低4bits**並複製基本列16byte名字。
所以只投影實際消費欄位，不杜撰完整26byte替換記錄。

byte3非零都會呼叫替換：selector1套目前唯一替換；超過1返回基本列，
但WORLD caller仍把WORD19低3bits換成返回列pose。byte3零則保留
原始wire pose。高13bits ordinal始終保留。

## 接入來源與限制

新增五份來源：`CnWorldMonster.h`、`CnCurrentEnemyDisplayCatalog.h`、
`CnCurrentEnemyDisplayRows.inc`、`CnWorldMonsterDisplay.h/.cpp`。
`prepare` 要求非零catalog/model revision、固定PE/encoded/plain
SHA及實際載入8076/1筆、必需的真實receiver/resource `current` callback。
每種模型仍需要实际cache/loader供應器：單模型先取得004829D0輔助欄位，
再004828F0取／載入model，model必須<200hex；有效selector3D才改
本地byte3。四部件經真正00483C10語義供應器取得四signed handles，
任一負值不產生可用projection。缺值不補0／預設模型。
callback前後重查revision；它代表必需的實際資格來源，不是已建好的
正式資料供應器或已觀測到客戶端模型。

原生兩個constructor使用同一256筆、stride1D8、owner+70實例池。
同ID已有實例時更新座標／方向／state／title及scene high-bit隱藏，
**不重建名字、模型或single/composite類型**。新ID找第一個FFFFFFFF
空slot，分兩種模型初始化；滿池記錄失敗。來源projection不模擬池，
不把重送71當成外觀替換成功。實際消失／重用／reset與壽命仍要追查，
不能挪用玩家6F presence lease作怪物身份。

這輪有新的WORLD71來源binding，沒有C2S遭遇／互動原因配對，沒有
common怪物權威／spawn／儲存／TW和CN推播controller／Application
掛載，因此完整雙向路徑新增0、partial owner chain新增0。
沒有新增DB表，既有TW RecoveredMonsterRecord只作差異context，
不能當CN證據；凍結TW runtime和原生字體／繁簡轉換均未改。

## 能力值研究的界線與下輪

此限定71 lookup／constructor未恢復雙攻、雙防、四維、五行、HP/MP
或完整攜帶技能。顏色、pose、模型、名字及catalog ordinal都不能
冒充這些值；未讀欄位維持opaque，此結果不證明遊戲全域或官方S2C
一定不傳能力。觀測83使用某技能也只證明該次施放，不證明完整技能集合。
不以外觀列建立假的共同怪物stat表。

接續追世界怪物移動／刪除／選取與戰鬥入場的實例壽命、原生C2S
producer及1C/78/83等consumer來源；再把真正怪物authority與共享
戰鬥核心、版本呈現／持久化連接。未知精確能力和原生規則繼續定點逆向。
全遊戲總數／完整路徑總数及完成率維持未知，不用opcode或外觀數相除。
