"""FFmpeg video optimization utilities for Flashare."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from flashare.config import config


@dataclass
class OptimizationResult:
    """Result of a video optimization operation."""
    success: bool
    input_path: Path
    output_path: Optional[Path]
    input_size: int
    output_size: Optional[int]
    error: Optional[str] = None
    
    @property
    def compression_ratio(self) -> Optional[float]:
        """Get the compression ratio (input/output size)."""
        if self.output_size and self.output_size > 0:
            return self.input_size / self.output_size
        return None
    
    @property
    def size_reduction_percent(self) -> Optional[float]:
        """Get the percentage size reduction."""
        if self.output_size is not None:
            return ((self.input_size - self.output_size) / self.input_size) * 100
        return None


def is_ffmpeg_available() -> bool:
    """Check if FFmpeg is available on the system."""
    return shutil.which("ffmpeg") is not None


def is_video_file(file_path: Path | str) -> bool:
    """
    Check if a file is a video based on extension.
    
    Args:
        file_path: Path to the file to check.
        
    Returns:
        True if the file appears to be a video.
    """
    file_path = Path(file_path)
    return file_path.suffix.lower() in config.video_extensions


def optimize_video(
    input_path: Path | str,
    output_path: Optional[Path | str] = None,
    preset: Optional[str] = None,
    crf: Optional[int] = None,
) -> OptimizationResult:
    """
    Optimize a video file using FFmpeg with H.265 encoding.
    
    Args:
        input_path: Path to the input video file.
        output_path: Path for the output file. If None, creates .optimized.mp4.
        preset: FFmpeg preset (ultrafast, superfast, veryfast, faster, fast,
                medium, slow, slower, veryslow). Defaults to config value.
        crf: Constant Rate Factor (0-51, lower = better quality).
             Defaults to config value.
    
    Returns:
        OptimizationResult with details about the operation.
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        return OptimizationResult(
            success=False,
            input_path=input_path,
            output_path=None,
            input_size=0,
            output_size=None,
            error=f"Input file not found: {input_path}"
        )
    
    if not is_ffmpeg_available():
        return OptimizationResult(
            success=False,
            input_path=input_path,
            output_path=None,
            input_size=input_path.stat().st_size,
            output_size=None,
            error="FFmpeg is not installed or not in PATH"
        )
    
    # Determine output path
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}.optimized.mp4"
    else:
        output_path = Path(output_path)
    
    # Get input file size
    input_size = input_path.stat().st_size
    
    # Build FFmpeg command
    preset = preset or config.ffmpeg_preset
    crf = crf or config.ffmpeg_crf
    
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-vcodec", "libx265",
        "-crf", str(crf),
        "-preset", preset,
        "-acodec", "aac",
        "-y",  # Overwrite output
        str(output_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            return OptimizationResult(
                success=False,
                input_path=input_path,
                output_path=output_path,
                input_size=input_size,
                output_size=None,
                error=f"FFmpeg error: {result.stderr[:500]}"
            )
        
        output_size = output_path.stat().st_size
        
        return OptimizationResult(
            success=True,
            input_path=input_path,
            output_path=output_path,
            input_size=input_size,
            output_size=output_size,
        )
        
    except subprocess.TimeoutExpired:
        return OptimizationResult(
            success=False,
            input_path=input_path,
            output_path=output_path,
            input_size=input_size,
            output_size=None,
            error="FFmpeg operation timed out"
        )
    except Exception as e:
        return OptimizationResult(
            success=False,
            input_path=input_path,
            output_path=output_path,
            input_size=input_size,
            output_size=None,
            error=str(e)
        )


def get_video_info(file_path: Path | str) -> Optional[dict]:
    """
    Get video file information using FFprobe.
    
    Args:
        file_path: Path to the video file.
        
    Returns:
        Dictionary with video info, or None if unavailable.
    """
    if not shutil.which("ffprobe"):
        return None
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        return None
    
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except Exception:
        pass
    
    return None
