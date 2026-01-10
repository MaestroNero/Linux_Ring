# Secure Kali Linux Environment Manager (GUI)

Professional, native Linux desktop application to manage and harden Kali Linux environments.
Built with Python 3 and PySide6 (Qt for Python), this tool exposes a modern GUI to perform user management, service control, firewall/profile-based hardening, tool installation, updates and process monitoring — all with secure privilege elevation when required.

Status
- Project type: Desktop application for Kali Linux (GNOME / KDE)
- Language: Python 3
- GUI: PySide6 (Qt for Python)
- Intended OS: Debian-based (Kali Linux)
- Stability: Initial implementation / roadmap stage

Highlights
- Modern, dark-themed native GUI with sidebar navigation
- Tools Manager: grid of tool cards with install/update/remove actions, background installs, progress bars and live logs
- Predefined Secure Environment Profiles (Student, Pentesting Lab, Hardened) with preview and sequential apply
- Interactive tables for Users, Services, Processes and Ports
- Real-time logging and formatted feedback for actions
- Designed for PolicyKit/privilege separation — UI runs unprivileged and escalates specific operations

Quick Screenshot (placeholder)
> Replace these placeholders with real images/screenshots in /assets/screenshots/
- Dashboard
- Tools Manager (card grid)
- Profile preview & apply dialog
- Logs panel

Table of contents
- Features
- System requirements
- Install (dev workflow)
- Running
- Architecture & Folder Structure
- UI / UX notes
- Tools Manager design details
- Secure Environment Profiles
- Elevation & Security (PolicyKit)
- Logging & Error handling
- Development / Contributing
- Roadmap
- License

Features
- Dashboard: system overview (CPU, memory, network, recent logs)
- Secure Environment Setup: apply predefined profiles with previews
- User Management: add/remove/modify users with roles and status
- Service Management: start/stop/enable/disable services, port/Risk view
- Tools Manager: install/update/remove security tools with progress and logs
- Updates & Patching: apt-based systems updates with logs and history
- Processes & Ports: list and manage processes and open ports
- Logs & Monitoring: formatted, real-time logs and action history

System requirements
- Kali Linux (Debian-derived)
- Python 3.10+ (3.11 recommended)
- Desktop environment: GNOME or KDE or any Wayland/X11
- apt package manager (for tool installation)
- Required Python packages listed in requirements.txt
- Access to PolicyKit or sudo for operations that modify system state

Install (developer / testing)
1. Clone:
   git clone https://github.com/MaestroNero/Secure-Kali-Linux-Environment-Manager-with-a-Graphical-User-Interface.git
   cd Secure-Kali-Linux-Environment-Manager-with-a-Graphical-User-Interface

2. Create and activate virtual environment:
   python3 -m venv venv
   source venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt

4. Run:
   python main.py

Running in production / with proper elevation
- The UI is designed to run as a normal user. Only specific backend operations require elevated privileges (apt, systemctl, useradd/del, ufw/iptables).
- Recommended: implement a Polkit-enabled helper backend or use pkexec wrappers for elevated commands (see "Elevation & Security" section below).
- Do NOT run the whole GUI as root (bad UX/security).

Architecture & Project layout

```Map for the Project
secure-kali-manager/
├── main.py                         # Application entry point
├── requirements.txt                # Python dependencies
├── ui/                             # UI layer (PySide6)
│   ├── main_window.py
│   ├── sidebar.py
│   ├── dashboard.py
│   ├── users_view.py
│   ├── services_view.py
│   ├── tools_view.py
│   ├── profiles_view.py
│   ├── processes_view.py
│   ├── logs_view.py
│   └── dialogs.py
├── core/                           # Business logic / system interaction
│   ├── user_manager.py
│   ├── service_manager.py
│   ├── tool_installer.py
│   ├── profile_manager.py
│   ├── process_manager.py
│   └── firewall_manager.py
├── assets/
│   ├── icons/
│   └── styles.qss                  # Dark theme
└── logs/
```

UI / UX Notes
- Left Sidebar: Dashboard, Secure Environment Setup, User Management, Service Management, Tools Manager, Updates & Patching, System Processes, Logs & Monitoring
- Main content: dynamic pages (stacked widget)
- Bottom panel: persistent logs & action output (formatted, color-coded)
- Theme: dark Qt stylesheet; responsive layout using Qt layouts and size policies

