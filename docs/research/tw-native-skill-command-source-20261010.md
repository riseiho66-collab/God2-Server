# 台服 C35 原始技能指令接入，第241輪

本輪只處理台服 C35 技能的原始碼串接，沒有建置、測試、執行遊戲／原生／codec、存取遊戲資料庫／SQL、遷移或部署。沒有修改網頁客戶端或官方服務。這個增量不代表整個 C35、完整戰鬥或台服遊戲完成。

## 實際來源鏈

新增 `TaiwanNativeSkillCommand` 將完整17 bytes保存為獨立 WireRecord。網路層只判斷固定格式，不讀技能資料庫，不把陣法的兩個 WORD 當目標遮罩，也不依網頁補零假設原生未寫欄位。原有 CUSTOM PK／diagnostic 解析仍是預設路徑。

`RecoveredWorldRecords` 的新解析分支只在實際安裝 native skill binding 後選擇。能力由 `SharedTaiwanWorldRecordSource::create` 的完整 dispatch／release／invalidate binding 導出，經既有 host plan 與 Application 傳入 Session；不是用設定旗標冒稱技能已開通。

Session 保存跨 frame 的83前綴與3終筆，檢查同一 actor／side／context／完整 operand、既有有界筆數與 timeout，禁止插入其他指令，網路與遊戲 executor 都要求 InBattle。新入口另外釘住第一筆指令的 battle_generation，暫存、完成後排隊到 game executor 都重新比對；context並非 nonce，不允許離開再進戰鬥後重解讀舊前綴。原始未寫 bytes 和重複選取保留。這只是輸入格式與階段界線，不是技能權利或回合授權。

Mixed dispatcher 在任何子處理器執行前複製完整指令，逐個完整技能序列分派，維持與移動、物品、聊天等原始順序，攔截發生在聊天 Others 複製之前。新 binding 的實際 release 與 active invalidation 一併傳遞。已有提交前綴失敗時不假裝整批回滾或重送，也不生成任意成功包。

## 定義與權威界線

遊戲 owner 使用實際 Application Context 的 NativeSkillCatalog，讀取完整110-byte定義及來源 tuple，再做同版資格解析。類型分開保存 ordinary mask、scope13／14／16 ordered 重複目標、scope17 self+friendly 單包 combined，以及 normal formation mode0 的整數 source／destination。scope5保留原生直接寫入的3FFF，群體樣板保留空位置bits，不裁成存活目標。formation大小只按5..13唯一source的幾何界限限制，不稱原生通用批次上限；實際assignment策略仍屬權威端。實際支援範圍與原生定點 bytes 見本輪 native 子代理封存。

NativeSkillRecord 的 WORD+42只證明客戶端 MP 門檻，不能充當服務端扣款。定義存在也不代表玩家學會。真正 WorldOwner 仍須供應目前 actor／學會狀態／回合 grant／資源／規則、一次結算與完整原生回覆。新服務端元件把這些責任接到 mandatory owner 邊界，沒有自動使用舊單 actor CUSTOM0086，也沒有猜戰鬥傷害、MP cost、S2C 或陣法 state9。

完整真 WorldOwner 實作、learned／grant／cost 發行者、所有完整 native reply 與普通 Main 選用仍未接齊。因此本輪只能記為有明確依賴的來源能力；新增完整雙向玩法0，不能計台服100%。kind2 mode1與 alternate技能供應仍未資格化，不以 main S34代替。

## 來源與帳本

網頁端 immutable receipt 原文54,128 bytes，SHA256 `11e35daa88af2b428674d0a0075f4ff34c83960deaef84cd38315f0275a4265e`；本輪另外對同149c原生映像做 bounded 靜態來源比對。完整 before／final 原文、定點來源與每輪帳本在外部 `C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-skill-command-component-source-241`，歷史第240輪封存不改寫。

TW已觀測 C2S156、世界 S2C252有效值（230固定、22可變）、battle110索引不因本輪增加。opcode、解析器、條件式來源段不作全遊戲分母；完整 phase／state／variant／deferred 路線分母與台服整體百分比仍未知。後續優先補真權威處理與完整回覆，再推進其餘台服缺口。
