import os
import subprocess
import sys

def build():
    # 確保安裝了 pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 打包指令
    # --noconsole: 不顯示控制台視窗
    # --onefile: 打包成單一 exe
    # --name: 指定檔名
    # --add-data: 包含必要的檔案 (Windows 下格式為 "src;dest")
    
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name=DesktopTimezoneClock",
        "--clean",
        "main.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\nBuild completed! The executable is in the 'dist' folder.")

if __name__ == "__main__":
    build()