Tools Manager (critical)
Design:
- Grid-based card layout; each card shows:
  - icon, name, short description
  - installed status + current version (if known)
  - action buttons: Install, Update, Remove (Remove optional/controlled)
  - progress indicator when action in progress

Behavior:
- Actions run asynchronously using QThread/QRunnable + signals or QProcess for apt/git operations. Never block the main thread.
- Real-time progress: capture apt/dpkg or custom script output, parse progress lines to update progress bar.
- Logs: all install/update output goes to the bottom session log (formatted; errors highlighted).
- State sync: after action completes, refresh tool metadata (installed, version) and update card UI.

Tools metadata
- Keep a local JSON/YAML catalog (assets/tools_catalog.yml) with:
  - id, package_name, apt_package, github_repo, install_instructions, icon_path, description, default_args
- Installer uses apt when available, falls back to git clone & make/install for tools not in repos.

Secure Environment Profiles
Predefined profiles:
1. Student Secure Environment
   - disable root SSH login
   - disable unnecessary services
   - basic firewall rules (deny incoming, allow SSH from LAN)
   - install educational tools only

2. Pentesting Lab Environment
   - enable required services (postgresql, redis if needed)
   - allow limited ports for lab tools
   - install pentesting toolset
   - restrict external exposure

3. Hardened Secure Environment
   - lock non-essential users
   - disable unused services
   - aggressive firewall rules
   - file permission hardening (critical system directories)

Profile UI:
- Preview dialog: shows a table of planned changes (Action, Target, Before, After, Risk Level)
- Requires confirmation
- Application: sequential execution with per-step progress and the ability to roll back or log failures with suggested remediation

Elevation & Security (how to implement)
- Principle: least privilege. UI runs unprivileged; escalate only specific actions.
- Recommended approaches:
  - PolicyKit (Polkit) agent + helper: create a small setuid/Polkit-authorized helper actions that perform specific privileged operations. Communicate via D-Bus or command-line protocol.
  - pkexec wrappers: for simple setups, pkexec can be used to run helper scripts. Note pkexec requires a proper .policy file and careful sanitization.
  - Do not run the entire GUI as root.
- Example pattern:
  - core/tool_installer.py prepares and validates an operation, then requests privilege via polkit to execute the install script as root.
  - The helper scripts must validate inputs, restrict paths, and log all actions.

Logging & Feedback
- Central logging module in core/logging.py
- Logs stored in logs/ with rotation
- UI subscribes to log events (via signals) and displays formatted messages in the bottom panel
- Errors are shown as alerts in dialogs and as critical log entries

Development / Contributing
- Follow PEP8 / black formatting
- Use virtualenv for development
- Unit tests for core modules (process_manager, user_manager, firewall_manager)
- Integration tests for safe / simulated actions using containers or dedicated VM images (do not run destructive tests on host)

Packaging & Deployment (notes)
- Packaging as .deb preferred for Kali; consider creating a Debian package that:
  - installs assets into /usr/share/secure-kali-manager/
  - installs a .desktop file and system policy
  - registers polkit policy and helper binary
- Flatpak / Snap are possible but need system-level capabilities for privileged ops; less suitable.

Security considerations
- Validate and sanitize all inputs used in shell commands
- Avoid running arbitrary remote scripts as root
- Ensure logs do not leak sensitive information (do not print full password/keys)
- Prefer apt / distro packages over running arbitrary install scripts
- Provide clear user warnings for high-risk operations

Roadmap
- MVP: full UI skeleton + Tools Manager + Profiles + logging
- Next: Polkit helper + packaged .deb + real tool catalog
- Future: remote management via secure agent, audit/history reports, role-based access control

License
- MIT (or choose another OSS license)

Contact
- Maintainer: MaestroNero
- Repo: https://github.com/MaestroNero/Secure-Kali-Linux-Environment-Manager-with-a-Graphical-User-Interface

Replace placeholders (e.g., screenshots, tool catalog) with actual assets in assets/ and we can iterate on wording and structure.
