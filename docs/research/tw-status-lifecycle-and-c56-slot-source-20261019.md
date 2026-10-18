# 台服狀態生命周期與C56格位來源（round461）

本輪接起C9狀態面板到C2S56的另一個真正原生producer，並找到包含三格
狀態快取的整塊初始化清除。新增mode2格位／identity一致性比對，保留既有
七位元組解析、旗標及Session傳遞鏈。沒有用UI快取推導技能權限、DoT週期
或原服傷害公式，完整玩法新增0。

## 現用來源與方法

EXE SHA256：`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
完整證據根目錄：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/status-lifecycle-round461/`。
使用既有REA6.5.0公開launcher及Ghidra；原始sections逐bytes保持，analysis
CALL不當作原始caller，分析映像未執行。UI v21的91個seed映像SHA256為
`52072799591fd62c4c59f5bcda717d1e78e4aa24be406d8c9f980f50f5a8347d`。
新外部helper先AST／語法檢查後單次執行，沒有新增專案Python。

REA Evidence：

- UI／queue三函數：`ev_a2dcd8d671f254486e05496eb10255dc2ed33b25aa82ef776d405ba77f61804f`。
- 初始化／clear五函數：`ev_8fb4373e43553c93ca9c231f5634bee7e284f5fe1523088a1e44a43a7131e510`。
- CA／CE／CF四函數：`ev_f9cd3439b4ae58d90bf8a614c35009117d2e23ac65cf46909dfc50c1cb6afb06`。

完整偽碼、原始指令、warnings與close外存，所有session已終止。全函數
偽碼不等於可達／端到端驗收；以下主張均限定實際bytes與所選CFG。

## mode2狀態按鈕發出的C56

4E8910先更新三格文字，再處理事件。mask02優先走關閉；只有mask02未設且
mask20已設，才進入本輪所選按鈕路由。原始兩層表4E8DA8及4E8DB8／4E8DC8
已展開，完整限定CFG343條指令、無剩餘間接停止。屬性分配controls20..23
是原有支線，沒有當成新技能公式。

controls17..19導向4E8CEC。此時原始地址為
`role+4364+20*control`，所以control17精確對應role+44B8，三者是既有三格。
4E8CFC要求definition pointer非空，4E8D0B要求entry mode==2。
4E8D46經4132E0發送C56：

```text
56 | WORD[[U+8688C]] | definition kind BYTE | definition id BYTE
   | BYTE(control-17) | 未寫入的第六body BYTE
```

這個WORD的namespace、ownership與server target仍未知，不能命名為已授權角色ID。
raw5=slot0..2只適用此producer；497A90的raw5另來自U+23D872，尚不能全面
當成同一種slot欄位。tail保持原樣，不能用作nonce、generation或權限。

## 長度假設已核對並撤回

起初看到此caller的`push6`，曾提出六位元組variant設計，**未實作**。
原始4132E0證明第三參數是body count：413320先寫opcode，413338／340複製
六個body bytes，41333F再將count加一並更新queue。497A90在497AC1也push6。
因此兩個producer均為**七個logical bytes**；不是新增六byte grammar。

舊設計保留在`source/c56-six-byte-source-design-v1.json`，獨立更正receipt
明記rejected hypothesis。沒有建立新parser／旗標，也沒有依剩餘長度或
下一個opcode猜分支。`ui/status-ui-events-v3.json`保留兩caller與queue原始bytes。

`RecoveredRoleSkillStatus::Record::matches_mode2_slot_action`重用原7-byte
Request，只比對mode2、caller提供的native slot0..2、kind/id及控制WORD。
它不比較unwritten tail，不保存或消費窗口，不授權事件，也不建立費用／效果。
caller仍須綁實際current entry、正確控制欄位與receive generation；同樣的
kind/id/slot不能使舊mode2通知跨過後續mode0、初始化或重連繼續有效。
獨立複核將403條所選指令逐bytes對回現用EXE，並確認11份parser／Session／
World來源檔與本輪起始hash相同。這是靜態比對，不是C++測試或遊戲驗收。

## 真正的清除與沒有發生的清除

C9的matched entry更新會保留definition pointer，改mode／value並刷新本地origin。
新identity只找pointer為空的三格；mode0及倒數到期不能擅自解釋成空格可重用。
4E8910到期仍只清文字，未清definition、origin或HP。

本輪將歷史round311的bulk reset以現用aaf0重新綁定，而非算成全新函數：

- named2A條件成功分支：465176形成R=W+1539683C，465194呼468160。
  468315取R+90，46831B令ECX=1141h，468320清EAX，468326 REP STOSD。
  原始範圍`[R+90,R+4594)`等於role的`[O,O+4504)`，完整包含
  C9三格`[O+44B8,O+44F4)`。
- NULL第一參數的本地初始化分支也以相同範圍清零：46817B→4688D0，
  4688D7／DC／DE設定count、zero與起點，468904 REP STOSD。

named分支須滿足原始name、接收成功、2A及map等前置條件；NULL分支不用
接收成功。不能把任意初始化、map transfer或登入都概括成必走此clear。
468160後面仍有468763 switch未全展開，所選clear前沒有未解跳轉。
這是client快取初始化，不是server永久技能解除、DB刪除或正式狀態過期規則。

精確role+44B8..44F4位移掃描只見C9與顯示readers，不能排除computed alias／
bulk writes。402EB5的push44C0另屬allocator size，不是role狀態地址。
owner+86888的constructor與指標替換也不能直接當clear；4A97E0與4A97A0是
不同entry。C8呼叫後者，不能借前者的role-pointer替換推論清除狀態。

## 相鄰opcode沒有提供持續效果公式

| opcode／receiver | 本輪限定證據 |
|---|---|
| C8／4A89C0，2B | 掃role+D8的3EC-stride identity，更新selected pointer／index並刷新UI；非C9直接clear |
| CA／480070，9B | 兩DWORD mask，更新數字代碼列表及36格快捷欄，必要時送A5／10B；代碼未資格化為技能或狀態ID |
| CE／480230，11B | 原始`C2 04 00`，只有RET4，沒有讀body；不能算已完成效果處理 |
| CF／46B30E，177B | 備份176B body，前172B複製到另一物件；world／network handoff與條件reset，非直接DoT量 |

CA頁數`trunc((count+19)/20)`是UI公式；CF另讀body+AC BYTE，末三bytes及多個
子函數仍未知。相鄰opcode本身不建立同一個技能生命週期。

## 來源與盤點界線

C56仍走原有default-off入口及Others，沒有真正status-action owner。
`observe_world_self`只是既有7-byte自我目標觀察，未找到caller，不能借作此格位
動作的學習、費用、once結算或回覆來源。C35與其他門檻也不替代本路徑。

本輪只更新已有C9/C56來源與未接通說明，沒有新parser opcode、完整玩法或
部署。唯一正式靜態盤點沿用v29分類；分母與完成率仍null，goal維持active。
命中／暴擊、傷害／治療／持續扣補量、攻防減傷及五行相剋／抗性仍缺真正producer。
中毒maxHP十分之一是使用者規則，沒有從UI倒數或清除得到其tick時機。
未建置、測試、target／VM／codec執行、遊戲DB SQL、遷移、啟用或部署。
