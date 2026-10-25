"""
Cyberpunk-styled terminal user interface and logging utilities.
"""

import sys
import threading
import datetime
import ctypes

# Enable Virtual Terminal Processing for Windows console and enforce UTF-8
def _init_windows_console():
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            hStdOut = kernel32.GetStdHandle(-11) # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode))
            kernel32.SetConsoleMode(hStdOut, mode.value | 0x0004) # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        except Exception:
            pass

_init_windows_console()

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"

CYAN = "\033[96m"
BRIGHT_CYAN = "\033[38;5;51m"
YELLOW = "\033[93m"
BRIGHT_YELLOW = "\033[38;5;226m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
RED = "\033[91m"
WHITE = "\033[97m"
GRAY = "\033[90m"

class TerminalUI:
    """Thread-safe UI renderer for terminal interactions."""

    def __init__(self):
        self._lock = threading.Lock()
        self._active_prompt = "you > "

    def get_timestamp(self) -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")

    def print_banner(self, provider: str, min_interval: int, max_interval: int, hotkey: str):
        with self._lock:
            banner = f"""
{CYAN}╔══════════════════════════════════════════════════════════════════════╗
║  {BRIGHT_YELLOW}CAPRI // PROJECT CAPRICORN [DESKTOP CONSTRUCT v0.1]{CYAN}                 ║
║  {WHITE}Cyberpunk Desktop AI Assistant — Backend Daemon{CYAN}                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  {GRAY}Status    :{RESET} {GREEN}ONLINE{CYAN}                                              ║
║  {GRAY}AI Brain  :{RESET} {WHITE}{provider:<20}{CYAN}                               ║
║  {GRAY}Screen Eye:{RESET} {YELLOW}ACTIVE{CYAN} (Every {min_interval}s - {max_interval}s random){CYAN}                 ║
║  {GRAY}Voice Mic :{RESET} {MAGENTA}HOTKEY [{hotkey}]{CYAN} (Press to speak / press again to send)       ║
║  {GRAY}Commands  :{RESET} {GRAY}/watch (force see), /status, /clear, /exit{CYAN}             ║
╚══════════════════════════════════════════════════════════════════════╝{RESET}
"""
            print(banner, flush=True)

    def print_capri(self, text: str, source: str = "TALKING"):
        """Print Capri's speech in authentic cyberpunk styling."""
        with self._lock:
            ts = self.get_timestamp()
            tag = f"{YELLOW}[{ts}] [CAPRI // {source}]{RESET}"
            dialog = f"{BOLD}{WHITE}CAPRI :{RESET} {BRIGHT_CYAN}{text}{RESET}\n"
            print(f"{tag}\n{dialog}", flush=True)

    def print_status(self, state: str, message: str = ""):
        """Print status indicator (e.g., WATCHING, LISTENING, THINKING)."""
        with self._lock:
            ts = self.get_timestamp()
            color = CYAN
            if "WATCH" in state:
                color = YELLOW
            elif "LISTEN" in state or "RECORD" in state:
                color = MAGENTA
            elif "THINK" in state:
                color = BRIGHT_YELLOW
            elif "ERROR" in state:
                color = RED
            elif "OK" in state or "ONLINE" in state:
                color = GREEN

            extra = f" {GRAY}— {message}{RESET}" if message else ""
            print(f"{color}[{ts}] [CAPRI // {state}]{extra}{RESET}", flush=True)

    def print_user(self, text: str, is_voice: bool = False):
        """Print user message."""
        with self._lock:
            ts = self.get_timestamp()
            label = "you (voice)" if is_voice else "you"
            print(f"{GRAY}[{ts}]{RESET} {GREEN}{label} >{RESET} {WHITE}{text}{RESET}", flush=True)

    def print_system(self, text: str):
        with self._lock:
            print(f"{GRAY}[SYS] {text}{RESET}", flush=True)

# Global singleton UI instance
ui = TerminalUI()
