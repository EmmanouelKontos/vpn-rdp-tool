import subprocess
import platform

def get_vpn_command():
    system = platform.system()
    if system == "Windows":
        return ["wg-quick"]
    elif system == "Linux":
        return ["wg-quick"]
    else:
        raise OSError(f"Unsupported OS: {system}")

def connect_vpn(config_path):
    try:
        cmd = get_vpn_command() + ["up", config_path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, f"Successfully connected to VPN using {config_path}"
    except FileNotFoundError:
        return False, "WireGuard command not found. Is WireGuard installed and in your PATH?"
    except subprocess.CalledProcessError as e:
        return False, f"VPN connection failed:\n{e.stderr}"
    except Exception as e:
        return False, str(e)

def disconnect_vpn(config_path):
    try:
        cmd = get_vpn_command() + ["down", config_path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, f"Successfully disconnected from VPN using {config_path}"
    except FileNotFoundError:
        return False, "WireGuard command not found. Is WireGuard installed and in your PATH?"
    except subprocess.CalledProcessError as e:
        return False, f"VPN disconnection failed:\n{e.stderr}"
    except Exception as e:
        return False, str(e)
