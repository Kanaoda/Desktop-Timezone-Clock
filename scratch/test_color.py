import tkinter as tk
import win32gui
import win32api
import win32con
import time
import ctypes

def test_color_deviation(use_dpi_aware=False):
    if use_dpi_aware:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            print("DPI Awareness: ON")
        except:
            print("DPI Awareness: FAILED TO SET")
    else:
        print("DPI Awareness: OFF")

    root = tk.Tk()
    target_color = "#FF5500" # R=255, G=85, B=0
    root.config(bg=target_color)
    root.overrideredirect(True)
    root.geometry("200x200+100+100")
    root.attributes("-topmost", True)
    
    root.update()
    time.sleep(0.5) # Wait for rendering
    
    # Sample color
    hdc = win32gui.GetDC(0)
    # Target center of window (100, 100) -> (200, 200) in screen coords
    p = win32gui.GetPixel(hdc, 200, 200)
    win32gui.ReleaseDC(0, hdc)
    
    # win32 GetPixel is BGR
    r = p & 0xff
    g = (p >> 8) & 0xff
    b = (p >> 16) & 0xff
    sampled_hex = f"#{r:02x}{g:02x}{b:02x}".upper()
    
    print(f"Target: {target_color.upper()}")
    print(f"Sampled: {sampled_hex}")
    
    if target_color.upper() == sampled_hex:
        print("RESULT: MATCH")
    else:
        print(f"RESULT: DEVIATION DETECTED! (Diff: R:{r-255}, G:{g-85}, B:{b-0})")
    
    root.destroy()

if __name__ == "__main__":
    test_color_deviation(use_dpi_aware=False)
    print("-" * 20)
    # Note: DPI awareness can only be set once per process. 
    # To test both, I should probably run them separately.
