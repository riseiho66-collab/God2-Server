# 同一 Application 世界物件、回呼生命週期與 TW83/08 原生欄位

本輪 `20261008-shared-world-host-context-source` 推進 M2 的正式來源 hosting，並補 M1 戰鬥 consumer 分支。三名代理分工交付十個 C++ 檔案的來源增量：新增四個來源檔、修改六個既有來源。所有改動仍屬 PHASE1；沒有建置、測試、原生或 C++／Lua 執行、資料庫／SQL 存取、部署或原生客戶端驗收。

## 共用世界的實際呼叫位置

新增 `SharedWorldHost`，由實際 Application 的 game 執行緒與同一份 `RecoveredCharacterRepository` 建立，僅建立一份 `SharedWorldPresence` 及使用這份 presence 的 `SharedActorVisibility`。存取必須在 owner 執行緒；repository、presence 與 visibility identity 一起核對。這不產生 native actor handle、位置、場景、權限、資料庫或任何成功回包。

新增 `SharedWorldHostPlan`。四個明確 `run_server` 入口涵蓋 TW、TW＋CN、TW＋網頁及 TW＋CN＋網頁。既有四個公開入口的 body 保留，普通 Main 仍未選用此計畫。明確 plan 要求真正的 `make_taiwan_entered` provider、實際帳號認證與完整 TW 連線組態，並在任何 listener 建構前拒絕不相容組態。

在 game scope 中，Application 以真正的角色 repository 建立一次 host，交給 mandatory provider 的 Context 同時帶實際 maps 與 game executor。真正的 Entered owner 由 provider 回傳，缺失拒絕，不填 true、假資料或只改 state 的回呼。character listener 的 handler descriptor 實際接入每條 Session 的 lifecycle factory；CN listener 的新增 constructor 同時接收同一個 host。

`SharedServerPlan::Context` 尾端新增 `common_world`，保留原 aggregate 順序。CN State 在 controllers 前宣告強 host owner，讓 controllers／connections 先釋放，再釋放 host；實際 `plan.controllers` 取得 exact pointer。舊 constructor 委派 null，不建立另一套 CN registry。這是提供同一物件的來源呼叫鏈；外部 CN world preparation／publisher 還必須真正選用該 host 的 exact presence／visibility pair，不能只拿同一 repository 或只比 presence 就當成全部已整合。

## 網路副本與 game owner 的資源釋放

靜態追查發現一條具體邊界：TcpServer template 與 Session 都持有 factory／hooks；`TcpServer::~TcpServer` 仍會 post 強 Impl，而 `Session::finish` 原本只消費 installed cleanup。若 Entered 強持 affine world owner，這些回呼副本可能在 game scope 之後才解構。單純在 listener 清 factory、只包 prepared／ready、改成 weak source，或刪除 destructor guard，都無法涵蓋完整來源生命週期。

本輪以 opt-in game-owned vault 持有真正 factory、每條 Session 的實際 hooks 與 installed cleanup，網路／Session 副本只持可撤銷 façade。Session 尾端新增 trusted cleanup-owner 接口，把真正 cleanup 轉成 façade 再安裝；只允許完整 factory opt-in，不影響舊 direct/default 路徑。正常 disconnect 仍先消費 cleanup，再走原 disconnect；scope guard 涵蓋正常結束及 provider／listener 啟動失敗，先關閉新呼叫，再於 game owner 清理實際回呼與強資源，最後 DB 才離開 scope。TcpServer 原有 stop body 保留。實際 guard、slot 與例外分支依代理精確位置與原檔副本保存；這是來源修補，未以 runtime 驗收證實。

另追到 factory 已建立 slot、但網路關閉先於 prepared 的分支：沒有 installed cleanup 的 slot 也必須釋放，否則會長期佔用 explicit max_sessions 容量。配對的 trusted abandon façade 在 game disconnect 的既有 cleanup 之後、原 disconnect 之前消費真正 session.id／pointer 所屬 slot；正常已清理則不重複消費。prepared／ready 的 identity 與重入檢查失敗，不得撤掉別的合法 slot；只有真正 hooks 開始後的 false／throw 才走該 slot 的清理。

