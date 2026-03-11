import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal

class ImageTableInputDialog(BaseModal):
    def __init__(self, master_app):
        super().__init__(master_app, "Tabela de Figuras", 350, 330)
        ctk.CTkLabel(self.border_frame, text="Tabela de Figuras", font=("Segoe UI", 14, "bold")).pack(pady=15)

        self.rows = self._create_input_row("Linhas:", "2", justify="center", label_width=110)
        self.img_size = self._create_input_row("Tam. Imagem (%):", "40", justify="center", label_width=110)
        self.caption = self._create_input_row("Legenda:", label_width=110)
        self.label = self._create_input_row("Label:", prefix="tab:fig_", label_width=110)

        self._create_action_buttons("Inserir", self._on_ok)

    def _on_ok(self):
        try:
            r, size = int(self.rows.get()), int(self.img_size.get())
            self.result = (r, size, self.caption.get(), f"tab:fig_{self.label.get().strip()}")
            self._close_dialog()
        except: pass