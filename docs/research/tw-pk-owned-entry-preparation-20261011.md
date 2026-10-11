# TW274：從實際共用來源產生 PK Prepare 收據

本輪把既有私有來源鏈接到可直接作為 `OwnedPkEntryAdmission::Prepare` 的具體工廠：取得兩個真正的 Session／正常入場收據、目前共用 ready lease 與位置，再在內部產生完整雙視角入場內容，呼叫既有 `prepare_owned` 保留 durable room ticket。新增的是明示 CUSTOM-0112 的來源整合；Application 尚未安裝此 Prepare 或 RoomAuthority，不宣稱完整 C69／PK 路由、原服規則或客戶端驗收。

執行範圍限 PHASE1 靜態原始碼、文件、雜湊及帳務。沒有 build、compiler、test、runtime、native／VM、codec、game DB／SQL、migration、activation 或 deployment。GitHub、Discord、`.git`、`.gitignore`、工作流及其他通知檔完全排除本輪遊戲來源證據。帳號存檔、聊天、IME、認證、原生字體、文字轉換、客戶端、CN／web 與共用 64 位數值目標維持既有範圍。

## 原有來源及具體缺口

`SharedTaiwanNativeWorldHostPlan` 的聯合裝備交易工廠每次建立不同 `SqliteOwnedEquipmentTransaction` identity。其 `Committed` 還包含兩個實際 writer 私有 identity，不能從另一個 joint 挪用。`SharedTaiwanMovement` 寫入後取得真正 Committed，但只在當次發布流程使用；`SharedTaiwanNativeEquipmentPublicationSource` 私有保留 joint 與收據，沒有對 PK 開放取得介面。既有 `observe_before` 提供完整目前資料，型別不是 Committed；以兩個獨立 reader 快照拼接、重解讀 Before、無變動假寫入或任意 bool 都不能補這個缺口。

Application 的舊 `pk_peer` 使用 companion restoration 私有來源及既有 written batch，不能直接等同正常 shared-native 入場來源；原有私有 `normal_world_initialization()` 只能在真正 world-record callback 取得。`current_on_game` 能重驗既已取得的私有收據，不能從外部原始 bytes 製造。正常收據的通用 current 可容許 CharacterSelected，但本輪 Prepare 更嚴格要求實際 InWorld、entry_written、目前 ready lease 與 saved current position。

本輪使用的 `RecoveredWorldEntry::Frame` 是實際 typed **40 bytes**，logical S2A 是 **37 bytes**。先前已封存文件的 Frame42 說法維持歷史紀錄，TW267 已明確更正；本輪不覆寫舊封存。

## 唯讀取得真正 joint 收據

在 `SqliteOwnedEquipmentTransaction.h/.cpp` 加入 `observe_committed(account, character)`。它重用同一 joint 的 `observe_before`：單一一致讀取範圍取得完整 inventory／equipment、同源 common root 及位置，保留既有 namespace／TEMP-shadow／repository owner／reentry 檢查。缺少任一完整資料就拒絕。

該次單一完整觀察在原讀取範圍結束後，為 joint 與兩個真正 writer identity 私有建立 immutable token，然後呼叫同一 joint 的 `committed_current` 再讀並比較完整資料。它不是兩次獨立 writer observation 的組合，不寫資料、不升 revision、不 grant 物品、不決定穿裝備權限。名稱 Committed 在這裡表示已持久化資料的私有觀察收據；**不證明曾執行某次歷史 writer，不建立原生 capture、native issuer 或動作權限**。原有 replace／movement／before／current 行為不改。

## 實際 Prepare API 與來源鏈

新增 `src/handlers/OwnedTaiwanPkEntryPreparation.h`，非可複製物件，建構時保留 actual game owner thread；可用 `prepare(const Pair&)` 或 `operator()(const Pair&)`。依賴為同一 SQLite connection 的實際 accounts、characters、world snapshots、auxiliary、secondary text、room repository，以及同一 shared presence 與 joint。Fight catalog 按值保留其 shared immutable storage，避免暫時 catalog 借用懸空；其原始完整 archived input 與四個 side-qualified selections 的資格仍沿用 TW266。

只接受四種具體 owner resolver，不接受 View／stats／raw template／control mask／caller digest：

- `Sessions(session_id)` 回傳真正 `shared_ptr<Session>`。
- `Initializations(exact_shared_session)` 回傳真正既已 mint 的 `Session::NormalWorldInitialization`，來源必須由正常 world-record callback 私有取得並適當保留。
- `Resolve(session_id)` 回傳完整目前 `OwnedPkInvitationService::Peer`。
- `Seed(immutable_pair)` 回傳明示 trusted server-owned `optional<uint32_t>`。

