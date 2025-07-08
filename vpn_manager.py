import subprocess
import platform
import os

def find_wireguard_windows():
    """Search for WireGuard executable in common locations"""
    possible_paths = [
        r"C:\Program Files\WireGuard\wireguard.exe",
        r"C:\Program Files (x86)\WireGuard\wireguard.exe"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    # Fall back to PATH lookup
    return "wireguard.exe"

def connect_vpn(config_path):
    system = platform.system()
    # Attempt to disconnect first to ensure a clean state
    disconnect_vpn(config_path) 
    try:
        if system == "Windows":
            wg_path = find_wireguard_windows()
            cmd = [wg_path, "/installtunnelservice", config_path]
        elif system == "Linux":
            # Use sudo for Linux systems and handle DNS resolver conflicts
            cmd = ["sudo", "wg-quick", "up", config_path]
        else:
            raise OSError(f"Unsupported OS: {system}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Handle DNS resolver conflicts specifically
            if "resolvconf: signature mismatch" in result.stderr:
                # Try to fix resolvconf signature issue
                fix_cmd = ["sudo", "resolvconf", "-u"]
                subprocess.run(fix_cmd, check=False)
                # Retry VPN connection
                result = subprocess.run(cmd, capture_output=True, text=True)
                
        if result.returncode != 0:
            return False, f"VPN connection failed:\n{result.stderr}"
            
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
            wg_path = find_wireguard_windows()
            cmd = [wg_path, "/uninstalltunnelservice", tunnel_name]
        elif system == "Linux":
            # Use sudo for Linux systems
            cmd = ["sudo", "wg-quick", "down", config_path]
        else:
            raise OSError(f"Unsupported OS: {system}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"VPN disconnection failed:\n{result.stderr}"
        return True, f"Successfully disconnected from VPN using {config_path}"
    except FileNotFoundError:
        return False, "WireGuard command not found. Is WireGuard installed and in your PATH?"
    except subprocess.CalledProcessError as e:
        # If the tunnel is not found, it's already disconnected, so we can consider it a success for pre-disconnect
        if "Tunnel not found" in e.stderr or "No such device" in e.stderr:
            return True, f"VPN tunnel {tunnel_name} was not active or already disconnected."
        return False, f"VPN disconnection failed:\n{e.stderr}"
    except Exception as e:
        return False, str(e)
