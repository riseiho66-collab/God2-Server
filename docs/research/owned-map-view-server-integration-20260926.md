# 已持有區域地圖的服務端串接（2026-09-26）

## 正式實裝

發佈 `artifacts/releases/owned-map-view-20260926-01`，正式 PID31460／127.0.0.1:2592。
正式 EXE 與最終隱藏驗收03相同 SHA256：
`f071a1f7dfe59c0191af3979d6858dc80ca8a7ebf127e58dc0d99bff482f7ad2`。

- 已持有 SPI5576 在崑崙仙界4/3、SPI5569在楓華鎮2/4可透過原生背包雙擊25取得3F0100大地圖面板回應；可關閉後再次開啟。
- 這是 **CUSTOM-0044** 的區域准入／不消耗展示規則。25 producer與3F consumer有原生證據，但原服25→3F配對、區域使用範圍與消耗規則未還原，不能宣稱原生道具系統已完整。
- 不要求引導任務stage3，不使用舊diagnostic_town_map_replied一次性限制。原61場景轉移實驗仍分開保留，不能由地圖道具開啟此正式展示路徑。
- 只接受已認證、完成world tail／背包還原、CharacterSelected或InWorld、無待決轉圖的session。角色持有權由repository檢查；戰鬥狀態不接受。
- 整包須只有一個25、idle ticks、至多尾端1F00。混合搬移／其他操作、重複25先拒絕，不執行前綴操作。未知尾byte不當數量或授權。
- 格位0..29、相符item、count1、正revision與原始來源須全部成立。3F無地圖ID，使用目前場景選圖，因此驗證目前area/scene/kind及完整原始map row，避免開錯區域圖。
- 無新道具發放、任務進度修改、角色位置／資源／背包消耗。沒有自動向新角色贈送5576。

## 資料來源與持久化

Migration26增設native_map_item_sources/native_map_item_rows，transactional importer與C++唯讀reader完整比對來源、RowDesc、兩個原始SPI record的每個欄位。
正式SQLite另匯入144筆原生Map_City_Coordniate原始record與其來源。這144筆是地圖資源索引，**不是NPC、怪物或人物出生座標**。
兩筆SPI來源是SOURCE_DISPLAY_ONLY，不是20byte裝備instance，也沒有升級source flags為原始玩法授權。

啟用world.owned_map_views.enabled時，startup要求兩個原始item與2/4、4/3 map來源完整釘定；缺資料直接啟動失敗，不讓錯誤設定成為可用狀態。
已持有5576 scalar instance參照既有CUSTOM-0037新登入背包還原；不假造裝備metadata。背包展示可由此開關啟用，無須引導任務progress開關。

## 驗證與修正

- 來源importer：一般與-O各5tests；idempotence、失敗rollback、既存transaction、來源／flags／schema衝突拒絕。
- C++ source reader267checks；原始資料唯讀，破壞測試只改記憶體clone。
- C++ owned map3292checks：兩個原生區域row、所有256尾byte、格位30..255、非法數量／revision／來源、錯誤區域／原始bytes、整包grammar及錯誤account owner拒絕。
- Own-server TCP2cases：兩區各自連線／多次使用、尾1F00、錯ID／缺格位／超界、重複25、混合24搬移、重啟／再登入，所有已保存資料無變化。TCPpeer不是實機UI驗收。
- 首輪TCP發現混合25+24在較早inventory路由斷線；已將地圖整包preflight移到任何操作路由前，兩case再次通過。不消費25前綴，也不搬移24。
- CTest config/database/Kunlun/movement4/4；後續config/database/import_native_map_items/owned_map_view_server4/4。
- hidden God2Lab最終03，實際背包雙擊兩次，原生面板flags33→17→33→17，renderer handle11、場景metadata47/7/8，無backpack或quest修改；接著實際走動存檔4/3/126/128/revision2，時鐘繼續同步，client存活。native state checks，不宣稱截圖像素驗證。
- 正式套用verification：player_tables_changed=[]，quick_check=ok，client unchanged，僅設定owned_map_views.enabled增加；accounts/saves、Kunlun出生設定、NPC／monster native-only及所有其他配置保持。

失敗01只因測試fixture仍開啟舊map_probe而關閉quest_progress，觸發既有config依賴；fixture改關閉舊probe，正式配置未鬆綁。source migration fixture改用--migrate-only，避免要求尚待匯入的來源先啟動玩法。
02為中間候選驗收，03才是最終candidate及正式發佈依據。全程無截圖、桌面切換、client記憶體寫入；input desktop保持Default，source DB及兩個client SHA保持。

## 尚未完成

這輪不代表一般25使用、裝備28、技能書、地圖轉移、所有任務或NPC／怪物出生已完整。
原始新角色出生地图已為崑崙；精確原始XY仍未找到，CUSTOM-0040暫用126/126。
下一項按已交付的current-player-equipment-frontier-20260926.md追28普通武器34的完整owned metadata／after-state效果，不以單純背包搬移冒充已穿裝結算。
整體完成度維持約11%規劃估計，非量測封包覆蓋率。目標保持active。
