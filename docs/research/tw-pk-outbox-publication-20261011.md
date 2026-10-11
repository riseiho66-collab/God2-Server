# TW277：私人入場完成憑證與持久 PK 輸出串接

本輪接通既有持久化 PK grant/result 資料列與實際 Session 非同步寫出，不新增封包、不修改傷害公式，也不把寫入 socket 視為客戶端 ACK。實作為明示 opt-in 的 CUSTOM-0115；Application 尚未安裝此 driver，完整 C69/PK 路由、原生畫面驗收及部署仍未完成。

來源範圍是五個既有 C++ 檔與一個新檔：`src/net/Session.h/.cpp`、`src/db/SqliteOwnedPkRoomRepository.h`、`src/handlers/OwnedPkRoomState.h`、`src/handlers/OwnedPkEntryAdmission.h`，以及新的 `src/handlers/OwnedPkOutboxPublication.h`。既有未使用新 PK proof 的 skill sender 保留原本 87/38/86-5 限制；不能利用新結果輸出偷偷放寬舊 sender。

## 實際來源與本輪缺口

TW270 入場已持有真正 Session 私鑄 hold、完整 Prepared 入場 bytes、精確兩個 Session/帳號/角色/common lease/PK 世代，並在一個 shared Battle durable activate 後才 commit/release。TW276 能以原 Ticket 回復同 process 的 Battle，但兩者沒有提供入場 pending 清除後仍可用的私人寫畢憑證，也沒有真正把 Repository 的 grant/result outbox 接到 Session。

本輪 native agent 是 **before-only source lifecycle audit**，沒有新 native machine-code span、執行或新封包格式資格。其封存為：

- `agents/native/seal.json`：`4683615acbd5b97e85b0083d728297c7bbb07c21a0375a469bedf469a0f8e7f1`。
- 18 個完整來源輸入、41 個封存 members；實際 `findings.json` 記錄舊 proof、queue/owner 完成順序、own-viewer 初始 0B 條件、grant epoch 與 checkpoint revision 分離，以及後續 round grant 仍缺原始來源。
- 該 receipt 不審查本輪新 C++；新程式的來源閱讀與獨立審查另行記錄。歷史封包/native 證據不因本輪 source transport 而升格為已驗收。

## 私人 Written 憑證

`NativePkEntryHold::Data` 新增 atomic `written_accepted`。它只在真正 entry 全長 local write 後、實際 `native_pk_entry_written` owner 回傳 true，並再次通過精確 transport/identity fence 後設為 true；失敗、例外或 callback 拒絕均不產生可用能力。

新 `Session::native_pk_entry_written_current(hold)` 先檢查私人 hold 的 exact Session incarnation、actual game executor 與建立執行緒，再讀 game-owned 帳號與角色。其同步 transport helper 要求：Written phase、owner accepted、入場 pending 已清除、Session 未關閉、InBattle 與正確 battle generation、原本 common identity pointer/完整帳號角色/common generation、原 private NormalInitialization pointer 與 entry-written/未退休、以及入場前預配置的 exact battle delivery identity pointer/PK world generation。

此檢查不使用已不適用 InBattle 的 `normal_world_initialization_current_on_game`，也不要求舊 `native_pk_pending == data`。反過來，pending 尚未清除時必須為 false，因此不能在 entry owner completion 內直接送下一包。private initialization 仍要是同一份已 written 且未退休的 receipt；這不是重新授予 world 權限。

`written_accepted` 僅描述 entry owner 接受實際 local write，不是原服 nonce、玩家輸入權限、技能 grant、原生渲染或遠端收件 ACK。common identity 仍沿用入場保留的 exact lifecycle，不能提前 release common presence。

## 精確 room 綁定與 durable owner

Ticket 新增 identity-only `same_incarnation`：同 id、同私人 issuer、同 immutable Input pointer。它不改舊 Ticket equality/readset；`RoomState::owns_ticket` 以此確認實際 map 中持有的原 Ticket，單用 room id 或相同 JSON/readset 字串不能替代。

Admission 新增 optional Bind seam，在 durable activate、visibility departure 與兩個 Session commit 均成立後、任何 entry release 之前呼叫。Bind 前後再次確認 exact Committed holds/stage，失敗走既有 postcommit 關閉兩端並保留 active room/outboxes/locks，不能 abandon active 或恢復 world。舊 constructor absence 保持原流程。

