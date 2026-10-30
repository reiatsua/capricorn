import ctypes
import numpy as np
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

hwnd = 328548
rect = (ctypes.c_long * 4)()
user32.GetWindowRect(hwnd, rect)
left, top, right, bottom = rect[0], rect[1], rect[2], rect[3]
w, h = right - left, bottom - top

hdc = user32.GetDC(0)
memdc = gdi32.CreateCompatibleDC(hdc)
hbitmap = gdi32.CreateCompatibleBitmap(hdc, w, h)
oldbmp = gdi32.SelectObject(memdc, hbitmap)
gdi32.BitBlt(memdc, 0, 0, w, h, hdc, left, top, 0x00CC0020)

bmpinfo = (ctypes.c_uint32 * 10)()
bmpinfo[0] = 40
bmpinfo[1] = w
bmpinfo[2] = -h
bmpinfo[3] = 1 | (32 << 16)

buffer = ctypes.create_string_buffer(w * h * 4)
gdi32.GetDIBits(memdc, hbitmap, 0, h, buffer, bmpinfo, 0)
gdi32.SelectObject(memdc, oldbmp)
gdi32.DeleteObject(hbitmap)
gdi32.DeleteDC(memdc)
user32.ReleaseDC(0, hdc)

img = Image.frombuffer("RGBA", (w, h), buffer, "raw", "BGRA", 0, 1).convert("RGB")
img.save("spotify_captured.png")
print("Saved spotify_captured.png, size:", img.size)

arr = np.array(img)
# Search for Spotify neon green circle in the upper half of the window (top results area)
# Spotify green is #1ed760 -> R: ~30, G: ~215, B: ~96
mask = (arr[:, :, 0] >= 15) & (arr[:, :, 0] <= 55) & \
       (arr[:, :, 1] >= 180) & (arr[:, :, 1] <= 240) & \
       (arr[:, :, 2] >= 70) & (arr[:, :, 2] <= 130)

# Limit search to top result card area:
# y between 100 and 450, x between 200 and 800
submask = mask[100:450, 150:800]
ys, xs = np.where(submask)
if len(ys) > 0:
    btn_x = left + 150 + int(np.mean(xs))
    btn_y = top + 100 + int(np.mean(ys))
    print(f"Found Green Play Button! Screen coords: ({btn_x}, {btn_y}), Pixel count: {len(ys)}")
else:
    print("No green button found in target area.")
