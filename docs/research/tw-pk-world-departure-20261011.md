# TW275：雙方原生 PK 入場前的共用世界可見性退場

本輪接上實際 `OwnedPkEntryAdmission` 的 opt-in 可見性退場：兩個真正 Session 的私有 PK entry holds 都完成後，先由同一 `OwnedPkRoomState` activate 一個 shared Battle，再退出兩方的世界可見性，重驗兩個 holds，最後 commit Session、再驗退場 receipt，才 release entry writes。這是 CUSTOM-0113 的生命週期選擇，不是原服退場時序、原子雙 socket 寫入、native ACK 或完整 PK route。Application 尚未安裝完整 RoomAuthority；技能、turn/results、terminal return 和持久 recovery 仍未完成。

PHASE1 僅讀寫 source、文件、hash／diff／靜態帳務；沒有 build、compiler、test、runtime、native、VM、codec、game DB／SQL、migration、activation 或 deployment。本輪不改 client、auth、聊天規則、IME、字體、繁簡轉換、數值擴充、CN／web wire 或預設啟用狀態。

## 真正 owner 與新增接點

`SharedActorVisibility.h/.cpp` 新增私有 mint 的 `TaiwanPkDeparture`、`withdraw_taiwan_pk` 及 `taiwan_pk_departure_current`。withdraw 的三組 by-value inputs 是 exact two common `Lease`、兩個強持有的 shared Session、兩個 Session 私有 `NativePkEntryHold`。公開 scalar、caller bool、相同帳號字串或 frame hash 都不能取代私有 hold。

每個 hold 必須是該 Session 的 exact Held incarnation，並由真正 game owner／相同 asio game executor 檢查。私有 current guard 在讀 Session mutable fields 前執行。接著比較完整 account、character、session ID、common generation，保留 complete current saved position，重觀察 exact ready lease 和 saved position；兩方必須在同 area／scene。PK Peer.world_generation 和 common Lease.generation 仍是不同 namespace，沒有互相比值或縮窄。

`Session.h/.cpp` 新增只讀 `native_pk_entry_committed_current`。它只接受同 thread、同 game executor、同 Session、同 pending token、Committed phase、未 completing，重用既有 committed transport qualification，並要求實際 preallocated battle identity pointer 及 account／character 完整相同。它不要求已失效的 prebattle normal-initialization current，也不延長 token 到 Released／Written。舊 Held guard、skill publisher 與 world sender 行為未放寬。

`OwnedPkEntryAdmission.h` 的新 optional visibility/presence dependencies 必須同時提供或同時缺席，並要求 visibility owns 該 exact presence。prepare 在 holding 前另由 private267 appearance `owns_presence` identity-only accessor 檢查實際來源 registry。`OwnedTaiwanPkAppearanceSource.h` 只新增這項 identity accessor，沒有重寫 Current 或存檔。相同 Presence 不能證明全域只有一個 Visibility；選用實際 Application visibility 仍是可信 owner 的責任。沒有 dependency 的舊 admission path 不增加退場行為。

## 兩方 marker 與完整邊集合

在任何可見性 mutation 前，withdraw 先配置完整 paired state、兩個 registry map nodes、受影響 pending states 的強持有清單，以及現有 outgoing edge 的完整 native removal bytes。每個 removal 來自原有 entry 所保存的 remove record，沿用既有 TW/CN producer；沒有猜 6F、73、actor identity 或未觀察的附近玩家。

兩個 marker 同時以預配置 node transfer 安裝。接著先移除 **兩方全部 incoming 和 outgoing edges**，並 detach 所有涉及任一 source／recipient 的 pending appearance／outward map entries，才執行任何 completion、close 或 native send。這避免先處理一方 outgoing 時把 world73 排到另一方 held PK entry 後面。

所有新的直接 show、initial publication、outward publication、appearance publication、movement／expected-model／chat-actor source reads，都檢查 exact departed source 與 recipient；已準備的 initial token 在發佈前也重驗所有 staged sources。檢查包圍實際 name／scene／repository callbacks，防止 callback 中退場後舊 token 再插入邊。這只是針對 opt-in exact TW departed lease 的可見性 gate，不新增聊天過濾、CN 規則或封包轉換。

