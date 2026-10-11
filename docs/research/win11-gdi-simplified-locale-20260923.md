# Windows 11 Simplified text rendering probe (2026-09-23)

The user selected zh-CN in the launcher on a Traditional Chinese Windows 11
host and reported garbled red text in the login scene. The surrounding
Traditional Chinese login UI is original fixed UI art and is expected.
`God2Launcher.player.settings.xml` and `config/user.settings` both recorded
zh-CN. The current client imports `TextOutA`, `ExtTextOutA`, `CreateFontA`,
`DrawTextA` and `GetACP`. The screenshot alone does not locate the red text's
specific source or prove it uses one of those imports.

Microsoft documents that `activeCodePage` can select a legacy process code
page on Windows 11, but GDI does not honor the per-process active code page for
text rendering. See:

- https://learn.microsoft.com/en-us/windows/win32/sbscs/application-manifests#activecodepage
- https://learn.microsoft.com/en-us/windows/apps/design/globalizing/use-utf8-code-page

`tools/locale_probe/gdi_codepage_probe.c` tests this on the actual host without
changing the machine locale. It draws CP936 bytes for `简体中文` with `TextOutA`,
then compares raster hashes with `TextOutW` in intended and CP950-decoded form.
The executable was built as x86 native code using the checked-in manifest for
the zh-CN variant. Results in `artifacts/locale-gdi-probe-20260923/`:

| Launch | GetACP | TextOutA raster | Intended Unicode raster | CP950-decoded raster |
| --- | ---: | --- | --- | --- |
| ordinary | 950 | `38d20190880b22b5` | `ba950d10cee8b89d` | `38d20190880b22b5` |
| Win11 zh-CN manifest | 936 | `38d20190880b22b5` | `ba950d10cee8b89d` | `38d20190880b22b5` |
| Win11 zh-CN manifest through bundled Locale Emulator 2.5.0.1 | 936 | `ba950d10cee8b89d` | `ba950d10cee8b89d` | `38d20190880b22b5` |

The same native probe with the bundled zh-TW profile reports GetACP950 and
the CP950 raster. The bundled Locale Emulator therefore repairs this specific
native GDI mismatch on the current Windows 11 host. Its upstream LEProc `-run`
mode reads the executable sidecar `.le.config`; our launcher already used this
path on Windows 10. Source:
https://github.com/xupefei/Locale-Emulator/blob/master/LEProc/Program.cs

`Launcher-src/launcher-src/TaiwanSupport.cs` now writes the profile and uses
LEProc for both Windows 10 and 11, retaining the Win11 localized manifest and
the existing client resource selector. Launch success now requires a *new*
client process ID, so a previously running identical client cannot mask a
failed second launch. `launcher-src/test-project.cmd` passes.
The rebuilt player helper is installed in both the player package and current
client (SHA256
`836ce5849897a4f016b1ae96e735a5a341beadd29b7e1858e0cae83570b24fd2`);
the prior copies are preserved in the probe artifact directory. Player
endpoint isolation tests pass after installation.

This establishes a process-level GDI fix for representative CP936 bytes. It
does not yet prove which renderer produced the screenshot's red text, nor that
the packed God2 client will render every simplified glyph correctly. A real
game launch and visual check on Windows 11, plus Windows 10 host validation,
remain necessary before claiming bilingual client acceptance.
