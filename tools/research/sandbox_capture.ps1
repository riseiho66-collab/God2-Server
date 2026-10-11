param(
    [ValidateSet('Probe', 'Prepare', 'Run')][string]$Mode = 'Probe',
    [string]$Script = 'capture-startup.txt',
    [string]$RunId = 'startup'
)
$ErrorActionPreference = 'Stop'
$output = 'C:\Output'
if (-not (Test-Path -LiteralPath $output)) { throw 'Run only inside the prepared GOD2 Windows Sandbox' }
if ($RunId -notmatch '^[a-zA-Z0-9_-]+$' -or $Script -notmatch '^[a-zA-Z0-9_-]+\.txt$') { throw 'Invalid capture run name' }
$environmentPath = "$output\environment-$Mode.json"
if ($Mode -eq 'Run') { $environmentPath = "$output\environment-Run-$RunId.json" }
if (Test-Path -LiteralPath $environmentPath) { throw 'Environment output already exists' }
$ips = @(Get-NetIPAddress -ErrorAction Stop | Where-Object { $_.IPAddress -ne '::1' -and $_.IPAddress -notlike '127.*' })
$probe = [ordered]@{
    captured_at = [DateTime]::UtcNow.ToString('o')
    computer = $env:COMPUTERNAME
    operator = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    os = (Get-CimInstance Win32_OperatingSystem).Caption
    non_loopback_addresses = @($ips | Select-Object IPAddress,InterfaceAlias)
    isolation_verified = ($ips.Count -eq 0)
}
$probe | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $environmentPath -Encoding UTF8
if ($ips.Count -ne 0) { throw 'Non-loopback network address present; refusing client execution' }
if ($Mode -eq 'Probe') { exit 0 }
$expected = 'FB72296CAB5950B74D8F7C98155145F7C5F58749C3011ADB0540325B60749DD1'
if ($Mode -eq 'Prepare') {
    if (Test-Path -LiteralPath 'C:\God2Work') { throw 'Working directory already exists' }
    New-Item -ItemType Directory -Path 'C:\God2Work' | Out-Null
    Copy-Item -Path 'C:\Input\Client\*' -Destination 'C:\God2Work' -Recurse
    Copy-Item -LiteralPath 'C:\Input\Debugger' -Destination 'C:\Debugger' -Recurse
    $hash = (Get-FileHash -LiteralPath 'C:\God2Work\God2.exe' -Algorithm SHA256).Hash
    if ($hash -ne $expected) { throw 'Working copy hash mismatch' }
    [ordered]@{original_artifact_sha256=$expected; working_copy_sha256=$hash; copied_at=[DateTime]::UtcNow.ToString('o')} |
        ConvertTo-Json | Set-Content -LiteralPath "$output\working-copy.json" -Encoding UTF8
    exit 0
}
if ($RunId -notmatch '^[a-zA-Z0-9_-]+$' -or $Script -notmatch '^[a-zA-Z0-9_-]+\.txt$') { throw 'Invalid capture run name' }
if ((Get-FileHash -LiteralPath 'C:\God2Work\God2.exe' -Algorithm SHA256).Hash -ne $expected) { throw 'Working copy changed before launch' }
$stdout = "$output\$RunId-stdout.log"
$stderr = "$output\$RunId-stderr.log"
if ((Test-Path -LiteralPath $stdout) -or (Test-Path -LiteralPath $stderr)) { throw 'Capture output already exists' }
$arguments = '-testing -cf "C:\Input\Scripts\' + $Script + '"'
try {
    $process = Start-Process -FilePath 'C:\Debugger\headless.exe' -ArgumentList $arguments -WorkingDirectory 'C:\God2Work' -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
} catch {
    [ordered]@{started=$false; error=$_.Exception.Message; captured_at=[DateTime]::UtcNow.ToString('o')} |
        ConvertTo-Json | Set-Content -LiteralPath "$output\$RunId-launch-failure.json" -Encoding UTF8
    throw
}
if (-not $process.WaitForExit(120000)) {
    Stop-Process -Id $process.Id -Force
    Get-CimInstance Win32_Process -Filter "Name='God2.exe'" | Where-Object { $_.ExecutablePath -eq 'C:\God2Work\God2.exe' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    throw 'Bounded capture timeout; preserve logs and do not claim completion'
}
$process.Refresh()
[ordered]@{debugger_pid=$process.Id; exit_code=$process.ExitCode; completed_at=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json | Set-Content -LiteralPath "$output\$RunId-exit.json" -Encoding UTF8
exit $process.ExitCode
