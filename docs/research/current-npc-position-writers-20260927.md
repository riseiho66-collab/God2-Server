# 當前 EXE：NPC 位置 writer 與本地來源補查

2026-09-27；有界只讀稽核。先讀 `native-npc-placement-audit-20260926.md` 與 `native-npc-source-inventory-followup-20260926.md`。未用退役 Classic/XJZ、未修改客戶端、DB、Application 或 Ghidra 專案，未啟動遊戲或操作桌面。

## 結果

**新增可授權的完整原服 NPC placement：0。** 本輪確實補到先前反編譯索引漏掉的原生座標 setter `004CCEC0`，以及本地建立入口 `00467CD0`。兩者都不是 area/scene/NPC/x/y/facing 配置表：前者消費 caller 的座標參數；後者建立滑鼠位置標記，唯一已知 caller 使用 selector `FFFF`。

這比只重讀 S2C72 多覆蓋了本地生成、逐格移動、追趕校正、初始化和未辨識程式缺口；**不宣稱整個客戶端不存在另一條未知間接路徑。** 既有約 84.97% 函式覆蓋不足以支持那種全域結論。

## 可重跑證據

```powershell
python -X utf8 -B -m tools.strike_lab.current_npc_position_writers_20260927 `
  --output artifacts/research/npc-position-writers-20260927/new-run
