# 第315輪：入口body方向、暫存器來源與遠端參數別名

本輪提供實際原生呼叫與來源界線的更正，C++新增／修改0；新完整玩法branch、opcode、雙向route均0。原第226輪及其他歷史封存不改，這份記錄與315包是有效successor。

## 入口呼叫方向與欄位界線

46819C所算完整scratch body指標，送415690@4681A3作目的寫入。所選2A branch從真正packet source複製36B至scratch，不能把這個目的指標稱為讀取scratch所有欄位的input alias escape。其後413670→415B20在global5B4DA8非0時可call412CF0並傳owner；callback/globalalias仍opaque，不因目的formalarg方向更正宣稱全部子呼叫或全域都不讀body。

actual4607D0是低WORD setter，完整所選leaf不呼叫child或寫EDX；呼叫端IMUL/SAR count運算的EDX高16，因此不因該callee而丟失。後面的AX→DX與WORD右移只改低16。以Q為該計數暫存器結果，461AD0實際formalarg1=LE32(B24)&3F，arg2=(Q&FFFF0000)|(LE16(B24)>>6)，arg3=45AA70返回ptr、arg4=45A000返回ptr、arg5=Main；不是完整bodypointer。

arg2高位不是直接複製B26..27；45AA70/45A000返回資料與早前partial-register lookup參數仍opaque，不能推Q與B26間接完全獨立。這是consumer/register來源的更正，不是數值為0或server producer已恢復。461AD0只資格prefix與epilogue，不冒稱完整大函式閉包；原36B及高位仍保留。

4684D6的ESP rebasing形成body+12並傳到461270。該方法及selected8B component讀取已在歷史weapon來源資格化，只保留actual caller-context，不將已知方法再算成新發現。其餘callee與opaque範圍依315實際REPORT/readscope；不從限定direct footprint宣稱所有間接／整個生命週期都不讀某欄位。

## 遠端full6F參數別名

4FB460將fullbody傳給既有4FC1C0。成功支路EBX保持body base到4FC462才被bodyDWORD4值替換；所選direct/formalargument追蹤沒有新增body8 load或body8 pointer子呼叫來源。已知body14 components到4FC130、body1C/2C/3C字符串複製及textchildren分開，不重跑它們作新field authority。

4FC1C0以入口SP=E計：成功路徑保存EDI後SP=E-20h，arg2 body slot為E+8=[ESP28]。nonnull worldcell支路在4FC3D0/4FC3E0先把該slot覆寫為0／另一worldcell scalar；4FC403在先PUSH後SP=E-24h，LEA[ESP2C]仍為E+8，送449330時指向的是repurposed scalar cell。null worldcell支路跳4FC437、保留前面frame內容，這次不替它發明初始化。不能因slot曾是body便聲稱wholebody indirectescape；不把opaque child implicit register／所有alias都視為已關閉。

disp220掃描只得到候選位置，含錯位、data、stack與未證base。沒有新的actual remote A220 reader資格，不代表全映像／所有indirect reader不存在。full6F DWORD9/17及A220的權威來源保持未知；不改稱reserved、unused、padding或補0。

## 現有服務端接點及限制

真正可接入口仍是完整NativeWorldEntrySnapshot與Offer::from_actual_source(Snapshot,Issuer)，由Supply(scope,prior)送到既有replace_from_issuer，再由StoredSource Supply/Current與world lifecycle接收。snapshot/revision/root/position/resource guards只保留與資格既有完整來源，不生成缺失資料。

RecoveredWorldEntry::historical_body及decoded(local_id,profile,x,y,area,scene,kind=2)是opt-in歷史candidate，只改部分profile／identity／geometry，不是actual149c ownedproducer。RecoveredWorldEntryView保留原wire與baseline，不授予after-state或DA emission權。B0/B4 resource/status、B8..11、其餘opaque及kind規則、actual149c 八components/transform/scalars的持久owned來源仍有缺口。第314輪恢復的兩份原明文保持，不重新計入315增量。

