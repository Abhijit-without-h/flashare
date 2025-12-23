"""fzf file selection wrapper for Flashare."""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional


def is_fzf_available() -> bool:
    """Check if fzf is available on the system."""
    return shutil.which("fzf") is not None


def select_file(
    start_dir: Optional[Path] = None,
    prompt: str = "Select file to share > ",
    preview: bool = True,
) -> Optional[Path]:
    """
    Open fzf to select a file.
    
    Args:
        start_dir: Starting directory for file search. Defaults to current directory.
        prompt: Prompt text to display.
        preview: Whether to show file preview.
        
    Returns:
        Path to the selected file, or None if cancelled.
    """
    if not is_fzf_available():
        return _fallback_select(start_dir)
    
    start_dir = start_dir or Path.cwd()
    
    # Build the find command
    # Exclude hidden files and common unwanted directories
    find_cmd = (
        f'find "{start_dir}" -type f '
        '-not -path "*/.*" '
        '-not -path "*/__pycache__/*" '
        '-not -path "*/node_modules/*" '
        '-not -path "*/.git/*" '
        '2>/dev/null'
    )
    
    # Build fzf command
    fzf_opts = [
        "--prompt", prompt,
        "--height", "80%",
        "--layout", "reverse",
        "--border", "rounded",
        "--info", "inline",
    ]
    
    if preview:
        # Use head for preview (or bat if available)
        preview_cmd = "head -50 {}" if not shutil.which("bat") else "bat --color=always --style=plain --line-range=:50 {}"
        fzf_opts.extend(["--preview", preview_cmd])
    
    fzf_cmd = ["fzf"] + fzf_opts
    
    try:
        # Pipe find output to fzf
        find_proc = subprocess.Popen(
            find_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        
        fzf_proc = subprocess.Popen(
            fzf_cmd,
            stdin=find_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        
        stdout, _ = fzf_proc.communicate()
        find_proc.wait()
        
        if fzf_proc.returncode == 0 and stdout.strip():
            return Path(stdout.strip())
        
    except Exception:
        pass
    
    return None


def select_multiple_files(
    start_dir: Optional[Path] = None,
    prompt: str = "Select files (TAB to multi-select) > ",
) -> list[Path]:
    """
    Open fzf to select multiple files.
    
    Args:
        start_dir: Starting directory for file search.
        prompt: Prompt text to display.
        
    Returns:
        List of selected file paths.
    """
    if not is_fzf_available():
        result = _fallback_select(start_dir)
        return [result] if result else []
    
    start_dir = start_dir or Path.cwd()
    
    find_cmd = (
        f'find "{start_dir}" -type f '
        '-not -path "*/.*" '
        '-not -path "*/__pycache__/*" '
        '2>/dev/null'
    )
    
    fzf_cmd = [
        "fzf",
        "--prompt", prompt,
        "--multi",  # Enable multi-select
        "--height", "80%",
        "--layout", "reverse",
        "--border", "rounded",
    ]
    
    try:
        find_proc = subprocess.Popen(
            find_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        
        fzf_proc = subprocess.Popen(
            fzf_cmd,
            stdin=find_proc.stdout,
            stdout=subprocess.PIPE,
            text=True,
        )
        
        stdout, _ = fzf_proc.communicate()
        find_proc.wait()
        
        if fzf_proc.returncode == 0 and stdout.strip():
            return [Path(line) for line in stdout.strip().split('\n') if line]
        
    except Exception:
        pass
    
    return []


def _fallback_select(start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Fallback file selection when fzf is not available.
    
    Args:
        start_dir: Starting directory.
        
    Returns:
        Selected file path or None.
    """
    print("\n⚠️  fzf not found. Install it with: brew install fzf")
    print("   Falling back to manual input.\n")
    
    try:
        path_str = input("Enter file path (or drag file here): ").strip()
        
        # Remove quotes if present (from drag & drop)
        path_str = path_str.strip("'\"")
        
        if path_str:
            path = Path(path_str)
            if path.exists() and path.is_file():
                return path
            print(f"❌ File not found: {path}")
    except (KeyboardInterrupt, EOFError):
        pass
    
    return None
