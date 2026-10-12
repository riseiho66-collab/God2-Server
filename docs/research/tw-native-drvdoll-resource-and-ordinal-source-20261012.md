# 第318輪：DrvDoll 原始序號來源接入入口生命周期

新增兩個C++來源檔，修改四個既有檔，完成一項原始資源來源接入；完整玩法branch/opcode/雙向route新增0。317原件與封存保持。本輪是PHASE1來源工作，未建置、測試或執行遊戲。

## 恢復真正的獨立來源

Fresh verified=true archive lookup精確恢復DrvDoll.csvZ.decoded 7620B，SHA256 de9510e0c5b1171e164b407c931b41e7fc3c5a7b5ffa3aba9193a51063f2dd9f。實際archive原path使用lowercase drvdoll；uppercase首次exactpath miss保留，後按exactSHA唯一source恢復，非全域absence。普通archive-zlib slice2057B，offset348259280，放God2外；原502df... csvZ未恢復／解碼。Archive readonly/query_only SQL不是gameDBSQL，wholepack/index未全域reaudit。

145physical lines全部CRLF，firstdata26/count120。每row是7rawfields、6commas，native配置5只consume前5；兩comment欄保留。Col0 label巧合0..119，不是nativeindex；col1在ordinal0為empty，其他0；col3僅0/2/12/28，filename原bytes最大30，只有ordinal0空。五selected rawrowsL26/27/28/29/145與120rawrow envelope保留line/offset/fields；未宣稱讀完所有中文字義。

## 原生行寫入的實際規則

4637B0載入器的46382E..46398E段，用signedWORD count+24F70當ordinal、136B stride、bank+24F74；每row INCWORD，EOF close及signedcount==headermax assertion，若assert返回則normal return1，不假定assert必然abort。Genericcount>=32768未證安全；原表120rows在此域內。

Col1經451B50取signedDWORD低WORD→row+0；cache row+2直接寫FFFF；col3 FILD signedDWORD×mapped FLOAT32 bits3DCCCCCD再FSTP row+4；col4 text→row+8，strlen<128 assertion、copyhelper127並explicit row+135 NUL。只釘signed sourceint/factorbits，不模擬FPU rounding、cache或ROM。Empty col1沿known313的451B60 strlen0→EAX0，451BA0 RET保持0，有exactorigin，不是填預設成功。

Selected352B/93sites，explicit歷史run overlap281B/73sites、相對tail closure71B/20sites；wholeloader早在20260919已知，globalnewmethods0。4B floatconstant匹配mapped/PE。478B trueentry continuity只作機械map；七known313 helpers、317prefix126B reference不重計coverage。初切點463980落在instruction內，保留excluded correction，不升格有效span。

## 真正C++來源接點

TaiwanNativeDrvDoll::from_pinned_decoded要求supplied absolute origin、exact7620B/SHA、header与120ordinal，保留全plain、header、rawrows/all7fields/line/offset。Parser只承接原integer/delimiter subset；col1 exactempty accessor0與低WORD、col3原signed32、filename原bytes。無隱含file read、CSVZ codec、DB、float計算、ROM查找或原wire修改。Label對ordinal比對只資格核原固定檔，不把native改成label-key查表。find>=120回nullptr，是absent source row，不在入口添加拒絕條件；empty row0不造有效handle。

既有SharedTaiwanNativeWorldEntryOfferSource::SceneContent強持qualified immutable DrvDoll source，供原mandatory SceneSupply查閱，before/after producer、Issuer/CAS與stored Qualify保留同identity。新增explicit paired overload及SharedTaiwanNativeWorldHostPlan sameContext overload，保留real writer/read/commonowner/fullqualify需求。舊overloads defaultnull保持，不另造supplier/serializer、guess padding、owned selector、scene admission或Main opt-in。CMake既有GLOB_RECURSE包含新增.cpp，未改構建配置／執行構建。

## 數量與剩餘工作

TW C2S候選156；world74=部分来源50/control11/未接13；S2C252=fixed230/variable22，reply48/push11/gated4/未分類117。Battle indexed110/specialized9；86 selectors7/cases6；83 actions23/projections2/outside21。TW chains3/bindings38 unique34。CN historical C2S156/S2C phase280/length253各scope獨立，chains35/bindings93 unique71，本輪CN增量0。Mixed282/CUSTOM135/groups26/pending10保持；50/74=67.6%只計世界解析部分分支，全遊戲總數、完整分子／分母、TW及整體百分比null。

完整actual149c owned2A creation/mutation B0/B4、kind/B8/opaque、components/transform/scalars、正常Entered/install與full6F及其餘玩法仍open。下一步直接追這些actual原來源，而非重查已知資源rowloader。不把資料availability／consumer／sourcebinding當完整issuer或玩法。

沒有build/compiler/tests/runtime/native/VM/emulator/resourcecodec/gameDBSQL/migrate/activate/deploy。只有ordinary archivezlib/readonly archive-tool SQL與靜態來源記錄，worker與rootsource增量分開。Frozen帳號存檔、auth/chat/IME/頭像/原字體/繁簡轉換、TW/CN/web、shared64、coins99999999999、stack99、level保持。

## 固定證據

外部包：`C:\Users\risei\.codex\artifact-archives\god2-server\20261012\tw-native-drvdoll-resource-and-ordinal-source-318`。Currentclosures含全部actualnested seals；partialhistorical capture不代表完整原包，manual讀範圍另記。

```json
{
  "native-entry": {
    "qualified_spans": 1,
    "bytes": 352,
    "sites": 93,
    "new_selected_spans_vs_reference": 0,
    "new_bytes": 71,
    "new_sites": 20,
    "explicit_overlap_bytes": 281,
    "overlap_sites": 73,
    "data_slices": 1,
    "data_bytes": 4,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "142270206a40465da3434d6203a31e85618d77d68777630d114827bbd19e4f83",
    "canonical_closure_sha256": "08aa4d3ab0230ab535f81141e99b93089ed3ad45dec3efad250fda5f333ab135",
    "closure_members": 100,
    "closure_bytes": 7393609
  },
  "profile-resource": {
    "round": 318,
    "restored_exact_original_sources": 1,
    "restored_bytes": 7620,
    "source_data_rows": 120,
    "selected_rows": 5,
    "source_byte_scan_only": true,
    "readonly_archive_index_sql": true,
    "verified_archive": true,
    "general_archive_zlib_restores": 1,
    "resource_csvz_decode_executed": false,
    "input_count": 13,
    "input_bytes": 59670,
    "native_methods_increment": 0,
    "source_increment": 0,
    "cpp_increment": 0,
    "branch_increment": 0,
    "opcode_increment": 0,
    "fullroute_increment": 0,
    "game_completion_increment": 0,
    "completion_percentage": null,
    "actual_owned_selector_grants": 0,
    "mechanical_row_envelopes": 120,
    "raw_source_fields": 7,
    "native_configured_fields": 5,
    "raw_seal_sha256": "c983ec485a343d24ae09c0dc76cc410fca2f95dd070be8eb94d5eed65820fa6e",
    "canonical_closure_sha256": "b8cec4aba135ed9a0e69d90dd6002f124ab02b9ca4dce61256c3d2577c3dffd8",
    "closure_members": 38,
    "closure_bytes": 227658
  }
}
```
