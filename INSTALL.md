# Installation Guide

Flashare is distributed as a standalone binary for easy one-line installation. No Python installation is required.

## 🚀 One-Line Install

### macOS / Linux
Run this command in your terminal:
```bash
curl -fsSL https://raw.githubusercontent.com/Abhijit-without-h/flashare/main/install.sh | sh
```

### Windows (PowerShell)
Run this command in PowerShell:
```powershell
irm https://raw.githubusercontent.com/Abhijit-without-h/flashare/main/install.ps1 | iex
```

---

## Alternative: Build from Source
If you are a developer or want to build it yourself:

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/Abhijit-without-h/flashare.git
    cd flashare
    ```
2.  **Install dependencies and run:**
    ```bash
    # Using uv (recommended)
    uv sync
    uv run flashare --help
    ```
