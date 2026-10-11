# OrangeShop C2S BF 選取數量與 money 欄位，2026-10-06

原生 build SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。兩個 assert 原始字串、引用指標、有界反組譯與原始 bytes 封存於 `artifacts/integration/packet-connections-20261006/bf-orange-shop-money-quantity-v6.json`。本輪沒有建置、測試、客戶端執行或正式資料操作。

原生 `PMOrangeShop.cpp` 中，奇數模式48-byte列的 `+2` u16 在 `CF558` 路徑由 assert 稱為 `m_osgdSC.vi[iItem].money > 0`；偶數模式6-byte列的 `+2` u16 在 `CF5D6` 路徑由 assert 稱為 `m_ogdSC.vi[iItem].money > 0`。兩者選取時均計算「UI 顯示餘額 ÷ 這筆 money」，並將數量上限截到30。偶數模式還會用同 key 的後續列更新可選上限；奇數模式的後續列搜尋也會調整本地呈現值。因而列+2有原生命名為 money 的依據，但服務端仍需自行確定權威價格、餘額、商品來源與交易版本。

`CF7FD` 的點選處理在選取數量 `UI+9695E` 與上限 `UI+96960` 之間遞增／繞回；`D18C1` 的輸入處理將手動數量截到上限，並比較「所選數量×當前顯示 money」與 `UI+9697A`。`CFACF..CFAD8` 的共用準備分支把數量低8位放 body byte2；`CFB80`／`CFD7F` 分支再依模式1/3/5/7或0/2/4/6將 body byte3 映為類別1..4；bytes0..1是選取 key；bytes4..7是列+2 的 money u16 零擴充或重複列搜尋後的同欄位值。這給出 OrangeShop BF 候選格式 `BF | key:u16 | quantity:u8(1..30) | category:u8(1..4) | displayed_money:u32(高16位為0)`。

`RecoveredBFRequest::orange_shop_selection_shape` 現只解析這個候選；它不准入請求、不扣款、不發物、不發回覆。每日 dialog32 的 `BF | item:u16 | 01 | 01 | displayed_amount:u32` 可能與 OrangeShop 形狀在位元組上重疊，因此僅靠 BF payload 不能決定事務。必須由已發 EE/F3 列表、擁有者、當前介面模式與權威商品及餘額狀態核對。服務端現有一般交易 wallet 不能在缺乏證據下被視為 OrangeShop 的相同貨幣；目前正式來源沒有專用商品目錄或權威 OrangeShop 交易。新增完整雙向路徑0。
