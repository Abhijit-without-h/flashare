# Documentation

## How It Works

Flashare is a CLI-first tool that simplifies local file sharing. It combines a FastAPI backend with a modern web UI.

### Networking Model
- **Local Transfer**: All transfers happen over your local Wi-Fi or Ethernet network.
- **Zero Configuration**: Flashare automatically detects your local IP and sets up a temporary server.
- **QR Code**: Generates a QR code for mobile devices to join the local server instantly.

### Security & Privacy
- **E2E Local**: Data never leaves your local network. No cloud intermediate.
- **Temporary Lifecycle**: The server only runs while you are actively sharing.
- **No Telemetry**: We do not collect any usage data.

### Design Philosophy
1. **Speed**: Instant sharing with zero setup.
2. **Simplicity**: No accounts, no logins, no "cloud".
3. **Power-User Friendly**: CLI-first for rapid workflows.

## Internal Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JS + CSS (Glassmorphism design)
- **Optimization**: FFmpeg for video transcoding.
- **Compression**: Zstandard for fast data transfer.
