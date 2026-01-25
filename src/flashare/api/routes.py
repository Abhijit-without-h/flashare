"""API routes for Flashare - Enhanced with parallel processing and batch uploads."""

import os
import asyncio
from pathlib import Path
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor
import functools

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse, Response
import aiofiles

from flashare.config import config
from flashare.core.compression import generate_compressed_stream
from flashare.core.qr import get_qr_data, generate_qr_png_bytes
from flashare.core.network import get_server_url


router = APIRouter()

# Thread pool for CPU-bound operations
executor = ThreadPoolExecutor(max_workers=4)


# ==================== Utility Functions (Lambda-style) ====================

format_size = lambda size_bytes: (
    f"{size_bytes:.1f} B" if size_bytes < 1024 else
    f"{size_bytes/1024:.1f} KB" if size_bytes < 1024**2 else
    f"{size_bytes/1024**2:.1f} MB" if size_bytes < 1024**3 else
    f"{size_bytes/1024**3:.1f} GB"
)

get_file_extension = lambda filename: Path(filename).suffix.lower()[1:] if Path(filename).suffix else ""

is_image = lambda filename: get_file_extension(filename) in {"jpg", "jpeg", "png", "gif", "webp", "svg", "heic", "bmp"}
is_video = lambda filename: get_file_extension(filename) in {"mp4", "mov", "avi", "mkv", "webm", "m4v"}
is_audio = lambda filename: get_file_extension(filename) in {"mp3", "wav", "flac", "aac", "ogg", "m4a"}
is_document = lambda filename: get_file_extension(filename) in {"pdf", "doc", "docx", "txt", "rtf", "md", "xls", "xlsx", "csv"}


def get_file_type(filename: str) -> str:
    """Categorize file by type using lambda predicates."""
    predicates = [
        (is_image, "image"),
        (is_video, "video"),
        (is_audio, "audio"),
        (is_document, "document"),
    ]
    return next((category for predicate, category in predicates if predicate(filename)), "file")


async def run_in_executor(func, *args):
    """Run blocking function in thread pool executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, functools.partial(func, *args))


# ==================== File Operations ====================

async def _save_uploaded_file(file: UploadFile) -> dict:
    """
    Save an uploaded file and return result.
    
    Uses efficient chunked writing for large files.
    """
    if not file.filename:
        return {"success": False, "error": "No filename provided"}
    
    # Sanitize filename
    safe_filename = Path(file.filename).name
    file_path = config.uploads_dir / safe_filename
    
    # Handle duplicate filenames
    counter = 1
    original_stem = file_path.stem
    while file_path.exists():
        file_path = config.uploads_dir / f"{original_stem}_{counter}{file_path.suffix}"
        counter += 1
    
    try:
        # Save the file with async I/O
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(config.chunk_size):
                await f.write(chunk)
        
        stat = file_path.stat()
        return {
            "success": True,
            "filename": file_path.name,
            "size": stat.st_size,
            "size_human": format_size(stat.st_size),
            "type": get_file_type(file_path.name),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "filename": safe_filename}


async def _get_file_info(file_path: Path) -> dict:
    """Get file info dictionary - async-optimized."""
    stat = await run_in_executor(file_path.stat)
    return {
        "name": file_path.name,
        "size": stat.st_size,
        "size_human": format_size(stat.st_size),
        "modified": stat.st_mtime,
        "type": get_file_type(file_path.name),
    }


# ==================== API Endpoints ====================

@router.get("/api/files")
async def list_files():
    """
    List all available files in the uploads directory.
    
    Uses parallel processing for faster file stat operations.
    
    Returns:
        List of file information dictionaries sorted by modification time.
    """
    if not config.uploads_dir.exists():
        return []
    
    # Get list of file paths
    file_paths = [
        f for f in config.uploads_dir.iterdir() 
        if f.is_file() and not f.name.startswith('.')
    ]
    
    if not file_paths:
        return []
    
    # Process files in parallel using asyncio.gather
    tasks = [_get_file_info(fp) for fp in file_paths]
    files = await asyncio.gather(*tasks)
    
    # Sort by modification time (newest first) using lambda
    files_sorted = sorted(files, key=lambda x: x["modified"], reverse=True)
    
    return files_sorted


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
        return StreamingResponse(
            generate_compressed_stream(file_path),
            media_type="application/octet-stream",
            headers={
                "Content-Encoding": "zstd",
                "Content-Disposition": f'attachment; filename="{filename}"',
            }
        )
    else:
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
    Upload a single file from the phone to the laptop.
    
    Args:
        file: The uploaded file.
        
    Returns:
        Upload result information.
    """
    result = await _save_uploaded_file(file)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Upload failed"))
    
    return result


@router.post("/api/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple files simultaneously with parallel processing.
    
    Uses asyncio.gather for concurrent file saving operations.
    
    Args:
        files: List of files to upload.
        
    Returns:
        Batch upload results with summary.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Process all files in parallel
    tasks = [_save_uploaded_file(file) for file in files]
    results = await asyncio.gather(*tasks)
    
    # Compute summary using filter lambdas
    successful = list(filter(lambda r: r["success"], results))
    failed = list(filter(lambda r: not r["success"], results))
    
    total_size = sum(map(lambda r: r.get("size", 0), successful))
    
    return {
        "success": len(failed) == 0,
        "files": results,
        "summary": {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "total_size": total_size,
            "total_size_human": format_size(total_size),
        }
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
    
    Runs PNG generation in executor to avoid blocking.
    
    Returns:
        PNG image of the QR code.
    """
    png_bytes = await run_in_executor(generate_qr_png_bytes, config.port)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/api/status")
async def get_status():
    """
    Get server status and information.
    
    Returns:
        Server status information including file count and storage stats.
    """
    files = list(config.uploads_dir.glob("*")) if config.uploads_dir.exists() else []
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    
    return {
        "status": "online",
        "url": get_server_url(config.port),
        "uploads_dir": str(config.uploads_dir),
        "file_count": len(files),
        "total_size": total_size,
        "total_size_human": format_size(total_size),
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
    
    # Use executor for file deletion (blocking I/O)
    await run_in_executor(file_path.unlink)
    
    return {"success": True, "deleted": filename}


@router.delete("/api/files")
async def delete_multiple_files(filenames: List[str]):
    """
    Delete multiple files from the uploads directory.
    
    Uses parallel processing for batch deletions.
    
    Args:
        filenames: List of filenames to delete.
        
    Returns:
        Batch deletion results.
    """
    async def delete_single(filename: str) -> dict:
        file_path = config.uploads_dir / filename
        
        if not file_path.exists():
            return {"filename": filename, "success": False, "error": "File not found"}
        
        try:
            file_path.resolve().relative_to(config.uploads_dir.resolve())
        except ValueError:
            return {"filename": filename, "success": False, "error": "Access denied"}
        
        try:
            await run_in_executor(file_path.unlink)
            return {"filename": filename, "success": True}
        except Exception as e:
            return {"filename": filename, "success": False, "error": str(e)}
    
    # Process deletions in parallel
    tasks = [delete_single(fn) for fn in filenames]
    results = await asyncio.gather(*tasks)
    
    successful = len(list(filter(lambda r: r["success"], results)))
    
    return {
        "success": successful == len(filenames),
        "results": results,
        "summary": {
            "total": len(filenames),
            "successful": successful,
            "failed": len(filenames) - successful,
        }
    }
