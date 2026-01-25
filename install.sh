#!/bin/bash
# Flashare Install Script for macOS/Linux
# Downloads the latest release binary and installs it

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚡ Flashare Installer${NC}"
echo ""

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64|amd64)
        ARCH="amd64"
        ;;
    arm64|aarch64)
        ARCH="arm64"
        ;;
    *)
        echo -e "${RED}Unsupported architecture: $ARCH${NC}"
        exit 1
        ;;
esac

case "$OS" in
    darwin)
        OS="darwin"
        ;;
    linux)
        OS="linux"
        ;;
    *)
        echo -e "${RED}Unsupported OS: $OS${NC}"
        exit 1
        ;;
esac

BINARY_NAME="flashare-${OS}-${ARCH}"
INSTALL_DIR="${HOME}/.local/bin"
GITHUB_REPO="Abhijit-without-h/flashare"

echo -e "Detected: ${GREEN}${OS}/${ARCH}${NC}"

# Create install directory if needed
mkdir -p "$INSTALL_DIR"

# Check if we can get the latest release
LATEST_URL="https://github.com/${GITHUB_REPO}/releases/latest/download/${BINARY_NAME}"

echo -e "Downloading from GitHub releases..."

# Try downloading from releases, or build from source
if curl -fsSL "$LATEST_URL" -o "${INSTALL_DIR}/flashare" 2>/dev/null; then
    chmod +x "${INSTALL_DIR}/flashare"
    echo -e "${GREEN}✓ Downloaded flashare to ${INSTALL_DIR}/flashare${NC}"
else
    echo -e "${YELLOW}Release not found, building from source...${NC}"
    
    # Check for Go
    if ! command -v go &> /dev/null; then
        echo -e "${RED}Go is not installed. Please install Go 1.21+ first:${NC}"
        echo -e "  macOS: brew install go"
        echo -e "  Linux: https://go.dev/dl/"
        exit 1
    fi
    
    # Clone and build
    TEMP_DIR=$(mktemp -d)
    git clone --depth 1 "https://github.com/${GITHUB_REPO}.git" "$TEMP_DIR"
    cd "$TEMP_DIR"
    go build -o "${INSTALL_DIR}/flashare" ./cmd/flashare
    rm -rf "$TEMP_DIR"
    
    echo -e "${GREEN}✓ Built and installed flashare${NC}"
fi

# Add to PATH if needed
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    echo ""
    echo -e "${YELLOW}Add this to your shell config (~/.bashrc, ~/.zshrc):${NC}"
    echo -e "  export PATH=\"\$PATH:${INSTALL_DIR}\""
fi

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo -e "Run ${BLUE}flashare${NC} to start."
