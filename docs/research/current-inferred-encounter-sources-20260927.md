# 可用的原文地域／怪物／收集目標約束：2026-09-27

## 本輪可落地結果

最小候選是 **截仙遺址的大灰狐 → 狐皮收集目標**。本輪取得四組當前原文與確切顯示 lookup 的交叉證據，並提供可重跑、逐列留 hash 的 JSON。這些證據能約束「某地域可選哪些怪物外觀、文字說要收集什麼」，不再只是 consumer 接受任意座標的負面結論。

本輪只新增獨立工具／研究輸出；沒有改共用 runtime、DB、客戶端，沒有啟動遊戲。**尚未實裝遇敵或任務**。原始 monster stats、觸發條件與獎勵仍缺；若主線接入最小功能，這些欄位必須另有明示推定／CUSTOM policy，不能將文字提示冒充完整原服規則。

## 精確候選與命名空間

| 候選 | 原文場景 → native map `(area,scene,kind)` | EnyName 顯示鍵 `(area,scene,ordinal)` | 材料／收購書 | 原文目標 |
|---|---|---|---|---|
| **大灰狐** | 截仙遺址 `(3,0,1)` | `(3,0,1)` | MAT01 **3456 狐皮**；MIS **4408 收購書** | Mission_data **69/描述4**：30 狐皮 |
| 巨水蛭 | 截仙遺址 `(3,0,1)` | `(3,0,6)` | MAT01 **3505 巨水蛭的尾巴** | NPCMission **5965** 明說活動區域／材料來源；本輪不指派 quest |
| 食土蚤 | 風吼黑洞 `(3,2,3)` | `(3,2,1)` | MAT01 **3462 蟲殼**；MIS **4412 收購書** | Mission_data **69/描述8**：30 蟲殼 |
| 大毛虫 | 天絕黑洞 `(4,12,3)` | `(4,12,2)` | MAT01 **3408 毛虫怪的卵**；MIS **4411 收購書** | Mission_data **69/描述9**：30 毛虫怪的卵 |

`kind` 是 map catalog 原始欄位，不是先前口述的 kind0。NPCMission、NPCNormal 的文字 ID、Mission_data 的 journal ID／描述索引、item key、EnyName ordinal、世界 instance ID 全部分開保存。表中的 EnyName tuple **不是** recovered server monster-template ID 或世界 instance ID。

僅接受 area>0、lookup-visible、同 map area/scene 且 CP950 名稱 bytes 完全相符的唯一 row。其他同名 lookup（含 area0 跟隨寵／戰寵命名空間）全部留在 JSON 的 `same_name_visible_records`，不自動選用。巨水蛭另有 `(3,1,3)`、`(8,11,22)`；大毛虫另有 `(8,5,3)`，地域原文使本表能排除這些同名候選。

## 可驗證的原始文字

### 明列場景與生物的清單

`NPCMission03.csvZ` 實體行958、text ID **2956**，row SHA256：
`38b0e5b3e3b2249bcdaaac2dd97026988f279961c05195fec1b9360b6f1eef9f`

```text
2956,鴻濛境-樹妖，雲鶴。\n截仙遺址-大灰狐，大黃蜂，蚌精，火焰蟹，綠蜻蜓，巨水蛭。\n金光黑洞-金魅，負刀半妖，火甲兵。\n化血黑洞-幽魂，幻法師。\n紅沙黑洞-石猴，火蜻蜓，紅鷹。
```

`NPCMission03.csvZ` 行959、text ID **2957**，row SHA256：
`30e51624bfa23fae9a242435043fd120c40f5eb39b895407a7ee622d9019060c`

```text
2957,落魂黑洞-腐木骷髏，化骨僵屍，攝魂鬼。\n風吼黑洞-食土蚤，藍犀獸，綠水蛭。\n參天林-樹妖，紅頂鶴，紅花蝶，樹精，鐵樹精。\n寒冰黑洞-水蚌精，銀霜武士，鯨龍。\n天絕黑洞-小蘑菇，大毛虫，拂塵草。
```

這是直接的地域—生物原文，不是把同一行無關姓名做笛卡兒積。工具只保留人工選定且 exact-map join 成功的四組，不將整行每個怪物都套到每個場景。

