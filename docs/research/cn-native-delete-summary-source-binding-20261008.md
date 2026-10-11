# CN 刪除操作接入完整摘要失效來源

第153輪 `20261008-cn-native-delete-summary-source-binding` 將152輪明確 summary-aware storage entry 接入實際 `SharedCharacterDeleteOperation`。新 source mode 是 host 顯式提供的 `Sources::native_summary_removal`：同一 typed SQLite summary repository 加實際 issuer Prepare。沒有 default supplier、schema install、原生數值、成功封包或退回 legacy 的替代規則。Main／實際 source factory／issuer／schema 尚未設定；本輪只 source integration。

新增 `read_removal_observation` 從同一 accounts／mutable characters／SQLite 取得完整 account summary scopes 與全部共用 roots。此方法要求 owner thread、相同 backend、autocommit 和無其他 summary writing lease，自有 BEGIN IMMEDIATE，兩份 owned vectors 在同一 snapshot、read COMMIT 前形成，之後只 NRVO／move 返回。此讀取 COMMIT 沒有持久資料 mutation，也不等於角色已刪除。缺 schema／孤兒／malformed／wrong owner 按既有完整 inventory reader 拒絕，不給假 empty。

新 move-only `SummaryDecision` 擁有 exact Scope（包括唯一 Attempt）、完整 expected common row、整份 actual Observation、必需 phased Current。Prepare 接收借用觀察但必須產生自己的 owned Decision，不能留下失效 references。Decision 與實際讀取觀察須完全相等：所有 destination／build scopes、完整 native records／revision／origin、ordered mapping／optional role、完整 roots 都保留，不只 CN 或含 selected ID 的部分。沒有從 native slot／名字／row byte 推 common ID 或權利。

既有 native Decision 仍供給完整原生02（23-byte）與真正 native rule／guild／lease／replay Current。**只有實際 status0 removal decision** 才讀 summary Observation、呼叫 summary Prepare，再檢查返回的 Scope／row／Observation、Deciding phase／selection／identity／stored root，持有 SummaryDecision 後進入 Removing。非零 native02 沒有 summary read／Prepare／invalidation；configured source malformed、Prepare null／exception／錯 Attempt 或來源不一致，操作停止，不 reset source 或退回 legacy。

配置新 source 的 Removing branch 實際呼叫 `SharedCharacterRemoval::commit_with_native_summaries`，輸入整份 expected summaries。BeforeErase／BeforeCommit wrapper 同時要求既有 native Decision／selection gates 與 SummaryDecision 的完整 inventory／original roots 匹配、actual summary Current，再次檢查既有 gates。152 writer 比對 actual transaction 的完整 expected→absence，以及 actual roots→minus exact ID；BeforeCommit callback 保留 original roots 作授權輸入，不能誤要求資料庫中被刪 row 還在。

未選用新 source 的既有 legacy branch 保留。Composition 獨立檢查 optional presence，避免 partial source 的 bool=false 被當沒有選用；必须是 exact Context.character_summaries、accounts／characters 與同一 deletion repository，且既有 preparation presence registry 相符。沒有把 generic repository cast 成 SQLite、開第二個 DB、默認選 schema 或修改 frozen TW handler。

Queue phases 在 successful removal return 後由 `committed_` 事實啟用新 Current；BeforeQueue／AfterQueue 同時保留原 native Decision、selection、stored root／presence gates。Summary Current 看 actual committed operation／receipt，而非失效後的舊 raw summary Current。非零 reply 要求沒有 committed removal 或 SummaryDecision。所有 observation／SummaryDecision／expected inventory 都在 removal SQL 前 owned。

**既有 transport 的 send_batch／completion std::function 配置及 queue source checks 仍在 removal COMMIT 後。** 本輪沒有聲稱 transport 全部 preallocate、durable response receipt、replay／disconnect recovery 或 COMMIT 後 queue failure 已解決。Storage writer 只立即 apply 已準備的 affected-character admission invalidation；general CAS 和 whole-account issued worldoffer refresh／revocation仍 OPEN。Actual new issuer／source factory／Main CN plan／schema／native data未啟用，不計 complete route 或 playable acceptance。

原生 WORLD68 新增兩個 resource lookup helper 的 key/output WORD 關係：actual UI ECX→resource＋65364→unsigned LOWWORD key gate→output WORD；callback arg 的低 WORD 覆寫與 saved index／record pointer 區別保留。GUI負 handle 的具體分支上 same-owner preservation 有資格，其他 GUI callback effects仍未知。新 helper144 bytes／44 sites、GUI bridge89 bytes／29 sites；含沿用 callback／lookup 的 bounded delivery775 bytes／243 sites，舊 WORLD68 phase不重計，native1／30不當 stack99。

GodLevel 新 typed copy boundary 證明 parser CRT 的379-byte scratch條件與94-byte bank／selected-row destination資格不同。來源 Current 必須保有實際欄位、NUL與目的地資料契約；selector4 bytes／first NUL／42CA20 caller、selected-row destination capacity仍未知。9個 primary／9207 bytes／106 sites屬 bounded evidence，不代表 global writer排除或 runtime safety／接受。

三位子代理分工與 M2獨立唯讀 review 保留原始 hash／read ranges，歷史封存不覆寫。新 packet／phase bindings／完整 owner chains／完整雙向 route 均0；全遊戲分母、completed total與百分比未知。PHASE1只有 static source/file/hash/PE/CFG/帳本，無 build/test/native/C++/API/VM/server/client/Lua/DB/import/migration/restart/deployment。完整 TW／CN／PC／web／WSS、numeric64／coin99999999999／qualified stack99 與凍結功能要求維持。
