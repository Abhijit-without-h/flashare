"""Main CLI entry point for Flashare."""

import argparse
import shutil
import sys
from pathlib import Path

from flashare import __version__, __app_name__
from flashare.config import config
from flashare.cli.fzf import select_multiple_files, is_fzf_available
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
    """Main entry point for the flashare command."""
    parser = argparse.ArgumentParser(
        prog="flashare",
        description=f"{__app_name__} - CLI-First Hybrid File Sharing Tool",
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{__app_name__} {__version__}",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Send command
    send_parser = subparsers.add_parser("send", help="Send files or folders")
    send_parser.add_argument(
        "files",
        nargs="*",
        help="Files to share (opens fzf selector if not provided)",
    )
    send_parser.add_argument(
        "-p", "--port",
        type=int,
        default=config.port,
        help=f"Server port (default: {config.port})",
    )
    send_parser.add_argument(
        "-H", "--host",
        default=config.host,
        help=f"Server host (default: {config.host})",
    )
    send_parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Skip video optimization even for video files",
    )
    send_parser.add_argument(
        "-d", "--directory",
        type=Path,
        default=Path.cwd(),
        help="Starting directory for file selection",
    )
    
    # Receive command
    receive_parser = subparsers.add_parser("receive", help="Receive files (starts server)")
    receive_parser.add_argument(
        "-p", "--port",
        type=int,
        default=config.port,
        help=f"Server port (default: {config.port})",
    )
    receive_parser.add_argument(
        "-H", "--host",
        default=config.host,
        help=f"Server host (default: {config.host})",
    )
    
    # Version command
    subparsers.add_parser("version", help="Show version information")
    
    args = parser.parse_args()
    
    # Handle version command
    if args.command == "version":
        print(f"{__app_name__} {__version__}")
        return
    
    # Default to 'send' if no command provided
    if not args.command:
        # Re-parse or manually set defaults for 'send'
        # For simplicity, we'll treat no command as 'send' with no files
        command = "send"
        files_to_share = []
        port = config.port
        host = config.host
        no_optimize = False
        directory = Path.cwd()
    else:
        command = args.command
        port = args.port
        host = args.host
        if command == "send":
            files_to_share = args.files
            no_optimize = args.no_optimize
            directory = args.directory
    
    # Update config with CLI arguments
    config.port = port
    config.host = host
    
    # Print banner
    print_banner()
    
    # Check for required tools
    if not is_fzf_available():
        print_warning("fzf not found. Install with: brew install fzf")
    
    if not is_ffmpeg_available():
        print_warning("ffmpeg not found. Video optimization disabled.")
    
    # Receive mode (equivalent to server-only)
    if command == "receive":
        _start_server(host, port)
        return
    
    # Get files to share
    file_paths = []
    
    if files_to_share:
        for f in files_to_share:
            p = Path(f)
            if not p.exists():
                print_error(f"File not found: {f}")
                sys.exit(1)
            file_paths.append(p)
    else:
        # Use fzf to select files
        print_info("Select files to share (Press TAB to select multiple)...")
        file_paths = select_multiple_files(start_dir=directory)
        
        if not file_paths:
            print_warning("No files selected. Starting server with existing files...")
            _start_server(host, port)
            return
    
    # Process each file
    for file_path in file_paths:
        console.print()
        print_info(f"Processing: [cyan]{file_path.name}[/]")
        
        final_path = file_path
        
        # Check if video and offer optimization
        if is_video_file(file_path) and not no_optimize and is_ffmpeg_available():
            if confirm(f"Optimize {file_path.name} for faster transfer?"):
                with create_progress() as progress:
                    task = progress.add_task(f"Optimizing {file_path.name}...", total=None)
                    
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
    _start_server(host, port)


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
