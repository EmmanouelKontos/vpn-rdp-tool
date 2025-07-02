# Universal VPN & RDP Tool

A cross-platform desktop application for managing WireGuard VPN connections, sending Wake-on-LAN (WOL) packets, and launching Remote Desktop Protocol (RDP) clients with a clean and modern user interface.

![Screenshot](screenshot.png) <!-- You can add a screenshot of the app here -->

## Features

- **Modern UI:** Built with CustomTkinter for a sleek and theme-adaptable interface.
- **VPN Control:** Easily connect to and disconnect from WireGuard VPNs.
- **Wake-on-LAN:** Wake up remote machines on your network.
- **RDP Launch:** Quickly start a remote desktop session to your configured hosts.
- **Dynamic Configuration:** Manage all your settings through a user-friendly GUI.
- **Real-time Logging:** An activity log provides clear feedback on all operations.
- **Standalone Executable:** Packaged with PyInstaller for easy distribution and use without needing to install Python or any dependencies.

## Getting Started

### Using the Executable

1.  **Download the Executable:** Grab the latest version for your operating system from the [Releases](https://github.com/YourUsername/vpn-rdp-tool/releases) page.
2.  **Run the Application:** Double-click the `UniversalVPNTool` executable to start it.
3.  **Configure:** On the first launch, a `config.json` file will be created in the same directory as the executable. Use the **Settings** tab in the application to configure your WireGuard path and host profiles.

### Configuration (`config.json`)

The application uses a `config.json` file to store your settings. You can edit this file manually or manage it through the app's **Settings** tab.

```json
{
    "wireguard_config_path": "/path/to/your/wireguard.conf",
    "hosts": [
        {
            "name": "Workstation",
            "ip_address": "192.168.1.101",
            "mac_address": "00:1A:2B:3C:4D:5E",
            "rdp_user": "myuser"
        },
        {
            "name": "Home Server",
            "ip_address": "10.0.0.5",
            "mac_address": "F6:E5:D4:C3:B2:A1",
            "rdp_user": "admin"
        }
    ]
}
```

## For Developers

If you want to run the application from the source or contribute to its development, follow these steps.

### Prerequisites

- Python 3.8+
- Pip
- Git

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YourUsername/vpn-rdp-tool.git
    cd vpn-rdp-tool
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python main.py
    ```

### Building the Executable

To build the standalone executable from the source, make sure you have PyInstaller installed (`pip install pyinstaller`).

Then, run the build command:

```bash
pyinstaller --name UniversalVPNTool --onefile --windowed --add-data 'icon_cache:icon_cache' main.py
```

The final executable will be located in the `dist` directory.

**Note on Cross-Compilation:** To build the Windows executable, you must run the PyInstaller command on a Windows machine. To build the Linux executable, you must run it on a Linux machine.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
