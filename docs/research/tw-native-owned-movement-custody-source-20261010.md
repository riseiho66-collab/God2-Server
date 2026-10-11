第239輪只推進台服一般移動2E→同庫位置與背包見證→原5D／周邊5E來源。新增 CUSTOM-0095 保存政策：從目前精確共同持有物品與完整1215-byte原始見證出發，在一次實際 SQLite outer transaction 內一起更新共同位置及見證位置／revision；所有物品ID、數量、取得來源、aliases、inventory revision與1215／DA15 bytes原樣保存。這是明示的自訂保存規則，不是重新取得原生afterstate，不能用來修補已過期／缺失的材料。

具體程式已接 actual Sources／StoredSources Context factory→NativeMovementHost→MovementSource→強持有 controller→SqliteOwnedEquipmentTransaction。強制相同 Application readers／writers／character repository、Session／lease／actor／root／完整old position，缺一拒絕且不回退。原本 native scene／Lua幾何／權威／完整5D與peer材料仍全部必要；沒有新增任意成功／空Action或猜回包。

交易在 Prepared／BeforeWrite 調用現有實際場景與peer Current；寫入位置後只用封閉的完整來源讀取核對，避免用仍處於舊位置的scene Current誤判。actual main位置CAS→完整inventory/native-old核對→native witness stage→完整next核對；一次COMMIT前配置同庫durable receipts。提交後核對當前receipt／Session／lease／位置，再沿用真scene publish和peer deliver。完整物品存檔不重寫，既有default-null／borrowed路徑不選此政策。

本輪修改10個C++來源檔，新增1個條件式來源串接增量；新增完整雙向路徑0，TW／全遊戲百分比仍未知。可見候選仍為TW C2S156、world S2C252有效值（230固定＋22變長）、battle110索引（9特別分派）；這些不能當完整玩法分母。仍缺真正持有物品／完整材料發行、正式Main來源接入、其餘玩法及phase/state/variant完整分母。沒有建置、測試、執行原生／codec／SQL、存取資料庫、遷移或部署。