## TW 戰鬥 action08 的 bounded consumer

新增 `RecoveredBattleAction08Control.h`，保存完整 raw15 bytes；只涵蓋原生 S2C83/action08、source BYTE 0..27。BYTE+3 為原始 operand，WORD+5/+7 為兩個原始 target mask；unsigned WORD+9 是 acting side0 的 manager+488 零／非零控制，side1 不寫此 flag，不能命名為傷害或 HP。BYTE+4 與 tail11..14 保持 opaque，mask 高位、空 mask、多目標或同側均不擅自 normalize／拒絕。

actor case `12C69F` 轉到 `12A8D0`，需真正 source／target actor 存在及 unsigned source WORD+1A<0x1000 等 setup 條件；共同 actor+1E7/+1E9 stores 後，08 setup 再寫 +1EB=88、+232=0。outer batch、actor kind、manager binding、lifetime 與 null 分支仍由真實 dispatcher 決定。正常 forward 強制 return1 不證明 setup 實際完成；source>=28 才有已保存的明確 zero return。視圖只描述條件分支，不模擬 actor writes，runtime emission／mutation 均為 false，沒有原生 issuer、C2S pairing 或遊戲權限新增。

證據使用 mapped image `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`；原始 input 真正在 before952 inventory 中，並保存完整 before/current observations、16 段 code、6 段 data 與 26 個精確 native sites。它與 unpacked PE 及已安裝字體還原版維持不同 epoch。舊 30 筆戰鬥 inventory 和165 annotation 原樣保留，本輪另加166 annotation；08 值原先已知，原生新值為 0。

## 本輪計數與剩餘來源

| 範圍 | 目前盤點 | 本輪完整路徑新增 |
|---|---:|---:|
| TW C2S 候選 opcode 值 | 156 | 0 |
| TW S2C 長度表支援值 | 252 | 0 |
| CN C2S 候選 opcode 值 | 156 | 0 |
| CN S2C 分階段 endpoint | 280（account6／world206／battle68） | 0 |
| TW83 action／86 selector inventory | 23／7 | 0 |

本輪新增一個 bounded raw field view、同一 world host 的實際 Application 呼叫鏈、TW factory hosting、CN Context 接線與 TW 回呼資源 owner。new opcode／native phase binding／完整雙向路徑仍均為 0。TW 世界 parser63 中已審查42個來源分支，66.7% 僅是該 parser 範圍，不能當全遊戲進度；既有 CN91／TW10 個未 hosting 的 phase bindings 不因新增 host 而改成完整路徑。全遊戲分母、完成數與完成百分比仍為 unknown／null。

仍缺真正 Taiwan Entered／scene／持久位置與 revision、完整 native entry／5D／逐收件者6F／5E／73，CN world preparation 對 exact pair 的實際選用，以及 native account issuer／rights／catalog／summary／Reservation／Main 選用。候選 frame 與 legacy CharacterSelected 不因新 host 而升格。64位共用數值的持久 schema／profile／實際 caller／TW-CN-web wire-object-display、stack99 全部 mutation caller，以及全遊戲狀態變體盤點仍繼續。

本輪使用 before952 全檔快照，保留並核對 prior165 root1259＋catalog553 全部1812個封存檔；本輪 agent 所有 stage、原始資料、副本、缺失 before 紀錄、靜態報表 raw/final 與新 catalog 均位於 `artifacts/integration/packet-connections-20261006/shared-world-host-context-source-01`。完整目標保持 active；全部來源串接後才集中測試、修復、恢復與可玩發布。

application-world-host 的初次 README 中文存檔出現編碼錯誤，已改存正確的英文說明。原始 README bytes、第一次 seal 及全部85個舊 members 的 preservation map 保留，最終 seal 包含這段 lineage；五個正式來源檔與30份 current origins 完全未因文件修正改動。不把這次文件修正算作程式或封包增量。
