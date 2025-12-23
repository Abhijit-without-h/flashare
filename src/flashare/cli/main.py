"""Main CLI entry point for Flashare."""

import argparse
import shutil
import sys
from pathlib import Path

from flashare import __version__, __app_name__
from flashare.config import config
from flashare.cli.fzf import select_file, is_fzf_available
from flashare.cli.ui import (
    console,
    print_banner,
    print_qr_code,
    print_server_info,
    print_file_ready,
    print_optimization_result,
    print_error,
    print_warning,
    print_success,
    print_info,
    confirm,
    create_progress,
)
from flashare.core.ffmpeg import is_video_file, optimize_video, is_ffmpeg_available
from flashare.core.network import get_server_url


def main():
    """Main entry point for the share command."""
    parser = argparse.ArgumentParser(
        prog="share",
        description=f"{__app_name__} - CLI-First Hybrid File Sharing Tool",
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{__app_name__} {__version__}",
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        help="File to share (opens fzf selector if not provided)",
    )
    
    parser.add_argument(
        "-s", "--server-only",
        action="store_true",
        help="Start server only without file selection",
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=config.port,
        help=f"Server port (default: {config.port})",
    )
    
    parser.add_argument(
        "-H", "--host",
        default=config.host,
        help=f"Server host (default: {config.host})",
    )
    
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Skip video optimization even for video files",
    )
    
    parser.add_argument(
        "-d", "--directory",
        type=Path,
        default=Path.cwd(),
        help="Starting directory for file selection",
    )
    
    args = parser.parse_args()
    
    # Update config with CLI arguments
    config.port = args.port
    config.host = args.host
    
    # Print banner
    print_banner()
    
    # Check for required tools
    if not is_fzf_available():
        print_warning("fzf not found. Install with: brew install fzf")
    
    if not is_ffmpeg_available():
        print_warning("ffmpeg not found. Video optimization disabled.")
    
    # Server-only mode
    if args.server_only:
        _start_server(args.host, args.port)
        return
    
    # Get file to share
    file_path = None
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            sys.exit(1)
    else:
        # Use fzf to select file
        print_info("Select a file to share...")
        file_path = select_file(start_dir=args.directory)
        
        if not file_path:
            print_warning("No file selected. Starting server with existing files...")
            _start_server(args.host, args.port)
            return
    
    # Process the file
    console.print()
    print_info(f"Selected: [cyan]{file_path.name}[/]")
    
    final_path = file_path
    
    # Check if video and offer optimization
    if is_video_file(file_path) and not args.no_optimize and is_ffmpeg_available():
        if confirm("Would you like to optimize this video for faster transfer?"):
            with create_progress() as progress:
                task = progress.add_task("Optimizing video...", total=None)
                
                result = optimize_video(file_path)
                
                progress.update(task, completed=100)
            
            if result.success and result.output_path:
                print_optimization_result(
                    file_path.name,
                    result.output_path.name,
                    result.input_size,
                    result.output_size or 0,
                )
                final_path = result.output_path
            else:
                print_error(f"Optimization failed: {result.error}")
                print_info("Using original file instead.")
    
    # Copy to uploads directory
    dest_path = config.uploads_dir / final_path.name
    
    # Handle duplicates
    counter = 1
    original_stem = dest_path.stem
    while dest_path.exists():
        dest_path = config.uploads_dir / f"{original_stem}_{counter}{dest_path.suffix}"
        counter += 1
    
    shutil.copy2(final_path, dest_path)
    
    print_file_ready(dest_path.name, dest_path.stat().st_size)
    
    # Start server
    _start_server(args.host, args.port)


def _start_server(host: str, port: int):
    """Start the FastAPI server."""
    from flashare.server import run_server
    
    console.print()
    print_server_info(host, port)
    print_qr_code(port)
    
    print_info("Starting server... Press [bold]Ctrl+C[/] to stop.")
    console.print()
    
    try:
        run_server(host, port)
    except KeyboardInterrupt:
        console.print()
        print_success("Server stopped. Goodbye!")


if __name__ == "__main__":
    main()
