# Flashare ⚡

**CLI-First Hybrid File Sharing Tool**

A power-user CLI hub for file transfers with a FastAPI backend, BLE connectivity, Zstandard compression, fzf integration, and a modern mobile web UI.

---

## Features

- 🔍 **Fuzzy File Selection** - Use `fzf` to quickly select files to share
- 📹 **Video Optimization** - Auto-transcode videos with FFmpeg for faster transfers
- 🗜️ **Zstandard Compression** - 3-5x faster than gzip with better compression ratios
- 📱 **Mobile Web UI** - Modern glassmorphism PWA interface
- 🔵 **BLE Discovery** - Android devices can discover the server via Bluetooth
- 📷 **QR Code** - Scan to connect on any device

---

## Installation

### Prerequisites

```bash
# Install system tools (macOS)
brew install fzf ffmpeg

# Or on Linux
sudo apt install fzf ffmpeg
```

### Install Flashare

```bash
# Clone the repository
cd /path/to/flashare

# Install with uv
uv sync

# Or install with pip
pip install -e .
```

---

## Usage

### Quick Start

```bash
# Start the file sharing wizard
share

# Or using uv
uv run share
```

This will:
1. Open `fzf` to select a file
2. Offer to optimize videos with FFmpeg
3. Display a QR code for mobile connection
4. Start the server

### CLI Options

```bash
# Share a specific file
share /path/to/file.pdf

# Start server only (share all files in uploads/)
share --server-only

# Custom port
share --port 9000

# Skip video optimization
share --no-optimize

# Start from a specific directory
share --directory ~/Documents
```

### Mobile Access

1. **QR Code**: Scan the QR code displayed in the terminal
2. **URL**: Navigate to the URL shown (e.g., `http://192.168.1.10:8000`)
3. **Bluetooth (Android)**: Tap "Scan Bluetooth" in the mobile app

---

## Project Structure

```
flashare/
├── pyproject.toml          # Project configuration
├── src/flashare/
│   ├── __init__.py         # Package init
│   ├── __main__.py         # python -m flashare entry
│   ├── config.py           # Configuration
│   ├── server.py           # FastAPI server
│   ├── core/
│   │   ├── network.py      # IP detection
│   │   ├── compression.py  # Zstandard compression
│   │   ├── ble.py          # BLE advertising
│   │   ├── qr.py           # QR code generation
│   │   └── ffmpeg.py       # Video optimization
│   ├── api/
│   │   └── routes.py       # API endpoints
│   ├── cli/
│   │   ├── main.py         # CLI entry point
│   │   ├── fzf.py          # fzf wrapper
│   │   └── ui.py           # Rich terminal UI
│   └── static/
│       ├── index.html      # Mobile web UI
│       ├── styles.css      # Styling
│       └── app.js          # Frontend logic
└── uploads/                # Shared files directory
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Mobile web UI |
| `/api/files` | GET | List available files |
| `/api/download/{filename}` | GET | Download file (Zstd compressed) |
| `/api/upload` | POST | Upload file from phone |
| `/api/qr` | GET | Get QR code data |
| `/api/qr.png` | GET | Get QR code as PNG |
| `/api/status` | GET | Server status |

---

## License

MIT
