"""BLE advertising utilities for Flashare."""

import asyncio
from typing import Optional

from flashare.core.network import get_server_url


# BLE Service UUID for Flashare
FLASHARE_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"


class BLEAdvertiser:
    """
    BLE advertiser for broadcasting the server URL.
    
    This allows Android devices to discover the Flashare server
    automatically via Bluetooth Low Energy.
    """
    
    def __init__(self, port: int = 8000):
        """
        Initialize the BLE advertiser.
        
        Args:
            port: The server port to advertise.
        """
        self.port = port
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
    @property
    def server_url(self) -> str:
        """Get the server URL to advertise."""
        return get_server_url(self.port)
    
    async def start(self) -> None:
        """Start advertising the BLE service."""
        if self.running:
            return
            
        self.running = True
        self._task = asyncio.create_task(self._advertise_loop())
        
    async def stop(self) -> None:
        """Stop the BLE advertising."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _advertise_loop(self) -> None:
        """
        Main advertising loop.
        
        Note: Full BLE GATT server implementation requires platform-specific
        code. This provides a basic structure that can be extended.
        """
        try:
            # Import bleak here to make it optional
            from bleak import BleakScanner
            
            print(f"🔵 BLE advertising on: {self.server_url}")
            print(f"   Service UUID: {FLASHARE_SERVICE_UUID}")
            
            # In a full implementation, we would:
            # 1. Create a GATT server with a characteristic containing the URL
            # 2. Advertise the service UUID
            # For now, we just keep the task running as a placeholder
            
            while self.running:
                # Heartbeat - in production, this would manage the GATT server
                await asyncio.sleep(1)
                
        except ImportError:
            print("⚠️  BLE not available (bleak not installed)")
        except Exception as e:
            print(f"⚠️  BLE advertising error: {e}")


async def start_ble_advertiser(port: int = 8000) -> BLEAdvertiser:
    """
    Create and start a BLE advertiser.
    
    Args:
        port: The server port to advertise.
        
    Returns:
        The running BLEAdvertiser instance.
    """
    advertiser = BLEAdvertiser(port)
    await advertiser.start()
    return advertiser
