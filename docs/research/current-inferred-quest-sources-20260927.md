# 果力村收集任務：可實作來源包（2026-09-27）

## 交付與界線

建議先接 **234「果力名產」**：廚師梁禎收取蝸牛肉 `5098 × 5`。這條只有一位 NPC 與一種材料；當前來源提供名稱、描述、數量、對話，歷史社群頁提供等級與獎勵。接受、扣物、完成收據與防重送須登記為明確 CUSTOM 設計。此交付提供主線實作輸入，**沒有宣稱已整合或已通過真客戶端任務驗收**。

- 生成器：`tools/strike_lab/current_inferred_quest_sources_20260927.py`
- 資料包：`artifacts/research/inferred-quest-sources-20260927/source-bundle.json`
- schema：`god2-inferred-guoli-quest-source-bundle-v1`
- normal / `-O` 輸出完全相同，SHA256：`ab3e063564d0e7b351c3abab9e3475419c3a710ec9371b3de4d9b01f44a76541`
- 現用 EXE：`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`

生成器驗證現用 EXE、四個 CSVZ 及各解碼內容的完整 SHA256；各引用行保留 CP950 raw hex、行號、行 hash 與文字。沒有寫入 DB 或客戶端。

## 可接的四個任務

所有 NPC 的場景為當前 gamedata 唯一名稱「果力村」，`area=13, scene=12, kind=0`，資產 `North002/Cityjiu02/Cityjiu02.mdt`。表內 NPC ID 是 NPCAppearData catalog key，**不是已證實的世界 instance ID**；座標來自 Mission_data 文字，面向仍未知。

| journal ID / 名稱 | NPC catalog / 名稱 | 當前文字 xy | 材料 key × 數量 | Mission_data 行 | offer / incomplete / completion |
|---|---|---|---|---|---|
| 234 果力名產 | 2936 廚師梁禎 | 108,110 | 5098 蝸牛肉 ×5 | 1487–1488 | 8886 / 8887 / 8888 |
| 236 青梅竹馬 | 2937 李樂 | 113,69 | 5091 冬蟲夏草 ×5 | 1491–1492 | 8891 / 8892 / 8893 |
| 237 愛心便當 | 2938 阿銀嬸 | 69,72 | 5098 蝸牛肉 ×10 | 1493–1494 | 8901 / 8902 / 8903 |
| 238 禦寒衣物 | 2939 馬老伯 | 68,116 | 3464 兔皮 ×20 | 1495–1496 | 8896 / 8897 / 8898 |

對話 ID 屬 `NPCMission09`；資料包另外包含每條前後 idle 對話。這些角色標籤由對話語義配對，尚不是恢復的原服 state transition table。journal ID 則直接取 Mission_data definition 首欄。`(1 << 16) | mission_id` 是既有原生 journal selector 形式；何時設置、何時清除屬本次服務端政策。

### 原始欄位定位

- `gamedata` 行 1707–1710：四位 NPC 的完整名稱與 catalog row。
- 行 8074：`5098,10,Mis03098,41690,蝸牛肉,...`，MIS 來源。
- 行 8067：`5091,10,Mis03091,51074,冬蟲夏草,...`，MIS 來源。
- 行 6801：`3464,6,Mat03064,41064,兔皮,...`，MAT01 來源。
- `NPCMission09`：234 的五句在行 887–891；236 在 892–896；238 在 897–901；237 在 902–906。
- `NpcMission13` 行 974、text ID 12972 明寫：蝸牛肉／殼由果力村外果村蝸牛掉落，冬蟲夏草由村外大蝴蝶掉落。這是掉落來源文字，**不提供機率、擊殺條件或保證掉落規則**。本次沒有找到兔皮的相同精度掉落表。

未將 item row 的其他數字當獎勵，也未從 tooltip 補出原服任務判定。235 涉及另一 NPC 的取物鏈，本次刻意先選上述單 NPC 收集任務。

## 歷史外部交叉核對

[巴哈姆特 GOD2 8591 果力村頁](https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E6%9E%9C%E5%8A%9B%E6%9D%91) 的搜尋結果於 2026-09-27 提供下列數值；直接開啟頁面回 HTTP 403，因此沒有宣稱保存或 hash 完整外部頁面。

