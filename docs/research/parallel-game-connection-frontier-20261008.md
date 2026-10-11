# 三代理接線與共用原生快照儲存

本輪 `20261008-parallel-game-connection-frontier`，第一階段只改來源。上一個
委派回合屬於已確認的等待：三個代理都有當前執行中的工作句柄；本輪接收其
實際來源分析後，選定原生快照儲存缺口並分配不重疊的實作。修改前已保存
938 個當前來源，並現讀上一輪完整 1,737 個封存檔。未執行 C++、SQLite、
原生客戶端、服務端、Lua、建置、測試、驗收、遷移或部署。

## 三名代理的實際責任

| 代理 | 本輪來源修改 | 同時整理的缺口 |
|---|---|---|
| m2_source_hosting | 新增 `NativeDeliverySnapshotSchema.h/.cpp` | 登入、帳號、角色、世界的實際資料供應與正式入口 |
| receiver_frontier | `SqliteDatabase.h/.cpp` 的明確安裝／資格化入口 | TW/CN phase、state、variant 分母及正式世界 caller |
| title32_boundary | `main.cpp` 的明確 schema-only 選用 | 仙幣、EXP、HP、傷害、stack99 的儲存／計算／封包／畫面差距 |

## 本輪要補的真實來源鏈

帳號與角色快照的 reader、完整 CAS writer、CN supplied-input Plan 已存在，
但其三張共用表只有 DDL 宣告，沒有明確安裝 caller。單純增加 callback 或
宣稱有 writer，不能使缺表的實際儲存來源可用。本輪接入以下鏈路：

`main --migrate-only --native-delivery-schema` → 原有設定與共用 SQLite →
原有 base migrate → 明確 `install_native_delivery_snapshot_schema()` →
獨立版本 ledger、完整資格化與同交易建立三表 → 原有同 connection 的
帳號／角色 reader、writer。

共同三表為 `account_native_snapshots`、
`account_native_character_summaries`、`account_native_character_summary_rows`。
既有主鍵的 client SHA 欄位保存原生版本差異，不需重複 gameplay tables。
不變更原三表 DDL、base migration 1..53 或其歷史，不直接增加 migration54。
獨立 storage ledger 只記錄交付格式，不能代表實際帳號權限或原生資料。

資格化使用同一 `SqliteDatabase` 已配置的完整 migration vector，逐項比對
version／name／完整 SQL，前後保留原 applied_at，並以分開的記憶體 schema reference
取得父表與目標表的 metadata。此 reference 是未執行的 C++來源實作，
本輪沒有啟動 SQLite。目前來源明確限定已配置32..53的完整 prefix；
更改的父表 DDL 或其他 prefix 會拒絕，不能宣稱所有 schema 都可收編。
額外無關的表／index／trigger 保持原樣。未選取或複製 live credential／
gameplay row 值；FK 資格化可能掃描既有資料，不能說未讀任何 row。

缺表時只允許完整、同交易建立；部分存在、碰撞、修改的表／index／trigger
不能默默收編。完整既有 schema 必須符合相同契約才可重用。原有存檔與未知
物件保留，不以 DROP、ALTER、填預設值或修正資料完成資格化。
新命令僅與 `--migrate-only` 同用，拒絕任何明確 `--run-for`，包括0；
普通啟動與原有 migrate-only 未選新旗標時保持原路徑。

這是儲存來源串接，尚未執行安裝。未輸入 metadata40、billing16、角色75B07、
revision 或 origin；未製造 issuer／登入權限、選服目錄、角色 visibility 或
世界 Reservation；普通 main 仍未選用 CN native login factory。
不能把此命令、schema 資格化或 storage COMMIT 當作 native ACK、可玩登入或
全遊戲封包完成。

## 代理盤點改變的下一步

封包組指出：已有保存的 TW battle83 的23個 action 與86的7個 selector，
catalog 仍主要按 opcode 記錄。本輪已將這30個子分派記錄展成獨立 frontier，
各自保留原生 case、既有 scoped projection／caller 和未知 state／variant。
83僅01／03有既有 scalar source 資格，86僅0／1有既有 vitals source 資格；
17與03、6與0的 native case 相同，不能因此沿用其來源資格。
所有 C2S pairing／完整路徑仍 OPEN。使用歷史 mapped149c 原生證據，當前
font-restored99cd 安裝版仍為獨立基準，未重寫或重新冒稱原生驗收。
這些數量已存在於歷史報告，不能重新當作新 opcode。TW common world
lifecycle／movement 另缺 Application 的實際同 presence／WorldOwner caller。
CN D3 的 account source phase 已有證據，不得因 unphased endpoint 的缺口重複
計數。這些具體來源與行號保存在本輪 backend 代理收據中。

數值組確認：HP64／傷害64的共用 domain、Lua exact arithmetic 與補給服務
已有局部來源；現存持久化 CHECK、checkpoint profile、Application caller、
TW/CN native wire／object／floating text 與 web 顯示仍有不同缺口。
保留既有 diagnostic fixture 與 checked legacy projection，不能直接刪除
guard 就宣稱完成。stack99 domain 也尚不能代表全 mutation 已接通。
數值 matrix 與完整來源副本保存在本輪 CLI 代理收據。

接續優先：沿本輪 TW83／86 子分派補全 state／variant 分母；明確存檔保留與 recovery 的 wide schema
來源；接有實際 projector 與資源／metadata 權威的 numeric caller；追完實際
CN account／summary／world issuer 和正式選用。共用表仍為預設，只有證明
無法共用的儲存使用 `_tw`／`_cn` 後綴。

## 本輪封包與完成度

| 版本／方向 | 已盤點數字 | 本輪新增 |
|---|---:|---:|
| TW C2S | 156 個已識別 opcode；phase／variant 未閉合 | 0 |
| TW S2C 長度表 | 252（230 fixed、22 variable） | 0 |
| CN C2S | 156 個已識別 opcode；phase／variant 未閉合 | 0 |
| CN S2C phase entries | 280＝account6＋world206＋battle68 | 0 |
| catalog endpoint rows | 958；不能當完整玩法分母 | 0 |
| TW83／86 子分派 frontier 記錄 | 30（23 action＋7 selector） | 30筆展開；新原生值0 |
| 新完整雙向 gameplay routes | 0 | 0 |
| 全遊戲去重封包／完整路徑總數／完成百分比 | 未知，維持 null | — |

TW world parser63中的42個已做 scoped source review（66.7%），只是該分組
研究覆蓋。CN conditional receivers14、context12；CN/TW unhosted phase bindings
91／10，distinct opcode69／10；partial owner chains35／3。均不可當全遊戲
完成率或部署成果。本輪實際修改／新增5個 C++來源檔，沒有新增原生 opcode。

仙幣上限維持99,999,999,999；EXP、HP、傷害 gameplay cap 仍待另定。保留原生
等級、字體、CP950／CP936、繁簡轉換、帳號、存檔、聊天、IME、認證、頭像及
凍結功能。TW／CN／web 全遊戲目標仍 active，全部來源串接後才集中測試、
修復與可恢復發布。
