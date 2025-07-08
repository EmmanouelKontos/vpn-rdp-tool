import socket
import struct
import threading
import time
import subprocess
import platform  # Added for OS detection
from typing import Tuple, List, Dict
import netifaces

def create_magic_packet(mac_address: str) -> bytes:
    """Create a magic packet for Wake-on-LAN."""
    # Remove any non-hex characters and convert to uppercase
    cleaned_mac = ''.join(c for c in mac_address if c in '0123456789ABCDEFabcdef').upper()
    if len(cleaned_mac) != 12:
        raise ValueError("Invalid MAC address format: must be 12 hex digits")

    mac_address = cleaned_mac

    # Create the magic packet (6 bytes of 0xFF followed by 16 repetitions of the MAC address)
    return b'\xFF' * 6 + bytes.fromhex(mac_address) * 16

def get_broadcast_addresses() -> List[str]:
    """Get all broadcast addresses for active network interfaces."""
    broadcast_addresses = []
    for interface in netifaces.interfaces():
        try:
            addrs = netifaces.ifaddresses(interface)
            # Get IPv4 addresses
            if netifaces.AF_INET in addrs:
                for link in addrs[netifaces.AF_INET]:
                    if 'broadcast' in link:
                        broadcast_addresses.append(link['broadcast'])
        except ValueError:
            continue  # Skip invalid interfaces
    return broadcast_addresses

def send_wol_packet(mac_address: str, broadcast_address: str = '255.255.255.255', port: int = 9) -> bool:
    """Send a Wake-on-LAN packet to a specific broadcast address."""
    try:
        magic_packet = create_magic_packet(mac_address)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, (broadcast_address, port))
        return True
    except Exception as e:
        print(f"Error sending WoL packet to {broadcast_address}: {e}")
        return False

def wake_host(mac_address: str, max_attempts: int = 3) -> Tuple[bool, str]:
    """Send Wake-on-LAN packets to all available broadcast addresses."""
    if not mac_address:
        return False, "No MAC address provided"
    
    # Get all available broadcast addresses
    broadcast_addresses = get_broadcast_addresses()
    if not broadcast_addresses:
        broadcast_addresses = ['255.255.255.255']  # Fallback to default
    
    attempts = 0
    for attempt in range(max_attempts):
        attempts += 1
        success_count = 0
        for addr in broadcast_addresses:
            if send_wol_packet(mac_address, addr):
                success_count += 1
        
        if success_count > 0:
            return True, f"Sent {success_count} WoL packets to {mac_address} via {len(broadcast_addresses)} interfaces"
    
    return False, f"Failed to send WoL packets after {max_attempts} attempts"

def check_host_status(ip_address: str, timeout: int = 2) -> str:
    """Check host status using ICMP ping and RDP port check."""
    # First try ICMP ping
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', '-W', str(timeout), ip_address]
        if subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "online"
    except Exception:
        pass
    
    # If ping fails, check RDP port (3389)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_address, 3389))
            if result == 0:
                return "online"
    except Exception:
        pass
    
    return "offline"

def wake_and_verify(mac_address: str, ip_address: str, max_wait: int = 60) -> Tuple[bool, str]:
    """Send WoL packet and verify if host comes online."""
    # Send wake command
    wake_success, wake_message = wake_host(mac_address)
    if not wake_success:
        return False, wake_message
    
    # Check status periodically
    start_time = time.time()
    while time.time() - start_time < max_wait:
        status = check_host_status(ip_address)
        if status == "online":
            return True, "Host is online"
        time.sleep(5)  # Check every 5 seconds
    
    return False, "Host did not come online within timeout period"

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python wol_manager.py <MAC_ADDRESS> [IP_ADDRESS]")
        sys.exit(1)
    
    mac = sys.argv[1]
    ip = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Broadcast addresses: {get_broadcast_addresses()}")
    success, message = wake_host(mac)
    print(f"Wake result: {success} - {message}")
    
    if ip:
        print(f"Host status: {check_host_status(ip)}")
