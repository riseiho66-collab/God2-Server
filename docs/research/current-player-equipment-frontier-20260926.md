# 普通角色裝備 C2S28：原生鏈與整合邊界

2026-09-26。有界只讀分析；新增獨立oracle，沒有修改Application／DB／客戶端，沒有啟動遊戲。未讀退役資料，未推測戰鬥stat公式。

## 可直接交給整合者的結論

- 5-byte C2S28是 `28 key:u16 source_slot:u8 flag:u8`。所有已找到的當前直接caller都傳flag=1；**卸装仍是1，不能把尾byte解釋成equip/unequip bool**。wire沒有destination。
- 背包是0..29；**普通人物裝備是30..36**。37是神獸，38..41是另一個裝備頁，不宜合併為人物30..41。NCP42..44、蛋45、護符46..49均另域。
- 可建立 owned-instance 交易骨架：以owner+revision+slot+key定位既有完整20-byte instance，來源在bag表示裝備候選、來源在角色裝備域表示卸装候選；空格和交換須由authoritative state決定。這是可實裝服務政策，不是原服自動選格規則。
- 投影必須送完整3B metadata，41只能寫count與低WORD key，**不能把已有裝備實例縮成key+18zero**。3B/41不會自動重算人物stats或世界外觀。
- 目前尚不能把「兩格已搬移」宣稱為完整穿裝：缺物品到角色外觀欄位的資格、原生装备限制／屬性變化規則及當前客戶端驗收。現有22/24 snapshot是世界進入還原，並非通用中途equip刷新API。

## 新執行證據

工具：`tools/strike_lab/current_equipment_20260926.py`。

```powershell
python -X utf8 -B -m tools.strike_lab.current_equipment_20260926
python -O -X utf8 -B -m tools.strike_lab.current_equipment_20260926
```

兩種模式皆通過：**186個完整producer→原生queue案例 + 4012個裝備guard案例（400拒絕）**。檢查寫入範圍、queue prefix/suffix canary、精確停止點、stack平衡及pending欄位。檢查使用非assert的require，因此-O不會略過。

producer病例執行RVA96550及132E0到原生return，掃slot0..49和flag0/1/255；另測866E4 gate與兩個modal的0、8、20h、28h旗標。成功把UI+85608設1；拒絕不改pending、不發封包。這證明producer原樣傳第三參數低byte，**不是證明遊戲允許flag0/255**；所有caller仍固定1。

guard執行49B5E0到成功return或拒絕的475D60入口，測6999..8001與低2bit狀態0..3；拒絕停在訊息renderer之前。没有替換原生遊戲callee，沒有宣稱畫面／聲音或完整equip-response跑通。

Current EXE SHA256：`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`。
gamedata.csvZ SHA256：`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`。
message.csvZ SHA256：`5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`。

## 原生槽位名稱：不是憑位置猜

498030讀取VA005905F0起20個WORD，將message文字指標依序放入005B67BC；4993B0以slot30起逐格綁定tooltip。當前EXE原始20個ID為：

```text
64,65,66,67,68,69,69,70,64,65,68,69,572,572,573,574,704,705,706,707
```

這裡是message.csvZ後段一般文字索引（64位於解碼行2090），不是同檔另一section的SystemMessage64。各section的數字不能互換。

| slot | 原生文字 | scope |
| --- | --- | --- |
| 30 | 頭盔 | 普通人物 |
| 31 | 鎧甲 | 普通人物 |
| 32 | 手套 | 普通人物 |
| 33 | 鞋子 | 普通人物 |
| 34 | 武器 | 普通人物 |
| 35、36 | 法寶 | 普通人物，兩個同類格 |
| 37 | 神獸 | 別於普通衣武，不納入本輪 |
| 38、39、40、41 | 頭盔、鎧甲、武器、法寶 | mode1裝備頁 |
| 42、43 | 戰寵道具 | 別於普通裝備 |
| 44 | 戰寵裝備 | 現有NCP lifecycle另域 |
| 45 | 寵蛋裝備 | 別域 |
| 46..49 | 護符1..4 | 別域 |

