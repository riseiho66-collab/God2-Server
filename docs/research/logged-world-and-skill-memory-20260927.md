# 登入後全量場景／技能／戰鬥程式碼記憶體擷取

## 實際擷取

工具：`tools/strike_lab/current_logged_world_memory_20260927.py`。
成功收據：`artifacts/research/logged-world-memory-20260927-04/memory-result.json`，SHA256 `da478422303599c09ba8bdb7033267a911e65036ebbbdd1384f9f919d5bb09cb`。

在 God2Lab 隱藏桌面，以獨立複本資料庫與 loopback2598 測試服，透過既有隔離登入測試流程进入崑崙仙界4/3。使用 `OpenProcess(0x1010)` 與 `ReadProcessMemory`，沒有注入、寫程序記憶體、截圖或切換使用者桌面。所啟動的客戶端、測試服及 runner 均已關閉，來源檔案核對未變。

| 實讀範圍 | 結果 |
|---|---|
| 當前場景 NPC pool | 完整256×472 bytes；occupied0 |
| 當前場景 monster/follower pool | 完整256×472 bytes；occupied0 |
| 靜態 NPC catalog | 全4043筆，全部來源欄位吻合；4043筆可變尾段非零數0 |
| EnyName arena | 全7815筆及96組descriptor吻合 |
| map catalog | 全144筆來源selector、packed geometry及layer dimensions吻合 |
| cbspec2 skill source | 全448筆110-byte記錄吻合，完整112656-byte載入body亦吻合 |
| 當前 `.text` 記憶體 | 全1503232 bytes實讀並保存，7段戰鬥／技能已資格碼與目前正式EXE一致 |

**512個完整槽是當前一個場景，不是144張地圖各自的世界實例。** 本次測試服啟用 native-only 位置規則且沒有合格原始spawns；空池只能說當次沒有收到NPC／怪物出現資料，不能說原遊戲地圖沒有NPC／怪物。NPC尾段零值也不能升格為原生零攻防。

## 修復的定位問題

第一輪 `logged-world-memory-20260927-01` 全heap字串掃描超出既定800MiB界線，未放大限制後當作成功。改為依兩個已登入世界指標定位 C，直接驗證全部quest/catalog記錄。

第二輪預設 `W+A7E0444` 技能位置未吻合來源，沒有匯入錯值。第三／四輪改以角色 root+4504 公布的實際技能指標，完整source匹配且指標唯一。世界W與技能manager是不同記憶體物件，不能把它們的相同offset當成同一owner。

第四輪另擷取全`.text`。與正式EXE共45個byte不同：一byte是已資格lab2598埠差異，其餘44byte位於四個 input API thunks（keybd_event、mouse_event、PostMessageA/W）。相對精確lab映像的全部改變都限制在這些wrapper的已記錄範圍；未把它們當傷害公式。7個戰鬥／技能範圍逐byte一致。

## 全技能接入正式服務端

找到正式 `native_skill_catalog` 原本是空的，修正這個來源接入缺口。

- 部署：`artifacts/releases/native-skill-memory-20260927-01`。
- 工具：`tools/operations/native_skill_memory_release_20260927.py`，實際RAM收據驗證、SQLitebackup、隔離匯入、全表比較、C++逐筆讀回、停止自有服務／重啟、失敗rollback。
- 正式匯入448筆及其完整來源metadata。bank計數121/129/87/111。
- 現有 `Application` 的 `native_skill_catalog` C++→Lua callable現在可查到完整原始記錄及已驗證client MP threshold。
- 新read-only C++工具 `native-skill-memory-reader` 逐筆核對448個ID、全部110-byte原值和WORD+42 MP門檻，並檢查各bank尾端不存在額外來源ID。
- 正式玩家表全部不變；沒有技能學習／所有權grant；client、config及執行中的server EXE未變。服務端重新接聽2592，verify時PID26992。

這是技能原始資料及既有source lookup的接入，**不是448個技能的完整戰鬥實裝，也不是MP收費時機或傷害公式驗收**。

## 全記憶體程式碼欄位候選

工具 `tools/strike_lab/current_live_formula_readers_20260927.py` 以實際`.text`、實際448記錄與正式全量NPC／EnyName／skill資料表核對，不寫資料庫。normal與`-O`執行均通過。

線性解碼507527條指令，保留1142個技能numeric offset相交的讀取候選；297 bytes跳過。每筆保留實際指令bytes、地址、source function候選和alias未資格標記。這不是1142個公式，也不是整個控制流的完整恢復。

例如battle區+46候選中，有多筆其實是+44的DWORD pointer讀取。`512E90`讀的是param_1+44指向的目標清單；`518E50`讀的是battle manager+44狀態。offset相交不能證明讀了110-byte skill definition+46，不能將其60低byte命名為60%機率。

## 驗證

CTest `native_skill_catalog`、`native_skill_lua`、`import_native_skills`、`current_damage_formula`、`current_hit_formula`、`current_critical_formula`、`current_skill_mp_gate`、`current_skill_mp_sync`：8/8通過。

初次import CTest中14個case有1個因舊native-skill-catalog測試執行檔未建置而失敗；補建該既有target後整組重跑通過，沒有繞過測試。formula命名的測試驗證既有bounded consumer／result arithmetic，不代表原始攻防結算已找回。

## 尚未完成與下一個來源界線

這輪新增合格原生NPC／怪物出生實例0，新增原始服務端攻防／命中／暴擊公式0。

實際code的83/03與83/0D路徑讀取received amount/result；HP/MP套用器做符號延伸、32-bit累加／clamp。它們沒有證明amount/result的產生公式。119E30中的投影乘法仍缺原始K值producer、stat binding及權威writeback；單看乘法或技能文字不能填補。

繼續追查必須針對實际非零資料producer、收到的原始71/72/F8與83資料及間接caller owner；我們的測試服回填值必須維持OUR_SERVER來源，不能循環當成原服原生資料。全原生內容驗收尚未完成，整體工程完成度仍約11%（估計）。
