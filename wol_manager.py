from wakeonlan import send_magic_packet

def wake_host(mac_address):
    try:
        send_magic_packet(mac_address)
        return True, f"Magic packet sent to {mac_address}"
    except Exception as e:
        return False, str(e)
