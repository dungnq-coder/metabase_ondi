
---

# 🚀 Environment Setup Guide

This project uses **[uv](https://astral.sh/uv/)** — a fast, Rust-based tool for managing Python virtual environments and dependencies.

Follow the steps below to set up your development environment.

---

## 📚 Table of Contents

1. [Installing `uv`](#-1-installing-uv)
2. [Setting Up the Virtual Environment](#-2-setting-up-the-virtual-environment)
3. [Verification](#-3-verification)
4. [Run the Application](#-4-run-the-application)

---

## 📦 1. Installing `uv`

`uv` is a high-performance, modern replacement for `pip` and `venv`.

### 🐧 1.1 Linux & macOS

Open your terminal and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
````

### 🪟 1.2 Windows

#### PowerShell

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

> ⚠️ After installation, restart your terminal or make sure the `uv` command is available in your `PATH`.

---

## 🛠️ 2. Setting Up the Virtual Environment

After installing `uv`, create and activate your virtual environment.

### 🐧 2.1 Linux & macOS

```bash
cd path/to/your/project
uv venv --python 3.11.8
source .venv/bin/activate
uv sync
```

---

### 🪟 2.2 Windows

```powershell
cd path\to\your\project
uv venv --python 3.11.8
```

Then activate depending on your shell:

#### 🟣 PowerShell

```powershell
.venv\Scripts\Activate.ps1
uv sync
```

#### ⚫ Command Prompt (CMD)

```cmd
.venv\Scripts\activate.bat
uv sync
```

> 💡 **Tip:** If you get a script execution error in PowerShell, allow script execution:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

## ✅ 3. Verification

After activation, your terminal prompt should look like:

```
(.venv) C:\path\to\project>
```

Check your Python version:

```bash
python --version
```

✅ **Expected output:**

```
Python 3.11.8
```

---

## ▶️ 4. Run the Application

Once the environment is set up and activated:

```bash
python main.py
```

> Make sure you are in the **root folder** of the project before running.

---

## 🧩 Notes

* `uv` automatically installs dependencies listed in your `pyproject.toml` or `requirements.txt` when you run `uv sync`.
* To remove the virtual environment, simply delete the `.venv/` folder.
* To upgrade dependencies, run:

  ```bash
  uv sync --upgrade
  ```

---

