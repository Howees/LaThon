import customtkinter as ctk
from lathon.ui.main_window import MiniOverleaf

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = MiniOverleaf()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()