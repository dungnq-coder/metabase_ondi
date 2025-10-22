
---

# 🚀 Environment Setup Guide

This project uses **[uv](https://astral.sh/uv/)** — a fast, Rust-based tool for managing Python virtual environments and dependencies.

Follow the steps below to set up your development environment.

---

## 📦 1. Installing `uv`

`uv` is a high-performance, modern replacement for `pip` and `venv`.

### 🐧 1.1 On Linux & macOS

Open your terminal and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 🪟 1.2 On Windows (PowerShell / CMD)

#### PowerShell

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

#### Command Prompt (requires `curl`):

```cmd
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> ⚠️ **Note:** After installation, restart your terminal or ensure the `uv` binary is in your system's `PATH`.

---

## 🛠️ 2. Setting Up the Virtual Environment

After installing `uv`, you can create and activate your virtual environment.

### 🐧 2.1 On Linux & macOS

Navigate to your project directory:

```bash
uv venv python=3.11.8
source .venv/bin/activate
uv sync
```

### 🪟 2.2 On Windows

Navigate to your project directory, then:

```cmd
uv venv python=3.11.8
```

#### For CMD:

```cmd
.venv\Scripts\activate
uv sync
```

#### For PowerShell:

```powershell
.venv\Scripts\Activate.ps1
uv sync
```

---

## ✅ 3. Verification

After activating the environment, your terminal prompt should include the name `.venv`.

To verify the Python version:

```bash
python --version
```

✅ **Expected output:**

```
Python 3.11.8
```
## 4. Run

After verify successfully you can run main.py for CLI:

```bash
python main.py
```
Make sure that you in root folder of project.
---
