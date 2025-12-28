# Flashare Installer (Windows PowerShell)

$repo = "Abhijit-without-h/flashare"
$binaryName = "flashare.exe"
$installDir = Join-Path $HOME ".flashare\bin"
$ErrorActionPreference = "Stop"

Write-Host "⚡ Installing Flashare..." -ForegroundColor Cyan

# Ensure install directory exists
if (!(Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}

# Detect Architecture
$arch = $env:PROCESSOR_ARCHITECTURE.ToLower()
if ($arch -eq "amd64") {
    $arch = "amd64"
} elseif ($arch -eq "arm64") {
    $arch = "arm64"
} else {
    Write-Error "Unsupported architecture: $arch"
    exit 1
}

$assetName = "flashare-windows-$arch.exe"

# Fetch latest release URL
Write-Host "🔍 Finding latest release..." -ForegroundColor Cyan
try {
    # Get the first item from the releases list (supports pre-releases)
    $releaseInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases?per_page=1"
    # releaseInfo might be an array if there are multiple releases, but per_page=1 should return an array of 1
    if ($releaseInfo -is [array]) {
        $releaseInfo = $releaseInfo[0]
    }
    $asset = $releaseInfo.assets | Where-Object { $_.name -eq $assetName }
} catch {
    Write-Error "❌ API Request failed. Please check your internet connection."
    exit 1
}

if ($null -eq $asset) {
    Write-Error "❌ Could not find binary for Windows-$arch in the latest release."
    Write-Host "This might mean the release is still building. Please try again later." -ForegroundColor Yellow
    exit 1
}

$downloadUrl = $asset.browser_download_url

Write-Host "📥 Downloading $assetName..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $downloadUrl -OutFile (Join-Path $installDir $binaryName) -UseBasicParsing

# Add to PATH if not already present
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$installDir*") {
    Write-Host "⚙️  Adding $installDir to User PATH..." -ForegroundColor Cyan
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installDir", "User")
    Write-Host "⚠️  Please restart your terminal for changes to take effect." -ForegroundColor Yellow
}

Write-Host "✅ Flashare installed successfully!" -ForegroundColor Green
Write-Host "🚀 Run 'flashare --help' (might need a terminal restart)." -ForegroundColor Green
