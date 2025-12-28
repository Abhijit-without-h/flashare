"""Rich terminal UI components for Flashare - Modern aesthetic terminal experience."""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.rule import Rule
from rich import box
from pathlib import Path
from typing import Optional
from datetime import datetime

from flashare import __app_name__, __version__
from flashare.core.qr import generate_qr_ascii
from flashare.core.network import get_server_url


# Global console instance with better styling
console = Console(
    force_terminal=True,
    legacy_windows=False,
    highlight=True,
    soft_wrap=True,
)

# Modern color palette
COLOR_PRIMARY = "cyan"
COLOR_SUCCESS = "green"
COLOR_WARNING = "yellow"
COLOR_ERROR = "red"
COLOR_ACCENT = "bright_blue"
COLOR_MUTED = "dim white"
COLOR_BG = "default"


def print_banner():
    """Print the Flashare banner with modern styling."""
    # Create a stylized banner
    title_text = Text()
    title_text.append("⚡ ", style="yellow bold")
    title_text.append(__app_name__, style="cyan bold")
    title_text.append(f" v{__version__}", style=f"{COLOR_MUTED}")
    
    subtitle = Text(
        f"Modern file sharing at lightning speed",
        style="dim italic"
    )
    
    # Create a visually appealing panel
    console.print()
    console.print(
        Panel(
            Align.center(
                Text.assemble(
                    title_text,
                    "\n",
                    subtitle,
                ),
            ),
            box=box.ROUNDED,
            padding=(1, 3),
            border_style=f"{COLOR_PRIMARY} bold",
            expand=False,
        ),
    )
    console.print()


def print_qr_code(port: int = 8000):
    """
    Display QR code in modern styled panel.
    
    Args:
        port: Server port number.
    """
    url = get_server_url(port)
    qr_ascii = generate_qr_ascii(port=port)
    
    console.print()
    console.print(
        Panel(
            Align.center(qr_ascii),
            title="[bold bright_cyan]📱 Scan to Connect[/]",
            subtitle=f"[italic dim]{url}[/]",
            box=box.DOUBLE,
            border_style=f"{COLOR_SUCCESS} bold",
            padding=(2, 3),
        ),
    )
    console.print()


def print_server_info(host: str, port: int):
    """
    Display server connection information with modern styling.
    
    Args:
        host: Server host.
        port: Server port.
    """
    url = get_server_url(port)
    
    # Create styled info table
    table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 2),
        border_style=f"{COLOR_MUTED}",
    )
    table.add_column("Label", style=f"{COLOR_MUTED}")
    table.add_column("Value", style=f"bold {COLOR_PRIMARY}")
    
    table.add_row("🌐 Server URL", f"[link={url}]{url}[/link]")
    table.add_row("📡 Host", f"[{COLOR_ACCENT}]{host}[/]")
    table.add_row("🔌 Port", f"[{COLOR_ACCENT}]{port}[/]")
    
    # Wrap in a panel
    console.print()
    console.print(
        Panel(
            table,
            title="[bold]Server Configuration[/]",
            box=box.ROUNDED,
            padding=(1, 2),
            border_style=f"{COLOR_ACCENT}",
        ),
    )
    console.print()


def print_file_ready(filename: str, size: int):
    """
    Display file ready for transfer with modern design.
    
    Args:
        filename: Name of the file.
        size: File size in bytes.
    """
    size_str = _format_size(size)
    
    # Create status message
    status = Text()
    status.append("✓ ", style=f"bold {COLOR_SUCCESS}")
    status.append("Ready to share: ", style="")
    status.append(filename, style=f"bold {COLOR_PRIMARY}")
    status.append(f" ({size_str})", style=f"{COLOR_MUTED}")
    
    console.print()
    console.print(
        Panel(
            Align.center(status),
            box=box.ROUNDED,
            border_style=f"{COLOR_SUCCESS} bold",
            padding=(1, 2),
        ),
    )
    console.print()


def print_optimization_result(
    input_file: str,
    output_file: str,
    input_size: int,
    output_size: int,
):
    """
    Display video optimization results with visual metrics.
    
    Args:
        input_file: Original filename.
        output_file: Optimized filename.
        input_size: Original size in bytes.
        output_size: Optimized size in bytes.
    """
    reduction = ((input_size - output_size) / input_size) * 100
    
    # Create modern metrics table
    table = Table(
        title="[bold bright_magenta]📹 Video Optimization[/]",
        box=box.ROUNDED,
        border_style=f"{COLOR_PRIMARY}",
        padding=(0, 2),
    )
    table.add_column("Type", style="dim")
    table.add_column("File", style=f"{COLOR_PRIMARY}")
    table.add_column("Size", justify="right", style=f"{COLOR_ACCENT}")
    
    table.add_row("📄 Original", input_file, _format_size(input_size))
    table.add_row("⚡ Optimized", output_file, _format_size(output_size))
    
    # Add reduction row with color gradient effect
    reduction_text = f"Reduction: [bold {COLOR_SUCCESS}]-{reduction:.1f}%[/]"
    table.add_row("", "", reduction_text)
    
    console.print()
    console.print(table)
    console.print()


