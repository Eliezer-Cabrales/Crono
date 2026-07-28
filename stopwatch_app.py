import ctypes
import platform

# 1. ESTO DEBE IR ANTES DE IMPORTAR TKINTER
# Obliga a Windows a leer los píxeles físicos exactos de todas tus pantallas (0 chapuzas de escalado)
if platform.system() == "Windows":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import tkinter as tk
from stopwatch_app import StopwatchApp

if __name__ == "__main__":
    root = tk.Tk()
    app = StopwatchApp(root)
    root.mainloop()