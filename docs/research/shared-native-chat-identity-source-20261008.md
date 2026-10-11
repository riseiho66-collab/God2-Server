# 台陸原生私聊共用身分來源：第181輪

本輪新增兩個、修改六個 C++ 來源檔，將共用在線角色姓名觀察接入實際 CN 與 TW 原生私聊呼叫。來源紀錄172→173；這是局部來源串接，新增 opcode、phase binding、完整雙向玩法路徑均0。全遊戲路徑分母、完成數與百分比仍未知。目標保持 active，全部來源串接後才集中建置、測試、驗證、修復與發布。

`SharedWorldPresence::ready_characters()` 先複製同一實際 registry，再透過原有 repository 介面讀取 active lease 的完整角色 root 與實際存檔位置。完整 session/account/character/generation 保持64位元；pending 只參與 registry 一致性，不能成為在線收件者。每次 virtual observer 前後核對 registry，並重新讀取完整人口與所有 root/position。缺少或重複所有權、讀取期間重入或變更使整次觀察失效，不把失效角色偷偷視為離線；既有 lease 操作行為保持。

新 `SharedChatIdentitySource` 持有同一實際 presence，先深拷貝原始目標名字與明確 CP936/CP950，再取得上述完整人口。共用 root 名字沿用既有14-byte存儲契約，stored codepage0僅允許不變ASCII；936/950嚴格原文往返，不採繁簡轉換、正規化、大小寫折疊、裁切、替換或預設編碼。不可變 Lookup 保存完整 root、位置、lease、原文與同來源 capability；Matched／NoReadyMatch／Ambiguous／UnqualifiedTarget 分開，current 重新核對整個觀察。NoReadyMatch 只表示當下共同在線人口沒有匹配，不證明全域或離線不存在；任何結果都不授予 actor mapping、權限、會員資格或回覆。

CN 的實際 `SharedNativeChat::dispatch` 使用原始 target/CP936 查找，將不可變觀察傳給真正 WorldOwner，並在既有來源、收件者與 callback／發送前後核對 current。TW 實際 source 在 WorldOwner::input 提供原生 ordinary/whisper 來源、明確編碼與精確 body boundaries 後填入觀察；input 不得自行塞入本 source 的 proof。TW 僅核對 retained private2/9／`$target` envelope，不冒稱已恢復完整 body grammar 或猜 whitespace trimming；真正 input 仍須提供資格完整的 body。Sender cipher、有序回覆、peer transports、完整5C header／prefix／suffix保持既有來源責任。

台服子代理從實際 pinned native image 找到：既有6F first name →完整DWORD actor lookup4FC960→新 getter4FAC70→bounded466EC4→47DCF0 私聊目標；typed getter4165D0由4B2A90供15-byte+NUL限制。History50F1C0使用72-byte slots，接受strlen<72。Peer stride是0x268，也就是616十進位，先前探索訊息的268十進位保留為歷史更正。19個指令範圍3901B，其中新9完整／3bounded共1439B，另7 retained；54 instruction sites、2 jump tables、104 C++ sites不是封包新增數。

原生15-byte目標、history、手動輸入、收到的文字與 common14-byte 名字屬不同來源範圍；本輪不裁掉第15個 byte 來製造匹配。實際 issued peer/name publication必須另行綁定完整共同lease、原始名字／codepage與原生ID。原生WORD、actor DWORD、peer低12位元不能充當 common64 ID。Matched 也不能直接決定私聊收件者。

陸服子代理保留6個已恢復 native name/cache/D3/UI transfer ranges404B，沒有新增 native spans／bytes／relations。CommonIdentity 和 NativePromptMarker 必須按既有 native-summary metadata來源分別處理；`%…%` selection prompt不是全域名字禁令或ready alias。NativeSummary的scope／character_ids／account_snapshot／current仍private，D3 pre-mutation NameIdentity不能代替ready lease。完整PE、實際TSV/C、source originals、derived ranges及讀取當下mutable contexts分別保存。

| 保留盤點，本輪未增加 | TW | CN |
|---|---:|---:|
| C2S opcode值 | 156（151通用＋5補充） | 156 |
| S2C紀錄 | 252長度支援值（230fixed＋22variable） | 280phase/opcode entries（account6／world206／battle68） |
| 新opcode／新phase binding | 0／0 | 0／0 |
| 新完整雙向玩法路徑 | 0 | 0 |

958 endpoint rows／28 groups與30 battle action-selector frontier entries保持，皆不能當全遊戲功能分母。實際 native issuer/name namespace、私聊權限／mute／rate／native回覆、群組會員與收件名單、完整 header／loaded sinks／cipher、entry／Main掛載以及全遊戲其他玩法仍OPEN。不得拿 TW CUSTOM0073/74/75/62 的窄ID、registry、guild維護或formatter當CN原生權威。

Fresh before1294 SHA256 `56754835636d95dd9ddbdd5a716c910391ea77f3b33dec8235918b42c3e5dcfc` 與完整上一輪2249 sealed members已在修改前保存並核對。八個最終完整 C++ 原件、root初始／中間稿、實際完整來源 contexts、三代理 seal、四份 raw/final報告分別保存，舊基準不改。

本輪只讀寫靜態來源與證據：未建置、測試、執行 native／C++／Lua／codec／Windows API，未存取DB／執行SQL，未更新正式服務／部署，未重試先前被停止的155 formatter／capacity／render／glyph研究鏈。TW／CN／網頁完整遊戲目標、64位元數值、仙幣99999999999、qualified stack99、等級不改、共用表及必要_tw/_cn、原生字體與繁簡轉換、帳號存檔／IME／認證／頭像／凍結功能全部保留。
