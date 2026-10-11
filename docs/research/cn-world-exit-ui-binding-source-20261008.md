# CN 退出 UI 綁定與 A0／A3 旗標來源

本輪 `20261008-cn-world-exit-ui-binding-source`，PHASE1 靜態原生恢復及來源增量。前一個狀態回報未新增成果；既有127封存維持，104檔 before snapshot 已在本輪修改前保存。未建置、測試、執行 native／C++／API、讀寫 DB、遷移或部署。

原生輸入為固定 CN `God2_opt.exe`，SHA256 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。僅使用原始 VA 的 FileView／PE32 指令與個別函式恢復檔；未使用21xxxxxx映射別名或整份反編譯巨檔。

## 三個有條件的旗標寫入

`0048FCC0` 讀原生記錄 opcode，再經 `004929D8` 表定位 A0／A3。兩個分支傳入 record+1，ECX 都是同一 world+89B26C。A0 cell `00492C58`→`0048FF27`→`00534D10`；A3 cell `00492C64`→`0048FF7C`→`00533430`。

`00533430` 直接寫 owner+8AC=1。A0 則讀 BYTE(*(owner+430A8)+D4)：只有非零才清理8B0／C3C／A48的400 bytes／C40／D20／8A8，設C44=1，將兩個payload bytes分別寫F74／F75，呼叫00534640，正常返回後寫8AC=0。零gate不作這些寫入；不能把UI/resource gate解釋成server權限或實際退出理由。00534640的完整副作用仍待追。

初始 `004AC850` 以同一 ECX 呼叫 `00534320`，後者設8A2／8A4／8A8／8AC=0。這與收件後A0、A3，以及上一輪004AE370的post-tail讀取屬同一具體owner lineage。A3寫1後，**只有後續四個tail callbacks完成時实际8AC仍為1**，才覆寫command=-15→world5→main4；該main分支沒有本switch的020x傳送，並走外層登入UI分支。不能省略callbacks或把A3直接當成C2S02的請求／回覆配對。

`00567B50` 的 primary 表 `00567CA4` 中 A0 cell `00567F24` 與 A3 cell `00567F30` 都指向00567B69，回傳**完整logical length3**。A3 callee忽略payload不代表原生包長1。新增 `CnWorldExitLifecycleControl.h` 精確讀兩種3B記錄並保留全部原始bytes；只提供正常consumer返回之後的條件式8AC寫入投影。沒有原生server issuer、猜測payload或正式權威handler。

## UI 資源與同一 owner

`0048CAA0` 取 world+8885C4 的main物件，使用 **LEA main+464**，不是讀main+464指標，保存至world+A69F20。此地址經堆疊15-DWORD陣列第8項傳給004AC850，寫同一owner+65364；既有124的ProgramMsg loader已定位該resource class的+B2F60／+B2F64。

`005277A0` 從 primary WORD table `008A3638` 讀62／63，檢查非零與不超過signed resource+B2F64，取一基底4-byte pointer table+B2F60，寫global009F1058／009F105C；超出範圍原生置NULL。固定message.csvZ及既有解碼receipt保留，CP936的**ProgramMsg** 62是「确定」、63是「取消」，不是相同ID的SystemMessage區段。

`00527650` 呼叫00451460並把真正返回AX寫owner+1C8544，item2／3分別綁上述ProgramMsg指標。`00527D80` 設43088=1，把另一個真正返回AX寫owner+1C84AE，item2／3使用image22/23、24/25且text指標為0；沒有猜測這組圖片的文字、handle初始值或完整啟用／銷毀順序。原生字體、資產、繁簡轉換及客戶端二進位不改。

## 計數修正與缺口

reporter改以目前ledger的direction／phase／opcode tuples計數。`--catalog` 同時要求catalog保留的source-ledger與當前ledger逐byte及SHA一致、四項phase計數一致；舊ledger catalog114指標僅作歷史記錄，全部舊報告不覆寫。原始新報告仍另存，不手動改76／56為新成果。

第一次report產生後，靜態閱讀發現未提供`--catalog`時本輪會明確記錄null，但下一輪歷史相容分支會對null呼叫.get。追加兩個null-safe歷史讀取；原始reporter來源、catalog128與report全部保留，另建`endpoint-catalog128-final`及`20261008-cn-world-exit-ui-binding-source-final`原始報告。修正前後phase計數與玩法成果均不變，未執行測試或report缺少catalog的測試案例。

新增readonly3B格式reader2、旗標writer cases3、兩組UI handle綁定及ProgramMsg來源關聯。這些端點早已在CN盤點中，因此新增opcode／來源phase binding／owner chain／完整雙向路徑均0。真正A0／A3 sender／條件／兩bytes語義、state6 producer、早期signed-WORD returns、03 payload、退出規則／save／replay／Application仍開放。TW／CN／PC／web／WSS、所有玩法、numeric64、背包99及全遊戲分母維持完整目標；全量完成後才集中測試、修復與發布。全遊戲total／completed／percent保持null。