新的 `OwnedPkOutboxPublication::bind` 接受這份原 Ticket、兩個真正 shared Session 與兩個私鑄 Committed hold；重查 same actual game executor、各 Session id、完整 account/character、實際私人 appearance common lease、獨立的 PK world generation/prebattle generation、normal frame/logical/tail/config 和 exact Prepared entry bytes。綁定 map/session index 節點先預配置，發布區段不呼叫 callback、不改 DB、不送資料。

這個 driver 借用真實 RoomState/repository，連同 callback owners 必須在同一 actual game executor 存活並 drain；它不讓 caller 的 bool 或數字構造私人 hold。最多保留 256 個 binding，failed binding 同樣保留；此數量是明示 CUSTOM 的資源限制，不是原生遊戲容量。沒有 terminal retirement/reconnect 時容量可能耗盡，不能任意刪除 active 證據或重綁 successor。

每端 own Written-current 成立且自身沒有 NativeBattle publication pending 後，`room_for` 才接受該實際 Session 的 control/action。最後的 parent 窄修明確阻擋 submitted callback 完成但 strand pending 尚未清除的窗口，避免經 input wrapper 繞過暫停。own 初始 entry submitted gate 原本就不要求對方先寫畢；本輪保留這個差異。driver 的 `control_native`/`submit_native` 從私人 binding/目前 round 取得 caller、revision 與 grant epoch；current profile/skill policy 仍由另外的真正 server owner 提供，這裡未補原生技能或 Lua 規則。

## 輸出 grammar 與資料列 fencing

`send_native_pk_output` 是獨立新 API，必須使用上述私人 Written hold 與 immutable delivery，完整比對 Session/account/character/common generation/battle generation，並由現有 native record parser 劃定 record 邊界。允許的完整資料只有：

1. 一個可解析的完整 17-byte primary-own-slot0 `86/5` grant。
2. 一或兩組 scalar result：`[可選 own-slot0 MP] → 83 selector1或3 → 對應目標 HP`，最後一個完整 121-byte `88`。actor/目標只允許目前 two-player 相對位置 0/14，每個 source 至多一組、target mask 只允許 slot0，MP 只能 own0 且屬 source0。

這不接受 arbitrary 83、82/1C/89、87/38 或未知 subtype，不把 parser 成功當玩法授權。所有 opaque bytes 保留 exact durable row，沒有新 template、padding/default 或自行猜測 raw counter/結果值。現有 result producer 來源與 LegacyCustom 限制仍保留，64 位元 numeric extension 未因此完成。

driver 的 explicit `publish_pending(room)` 才建立 immutable Flight。每 viewer 不能有重疊 flight/publication；entry revision1 只歸 Admission 寫入，不走 result writer。同一 viewer 同時存在 result 與 grant 視為來源錯誤。傳輸 sequence 只做 correlation，不是 grant epoch、round revision 或輸入 nonce。

Flight 在任何 sender callback 前進入 owner map。game-owner 的 before-write hook 與 full-write completion hook 都重新比對原 Ticket incarnation、own Written proof、兩端未關閉、目前 checkpoint/round headers，以及 exact pending row 的 room/viewer/session/PK generation/battle generation/完整 bytes。grant key 使用目前 grant epoch；result key 使用 checkpoint/outbox revision，兩者不互相冒充。

只有實際全長 async_write、exact queue frame/pending/identity、同一 immutable written delivery 與完成時 durable row fence 均成立，才呼叫 `grant_submitted(epoch,viewer)` 或 `submitted(revision,viewer)`。enqueue、reservation、before hook、callback intention 或 partial write 都不更新 submitted。已 submitted 的列不被此 driver 重置、重送或改編碼。

## 普通 response 順序、輸入與 timeout

PK output 使用原 held NativeBattle queue、budget Reservation 與前後 game-owner hooks，但 pending 額外持有真正 private entry data。所有會寫出/完成的 conditional transport fence 都重新檢查它；網路 strand 只讀同步 atomic/immutable material，不讀 game-owned account/character。

