# CN billing 原生顯示變體與資源 owner

本輪 `20261008-cn-billing-presentation-variants-source`，PHASE1 file/source 靜態恢復。上一輪已交付共用 snapshot reader、CN stored Profile producer、catalog123 與 124-file source seal，分類為 progress。修改前保存 81-file before snapshot 及完整前輪 seal；不改寫歷史基準。

## 原生分派

固定 CN PE32 SHA `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。`00443FA0` 以 UI+7C 的 billing paytype 為基礎，只有實際所選 group 的 billing BYTE（UI+8D+group*14h）為 6／7 時才覆蓋它。這只是 UI 顯示來源，不是 server entitlement。billing record 仍是 S2C0A 的完整 16-byte payload。

`004442DD` 比較 paytype 與 9；9 以上先呼叫 `0053E3D0` assertion。若其返回，後續仍經 `004442FC` 比較 7。`00444305` 的間接 jump 使用 `0044445C` 八個 DWORD table cells。8 不呼叫 assertion，但跳到 `00444449` epilogue，這段 billing switch 不改 UI rows9／10／11；不能理解成清空、成功權益或第九個已命名 PayType。9 以上 assertion 的真實退出／例外行為未在本輪資格化。

|effective paytype|primary target|ProgramMsg label ID|billing rows9／10／11 的處理|
|---|---|---:|---|
|0|0044430C|321|月制 label；date 格式322；points 格式320；先检查限定日期 operands|
|1|004443CA|319|計時 label；date322；points320|
|2|004443D5|323|半日 label；date322；points320|
|3|004443E0|324|label，清空 date／points 列|
|4|004443E8|478|label，清空 date／points 列|
|5|004443F0|651|label，清空 date／points 列|
|6|004443F8|688|group override 可選此 label，清空兩列|
|7|00444400|689|group override 可選此 label，清空兩列|

只有 case0 檢查 signed year <0、BYTE(month-1)>11、day<1／>31。year0 不觸發這個 branch；原生 assertion 文字中的 `year >0` 不能取代實際指令。不檢查實際月長、閏年、hour／minute，也不證明日期是 server access deadline。cases1／2 直接顯示同一組 operands，不經月制的 assertion 條件。date 使用 signed WORD year、四個 zero-extended BYTE；points 使用兩個 DWORD 並以 ProgramMsg320 的兩個 `%d` 顯示，因此沿用有號解讀。

## 正確資源鏈

`00428C80` 的 `004294CB` 比對 `ProgramMsg` literal `007EE944`。該分支建立 resource owner+B2F60 的 4-byte pointer table；CSV ID 減1作 index，最大已載 ID 為 signed WORD owner+B2F64。這和 owner+B2F58 的 SystemMessage 16-byte row table 不同。

`00445040` 綁定 UI+16188=實際 main+464 的 resource owner。原生 `00886918` 的十一個 WORD ID 為 `[319,320,321,322,323,324,478,651,657,688,689]`，供應 globals `009EDDE4..009EDE0C`。每個 ID 需非零且不超過 resource maximum；否則對應指標為 null，不能假設這是當前已載入的 runtime text。`009EDE04` 的 ProgramMsg657 為另一個計時點數格式；本輪八個 case 沒有使用它，不能把它配成 paytype8。

沿用已封存 decoded `message.csv`，現讀 packed `message.csvZ` 的 hash 與原 receipt 相符，只解析 CSV，不執行 native／C++ resource loader。保留 ProgramMsg 與 SystemMessage 的同 ID rows 並明確標示不同 section。舊 `system-message-resources.json` 是 SystemMessage section，這些 ID 在該 section 對應其他內容，不能作 billing label 或 format；歷史原檔保持，另存被排除的候選來源紀錄。

## 來源接入與限制

既有 `CnAccountBilling` 新增唯讀 `presentation(actual_group_type)`，以 typed kind 和 ProgramMsg IDs 提供實際顯示 operands。完整 billing16、opaque byte5、原 paytype、日期及 points 仍保留；不建立缺失 profile，不改 paytype，不做日期轉換或格式化。既有 `SharedAccountSuccess::NativeData::Observation.billing` 已提供此同一 owned view，實際 Authority 可在既有 observation 中取得它；本輪未改認證、issuer、transport 或 callback 行為。

新增 display operand projection1、eight-cell primary dispatch qualification1、ProgramMsg label-source relation1。八個 case 加 default8／assertion>=9 是 consumer 條件範圍，不當作十個新封包、十個完整玩法或十條回覆路徑。沒有新增 opcode／phase binding／完整 owner chain／完整雙向路徑。正式 snapshot／權益／期限／catalog metadata／Application、全部世界與玩法、TW／CN／PC／web／WSS、numeric64、stack99 及完整分母仍未完成。

未建置、測試、執行 C++／原生／API／codec／服務，未讀 DB、遷移或部署。全部凍結功能、帳號存檔、認證、聊天、IME、頭像、字體、繁簡轉換、等級、客戶端資源及歷史封存保持。
