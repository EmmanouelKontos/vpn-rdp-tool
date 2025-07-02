import subprocess
import platform

def launch_rdp(ip_address, username=None):
    system = platform.system()
    try:
        if system == "Windows":
            cmd = ['mstsc.exe', f'/v:{ip_address}']
            if username:
                cmd.extend(['/prompt'])
        elif system == "Linux":
            cmd = ['xfreerdp', f'/v:{ip_address}']
            if username:
                cmd.extend([f'/u:{username}'])
        else:
            return False, f"Unsupported OS: {system}"
        
        subprocess.Popen(cmd)
        return True, f"RDP client launched for {ip_address}"
    except FileNotFoundError:
        return False, "RDP client (mstsc.exe or xfreerdp) not found."
    except Exception as e:
        return False, str(e)
