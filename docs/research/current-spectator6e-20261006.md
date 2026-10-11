# 當前原生 C2S 6E 觀戰控制格式與仍缺的生命週期

verified mapped image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。
`artifacts/integration/packet-connections-20261006/spectator6e-static-v1.json`
保存原 bytes、五個 `.text` 直接 caller、queue edge 及有界反組譯。
這是靜態來源工作，未建置、測試、執行客戶端或更新服務。

`97D40→97D66` 呼叫原生 queue `132E0`，排入 C2S logical9：
`6E, mode BYTE, raw stack BYTE×3, context DWORD LE`。
原函式只在 context 作 signed32 比較、非負時送出；它寫 body0
及 body4..7，body1..3 在此 producer **未初始化**，不能要求零、
解釋為權限或放進所有權查詢。

五個直接 caller 中 `66274/66642/7B738/DD02E` 傳 mode1，
其 context 來自各自已有的世界／UI選取。`1130A8` 在戰鬥
spectator state gate 下傳 mode2、context0。這能界定原生兩種
發送形狀，但不證明 server 的觀戰進入、退出、房間綁定、
戰鬥 participant 投影、離線清理或因果回覆。

獨立 S2C 6E 長度表為5，世界 dispatch 是預設分支 `6B517`；
不能因同號把它算成 C2S 6E 的有效回覆。實際觀戰視角需要
另追 battle entry、1C/83/86/88/89 等狀態生命週期。

正式來源新增 `RecoveredSpectator6E` 原樣 codec 和
`RecoveredWorldRecords`／`Session` 預設 false 解析旗標。
`Application` 沒有啟用它，也沒有觀戰權威狀態／回覆路徑；
本輪沒有新增完成的功能串接。原先「世界解析器之外」的6E
現已移入**已解析但功能未接通**清單。
