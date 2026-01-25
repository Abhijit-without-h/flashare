
<div align="center">

# Flashare ⚡

### Fast, Local, CLI-First File Sharing

[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/Abhijit-without-h/flashare?style=flat-square&color=black)](https://github.com/Abhijit-without-h/flashare/releases)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey?style=flat-square)](https://github.com/Abhijit-without-h/flashare)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

<p align="center">
  Flashare is a <b>power-user tool</b> that lets you instantly share files between devices using a clean CLI workflow and a modern mobile web interface.<br>
  <b>No cloud. No accounts. No setup.</b>
</p>

[Report Bug](https://github.com/Abhijit-without-h/flashare/issues) · [Request Feature](https://github.com/Abhijit-without-h/flashare/issues)

</div>

---

## ✨ Why Flashare?

Built for developers and privacy-focused users who want transfers to *just work*.

- ⚡ **Instant Local Transfers:** Direct P2P over Wi-Fi/LAN.
- 🧠 **CLI-First Workflow:** Seamless integration with your terminal.
- 📱 **Mobile-Friendly Web UI:** Scan a QR code and download.
- 🗜️ **Smart Compression:** Uses Zstandard for speed and efficiency.
- 📹 **Video Optimization:** Automatic transcoding for large media files.
- 🔒 **Private by Design:** Files never leave your local network.

---

## 🚀 Key Features

| Feature | Description |
| :--- | :--- |
| **Fuzzy Selection** | Interactive file picking powered by `fzf`. |
| **Zstd Compression** | Faster and more efficient than standard gzip. |
| **Auto-Transcode** | Optional FFmpeg optimization for smoother video sharing. |
| **Modern UI** | A clean, responsive web interface for the receiver. |
| **QR Code Share** | Generate a terminal QR code for instant mobile connection. |

---

## 📦 Installation (v0.1.2)

Flashare installs as a **single binary** with no required runtime dependencies.

### macOS / Linux
```bash
curl -fsSL https://raw.githubusercontent.com/Abhijit-without-h/flashare/main/install.sh | sh

```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/Abhijit-without-h/flashare/main/install.ps1 | iex

```

> **Note:** After installation, please restart your terminal.

### 🔧 Optional Dependencies

While Flashare works standalone, installing these enhances the experience:

* **`fzf`** — Enables the interactive file picker.
* **`ffmpeg`** — Enables video compression/optimization.

```bash
# macOS
brew install fzf ffmpeg

# Linux (Debian/Ubuntu)
sudo apt install fzf ffmpeg

```

---

## 🧭 Usage

### Quick Start

Simply run the command to start the interactive wizard:

```bash
flashare

```

**This will:**

1. Open a file picker (if `fzf` is installed).
2. Offer to optimize video files.
3. Display a QR code.
4. Start the local server.

### Command Reference

| Action | Command |
| --- | --- |
| **Share specific file** | `flashare ~/Downloads/doc.pdf` |
| **Share directory** | `flashare --directory ~/Documents` |
| **Server only** | `flashare --server-only` |
| **Custom port** | `flashare --port 9000` |
| **Skip optimization** | `flashare --no-optimize` |
| **Help** | `flashare --help` |

---

## 📱 Receiving Files

1. **Scan:** Use your phone to scan the QR code generated in your terminal.
2. **Browse:** Alternatively, navigate to the URL shown (e.g., `http://192.168.1.X:8000`).
3. **Download:** No app installation required on the receiving device.

---

## 🌱 Philosophy

Flashare is built around three core principles:

1. **Speed over complexity.**
2. **Local over cloud.**
3. **Ephemerality:** Tools that disappear once the job is done.

**Run it. Share. Exit. Done.**

---

## 🛡 Security

* **No Cloud Uploads:** Data never touches an external server.
* **No Background Services:** The server dies when you close the terminal.
* **Local Only:** Transfers are restricted to your local network (LAN).

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

<div align="center">
<sub>Built with ❤️ by <a href="https://www.google.com/search?q=https://github.com/Abhijit-without-h">Abhijit</a></sub>
</div>

