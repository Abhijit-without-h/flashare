# Flashare Install Script for Windows
# Downloads the latest release binary and installs it

$ErrorActionPreference = "Stop"

Write-Host "⚡ Flashare Installer" -ForegroundColor Blue
Write-Host ""

# Detect architecture
$Arch = if ([System.Environment]::Is64BitOperatingSystem) { "amd64" } else { "386" }

$BinaryName = "flashare-windows-$Arch.exe"
$InstallDir = "$env:LOCALAPPDATA\Flashare"
$GithubRepo = "Abhijit-without-h/flashare"

Write-Host "Detected: windows/$Arch" -ForegroundColor Green

# Create install directory
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

$LatestUrl = "https://github.com/$GithubRepo/releases/latest/download/$BinaryName"
$DestPath = "$InstallDir\flashare.exe"

Write-Host "Downloading from GitHub releases..."

try {
    Invoke-WebRequest -Uri $LatestUrl -OutFile $DestPath -UseBasicParsing
    Write-Host "✓ Downloaded flashare to $DestPath" -ForegroundColor Green
} catch {
    Write-Host "Release not found, building from source..." -ForegroundColor Yellow
    
    # Check for Go
    if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
        Write-Host "Go is not installed. Please install Go 1.21+ first:" -ForegroundColor Red
        Write-Host "  https://go.dev/dl/"
        exit 1
    }
    
    # Clone and build
    $TempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
    git clone --depth 1 "https://github.com/$GithubRepo.git" $TempDir
    Push-Location $TempDir
    go build -o $DestPath ./cmd/flashare
    Pop-Location
    Remove-Item -Recurse -Force $TempDir
    
    Write-Host "✓ Built and installed flashare" -ForegroundColor Green
}

# Add to PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    Write-Host "✓ Added to PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "✓ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Restart your terminal and run 'flashare' to start." -ForegroundColor Cyan
