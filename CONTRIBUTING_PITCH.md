<div align="center">

# 🔍 Magika GUI — Portable AI File Inspector

**The ultimate deep-learning powered file identification tool — no installation required.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Powered by Magika](https://img.shields.io/badge/Powered%20by-Google%20Magika-4285F4.svg)](https://google.github.io/magika/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-0078D6.svg)]()

<br>

> **Identify any file's true type using Google's deep learning model — even if the extension is changed, missing, or deliberately obfuscated.**

<br>

![Magika GUI Screenshot](screenshots/main-window.png)

</div>

---

## ⚡ What is this?

**Magika GUI** wraps [Google's Magika](https://github.com/google/magika) — a state-of-the-art AI file identification system — into a beautiful, portable desktop application. 

This project provides **native, zero-dependency binaries** for Windows, Linux, and macOS. No Python knowledge needed. No command line required. Just download, run, and scan.

Magika uses a custom deep learning model trained on **millions of files** to identify over **100+ file types** with >99% precision. It's the same technology Google uses internally at scale.

---

## ✅ Verified Environments
The current version has been successfully tested and verified on:
- **Windows**: 10, 11 (Native)
- **Linux**: Ubuntu (via WSL2 / Native)
- **macOS**: Intel & Apple Silicon (via Rosetta 2)

---

## 🎯 Features

### 🧠 AI-Powered Identification
- Detects the **true file type** regardless of extension or obfuscation
- Powered by Google's production-grade deep learning model (ONNX)
- Returns a **confidence score** for every identification

### 📊 Visual Analysis Dashboard
- **Pie Chart** — File type distribution across your scanned directory
- **Histogram** — Confidence score distribution
- **Stat Cards** — Total files, unique types, average confidence at a glance

### 🔎 Deep File Inspector
- **Sortable columns** — Click LABEL (A→Z) or SCORE (▲▼) to sort
- **Type filter** — Dropdown to filter by any detected file type
- **Live search** — Find specific files by name instantly

### 📦 Multi-Platform & Portable
- **Windows**: Single `.exe` file
- **Linux**: Portable binary + **`.deb` package** for Debian/Ubuntu
- **macOS**: Portable `.app` (Intel/Universal)
- No Python or dependencies required on the host system.

---

## 📸 Screenshots

<div align="center">

| Main Scanner | Analysis Dashboard |
|:---:|:---:|
| ![Scanner](screenshots/main-window.png) | ![Analysis](screenshots/analysis-window.png) |

</div>

---

## 🚀 Quick Start

### Option A: Download Binaries (Recommended)
1. Go to [**Releases**](../../releases)
2. Download the version for your OS:
   - **Windows**: `magika-gui-windows.exe`
   - **Linux**: `magika-gui-linux` or `magika-gui.deb`
   - **macOS**: `magika-gui-macos.zip`
3. Run the file — that's it!

> [!NOTE]
> **macOS Users**: Since the app is not signed, you may need to **Right-Click -> Open** the first time to bypass Gatekeeper.

### Option B: Run from Source
```bash
# Clone the repo
git clone https://github.com/nullsaint/magika-gui-portable.git
cd magika-gui-portable

# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

---

## 🛠️ How It Works

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│  Select Dir  │───▶│  Walk Files  │───▶│  Magika Engine  │
└─────────────┘    └──────────────┘    │  (ONNX Model)   │
                                       └────────┬────────┘
                                                │
                         ┌──────────────────────┤
                         ▼                      ▼
                   ┌──────────┐          ┌─────────────┐
                   │ Terminal  │          │  Analysis    │
                   │  Output   │          │  Dashboard   │
                   └──────────┘          └─────────────┘
```

1. **Select** a folder to scan
2. Magika's neural network **analyzes** each file's binary content
3. Results stream to the **terminal** in real-time
4. Click **ANALYSIS** for the full visual dashboard
5. **Filter, sort, search** and **export** your findings

---

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Engine | [Google Magika](https://github.com/google/magika) (ONNX Runtime) |
| GUI Framework | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Charts | [Matplotlib](https://matplotlib.org/) (Object-Oriented API) |
| CI/CD | GitHub Actions (Auto-build for Win/Linux/Mac) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

---

## ⚠️ Disclaimer

> **This application is NOT an officially supported Google project.**
> It is solely a personal project created for **experimentation and educational purposes only**.
>
> This project uses Google's open-source [Magika](https://github.com/google/magika) library
> under its [Apache 2.0 License](https://github.com/google/magika/blob/main/LICENSE).
> The GUI wrapper is an independent, community-built tool and is not endorsed,
> maintained, or affiliated with Google LLC in any way.
>
> Use at your own risk. The authors assume no liability for any misuse of this software.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

The underlying Magika engine is licensed under **Apache 2.0** by Google.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs via [Issues](../../issues)
- 💡 Suggest features
- 🔧 Submit pull requests

---

<div align="center">

**Built with ❤️ using Google's Magika AI**

*Identify. Inspect. Investigate.*

</div>

---

## 🧠 Technical FAQ & Cheat Sheet
If the Google team asks technical questions, here are the ready-made answers:

### 1. How did you handle the model packaging?
> "I used PyInstaller's `--add-data` flag to bundle the `models` and `config` directories directly from the installed `magika` site-package. In the build script, I programmatically locate the library using `os.path.dirname(magika.__file__)` to ensure the correct version of the models is grabbed. This preserves the folder structure Magika expects when it unpacks into the temporary `_MEIPASS` directory."

### 2. Is there a license conflict (MIT vs Apache 2.0)?
> "No, the licenses are fully compatible. The GUI is an independent wrapper licensed under MIT, while the underlying engine is imported as a dependency under its original Apache 2.0 license. I have included a clear Disclaimer and Attribution section in the README to clarify that this is a community project and that Google owns the Magika engine."

### 3. How is the .deb package built?
> "The `.deb` is generated via GitHub Actions on a Linux runner (`ubuntu-latest`). After the binary is built, the workflow creates the standard Debian folder structure, generates the `DEBIAN/control` metadata, and uses `dpkg-deb --build` for a clean, native package creation."
