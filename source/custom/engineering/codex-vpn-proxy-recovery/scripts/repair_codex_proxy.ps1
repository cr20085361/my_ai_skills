[CmdletBinding()]
param(
    [string]$ProxyHost = '127.0.0.1',
    [int]$ProxyPort = 10808,
    [switch]$RestartCodex,
    [switch]$SetAllProxy
)

$ErrorActionPreference = 'Stop'

$listener = Get-NetTCPConnection -State Listen -LocalPort $ProxyPort -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $listener) {
    throw ('No listener found on {0}:{1}. Start v2rayN and confirm the HTTP/mixed port.' -f $ProxyHost, $ProxyPort)
}

$proxy = "http://${ProxyHost}:$ProxyPort"
$proxyNames = @('HTTP_PROXY', 'HTTPS_PROXY', 'WS_PROXY', 'WSS_PROXY')
foreach ($name in $proxyNames) {
    [Environment]::SetEnvironmentVariable($name, $proxy, 'User')
}
if ($SetAllProxy) {
    [Environment]::SetEnvironmentVariable('ALL_PROXY', $proxy, 'User')
}

$noProxy = [Environment]::GetEnvironmentVariable('NO_PROXY', 'User')
$entries = @()
if ($noProxy) {
    $entries = @($noProxy -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}
foreach ($localEntry in @('localhost', '127.0.0.1', '::1')) {
    if ($entries -notcontains $localEntry) {
        $entries += $localEntry
    }
}
[Environment]::SetEnvironmentVariable('NO_PROXY', ($entries -join ','), 'User')

Write-Output "Proxy variables written to the current user environment: $proxy"
Write-Output "Listener PID: $($listener.OwningProcess)"

if (-not $RestartCodex) {
    Write-Output 'Codex was not restarted; the new settings apply on the next launch.'
    exit 0
}

$package = Get-AppxPackage -Name OpenAI.Codex -ErrorAction SilentlyContinue | Select-Object -First 1
if ($package) {
    $chatGPT = Join-Path $package.InstallLocation 'app\ChatGPT.exe'
} else {
    $running = Get-Process ChatGPT -ErrorAction SilentlyContinue | Select-Object -First 1
    $chatGPT = if ($running) { $running.Path } else { $null }
}
if (-not $chatGPT -or -not (Test-Path -LiteralPath $chatGPT)) {
    throw 'Could not find Codex Desktop ChatGPT.exe. Proxy variables were saved but Codex was not restarted.'
}

$escapedPath = $chatGPT.Replace("'", "''")
$restartPayload = @"
`$proxy = '$proxy'
`$env:HTTP_PROXY = `$proxy
`$env:HTTPS_PROXY = `$proxy
`$env:WS_PROXY = `$proxy
`$env:WSS_PROXY = `$proxy
$(if ($SetAllProxy) { "`$env:ALL_PROXY = `$proxy" })
Start-Sleep -Seconds 8
Get-Process -Name ChatGPT,codex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Start-Process -FilePath '$escapedPath'
"@
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($restartPayload))
Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @('-NoProfile', '-EncodedCommand', $encoded)
Write-Output 'Codex restart scheduled with explicit proxy inheritance.'
