# 台服技能控制與施放角色來源，第244輪

本輪只推進台服技能串接。修改5個既有C++來源檔，將同一 issued-list
觀察中的實際戰鬥 actor／side 接到 C35 原始輸入及 WorldOwner qualification。
新增完整雙向玩法、opcode及部署皆為0；完整台服分母與百分比仍未知。

## 原生來源與限定範圍

固定 same149c 原件的5156E0 accessor，只有 A=`B+A9E9C38` 為0且
B=`B+A9E9C3C` 非0時回傳 BYTE `B+52`；其餘分支回傳 BYTE `B+51`。
它與5156A0選 primary／secondary 清單的 predicate 相同。回傳只確定AL，
不可把保留的EAX高位解讀成角色ID。

實際 action3 caller514040..514059將5156E0回傳值送進518E50 builder的
actor參數；此切片支持該支線的資料流，不宣稱所有UI／輸入變體已恢復。
5155BF..5155E9的技能目標設定 caller也使用同一 accessor。
這些來源都不是世界 Main+8688C local actor pointer，也未證明 actor slot
等於已選仙靈key。詳細原件、完整閱讀來源與切片保存在外部第244輪
`tw-native-skill-publication-source-244/agents/native`；舊封存不變。

S86/5固定 logical17。直接寫入子集如下：

| logical3 | 寫入 | actor來源 |
| --- | --- | --- |
| bit0有值 | A=1 | logical4低nibble → BYTE+51 |
| bit1有值 | B=1 | logical4高nibble → BYTE+52 |
| 對應bit無值 | 保留完整舊DWORD及actor BYTE | 不清除、不補0 |

其他flag bits不能當成clear。nibble14／15可完整保留；現有 owned C35
grammar採actor<14，是受支援域的限制，不能聲稱原生86/5拒絕14／15。
logical2及5..16保持原始值，沒有猜測time、duration或permission。

真117590還會呼叫115670／115740等UI與rearm helpers。本輪只投影上述
control／actor直接欄位，未投影完整consumer、時鐘、W或selected UI index。
原生 post-builder cleanup會優先消耗A、再B，並可能改W；未連線、未入隊
也可到達。故不能把收到C35、入隊、cleanup或沒有收到C35當成服務端
已接受／已結算的證據。其他86 selectors及cleanup仍需真正owner提供
完整當前替換，不由此子集自動推進。

## 本輪來源連接

`TaiwanNativePrimarySkillList::Snapshot`增加明確實際 primary／secondary
actor BYTE及最後一筆完整17-byte86/5；最後一筆不是完整歷史、grant
incarnation或native nonce。`apply86_control`保留未置位的完整DWORD與actor，
只投影直接寫入。PRIMARY lookup帶出同snapshot的BYTE+51與side0。

`SharedTaiwanIssuedSkillSource::apply86_control_from_issued`先擁有輸入，
保持真Session生命週期，再進既有 private previous-ticket replacement。
完整main／aux catalog、common lease、位置、battle generation及Session
身分仍須當前；local revision只表示記憶體來源觀察的新舊。

`SharedTaiwanNativeSkillCommandSource`要求原始C35 actor／side及真正
WorldOwner qualification都與同一 immutable issued Selection相符。
既有 action前current檢查與action後新durable receipt要求不變；不以舊
consumed ticket作action後檢查。沒有把actor自動轉成saved deity、learned
ownership、turn permission、MP扣費或完整battle authority。

## 接續缺口

真實一般native publisher仍未接入。既有common-world held sender僅允許
InWorld／CharacterSelected，而此registry要求InBattle；PRIVATE acceptance
sender與直接return Reply也不會發布此registry。需要獨立 battle sender、
實際queue／write生命週期、pending exact-slot拒選、取消及確切Current，
不能只新增工廠或把queued(true)當client ACK。來源位置與候選修改範圍
保存在同輪`agents/hosting/publisher-frontier.json`。

actor對真實selected deity的綁定、grant incarnation、native耗魔與規則、
once durable settlement、完整reply、secondary列表及普通Main仍OPEN。
本輪未執行build、test、compiler、runtime、native、codec、遊戲DB／SQL、
migration或部署。目標保持active，接續台服來源串接。
