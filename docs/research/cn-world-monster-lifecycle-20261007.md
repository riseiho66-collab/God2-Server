# CN 世界怪物71／78／74實例壽命來源

輪次 `20261007-cn-world-monster-lifecycle`；基準 catalog46。
第一階段來源整合；未建置、執行C++／Lua／遊戲、測試、正式DB存取或部署。
Python只執行靜態PE/CFG解讀、雜湊與封存、來源帳本生成。

## 原生接收owner不能合併

固定CN PE SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
世界switch DWORD表 `004929D8` 的opcode entries及直接primary指令：

| WORLD opcode | 入口 | logical長度 | 真正this-owner | 操作 |
|---|---|---:|---|---|
| 71 | 00491752 | 21 | main+1499FA0 | 外觀lookup後single/composite新增／已有實例更新 |
| 78 | 004919CB | 5 | main+1499FA0 | 004FB290名字title等級顯示 |
| 74 | 004919DF | 5 | main+1499FA0 | 004FA750移除low16實例 |
| 73 | 00490BB7 | 5 | main+1464C58後main+1499FA0 | 移除player，再移除轉換後high-bit實例，再UI清理 |
| 75 | 00491DAB | 5 | main+147C720 | 另一個pool的004FA750，不是71的pool |
| 77 | 00490DB6 | 7 | main+147C720（byte5&8） | 004FA820呈現資源，否則self/player分支 |

71構造器本輪不重跑恢復，只核對catalog46封存的primary bytes及manifest；
同callee不證明同object/實例命名空間。75及77雖也有256×1D8的結構，
主物件offset不同，不把它們當71的刪除／移動。前輪沒有接75／77，
因此保留前輪原始紀錄，這輪新增具體owner邊界。

73低WORD移除player後，以完整DWORD low15 OR8000送進main+1499FA0。
它會同時影響player、怪物型pool及UI；不得用它代替任意怪物74。
74只讀WORD1，logical bytes3／4仍須來源提供且原封保留；不補零。

77 byte5&8使用另一pool；WORD1是其實例，byte3供004821A0資源轉換，
byte5 low3供呈現函式。不是座標移動，沒有技能或stat欄位證據。
其餘byte與player/self分支保留未接，不挪用71識別。

## 清理與level consumer

004FA750以完整DWORD pool identity比對傳入zero-extended WORD，
找到後在特定畫面條件產生移除效果，再004FAC90清理該slot。
004FAC90按型別清除single／四部件render資源、title，ID設FFFFFFFF，
type byte+1D4清0、+17A清0、+17C DWORD清0；不宣稱整個slot歸零。
**+17B level byte未在此清零**，不能因刪除推定level記憶體為0。
新71不代表有新78、更不能預設level0。
004FBC00迴圈呼叫每個非FFFFFFFF slot的004FAC90；實際native reset
caller需分別資格化，不因來源有此函式就宣稱已在目前client執行。

78完整lowWORD是實例，highWORD是本次顯示的supplied level：
0..30使用原生 `Lv:%d`，31..99用table `(level-30)/10`，100..65535
用 `Lv:???`。先用完整WORD格式化，再只把lowBYTE存到slot+17B。
比如native特殊文字不表示服務端level=100，level byte也不能逆推原WORD。
本輪封存format bytes、level band pointer table及原始字串bytes，
不另生成與繁簡偏好衝突的level文字，也不修改字體。
這是呈現consumer，不是成長／雙攻雙防公式。

## 已接來源

新增 `CnWorldMonsterLifecycle.h` 的完整74／78保留型別。
新增 `SharedMonsterPublication.h/.cpp`：真正的common怪物來源
（common ID、incarnation、revision、area/scene）→真實CN收件連線與
同一SharedWorldPresence的ready世代／已存場景→上一輪Display::prepare
→必需的WorldOwner來源／完整record／native pool配置资格→送出原始71。
保存私有registry identity＋recipient lease＋本地generation＋原生low16
instance；**怪物不是player presence lease，DB ID不截成wire ID**。
這是實際來源呼叫鏈，但真正common怪物owner／資源supplier及Application
尚未提供，不能稱已運行或完整雙向玩法。

同收件者／原生ID已有expected binding拒絕再次show，不能靠71重送
假設名字／模型換成功。相同common monster incarnation也不重複占slot。
局部256上限只是來源bookkeeping；完整pool也可能有NPC，必須由真正
qualify_spawn確認全部occupancy、空slot、render／title創建與reset。
Display模型handle投影單獨不能證明constructor成功。

level沿同私有binding及common incarnation接受當前source revision，
world.current及qualify_level需證明真实供應的78，low16 instance完全匹配。
只送完整78，不推導level或能力。removal依qualify_removal取得實際
退役／可見範圍退出的publication revision，不能由source失效猜怪物死亡。
先失效old binding，再送完整74；舊token不影響後續相同wire ID的新實例。
場景真實pool reset／離線對精確舊recipient lease清理expected tokens，
沒有自創reset packet；場景已改變時不往新場景發舊74。

所有public操作要求同一game thread；authority callback重入拒絕，
qualification前後重查actual recipient/account/character/ready/scene與
來源／resource revision。送包只記入佇列預期，不是TCP receipt／render
或原生接受。已改expected model而傳輸失敗時失效token並關閉仍相同
recipient世代以等待真實恢復，不把不確定狀態當成功。

本輪新增1條未掛載partial publication owner chain（非雙向），
WORLD S2C來源binding新增74、78共2筆；71用既有來源不重算。
TW凍結來源、舊接受基準、client及DB未改；没有新TW／CN表。

## 尚缺

- 真實common怪物／spawn／視野／儲存／死亡及資格owner；实际CN resource
  cache、shared pool及reset事件供應與Application呼叫點。
- 世界怪物真正移動producer/consumer、點擊／互動／遭遇的C2S與戰鬥1C
  身份接續；75／77另一owner pool及NPC變體分開恢復。
- TW/CN同一怪物的呈現對應與跨版推播，以及雙攻、雙防、四維、五行、
  HP/MP、完整攜帶技能及原生規則。78顯示level不能補成真實能力。
- 全遊戲按方向／phase／state／variant分母與完整路徑仍未知。

本輪完整雙向路徑新增0，不能用58筆CN來源binding或958個endpoint索引
當完成遊戲分母。集中測試／原生接受留到所有來源串接後。
