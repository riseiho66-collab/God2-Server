# 原生HP與傷害顯示位寬

當前安裝TW與固定CN角色面板的HP/最大HP**正數格式上限2,147,483,647**。
TW24→004E71E0完整存role+5C/+60→004E6DB0：004E6E27/2A讀兩個DWORD，
004E6E36/3F以584A24的`%d/%d`交005077C0。CN24→00518F70存相同role欄位，
00519052呼叫00519640；0051971A/24讀+60/+5C，00519727/30以7EF9B8的
`%d/%d`交00450B80。UI有窗口handle gate；未做當前畫面像素/血條驗收。

**傷害不能用單一值概括全遊戲。** 已恢復的單次HP增減飄字分支TW0052B48E
`movsx eax,di`→59D968 `HP %+d`→00547AF7。CN00563704附近及00567231..
00567243也有sign-extended WORD→7F5CD8 `HP %+d`→00415310。該類值範圍為
-32,768..+32,767；若以減血的負值絕對量看，bit pattern能表示32,768。
目前部分服務端qualified presentation主動拒絕loss>32,767，是現有來源
資格範圍，不把它當所有原生技能的共同上限。

CN另外有**累計DWORD飄字**：00562E30內00563054讀object+B60 DWORD，
005630A8..B2送同一`HP %+d`；00564450亦有類似多目標累計值。此格式可
表達signed32範圍，正值最大2,147,483,647；減血負值幅度可到2,147,483,648，
但不能因此斷言某個實際技能或封包分支可供應這個傷害。上游累加、動作、
場景/狀態與native frame/producer並未全部窮盡，全遊戲技能傷害上限仍未知。

TW00528A70對actor+DE8執行DWORD ADD後`jns`，negative sum寫零，並用signed
cap比較。HP擴充不能只改文字格式，否則戰鬥狀態仍可能在bit31處被清零。
角色面板、血條、單次飄字、累計飄字與服務端權威傷害必須分開擴充。

封存目前兩版EXE雜湊、bounded原始bytes/asm、format strings及CN metadata：
artifacts/continuation/numeric64-scope-20261007/native-hp-damage-display-01/evidence.json。
第一階段僅靜態讀取；未建置、測試、執行、改EXE或正式DB操作。
