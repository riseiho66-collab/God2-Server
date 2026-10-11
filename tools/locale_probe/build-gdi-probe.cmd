@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x86 -host_arch=x64 >nul
if errorlevel 1 exit /b 1
cl /nologo /O2 /Fo:artifacts\locale-gdi-probe-20260923\gdi-native.obj /Fe:artifacts\locale-gdi-probe-20260923\gdi-native.exe tools\locale_probe\gdi_codepage_probe.c gdi32.lib
if errorlevel 1 exit /b 1
cl /nologo /O2 /Fo:artifacts\locale-gdi-probe-20260923\gdi-native-manifest.obj /Fe:artifacts\locale-gdi-probe-20260923\gdi-native-manifest.exe tools\locale_probe\gdi_codepage_probe.c gdi32.lib /link /MANIFEST:EMBED /MANIFESTINPUT:tools\locale_probe\gdi_zh_cn.manifest
exit /b %errorlevel%
