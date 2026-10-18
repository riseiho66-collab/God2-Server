# 台版全地圖與 NPC 傳送串接

使用者要求所有可傳送地點與 NPC 對話傳送，並指定內部黑箱驗證；另確認只有目前客戶端及服務端檔案，沒有原版服務端事件設定。本文件記錄後續全世界工作；先前 98 條同圖與 48 條碧遊宮／洞穴連線仍保留，不把舊範圍當成全遊戲完成。

## 導航與固定路線：CUSTOM-0155

產品為 `resources/world/tw/world-transfer-v1/catalog.json`，核心載入整份 SHA256 及各 grid SHA256，Lua 接受核心提供的固定 route ID；實際移動提交後，C++ 再核對該 ID、來源位置、owner、revision、ready 與 pending 狀態。傳送只 ACK 走入入口的合法前綴，捨棄舊場景尾步；所有新增路線使用 full-reset SC61，抵達 receipt 後重新發布已有的場景資料，存檔重登保留完整 area/scene/kind。

原 CAN 有 613 個 SceneKeys、303 個 canonical asset names。現有資源可建立 **587 個場景、287 個共用導航資源**：142 份室外 MDL、145 份室內 HMD。26 個 selector 的原資源缺失，沒有用其他 parent 的同名檔代替。16 筆 MapInfo 舊拼字／路徑差異依原數字 area/scene/kind 與實際 CAN canonical path 固定連接，沒有更改客戶端 CAN。

室外 32,701 個窗口、14,421,141 格均經現有 C++ 投影與獨立離線解析逐窗及整張 mask 比對。144 個一般室內資源亦逐格一致。官府 OFFICE 的例外不是整間房損壞：原 overlay model15 的 Pass 為 0×2，台版 REA 436C30 的 width 迴圈直接略過，只有原解析器誤拒。以該原檔 SHA 限定的解析後，Office 37×37 導航亦由 C++ 與獨立解析核對相同，未全域放寬原解析規則。

導航每格保存原觀測集合：mask0 未知、1 為原00、2 為原01、4 為原02；3/5/6/7 代表多種觀測。預設僅 2/4 可走；195 個逐筆釘選 marker 允許 mask6，各來源觀測只有01/02。含00、未知與其餘衝突不允許。不是全域把01與02等同，也沒有把動態佔位當成靜態地形。

363 個 HMD placement 先保留既有26個楓華鎮及6個崑崙綁定，其餘在相同 area、canonical path、decoded SHA 的 CAN aliases 之間，依原 placement record SHA 固定分配；82 個未使用 alias 仍明列。三份已補公布欄 MDL 的 door record 依完整原 record SHA 與 marker 重定位，避免新增模型引起的 offset 位移；非空導航 material 已逐項核對。

同 MDL 使用互反 record 的相同 marker slot。跨 MDL 與 HMD 的啟動／落點為已授權的固定服務端政策，**不是已恢復官方服務端程式**。原 auxiliary 已知 blocked 或缺失時，只可採同一固定 target record 的原 matching primary 且導航合格；不取最近格、不跨 model 猜落點。每條保留原 record、marker、hash、被排除候選及選定理由，舊280條 tuple 全部保留。

最終產品共 **2,399 條移動傳送方向**，SHA256 `0146feeb50d96a99ca5a494900b652b010532295f6f64e4da8addfbb22561c53`。最後補齊6條 HMD 返回，363組固定室內綁定現均有進出。其中 gold.hmd（1/92）與 towertop（7/3）原 base 根本沒有 exit marker，明列自訂防受困規則：人物先走離原 arrival 格，再重新踏回該原 marker，傳至同一固定原附加 record 的戶外 primary。抵達時 stationary/no-op 不會觸發；這不是恢復了不存在的原出口。其餘4條 sh03_r 使用現存原 indoor auxiliary 到原 outdoor primary。六條來源 mask2、目標 mask4，均有合格接近／離開格、沒有 source 多目的地衝突。

`source-index.json` 列全部613 nodes、1619個原參照及363組 HMD 綁定。未啟用 slot、缺 marker、缺原檔與無唯一 anchor 分開列出；它們不是同數量的實際遊戲故障，也不是全遊戲完成率的分母。NPC、事件與任務產生的傳送另計。

最終2,399條路線的端點涵蓋465個 SceneKeys。其餘122個已具導航的 selector 沒有合格步行路線端點，包含82個未綁定室內 alias，以及40個室外／事件場景（例如監獄、部分幫派／陣法場景、Gem全區與umg）。導航可載入及可重登不代表原事件入口已串接；這些不是新的已完成傳送。原1619參照中1434筆有合格 source walking route，185筆未取得資格；參照或未啟用 marker slot 的數量不可直接當成實際遊戲故障數。完整清單與分類保留於 source-index 及外部 `world-catalog-reachability-review-v1.json`。

## NPC 傳送：CUSTOM-0156

已連接 `OwnedNpcTeleportOffer` 的來源與狀態邊界：實際 NPC 發布身份、owner、完整場景／位置／world generation、NPC generation、定義及條件 readset，與已發出 menu／允許 choices／期限／私有 token。原生37→7A→85與6D→99/A9分開處理；移動、戰鬥、場景改變、關閉、過期與失效來源會撤銷 offer。選擇後還要重新核對完整 private Prepared 與資料來源，不能直接接受客戶端目的地。

85/99 的原生 WORD correlation 可循環使用，99避開原保留 contexts；A9固定 context 允許完成後再次開啟，不以一次使用或65,536次總量把正常遊戲永久鎖住。每次開啟使用新的 private64 token，舊 Prepared 不能消耗新 offer。原生 wire 沒有額外 nonce，在合法新 offer 期間收到與新選項完全相同的舊 payload，協定本身無法分辨；不宣稱已做到不可能的 wire replay 識別。