Constructor 驗證所有 concrete connection／source ownership，presence 必須擁有同一 characters repository，room 必須為同一 DB。借用資料庫、repositories、room 及 callback owners 必須比 Prepare、ticket 活得更久，並在相同 game executor drain 完後才銷毀。函式物件型別不會自行證明 resolver 來源正確；真正 Application owner 接線仍是下一個依賴。

每次 prepare 先複製完整 Pair 作內部 immutable attempt snapshot。要求不同 session／角色、正確 account、非零 PK world_generation、兩方 ready 且未 blocked、相同 area／scene。依序取得兩個 exact Session 與私有 initialization，先驗 current_on_game 與 entry_written，才讀 Session 的 account／character／state／battle_generation 等可變欄位；要求 InWorld 且世代完整相符。再取得真正 common ready lease，檢查 saved position 完整等於 Peer.position。

兩個 Session 必須通過現有 `same_native_pk_game_executor`，它比較實際 asio executor 及已知 common-ready game thread，不只是相同 thread ID。PK `Peer.world_generation` 由 Resolve 完整重觀察，**不等同 common `Lease.generation`**。初始 lease.position 是入場位置，移動後的目前 saved position 另讀；本輪不把兩個位置盲目視為永久相等。

內部來源串接為：

1. 同 joint `observe_committed` 完整目前 durable tuple。
2. TW267 `OwnedTaiwanPkAppearanceSource::observe`：真正 Session／私有初始化、實際 full typed entry、joint 完整來源與 ready lease。
3. TW268 `OwnedTaiwanPkCombatSource::observe`：同 concrete characters、role/resources/full auxiliary。仍是 CUSTOM-0106 採納舊6bf provenance server-owned totals，origin label 不是 native authority。
4. TW269 `OwnedTaiwanPkPlayerEntrySource::observe`：完整 primary root/name 及實際已存 secondary text/revision/codepage，依真正 recipient private config 嚴格 CP950／936 lossless projection。missing title／未知 codepage 不以空值或替代字補。
5. TW271 `OwnedTaiwanPkVitalSource::observe`：精確已存 HP／MP，保持 checked legacy DWORD、HP 正值及所有既有 domain 限制，不縮窄、不補 max1。
6. TW273 `prepare_waiting_notification_owned_initial_contexts`：只由兩組 exact private Player／Vital 和 catalog 產生兩個完整305-byte initial entries，以及私有 contexts／bulks／grants／appearance／recipient identities／vital templates／four Fight selections。每個 selection 保留四個 component rows；不是只保留四個 row references。
7. `rooms.prepare_owned`：以兩組 exact private Combat、完整 Prepared、真正供應 seed 及 **Prepared 自己產生**的 initial notification bounds，在既有 repository 內產生 resources／roles／actors／完整 source readset／digest 與 durable RESERVED ticket。沒有外部指定 expected native0B masks。

所有 CUSTOM-0105..0111 restricted domain／canonical wire／文字／clock-context／empty-slot 選擇維持明確標示。complete source chain 不把這些選擇改稱 original server producer，不產生 learned skill／hit-target／turn／Lua／monster formula authority，也不表示 full56 renderer 已成功。

## Seed 與 callback 邊界

Seed 是明示 CUSTOM-0112 的內部可信 server supplier。缺少值就拒絕，不從 clock、contextA、room ID、玩家值或 hash 猜測，不以 default0 補缺；supplier 明確回傳0仍是實際 uint32 seed。該值進入既有 shared Battle 與完整 readset，並非 native original RNG、global nonce、context timebase 或原生技能權限。未安裝真正 supplier，便不會完成 Application Prepare 接線。

所有 resolver 必須同步、不可 yield、pump executor、改 SQL、重入 Prepare 或變動 session owner。每次 callback 前後檢查 actual owner thread、reentry、SQLite autocommit 及 total_changes。回傳後反覆檢查相同 shared Session incarnation、私有 initialization、common lease／saved pose，並完整重觀察兩方 Peer。完整 Player.Current 再驗 root/text/role/resources/auxiliary/inventory/equipment/world material 與正常私有世代，不只比 SHA。

這些 guard **不是任意 callback side effect 的原子攔截器**。外部 connection 併發變更、改後復原的 ABA、執行器 pumping、尚未收到的 TCP 舊資料等仍屬既有 owner／admission/recovery 限制。callback throw 會傳播；若已產生 RESERVED ticket，RAII 仍呼叫原有 noexcept abandon。沒有在 callback 內開 source transaction；live 私有來源檢查在 SQL 外，room 原有 RESERVED closed full tuple comparison 在其 SQL 範圍內。

