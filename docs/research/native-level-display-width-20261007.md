# 原生角色面板等級顯示範圍

目前TW與固定CN的角色面板等級正值欄位範圍到**255**，不是127。
TW004E6E13先xor edx,edx，004E6E15只讀role+26的一個byte至dl，再以5823B4
`%d`交005077C0的control5；高位清零，0x80..0xff不會在此路徑被當負值。
CN00519700直接movzx eax,byte ptr[esi+26]，0051970C使用7ED65C `%d`，
00519715交00450B80的control5，亦為zero-extended unsignedbyte。

TW原生22 snapshot的logical1 levelbyte由RecoveredRoleLevel保留；現讀
004E6B40前段把输入byte存到role+26。格式化範圍不等於官方最高等級、
經驗門檻或所有角色/寵物/怪物/戰鬥/UI分支都已資格完整。0是否有效等級
與其他gameplay限制未以此格式函式決定。超過255需同步擴充原生欄位、
儲存/升級/經驗表/比較及各consumer，不以% d格式本身改寬作完整升級支援。

原始bytes/asm、字串與當前EXE雜湊保存在
artifacts/continuation/numeric64-scope-20261007/native-level-display-01/evidence.json。
只有靜態來源恢復；沒有建置、測試、執行、改EXE或正式DB操作。
