# 台服 PvE 完整身分／外觀投影來源複查（pass8）

日期：2026-10-21。基底：`6411c59413a110963d83ce687e46283979f8878b`。
本文件是 SOURCE_STATIC 複查，不是編譯、測試、封包解碼執行、遊戲或原生體感驗收。
本 lane 補普通 player 文字輸出安全資格與公開 Projection carrier 的先拒絕檢查；後者不冒充已證實的實際 Host 漏洞。

## 實際來源與資格

`OwnedPveApplicationSource` 持有 `shared_ptr<const OwnedPveWorldCatalog>`。
實際 scene 來自同一 catalog 的 `scene(area, scene)`；投影 closure 同時保留該
catalog 與其 scene 指標。現有實際 host 沒有替換 catalog 的 reload 入口，不能把
schema 描述中的版本規則當成已實作的 runtime reload／切換驗收。

資料庫 loader 一次載入完整 JSON、檢查重複 key／深度／數字形式，建構完整候選，
再比對版本與來源欄位。這份 catalog 是明示 `CUSTOM-0161` 的完整人工設定來源，
不是從原生 root 或名字自動產生所有封包。缺完整 source 時拒絕入戰。

Catalog 角色鍵是完整 character ID。實際 member source 另核目前私有 INIT、root40、
2A 的不變材料、原 movement binding 與完整存檔。2A 比對只正規化已證實的 actor
handle、map 與座標位元，其餘 kind／appearance／opaque bits 仍須相同。

主要角色的 `profiles()` 使用目前 member 的 live assignment，核 role 最大值、
resources 與 canonical Battle actor 的 owner／HP／MP／最大值一致，再只寫已知
level／HP／MP 欄位。`act` 和 `act_ai` 已在投影前呼叫 `updated_resources`；不能把
`publish` 裡較晚的同名呼叫誤判為 action 必然拿舊 resources 投影。

Pet1／Pet2 profile 由 active44 的完整 family、20-byte metadata、完整 stats 與
source SHA 選唯一候選。一般匹配只正規化當前 HP／MP；明示的
`owned_saved_vitals_level_v1` 才額外正規化／投影 level 與最大值。Pet2 packed 欄位
的高七個 opaque bits 仍保留。重複或 strict／projected domain 重疊會拒絕整份版本。

`pet_profile(character, saved)` 本身是純材料選型 API，不授存檔／Session 權限。
實際入戰在 Room repository 的 `validate_member` 核 saved pet 的完整 account／
character、active44、raw metadata／stats／revision／provenance；`structure`
再核 assignment 與 canonical actor controller。故不能把純 carrier 可人工構造
成其他 owner，說成已能從實際 Host 取得另一人的寵物。

## 投影與逐人返回

Projection 取 actual assignment 的 primary／pet 位置，資格主要角色與次要角色的
variant／native actor identity、實際 maximum，並以實際 checkpoint 更新 current
HP／MP／death bit。其餘完整 identity、appearance 與 vital opaque bytes 保留。
新成員取得完整 roster；原成員 admission 只補新成員，不重播舊角色 renderer。

Withdrawn／Returned／Retired 的顯示集合與返回來源分開。撤退的 combat tombstone
不能當成保存死亡；其本人 bulk 使用退出前已保存的 resources。完整保存由同一
Room repository transaction 與 claim/current cut 負責，純 Projection 不 mint 權限。

`return_world` 核實際 room committed resources、B4／E8 full root、完整 active44
tuple，並對照 retained world movement／handoff。E3／FB 以已提交的原始完整 stats
刷新現有格，沒有重播 S30 或重新製作任意 metadata。實際返回還包含個人完整
Return outbox Written、私有 Session successor、完整 material continuation 等來源。

## 原生證據邊界

沿用已關閉的 REA 證據及
`tw-native-identity-appearance-producer-followup-20261021.md`：World2A／DA 與
battle86/4 雖有四組 packed components 的同形資料，但 world mounted／Drv 特例
與 battle resolver 不同。現無一般 root40／equipped-slot 到完整 battle appearance
producer，不能跨舊 pin 直接借用或用零補 opaque 欄位。

S1C WORD7 的 metadata 解析具有 flag／ordinal alias，saved key 相同不證明相同
definition 或變身 lineage。完整 identity/status/unknown tail 仍需明示原生材料。
S1C 文字到 renderer 與 world6F 側欄快取是不同來源，不宣稱可互相代換。
本輪原生 lane 的新證據確認 ordinary player wire9..24／25..40 經 descriptor
送到 `5097D0`／`509E70` 的無界 strlen／copy(length+1)。`52CCD0` 實際 caller
以 descriptor+0E／+1E 傳入。`player_texts_terminated()` 純 accessor 統一檢查
兩欄各16-byte內有 NUL；Catalog 保留原本整份候選早拒，Projection 的已資格普通
primary branch 亦在任何輸出返回前先拒。Raw parser 仍接受並原樣保留未終止材料；
沒有補零／截斷，也不把這個伺服器安全限制說成原版 decoder 本來會拒絕或官方字數規則。
敵方 wire9..40 參數與 pet32-byte名字不套這個 player accessor。Pet 另有已證實的32-byte字串掃描資格。

