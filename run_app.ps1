$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$apiUrl = if ([string]::IsNullOrWhiteSpace($env:WASTE_API_URL)) {
    'http://127.0.0.1:8000'
} else {
    $env:WASTE_API_URL.TrimEnd('/')
}

function ConvertTo-PowerShellLiteral([string] $Value) {
    return "'" + $Value.Replace("'", "''") + "'"
}

function Test-TcpPort([string] $HostName, [int] $Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $pending = $client.ConnectAsync($HostName, $Port)
        return $pending.Wait(700) -and $client.Connected
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Test-ApiEndpoint([string] $Url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
        if ($response.StatusCode -ne 200) { return $false }
        $body = $response.Content | ConvertFrom-Json
        return $body.status -eq 'ok' -and $body.message -eq 'Smart Waste Segregation API is running'
    } catch {
        return $false
    }
}

function Test-DashboardEndpoint([string] $Url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
        return $response.StatusCode -eq 200 -and $response.Content.Trim() -eq 'ok'
    } catch {
        return $false
    }
}

function New-TerminalCommand([string] $Command) {
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
    Start-Process -FilePath 'powershell.exe' `
        -ArgumentList @('-NoLogo', '-NoExit', '-EncodedCommand', $encoded) `
        -WorkingDirectory $projectRoot `
        -WindowStyle Normal | Out-Null
}

try {
    Write-Host 'EcoTrack startup' -ForegroundColor Cyan
    Write-Host "Project folder: $projectRoot"
    Write-Host "Python: $python"

    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw "Project virtual-environment Python was not found: $python"
    }

    $version = & $python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "The virtual-environment Python could not start: $version"
    }
    Write-Host "Python check: $version"

    $uri = $null
    if (-not [Uri]::TryCreate($apiUrl, [UriKind]::Absolute, [ref] $uri) -or
        $uri.Scheme -ne 'http' -or $uri.AbsolutePath -ne '/') {
        throw "WASTE_API_URL must be an HTTP origin such as http://127.0.0.1:8000. Current value: $apiUrl"
    }

    $apiHost = $uri.Host
    $apiPort = $uri.Port
    $apiHealthUrl = $uri.GetLeftPart([UriPartial]::Authority) + '/'
    $dashboardUrl = 'http://127.0.0.1:8501'
    $dashboardHealthUrl = $dashboardUrl + '/_stcore/health'

    Write-Host "Configured API URL: $apiHealthUrl"

    $apiResponding = Test-ApiEndpoint $apiHealthUrl
    if ($apiResponding) {
        Write-Host "API already responds at $apiHealthUrl; keeping the existing process."
    } elseif (Test-TcpPort $apiHost $apiPort) {
        throw "API port $apiPort is already occupied, but the EcoTrack health endpoint did not respond. No duplicate API was started."
    } else {
        $apiCommand = @"
Set-Location -LiteralPath $(ConvertTo-PowerShellLiteral $projectRoot)
`$env:WASTE_API_URL = $(ConvertTo-PowerShellLiteral $apiHealthUrl.TrimEnd('/'))
Write-Host 'Starting EcoTrack FastAPI at $apiHealthUrl' -ForegroundColor Cyan
& $(ConvertTo-PowerShellLiteral $python) -m uvicorn backend.app:app --host $(ConvertTo-PowerShellLiteral $apiHost) --port $apiPort
if (`$LASTEXITCODE -ne 0) { Write-Host "FastAPI exited with code `$LASTEXITCODE" -ForegroundColor Red }
"@
        New-TerminalCommand $apiCommand

        $ready = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            Start-Sleep -Seconds 1
            if (Test-ApiEndpoint $apiHealthUrl) {
                $ready = $true
                break
            }
        }
        if (-not $ready) {
            throw "FastAPI did not become ready at $apiHealthUrl. Check the API terminal for its startup error."
        }
        Write-Host "FastAPI is ready at $apiHealthUrl"
    }

    $dashboardResponding = Test-DashboardEndpoint $dashboardHealthUrl
    if ($dashboardResponding) {
        Write-Host "Streamlit already responds at $dashboardUrl; keeping the existing process."
    } elseif (Test-TcpPort '127.0.0.1' 8501) {
        throw 'Dashboard port 8501 is already occupied, but the Streamlit health endpoint did not respond. No duplicate dashboard was started.'
    } else {
        $frontendCommand = @"
Set-Location -LiteralPath $(ConvertTo-PowerShellLiteral $projectRoot)
`$env:WASTE_API_URL = $(ConvertTo-PowerShellLiteral $apiHealthUrl.TrimEnd('/'))
Write-Host 'Starting EcoTrack Streamlit dashboard at $dashboardUrl' -ForegroundColor Cyan
& $(ConvertTo-PowerShellLiteral $python) -m streamlit run frontend\app.py --server.address 127.0.0.1 --server.port 8501 --server.showEmailPrompt false
if (`$LASTEXITCODE -ne 0) { Write-Host "Streamlit exited with code `$LASTEXITCODE" -ForegroundColor Red }
"@
        New-TerminalCommand $frontendCommand

        $ready = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            Start-Sleep -Seconds 1
            if (Test-DashboardEndpoint $dashboardHealthUrl) {
                $ready = $true
                break
            }
        }
        if (-not $ready) {
            throw "Streamlit did not become ready at $dashboardUrl. Check the dashboard terminal for its startup error."
        }
        Write-Host "Streamlit is ready at $dashboardUrl"
    }

    Write-Host ''
    Write-Host "EcoTrack dashboard: $dashboardUrl" -ForegroundColor Green
    Write-Host "FastAPI docs:       $apiHealthUrl`docs" -ForegroundColor Green
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
