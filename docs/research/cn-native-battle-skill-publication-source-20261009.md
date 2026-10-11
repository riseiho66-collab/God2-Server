# 陸服原生戰鬥技能列表發布來源（第194輪）

本輪把實際已提交事件供應的陸服 S87 記錄，接入相同世界主機、共用技能目錄與原始收件連線的既有 held queue。新增三個 C++ 來源、修改三個來源，共六檔。這是來源串接增量；真正技能學習、戰鬥權限、原生規則、儲存事件發行者及 Main 選用仍未完成，因此完整雙向玩法新增為零。

## 原生入口及本輪更正

固定陸服映像 SHA256 為 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。原生 S87 logical3、body2；延後消費 case `5523F6..552408` 以 `H+A97181` 作 payload、`H+A89658` 作列表元件，直接呼叫 `554750`。它沒有經過 `54DEF0`。後者的 body+1 適配器是保留證據，其真正當前入口仍 OPEN。初始任務假設及193紀錄保留，當前更正另存，不覆寫歷史封存。

`552870`、`553220`、`552CB0` 是介面建立函式；`5540B0`、`5545C0` 是介面刷新 consumer，不能充當 learned-row materializer。Root 讀取六份完整 canonical C（包含 `54DEF0`），只作來源分類，沒有追入 GUI、字型、render、glyph、容量或停止鏈。

新的 `CnBattleSkillUpdate87::Record` 完整保存原 WORD：bit14 選 primary/secondary、bit15 保留列表狀態、kind 六位與 ID 八位。它只解讀已供應 bytes，不從欄位構造任意消息、不推定 actor/epoch/學習或施放權限。原 `CnBattleDeferredRecord` 長度表不變，以 static_assert 比對獨立 S87 header 的長度，新增 typed `skill_update()` getter，避免相互 include。

Native 代理的12 code spans／1164 bytes、410 instruction sites 與5 data sites／1674 bytes全屬保留證據，本輪不重計新原生覆蓋。History 代理新增完整 `54CFF0..54D021` wrapper 49 bytes：保存 ECX H、payload+1 到 `H+A89658` 的 `554200`；AX 按 signed16 判斷，非負才經 `[H+20]` 呼叫 `4D4E00`。Root另讀完整 C及全部19條指令。該 wrapper 的 incoming caller/phase 未限定，不能取代真正 S38/S87 dispatcher；另外六段438 bytes為保留證據。

## 實際來源串接

`SharedBattleSkillPublication` 以明確供應的 post-commit Plan 保存 actual event/revision、完整原始記錄順序及原收件 Lease；必須有真正 WorldOwner，才能觀察共用已學習事件、存檔／replay、battle/list/slot epoch、原始旗標、定義命名空間、資源及 native profile。沒有預設成功、初始技能發布、學習 mutation 或 TW CUSTOM 規則替代。

Factory/bind 不查詢目錄／資料庫、不送封包。永久 receiver 為 weak；實際 pending 保存 strong 原連線。首次 ready publish 才取得原始 private Token，要求同一 presence/transports、完整 Lease、原註冊及完整 common character root／saved position。若 Gameplay 選用 command-data configuration，publisher 必須與它共用 exact catalog、shared reader 與 actual store lifetime。

每次 borrowed 技能查詢前，WorldOwner 必須限定真正 store lifetime／reader／catalog 關係；查詢後重新核對。保留完整110B `NativeSkillRecord` 及其原始 provenance，而不把有該 row 當作 learned/grant。整批記錄先完整保存，再經 BeforeQueue、BeforeRelease、AfterRelease 的純只讀觀察與前後 full-root/current 核對，送到既有 `send_world_batch_with_publication`。真 transport 的方法定義只作靜態閱讀，沒有执行 codec、Asio 或 Windows API。

發布前已配置 qualified/unqualified 的不可變歷史 receipt。真正 local held-release=true 是不可撤回的本地事實，後續資格失效或取消仍保留，不能冒稱客戶端 ACK／學習權／当前連線。prepare 的 observer Stage 在真 send 前結束，approval callback 擁有自己的 Stage；busy/submitting 防外部重入，inline completion 延後到 send 返回後處理。若 send throw 而 callback 已記錄 true，仍保留 true 和 unqualified receipt，終止原操作且不重送。初版、修訂及此修正完整來源與 diff 均保留。

`SharedWorldGameplay::Sources` 增加可選 publisher，同一來源檢查後在 initialize bind；重入、拒絕、terminal 與析構只退休該 publisher 的 pending。publisher 不清理共用 Token／Lease／registry／核心事件、不找後繼連線補送，也不改已凍結聊天行為。一般成功批次不 release publisher。

## 計數與缺口

| 範圍 | 當前盤點 | 本輪增量 |
|---|---:|---:|
| TW C2S 已觀察 opcode 聯集 | 156 | 0 |
| CN C2S 已觀察 opcode 聯集 | 156 | 0 |
| TW S2C 世界長度表支援項目 | 252（230固定／22變長） | 0 |
| TW S2C 戰鬥索引項目 | 110（9特殊／101預設） | 0 |
| CN S2C 分階段項目 | 280（帳號6／世界206／戰鬥68） | 0 |
| TW/CN endpoint 紀錄 | 958 | 0 |
| 來源串接段 | 186 | +1 |
| 完整雙向玩法新增 | — | 0 |
| 全遊戲路徑總數／完成率 | 未知／null | 未確認分母 |

方向／opcode 聯集不包含全部狀態與 producer/consumer 變體，958行和186段不能作玩法分母。CN14 receiver contexts只有12限定；47DE70、4812B0仍未知。TW65 parser opcode中42已限定檢視（局部64.6%，不是全遊戲完成率）；兩版仍有未接入及部分接入的來源鏈。

接續追真正共同 learned/native grant、S86歷史、battle/actor/context、target/formation/range/cost、單次權威結算及完整有序 native replies，接上儲存與 Main 的實際供應者。S87旗標、目錄存在、選中技能或本地回位都不能代替這些規則。台陸網頁全部玩法、共用表、共用64位計算及明確擴充 wire/object/飄字、僅仙幣上限99999999999、合格stack99、原生等級／字型／繁簡轉換／凍結功能的完整目標保持 active。

依所有者要求，PHASE1 未建置、測試、原生／C++／Lua／codec／API／runtime 執行、DB／SQL 存取或部署，未重試155、52F330、52F170停止鏈。全面測試驗證在全部來源路徑接通後進行。沿用193網頁來源 ACK；本輪沒有新的網頁客戶端驗收或共同遊戲驗收。

交付原件、before1390、完整 prior193封存2605成員、Root六檔全文／diff、三代理各自完整來源與初版修正 epochs、容量與唯一 round report 均位於 `artifacts/integration/packet-connections-20261006/cn-native-battle-skill-publication-source-01`。讀檔定位及 shell 編碼／VA篩選錯誤另存 process note，不作原生函式不存在或執行失敗的證據。
