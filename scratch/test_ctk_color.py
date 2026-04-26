import customtkinter as ctk
import win32gui
import time
import ctypes

def test_ctk_color():
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    target_color = "#FF5500"
    
    # Test a frame with the target color
    frame = ctk.CTkFrame(root, fg_color=target_color, width=200, height=200)
    frame.pack(padx=20, pady=20)
    
    root.overrideredirect(True)
    root.geometry("300x300+100+100")
    root.attributes("-topmost", True)
    
    root.update()
    time.sleep(0.5)
    
    hdc = win32gui.GetDC(0)
    # Sample center of frame
    # Frame is at (120, 120) roughly
    p = win32gui.GetPixel(hdc, 250, 250)
    win32gui.ReleaseDC(0, hdc)
    
    r = p & 0xff
    g = (p >> 8) & 0xff
    b = (p >> 16) & 0xff
    sampled_hex = f"#{r:02x}{g:02x}{b:02x}".upper()
    
    print(f"CTK Target: {target_color.upper()}")
    print(f"CTK Sampled: {sampled_hex}")
    
    if target_color.upper() == sampled_hex:
        print("CTK RESULT: MATCH")
    else:
        print(f"CTK RESULT: DEVIATION DETECTED!")
        
    root.destroy()

if __name__ == "__main__":
    test_ctk_color()
