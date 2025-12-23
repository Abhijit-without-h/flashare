"""QR code generation utilities for Flashare."""

import io
from typing import Optional

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from flashare.core.network import get_server_url


def generate_qr_ascii(url: Optional[str] = None, port: int = 8000) -> str:
    """
    Generate an ASCII art QR code for terminal display.
    
    Args:
        url: The URL to encode. If None, uses the auto-detected server URL.
        port: Server port (used if url is None).
        
    Returns:
        ASCII art representation of the QR code.
    """
    url = url or get_server_url(port)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=1,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Generate ASCII representation
    modules = qr.get_matrix()
    
    lines = []
    for row in modules:
        line = ""
        for cell in row:
            # Use block characters for better visibility
            line += "██" if cell else "  "
        lines.append(line)
    
    return "\n".join(lines)


def generate_qr_svg(url: Optional[str] = None, port: int = 8000) -> str:
    """
    Generate an SVG QR code for web display.
    
    Args:
        url: The URL to encode. If None, uses the auto-detected server URL.
        port: Server port (used if url is None).
        
    Returns:
        SVG string of the QR code.
    """
    url = url or get_server_url(port)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create SVG image
    from qrcode.image.svg import SvgImage
    img = qr.make_image(image_factory=SvgImage)
    
    # Convert to string
    buffer = io.BytesIO()
    img.save(buffer)
    return buffer.getvalue().decode('utf-8')


def generate_qr_png_bytes(url: Optional[str] = None, port: int = 8000) -> bytes:
    """
    Generate a PNG QR code as bytes.
    
    Args:
        url: The URL to encode. If None, uses the auto-detected server URL.
        port: Server port (used if url is None).
        
    Returns:
        PNG image bytes.
    """
    url = url or get_server_url(port)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def get_qr_data(port: int = 8000) -> dict:
    """
    Get QR code data for API response.
    
    Args:
        port: Server port.
        
    Returns:
        Dictionary with URL and QR representations.
    """
    url = get_server_url(port)
    
    return {
        "url": url,
        "ascii": generate_qr_ascii(url),
        "svg": generate_qr_svg(url),
    }
