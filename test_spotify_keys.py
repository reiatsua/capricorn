import ctypes
import time

user32 = ctypes.windll.user32
hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

hwnd = 328548
print("Bringing Spotify to front...")
user32.ShowWindow(hwnd, 9) # SW_RESTORE
user32.SetForegroundWindow(hwnd)
time.sleep(0.3)

# Let's test what keys do in Spotify
print("Foreground window:", user32.GetForegroundWindow())
