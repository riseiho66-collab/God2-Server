# TW278：真正私人入場前階段與 PK 提交界線

本輪修正台服普通入場的實際 C++ 前置障礙：正常 bootstrap 保留 `CharacterSelected`，既有 PK appearance、preparation 與 Session hold 卻只接受 `InWorld`。新 CUSTOM-0116 讓每位玩家在真正私人初始化已 Written/current 後，各自捕捉當時的合法階段，並精確保留至 commit；沒有把整個普通世界流程強制升為 InWorld。

本輪沒有安裝 Application PK owner、執行戰鬥、增加封包或完成整條 PK 路由。Lua/shared Battle 結果處理、fresh 83/88 來源、later-round grants、terminal return 與全面驗證仍是後續依賴。全遊戲完成百分比仍未知。

## 實際缺口與證據邊界

Session 普通角色 bootstrap 的現有程式明確設為 CharacterSelected。現有 `normal_world_initialization_current_on_game` 已允許 CharacterSelected 或 InWorld，並檢查真正私鑄初始化、實際 game owner 與相關身份。這個雙階段契約原本沒有被 PK supplier/hold 正確承接，造成有真正普通入場憑證的角色仍被更窄的 InWorld 判斷拒絕。

Application 中有歷史註解談到移動後的階段，但本輪沒有證明普通移動實際執行 InWorld promotion，因此不把它當恢復條件。全域呼叫 set_state(InWorld) 也會改變既有精確 phase_at_restore 來源關係；這次保留原有 bootstrap 與世界階段行為。

本輪 native worker 是既有來源與 retained evidence 的唯讀審計，不是新 native wire 逆向或執行驗收。主要 receipt `agents/native/seal.json` 為 `b287556182cc856216805e6b42e7a79b69944622bb38c0decbbd9040cde040b5`，67 members／1,320,664 B；補充 `agents/native/supplement/seal.json` 為 `cdd739b153874b7f483446e7952a44bdd0053492280b98724044397a08ab32b1`，30 members／1,064,351 B。兩者保存於本輪外部 task archive `tw-pk-turn-owner-278`，不覆寫先前封印。

補充 receipt 也明確撤回主要審計中「PK departure 移除 presence 資格」的推論：現有 paired withdrawal 移除 visibility incidences，保留真正 ready lease/common identity。Presence 仍在，不表示技能 issuer 已合格，也不能據此斷言它必然失格；真正 actor/model/grant/WorldOwner 與 issued skill 來源仍須獨立建立。這項 erratum 不修改 TW275/277 封印紀錄。

## 三個實際捕捉點

`OwnedTaiwanPkAppearanceSource` 在鎖定真正 Session、驗證私鑄 NormalWorldInitialization current_on_game 與 entry_written 後，才讀取當時 phase。只接受 CharacterSelected 或 InWorld，並將它保存在私有 State 的 const 欄位；其 Current 後續要求同一實際 phase。這不是公開 Material 欄位，不新增 durable readset 或 caller provenance。

`OwnedTaiwanPkEntryPreparation` 同樣在每個真正初始化通過後，保存 per-viewer 的本地 phase snapshot。所有 callback 前後、Pair 再觀察、完整 supplier chain 與 reservation 前後的 session_current 都要求各自原本的精確 phase。兩位玩家可以分別處於不同的合法入場前階段；不要求兩人共同轉入某個人造階段。既有 immutable Pair、Session/帳號/角色/common lease/PK 世代與 current saved position 關係維持不變。

Session 的 `prepare_native_pk_entry` 先使用真正私人 normal initialization 的 game-owner guard 與 Written 檢查，再擷取 actual state，私鑄 NativePkEntryHold::Data 的 const prebattle_phase。Request 沒有新增 phase 欄位，caller 不能選擇或偽造此狀態；沒有新增公開 getter。

Preparing/Held 的 transport_current 要求 actual phase 等於該 private captured phase，而非每次寬鬆接受兩種之一。準備或排隊後發生 phase 變化，既有 current/close 路徑會拒絕，不能把新階段悄悄重新綁定。清理 abort 同樣要求原 phase 與原 battle generation，沒有呼叫 set_state 或額外升階段。這不是新增歷史 phase epoch/ABA 證明；現有 private initialization、身份與世代條件仍負責各自的來源界線。

