"""Network utilities for Flashare."""

import socket
from functools import lru_cache


@lru_cache(maxsize=1)
def get_local_ip() -> str:
    """
    Auto-detect the local IP address for QR codes and BLE advertising.
    
    Returns:
        The local IP address as a string.
    """
    try:
        # Create a socket connection to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        # Connect to a public DNS to get the outbound IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to localhost
        return "127.0.0.1"


def get_server_url(port: int = 8000) -> str:
    """
    Get the full server URL.
    
    Args:
        port: The server port number.
        
    Returns:
        The complete server URL.
    """
    return f"http://{get_local_ip()}:{port}"
