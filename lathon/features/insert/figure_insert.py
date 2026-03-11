import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal

class FigureInputDialog(BaseModal):
    def __init__(self, master_app):
        super().__init__(master_app, "Inserir Figura", 350, 330)
        ctk.CTkLabel(self.border_frame, text="Inserir Figura", font=("Segoe UI", 14, "bold")).pack(pady=15)

        self.filepath = self._create_input_row("Arquivo:", "SUA_FIGURA_AQUI")
        self.width_val = self._create_input_row("Tamanho (%):", "80", justify="center")
        self.caption = self._create_input_row("Legenda:")
        self.label = self._create_input_row("Label:", prefix="fig:")

        self._create_action_buttons("Inserir", self._on_ok)

    def _on_ok(self):
        self.result = (self.filepath.get().strip(), self.width_val.get().strip(), self.caption.get().strip(), f"fig:{self.label.get().strip()}")
        self._close_dialog()