import subprocess
import platform
import os

def connect_vpn(config_path):
    system = platform.system()
    try:
        if system == "Windows":
            cmd = ["C:\\Program Files\\WireGuard\\wireguard.exe", "/installtunnelservice", config_path]
        elif system == "Linux":
            cmd = ["wg-quick", "up", config_path]
        else:
            raise OSError(f"Unsupported OS: {system}")

        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, f"Successfully connected to VPN using {config_path}"
    except FileNotFoundError:
        return False, "WireGuard command not found. Is WireGuard installed and in your PATH?"
    except subprocess.CalledProcessError as e:
        return False, f"VPN connection failed:\n{e.stderr}"
    except Exception as e:
        return False, str(e)

def disconnect_vpn(config_path):
    system = platform.system()
    try:
        tunnel_name = os.path.splitext(os.path.basename(config_path))[0]
        if system == "Windows":
            cmd = ["C:\\Program Files\\WireGuard\\wireguard.exe", "/uninstalltunnelservice", tunnel_name]
        elif system == "Linux":
            cmd = ["wg-quick", "down", config_path]
        else:
            raise OSError(f"Unsupported OS: {system}")

        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, f"Successfully disconnected from VPN using {config_path}"
    except FileNotFoundError:
        return False, "WireGuard command not found. Is WireGuard installed and in your PATH?"
    except subprocess.CalledProcessError as e:
        return False, f"VPN disconnection failed:\n{e.stderr}"
    except Exception as e:
        return False, str(e)
