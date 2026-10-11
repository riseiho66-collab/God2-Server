# CN 刪除回覆先暫存、後提交的來源接線

第154輪，PHASE1；僅修改與閱讀原始碼。未建置、測試、執行原生程式、存取資料庫或部署。

第153輪的刪除來源已能選擇完整帳號摘要失效，但實際 `send_batch` 在刪除 COMMIT 後才配置傳輸 completion、編碼原生封包與檢查容量。本輪將完整原生02的傳輸準備提前：原生 Decision／SummaryDecision → ReplyHeld → 現有 transport publication barrier 暫存所有已編碼 bytes → game executor 重新核對同一操作 → 同步共用刪除 transaction → BeforeQueue → release → AfterQueue。原生19／02內容與位寬未改；沒有新增猜測的封包或成功回覆。

`SharedCredentialConnection::send_world_batch_with_commit` 是明確允許實際交易提交的獨立入口，保留既有 observing publication 接口語義。它捕捉同一 verified account／world session，前後檢查 admitted／實際 world ticket。舊 observing wrapper 中 account 為 uint32、session 為 uint64 的同一 `auto` 宣告拆開，僅修正來源型別問題。

傳輸層 `CnTransportSession::send_batch_with_publication` 原始碼未改。它先建立 PendingSend、game work guard、bounded pending quota、原生編碼、完整 output 副本及 frame／byte 容量檢查，再設置 strand 持有的 barrier，最後才排入 game 提交 continuation。`write_next` 在 held frame 停止；既有前置 write 可完成，後續普通 send 不能超越 held frame。256 frames／1MiB 是現有操作界限，並非原生遊戲規則。

`commit_held_reply` 在 strand/game 非同步邊界後重新檢查 ReplyHeld、未提交、同一 retained Decision／SummaryDecision mode、完整選定 common row、原 offered identity、Scope／Attempt 與 selection。實際共用 writer 仍於同一交易核對完整舊摘要／all roots，保留 BeforeErase／BeforeCommit 的實際 native Current 與摘要 Current。局部 `[this,&current]` 只在此同步提交函式及其交易內使用，不跨越非同步邊界。預期摘要的 owned 副本在刪除 SQL 之前建立。

選定摘要來源失敗不退回 legacy；非零 native02 不讀取／準備摘要，也不刪除資料，只暫存並經原 Current 放行原始完整回覆。未選摘要的既有刪除交易仍走原共用 writer。新增 BeforeQueue 前後 phase 檢查；AfterQueue 原操作／存檔／佔用／identity／Current 檢查保留。傳輸仍只報本地 queue acceptance，不代表 native 客戶端已收到或接受。

本輪只處理傳輸準備的先後順序。刪除 COMMIT 後仍有可失敗的 strand post、async_write、completion post、關閉及實際 issuer Current／storage 讀取；失敗關閉不能回復已提交的刪除。Durable reply receipt、語義重播、斷線恢復及1E continuation仍 OPEN。若共用 coordinator 在 COMMIT 後 invariant apply 發生例外，既有 committed_ 記錄限制也未由本輪解決。不可宣稱 DB／網路已成為原子交易。

實際 native issuer、完整資料／schema、來源 factory／Main 與正式 hosting 仍未設定。TW／CN／PC／web 的完整遊戲、共用64位數值及 stack99 仍持續接線。子代理精確前沿為 WORLD68 的4501BF→407D70 nested owner，及 WORLD32 selected-row 的 allocator／目的容量。這些研究與本輪 conditional source 都不新增封包／phase／owner chain／完整雙向路徑；完整遊戲分母、完成數與百分比均未知。

三位子代理已完成本輪。WORLD68 補到實際 nested ECX=`DWORD[GUIroot+8]`、operation／slot／selector WORD，以及兩條無 child call 的有條件暫存器保留分支；其餘 child call／上游 mandatory helper 仍 OPEN，下一精確點407E16→409C00。WORLD32 補到實際 world+1478084→person+90→UI+430A8、owner+D8+index*3EC→selected+D0 的來源鏈。標題來源在 row+13，另一獨立 WORD 在 row+28；差21只表示到已知欄位的距離，未證實 declared 字串容量。整記錄搬移／清除還要求追蹤 selected-row revision。selector4／firstNUL／42CA20 caller及450B80 helper仍 OPEN。來源審查保存修改前及當前副本，沒有明確新增型別／生命週期／fallback／CAS 錯誤；沒有執行建置或測試。