### 最小大灰狐目標的交叉證據

`Mission_data.csvZ` 行443 是 `69,[城鎮任務]楓華商人,9`；行447：

```text
,,4,你要找的是３０個狐皮，這些你可以在截仙遺址的大灰狐身上找到！
```

行447 row SHA256：
`24e82258331bb3df7dba97cd32aa7fc266528a066475e00625ecc043fdd29392`。

`NPCNormal01.csvZ` 行999、text ID **997**：

```text
997,你要找的是/c3３０個狐皮/c9，這些你可以在/c3截仙遺址的大灰狐/c9身上找到，一切就麻煩你啦！
```

row SHA256：`8a4b092b251d226c4b0a707148b55e645177bc3be529110839bc738af92fafe1`。

gamedata 行6793 的 MAT01 item3456 名稱為「狐皮」，說明「敵人掉落物之一。」；行7386 的 MIS4408 名稱「收購書」，說明「上面寫著３０個狐皮」。兩列 row SHA256 分別：

- `767ab31642f97517d832d67ad86c3eba7a9867b1b6daf8cdc73e201ee4d3810f`
- `c8e561ef2c60253c9015044087dcdcc22d2812045c0e909b8b26f04c3e131d63`

這強化了收集目標的語義一致性。**69/描述4 → 997 → item4408 的事件 join 尚屬推定**；不能只因文字相同就認定任務已接受、書必定發給玩家、或交回後自動推進下一個描述。

### 巨水蛭的第二份地域來源

`NPCMission06.csvZ` 行967、text ID5965，完整原文存 JSON，關鍵句精確為：

```text
像這巨水蛭的尾巴當然是從巨水蛭身上獲得，而牠的活動區域就在截仙遺址那邊。
```

row SHA256：`e2e58cecb9bb90e3387bd0275602f35b38eb451a5485aaaaf71b2c5d88f88b2c`。

`NpcMission13.csvZ` 行144、text ID12142 又列「名稱：巨水蛭，地點：截仙遺址」。該列的 **21–30級是玩家可捕捉兌換的等級條件文字，不能當怪物等級**。row SHA256：`dec1bd9bd5051bd6a82aa74e902f76bb54f8a26f07bee6fd1ea2034b6dbacfaf`。

## Map／display source anchor

全部以下 records 來自同一 current gamedata.csvZ：

