from utils import sample_taskbar_color
import win32gui

def test_sampling():
    color = sample_taskbar_color()
    print(f"Sampled Color: {color}")
    
    tray = win32gui.FindWindow("Shell_TrayWnd", None)
    if tray:
        rect = win32gui.GetWindowRect(tray)
        print(f"Tray Rect: {rect}")
    else:
        print("Tray not found!")

if __name__ == "__main__":
    test_sampling()
