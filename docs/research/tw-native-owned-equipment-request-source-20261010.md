# 第233輪：台服實際 C28 請求接入共用物品選取來源

本輪新增實際 Session 原始批次→私有 C28 occurrence→混合分派→完整共用物品選取→必要實際 Action 的來源接點。新增一段部分來源鏈；完整雙向玩法新增0，台服全遊戲分母及完成百分比仍未知。沒有建置、測試、執行客戶端、封包 codec、資料庫、SQL、遷移或部署。

Session 僅在實際已認證、已接受世界尾段、持有共用 ready 身分的 game callback 中，於任何玩法 callback 前保存完整批次內每個 C28 的原始 Request 位址與 owned logical5。一次 take 只接受該原始位址；複製 Request 不能取用。私有 receipt 的所有複本共享同一次 take／dispatch 狀態，必要 Action 前先 claim；重複 claim 將當前 window 失效。RAII 在同步 handler 返回或異常退出時退休整個 window。綁定實際 Session、帳號、角色、ready 身分物件、批次序號、原始 record index、phase 與 battle generation；序號不溢位重用。

這是服務端內部一次 occurrence 的來源連結。它不是原生 wire nonce、二進位來源證明、客戶端 ACK、玩法權限或語意重送防護。相同5 bytes在另一批次仍是新 occurrence；真正裝備／使用重送必須依完整物品狀態、規則與整筆 CAS 處理。receipt API 與 game-owned 欄位相同，只能在序列 game callback 使用，不宣稱能隔離任意跨執行緒或惡意 C++ provider。

WorldRecordSource 僅在安裝完整 SelectionBinding 時，把原始 C28 分成逐筆 singleton run；移動及其餘最大連續段仍依原順序處理。C28 在聊天 composer 複製 Others records 前直接從原 span 取 receipt，失敗不能 fallback 到另一套 Others。Application 由實際 Binding 傳遞明確 opt-in；預設 false 保留既有分派及凍結功能。累積原生加密回包保持 run 順序及原有 frame／byte budget；必要 Current 仍觀察完整原始批次和實際前進 prefix。

OwnedItemRequestSource 強持有實際同一 presence 的 OwnedItemSelectionSource；後者用231共用 custody 儲存與完整版本化 alias，以 key／source slot 找完整 instance，不從 raw20 推 common ID。必須 supplied 完整 handle／release／invalidate，沒有猜測裝卸動作、空成功或預設回覆。Action 前核對完整舊 Selection.current；Action 後只核對 receipt、實際 ready lease、位置及 battle generation，不把已合法提交的新 inventory 和舊 Selection 比較而誤拒。Action 自己必須採232整筆 custody＋native snapshot 交易與真實規則／next issuer／durable receipt，並供應完整有序原生回覆或有依據的明確 no_reply。

重入／拒絕／異常傳遞實際 Action invalidation；真實 release 即使另一子清理異常仍執行。借用 Context 不被保留。HostPlan 的 with_owned_item_requests 只在實際同一 Application Context 建來源，拒絕重複安裝；不選 Main、不讀寫啟動資料庫、不授予任何物品。現有 chat、spectator、CN、web、數值及存檔來源保留。

presence 的 ready lease／saved position 讀取經實際 repository observers，故其前後均核對完整本地 receipt／Session phase／身分／battle generation 與 reentry fence；observer 捕捉已拒絕的重入後回傳有效資料，也不能讓 Action 繼續。混合來源 invalidation 有遞迴防護，每個子 callback 的複製也在各自異常處理內，避免一次配置失敗略過其餘清理。

相同 fence 也接入外層 WorldRecordSource 的 ready／stored／snapshot：repository observer 後重讀本地 phase／battle／ready 身分、精確 slot 物件與 live 狀態，防止 BeforeRun 的 observer 已 terminalize 外層後仍進入下一個 C28 Action。既有 Current 的純觀察與 game-only 合同不變，不宣稱隔離任意 provider 自行改寫同一資料庫。

原生依據維持149c SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。共享 producer VA496550 的第三參數低 BYTE 經4965D0／4965E9進 wire，並非 producer hardcode1。現有 logical5 decoder 僅支援已觀察 caller 的 flag1 subset，行為不改；flag1也有卸裝，不能當 equip boolean、數量或目的格。舊6bf EGG／SPP／WPN／EQU／TWP／TEQ執行探針保留為歷史，不能當149c驗收；本輪只修正 header 的來源說明。

仍未接通：真實 definition／取得物品權威、C28 action／目的裝備格／Lua裝卸條件與結算、full item→native1200/cache／DA15 producer、完整背包／裝備回覆、來源自己本地更新／混版 fanout、實際正式 Main suppliers。完整2A、once-issued admission、其餘台服 gameplay 與全路徑分母仍須持續追查。Conditional Action 插槽、私有 receipt、解析器、拒絕分支及資料庫技術交易均不計完整遊戲路徑。
