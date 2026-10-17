# 台服網頁客戶端服務端整合

2026-10-18使用者要求本服務端回歸只開發台服。現有WebServerPlan與gateway
僅接受下列兩條路徑，且只對應Application實際持有的台服原生端點：

| 路徑 | 原生角色 |
| --- | --- |
| /tw/native | Account/L |
| /tw/native-game | Character/world/G |

兩條路徑承載完整二進位byte stream。WebSocket message不等於原生packet，
gateway保留半包／合包、L/G獨立key、生命週期、背壓與控制frame處理；
不解碼或轉寫帳密、opcode及控制身分，不接受任意瀏覽器host/port代理。
Origin allowlist、輸入限額及正式WSS/TLS仍屬服務端責任。

原生PC與網頁共用同一C++/Lua權威核心、帳號、角色、SQLite存檔與世界。
台服繁簡文字顯示及CP950/CP936編碼邊界保留；玩家名字與帳密不可自動轉字。
現有前端專案由原分工維護，本次未修改任何客戶端檔案或訊息通知其他chat。

入口原始碼存在不代表Main已完整掛載、已可玩或已部署。完整台服入場、
場景、所有玩法路徑及集中原生驗收仍待完成。第一階段不啟動或測試服務。
舊介面與交接歷史保留Git及外部證據，現用契約以上述兩條路徑為準。
