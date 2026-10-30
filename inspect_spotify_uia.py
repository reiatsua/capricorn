import uiautomation as auto
import ctypes

user32 = ctypes.windll.user32
hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

hwnd = 328548
ctrl = auto.ControlFromHandle(hwnd)

def dump_controls(element, depth=0, max_depth=6):
    if depth > max_depth:
        return
    child = element.GetFirstChildControl()
    while child:
        name = child.Name
        ctype = child.ControlTypeName
        if name or ctype == 'ButtonControl':
            print("  " * depth + f"[{ctype}] '{name}' ({child.BoundingRectangle})")
        dump_controls(child, depth + 1, max_depth)
        child = child.GetNextSiblingControl()

print("Dumping UI elements...")
dump_controls(ctrl, 0, 5)
