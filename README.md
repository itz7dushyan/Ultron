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
3. Your Google Gemini 3.7 Flash API keys are already configured in `.env` with primary and fallback redundancy!

### 3. Launching Ultron
You have four ways to interact with Ultron:

- **Option A: Completely Invisible Background Service (Zero Terminal, Zero Taskbar Tab)** ⭐ *(Recommended)*
  Double-click `start_silent.vbs`!
  - Ultron runs 100% silently in the background using `pythonw.exe` with no console window and **no taskbar button**.
  - While you are working on your desktop, browser, or games, simply say **"Hey Ultron"** or **"Wake up Ultron"**.
  - The futuristic **Orange Aurora Waves** and **Central Arc Reactor HUD** appear on screen, and Ultron answers **instantly in <50ms** calling you **"Boss"**!
  - To check status: double-click `status_ultron.bat`.
  - To stop: double-click `stop_ultron.bat`.

- **Option B: Pure Hands-Free Voice Assistant (Console Window)**
  Double-click `voice_mode.bat` or run:
  ```powershell
  python main.py --voice
  ```

- **Option C: Hybrid Desktop Terminal (Voice + Keyboard)**
  Double-click `run.bat` or run:
  ```powershell
  python main.py
  ```

- **Option D: Cybernetic Web HUD Portal**
  Double-click `portal.bat` or run:
  ```powershell
  python portal_server.py
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

Ultron understands spoken Hindi and English, and **always responds in 100% clean, crisp English addressing you as "Boss"**:
- **System Audio & Master Volume Control**:
  - `"Set volume to 50%"` / `"Volume 60 percent karo"` / `"Volume 30"`
  - `"Volume up"` / `"Awaaz badhao"`
  - `"Volume down"` / `"Awaaz kam karo"`
  - `"Mute audio"` / `"Unmute"`
- **Media Playback Controls**:
  - `"Pause music"` / `"Play music"` / `"Song pause karo"`
  - `"Next track"` / `"Skip song"`
  - `"Previous track"` / `"Pichla song chalao"`
- **System Power & Window Management**:
  - `"Lock my PC"` / `"Lock laptop"` *(locks Windows session instantly)*
  - `"Show desktop"` / `"Minimize all"` *(sends Win+D)*
  - `"Maximize window"` / `"Minimize window"`
  - `"Close this tab"` / `"Tab band karo"` *(sends Ctrl+W)*
  - `"Close this window"` / `"Window band karo"` *(sends Alt+F4)*
- **Universal Application Launching**:
  - `"Open Spotify"` / `"Spotify kholo"`
  - `"Open Proton VPN"` / `"Proton VPN kholo"`
  - `"Open Discord"`, `"Open Steam"`, `"Open VLC"`, `"Open WhatsApp"` *(scans all installed apps dynamically!)*
  - `"Close File Explorer"` / `"File Explorer band karo"` *(closes folder windows safely without terminating Windows desktop shell)*
- **Browser Navigation & YouTube Automation**:
  - `"Search YouTube for Hans Zimmer Interstellar"`
  - `"Google search quantum computing 2026"`
  - `"Open new tab"` / `"Reload page"` / `"Switch tab"`
- **Clipboard Intelligence**:
  - `"Read my clipboard"` / `"What is in my clipboard?"`
  - `"Copy Hello World to clipboard"`
- **Compound Multi-Step Workflows**:
  - `"Make a google document on AI in 2026, then make a folder called Voice model testing and move the doc inside, and then open Spotify"`
  - *Decomposes compound tasks into sequential steps and executes them smoothly with verbal progress!*
- **Interactive 4K Wallpaper Selection**:
  - `"Change wallpaper to nature"` / `"Wallpaper change karo"`
  - *Pops up a futuristic 5-card 4K preview gallery window directly on your screen with titles, descriptions, and numbers so you can see them visually and pick via voice or click!*
- **Screenshot & Media Organization**:
  - `"Take a screenshot and save it to Screenshots"`
  - `"Organize screenshots in Screenshots folder"` *(sorts and sequentially renames them to `Screenshot_001.png`, `Screenshot_002.png`, etc.)*
- **System Audit**: Type `logs` to see the live SQLite table of every action Ultron performed.

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
