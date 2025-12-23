"""Rich terminal UI components for Flashare."""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich import box
from pathlib import Path
from typing import Optional

from flashare import __app_name__, __version__
from flashare.core.qr import generate_qr_ascii
from flashare.core.network import get_server_url


# Global console instance
console = Console()


def print_banner():
    """Print the Flashare banner."""
    banner = Text()
    banner.append("⚡ ", style="yellow bold")
    banner.append(__app_name__, style="cyan bold")
    banner.append(f" v{__version__}", style="dim")
    
    console.print(Panel(
        banner,
        box=box.ROUNDED,
        padding=(0, 2),
        border_style="blue",
    ))


def print_qr_code(port: int = 8000):
    """
    Display QR code in the terminal.
    
    Args:
        port: Server port number.
    """
    url = get_server_url(port)
    qr_ascii = generate_qr_ascii(port=port)
    
    console.print()
    console.print(Panel(
        qr_ascii,
        title="[bold cyan]📱 Scan to Connect[/]",
        subtitle=f"[link={url}]{url}[/link]",
        box=box.DOUBLE,
        border_style="green",
        padding=(1, 2),
    ))
    console.print()


def print_server_info(host: str, port: int):
    """
    Display server connection information.
    
    Args:
        host: Server host.
        port: Server port.
    """
    url = get_server_url(port)
    
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column("Label", style="dim")
    table.add_column("Value", style="bold")
    
    table.add_row("🌐 Server", url)
    table.add_row("📡 Host", host)
    table.add_row("🔌 Port", str(port))
    
    console.print(table)


def print_file_ready(filename: str, size: int):
    """
    Display file ready for transfer.
    
    Args:
        filename: Name of the file.
        size: File size in bytes.
    """
    size_str = _format_size(size)
    
    console.print()
    console.print(Panel(
        f"[bold green]✓[/] Ready to share: [cyan]{filename}[/] ({size_str})",
        box=box.ROUNDED,
        border_style="green",
    ))


def print_optimization_result(
    input_file: str,
    output_file: str,
    input_size: int,
    output_size: int,
):
    """
    Display video optimization results.
    
    Args:
        input_file: Original filename.
        output_file: Optimized filename.
        input_size: Original size in bytes.
        output_size: Optimized size in bytes.
    """
    reduction = ((input_size - output_size) / input_size) * 100
    
    table = Table(title="📹 Video Optimization", box=box.ROUNDED)
    table.add_column("", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    
    table.add_row("Original", input_file, _format_size(input_size))
    table.add_row("Optimized", output_file, _format_size(output_size))
    table.add_row("", "", f"[green]-{reduction:.1f}%[/]")
    
    console.print()
    console.print(table)


def print_error(message: str):
    """Display an error message."""
    console.print(f"[bold red]✗ Error:[/] {message}")


def print_warning(message: str):
    """Display a warning message."""
    console.print(f"[yellow]⚠ Warning:[/] {message}")


def print_success(message: str):
    """Display a success message."""
    console.print(f"[bold green]✓[/] {message}")


def print_info(message: str):
    """Display an info message."""
    console.print(f"[blue]ℹ[/] {message}")


def confirm(prompt: str, default: bool = True) -> bool:
    """
    Ask for user confirmation.
    
    Args:
        prompt: The question to ask.
        default: Default answer if user just presses Enter.
        
    Returns:
        True if confirmed, False otherwise.
    """
    suffix = " [Y/n]" if default else " [y/N]"
    
    try:
        response = console.input(f"{prompt}{suffix} ").strip().lower()
        
        if not response:
            return default
        
        return response in ('y', 'yes')
    except (KeyboardInterrupt, EOFError):
        return False


def create_progress() -> Progress:
    """Create a Rich progress bar for file operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def _format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
