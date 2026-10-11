# CN WORLD34／35完整格式與catalog來源

本輪 `20261008-cn-world-subject-skill-format-source`；PHASE1靜態來源工作。
固定CN映像582f2695。原生00567B50的長度分派中34／35皆回傳完整長度4；
WORLD0048FCC0兩個接收case把record+1分別交給004D5E60／004D5CC0。
134輪已保存這兩個consumer的完整局部normal-call-return CFG890B。
參數三BYTE依次為原生subject identifier、kind、ID，沒有新增旗標BYTE。
receiver length依據與原生table／分支留存；不使用S2C長度推定C2S格式。
BATTLE005485F0也有同值case，保留獨立階段標籤，本輪不掛載battle。

新增 `CnWorldSubjectSkillUpdate` 完整4-byte讀取及原生格式組合函式，
保存header及全部三個原始operand，不以原生subject byte充當共同角色ID／slot。
格式讀取保留ID0等語義不合格值；native assertion不是成功授權。
`CnPrebornSkillReferences::resolve_update_definition` 把該格式的kind／ID
接到133輪共用表CN dataset讀取程式，回傳owning來源記錄；不回退TW。
程式沒有傳送封包、授予技能、改存檔或安裝猜測的common publisher。

兩個WORLD S2C phase-format來源關聯新增，opcode值不新增；全部變體未完整，
共同技能／subject身份、資格、成本、规则、transaction／save／replay、實際sender、
recipient readiness及Application仍開放。完整雙向玩法0，全遊戲分母及百分比未知。
未建置、測試、native／C++／API執行、DB存取／匯入／遷移或部署；凍結功能保持。