## 統計

TW C2S候選156；世界解析74＝部分來源50／控制11／未接13；S2C252＝固定230／可變22，nondefault206／default46，reply48／push11／gated4／未分類117。Battle indexed110／specialized9；86 selectors7／cases6；83 actions23／projections2／outside21。TW未掛載chains3／bindings38 unique34。

CN歷史C2S156／S2C phase-opcode280／length253，各scope獨立；未掛載chains35／bindings93 unique71；本輪CN增量0。Mixed282／CUSTOM135／groups26／pending10保持。50/74＝67.6%僅限定解析分支比例；全遊戲總數、完整route數／分母與TW／全遊戲百分比未知。

沒有建置、compiler、tests、game/runtime/native/VM/emulator/resourcecodec/gameDBSQL、migration/activation/deployment；只做静態source/PE/Capstone與來源記帳。保留所有凍結功能、存檔、原字體／繁簡轉換、TW/CN/web、shared64、仙幣99999999999、stack99與等級。完整captured bytes不等於全部manual/callgraph；actualnested seals納入，partialhistory不冒稱完整原package。下一步以更正後實際source界線繼續取得完整入口與publication來源。

## 固定證據

外部包：`C:\Users\risei\.codex\artifact-archives\god2-server\20261012\tw-native-entry-body-alias-and-remote-opaque-315`。native intervals／relative overlaps／manual scope按以下固定metrics與各worker REPORT，不推全域新發現。

```json
{
  "native-entry": {
    "qualified_spans": 4,
    "bytes": 184,
    "sites": 61,
    "new_selected_spans_vs_reference": 3,
    "new_bytes": 92,
    "new_sites": 27,
    "explicit_overlap_bytes": 92,
    "overlap_sites": 34,
    "data_slices": 0,
    "data_bytes": 0,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "787368ac1a538beea0a30928b3bcdc82725a7cc4e4f70915c033f08cf1ee2c71",
    "canonical_closure_sha256": "3656e84c6c003fb32b8b5a53321873bf1ff26ad5a54e607ee3757ad3cfaa7346",
    "closure_members": 236,
    "closure_bytes": 10723673
  },
  "native-remote": {
    "round": 315,
    "native_qualified_new_cuts": 0,
    "native_qualified_new_bytes": 0,
    "source_integration_increment": 0,
    "opcode_completion_increment": 0,
    "full_route_completion_increment": 0,
    "game_completion_increment": 0,
    "completion_percentage": null,
    "global_historical_novelty_claim": false,
    "retained_selected_intervals": 3,
    "retained_selected_bytes": 2168,
    "retained_selected_instruction_sites": 707,
    "relative_reference_names": [
      "298 full6F case/full insert",
      "301 complete replacement",
      "308 bounded opaque references",
      "312 retained exact captures and effective correction",
      "313 references",
      "314 cleanup/package"
    ],
    "new_bytes_vs_named_references": 0,
    "overlap_bytes_vs_named_references": 2168,
    "raw_positive_dword220_pattern_occurrences": 79,
    "all_start_memory_disp220_candidates": 58,
    "stack_operand_candidates": 26,
    "nonstack_operand_candidates": 32,
    "retained_qualified_remote220_store": 1,
    "new_qualified_remote220_readers": 0,
    "all_possible_remote_reader_count": null,
    "input_count": 39,
    "input_bytes": 6702364,
    "percent_denominator": "Full-game route denominator remains unknown.",
    "raw_seal_sha256": "1747f1ad1fd045b8aeee20eccaff481b817d81101ab10b2f5fae60546c7d0f7d",
    "canonical_closure_sha256": "53483c37dc86638eaac886f6425192858fb2d3d60b8bc980c9a2a04a35a939dc",
    "closure_members": 59,
    "closure_bytes": 6805387
  }
}
```
