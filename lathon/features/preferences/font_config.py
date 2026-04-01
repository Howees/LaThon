import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
from lathon.ui.widgets.base_modal import BaseModal

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts


class FontConfigDialog(BaseModal):
    """
    Componente Modal: Configuração de Fonte e Tamanho do Editor.
    Lista as fontes instaladas no sistema e controla o tamanho do texto (zoom global).
    """

    def __init__(self, master_app):
        super().__init__(master_app, "Fonte do Editor", 380, 450)

        cfg = self.app.config.get_layout()
        self.current_family, current_size = cfg.get("font_family", "Consolas"), cfg.get("font_size", 12)

        # ==========================================
        # 1. ÂNCORAS INFERIORES (Botões e Slider)
        # Fixar esses elementos na base evita que sejam deslocados
        # em sistemas operacionais onde a lista de fontes é muito extensa.
        # ==========================================
        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.pack(side="bottom", pady=(10, 20))

        ctk.CTkButton(btn_f, text="Cancelar", width=80, fg_color="transparent", border_width=1,
                      text_color=Colors.TEXT_NORMAL, command=self._close_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Aplicar", width=100, command=self._apply).pack(side="left", padx=5)

        self.lbl_size = ctk.CTkLabel(self.border_frame, text=f"{current_size} px")
        self.lbl_size.pack(side="bottom", pady=(0, 10))

        self.slider_size = ctk.CTkSlider(self.border_frame, from_=10, to=24, number_of_steps=14,
                                         command=lambda v: self.lbl_size.configure(text=f"{int(v)} px"))
        self.slider_size.set(current_size)
        self.slider_size.pack(side="bottom", fill="x", padx=30, pady=5)

        ctk.CTkLabel(self.border_frame, text="Tamanho:", font=Fonts.UI_BOLD).pack(side="bottom", anchor="w",
                                                                                  padx=30, pady=(10, 0))

        # ==========================================
        # 2. CONTAINER FLEXÍVEL (Lista de Fontes)
        # Ocupa dinamicamente a área vertical remanescente.
        # ==========================================
        ctk.CTkLabel(self.border_frame, text="Selecione a Fonte:", font=Fonts.UI_BOLD).pack(side="top", anchor="w",
                                                                                            padx=30, pady=(20, 5))

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = Colors.BG_PANEL[1] if is_dark else "#f0f0f0"
        fg_color = Colors.TEXT_NORMAL[1] if is_dark else Colors.TEXT_NORMAL[0]

        list_frame = ctk.CTkFrame(self.border_frame, fg_color=bg_color, corner_radius=6, border_width=1,
                                  border_color=Colors.BORDER)
        list_frame.pack(side="top", fill="both", expand=True, padx=30, pady=(0, 10))

        scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical")
        scrollbar.pack(side="right", fill="y", padx=2, pady=2)

        self.font_listbox = tk.Listbox(list_frame, bd=0, highlightthickness=0, bg=bg_color, fg=fg_color, font=Fonts.UI)
        self.font_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.font_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.font_listbox.yview)

        # Captura as fontes instaladas no OS e prioriza fontes monospaced
        fonts = list(tkfont.families())
        fonts.sort()
        for pf in reversed(["Consolas", "Courier New", "Cascadia Code", "Fira Code", "Arial"]):
            if pf in fonts:
                fonts.insert(0, fonts.pop(fonts.index(pf)))

        for i, f in enumerate(fonts):
            self.font_listbox.insert("end", f)
            if f == self.current_family:
                self.font_listbox.selection_set(i)
                self.font_listbox.see(i)

    def _apply(self):
        """Delega a aplicação da fonte para o PreferencesManager."""
        sel = self.font_listbox.curselection()
        selected_font = self.font_listbox.get(sel[0]) if sel else self.current_family
        self.app.preferences_manager.apply_font_config(selected_font, int(self.slider_size.get()))
        self._close_dialog()