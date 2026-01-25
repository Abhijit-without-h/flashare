# Flashare ⚡

**High-Performance CLI File Sharing Tool**

A blazing-fast file sharing tool built in Go with a beautiful animated TUI, QR code connection, and modern mobile web UI. Share files between your laptop and phone instantly.

---

## ✨ Features

- 🚀 **Blazing Fast** - Built in Go for maximum performance
- 🎨 **Beautiful TUI** - Animated terminal interface with Bubble Tea
- 📱 **Mobile Web UI** - Modern glassmorphism PWA design
- 📷 **QR Code** - Scan to connect instantly
- 📦 **Multi-file Upload** - Parallel uploads with progress tracking
- 🗜️ **Zstandard Compression** - 3-5x faster than gzip
- 🌗 **Dark/Light Theme** - Toggle in web UI
- 📁 **Single Binary** - No dependencies, just download and run

---

## 📥 Installation

### Quick Install (Recommended)

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/Abhijit-without-h/flashare/main/install.sh | sh
```

**Go Install:**
```bash
go install github.com/Abhijit-without-h/flashare/cmd/flashare@latest
```

### Build from Source

```bash
git clone https://github.com/Abhijit-without-h/flashare.git
cd flashare
make build
./bin/flashare
```

---

## 🚀 Usage

### Interactive Mode (TUI)

Simply run:
```bash
flashare
```

This opens a beautiful animated menu where you can:
- Select files to share with a built-in file picker
- Start receive mode
- See server status with QR code

### CLI Commands

```bash
# Send specific files
flashare send file1.pdf file2.jpg

# Start receive mode (accepts uploads)
flashare receive

# Use custom port
flashare --port 9000 send

# Disable TUI (simple CLI mode)
flashare --no-tui receive

# Show version
flashare version
```

### Mobile Access

1. **QR Code**: Scan the QR code displayed in terminal
2. **URL**: Navigate to displayed URL (e.g., `http://192.168.1.10:8000`)

---

## 🛠️ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Mobile web UI |
| `/api/files` | GET | List available files |
| `/api/download/{filename}` | GET | Download file (Zstd compressed) |
| `/api/upload` | POST | Upload single file |
| `/api/upload-multiple` | POST | Upload multiple files |
| `/api/files/{filename}` | DELETE | Delete file |
| `/api/qr` | GET | Get QR code data |
| `/api/qr.png` | GET | Get QR code as PNG |
| `/api/status` | GET | Server status |

---

## 🏗️ Architecture

```
flashare/
├── cmd/flashare/          # CLI entry point
│   └── main.go
├── internal/
│   ├── cli/               # Cobra CLI + TUI launcher
│   ├── server/            # Fiber HTTP server
│   │   ├── server.go      # Routes & handlers
│   │   └── static/        # Embedded web UI
│   ├── tui/               # Bubble Tea TUI
│   └── qr/                # QR code generation
├── Makefile               # Build automation
└── go.mod                 # Go module
```

---

## 🔧 Development

```bash
# Build
make build

# Build with race detector
make dev

# Cross-compile for all platforms
make cross

# Run tests
make test

# Clean
make clean
```

---

## 📊 Performance

| Metric | Python (old) | Go (new) |
|--------|-------------|----------|
| Cold start | ~300ms | <10ms |
| Memory (idle) | ~50MB | ~10MB |
| Memory (100 uploads) | ~500MB | ~30MB |
| Binary size | N/A (needs Python) | ~8MB |
| Throughput | ~500 MB/s | ~2-3 GB/s |

---

## 📄 License

MIT

---

Built with ⚡ by [Abhijit](https://github.com/Abhijit-without-h)
