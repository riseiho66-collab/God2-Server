# 原服排程、回合計數與完整身份來源：pass8

本輪為 PHASE1 SOURCE_STATIC_ONLY。以目前台服原件及靜態 REA 追新上游，
沒有編譯、測試、遊戲／VM、codec、遊戲 SQL／schema、啟用或部署。
測試原碼、代碼複查與靜態報告不能當作實機通過，也不構成原服公式還原完成。

## 修正真正的世界身份來源查錯

`Application::deliver_visibility` 原本以 `spawn.identity()` 呼叫
`snapshot_character`，後者比較的是完整資料庫 character ID。
封包中的角色 handle 與完整64位元 character 是不同域；若角色編號大於 handle
範圍，可能漏載稱號；若另一角色的資料庫編號恰巧等於該 handle，則可能讀錯人。

現在 `snapshot_spawn` 先以完整原始6F記錄匹配真正 visibility Presence，
再以該 Presence 的完整 account／character 讀取文字，不從 handle 合成 DB ID。
文字讀取後再核相同原始 spawn、Session、owner、scene、pose、departure 及
收件人的帳角、phase、battle generation、語言和 PvE 狀態；失效便拒絕送出。
不以第一筆、名稱、低位截斷或缺資料補預設文字。繁簡顯示仍走原有接收者編碼。

同一讀取切面亦保留實際 sender／recipient Session registry 指標與各自 movement
觀察。PvE 掛載時兩者都必須存在並與原 scene 相符，SQL 後重核同 incarnation／pose；
不能只核新進者而漏掉回送給他的既有 peer。已在戰鬥的 sender 可使用自己的 retained
移動來源，不強套 normal phase。舊診斷未掛 PvE 且沒有該移動 owner 的路徑保留；
若原本取得觀察仍須核對，不以不存在的 owner 造資格。

未執行的 visibility 來源案例包含超過32位元的 account／character、另一角色 ID
與 handle 數值相撞、相同 handle 但不同完整 spawn、pose、Fight 更新及離場。
這些案例檢查來源查找；沒有宣稱覆蓋完整 Application／真實 SQL observer／客戶端。

## 世界資料組裝與延後入戰也保留原始來源

`OwnedPveApplicationSource::observe_world` 原先在讀位置／root 之前沒有捕捉正常世界
的原移動綁定，最後亦無純檢查就組裝並發布世界身份。現在第一個 SQL 前取得
`RecoveredNormalCompanionCurrent`，位置觀察、root 觀察及 visibility 發布前都重核
相同 Session／Written INIT／完整 owner／phase／battle／movement incarnation／pose。
同步 Deliver 介面把擁有的純判斷保留到實際收件人文字 SQL 後及每次發送前，
不是只在 visibility 入表前檢查。普通移動用正常世界來源；Fight 標記進入用真正
私有 PvE binding，返回則用新的 normal 來源，不能讓新增檢查阻斷合法返回。

移動回覆等待真正 Written 的 Pending 原先只保存座標與 INIT；同值 remove／reprepare
可能沿用舊回覆。現在 Pending 保存同一純觀察，poll 在進入真正 room provider 前
核對。合法新移動仍取得自己的觀察；舊 Written 不會替新 binding 授權。
房間內 member、逐人返回、寵物／技能接續繼續使用 pass7 的 retained 私有來源。

這是來源生命周期修正，沒有新增原服遭遇、先手、移動速度或戰鬥規則。
未建立完整 Application／NPC／銀行 host fixture；既有 helper 的來源案例不能冒充
上述宿主的執行驗收。改動後由另一位審查者複查原碼與等價入口。

## 回合上游、佇列及資料容量

[本輪回合 REA](tw-native-round-producer-pass8-20261021.md)追到網路完整 record
經 `519370 → 51D4E0` 進入 CWar ring 的實際路徑。成功 append 的分支保留
收到的 actor／group 次序；沒有在該分支看到依角色能力排序。
這個結論有成功 append 的容量前提，不能延伸為整個網路串流一定完整保留。

constructor 設 ring 容量 `0x1400`（5120 bytes），append 失敗後接收迴圈仍消耗
該 record，沒有重試。服務端單 logical frame 上限為2560 bytes，aggregate
上限為655360 bytes；兩者皆不能證明尚未消費的 ring 安全容量。
目前投影各路徑的單次保守大小另見
[投影來源與邊界審查](tw-pve-identity-projection-pass8-20261021.md)；單次大小界
不能證明跨 callback 的 ring 已清空，socket Written 或0B也不是原生動畫 ACK。
本輪沒有因此另造 ACK、改固定 counter 為遞增回合數或新增未證 pacing 公式。

新的 actor bulk reset 路徑沒有到達 latch6C，但仍只是已審範圍的結果。
原服先手比較、平手／技能優先級、RNG 排序、S83 group／S88 counter 產生者仍未
在目前客戶端取得。現有 CUSTOM 排程保留標示，不把 renderer 掃槽當成先攻公式。

## 外觀上游與文字安全資格

[本輪身份／外觀 REA](tw-native-identity-appearance-producer-pass8-20261021.md)
記錄當前 `aaf0...cd48` 的實際 caller、欄位來源與仍缺少的完整 producer。
沒有使用舊 csvZ pin 代替當前資料，也沒有執行 codec 或猜裝備映射。
本輪取得真正的 section dispatcher：`456130` 將 `EnyName` 交給 `45A1A0`，
將 `ChangeDollCount` 交給 `45BB10`。後者確有48B本機定義 writer；8B getter
含未初始化備用位元組，完整定義內亦有 process-local pointer，均不能當可攜封包
或一律補零。檔案 wrapper 會嘗試參數加Z及特定檔頭路徑；實際外層檔名仍待追，
沒有宣稱成功解碼目前 csvZ。裝備 C28 與 S3B／S41 的實際來源更新也已追到，
仍不能單憑這些入口推出裝備到完整 Fight 外觀或戰寵 WORD7 的唯一生成值。

普通 player1C 的 wire9..24／25..40 分別到兩個文字 renderer；renderer 使用
無界 strlen 及 copy。Catalog 已有兩欄各自範圍內終止字元的來源限制，本輪將該
限制抽成同一純檢查並補到直接 Projection 入口。失敗拒絕整份輸出，不截斷或補零。
這是安全來源資格，不是聲稱原生 receiver 會拒絕，也不是原服命名字數公式。
enemy 的9..40包含參數，pet亦有不同分支，不能一律套普通 player 的兩欄規則。
等價入口亦補齊 pet 單一32B文字的既有來源限制，以及敵方 variant400／無普通
appearance／無 MP writer 的既有 Catalog 類型限制；不能把 pet 或普通 player
放在敵方位置以繞過檢查。Raw codec 仍無損保留全部資料；敵方參數不套文字資格。

Projection 的公開 carrier 若 saved pet 與 assignment.pet 不一致，原先可能解參考
空 optional；現在解參考前明確拒絕。實際 host 的 repository 已先檢查這項一致性，
本輪不將純 API 防錯誇大為已證實的玩家可達 host 漏洞。
原件、完整外觀及未知 opaque 材料要求仍保留，沒有用安全檢查冒充生成規則。

## 交付與未完成項目

每項改動包含作者複查及修改後獨立代碼審查，原始證據、SHA、REA 關閉、
唯一正式靜態報告及提交收據位於：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass8`。
完整原服排程及完整身份／外觀 producer 仍未完成；集中編譯、回歸、實際台服聯合
驗收與部署尚未執行。另行暫停的完整目標與四小時 Discord heartbeat 維持原狀。
