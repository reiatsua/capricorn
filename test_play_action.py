import ctypes
import time

user32 = ctypes.windll.user32
hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

hwnd = 328548
print("Restoring and focusing Spotify...")
user32.ShowWindow(hwnd, 9) # SW_RESTORE
user32.SetForegroundWindow(hwnd)
time.sleep(0.5)

# Win32 key events
VK_RETURN = 0x0D
VK_DOWN = 0x28
VK_TAB = 0x09
KEYEVENTF_KEYUP = 0x0002

def press_vk(vk):
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)

# What is the title of Spotify now?
length = user32.GetWindowTextLengthW(hwnd)
buff = ctypes.create_unicode_buffer(length + 1)
user32.GetWindowTextW(hwnd, buff, length + 1)
print("Title before:", buff.value)

# Let's test Enter or Down + Enter
print("Sending Down Arrow + Enter...")
press_vk(VK_DOWN)
time.sleep(0.2)
press_vk(VK_RETURN)

time.sleep(1.0)

# Check title after
length = user32.GetWindowTextLengthW(hwnd)
buff = ctypes.create_unicode_buffer(length + 1)
user32.GetWindowTextW(hwnd, buff, length + 1)
print("Title after:", buff.value)
