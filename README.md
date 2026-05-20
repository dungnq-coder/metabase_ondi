# 🚀 Environment Setup Guide

This project uses **[uv](https://astral.sh/uv/)** — a fast, Rust-based tool for managing Python environments and dependencies.

Follow the steps below to set up your development environment.

---

## 📚 Table of Contents

1. [Install `uv`](#-1-install-uv)
2. [Set Up the Virtual Environment](#-2-set-up-the-virtual-environment)
3. [Verify the Setup](#-3-verify-the-setup)
4. [Run the Application](#-4-run-the-application)

---

## 📦 1. Install `uv`

`uv` is a high-performance alternative to `pip`, `pipenv`, and `venv`.

---

### 🐧 1.1 Linux & macOS

Open a terminal and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
````

---

### 🪟 1.2 Windows

#### Step 1 — Allow PowerShell scripts

Some Windows systems block script execution by default. Run **once**:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

> ⚠️ This allows local scripts, like the uv installer, to run safely.

---

#### Step 2 — Install uv

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

---

#### Step 3 — Add uv to PATH if necessary

`uv` installs to:

```
C:\Users\<YOUR_USERNAME>\.local\bin
```

If PowerShell cannot find `uv`, add it manually:

```powershell
$env:Path += ";$HOME\.local\bin"
[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path,
    [EnvironmentVariableTarget]::User
)
```

Then **restart PowerShell**.

Test:

```powershell
uv --version
```

You should see a version number like:

```
uv 0.9.10
```

---

## 🛠️ 2. Set Up the Virtual Environment

After installing `uv`, create and activate your project environment.

---

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

Activate depending on your shell:

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

> 💡 Tip: If you see a PowerShell script execution error, run:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

## ✅ 3. Verify the Setup

Your terminal prompt should now show:

```
(.venv) C:\path\to\project>
```

Check Python:

```bash
python --version
```

Expected output:

```
Python 3.11.8
```

---

## ▶️ 4. Run the Application

Once the virtual environment is active:

```bash
python main.py
```

> Make sure you run this from the **project root directory**.

---

## 🧩 Additional Notes

* `uv sync` installs all dependencies from `pyproject.toml` or `requirements.txt`.
* To remove the virtual environment, delete the `.venv/` directory.
* To upgrade packages:

```bash
uv sync --upgrade
```

---

## 🧪 Development

Install dev dependencies (test + lint + type-check tools):

```bash
uv pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

Lint and format:

```bash
ruff check src/ core/ tests/ main.py
ruff format src/ core/ tests/ main.py
```

Type-check:

```bash
mypy
```

---

## 🗺️ Project mappings

Per-project SQL/table rewrites live in `core/projects/<code>.yaml` — one file per
target project (`sr`, `nw`, `bl`). Shared constants (`ignored_tables`,
`spec_tables`) live in `core/projects/_global.yaml`. Adding a new project is a
YAML change, not a code change.

Example skeleton:

```yaml
short_code: xx
display_name: Example Project
table_mapping:
  source-project.dataset.foo: target-project.dataset.foo
rename:
  "('Old App Name')": "('New App Name')"
```

The short code must match the lowercased initials of the target Metabase
database name (e.g. database "Sword Rouge Lite" → `sr`).

---

## 🪵 Logging

Set the log level via environment variable:

```bash
METABASE_CLI_LOG=DEBUG python main.py
```

Default is `WARNING`. Menu UI output (✅, ❌, prompts) is always printed regardless.

---
