# Flashare – Phase 1 Setup & Requirements

This document tracks all requirements and tasks needed to ship **Phase 1** of Flashare:
- One-line installation
- Cross-platform support (macOS, Linux, Windows)
- Clean CLI experience
- Zero server / zero infra

---

## 🎯 Phase 1 Goals

- Allow users to install Flashare with **one command**
- No backend servers or paid infrastructure
- Works on macOS, Linux, and Windows
- Binary-based distribution (no runtime dependencies)
- Professional, trustworthy onboarding

---

## ✅ Target User Experience

### macOS / Linux
```bash
curl -fsSL https://raw.githubusercontent.com/Abhijit-without-h/flashare/main/install.sh | sh
flashare
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/Abhijit-without-h/flashare/main/install.ps1 | iex
flashare
```

---

## 📦 Distribution Strategy

* GitHub is used as the installer host
* GitHub Releases act as the binary CDN
* No external servers required

---

## 🧱 Platform Requirements

### Supported Operating Systems

* macOS (Intel + Apple Silicon)
* Linux (x86_64 + ARM64)
* Windows (x86_64 + ARM64)

### Required Binary Artifacts

Each GitHub Release **must include**:

```
flashare-darwin-amd64
flashare-darwin-arm64
flashare-linux-amd64
flashare-linux-arm64
flashare-windows-amd64.exe
flashare-windows-arm64.exe
```

---

## 🛠 Installer Requirements

### install.sh (macOS & Linux)

* Detect OS and architecture
* Fetch latest GitHub Release
* Download correct binary
* Install to `/usr/local/bin/flashare`
* Set executable permissions
* Display success message

### install.ps1 (Windows)

* Detect CPU architecture
* Fetch latest GitHub Release
* Download `.exe` binary
* Install to `%USERPROFILE%\.flashare\bin`
* Add directory to user PATH
* Prompt user to restart terminal

---

## 📄 Required Documentation Files

### 1. README.md

Must include:

* One-line install commands
* Platform-specific install instructions
* Basic CLI usage examples
* Link to deeper docs

### 2. INSTALL.md

Must explain:

* What the installer does
* Supported platforms
* Manual install steps
* Uninstall instructions
* Security note about script inspection

### 3. DOCS.md

Must explain:

* How Flashare works internally
* Networking model (local transfer)
* Security and privacy design
* Design philosophy

### 4. PHASE_1_SETUP.md (this file)

Tracks progress and scope for Phase 1

---

## 🧪 CLI Requirements

Flashare must support:

```bash
flashare
flashare --help
flashare send <file|folder>
flashare receive
flashare version
```

Optional (nice to have):

```bash
flashare update
```

---

## 🔐 Security Requirements

* No persistent background services
* No cloud uploads
* Local-network only transfers
* Temporary server lifecycle
* Links/QR codes expire automatically
* No telemetry by default

---

## 🧩 Engineering Tasks (To-Do)

### Core

* [ ] Finalize Flashare CLI interface
* [ ] Build single static binary per platform
* [ ] Validate binary naming conventions

### Installers

* [ ] Create `install.sh`
* [ ] Create `install.ps1`
* [ ] Test installers on all platforms

### Releases

* [ ] Create GitHub Release v0.1.0
* [ ] Upload all binaries
* [ ] Verify download URLs

### Docs

* [ ] Write INSTALL.md
* [ ] Write DOCS.md
* [ ] Update README.md

---

## 🚀 Success Criteria

Phase 1 is complete when:

* A new user installs Flashare in **under 10 seconds**
* No dependency installation is required
* Works identically across macOS, Linux, and Windows
* Users can immediately run `flashare`

---

## 🔜 Phase 2 (Out of Scope)

* Homebrew formula
* Scoop (Windows package manager)
* APT repository
* Auto-update mechanism
* GUI wrapper

---

## 🧠 Design Principle

> “If installation is not instant, the tool doesn’t exist.”

Phase 1 optimizes for **speed, trust, and simplicity**.