費用符合不代表已付款。只有有獨立來源證明的 ExplicitNoCost 可以走 position-only transaction；收費／道具／任務型傳送須有真正的條件供應者與費用＋位置聯合交易，不能當成免費傳送。原生86讀取 UI pointer 指向值的低WORD；尚未證明是自身 actor ID，因此只有獨立供應者已證明的 close source 才認領，不用舊誤解猜身份。

目前台版資料已檢查 73 份 CSV、14,600 NPCMission、2,031 NPCNormal、4,043 外觀資料、654 個傳送文字命中／46 個 MultiMessage 候選。文字可看出城鎮、洞穴、神廟、任務前置、通行證、等級與5000／6000／7000費用；**不能建立完整「NPC實例→選項→目的地→任務／費用」連接**。message ID／外觀 ID 不等於 NPC instance ID。私有現有 DB 的 verified opcode114 NPC rows 為0；退役地區的舊 atlas 不能充當台服來源。

因此實際 NPC travel definitions 為0，正向 NPC 遊戲傳送仍未完成；核心會明確記錄 SOURCE_GAP，不發出假的 NPC、零填的7A或未知條件的免費旅行。原版服務端缺失資料不會因拒絕 handler 或單元測試存在就變成已完成玩法。

## 集中驗證與發布

`world-build-v3.log` Release 建置通過。`world-baseline-ctest-v1.log` 的 diagnostic_door、wilderness_transfers、cross_map_transfers、recovered_parent_route 四套回歸，以及 `world-new-ctest-v1.log` 的 world_transfers、owned_npc_teleport_offer 兩套測試全部通過。世界測試實際準備587個場景及提交2399條路線，涵蓋owner／stale revision／pending／full reset／還原及錯誤kind；NPC測試包含85/99各65540次正常循環、A9重開及舊Prepared拒絕，屬合成供應者測試，不代表已有真實NPC定義。

正式 static packet report round452 已單次完成，不重跑；它早於本次世界串接，不能作為後續全量驗證證據。

測試重用 `artifacts/playtests/map-transfer-repair-20261018` 的既有隔離快照。合成人物透過實際 TCP 建立，只有該新人物正常斷線後才設定離線位置 fixture；測試腳本不開啟正式 DB。C++／Lua 是服務端執行期，新增離線 Python helper 僅在外部證據目錄，先 AST、單次執行，失敗版本不覆寫。

全量實際 Application TCP `qa-tcp-world-v8.json` 通過 **2399/2399條方向、587/587個場景冷登入／ready**，耗時1483.172秒。每條驗入口prefix ACK與invalid tail丟棄、精確SC61 selector/kind/X/Y及bit16清除、持久化revision、owned receipt、落點no-op不反彈、斷線後重新登入位置與ready。2376條另外完成普通相鄰格走動；其餘23個落點的全部可走鄰格都是其他入口，原測試明列未做普通走開，沒有把缺少的觀察當成通過。

另以 `qa-tcp-world-continuation-v1.json` 專測這23條未涵蓋的抵達後位移，全部通過實際下一步連鎖傳送、第二次精確full SC61、receipt/no-op及重登。23例都是原固定路線定義預期的連鎖結果。沒有重跑整份2399清單，也沒有修改核心／放寬檢查。

主TCP報告SHA256 `cf9d7568cec844a78fa93ca33eabddf1f4781832d9a26fc4529224e322eb933a`；23例補測報告SHA256 `f7be435f567890f7b18f937d283c5df29d3daa8aaf65e77b367c417f5f126d0f`。NPC正向傳送測試數為0，whole-game completeness仍false。

18:05切換正式核心，SHA256 `3f41ace75a28db2bbf96ca8e68eed51ab8bd70b35027bb2a29c36f3ec49b752e`，PID42212，登入2592／角色54103。切換前正式與QA均無Established連線；正式設定只新增world_transfers，原資料庫路徑與其他development功能設定保留，未執行部署SQL／schema安裝。新服務端兩個listener的原19-byte起始握手都與現有golden fixture相同；隔離QA服務端已停止。

`artifacts/releases/map-transfer-repair-20261018/deployment.json` 是現用收據。`tools/operations/start_local_server.ps1` 改為讀該收據的EXE／設定，限定專案內路徑並核對EXE SHA，避免下次重啟退回舊town核心；既有排程設定沒有修改。原部署與設定各留一份小型外部基準，沒有複製玩家資料庫或建立完整安裝備份。

使用者指定內部黑箱，因此未宣稱這批587場景與所有路線已逐個完成原版 GUI 驗收。先前原版 area2 一組同圖往返、抵達後走動及使用者神廟／客棧進出確認，仍只代表那些已觀察範圍。

外部證據根目錄：`C:/Users/risei/.codex/artifact-archives/god2-server/20261018/board-object-rea/door-repair`。包含來源索引、HMD fixed bindings、Office REA／byte provenance、逐格比對與產品安裝 SHA 收據；完整 TCP 報告在上一層。

切換後保留現用world-release與上一個cross-release回退基準；已確認無執行中程式及現用來源依賴的五個更舊EXE共25,934,336B，移至桌面「要刪除清理/God2-map-transfer-build-intermediates-20261018」。加上先前中間圖資，本輪相關待手動刪除共71,878,677B；C槽內搬移實際回收 **0B**。最終專案邏輯檔案長度19,716,634,789B，低於30,000,000,000B。此數值不是實體磁碟回收量，沒有移動玩家DB、來源、現用資源或設定。
