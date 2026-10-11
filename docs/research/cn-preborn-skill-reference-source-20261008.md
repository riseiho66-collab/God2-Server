# CN角色技能指標與共同catalog記錄來源

本輪 `20261008-cn-preborn-skill-reference-source`，PHASE1靜態恢復與來源串接。
承接133輪共用表適配器；不執行native／C++／DB或測試。

實際individual `004D5E60` metadata479B 與 `004D5CC0`411B 的入口normal-call-return
CFG完整，分別134／107 instruction sites、RET004D603C／004D5E58；沒有frontier。
WORLD `0048FCC0` 原生case34／35分別把收到資料的+1交给這兩個UI consumer。
這是既有原生接收分支的資料來源補強，不是新opcode或新完成玩法。

兩個consumer讀參數前三個BYTE作subject identifier／kind／skill ID。
004D5E60在同identifier角色中，以已保存定義指標的raw[1]／raw[0]查重；
新項目只在實際skill count小於100及非零ID時加入。
004D5F3E保存flags0，004D5F6C保存實際bank+kind*6E04+ID*6E-6A指標，
增加entry+1F0 count並處理原生page欄位及UI helper。
004D5CC0以同指標算式找既有項目，004D5D88將該項flags設為3。
這只說明上述UI分支的旗標寫入，不把0／3命名為可施放、已授權或伺服器成本。
也不是對其他原生技能狀態WORD／bit14／bit15格式的證明。

新增 `CnPrebornSkillReferences`，對**可選的實際native recovery snapshot**，
從retained bank及skill pointer整數差找出精確kind／ID／source offset，
再用133輪的實際共同表adapter取得owning CN `NativeSkillRecord`。
要求範圍、record對齊、宣告count、exact offset及Snapshot／catalog Current，
保留原順序、重複項、raw flags及來源Scope；不讀或解參考client memory。
來源pointer只用來恢復原生定義身份，不當共同gameplay skillID或角色授權。

既有 `SharedPrebornWindowSource::prepare_window` 在native Snapshot有提供時
串入此來源限定；未提供Snapshot的共同服務端操作仍不依賴玩家記憶體或虛構地址。
實際CN shared rows／binding／Application尚未配置，所以此來源程式尚未啟用。
共同skill／subject映射、資格、native Lua规则、save／replay／initial issuer及其餘玩法仍開放。
新opcode／phase／partial owner／完整雙向玩法0；全遊戲分母與百分比未知。