| 任務 | 歷史等級 | 歷史 EXP | 歷史名聲 |
|---|---:|---:|---:|
| 234 | 3 | 400 | 1 |
| 236 | 10 | 3000 | 1 |
| 237 | 5 | 1500 | 1 |
| 238 | 8 | 2000 | 1 |

材料與數量吻合当前文字；該頁馬老伯座標為 69,115，與當前來源 68,116 不同，採当前來源並保留差異。這些等級／獎勵是 **EXTERNAL_HISTORICAL_COMMUNITY_NOT_CURRENT_NATIVE**。沒有取得相關 17173 命中，不宣稱雙站核實。[果力島篇](https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E6%9E%9C%E5%8A%9B%E5%B3%B6%E7%AF%87) 的整體流程建議等級不應混作各任務接受門檻。

## 最小實作政策（CUSTOM-0051）

1. `not_started → accepted → completed`；每角色／任務唯一完成收據，先採一次性而不宣稱恢復原服 repeat policy。
2. 接受須本人、已發行 NPC 對話、合法場景／距離與空 journal 欄位。若採上述歷史等級，明確記為自訂採用；原服轉生與前置條件仍未知。
3. 完成須已接受且 NPC／階段／session revision 相符，從本人 bag 0..29 精確 item key 累計材料。扣物、EXP、名聲、journal 清除、完成收據在同一 transaction 原子提交。
4. 可採 slot 升冪扣除作為確定性的自訂規則；不碰其他 instance metadata、不把請求 raw word 解讀為任務 ID、不因刷新對話或重送 grant。
5. 已完成、物品不足、錯 NPC／owner、stale conversation、pending battle 一律無資產修改。發送成功文字及投影應對應已提交 after-state。

本 lane 已新增 `src/game/FruitVillageQuestRules.h`，以 `god2::FruitVillageQuestRules::rule(id)` 回傳 `optional<InferredQuestRules::Rule>`，`find(id)` / `descriptors` 提供唯讀描述；未知 ID 返回空值，不接受外部 Descriptor 來生成假原生規則。四條規則使用 CUSTOM-0051；當前 ID、item、quantity 為 NativeVerified，歷史 minimum／EXP／名聲及 maximum255、once、consume、scalar match、無 prerequisite、無貨幣／物品獎勵、collect-only 完整性承諾皆為 CustomInferred。Descriptor 的文字座標與對話 ID 不建立 NPC、不補面向。

`tests/test_fruit_village_quest_rules.cpp` 以四組實際來源數字驗證規則、欄位 provenance、未知 ID／未知 evidence 拒絕，並執行接受、跨 slot 精確扣除、剩餘數量、獎勵、防重送、材料不足與最低等級判定。MSVC C++20 normal 及 `/O2 /DNDEBUG` **各 PASS 94 checks**，命令與輸出在 artifact `build-test.cmd` / `cpp-tests.log`。這是 pure rules 測試；主線另負責 DB transaction、runtime route、CUSTOM 登記與真客戶端驗收。Python bundle 保留原交付時的 `design_id:null`／待採政策，來源包 hash 因此不變；C++ 是主線指派 CUSTOM-0051 後的具體政策。

尚需主線固定的政策：世界 instance／面向、交互距離、等級／轉生資格、EXP overflow／升級接法、取消與重複行為，以及實際材料獲取機率。面向未知不可默認為「原生 0」。僅 seed 材料完成測試不能證明材料獲取的遊玩循環已完成。

## 驗證交接

主線至少驗證：接受後原生 journal 正確顯示234；不足4個拒絕且 DB 不變；5個跨兩slot原子扣除；6個只扣5；並行重送只領一次；錯 NPC、其他owner、pending battle 與 stale revision 無修改；提交失敗全回滾；重登保留 accepted／completed 收據；完成後 inventory、journal、EXP／名聲投影與 DB 一致。最後需目前原版客戶端真正點擊接受、提交及重登，才能標記功能驗收完成。

### 已執行生成器驗證

```powershell
python -X utf8 -m tools.strike_lab.current_inferred_quest_sources_20260927 --output artifacts/research/inferred-quest-sources-20260927/source-bundle.json
python -X utf8 -O -m tools.strike_lab.current_inferred_quest_sources_20260927 --output artifacts/research/inferred-quest-sources-20260927/source-bundle-optimized.json
```

兩者成功，均輸出4條任務且第一候選234；完整來源 pin 通過。另已執行上述獨立 C++ rules 測試；未執行 runtime／DB migration／遊戲程式。
