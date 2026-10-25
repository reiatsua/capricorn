"""
Screen capture and periodic watcher background service.
"""

import io
import time
import random
import ctypes
import threading
from typing import Optional, Callable
from PIL import Image

import config
from terminal_ui import ui

def capture_desktop() -> Optional[Image.Image]:
    """Capture the current interactive Windows desktop using Win32 GDI."""
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        # Attach current thread to the interactive desktop if needed
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)

        user32.SetProcessDPIAware()
        w = user32.GetSystemMetrics(0) # SM_CXSCREEN
        h = user32.GetSystemMetrics(1) # SM_CYSCREEN

        hdc = user32.GetDC(0)
        memdc = gdi32.CreateCompatibleDC(hdc)
        hbitmap = gdi32.CreateCompatibleBitmap(hdc, w, h)
        oldbmp = gdi32.SelectObject(memdc, hbitmap)

        # BitBlt screen to memory DC (SRCCOPY = 0x00CC0020)
        gdi32.BitBlt(memdc, 0, 0, w, h, hdc, 0, 0, 0x00CC0020)

        # Extract bitmap bytes
        bmpinfo = (ctypes.c_uint32 * 10)()
        bmpinfo[0] = 40  # sizeof(BITMAPINFOHEADER)
        bmpinfo[1] = w
        bmpinfo[2] = -h # top-down DIB
        bmpinfo[3] = 1 | (32 << 16) # 1 plane, 32 bpp

        buffer = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(memdc, hbitmap, 0, h, buffer, bmpinfo, 0)

        # Clean up Win32 objects
        gdi32.SelectObject(memdc, oldbmp)
        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(memdc)
        user32.ReleaseDC(0, hdc)
        if hdesk:
            user32.CloseDesktop(hdesk)

        # Convert buffer to PIL Image
        img = Image.frombuffer("RGBA", (w, h), buffer, "raw", "BGRA", 0, 1)
        rgb_img = img.convert("RGB")

        # Downscale for performance & low latency if wider than MAX_SCREEN_WIDTH
        if rgb_img.width > config.MAX_SCREEN_WIDTH:
            ratio = config.MAX_SCREEN_WIDTH / float(rgb_img.width)
            new_h = int(float(rgb_img.height) * ratio)
            rgb_img = rgb_img.resize((config.MAX_SCREEN_WIDTH, new_h), Image.Resampling.LANCZOS)

        return rgb_img
    except Exception as e:
        ui.print_status("ERROR", f"Screen grab failed: {e}")
        return None

def image_to_jpeg_bytes(img: Image.Image) -> bytes:
    """Encode PIL Image to JPEG bytes."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=config.SCREENSHOT_JPEG_QUALITY)
    return buf.getvalue()

class ScreenWatcher(threading.Thread):
    """Background thread that periodically captures the screen and asks Capri to comment."""

    def __init__(self, on_screen_analyzed: Callable[[Image.Image], None]):
        super().__init__(name="ScreenWatcherThread", daemon=True)
        self.on_screen_analyzed = on_screen_analyzed
        self._stop_event = threading.Event()
        self._manual_trigger = threading.Event()
        self.next_interval = random.randint(config.MIN_WATCH_INTERVAL, config.MAX_WATCH_INTERVAL)
        self._last_thumb = None

    def _is_screen_changed(self, img: Image.Image, threshold: float = 0.025) -> bool:
        """Determines if the screen has changed significantly to avoid burning quota."""
        try:
            import numpy as np
            thumb = np.array(img.resize((64, 36)).convert("L"), dtype=np.float32)
            if self._last_thumb is None:
                self._last_thumb = thumb
                return True
            diff = float(np.mean(np.abs(thumb - self._last_thumb)) / 255.0)
            self._last_thumb = thumb
            return diff >= threshold
        except Exception:
            return True

    def trigger_now(self):
        """Immediately trigger a screen capture and analysis."""
        self._manual_trigger.set()

    def stop(self):
        self._stop_event.set()

    def run(self):
        ui.print_system(f"Screen Eye started. Next check in ~{self.next_interval}s.")
        time_elapsed = 0

        while not self._stop_event.is_set():
            # Check every 0.5s for stop or manual trigger
            if self._manual_trigger.is_set():
                self._manual_trigger.clear()
                self._do_screen_check(is_manual=True)
                time_elapsed = 0
                self.next_interval = random.randint(config.MIN_WATCH_INTERVAL, config.MAX_WATCH_INTERVAL)
                continue

            time.sleep(0.5)
            time_elapsed += 0.5

            if time_elapsed >= self.next_interval:
                time_elapsed = 0
                self.next_interval = random.randint(config.MIN_WATCH_INTERVAL, config.MAX_WATCH_INTERVAL)
                self._do_screen_check(is_manual=False)

    def _do_screen_check(self, is_manual: bool = False):
        ui.print_status("WATCHING", "Capturing screen...")
        screenshot = capture_desktop()
        if screenshot is not None:
            if not is_manual and not self._is_screen_changed(screenshot):
                ui.print_system("Экран без изменений — пропускаю анализ для экономии квоты.")
            else:
                self.on_screen_analyzed(screenshot)
        else:
            ui.print_status("ERROR", "Could not capture desktop screen.")
        ui.print_system(f"Next screen check scheduled in {self.next_interval}s.")