def print_error(message: str):
    """Display an error message with emphasis."""
    error_text = Text()
    error_text.append("✗ ", style=f"bold {COLOR_ERROR}")
    error_text.append(f"{message}", style="")
    
    console.print(
        Panel(
            error_text,
            box=box.ROUNDED,
            border_style=f"{COLOR_ERROR} bold",
            padding=(0, 1),
        ),
    )


def print_warning(message: str):
    """Display a warning message with visual prominence."""
    warning_text = Text()
    warning_text.append("⚠ ", style=f"bold {COLOR_WARNING}")
    warning_text.append(f"{message}", style="")
    
    console.print(
        Panel(
            warning_text,
            box=box.ROUNDED,
            border_style=f"{COLOR_WARNING}",
            padding=(0, 1),
        ),
    )


def print_success(message: str):
    """Display a success message."""
    success_text = Text()
    success_text.append("✓ ", style=f"bold {COLOR_SUCCESS}")
    success_text.append(f"{message}", style="")
    
    console.print(success_text)


def print_info(message: str):
    """Display an info message."""
    info_text = Text()
    info_text.append("ℹ ", style=f"bold {COLOR_ACCENT}")
    info_text.append(f"{message}", style="dim")
    
    console.print(info_text)


def print_separator(title: Optional[str] = None):
    """
    Print a styled horizontal separator.
    
    Args:
        title: Optional title for the separator.
    """
    if title:
        console.print(
            Rule(
                f"[bold {COLOR_PRIMARY}]{title}[/]",
                style=f"{COLOR_MUTED}",
            ),
        )
    else:
        console.print(Rule(style=f"{COLOR_MUTED}"))


def confirm(prompt: str, default: bool = True) -> bool:
    """
    Ask for user confirmation with modern styling.
    
    Args:
        prompt: The question to ask.
        default: Default answer if user just presses Enter.
        
    Returns:
        True if confirmed, False otherwise.
    """
    suffix = " [Y/n]" if default else " [y/N]"
    styled_prompt = f"[bold {COLOR_ACCENT}]?[/] {prompt}{suffix}"
    
    try:
        response = console.input(styled_prompt + " ").strip().lower()
        
        if not response:
            return default
        
        return response in ('y', 'yes')
    except (KeyboardInterrupt, EOFError):
        return False


def create_progress(description: str = "Processing...") -> Progress:
    """
    Create a modern Rich progress bar for file operations.
    
    Args:
        description: Description of the operation.
        
    Returns:
        Configured Progress instance.
    """
    return Progress(
        SpinnerColumn(style=f"{COLOR_PRIMARY} bold"),
        TextColumn("[progress.description]{task.description}", style=f"{COLOR_ACCENT}"),
        BarColumn(
            complete_style=f"bold {COLOR_SUCCESS}",
            finished_style=f"bold {COLOR_SUCCESS}",
            bar_width=30,
        ),
        TaskProgressColumn(style=f"{COLOR_ACCENT}"),
        console=console,
        transient=True,
    )


def print_transfer_summary(
    filename: str,
    size: int,
    download_count: int = 0,
    duration: float = 0,
):
    """
    Display a summary of completed file transfer.
    
    Args:
        filename: Name of the transferred file.
        size: File size in bytes.
        download_count: Number of downloads.
        duration: Transfer duration in seconds.
    """
    summary_table = Table(
        title="[bold bright_cyan]📊 Transfer Summary[/]",
        box=box.ROUNDED,
        border_style=f"{COLOR_PRIMARY}",
        padding=(1, 2),
    )
    summary_table.add_column("Metric", style="dim")
    summary_table.add_column("Value", style=f"bold {COLOR_ACCENT}")
    
    summary_table.add_row("📄 File", filename)
    summary_table.add_row("📦 Size", _format_size(size))
    summary_table.add_row("📥 Downloads", str(download_count))
    if duration > 0:
        summary_table.add_row("⏱️  Duration", f"{duration:.1f}s")
    
    console.print()
    console.print(summary_table)
    console.print()


def _format_size(size_bytes: int) -> str:
    """
    Format bytes as human-readable size with color coding.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Formatted size string.
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    
    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    
    return f"{size:.1f} PB"