引用 `native-material/identity-text-and-morph-definition-pass8-v1.json`
（`ev_fa1ff51044aca047c7cb471b3ca3304d974a1b7a924018b0be7421e45361c6fc`）、
同根 `assembly-primary-text-unbounded-copy-pass8-v2.json`／
`assembly-secondary-text-unbounded-copy-pass8-v2.json`，以及 pass7
`assembly-pet-species-word-pass7-v4.json` 的 `52D19A→52D1A1`／
`52D1AD→52D1B4` callers。分析映像為現用 aaf0 台服目標的明示 seeded analysis
映像，不能把該分析映像 SHA 說成原版 EXE SHA。

Pet 的同等 public API 旁路亦有 native 證據：`515C90` 在 `5164E0` 資格 secondary
variant 後，以 `5164F6` 取得 wire+9，`516503` 做無界 SCASB，隨後複製。故另以
`pet_text_terminated()` 檢查其自己32-byte來源，Catalog 與 Projection qualified
pet 共用；不把 player 兩欄規則套到 pet。證據沿 pass7
`assembly-identity-complete-pass7-v3.json`，不擴成敵方名字限制。

## 複查結果與未執行限制

原 Catalog 已限制 player 文字候選；純 Projection API 可接收另造 RecipientProfile，
故新增同一已證實普通 player 文字安全資格，避免這個實際公開 source API 繞過候選
建構檢查。Pet 亦有獨立32-byte資格；敵方位置必須保持 Catalog 原有的0x400／無appearance／無MP profile，不能用敵方位置繞過primary或pet文字資格。另 `roster` 在解參考 pet assignment 前驗 saved-pet 存在性與 actual
assignment 一致；不一致兩方向及越界都回 `ProfileRequired`，不再對空 optional
解參考。沒有寵物的合法 reserved partner 仍接受。Repository 的 actual Host 本來
已有相同結構資格；本次未宣稱玩家能從該 Host 送入這個 malformed carrier。
根代理本輪另修實際 normal-world source／visibility full-owner 問題，應以各自
候選 SHA 與獨立 review 收據為準，本文件不先宣告其完成。

既有 `test_owned_pve_world_catalog.cpp` 含 strict／projected variant、opaque bit、
source drift、family／key、overlap、primary full resources、DWORD 邊界等 SOURCE
案例；本輪另補直接 Projection 的兩文字欄各缺 NUL、最後一格 NUL 合法、敵方 opaque
參數不套 player限制，以及 pet／assignment 兩向不一致、越界、合法空 partner 的
SOURCE 案例，並涵蓋pet32-byte缺NUL／末位NUL、enemy錯variant／多餘appearance或MP拒絕。所有案例仍未執行。完整 current-client host fixture、
原生身分／外觀 producer、先手與回合規則及 runtime reload 均不能由本次只讀審查
宣稱完成。沒有執行 build、test、game、VM、codec、遊戲 SQL、schema 或部署。

## Native battle ring 的單次來源算界

本輪 round lane 新證據：`519370` 對 1C／38／83..88 按原 record 長度追加到
`CWar` ring，89 追加後停止該次 drain；82 不走這個 append case。constructor
`510E84` 以 `0x1400` 配置 ring，`51D300`／`51D4E0` 證實是5120 bytes；追加
失敗仍 consume network record，不能指望重試。引用本輪
`native-round/battle-resource-constructor-base-widths-pass8-v8.json`、
`incoming-battle-queue-writer-widths-pass8-v3.json`。這不是單一 network frame cap。

目前固定 template／唯一 slot／唯一 hit 的來源界如下，保守連不入 ring 的82也算入：

| 一次投影／有界同操作 | 每位接收者最多 bytes | 來源界 |
| --- | ---: | --- |
| Entry／新 Admission | 2374 | 28 actors×(45 identity+17 HP)，14×17 MP，最多14×17 appearance，另9 entry+121 bulk+17 grant+15 support |
| 原成員 Admission | 313 | 最多2新actors×96（含所有友方欄位的保守高估）+121 bulk |
| Action／Terminal | 1091 | 最多28唯一targets×(15 attack+17 absolute HP)，另17 source MP+121 bulk+57 terminal；非terminal grant17較小 |
| Support | 153 | 15 control+121 bulk+17 grant |
| Pass／新輪 Grant | 138 | 121 bulk+17 grant |
| RowSwap／完成 | 136／17 | 15 result+121 bulk，完成只grant |
| Withdrawal | 151 | 最多2×15 removal+121 bulk |
| 同次全員 cleanup | 2114 | 最多14名各一次Withdrawal，14×151，並非任意合併所有回合 |

以上皆低於5120；因此沒有把完整 frame／aggregate 上限改成5120，也沒有新增
任意拒絕正常路由的截斷。Writer 自己依原生 `0xA00` logical frame 邊界分完整
record；network 分 frame 也不證明 renderer 已消費 ring。逐人 Return 的普通世界
刷新有自己的 actual C1C／Written cohort，不冒充戰鬥 ring 清空 ACK。

此算界只涵蓋一次投影及上述有界 cleanup，不證明跨 callback、跨回合未消費的
ring 總積壓低於5120。Session Written 是 socket 完整寫入，不能當成 ring 讀完或
動畫完成。未新增不存在的 native ACK；原生 renderer／inbound queue 跨回合契約
仍以 native lane 研究文件及後續實際驗收為準。
