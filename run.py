import customtkinter as ctk
from lathon.ui.screens.main_window import main_window

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = main_window()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
