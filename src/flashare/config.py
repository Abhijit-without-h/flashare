"""Flashare configuration management."""

import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Config:
    """Application configuration."""
    
    host: str = "0.0.0.0"
    port: int = 8000
    uploads_dir: Path = field(default_factory=lambda: Path.cwd() / "uploads")
    static_dir: Path = field(default_factory=lambda: Path(__file__).parent / "static")
    
    # FFmpeg settings
    ffmpeg_preset: str = "ultrafast"
    ffmpeg_crf: int = 28
    video_extensions: tuple = (".mov", ".mkv", ".avi", ".mp4", ".webm")
    
    # Compression settings
    zstd_level: int = 3
    chunk_size: int = 1024 * 64  # 64KB chunks
    
    def __post_init__(self):
        """Ensure uploads directory exists."""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
