# Linux Ring

**Linux Ring** is a comprehensive, professional GUI application designed to manage, harden, and monitor Linux environments (specifically tailored for Kali Linux). Built by **Maestro Nero**, this tool leverages Python 3 and PySide6 to provide a seamless, modern interface for system administration tasks.

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

## Project Structure

```
Linux_Ring/
├── main.py                 # Application entry point
├── core/                   # Backend logic (Managers)
│   ├── firewall_manager.py
│   ├── service_manager.py
│   ├── tool_installer.py
│   └── ...
├── ui/                     # PySide6 Frontend
│   ├── main_window.py
│   ├── dashboard.py
│   └── [feature]_view.py
├── assets/                 # Configuration and Styles
└── logs/                   # Application logs
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