49A090(mode0)啟用30..37、42..49，隱藏38..41；mode1反之。49A330對mode1頁按鈕還要求actor+4非零。38..41的3B/41/3C額外可能發C2S6D/1，普通30..36没有此分支。

## Producer與交互條件

### 496550共用producer

條件：DWORD UI+866E4=0；UI+232DEA與UI+232E20兩個panel均不存在或沒有0x20 flag。成功設UI+85608=1後送28。此函式沒有bag/equipment domain、instance所有權或count驗證；任意byte slot在原生producer層可表達，不等於服務端應接受。

### 49A330背包UI

`4820A0`將UI+232DC8節點事件送49A330；slot record位於UI+8560C+24*slot，count在+0，完整20-byte instance在+4。

- event mask04啟用：讀source item與459A60 metadata，metadata+11A的04 flag才走裝備；先通過49B5E0後送28(key,source,1)，再呼叫4D5910。未要求client傳目的格。
- drag-release（mask20）到另一格：做modal/當前drag等檢查。source bag、destination30..37且metadata flag04時走28；**沒有驗證拖放格是否與物品種類相符，也沒有把destination寫入packet**。來源equipment30..41等、destination bag的路徑同樣送28(key,source,1)。
- destination38..41的分支另呼叫49B5E0，不得與普通page合併。
- bag→bag另走C2S24，不能用28一般化所有move。
- 同格按下／放開的另一branch可能只顯示資訊；先前C2S25的PET52/53/54特例不屬本次普通裝備。

因此source slot可作server操作意圖的條件，但wire不足以復原原服法寶35/36選擇或卸装選哪個空bag格；任何自動選格規則應標記為明確服務政策。

### 其他當前callers

- 4963C0：快捷鍵先29→0尋找同key且count>0的bag；metadata flag04才送28（53/55類先分到25）。相同key多個instance時實際source是最高matching slot，仍要以slot+key查owner實例。
- 4999C0：掃30..37的既有裝備，再尋bag同key且instance某packed欄位符合條件；找不到時送equipment來源，找到則送bag來源。讀的是instance+0x0C的bits8..14，不在本輪替它取耐久／修理語義。
- 5151A0：戰鬥側來源也可送28，另有戰鬥狀態與命令安排。不能因同opcode就讓普通世界equip服務接收戰鬥中的request。
- 所有這些直接caller第三參數均為1。

### 49B5E0限制實際屬神仙

只在7000<key<8000範圍測UI+866BA低2bits：狀態2拒7101..7200或7401..7500，狀態1拒7201..7300或7501..7600。拒絕使用SystemMessage0x362=866，在message.csvZ行941明寫「裝備道具與神仙的性別不符」。此guard不是普通角色性別／level／職業限制的完整驗證，也不證明其他item沒有伺服端限制。

## 源物品可用資料和映射界線

當前原生metadata loader與既有 `current_item_metadata.py` 已涵蓋WPN/EQU/TWP/TEQ的flag04路徑。源表有武器／防具文字、能力描述和數值欄位，但沒有在本輪把任何描述轉成最終戰鬥公式。

- WPN:1 菜刀，gamedata行4804；TWP:19001 精淬菜刀，行15478：武器，與原生slot34「武器」對應。既有battle reach原生consumer也直接讀UI+85940，即slot34 instance低WORD。
- EQU:1001 柳葉甲，行5435：防具-鎧；1101山水袍行5521：防具-袍；1201鐵箍、1301三叉冠、1401木盔、1501皮手套、1601草鞋各有來源分類文字。
- 不能單用EQU category整數泛化：原表另有8/9/10等任務／變種category。新服務若先限制少數已確認實例，使用明確source-backed whitelist，而不是category%8這類猜式。
- 35／36雙法寶目的格決策未由packet授權；應先排除或明確標示server selection policy。
- client metadata396-byte definition與20-byte owned instance是不同資料。原生解析定義不會自動產生該玩家所持實例的附加屬性、品質、強化等20-byte值。