registry key 是 Session ID，但 marker 必須同時符合完整 Lease incarnation。舊 lease 的 cleanup 不阻擋／刪除 successor lease。withdraw 中的 paired state 維持阻擋，即使同步 callback 重入 release。重入 withdraw 會 poison 目前 pair；read fence 重入也會拒絕。沒有回傳 receipt 不表示已變動的世界可見性已回復。

## 已送出 pending 發布的拒絕邊界

REVIEW275-01 是實際 transport 邊界：`send_common_world_records_with_publication` 在 publish callback 拒絕或 common phase qualification 失效時，有獨立的 Session.fail continuation。只 suppress Visibility.reject_output 的 close，不能安全取消已送到 PK participant 的 pending world publication。

因此 withdraw 在安裝 marker、移除邊、取消 callback **之前**，拒絕任何尚未 finished、已 issued 的 pending outward delivery 或 DA appearance，其 exact recipient 為任一 participant。這不是假的 drain／rollback；因 admission 已 durable activate，此拒絕會走 close-both、保留 active room／outboxes／locks 的 recovery 路徑。

尚未 issued 的涉及發布可以取消。已 issued 但只往 surviving observers 的 outgoing 發布，保留舊 failure／close policy；其 observers 可能已有部分 6F／DA，不能宣稱回滾。finished-success 已經 release 舊 frame，既有 FIFO 位於 PK entry 前，這項 preflight 不再把它當 pending 發布；它也不是已收到或已渲染的證明。

這個 scoped tracking **不證明 universal socket quiescence**。先前取消但未受此 registry 追蹤的 continuation、其他外部 sender、尚未收到的 TCP 舊 bytes、frame 部分 I/O 仍可能造成 close 與 durable recovery。沒有 native epoch／nonce，也沒有本輪新增的 typed Session publication drain。不能把零舊 read 的 cancellation confirmation 或 queue order 當成 native ACK。

## completion、surviving observers 與失敗

移除模型與 detach pending 後才呼叫舊 finish functions，保持各 pending completion 至多一次。對兩個 exact marked recipients，Visibility 自己的 expected-model reject close 不再觸發；然而任意外部 done callback 仍可能關閉它們。withdraw 不是 callback side-effect 的原子屏障，所以完成後必須重新檢查兩個 exact Held transports、common lease／saved pose 與 marker incarnation。

兩方互相的 incoming edges 只消失，不發 world remove 到 participant。只有 source 為 participant、recipient 為 surviving observer 的原有邊，提交原先保存的 native73。submission failure 仍沿用 observer 的精確 incarnation rejection；不回滾已刪除的邊、saved position 或 active room。native73 只觀察到本地 submission intention，沒有新增 local fullwrite receipt，更不是 native consumer 成功。

Admission 的順序是：

1. 既有 Accepted69 後才準備兩個 exact input barriers／held entries；仍未 InBattle。
2. 原有 current／private Player／Peer guards 後，`rooms.activate` 一次；從此是 active failure policy。
3. optional `withdraw_taiwan_pk`，再驗退場 current、StageActive、兩個私有 Held current。
4. 兩次既有 no-allocation Session commit；後驗兩個私有 Committed current、退場 receipt 及 StageActive。
5. release 兩個 held writes；既有 exact full local socket write callback 才記各 outbox submitted，雙方完成後才通知 admission completion。

任何 durable activate 後的拒絕、callback side effect、第二方 commit／post failure 或 partial socket write 都 close both，保留 active room 與 recovery material，不 resume world 或 abandon active。不可在步驟3後再呼叫 full Player／Appearance.Current：active room owner locks 可以使其舊 world-current domain 正當失效。不可在步驟4後要求 prebattle normal initialization current；新的 Committed guard 正是區分這個 phase。

## receipt、marker 與 terminal return

`taiwan_pk_departure_current` 只接受該 Visibility 私有 paired state、兩個 exact markers、兩個原 Session 和 private transport，且 transport 為 Held 或 Committed **PRE-RELEASE**。release、Written、pending-cleared、timeout／close 都不能以此 receipt 重新授權。marker 本身在 token 不再 current 後仍存在，阻止 world edges 被重新發布。

