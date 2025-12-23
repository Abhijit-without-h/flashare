"""Zstandard compression utilities for Flashare."""

from pathlib import Path
from typing import Generator, BinaryIO
import zstandard as zstd

from flashare.config import config


def create_compressor(level: int | None = None) -> zstd.ZstdCompressor:
    """
    Create a Zstandard compressor instance.
    
    Args:
        level: Compression level (1-22). Higher = better compression, slower.
        
    Returns:
        A ZstdCompressor instance.
    """
    return zstd.ZstdCompressor(level=level or config.zstd_level)


def generate_compressed_stream(
    file_path: Path | str,
    chunk_size: int | None = None
) -> Generator[bytes, None, None]:
    """
    Generate compressed chunks from a file using Zstandard.
    
    This is designed for streaming responses - yields compressed
    chunks that can be sent directly to HTTP clients.
    
    Args:
        file_path: Path to the file to compress.
        chunk_size: Size of chunks to read. Defaults to config value.
        
    Yields:
        Compressed byte chunks.
    """
    chunk_size = chunk_size or config.chunk_size
    compressor = create_compressor()
    
    with open(file_path, 'rb') as f_in:
        for chunk in compressor.read_to_iter(f_in, size=chunk_size):
            yield chunk


def compress_file(input_path: Path | str, output_path: Path | str) -> Path:
    """
    Compress a file completely using Zstandard.
    
    Args:
        input_path: Path to the input file.
        output_path: Path for the compressed output file.
        
    Returns:
        Path to the compressed file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    compressor = create_compressor()
    
    with open(input_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            compressor.copy_stream(f_in, f_out)
    
    return output_path


def decompress_stream(
    input_stream: BinaryIO,
    chunk_size: int | None = None
) -> Generator[bytes, None, None]:
    """
    Decompress a Zstandard stream.
    
    Args:
        input_stream: A file-like object with compressed data.
        chunk_size: Size of chunks to yield.
        
    Yields:
        Decompressed byte chunks.
    """
    chunk_size = chunk_size or config.chunk_size
    decompressor = zstd.ZstdDecompressor()
    
    for chunk in decompressor.read_to_iter(input_stream, size=chunk_size):
        yield chunk
