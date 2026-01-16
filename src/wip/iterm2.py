"""iTerm2 inline image support for terminal rendering."""

import base64
import os
import sys
from pathlib import Path

# Get the assets directory path
ASSETS_DIR = Path(__file__).parent / "assets"

# Bufo image mappings for different task states
BUFO_IMAGES = {
    "active": "bufo_active.png",
    "backlog": "bufo_backlog.png",
    "done": "bufo_done.png",
    "hold": "bufo_hold.png",
    "stale": "bufo_stale.png",
}

# Fallback emojis for non-iTerm2 terminals
FALLBACK_EMOJI = {
    "active": "🔥",
    "backlog": "💤",
    "done": "✅",
    "hold": "🔒",
    "stale": "⚠️",
}


def is_iterm2() -> bool:
    """Check if we're running in iTerm2."""
    term_program = os.environ.get("TERM_PROGRAM", "")
    return term_program == "iTerm.app"


def inline_image_escape(image_path: Path, width: int = 2, height: int = 1) -> str:
    """Generate iTerm2 inline image escape sequence.

    Args:
        image_path: Path to the image file
        width: Width in terminal cells
        height: Height in terminal cells

    Returns:
        Escape sequence string that displays the image inline
    """
    if not image_path.exists():
        return ""

    # Read and base64 encode the image
    image_data = image_path.read_bytes()
    encoded = base64.b64encode(image_data).decode("ascii")

    # Build iTerm2 inline image escape sequence
    # Format: ESC ] 1337 ; File = [args] : base64data BEL
    # Use \x1b for ESC and \x07 for BEL (more explicit than \033 and \a)
    args = f"inline=1;width={width};height={height};preserveAspectRatio=1"

    return f"\x1b]1337;File={args}:{encoded}\x07"


def get_bufo_str(state: str, width: int = 2, height: int = 1) -> str:
    """Get a bufo image string for the given task state.

    In iTerm2, returns the escape sequence for inline image.
    Otherwise, returns the fallback emoji.

    Args:
        state: One of "active", "backlog", "done", "hold", "stale"
        width: Width in terminal cells
        height: Height in terminal cells

    Returns:
        Inline image escape sequence or emoji string
    """
    if not is_iterm2():
        return FALLBACK_EMOJI.get(state, "")

    image_name = BUFO_IMAGES.get(state)
    if not image_name:
        return FALLBACK_EMOJI.get(state, "")

    image_path = ASSETS_DIR / image_name
    if image_path.exists():
        return inline_image_escape(image_path, width, height)
    return FALLBACK_EMOJI.get(state, "")


def bufo(state: str) -> str:
    """Get a bufo representation for the given task state.

    This is the main function to use - it handles iTerm2 detection
    and falls back to emoji when needed.

    Args:
        state: One of "active", "backlog", "done", "hold", "stale"

    Returns:
        Inline image escape sequence (iTerm2) or emoji string
    """
    return get_bufo_str(state)
