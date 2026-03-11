import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal

class TableInputDialog(BaseModal):
    def __init__(self, master_app):
        super().__init__(master_app, "Inserir Tabela", 350, 330)
        ctk.CTkLabel(self.border_frame, text="Inserir Tabela", font=("Segoe UI", 14, "bold")).pack(pady=15)

        self.rows = self._create_input_row("Linhas:", "3", justify="center")
        self.cols = self._create_input_row("Colunas:", "3", justify="center")
        self.caption = self._create_input_row("Legenda:")
        self.label = self._create_input_row("Label:", prefix="tab:")

        self._create_action_buttons("Inserir", self._on_ok)

    def _on_ok(self):
        try:
            r, c = int(self.rows.get()), int(self.cols.get())
            self.result = (r, c, self.caption.get(), f"tab:{self.label.get().strip()}")
            self._close_dialog()
        except: pass