## Reservation 與根工廠整合

在完整來源與 seed 取得後，Prepare 於 reservation 前再次 exact resolve Pair、same actual executor、local Session／lease 與 full Player.Current。產生 ticket 後又重做 exact resolver／full current，並呼叫既有 `rooms.current`。任何後置拒絕或 exception 都 abandon RESERVED；durable identifier 仍由既有 repository 保留，不回收或 reinterpret 既有 ticket。這不是原子 live Session／SQL／雙 socket admission，也不把 preflight→commit 窗口描述成完整 CAS。

`SqliteDatabase.h/.cpp` 新增 `make_owned_taiwan_pk_entry_preparation(room,presence,catalog,Sessions,Initializations,Resolve,Seed)`。root 工廠從實際 Impl 私有 connection 與相同 DB-owned writer／repository 組合此物件，呼叫端不必取得 raw DB。`SqliteOwnedPkRoomRepository.h` 只新增 connection identity accessor。工廠只 assemble，沒有 schema／DDL／population／reservation／send；仍須既有 migrated database 及 caller 已備妥 room。

Prepare 階段不 hold input、不轉 InBattle、不增加 battle_generation、不 queue 82、不 release visibility、不 active room。後續真正 Accepted69→dual hold→one durable activate→two commit→full-write completion 使用 TW270 admission contract；本輪沒有改它或把 `commit()` posted intention 說成成功。所有 old APIs、template paths、writer semantics、raw readsets 和 defaults 保留。

## 首版與精化紀錄

首版三個 worker source 完整保留於外部 `agents/source/first-candidate`，沒有以精化覆寫。SOURCE274-01 是實際 caller Pair alias 風險：首版 exact checks 使用 captured old peers，卻在 seed／repository call 使用 caller 原 Pair reference。trusted callback 若經另一 alias 改 world_generation，可能造成二者不一致；不能依靠外層 admission 再擋。refinement2 在 owner/reentry guard 後立即完整複製 Pair，Seed／Resolve comparisons／repository input 始終使用同一 immutable snapshot。root 與 independent reviewer 均確認這項窄修。

CUSTOM index 追加 CUSTOM-0112，原109 entries 與其他 top fields 保持結構完全相同，總數110。只有新 opt-in source factory，無 Application 安裝、default enable、DB schema 或 migration；本輪混合來源紀錄增量及 packet 報告由 root 靜態帳務保存。新 opcode、phase association、完整 gameplay route 均為0；全遊戲分母／百分比仍未知，parser coverage 不是完成度。

## 下一個真正 hosting／生命週期依賴

Application 尚未提供此工廠需要的正常 shared-native initialization retention、exact Session registry、PK ready/blocked/world-generation resolver 和真正 server seed supplier。舊 companion pk_peer 不能盲用，未有 real owner 前不安裝 pk_rooms。common presence ready 本身不代表 Session InWorld；可見性 recipient gating 與 source departure 應由專門生命周期接點負責。

尤其不能在 Prepare／commit／entry write 中直接呼叫舊 lifecycle.release：那會終止共用綁定，撤銷 TW270 held/current/written 還需要的 common identity。既有 `SharedActorVisibility.release` 能移除邊並發送原生 remove，但不是可逆 suspend；PK terminal world-return／reconnect／partial-I/O recovery 尚未串完。必須補具體 departure/visibility owner，保持雙 Session transport qualification，再完成後續技能、35、turn/results、later grants/counters、world return 與持久 recovery。

## 證據範圍

外部輪次根目錄是 `C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-owned-entry-preparation-274`。worker 完整保留 root133 truebefore files／18,815,385 bytes；其中94 source files。原始三檔首版、refinement2、full manifests／diff、policy old/new、來源閱讀及後續 root account/report epoch 分別保存。

本輪 native agent 做的是**靜態 source lifecycle audit**，不是新的 PE native recovery 或執行：`agents/native/seal.json` SHA256 `dbf67e4cc99e1c01a9793fe4495be94f19335a8e68aa022fdfc4c396d56bdbfa`；`findings.json` SHA256 `443ffdc14804c971190813cf7e6bedd101b1aed425f711537c4e55d438a89f88`。audit 的「沒有 observe_committed」只針對 before baseline，不能套到本輪新 source。

CUSTOM index 本輪 SHA256 `2280bc6ac40d6cfdb143f1216ac272326cc65a201a5321619539191aa30b9e6e`。完整候選／doc pin、靜態帳務及獨立審查終端封存由 root 輪次報告記錄，避免把互相參照的 seal 寫回已凍結來源。檔案雜湊、static review 或 verified archive 都不是 build／test／native rendering／production activation。
