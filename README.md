# 🤖 Ultron: Autonomous Desktop AI Assistant

Ultron is a voice-controlled, multi-agent AI assistant engineered specifically for **Windows 11**. It gives you hands-free and direct command over your entire system—opening apps, navigating the browser, running PowerShell tasks, connecting to VPN servers, managing online APIs, and autonomously writing, testing, and debugging full software projects.

---

## ⚡ Quick Start (No Coding Knowledge Needed)

### 1. Requirements
- **Windows 10 or 11**
- **Python 3.10+** (Python 3.13 is already installed and verified on your system!)

### 2. Setup
1. Open this folder:
   `C:\ULTRON\`
2. Double-click `install.bat` (or run `python -m pip install -r requirements.txt` in PowerShell).
3. Open `.env` in Notepad and paste your API key (e.g., `GROQ_API_KEY=...` or `OPENAI_API_KEY=...`).

### 3. Launching Ultron
Double-click `run.bat` or run:
```powershell
python main.py
```

---

## 🏗️ Multi-Agent Architecture

Ultron operates with 5 specialized internal agents that share a common SQLite event log and synchronized memory:

```
                  ┌──────────────────────┐
                  │    Manager Agent     │ ◄── User Voice / Command
                  └──────────┬───────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│Thinker Agent │      │ Coder Agent  │      │Executor Agent│
│(Plans steps) │      │(Writes code) │      │(Runs tools)  │
└──────────────┘      └──────┬───────┘      └──────┬───────┘
                             ▼                     ▼
                      ┌──────────────┐      ┌──────────────┐
                      │   QA Agent   │      │Safety Sentinel│
                      │(Tests code)  │      │(Guards risks)│
                      └──────────────┘      └──────────────┘
```

1. **Manager Agent**: Understands high-level goals, assigns work, and speaks answers back to you.
2. **Thinker Agent**: Breaks complex requests into step-by-step logic and assesses safety risks.
3. **Executor Agent**: Interacts directly with Windows (opens apps, controls browser, moves files, connects VPN).
4. **Coder Agent**: Writes and updates code in `UltronProjects/<project_name>/`.
5. **QA / Debugger Agent**: Automatically checks syntax, runs tests, and catches bugs before delivery.
6. **Shared State & Event Log**: Central SQLite database (`data/ultron_state.db`) that records every action with timestamps for total auditability.

---

## 🛡️ Safety & Confirmations

Ultron grants you full system power without risking accidental damage:
- **Low Risk** (Opening apps, searching files, reading content): Executes instantly.
- **High Risk** (Deleting folders/files, running ad campaigns, spending money, public social media posts, destructive terminal commands): **Halted immediately** until you verbally say **"Yes"** or press **"y"** in the console.

---

## 🎙️ Spoken & Written Commands

You can speak or type commands like:
- **App Control**: `"Hey Ultron, open Chrome"` or `"Close Notepad"`
- **Browser Automation**: `"Open Chrome and go to chatgpt.com"`
- **VPN Control**: `"Connect my VPN to Germany"`
- **File Management**: `"Create a new folder called ClientX on Desktop"`
- **Project Workflows**: `"Build a simple landing page for a digital marketing agency"`
  - *The Thinker plans the architecture.*
  - *The Coder writes the HTML, CSS, and JS.*
  - *The QA agent verifies syntax and validity.*
- **System Audit**: Type `logs` to see the live table of every action Ultron performed.

---

## 🔄 How to Pull Future Updates Without Breaking Custom Logic
To merge changes from a public base repository in the future:
1. Custom Ultron components live in self-contained folders:
   - `agents/`: Multi-agent definitions
   - `shared_state/`: SQLite memory & event log
   - `tools/`: Windows & API integrations
   - `voice/`: Neural audio engine
2. Keep your project in a Git repository:
   ```powershell
   git init
   git add .
   git commit -m "Ultron custom build"
   ```
3. If syncing with an upstream repository:
   ```powershell
   git remote add upstream <URL>
   git fetch upstream
   git merge upstream/main --no-commit
   ```
   Because our custom modules are isolated into separate directories, upstream changes merge cleanly with minimal conflicts!
