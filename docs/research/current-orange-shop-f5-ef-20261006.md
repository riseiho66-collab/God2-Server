# OrangeShop 相鄰 S2C F5／EF 更新，2026-10-06

原生 build SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。S2C consumer 的長度、WORLD 分派、有界 bytes 見 `artifacts/integration/packet-connections-20261006/bf-ui-list-receivers-v4.json`。S2C EE consumer `CE003` 的診斷呼叫與原始字串另封存於 `artifacts/integration/packet-connections-20261006/bf-orange-shop-identity-v5.json`：來源檔 `PMOrangeShop.cpp`，assert 表達式直接命名 `ORANGESHOP_GOODS_DATA_SC`，並以 `nKindNum+nSaleNum+u8LimitNum` 乘每列大小檢查 EE 封包。它支持把 EE 確認為 OrangeShop 商品資料；不能由檔名推出貨幣、價格、物件所有權或交易成功規則。

S2C `F5` logical 29 bytes，WORLD `69100→CE140`，body 開頭 u16 是變體。變體7將自身識別值放 `UI+97C84`，把 body+4 的 u16 與 body+8 的 u32 存到 `UI+97C88`／`+97C8C`。變體8寫入 `UI+97CA0` 及 body+4、+6、+8、+0C、+10、+14、+18、+1A 的各欄位。處理後若既有 `UI+97C88==1`，consumer 會清空 `UI+96978` 起的548 bytes，即 EE header 與最多90筆6-byte列。這是對 BF 偶數模式列表的狀態失效影響，並未證明 F5 是 BF 交易結果。

S2C `EF` logical 3 bytes，WORLD `69124→D19A0`，body u16 非 `FFFF` 時更新 `UI+9697A` 並刷新數字呈現；`FFFF` 則關閉相應 UI 控制。`UI+9697A` 同時在 C2S BF 偶數模式的數量門檻使用，因此 EF 是該門檻的一個可觀察更新來源。此 u16 的經濟單位與權威存檔欄位仍未證實。

正式來源新增 `RecoveredOrangeShopUiUpdates` 純格式 codec，保留 EF sentinel 與 F5 原始29 bytes；僅對 F5已定位的7／8變體提供有界輸出。它不接入 Application、不發包、不變更帳號或存檔。已知方向性關係是 `EE→6-byte列→BF偶數選取`、`F3→48-byte列→BF奇數選取`，以及 F5可清空EE列、EF更新偶數門檻。哪個 C2S BF 導致哪個 S2C、扣款與物件規則、失敗重試、持久狀態與 Lua 尚未恢復；新增完整雙向路徑0。沒有建置、測試、客戶端執行或部署。
