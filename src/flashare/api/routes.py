"""API routes for Flashare."""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse, Response
import aiofiles

from flashare.config import config
from flashare.core.compression import generate_compressed_stream
from flashare.core.qr import get_qr_data, generate_qr_png_bytes
from flashare.core.network import get_server_url


router = APIRouter()


@router.get("/api/files")
async def list_files():
    """
    List all available files in the uploads directory.
    
    Returns:
        List of file information dictionaries.
    """
    files = []
    
    if config.uploads_dir.exists():
        for file_path in config.uploads_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "size_human": _format_size(stat.st_size),
                    "modified": stat.st_mtime,
                })
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    return files


@router.get("/api/download/{filename}")
async def download_file(filename: str, compressed: bool = True):
    """
    Download a file with optional Zstandard compression.
    
    Args:
        filename: Name of the file to download.
        compressed: Whether to use Zstd compression (default: True).
        
    Returns:
        StreamingResponse with the file content.
    """
    file_path = config.uploads_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    # Security: ensure the path is within uploads directory
    try:
        file_path.resolve().relative_to(config.uploads_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if compressed:
        # Stream with Zstandard compression
        return StreamingResponse(
            generate_compressed_stream(file_path),
            media_type="application/octet-stream",
            headers={
                "Content-Encoding": "zstd",
                "Content-Disposition": f'attachment; filename="{filename}"',
            }
        )
    else:
        # Stream without compression
        async def file_iterator():
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(config.chunk_size):
                    yield chunk
        
        return StreamingResponse(
            file_iterator(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_path.stat().st_size),
            }
        )


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file from the phone to the laptop.
    
    Args:
        file: The uploaded file.
        
    Returns:
        Upload result information.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Sanitize filename
    safe_filename = Path(file.filename).name
    file_path = config.uploads_dir / safe_filename
    
    # Handle duplicate filenames
    counter = 1
    original_stem = file_path.stem
    while file_path.exists():
        file_path = config.uploads_dir / f"{original_stem}_{counter}{file_path.suffix}"
        counter += 1
    
    # Save the file
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(config.chunk_size):
            await f.write(chunk)
    
    return {
        "success": True,
        "filename": file_path.name,
        "size": file_path.stat().st_size,
        "size_human": _format_size(file_path.stat().st_size),
    }


@router.get("/api/qr")
async def get_qr():
    """
    Get QR code data for connecting to the server.
    
    Returns:
        QR code information including URL and encodings.
    """
    return get_qr_data(config.port)


@router.get("/api/qr.png")
async def get_qr_image():
    """
    Get QR code as PNG image.
    
    Returns:
        PNG image of the QR code.
    """
    png_bytes = generate_qr_png_bytes(port=config.port)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/api/status")
async def get_status():
    """
    Get server status and information.
    
    Returns:
        Server status information.
    """
    return {
        "status": "online",
        "url": get_server_url(config.port),
        "uploads_dir": str(config.uploads_dir),
        "file_count": len(list(config.uploads_dir.glob("*"))),
    }


@router.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """
    Delete a file from the uploads directory.
    
    Args:
        filename: Name of the file to delete.
        
    Returns:
        Deletion result.
    """
    file_path = config.uploads_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check
    try:
        file_path.resolve().relative_to(config.uploads_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path.unlink()
    
    return {"success": True, "deleted": filename}


def _format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
