# 第229輪：台服遠端 DA 實際綁定與送包入口

本輪新增 `RecoveredTaiwanPlayerAppearanceUpdate`，獨立以同一149c原生映像的 DA15 格式持有完整實際來源 bytes；既有6bf fixture 介面保持原用途。`SharedActorVisibility::publish_taiwan_appearance` 接入真正的 private Binding、完整 Entry 觀察值、Session common-world identity 與 held queue。這是一個來源串接增量，尚未具備正式裝備交易呼叫端，新增完整雙向遊戲路線為0。

## 原生依據與限制

原生映像3174400B、SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`，沿用完整保留來源，沒有重訂舊基準。第229輪保留8段363B／114個指令位置及2個指標8B，新增原生覆蓋0。

6F consumer 的 payload+14h（logical21..28）先完整存入 actor250/254；payload+4Ch（logical77/78）存 actor262；logical79/80 對應 actor264/265。DA 的實際遠端4FC130只改每個奇位元組的高3 bits，保留其低5 bits與偶位元組；actor61 bit10 的特例還會跳過該保存動作。DA scalar5/6 對應264/265，但 DA transform3/4 是否寫入遠端262尚未證明。不能從同名欄位或舊預覽測試宣稱全部遠端快取已還原。6F 的低12位 actor identity 與 DA 完整WORD查找也必須透過實際綁定，不截斷共用資料庫ID。

因此本輪保留完整入場6F，新增不可變的「最近DA發布紀錄」。紀錄包含完整15 bytes、實際權威來源 revision 與 provenance，只代表發布歷史，不是假造 after6F／完整原生快取。舊完整 Entry token 比較該紀錄 identity，更新後即失效；移動仍只投影已確認的位置。重新出現／重新入場的完整6F必須重新由真正來源供應，不以舊入場6F或DA紀錄重播最新完整外觀。

## 實際來源接點

單一已出現的台服收件角色使用不可自行構造的 Binding，完整保存 before Entry、強收件 Session、座標、common-world generation 與 battle generation。必要的 `TaiwanAppearanceSource` 必須每次返回完整已提交 afterstate（DA record、正值且逐次增加的實際來源 revision、1..2048B且無NUL的 provenance），不能只返回 bool Current。Prepare、held publish 前、發布紀錄安裝後與 queue release 回呼均重新讀取並要求完全相等；所有外部讀取前後都重查同一個完整 Entry／transport／presence。

pending owner map 擁有真正 provider、completion、強 Session 及 registry keepalive；跨 IO 的 facade 僅持 weak registry、固定 key 與不重用 nonce。紀錄與 full after-token 在 IO 前配置，held publish 只安裝預配置紀錄，然後才讓 Session 放行 DA。實際 provider 的呼叫副本在 game owner 執行與析構。巢狀 publication 會令原操作失效；相同 pair 的 show、移動準備、完整移動集合與 advance 在 pending 期間拒絕。

hide、reset、release 會取消精確綁定的 pending；顯式 drain 用於 executor 停止前。取消入口及完成函式保留 owner 直到整個方法結束，避免完成回呼解除最後外部 owner 後使用已析構的 registry。drain 期間拒絕新的發布。未送入 IO 的準備失敗保留既有角色；已 issued 的失敗只移除原 incarnation 並關閉原 receiving generation，不能移除新 incarnation、重送裝備變更或回滾已 durable 的交易。

成功只代表本地 held queue 放行，不代表 socket 寫完、客戶端收到或畫面驗收。原生自角色 DA、完整TW/CN觀察者 fanout、CN格式與跨版本外觀映射不從這個單一TW入口推定；CN變體明確不適用，既有CN功能保留。

## 尚缺的完整路線

真正同資料庫的共用裝備 instance／slot mutation、完整 before/after row與來源revision、實際 item→12B外觀 afterstate、outer durable COMMIT 與此入口的正式呼叫仍未供應。原生規則／資源資格由該真正來源負責；字串provenance、DA解析或任意callback均不自動成為權威。入場baseline、舊6bf/c5d8測試資料與 SAVEPOINT release 都不能代替它。pending 必須在 executor 停止前 drain；正式 Application retain/drain／綁定及Main啟用仍為OPEN。

另有完整2A來源、once-Issued admission/lifecycle、13個世界玩法分支與全遊戲狀態／變體分母未完成。來源段214→215只是部分來源段累計；台服與全遊戲完成率仍為未知。本輪1個新增C++來源檔、2個修改檔、0條新增完整雙向路線；沒有建置、測試、原生／codec／遊戲執行、資料庫／SQL、遷移或部署。目標保持active，優先台服完整串接，再集中測試驗證。
