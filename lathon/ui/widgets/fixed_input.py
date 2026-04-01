import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal
from lathon.ui.design import Colors


class FixedInputDialog(BaseModal):
    """
    Modal de entrada de texto simples.
    Ideal para ações rápidas como renomear arquivos, criar pastas ou buscar termos.
    """

    def __init__(self, title, text, master_app=None):
        super().__init__(master_app, title, 350, 180)

        # Mensagem de instrução
        ctk.CTkLabel(self.border_frame, text=text, text_color=Colors.TEXT_NORMAL).pack(pady=(20, 5))

        # Campo de entrada principal
        self.entry = ctk.CTkEntry(self.border_frame, width=250, fg_color=Colors.BG_MAIN, text_color=Colors.TEXT_NORMAL)
        self.entry.pack(pady=10)

        # Atalhos de teclado para produtividade
        self.entry.bind("<Return>", self._on_ok)
        self.entry.bind("<Escape>", self._on_cancel)
        self.entry.focus_set()

        # Botões de controle
        btn_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(
            btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
            text_color=Colors.TEXT_NORMAL, width=80, command=self._on_cancel
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="OK", width=80, command=self._on_ok
        ).pack(side="left", padx=5)

    def _on_ok(self, event=None):
        """Salva o texto digitado e encerra o diálogo."""
        self.result = self.entry.get()
        self._close_dialog()

    def _on_cancel(self, event=None):
        """Aborta a operação, retornando None."""
        self.result = None
        self._close_dialog()

    def get_input(self):
        """Método de interface pública para recuperar o dado inserido."""
        return self.get_data()