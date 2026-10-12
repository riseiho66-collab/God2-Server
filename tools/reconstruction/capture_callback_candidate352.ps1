$ErrorActionPreference='Stop'
$serverRoot='C:/Users/risei/Desktop/God2/God2-Server'
$reviewRoot='C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round352-blacklist-submitted-chain-source-order-review'
$history=Join-Path $reviewRoot 'history/callback-qualified-candidate'
if(Test-Path -LiteralPath $history){throw 'Exclusive candidate exists'}
New-Item -ItemType Directory -Path $history | Out-Null
$actual=Join-Path $serverRoot 'src/core/Application.cpp'
$bytes=[IO.File]::ReadAllBytes($actual)
$hash=(Get-FileHash -LiteralPath $actual -Algorithm SHA256).Hash.ToLowerInvariant()
if($bytes.Length -ne 713375 -or $hash -ne '6fc65b1edb323a8ac423958447af61ef2db2b4b1a4f0e980cc22ce8f42e3e896'){throw 'Candidate changed; preserve and inspect new scope separately'}
[IO.File]::WriteAllBytes((Join-Path $history 'Application.cpp'),$bytes)
$upstream='C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round352-blacklist-submitted-chain-host-implementation'
foreach($name in @('exact-edits-and-inverse.json','callback-qualification-correction.json')) {
    Copy-Item -LiteralPath (Join-Path $upstream $name) -Destination (Join-Path $history $name)
}
$receipt=[ordered]@{scope='HISTORICAL_EARLY_CALLBACK_QUALIFIED_CANDIDATE_NOT_FINAL_CANONICAL_FREEZE';actual_path=$actual;retained='history/callback-qualified-candidate/Application.cpp';bytes=$bytes.Length;sha256=$hash;review='STATIC_CONDITIONAL_PASS_NO_TARGET_EXECUTION'; final_seal=$false}
[IO.File]::WriteAllText((Join-Path $history 'candidate-reference.json'),(($receipt|ConvertTo-Json -Depth 10).Replace("`r`n","`n")+"`n"),[Text.UTF8Encoding]::new($false))
Write-Output 'Historical candidate captured; final source list and seal remain pending.'
