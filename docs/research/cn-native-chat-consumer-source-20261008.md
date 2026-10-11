# 陸服聊天到台服接收契約與實際來源生命週期：第180輪

本輪維持目標 active 與第一階段來源串接。所有遊戲路徑接好前不建置、逐項測試、執行原生／C++／Lua／codec／API／DB／SQL、驗收或部署。全遊戲 TW／CN／web、64位元數值、stack99與既有凍結功能保持完整範圍。

陸服 `SharedWorldGameplay` 的實際聊天 ingress 原先送給台服收件者時，仍手寫完整5C形狀、使用254-byte文字域，並用語系 bit 選CP936／CP950。本輪接入第179輪的只讀 `RecoveredTaiwanChatConsumerContract`：讀完整 supplied record、保留前13-byte header與全 actor DWORD，八種已確認 plain channel採整段 text252 bytes，再扣原始名稱／prefix／suffix。正文才做逐收件者繁簡呈現。收件者 supplied codepage 欄位必須明確、有效並由實際 source owner資格確認；native consumer tag保持其自己的資格，不再代替 wire encoding。特殊 consumer與未知 fields 不補默認。

`SharedNativeChat` 實際 WorldOwner 從 borrowed reference 改為 strong shared ownership，實際 `SharedWorldGameplay` 呼叫同步傳遞原本已持有的 `sources_.chat`。不新增空的權限服務、不從凍結 CUSTOM handler借用默認遊戲規則。真正 full lease／common delivery、saved position、TW phase與battle generation、CN admission、actual recipient transport及每個 owner／visibility callback前後的來源資格仍需符合。

找到的另一個實際 gap 是遊戲 callback返回後未重新核對來源。`CnTransportSession::close`立即設定close_requested旗標，`closing`亦立即可見；socket與OnClosed清理才延後執行。舊chat在某些owner／visibility callback返回後，尚未再次核對便繼續嘗試send。本輪由outer gameplay保存同一個chat來源的實際失效callback，在active-batch拒絕時先通知再關閉，並於每次callback前後重新核對；chat自身失效後不能继续後面的發送。這是目前ongoing-chat呼叫鏈修補，不代表全部初始化／其他遊戲來源都已覆蓋。

共用權限研究顯示：既有 OwnedPrivate／Party／Guild chat分別帶有CUSTOM-0073／0074／0075，NativeParty為CUSTOM-0062。它們的角色ID窄域、TW online registry、admin配置guild會員、CUSTOM prefix與原生mode3 UI，不能直接當CN權限或完整chat actor映射。真正可共用的現有來源包括64位元帳號／角色ownership、原始name_profile／name_codepage及 `SharedWorldPresence` 完整tuple／generation／ready lease／saved position；它本身不供應公會／組隊名單、whisper lookup或原生完整5C issuer。

原生接收端研究按實際欄位使用範圍保存；已保留的 producer／consumer／UI gates不重算新增函式、封包或遊戲路徑。沒有現讀的native input不得以receipt冒充原件；完整 current sources、native originals、before、intermediates與derived分開列。

本輪CN欄位對照保留world5C366 bytes與battle5C68 bytes，共434 bytes、四項既有關係；新span／bytes／relation均0。world0／6讀actor DWORD+05，party1／guild3／named2／9只向既有consumer傳channel與text；battle讀BYTE+09與text+0D，不與world actor domain混用。header3／4／10／11／12僅在這兩個限定case的直接operand中未讀，不能宣稱callee或全遊戲不用。自身actor來源+1478084仍未資格確認，不能拿peer low12映射替代。共用權限代理保留17份完整實際C++輸入、70個來源位置與7份原文摘錄；native inputs保持空。

| 目前索引／本輪增量 | TW | CN |
|---|---:|---:|
| C2S opcode索引 | 156（151一般＋5補充） | 156 |
| S2C有長度定義的opcode／階段項目 | 252（230定長＋22變長） | 280（帳號6／世界206／戰鬥68） |
| 新opcode／phase binding | 0／0 | 0／0 |
| 新完整雙向遊戲路徑 | 0 | 0 |

四個既有C++來源實際變更，來源紀錄171→172。958 endpoint rows／28群組／30 battle action-selector entries不重計。全遊戲分母、完整已接通總數與百分比保持未知，`Main`尚未選用新的native方案。

仍需接上真實channel-specific membership／whisper identity／audience／rights／mute／rate、完整native header與loaded destination來源、真正entry與Application選用，以及其餘所有遊戲路徑。仙幣99999999999、其他上限另定、等級不改、共用資料表預設、必要例外尾_tw／_cn、原生字體／繁簡轉換、存檔／認證／IME／頭像等要求維持。

fresh before1290 SHA256 `b82c93aba7604dd3ad4e107013068220b364836f36c1a37057bd1bd55d3097f7`；修改前完整核對第179輪2226封存成員，原封存與基準不更新。四份原始及四份最終進度報告分開保存。未重試先前被安全工具停止的第155輪formatter／capacity鏈。
