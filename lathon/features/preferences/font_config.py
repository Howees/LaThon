import customtkinter as ctk
from tkinter import font as tkfont
from lathon.ui.widgets.base_modal import BaseModal

class FontConfigDialog(BaseModal):
    def __init__(self, master_app):
        super().__init__(master_app, "Fonte do Editor", 350, 240)

        cfg = self.app.config.get_layout()
        current_family, current_size = cfg.get("font_family", "Consolas"), cfg.get("font_size", 12)

        ctk.CTkLabel(self.border_frame, text="Tipo de Fonte:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=30, pady=(20, 0))
        fonts = list(tkfont.families())
        fonts.sort()
        for pf in reversed(["Consolas", "Courier New", "Cascadia Code", "Fira Code", "Arial"]):
            if pf in fonts: fonts.insert(0, fonts.pop(fonts.index(pf)))

        self.combo_font = ctk.CTkComboBox(self.border_frame, values=fonts[:100])
        self.combo_font.set(current_family)
        self.combo_font.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(self.border_frame, text="Tamanho:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=30, pady=(10, 0))
        self.slider_size = ctk.CTkSlider(self.border_frame, from_=10, to=24, number_of_steps=14, command=lambda v: self.lbl_size.configure(text=f"{int(v)} px"))
        self.slider_size.set(current_size)
        self.slider_size.pack(fill="x", padx=30, pady=5)
        self.lbl_size = ctk.CTkLabel(self.border_frame, text=f"{current_size} px")
        self.lbl_size.pack()

        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.pack(pady=10)
        ctk.CTkButton(btn_f, text="Cancelar", width=80, fg_color="transparent", border_width=1, text_color=("black", "white"), command=self._close_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Aplicar", width=100, command=self._apply).pack(side="left", padx=5)

    def _apply(self):
        self.app.apply_font_config(self.combo_font.get(), int(self.slider_size.get()))
        self._close_dialog()