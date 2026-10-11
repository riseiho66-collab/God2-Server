# 原生帳號目錄延後取得與發布有效性（20261008）

本輪修改 SharedStoredAccountProfileSource.h/.cpp、SharedLoginComposition.cpp、SharedIssuedAccountSource.cpp 四個實際來源。這是 M2 原生帳號來源與正式傳輸邊界的接線，沒有新訂 gameplay、CUSTOM、opcode 或目錄數值。

監聽服務先 bind、建立 controllers，再 start；registry 在 start 前不可 observe。因此 with_active_directory 在建立時只保留實際 Prepare、同一個監聽 registry、已選定 client configuration，以及 game thread。compose_native_login 選用 stored_issued_account_source 時，先完成來源衝突與 snapshot repository 檢查，再把該 Prepare 包裝，最後才呼叫原有 create。建立工廠不取得 active snapshot，也不提早執行 Prepare。

每次帳號準備由同一 game owner 執行；busy guard 阻止重入，RAII 在失敗與例外時還原。取得真正 active snapshot 後才呼叫實際來源，回來後重查 snapshot 是否有效。完整 raw catalog 由原有 from_catalog 核對實際 listener 和 configuration，成功後放入有擁有者的 directory，清除互斥的 raw catalog。已有 directory 的形式保留原物件與來源，核對它仍有效、沒有另一份 raw catalog，並與實際 host/config 再次比對。缺少來源、目錄不完整、互相衝突或過期均不成功。

子代理另找出既有 issuer 的生命週期缺口：Prepared.directory 的 catalog 被複製後，原 Plan 沒有留在 Native::Current，後續只有 Context 的 directory gate。此輪在產生 key／複製 credential bytes 之前，以 shared_ptr 保留原 directory；Prepared、BeforeIssue、BeforePublish 都檢查其 current，後兩階段另核對實際完整 ordered04/05/06 catalog_records，真實 profile Authority 與 credential Current 之後再檢查一次。原有 Context gate 保留，所以兩個來源條件都需成立。沒有 directory 的舊形式沿用原流程。

原 create 的固定客戶端 snapshot、40B metadata、16B billing、revision、整份重讀與真正權限觀察均未改。原 native205B1D、17B0A、key policy、credential 身分、summary、deadline 及世界入口來源也未替換。目錄檢查對 enabled nodes 要求與全部 world binds 對應；disabled nodes 仍按來源序列化，只受原本 shape 條件約束，不能說每一 node 都有 host endpoint 權限。

有效性檢查覆蓋準備、issue 與 held BeforePublish。完成回呼依原流程釋放 request、credential references、Native Current 及 catalog，不增加送出之後的來源否決，也不宣稱可撤回遠端已收資料。stop 先使 registry 失效再關閉傳輸；來源能力仍需後續全面原生驗收。

Main 仍走沒有 CN plan 的一般 run_server。真正 account Prepare／phased entitlement、完整 snapshot、summary authority、world Reservation／native02與2A、來源選用及可恢復 schema 都仍缺實際掛接。此輪沒有填零、預設權限、猜造資料或把存檔存在視為可登入；正式 hosting 與完整雙向路線不計完成。

先前161封存與 before932 保留，三個子代理分別處理來源、呼叫點、原目錄發布有效性。本輪僅讀寫來源與檔案帳目，未建置、測試、執行原生／C++／Lua／API、存取 SQLite、遷移、重啟或部署。全遊戲分母仍未知，新 opcode、phase binding、完整路線均為零。TW/CN/web 全部支援目標、共用表預設、_tw／_cn 例外、數值64範圍、仙幣單獨上限、等級及凍結功能全部保留。
