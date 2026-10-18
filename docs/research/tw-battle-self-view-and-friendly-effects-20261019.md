# 台服自身視角來源與友方效果（round472）

本輪把實際 Session 輸出的 primary86/5 接到 NativeDeltaLab、Service 與 Battle。
只有具備同一場次、同一完整 owner、完整 Written 來源的友方非自身 kind1 非零 selector，
才能忽略與該目標無關的 raw outcome。沒有來源時保留原有保守檢查。
這是本機輸出來源資格，不是遠端採納、回合權限或完整玩法驗收。

## 現用原始證據

God2.exe SHA256 為
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`；
453 筆 cbspec2.bin 保持
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整證據在
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/battle-self-view-round472/`。
`identity/battle-self-slot-consumer-v1.json` SHA256 為
`e71a3ab0d28130aa6d1f06eb9c7efcca36664cde915fc364286878989edafdc8`，
核對 8 個既有函數、2,985 筆原始指令，本輪沒有新增 REA session。

517590 的86/5分支讀 logical BYTE3 bit0 與 BYTE4 low4；5175D9 先寫 B+51，
5175DC 才檢查肖像 signed handle。這個 setter 不依賴 B+48、World R0 或 actor 編號配對。
本輪僅接受 slot0..13；14／15 不形成可用的友方自身來源。

5169F0 在 side 非0或 slot 不等於 B+51 時，於讀取 raw outcome 前返回。
kind1 非零 selector 的累計儲存路徑也不讀 raw14；因此友方非自身可解除該項無關限制。
自身 raw0／28 仍會設定／清除 bit0；其他值不能概括成不變，raw32 的 CL&31
亦會清除該 bit。這不構成任何出手／技能權限。

已知其他 writer 包括5112C0初始化 B+51=FF，以及515C90的1C身分／資源分支。
全域 alias、其他 phase 與遠端 queue 路由仍有未閉合部分。

## 實際 Session 輸出資格

接受的 game world_records callback 在遊戲執行緒產生完整最終 response；若當時是
台服角色模式、InBattle 且有完整非零 owner，Session 為該原始 response 建立私有
WorldResponseWrite source。已有顯式觀察來源時沿用原來源，不替換 observer、輸入 barrier
或 DB bootstrap 權限。公開 scalar、Policy、pose 或相同 bytes 的 generic sender 都不能造出資格。

中央 append_write 依完整 envelope／record 邊界判讀整筆 Write，不掃描 body 子字串。
1C／82 清除之前候選；同一完整 Write 最後的有效 primary86/5 可提供新 slot。
2A／CF、unsupported primary slot14／15 會使整筆 Write 不合格，後面的 grant 不能修復。
未知、截斷、checksum 錯誤等輸出亦撤銷舊資格；既有輸出 bytes 仍照原路處理。
secondary-only 通知不是 primary writer。已識別 record 沒有已知 writer，並不代表
已證明所有原生 phase 都無副作用。

新 writer 在入列時推進獨立、不回繞的 epoch 並撤銷舊 occurrence。
另以獨立 writer-intent epoch 覆蓋真正 output API 到 strand 的等待窗口：
相關通知在交接前便撤銷舊來源，原始 response 保留其當時的 intent ticket，
append、完整 Written 與 Current 都要求該 ticket 仍有效。較新 writer 尚未入列時，
較早的原始通知即使取得新 FIFO epoch 並完整寫出，也不能重新授予資格。
沒有把所有輸入 dispatch／actor-status work 一概視為自身位置 writer。
候選必須持有原始 response、同一 Session、完整64位元 account／character／battle generation、
exact whole frame 與 Pending 狀態。實際 async_write 完整完成且原 response 已 Written，
再核對相同 source、frame、epoch、場次與目前 occurrence，才成為 Written。
失敗、取消、重複或延遲 completion 都不能恢復已撤銷資格；epoch 耗盡時停止授予。

讀取時再核對原 game thread、world_ready、非 closing、完整 owner、InBattle、同一場次與
目前私有來源。任何實際 phase 變更都撤銷舊來源。generic grant 只使舊資格失效，不能 mint。
NativeBattlePending／PK held grant，以及不等於原始完整 response 的拆分／cohort 輸出，
目前也只會失效處理，沒有被擴大成新授予路徑。Written 不證明客戶端 B+51 或 R0 已採納。

## Core／Service 與實際呼叫點

Service 獨立保存真正 bind 當時的 battle generation，不借用 pose 或 bootstrap 欄位。
可選 Session::BattleSelfView 必須是目前相同 Session／owner／場次的來源，slot 存在於 roster，
並保留來源角色的 controller、存活、第一目標、每來源70筆、型別與原有權限限制。
primary self slot 與目前出手位置分開，不能為了視角而把戰寵控制位置硬改成自身位置。

Service 才能建立私有 Battle::NativeDeltaView，綁定 battle id／revision／controller／self slot。
Battle 同時在前置檢查與套用後檢查採用相同 outcome predicate；放寬僅限友方且非自身的
kind1 非零 selector。自身、selector0、selector20、kind2／3、Legacy 數值邊界與勝負判定不變。
Service 在編碼後及提交前再次核對來源；失效不發布 staged state 或 checkpoint。
仍要求既有的 serial game owner 與純、不重入的 encoder／持久化 callback 契約；
這不是任意並行 sender 與 commit 之間的全域線性化保證。

Application 的實際 NativeDeltaLab 呼叫取得 Session 唯讀來源並交給 Service。
缺少來源仍走原保守檢查；不是直接略過效果處理。現有 Lab hosted roster 僅0／14，
三角色友方非自身案例由實際 Session／Service 合成 fixture 覆蓋於測試原始碼，
並未因此新增 hosted 戰寵／怪物或完整玩法。

## 回歸原始碼與未完成項目

純 helper 測例涵蓋 epoch、一次性 Written、失敗／取消／延遲 completion、完整多 frame 排序、
body 同值、invalid slot、2A／CF hard poison 與截斷。實際 socket fixture 經選角、tail、
normal world 與真正 game callback，檢查完整64位元 owner、其他 Session、generic 重送、
後續1C、phase／場次失效及編碼後失效回滾；另寫友方非自身 raw0／28／255 的一致效果、
自身／selector／kind／source 保守拒絕、混合批次原子性與 RNG checkpoint 不變斷言。
編碼期間真正呼叫 send_world_records(primary1) 的案例，要求尚未 pump strand 即拒絕，
並驗證零提交；之後排出的新通知與後續原始 callback 可依序刷新來源。
socket fixture 沒有強制製造延遲 completion；該時序目前由純 occurrence 案例與來源審查覆蓋。
這些案例是未執行的回歸來源，不是測試通過或客戶端驗收。

獨立靜態審查、唯一正式盤點、來源／容量／publication 收據外存。
PHASE1 未建置、執行測試、native、VM、codec、遊戲 DB SQL、schema、遷移、啟用或部署。
技能傷害／治療、命中／閃避／暴擊、攻防／五行與持續 tick 的原始生成公式仍需真正來源。
完整玩法新增0，全遊戲分母／百分比 unknown/null，goal active。
