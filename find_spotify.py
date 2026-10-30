import ctypes
import os

user32 = ctypes.windll.user32
hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

windows = []
def enum_cb(hwnd, lparam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls_name = cls_buff.value
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        windows.append((hwnd, pid.value, cls_name, title))
    return True

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
user32.EnumWindows(EnumWindowsProc(enum_cb), 0)

for h, p, c, t in windows:
    if "spotify" in t.lower() or "spotify" in c.lower() or "americano" in t.lower() or "chrome_widgetwin" in c.lower():
        print(f"HWND: {h}, PID: {p}, Class: '{c}', Title: '{t}'")
