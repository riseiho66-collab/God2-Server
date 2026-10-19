# 三分流角色退場占用與隔離（2026-10-19）

本輪沿用 CUSTOM-0159，修補實際 Session／WorldLifecycle 清理的角色占用界線。這是自製的程序內保護，不是原服持久存檔公式，也不授予另一分流入場權限。完整遊戲分母與完成率仍為 unknown/null。

原先 visibility、native scene 或 Application 清理失敗時，Presence 的一般 release 仍可能讓程序共用角色 claim 消失；進場等待取消也可能早於 Session 的 disconnect cleanup。另一分流因而可能在舊角色尚未完成清理時重新準備同一角色。

## 實際接線

- SharedChannelCharacterOwnership 分開 active/current 與 occupied。私有 claim 的 None、Pending、Quarantined、Released 狀態不由網路欄位決定；Pending/Quarantined 持續排斥同一 full64 character 與 Session，包含來源 world unregister 及新 reservation 的 prune。
- SharedWorldPresence 從實際儲存的完整 Lease／私有 claim 發行 opaque TerminalRetirement。先標記 Pending 才配置 token；配置失敗仍隔離。普通 release 只移除原始 local entry，不放掉 terminal claim。正常釋放須原 issuer、registry、world、claim、索引與已 detach 狀態全部吻合，而且只成功一次。false、遺失最後 token、提早 finish、world teardown 不會自動解除隔離。外來 token 不改原始或後繼角色。
- 同步／非同步 SharedTaiwanWorldLifecycle 實際 prepared 都向 Session 安裝成對 begin/finish。finish 直接持有原 Binding，經過 Vault consume 刪除 Slot 也不依賴 id 重查。早期 release/cancel 在任何 scene cancel／owner cleanup 前取得或沿用同一 hold；cleanup all-attempted，錯誤永久保存。
- Session 在 GAME 一次取走全部回呼，begin → App disconnect → common cleanup → abandon。回呼銷毀與 full64 identity/phase/battle fence 後，才呼叫同一 finish(clean)；失敗或拋錯禁止成功03。實際 bound native active logout 缺成對掛鉤也不能成功。sticky failure 沒有清除 API，較早的錯誤不能被後來正常返回洗白。
- Application Vault consume 即使已移除 Slot，仍把 records/movement/cancel/stored cleanup/publication 的清理錯誤保存到同一 Session。
- SharedTaiwanWorldEntered 保留預先登記的 exact Session／完整 Lease cancellation record。原先 noexcept cancel 吞掉的 native/material/unpublished/visibility 清理例外現在保留且可由 explicit cancel 觀察；destructor 仍不拋錯。完成通知造成的合法 idempotent cancel 與真正未完成 cleanup 重入分開處理。

terminal 後 Current/ready/status incarnation 可正常失效；final finish 不要求已退休 scene Current。Visibility 的原始 incidence 先移除再進行外送，外送失敗不倒轉 local retirement。這不等於證明其他玩家已收到畫面消失訊息。

## 靜態檢查與界線

新增／擴充既有 C++ 測試來源：full64、同低32不同身份、錯誤／外來／過期／複製 token、detach、未完成／失敗／遺失、world unregister／prune、外執行緒最後 token drop、成對掛鉤半對拒絕、begin/finish 失敗與早期 sticky failure。這些案例本輪沒有執行。源碼獨立審查及 byte/EOL／patch 檢查不算建置或黑箱驗收。

隔離狀態只在程序內存在；沒有任意解除、持久復原或重新登入放行 API。清理結果不足、token 遺失及掛鉤未安裝的早期退場會保守保留占用，後續必須接有證據的 recovery。主程序重啟不提供持久隔離保證。movement 每步既有 commit 也不能當成其他系統已完整存檔。

尚待完成：PK 等保留狀態的持久復原、各系統 save qualification、目標分流 admission、Main 與完整 native providers、可信 Web G 選線、六向切換及原版台服客戶端驗收。沒有啟用或部署三分流。本輪沒有 build、test、native/codec/game runtime、DB SQL、schema、migration 或 import/export。

網頁客戶端由其專用工作樹持續移植；沿用 WEB_CLIENT_WASM_SERVER_HANDOFF_20261019.md 的 C++20／WASM 交接與手寫 JS 逐批退役規則。本輪沒有修改或提交客戶端。
