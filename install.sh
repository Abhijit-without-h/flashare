#!/bin/bash

# Flashare Installer (macOS & Linux)
# Installs flashare binary from GitHub Releases.

set -e

REPO="Abhijit-without-h/flashare"
BINARY_NAME="flashare"
INSTALL_DIR="/usr/local/bin"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "⚡ ${GREEN}Installing Flashare...${NC}"

# Detect OS
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *) echo -e "${RED}Unsupported architecture: $ARCH${NC}"; exit 1 ;;
esac

case "$OS" in
    darwin|linux) ;;
    *) echo -e "${RED}Unsupported OS: $OS${NC}"; exit 1 ;;
esac

ASSET_NAME="flashare-${OS}-${ARCH}"

# Fetch latest release URL (including pre-releases)
echo "🔍 Finding latest version..."
LATEST_RELEASE_URL=$(curl -s "https://api.github.com/repos/$REPO/releases?per_page=1" | grep "browser_download_url" | grep "$ASSET_NAME" | head -n 1 | cut -d '"' -f 4)

if [ -z "$LATEST_RELEASE_URL" ]; then
    echo -e "${RED}❌ Error: Could not find binary for $OS-$ARCH in the latest release.${NC}"
    echo "This might mean the release is still building. Please try again in a few minutes."
    exit 1
fi

echo "📥 Downloading $ASSET_NAME..."
TEMP_FILE=$(mktemp)
curl -L --progress-bar -o "$TEMP_FILE" "$LATEST_RELEASE_URL"
chmod +x "$TEMP_FILE"

echo "⚙️  Installing to $INSTALL_DIR..."
if [ -w "$INSTALL_DIR" ]; then
    mv "$TEMP_FILE" "$INSTALL_DIR/$BINARY_NAME"
else
    echo "⚠️  ROOT permission required to move binary to $INSTALL_DIR"
    sudo mv "$TEMP_FILE" "$INSTALL_DIR/$BINARY_NAME"
fi

# Verification
if command -v flashare >/dev/null; then
    echo -e "${GREEN}✅ Flashare installed successfully!${NC}"
    echo -e "🚀 Run 'flashare --help' to get started."
else
    echo -e "${RED}❌ Installation failed. 'flashare' not found in path.${NC}"
    exit 1
fi