```

約 8 秒。輸出限制在所指定目錄。執行既有 Ghidra 專案時明確使用 `-readOnly -noanalysis`，並先比對 saved program SHA；沒有重新 seeding、analysis 或 publication。既有輸出可用 `--reuse-export` 重驗本機 PE bytes 與 native vectors。

本輪正式證據目錄：`artifacts/research/npc-position-writers-20260927/qualified/`。

- `instructions.tsv`：51 個已辨識子系統函式的真實指令邊界。
- `references.tsv`：145 個 saved-analysis incoming references。
- `reference-context.tsv`：每個 reference 前最多 20 條原生指令。
- `pool-instruction-references.tsv`：全已分析指令中的 54 個 pool displacement 引用。
- `additional-native-instructions.tsv`：12 段原索引未包含的 machine code；不把鄰接 jump table 當指令。
- `evidence.json`：所有 range hash/raw offset、raw call candidates、未辨識範圍、15 個本地 builder vectors、3 個未辨識 setter vectors。

7,007 個輸出 instruction rows（含重複 context）均逐 byte 與現用 PE 及 pinned mapped image 相同。現用檔 SHA256：

`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`

mapped image SHA256：

`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`

重要掃描修正：此解殼 PE 原 `.text` section flags 是 `C0000040`，並沒有 `IMAGE_SCN_MEM_EXECUTE`。本工具明確掃原 `.text` 加其他 executable sections；僅按 executable bit 掃描會漏掉整個原生遊戲碼。

## 兩個相同結構、不同用途的 pool

設 world object 為 W：

| 容器 | 當前原生 owner |
| --- | --- |
| NPC／本地標記 | `N = W + 1539AED8` |
| 怪物／玩家跟隨寵物 | `M = W + 153B8758` |

兩者均由同一組 `CPMonster` 方法處理，最多 256 records，每筆 `1D8` bytes，record=`owner+70+index*1D8`。不能因函式名稱或相同 record 結構把怪物／跟隨寵物當成世界 NPC 配置。

| record offset | 本輪確證用途 |
| --- | --- |
| `+00` DWORD | 查找／occupancy identity；空槽 `FFFFFFFF` |
| `+08` WORD | 當前方向編號 |
| `+10/+14` DWORD | 當前 tile x/y |
| `+18/+1C` float | 投影後畫面座標；不是新的地圖座標來源 |
| `+24..+30` | 移動步數、畫面增量與下一方向 |
| `+34` 起 | 40-entry 移動佇列及其 cursor |
| `+180/+184/+188/+18C` DWORD | 最近來源／目的座標快照 |

area/scene 不在此 record 的已證位置欄位。0x72 consumer 消費當前 world 場景 context；單筆 72 的座標不自帶完整 area/scene provenance。

## 已查 writer 與來源

| writer VA | 寫入／來源 | 已知 incoming chain；是否 placement 來源 |
| --- | --- | --- |
| `4CA680` | 256×`1D8` records 全清零，再設定空 identity、無效 renderer handles | world initializer `464910`，calls `4654B2/4654D5`，分別初始化 N/M；清零不是生成 NPC |
| `4CC380` | 普通 NPC `+08,+10,+14` 及位置快照 | `468AE0` case72 call `46AA89`；另本地 `467CD0` call `467D57` |
| `4CBD70` | 組合外觀 NPC 同樣方向與座標欄位 | case72 calls `46A87A/46A9C0`；選用 NPCAppearData flags `+10&8000`，位置仍來自 received record |
| `4CCA50` | 從 payload DWORD+16 解目的 x/y，交給移動校正器 | **opcode60** call `46AAB4`，owner=N。非 NPC 初始配置 |
| `4CD8D0` | 若 record 與 caller 的起點相差超過 1 tile，覆寫 `+10/+14`；依路徑產生器 `45FD80` 填佇列 | `4CCA50` 與 `4CCB10`；來源仍是移動記錄的起終點 |
| `4CA800/4CAAC0` | 取移動佇列下一格寫 `+10/+14`，並把方向 `+30` 複製到 `+08` | 只有 update loop `4CAD10`；該 loop 由 world frame `466B00` 分別對 N/M 呼叫 |
| `4CD3E0` | 依目前與下一格 delta，寫移動欄位 `+30` 方向及投影增量 | 只有 `4CA800/4CAAC0`；不讀 NPC 世界配置 |
| **`4CCEC0`（新補）** | `record+10/+14` 寫 caller 的兩個 **signed WORD**，再更新投影位置 | 未發現 raw direct E8 或 absolute pointer 指向此 entry；不能斷言從未經運算／間接呼叫。此 setter 本身沒有表讀取或場景鍵 |
| `4CB120/4CB720` | 怪物／跟隨寵物的方向、tile、快照 | case71 `46A5B3/46A536` 及跟隨寵物 `46C6A0` 的 `46CB87/46CB66`；owner=M，不是 N |
| `4CCB10/4CCC00` | 移動起終點快照與佇列 | 前者 **opcode5F**；後者由 `46CC00` 封裝跟隨寵物更新；owner=M |

補充：`4CACD0` 逐 frame 累加的是 record `+18/+1C`；`4CA760` 做畫面平移；`4CA7B0/4CDB10/4CDAA0` 更新 renderer。這些不構成新的 tile placement 來源。`4CA730/4CCE10` 移除現有物件，清 identity/handles；它們不查 spawn 表。

Opcode 身分以原生 jump table `46B5D4+4*opcode` 確認，沒有按 callee 鄰近位置推定：`5F→46A677`、`60→46AAAA`、`72→46A68B`。`74` 是 monster remove；`75` 是 NPC remove；`76` 在此 switch 為 default。完整證據含 `world_dispatch_entries`。

### 0x72 原生輸入的位置來源仍相同

含 opcode 的 logical21：

```text
selector = DWORD(logical+1)             // low WORD 同時用於此 pool 的查找 identity
facing   = BYTE(logical+9) >> 5
packed   = DWORD(logical+17)
x        = (packed >> 2) & 7FFF
y        = packed >> 17
```

高 WORD 的 catalog fallback／組合外觀選擇不提供 x/y。兩個外觀分支都從同一服務端 payload 讀方向與座標。沒有在新分支找到原生預設城鎮座標表。

## 新發現 1：本地入口是位置標記，不能拿來生成全部 NPC

`467CD0(kind,x,y)` 在 stack 組出 20-byte record，再呼 `4CC380`：

```text
selector.low = (-(kind & FF) - 1) & FFFF
opaque DWORDs 1..3 = 0
packed = ((x & 7FFF) | ((y & FFFF) << 15)) << 2  // DWORD 截斷
facing = 0
```

唯一已知 incoming call `4675C9` 屬 `466B00`：明確 `kind=0`，x/y 經 `4493C0` 將輸入／畫面座標轉換到地圖，再加當前 viewport offsets。後續不再需要標記時由 `467D70(0)` 移除相同 selector。**這是 caller 當下指定位置的 `FFFF` 標記，沒有一列原服 NPC 的固定座標。**

資源 selector `58A58C` raw bytes=`09 01`，`461010(0)` 將兩 bytes 交 `461580` lookup；`kind!=0` 回 `FFFF`。其兩 bytes 是外觀資源鍵，不能解作 area9/scene1。

原生 builder 15 vectors PASS，包括 x/y 0、1/2、126/127、32767、65535，kind 0/1/255。只執行 `467CD0..467D33`，在首個 resource lookup call **之前**停止，沒有替換任何 game callee，也不宣稱完成 renderer。

## 新發現 2：未反編譯的座標 setter

`4CCEC0..4CCF74` 是完整 machine code（`ret 0C`），先用 signed slot 計算 record，再於 `4CCEE6/4CCEE9` 寫 x/y。三個 native vectors 執行至 `4CCF6B` renderer call 前：

| slot | caller x/y WORD | 寫入 DWORD x/y |
| ---: | --- | --- |
| 0 | 126/127 | 126/127 |
| 255 | 32767/0 | 32767/0 |
| 3 | FFFF/8000 | -1/-32768 |

函式無 slot bounds guard，不能直接視為可用 server codec。其來源完全是 caller 參數，不含 area/scene、NPC selector table 或 loader。

| 程式區間（end exclusive） | PE raw offset | SHA256 |
| --- | --- | --- |
| `467CD0..467D65` | `672D0` | `59a6beb0acf71fe984c4a19ac34b79c4fb906341ec3793c025ae6f75af4c7592` |
| `4CA680..4CA715` | `C9C80` | `17dcaf76e595777831c5cb7f468a5f08ead335364d43327e5b47052d37273232` |
| `4CC380..4CC83D` | `CB980` | `5cb026bb204b4db7003f00af951940bf6ec21dbf6d4acc807d2d50329e8c16fd` |
| `4CBD70..4CC32C` | `CB370` | `a3c816f0ff12570a075b0ba2cd3eb15f14fd99aae11583d546bf35b4fc44a3e6` |
| `4CCEC0..4CCF75` | `CC4C0` | `6c3a2d74bcdd0cc4c4d7287a909c2bc75b2836cc51753bf59fecbb260612b769` |

## 其他未辨識缺口與常數表

本輪補讀 `4CD0E0`（狀態判斷）、`4CD130`（按距離／level篩選既有物件）、`4CD200`（字串名單查找）、`4CD270`（對既有物件求路徑距離）、`4CD6A0`（相鄰格 delta→方向行）、`4CD860/4CD8A0`（移動佇列讀取）、`4CD960`（queue cursor 計算）。這些沒有寫新的 NPC 世界位置配置。

`4CD660..4CD69F` 是 `4CD3E0` 的 switch target table；不能用線性反組譯得到的假 `add [mem]` 當位置 writer。後面的真正函式從 `4CD6A0` 開始。

`571250` 的 8×16-byte 常數表供移動 delta／投影方向使用，SHA=`ed0ba9ab0572ce94baff654784534ec52285200cc0c3a9c0b7a32363197089d4`，PE raw=`170850`。表中沒有 area/scene/NPC 身分欄位。本輪保留全部 128 bytes，不將方向表當 NPC 配置。

## 覆蓋界線與下一步

1. Raw `.text`/executable E8 掃描對本輪已辨識與新補 entries 找到 149 candidates；其中四個先前索引外 calls（`4CCF6B`,`4CD0E8`,`4CD866`,`4CD8A6`）已沿完整機器碼補查，另新缺口內 `4CD307→4CD200`。`4CCEC0` entry 沒有 raw E8 caller，整個 mapped image 亦沒有 literal pointer，但運算得出的／間接入口仍未全域證明。
2. Raw pool-range DWORD pattern 有 62 hits；其中 54 個落在 Ghidra 真實 instruction operand，清單完整保留。其餘是重疊 opcode/data 候選，沒有把 pattern 本身當 writer。已知 operand 中皆是兩個容器基址的 LEA/ADD，沒有新的直接 `world+NPCslot+position` 固定常數寫入。
3. 不能靠這次 `.text` direct-call census 排除 register-derived pointers、interior entry、computed calls，或現有未分析的其他程式段。完整未辨識範圍仍保留在 evidence；未修改 canonical Ghidra function set。
4. 若繼續技術追查，具體下一個可檢查的邊界是：`4CCEC0` 的間接／interior-entry可達性，以及 world owner `464910/46BCC0` 與未知 loader 對 N record pointer 的跨函式別名。現有本地標記／移動常數已查明，不宜再當新 placement 候選重複搜尋。
5. 可直接接線的完整原服 placement 仍缺 `area,scene,instance/catalog selection,x,y,facing` 共同來源。此輪沒有提供猜測值，也不將原生 consumer 所能接受的任意 x/y 當作原服輸入值。

至此停止本輪有界稽核。
