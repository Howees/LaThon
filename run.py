import sys
import ctypes
import customtkinter as ctk
from lathon.ui.screens.main_window import main_window

# Sem isso, a barra de tarefas pode ignorar seu ícone e mostrar o do Python
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('lathon.v1.0.2')
    except:
        pass

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = main_window()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()