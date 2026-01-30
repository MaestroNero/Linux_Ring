# Linux Ring

**Linux Ring** is a comprehensive, professional GUI application designed to manage, harden, and monitor Linux environments (specifically tailored for Kali Linux). Built by **Maestro Nero**, this tool [...]

<div align="center">

![Build](https://img.shields.io/badge/build-stable-28a745?style=for-the-badge&logo=github)
![Platform](https://img.shields.io/badge/platform-Kali_Linux-557C9D?style=for-the-badge&logo=kali-linux&logoColor=white)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Last Commit](https://img.shields.io/github/last-commit/MaestroNero/Linux_Ring?style=for-the-badge&logo=git)
![Language](https://img.shields.io/github/languages/top/MaestroNero/Linux_Ring?style=for-the-badge&color=3776AB)
![Technologies](https://img.shields.io/badge/technologies-PySide6%20%7C%20Qt%20%7C%20UFW-yellow?style=for-the-badge&logo=qt)
![Stars](https://img.shields.io/github/stars/MaestroNero/Linux_Ring?style=for-the-badge&color=ffac33&logo=github)
![Forks](https://img.shields.io/github/forks/MaestroNero/Linux_Ring?style=for-the-badge&color=blueviolet&logo=github)
![Issues](https://img.shields.io/github/issues/MaestroNero/Linux_Ring?style=for-the-badge&logo=github)
![Contributors](https://img.shields.io/github/contributors/MaestroNero/Linux_Ring?style=for-the-badge&color=9c27b0)

</div>


## Features

- **Dashboard**: Real-time system overview (CPU, Memory, Network) with recent activity logs.
- **Tool Manager**: Browse, install, update, and remove security tools with a modern card-based interface.
- **Secure Environment Profiles**:
    - **Student Secure Environment**: Locks down SSH, disables noisy services, and enforces basic firewall rules.
    - **Pentesting Lab Environment**: Enables necessary databases (PostgreSQL, Redis) and tools for lab work.
    - **Hardened Secure Environment**: Applies aggressive security measures, file permissions, and strict firewall policies.
- **Service & Process Management**: specific control over system daemons and running processes.
- **User Management**: graphical interface for managing users and groups.
- **Firewall Manager**: Simplified UFW management and status monitoring.
- **Task Queue**: Robust background task handling to ensure the UI remains responsive.

## Application Preview

> **Tip:** Click any image to view it in full resolution.

<!-- Dashboard -->
<p align="center">
  <a href="assets/screenshots/Screenshot%20From%202026-01-31%2000-46-41.png" target="_blank">
    <img src="assets/screenshots/Screenshot%20From%202026-01-31%2000-46-41.png" 
         alt="Dashboard Preview" 
         style="width:100%; max-width:1100px; height:auto; display:block; margin-bottom:20px;">
  </a>
</p>

<!-- Secure Profiles -->
<p align="center">
  <a href="assets/screenshots/Screenshot%20From%202026-01-31%2000-46-51.png" target="_blank">
    <img src="assets/screenshots/Screenshot%20From%202026-01-31%2000-46-51.png" 
         alt="Secure Profiles Preview" 
         style="width:100%; max-width:1100px; height:auto; display:block; margin-bottom:20px;">
  </a>
</p>

<!-- User Management -->
<p align="center">
  <a href="assets/screenshots/Screenshot%20From%202026-01-31%2000-47-18.png" target="_blank">
    <img src="assets/screenshots/Screenshot%20From%202026-01-31%2000-47-18.png" 
         alt="User Management Preview" 
         style="width:100%; max-width:1100px; height:auto; display:block; margin-bottom:20px;">
  </a>
</p>

<!-- Tool Arsenal -->
<p align="center">
  <a href="assets/screenshots/Screenshot%20From%202026-01-31%2000-47-25.png" target="_blank">
    <img src="assets/screenshots/Screenshot%20From%202026-01-31%2000-47-25.png" 
         alt="Tool Arsenal Preview" 
         style="width:100%; max-width:1100px; height:auto; display:block; margin-bottom:20px;">
  </a>
</p>

<!-- Extra / Additional Preview -->
<p align="center">
  <a href="assets/screenshots/Screenshot%20From%202026-01-31%2000-47-32.png" target="_blank">
    <img src="assets/screenshots/Screenshot%20From%202026-01-31%2000-47-32.png" 
         alt="Additional Preview" 
         style="width:100%; max-width:1100px; height:auto; display:block; margin-bottom:20px;">
  </a>
</p>





## Project Structure

```
Linux_Ring/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── core/                       # Backend logic (Managers)
│   ├── __init__.py
│   ├── firewall_manager.py     # Firewall control logic (UFW/Iptables)
│   ├── process_manager.py      # System process monitoring and control
│   ├── profile_manager.py      # Security profile management
│   ├── service_manager.py      # System service management (systemd)
│   ├── sudo_manager.py         # Privilege elevation handling
│   ├── task_queue.py           # Background task processing
│   ├── tool_installer.py       # Security tool installation logic
│   └── user_manager.py         # User and group management
├── ui/                         # PySide6 Frontend
│   ├── __init__.py
│   ├── main_window.py          # Main application window
│   ├── sidebar.py              # Navigation sidebar
│   ├── dashboard.py            # Dashboard view
│   ├── tools_view.py           # Tools management view
│   ├── services_view.py        # Services management view
│   ├── users_view.py           # Users management view
│   ├── processes_view.py       # Processes list view
│   ├── profiles_view.py        # Security profiles view
│   ├── logs_view.py            # Application logs view
│   ├── updates_view.py         # System updates view
│   ├── system_view.py          # System information view
│   ├── task_queue_view.py      # Task queue monitoring view
│   ├── terminal.py             # Embedded terminal widget
│   ├── about_view.py           # About page
│   ├── dialogs.py              # Custom dialogs and popups
│   └── widgets/                # Reusable UI widgets
│       └── charts.py
├── assets/                     # Configuration and Resources
│   ├── styles.qss              # Qt Stylesheet
│   ├── tools_catalog.yml       # Catalog of installable tools
│   └── icons/                  # Application icons
└── logs/                       # Application logs directory
```

## Requirements

- **OS**: Linux (Debian/Kali recommended)
- **Python**: 3.10+
- **Privileges**: Root/Sudo access is required for core system changes (services, packages, firewall).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MaestroNero/Linux_Ring.git
   cd Linux_Ring
   ```

2. **Set up a Virtual Environment:**
   Run the following commands to create and activate a clean virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Start the application from your virtual environment:

```bash
python main.py
```

*Note: The application includes a `SudoManager` to handle privileged operations securely. You may be prompted for your password.*

## Author

**Maestro Nero**

## License

This project is licensed under the MIT License.
