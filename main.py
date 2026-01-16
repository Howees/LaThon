import customtkinter as ctk
from app import MiniOverleaf

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")  # Ou "System"
    ctk.set_default_color_theme("blue")

    app = MiniOverleaf()

    # Vincula o evento de fechar janela à função segura
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    app.mainloop()