首版直接 insert held frame 會遇到 game handler 尚未 ACK 的順序窗口。refinement2 改為 strand staged reservation：`game_busy` 時不插入 held write，必須等該 ordinary callback ACK 已把普通 response 放入 queue，才 stage/qualify/release PK frame。沒有新 PK staged state 的舊 sender 行為不變。

首版「pending 中任何到達 bytes 都關閉」也已保留為歷史並撤回。最終版沿用 bounded append + pause：pending 時停止解析/dispatch，已到達資料仍受既有 buffer 上限。staging 與 held frame 釋放前拒絕已有 partial/staged records/skill prefix，避免把先前未完成 command 混入新 publication；在 unhold/write 之後到達的合法快速回應可暫存至 owner completion 與 pending clear 後再處理。這是限定窗口的 fast response 支援，不是無條件接受所有提前輸入。

尚未到達 TCP 的舊資料沒有 native epoch/nonce，無法證明其網路 freshness。完整 world→battle entry barrier 與 battle output 的 bounded pause 是不同政策，不可宣稱已消除所有 stale command。沒有自動 pump：entry callback、output before/complete 均不 inline 送下一個 flight，需真正 owner 的後續 dispatch 明確呼叫 `publish_pending`，否則待送列會保持 pending。

新 PK-only deadline 為既有 `close_timeout` 的 5 秒，涵蓋 staged hold/write/completion；沿用原 buffer/write budget（1 MiB/256）且不放寬舊 sender。timer、game/strand handoff 或 callback 失敗不得留下永久 held pending。deadline 可能在 game completion 排隊尚未執行時退休 pending，晚到 callback 要因 exact pending/identity 已失效而拒絕；不能稱 timeout 證明 callback 已執行。

正常 owner 可達的來源拒絕/失敗關閉兩端並保留 durable active/finished room、locks、submitted 原值。若 executor allocation/post 失敗阻止 game owner 通知，Session 至少關閉本端/由 strand deadline 退休，**不能保證同時通知或關閉另一端**；driver 的後續 owner dispatch 可發現 peer closing，但沒有自動監測/pump 保證。部分實際 I/O、owner DB mark 後的 final transport failure、另一端已收到 frame 都不具 network rollback/atomic fanout 能力，仍需真正 recovery owner。

## 審查與帳務界線

本輪 worker 的 Session 首版完整 epochs、refinement2 與 delta 都保留在外部 task archive 的 `agents/source/`。refinement2 Session.h 為 26,097 B／`dec2359991ce423b5138f5cb6ffad19330d26b4b7f04d845308d0f44cd795df7`；Session.cpp 為 184,371 B／`fe9312fb68f1fda2bf600213e52afe978bd5c34a6336764ace1b4a2e9e6111ba`。全六個 C++ pre-doc manifest 合計 269,205 B，包含 parent driver/Bind/private ticket seam；最後 parent input pending 窄修新增 53 B，另存 `source-freeze-final-manifest.json` 共 269,258 B。不能覆寫首版或冒稱先前版本已包含修補。

來源閱讀涵蓋 Session 新/受影響的 proof、write/fail/complete/release/read/feed/resume/ACK 路徑、四個實際 grant/result codec、完整新 driver、Admission Bind/sequencing、Ticket/Room identity seam及 native before-only findings。這不是逐字重讀整個歷史 Session 的全部互不相關功能；獨立 review 的終端 seal 由 root 輪次報告外部記錄，不在此文件反向引用造成循環 pins。

帳務預期五修改一新增、混合 source segment 259→260、review groups 26；CUSTOM 記錄 112→113。新增一條 bounded PK durable-output transport/source path，但沒有新增 opcode、完整 whole-game route 或 Phase/state/native wire 關聯完成數。最終精確數字與 unchanged source 範圍由 root 唯一靜態 packet_connection_report/final manifest 記錄；全遊戲百分比仍 null，不能把本輪 driver 當 TW100%。

本輪未做 build/compiler/tests/runtime/native/VM/codec/game DB/SQL/migration/activation/deploy。保留 frozen client/auth/chat/IME/fonts/conversion/CN/web/shared numeric 目標。後續缺口仍包括 Application 真正 hosting/resolvers、結果模板與學習技能/Lua/規則、later-round grant、terminal settlement/world return、跨 restart private Ticket/Session 重建、完整 network recovery 和原生 acceptance。這些沒有被 writer 或 retained same-process recovery 自動補齊。
