from rich.traceback import install
from rich.console import Console

# Initialize Rich console and install traceback handler before any other imports
console = Console()
install(show_locals=False, width=console.width)
