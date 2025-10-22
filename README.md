Environment Setup Guide
This project utilizes uv for fast and efficient management of virtual environments and dependencies. Please follow the steps below to set up your development environment.

I. Installing the uv Tool
uv is a high-performance package and environment manager built in Rust, designed as a modern replacement for pip and venv.

🐧 1. On Linux and macOS
Open your Terminal and run the following command:

```curl -LsSf https://astral.sh/uv/install.sh | sh```
🪟 2. On Windows (PowerShell/CMD)
Open PowerShell or Command Prompt and run one of the following commands:

# For PowerShell:
```irm https://astral.sh/uv/install.ps1 | iex```

# Alternatively, for CMD (ensure curl is available):
```curl -LsSf https://astral.sh/uv/install.sh | sh```
Note: After installation, you may need to restart your terminal session or ensure the installation directory of uv is added to your system's PATH environment variable for the uv command to be accessible.

II. Setting Up the Virtual Environment
Once uv is installed, we will proceed to create and activate the virtual environment using the specified Python version.

🐧 1. On Linux and macOS
Navigate to the project's root directory and run the commands below in sequence:

Create the virtual environment with Python 3.11.8:

```uv venv python=3.11.8```
Activate the virtual environment:

```source .venv/bin/activate```

```uv sync```
🪟 2. On Windows (Command Prompt or PowerShell)
Navigate to the project's root directory and run the commands below in sequence:

Create the virtual environment with Python 3.11.8:

```uv venv python=3.11.8```
Activate the virtual environment:

For Command Prompt (CMD):

```.venv\Scripts\activate```
For PowerShell:

```.venv\Scripts\Activate.ps1```

```uv sync```

III. Verification
After successful activation, your command line prompt should display the environment name (.venv).

To quickly verify the Python version within the virtual environment:

```python --version```
# Expected Output: Python 3.11.8
