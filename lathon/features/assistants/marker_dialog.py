import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors

class MarkerDialog(BaseModal):
    """Nova janela focada em inserir comentários com seletor visual de cor."""

    def __init__(self, master_app):
        super().__init__(master_app, "Marcação de Texto", 350, 220)

        ctk.CTkLabel(self.border_frame, text="Adicione um comentário (ou deixe em branco):", text_color=Colors.TEXT_NORMAL).pack(pady=(15, 5))
        self.entry = ctk.CTkEntry(self.border_frame, width=280, fg_color=Colors.BG_MAIN, text_color=Colors.TEXT_NORMAL)
        self.entry.pack(pady=5)
        self.entry.focus_set()

        self.entry.bind("<Return>", self._on_ok)
        self.entry.bind("<Escape>", self._on_cancel)

        # Seletor de Cores
        color_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        color_frame.pack(pady=(10, 0))

        self.selected_color = ctk.StringVar(value="#ffeb3b")  # Padrão: Amarelo

        colors = [
            ("#ffeb3b", "Amarelo"),
            ("#81c784", "Verde"),
            ("#64b5f6", "Azul"),
            ("#e57373", "Vermelho")
        ]

        for hex_code, name in colors:
            rb = ctk.CTkRadioButton(
                color_frame, text="", variable=self.selected_color, value=hex_code,
                fg_color=hex_code, hover_color=hex_code, border_color=hex_code,
                width=20, border_width_checked=6
            )
            rb.pack(side="left", padx=10)

        self._create_action_buttons("Marcar", self._on_ok)

    def _on_ok(self, event=None):
        self.result = (self.selected_color.get(), self.entry.get())
        self._close_dialog()

    def _on_cancel(self, event=None):
        self.result = None
        self._close_dialog()