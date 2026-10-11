# CN WORLD34／35的實際連線輸出來源

本輪 `20261008-cn-world-subject-skill-publication-source`，PHASE1來源串接；
承接135輪完整4-byte格式及原生consumer，沒有新opcode或新native變體。

新增 `SharedSubjectSkillPublication`，要求實際共用表CN catalog與真正post-commit
owner qualifier。Plan包含實際recipient Lease、event ID、已提交revision及原生記錄順序。
reader確認每筆完整34／35 shape、Form/header一致及實際CN definition來源，
不把subject BYTE當common character／slot，不把catalog row當技能授權。
輸出大小沿用既有native transport max_logical，沒有自造技能選擇上限或新格式。

先觀察actual account／WORLD role／session／character offer／admission／ready Lease及catalog，
並由共同owner限定真正subject／技能映射、rules／save／persistent replay／event順序及新revision。
使用既有 `send_world_batch_with_publication`：transport持有bytes，queue acceptance時
在同game owner重新觀察實際committed plan及recipient，通過後才release。
所有記錄與definition副本留存到completion；沒有查退休的preborn window Current。
local last-attempt只限制同一連線的直接重試，不冒稱durable replay或全局單次結算。
concurrent／失敗走既有close與local completion，不回傳虛構wire成功。

`SharedWorldGameplay::Sources` 新增可選subject_skills；既有actual1C gameplay
publication在同Lease／presence／connection綁定此issuer，綁定不發送任何34／35。
實際common事件完成結算與存檔後，才可由真正owner呼叫publish(plan)。
尚未配置實際issuer／qualifier／common規則／save／replay／CN rows／Application，
所以這是條件式source接入，不是部署／原生驗收或完成玩法。
BATTLE同值opcode及TW輸出未提升為此路徑；跨版本語義與其他所有玩法仍需接通。

新增output source owner1、held publication path1、既有gameplay source binding1。
新增2個重疊WORLD34／35 phase-source關聯，unique不新增，完整雙向玩法0。
未建置、測試、native／C++／API／DB執行、遷移或部署；全遊戲分母與百分比未知。
