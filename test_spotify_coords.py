import ctypes
import time

user32 = ctypes.windll.user32
hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

# Find Spotify window
hwnd = 328548
user32.ShowWindow(hwnd, 9)
user32.SetForegroundWindow(hwnd)
time.sleep(0.3)

rect = (ctypes.c_long * 4)()
user32.GetWindowRect(hwnd, rect)
left, top, right, bottom = rect[0], rect[1], rect[2], rect[3]
width = right - left
height = bottom - top
print(f"Spotify window: pos=({left}, {top}), size={width}x{height}")
