# 台服原生聊天型別與接收欄位來源：第179輪

本輪繼續第一階段來源串接，目標維持 active；未建置、測試、執行客戶端／服務端、codec、API、DB／SQL，也未部署。三個子代理分別完成台服接收契約、台服原生聊天來源及陸服原生呼叫欄位。既有封存、凍結聊天、帳號存檔、IME、認證、頭像與客戶端保持原件。

既有 `RecoveredWorldRecords` 對 `2F` 已產生四種不同型別：普通、Private、Party、Guild。新 dispatcher 前一輪只接普通 Request，本輪明確將私訊2／9、組隊1、公會3接到同一原生聊天來源；完整複製四個原始 header bytes 與原文，不把 opaque WORD 當角色ID或權限。型別與實際 selector 不一致時不可轉交其他 handler。整批 chat request 複製與分段在實際遊戲 callback 前完成；其他 request 保持最大連續區段、sender 輸出順序、兩個來源的 cleanup／invalidation。原解析器與凍結 handler 不改寫。

新增只讀 `RecoveredTaiwanChatConsumerContract`，保留完整 supplied native `5C`、actor DWORD（offset5）、channel／tag（offset9）、前13 bytes header 與 offset13 text。`SharedTaiwanNativeChatSource` 的實際輸出準備直接使用此契約，保留所有 opaque header 與原生名字／控制 prefix／suffix，僅转换正文。台服已確認 plain channels 0／1／2／3／5／6／8／9 的整段 text 上限252 bytes；各收件者名稱／prefix／suffix 必須扣除。board、structured、13／18及其他 consumer 不套此容量。

原生 `475E00` 先把 wire 0／8映射 selector0、1→1、2／9→2、3→3、5→5、6→6，再進入 `47DE00`。wire8／9不是原始表的第8／9欄。原圖的 literal 是 ASCII `1Ax`，實際 `47DC66` 初始化把每個四-byte slot 首 byte 改為 ESC；只讀契約提供 selector metadata，不能輸出原圖 label 冒充 loaded material。256-byte local buffer 扣除三-byte prefix 與 NUL 得252，但真正 loaded window、history、line capacity、renderer、resource generation 與特殊副作用仍需實際來源資格。

台服代理新增4個完整函式及1個有界 UI caller（1130 bytes），連同10段既有 context，共15段6363 bytes、93個精確指令位置與13份資料。新增完整範圍包含100-byte prefix initializer、20-byte local tab predicate、776-byte tab setter、21-byte auto-reply accessor；213-byte private-target UI caller另列有界區段。client tab、target pointer 與 UI gates 不是服務端會員或發送權限。特殊 GM 與 named-whisper 可能共有 channel2／WORDFFFF，真正 input provenance 必須另有來源，不可只由 header 猜定。

陸服代理新增三段 code 共524 bytes：兩個實際普通 UI argument transfer（25／20 bytes），以及479-byte generated-template caller。普通 UI 使用實際 body、可選 target、channel argument0、opaque WORD0；generated-template row0x26C／literal `~` 使用 WORDFFFF，不能當普通 UI 或組隊／公會權限證據。完整 prefix switch table118 bytes，其中8 bytes已由舊 producer保存，只有110 bytes是唯一新增資料。三條新關係不增加 opcode、phase 或完整遊戲路徑；先前完整 producer／auto9保留且不重計。CN receiver14／qualified12、47DE70與4812B0未知phase保持不變。

| 目前索引／本輪增量 | TW | CN |
|---|---:|---:|
| C2S opcode 索引 | 156（151一般＋5補充） | 156 |
| S2C length-supported opcode／phase entries | 252（230定長＋22變長） | 280（帳號6／世界206／戰鬥68） |
| 新 opcode／phase binding | 0／0 | 0／0 |
| 新完整雙向遊戲路徑 | 0 | 0 |

新增1個、修改3個 C++ 檔案；實際新增3個 typed chat caller 分支、1個只讀 consumer 契約與1個來源使用位置。来源紀錄170→171。958 endpoint rows、28群組、30 battle action／selector entries不重計；全遊戲分母、完整已接通總數與百分比仍未知。

目前仍缺真正 channel-specific party／guild membership、whisper identity lookup、權限／mute／rate／state、完整 native5C header／audience、sender cipher、loaded sink 資格及 Application 入口供應；`Main` 尚未選用此新方案。不得以同圖廣播、全零 header、默認 cipher 或 client gate補齊。其他全遊戲路徑、64位元TW／CN／web儲存與線路／物件／飄字、qualified stack99全部 mutation callers、web WSS／TLS／hosting持續在範圍內。仙幣99999999999、其他數值上限另定、等級不改、原生字體及繁簡轉換保留。

fresh before1285 SHA256 `84ef1dbd91fc9cf22107e947a2630b274a6b8169f5ee457be5f81a15ac6a33f7`；先前第178輪2258個封存成員在編輯前完整核對，未更新舊基準。三個代理的實際 original inputs／stable current originals／before／intermediate／derived 明確分開保存；代理未新讀原生圖時 input list保持空。根代理保存完整變更來源與目前定義閱讀紀錄；四份原始與四份最終報告各別封存。本輪未重試第155輪被安全工具停止的 formatter／capacity 鏈。