只有 exact `SharedActorVisibility.release(lease)` 在取消 pending／移除 incidence cleanup 完成後退休該 lease 的 marker。它先保留 strong state，nested same-lease release 不提前清除；不擦掉另一方或 successor marker。release 會 poison pair current。`reset_recipient` 不是 marker retirement，也沒有新增 resume API。

本輪從不呼叫 `SharedTaiwanWorldLifecycle.release` 取代 departure：它會撤銷 common identity，而 held/current/written entry transport 仍需它。Presence ready 與共同 transport identity 持續存在；visibility marker 是唯一新增的 departure 狀態。這不代表 PK terminal world-return 已完成。

真正 terminal return 還缺：保存資源／獎勵政策與兩方 terminal outboxes、native89 producer、可恢復 ticket load／enumeration、locks 釋放、完整新正常 entry 與 private initialization／common generation、世界重新發佈的 owner。單純 setInWorld 會再增加 battle generation，使舊 private normal initialization 不 current；舊 diagnostic single-action return 不能拿來共用。S86／88 更新 display 不等於 saved settlement 或 world-ready。

## 證據與帳務

首版已完整保留。REVIEW275-01 的 issued-recipient preflight 和 REVIEW275-02 的 exact shared Presence proof 都在獨立審查範圍內。REVIEW275-03 指出首版「收集 pending／removals 後再呼叫 repository fence」可經 observer 重入新增未收集的 incidence；refinement2 移除 collection 後的 callbackful fence，讓最後 full observer fence 在完整 pure collection 之前。此後至雙 marker node transfer 只有 registry reads／既有完整 record encoding／allocation，沒有外部 callback。

root 另找到 outward final pre-insert check 的重入缺口：`recipient_bound` 可經 Presence reader withdraw／finish pending，舊末端卻只檢查 transport。refinement2 在 observer 後補 final pure exact-pending pointer／finished／兩端 marker checks，並把早期 pending iterator lookup 移到 saved_position observer 後，避免解參照已遭 callback 刪除的 iterator。原 first source／raw full diff、first-to-refinement2 diff 均保留；沒有用後版覆寫舊證據。

worker 最後完整閱讀 normalized diff 時，在 outward `source_current` lambda 又發現同型 iterator 風險：首版及 refinement2 仍先 find pending，才呼叫 saved_position observer。refinement3 只把該 find 移到 observer 回來之後，保留原 full pending pointer／finished／source-marker qualification。先前 source／doc epoch 全部保留，沒有新增功能或放寬資格。

輪次外部根目錄：`C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-world-departure-275`。root truebefore143 files／102 source files。worker 只保留此次實際使用的11個 full before inputs（828,406 bytes），沒有複製全歷史樹。首版兩個 Visibility source、full manifests／diff 及後續精化各自保存；root 的 Session／Admission／Appearance source epoch 另外保存，未冒稱本 worker修改那些檔案。

native worker 本輪是靜態 source lifecycle／terminal audit，沒有新 PE scan 或 native execution。`agents/native/seal.json` SHA256 `44609dbc378b8313f505af13ef1c0665fc4f730406e587207005bf1dc369f465`；findings SHA256 `f91b27aca43c0ee3e7ca4a9226db94f8de87afb00c87f8b09ac00e058c77a72b`。它明示 baseline source 與後續 live Session／Admission edits 的界線，不能拿 baseline audit 冒充對新 source 的獨立審查。

CUSTOM-0113 append-only 保存原110 entries／其他 top fields，總111。六個 modified source files 包含 worker 的 Visibility.h/.cpp、root 的 Session.h/.cpp／Admission.h／Appearance.h；本輪不是六個 worker edits。新增 one opt-in departure/lifecycle source path，沒有新 opcode、phase association 或完整 gameplay route；groups26維持，whole-game denominator／百分比未知。完整 source pin、policy pin、靜態帳務／unique report 及獨立 reviewer 終端由 root 輪次報告記錄，避免 circular seal。雜湊／靜態閱讀不等於 compilation、native acceptance、部署或 TW100%。