只有既有 durable room activate 成功、兩端私人 hold 仍有效後的 commit，才把 captured prebattle phase 轉為 InBattle，並依原 Session 行為增加一次 battle generation。Committed/Released/Written 與後續 output proof 仍要求 InBattle、原 generation+1、真正 common/battle identity 與實際 owner acceptance，不接受 CharacterSelected/InWorld 作已提交替代。不得在 commit 後重用原 prebattle normal-current 作戰鬥權限。

## 檔案範圍與保留項目

本輪共五個既有 C++ 檔：`src/net/Session.h/.cpp`、`src/game/OwnedTaiwanPkAppearanceSource.h`、`src/handlers/OwnedTaiwanPkEntryPreparation.h`、`src/handlers/OwnedPkEntryAdmission.h`。實際行為改動限 Session.cpp、Appearance 與 Preparation；Session.h 和 Admission 只有說明文字，使註解符合 captured qualified prebattle phase。沒有新增 C++ 檔。

未改 normal bootstrap、Application dispatch/owner 安裝、普通移動、world/skill sender、held queue grammar、ACK staging、budget/deadline、input-prefix barrier 或 input/output fullwrite 流程。Material、原 readset bytes、schema、封包 bytes、Request、公用 phase getter 都沒有新增或改編碼。PK world_generation 與 common lease generation 仍是不同命名空間；本輪不以 phase 取代任何世代或私人來源證明。

已封印的歷史文件若將舊前置條件描述為 InWorld，仍保留作當時實作紀錄；本文件與 CUSTOM-0116 記錄本輪的窄修，不能偷偷更新舊 acceptance baseline。Frozen saves/auth/chat/IME/fonts/conversion/native clients/CN/web 與 shared64 數值目標維持原範圍。

## 靜態審查與 epochs

Worker 保留 Session 真正 before、首版完整 bytes、refinement2、diff 與 source notes。最終 Session.h 為 26,257 B／`189028bf01c28f5ce69d0927c7a0c1bf2d5dc0499d255415303dcbc62ccc4f67`；Session.cpp 為 184,945 B／`670202365214db7b9d4e4b262f0555dfa9586a3f0132b91a3417f20fa373317e`。

Session.h 原本混用 newline；首版到 refinement2 僅整理新增兩行註解的 newline，保留原有 bytes。早期 diff 生成將 before 以 universal newline 讀取、after 以 raw decode 處理，造成不相關 CR 顯示差異；該輸出與修正說明仍保留，`refinement2-semantic.diff` 對兩側相同正規化後只含實際窄修。不能將顯示雜訊當成 live 無關功能改寫，也不能隱藏首版 epochs。

Worker 實際閱讀範圍包括 Session 新/受影響 prepare/current/clean abort/commit/Written 路徑與差異、完整當前 Appearance/Preparation、Admission 註解、兩份 native/source findings、政策與新文件。沒有聲稱重新逐字審完 Session 184 KB 全部互不相關功能。獨立 reviewer 終端封印由 root 輪次報告外部記錄，避免文件反向引用造成循環 pins。

CUSTOM-0116 只 append 一筆：舊 113 筆及其他頂層欄位完整保留，總數為 114。沒有新增 opcode、完成整條路由或 gameplay phase association；唯一靜態帳務與最終五檔精確 pins 由 root account/report 記錄。本輪來源修正只解除已有 opt-in supplier/transport 的前置階段障礙，不等於已經在 Application 安裝、建立完整 Lua turn owner 或達到 TW100%。

PHASE1 未做 build/compiler/tests/runtime/native/VM/codec/game DB/SQL/migration/activation/deployment。後續仍缺真正 Application composition/initialization resolver、authoritative input 與同一 shared Lua resolver 的實際 hosting、fresh action/result 83/88 模板與 counter、later grants、終場存檔/鎖/世界返回、Session/restart/network recovery 及最後全方位測試與驗證。