## 回應必須分四層

### 1. Inventory：3B /41 /3C

3B logical為25 bytes：`3B count:u8 slot:u8 opaque:u16 instance[20]`。498DD0接收opcode後pointer，slot為payload+1，將payload+4的20bytes拷到slot+4。非stackable或metadata缺失count置1；stackable走加法並在該consumer上限30。裝備實例應以既有owned metadata完整保留，不能把未知opaque欄位默認為原生0。

41 logical為5bytes：`41 key:u16 slot:u8 count:u8`。4991E0寫count及instance低WORD，count<1清count/key，保留其餘metadata。它更新inventory UI，但不計算角色攻防或appearance。

3C對bag是減數量；30..37等equipment格則直接清count/key，再refresh。它也不清完整20bytes。

安全的instance搬移候選投影為：clear受影響slot→對非空after-state送完整3B→必要時41確定數量。該序列的槽位資料效果可沿用既有inventory/owned-pet原生consumer證據；**普通角色裝備整套外觀、stat與畫面仍須新驗收**。裝備不是現有map/MED的zero-metadata whitelist。

### 2. Pending／提示狀態

producer設UI+85608=1。498DD0只有對slot>=30的3B、pending非零時，呼叫44E140(sound29D)，然後清pending。3B送bag、41及3C均沒有這個清pending動作。

因此單純卸装→bag3B+equipment41會留下此欄位；目前可見影響是後續equipment3B的音效提示，**未證明它鎖住裝備或阻塞操作**。不能為清它而送假非空item或清無關格。完整原服卸装response順序仍有缺口，應在原客戶端測序列與pending，再決定是否需要其他真實狀態回覆。

### 3. 外觀

3B/41路徑只改inventory record／slot icon（37神獸另有panel刷新），不呼叫角色外觀614A0／61270。world dispatcher的36/37等appearance路徑獨立，現有`current-owned-appearance`只證fresh zero-index條件下的角色component；不是任意裝備到appearance的通用序列化證據。現有owned profile→2A/6F投影不應被當成更換武器／衣服的合格更新。

### 4. 屬性／資源

S2C22→4E6B40將服務端傳入欄位写到actor（含+60/+68/+78/+7C/+80/+84等），再刷新；S2C24→4E71E0是HP/MP路徑。D1→49F510、D2→49F540分别拷20bytes到UI+866A8/+866BC後刷新另一裝備頁的數值；不得混同人物22。

`RecoveredPlayerSnapshot`已明記22/24僅首次world-entry、在神仙綁定前送；24的HP-loss分支還會減神仙HP。不得直接把它當中途equip after-state投影。原生consumer給的是「如何寫入」；沒有提供普通裝備→最終角色屬性的formula、上限、狀態疊加順序。

## 可實裝最小scope及驗收門檻

若本輪整合要前進，優先單一普通武器slot34、已保存owned完整instance、bag↔34與既有裝備交換，拒絕battle／其他owner／revision不符／unknown item／37..49／容量不足。這個scope能把request、owner/CAS、20byte instance移動、持久化與relogin做實；目的格選擇與交換政策需保持明確來源標籤。

然而要標記「普通穿裝可玩」仍需：

1. 原client真實雙擊／拖放分別產28，server只操作所屬兩格；equip、swap、unequip、滿bag拒絕、重登後instance一致。
2. 追完整3B refresh及resource-bound icon，確認pending和後續操作，不能只停在copy以前。
3. 確認該武器對本人／他人世界外觀的更新；沒有合格外觀映射時不可謊稱已更新。
4. 屬性只能採已有權威after-state或另行驗證規則，不能直接把源表文字加到22而聲稱原生公式。無該證據時清楚報告裝備資料操作已接、戰鬥效果未完成。

本輪新增oracle只覆蓋producer與神仙guard；完整equip UI／外觀／屬性鏈尚未執行，研究至此停止。
