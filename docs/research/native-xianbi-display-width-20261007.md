# 原生仙幣錢包正數顯示上限

目前安裝台服及固定陸服兩版的錢包正數格式上限均為**2,147,483,647**。
這是當前EXE的儲存→格式化→UI更新靜態結果，尚未做原生畫面驗收；
不是官方服務端帳戶/交易/經濟上限，也不是每個視窗像素容量的聲明。

TW：S2C27的logical1 DWORD進00498D70，完整存入main+85604，呼叫0049B7B0。
0049B7C0呼叫004856D0，以格式字串5823B4的`%d`及一個DWORD參數進00547AF7
sprintf，再每三位加逗號。0049B7DF..E0送005077C0，格式58DB2C為`%11s`。
%11s是最低欄寬，不是11字元截斷；此路徑沒有把數值變為64或unsigned。

CN：已保存world/battle27接收分派均到004C7710。004C772B將DWORD完整存入
main+41AEC；004C7731呼叫004AD2C0，004AD2DC/E2以7ED65C的`%d`呼叫00415310
sprintf，再加千位逗號。004C7741/7750以7F27F0的`%11s`交00450B80更新UI。
CN metadata只是導航，主要bytes/calls/字串已從固定EXE現讀封存。

`%d`把該參數當signed32：0x7fffffff對應2,147,483,647；0x80000000開始
屬負数。4-byte native wire能保留0..4,294,967,295的bit pattern，不代表此
client路徑能顯示為同樣正值。因此不能以wire或SQLite範圍報原生顯示上限。
這個原生欄位限制可先定點修改格式化及相关signed算術；不是整EXE x64轉換。
格式字串可能共用，不能直接全局改`%d`破壞其他顯示；64位擴充仍需全鏈處理。

既有TW銀行研究另記錄signed500,000,000本地存入檢查；它與錢包格式上限
分開。CN銀行限制及所有金錢操作仍未在此輪恢復，不推廣TW規則到CN。

精確EXE雜湊、主要bytes、asm、字串與metadata副本：
artifacts/continuation/numeric64-scope-20261007/native-xianbi-display-01/evidence.json。
沒有建置、測試、執行客戶端/服務端、改EXE或正式DB操作。
