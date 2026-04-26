import tkinter as tk
import customtkinter as ctk
import win32gui
import time

def compare_tk_vs_ctk():
    target = "#333333"
    
    # Standard TK
    root_tk = tk.Tk()
    root_tk.config(bg=target)
    root_tk.geometry("100x100+100+100")
    root_tk.overrideredirect(True)
    root_tk.attributes("-topmost", True)
    root_tk.update()
    
    # Custom TK
    ctk.set_appearance_mode("dark")
    root_ctk = ctk.CTk()
    root_ctk.geometry("100x100+210+100")
    root_ctk.overrideredirect(True)
    root_ctk.attributes("-topmost", True)
    frame = ctk.CTkFrame(root_ctk, fg_color=target, width=100, height=100, corner_radius=0)
    frame.pack()
    root_ctk.update()
    
    time.sleep(1)
    
    hdc = win32gui.GetDC(0)
    
    # Sample TK
    p1 = win32gui.GetPixel(hdc, 150, 150)
    # Sample CTK
    p2 = win32gui.GetPixel(hdc, 260, 150)
    
    win32gui.ReleaseDC(0, hdc)
    
    def to_hex(p):
        return f"#{p&0xff:02x}{(p>>8)&0xff:02x}{(p>>16)&0xff:02x}".upper()
    
    print(f"Target: {target.upper()}")
    print(f"TK Rendered:  {to_hex(p1)}")
    print(f"CTK Rendered: {to_hex(p2)}")
    
    root_tk.destroy()
    root_ctk.destroy()

if __name__ == "__main__":
    compare_tk_vs_ctk()
