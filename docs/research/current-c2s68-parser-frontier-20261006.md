# Current-native C2S68 format frontier, 2026-10-06

The verified mapped image is `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`, SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`. The retained bounded native instructions are in `artifacts/integration/packet-connections-20261006/wrapper-ui-context-static-v3.json`. Addresses are RVAs at base `0x400000`.

The C2S wrapper `961A0` receives `(68,1)` at four guarded calls: `C3795`, `C37B3`, `C3832`, and `C39BD`. The queue branch emits logical bytes `68 00`; the wrapper may instead handle the event locally. `C3800..C3838` sends only when the selected large-map row `UI+232DA8` is nonnegative and has widget flag `0x10`; its other branch closes locally. `C3930..C39D7` has a separate panel-state gate and can also call `961A0`. Thus neither the four calls nor the one-zero format proves four transmitted operations or a server effect.

`RecoveredMapPanelControl68` now decodes exactly `68 00`. `RecoveredWorldRecords` admits it only under a dedicated default-false `map_panel68` parser flag, carried by `Session::RecoveredCharacterHandlers`; `Application` does not enable or handle the operation. This is format and parser source only. S2C `3F` opens the existing large-map panel; the unrelated S2C `68` consumer updates `UI+232DD8`. No current-native evidence proves which, if either, follows C2S `68`. A server response, saved-state authority, and phase/panel policy remain open. No guessed reply or success handler was added.

This round did not execute the client, build, test, deploy, inspect live saved state, or change formal service data. It does not count a complete gameplay connection.