- compressed SHA256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`
- decoded SHA256 `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`

截仙遺址 map catalog 行21084，raw row SHA256：
`5dd4e734ce94fc91b200a26b2fd4fe08328ff57be70c22bf6028b1e92df7763c`。
原始 kind1、area3、scene0，asset `Island02/Island02.mdt`。其735/483等catalog尺寸／座標欄位沒有被轉成出生點。

EnyName 大灰狐行21784、ordinal1，record SHA256（含原始行結尾）：
`ab1a79390d20486fae6615e47f04362b566ed74e834f1dcdc787551456ab7a2b`。
巨水蛭行21789、ordinal6：
`b2f9dbf9fbe141381df41bc8d03e1850f3329d42a93e89e76b7d8a233340e57e`。
JSON 保留原始 bytes、map 全欄位及另外兩個場景的對應列。

## 現有伺服器：哪些可以重用，哪些不能直接啟用

此處是 fresh source review，沒有沿用舊報告中的欄位誤標。

| 元件 | 目前能力與限制 |
|---|---|
| `src/game/Battle.h` `BattleActor` | 可信 server 供給 position/controller、HP/maxHP、MP/maxMP、物攻、法攻、物防、法防。沒有由 EnyName 自算 stats。 |
| `Battle` / `CombatRuleInput` | 可處理已授權 actors、revision、targets 與顯式規則的交易；屬 CUSTOM0006/0007，不是 recovered damage formula。 |
| `RecoveredBattleService::bind` | server 在進戰後綁定 session/account/character、Battle、Policy、encoder、checkpoint commit。C2S 不可直接授權這個 bind。 |
| `RecoveredBattleIdentity` | 已有 S2C1C **45-byte** codec；normal variant0400 的 ordinal/area/scene可用本文 tuple，displayed level、identity word、其餘 raw bytes仍需明確政策／qualified template。 |
| `RecoveredBattleEntry`, bootstrap/vitals | 有82進戰、1C身份、86資源及ready序列構造能力；batch policy原已明標CUSTOM0005，候選新場景仍需實際client驗收。 |
| `reserve_battle` / checkpoints | 已有 owner/resource revision檢查、pending reservation及原子checkpoint/settlement，能作工程基底。 |
| 現有 repo gate | `load_checkpoint`、`commit_checkpoint`硬限 `CUSTOM-0012/diagnostic-v1`；資源／reservation design亦限CUSTOM0012。不是泛用原生ownedbattle API。 |
| `Application.cpp` 現有新戰入口 | 約2040行後仍是diagnostic gate；town fixture要求area2/scene15、18/12、town stage3、地圖5569且未settled。不是截仙遺址原生遭遇條件。 |

`Application.cpp` 目前 enemy fixture 明確是：

```cpp
{14,0,150,150,0,0,20,25,13,6}
// position, controller, hp,max_hp,mp,max_mp,
// physical_attack,magical_attack,physical_defense,magical_defense
```

這些只是CUSTOM測試數值。20/25/13/6不是可套給大灰狐的原生值；最後兩項也不是舊報告曾誤寫的speed／其他scalar。現有診斷外觀仍是別處的三碑鴨，不能把這份數值與新地域生物名稱結合後改稱native。

`native_monster_placements_only` 目前會壓制該diagnostic encounter。不能為了用本文資料就默默移除此保護；新的推定路由應有自己的明示origin／policy，保留既有checkpoint歷史的policy標識。

## 最小推定功能建議（供主線實裝，這裡未改runtime）

1. 先做單一 **截仙遺址、大灰狐的顯式挑戰**：玩家必須已在已保存的area3/scene0，使用已證實的UI request途徑表示挑戰意圖；不自動傳送、不在猜測座標生成NPC、不用走路亂數觸發。全場景作admission filter是新CUSTOM政策，不是已恢復的原生region polygon。
2. 使用來源確切的 `(3,0,1)` 外觀與名稱；server另給獨立world/battle instance identity，不能把ordinal當instance。HP/MP、雙攻雙防、級別、技能、遭遇編成及開場opaque/context須由一份明示推定profile提供。
3. 以現有Battle/RecoveredBattleService及原子checkpoint骨架接線，但需新增/允許該profile的policy ID，並在來源、角色、pending battle與resources admission成功後才發82與bootstrap。不要覆寫既有diagnostic checkpoint為新policy。
4. 若做收集目標，可讓介面顯示「30狐皮」且追蹤已擁有MAT01:3456；掉率、每次掉落量、收購書授予、接受事件、回報NPC、移除材料、獎勵與完成旗標均是獨立未解規則。沒有這些交易以前，不將查詢到30件當作完成原生quest69。

上述最小方案消除了隨機出生座標與遇敵率需求，保留原文確實支持的地域／物種／材料約束。但它仍是**有原文約束的推定玩法**，不是完整原服任務復原。數值平衡及實際client acceptance是主線新增政策的必要驗收；本輪沒有選定新怪物stats、drop rate或reward。

## 工具與驗證

```powershell
& 'C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe' `
  -m tools.strike_lab.current_inferred_encounter_sources_20260927
& 'C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe' -O `
  -m tools.strike_lab.current_inferred_encounter_sources_20260927
```

兩次皆成功：4 candidates、7個sourcefiles；輸出 `artifacts/research/inferred-encounter-sources-20260927/evidence.json`。文字各來源packed/decoded hash固定；引文strict CP950，name join以raw CP950 bytes比較；item key限定MAT01/MIS section，避免同數字NPCAppearData碰撞。非引用的invalid-name bytes不以replacement混入join。

Text/item row hash以去CR/LF的完整原始列計算；EnyName parser原有record hash包含其原始行結尾，兩種邊界均在JSON保留rawbytes。伺服器檔案SHA与關鍵行號一併存入 `server_code_readonly`，方便辨識後續主線改動。

本輪完成後停止；無執行中工具或private client。
