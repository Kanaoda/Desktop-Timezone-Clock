import win32gui
import win32api
import win32con
from collections import Counter

def debug_taskbar_colors():
    tray = win32gui.FindWindow("Shell_TrayWnd", None)
    if not tray:
        print("Tray not found")
        return
    
    rect = win32gui.GetWindowRect(tray)
    print(f"Taskbar Rect: {rect}")
    
    hdc = win32gui.GetDC(0)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    
    colors = []
    # Sample a grid in the taskbar
    steps_x = 20
    steps_y = 5
    for i in range(steps_x):
        for j in range(steps_y):
            x = rect[0] + (width * i // steps_x)
            y = rect[1] + (height * j // steps_y)
            color = win32gui.GetPixel(hdc, x, y)
            r = color & 0xff
            g = (color >> 8) & 0xff
            b = (color >> 16) & 0xff
            colors.append((r, g, b))
    
    win32gui.ReleaseDC(0, hdc)
    
    counts = Counter(colors)
    most_common = counts.most_common(10)
    print("\nMost common colors (R, G, B):")
    for (color, count) in most_common:
        hex_color = "#{:02x}{:02x}{:02x}".format(*color)
        print(f"{hex_color}: {count} occurrences")

if __name__ == "__main__":
    debug_taskbar_colors()
