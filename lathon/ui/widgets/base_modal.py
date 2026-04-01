import customtkinter as ctk
from lathon.ui.design import Colors, resource_path


class BaseModal(ctk.CTkToplevel):
    """
    Classe base para todas as janelas secundárias do tipo Modal (pop-ups que exigem ação).
    Centraliza a lógica de geometria, design base, e bloqueio da janela principal.
    """

    def __init__(self, master_app, title, width, height):
        super().__init__(master_app)
        self.app = master_app
        self.title(title)
        self.result = None

        # Aplica o ícone com leve delay para contornar limitações do Toplevel
        self.after(200, lambda: self.iconbitmap(resource_path("icones/lathon.ico")))
        self.withdraw()  # Oculta a janela enquanto calcula as dimensões

        if master_app:
            self.transient(master_app)  # Mantém a modal sempre sobreposta ao app principal

        self.configure(fg_color=Colors.BG_PANEL)

        self.border_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.border_frame.pack(fill="both", expand=True)

        # Lógica para centralizar a janela perfeitamente na tela do usuário
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        pos_x = int((ws / 2) - (width / 2))
        pos_y = int((hs / 2) - (height / 2))
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        self.deiconify()
        self.grab_set()  # Intercepta todos os eventos de mouse/teclado para esta janela

    def _close_dialog(self):
        """Libera o foco devolvendo-o à janela principal e destrói o modal."""
        self.grab_release()
        self.destroy()
        if self.app:
            self.app.focus_force()

    def get_data(self):
        """
        Pausa a execução do código na janela pai até que este modal seja fechado.
        Retorna o resultado coletado.
        """
        self.master.wait_window(self)
        return self.result

    # ==========================================
    # UTILITÁRIOS PARA CONSTRUÇÃO DE FORMULÁRIOS
    # ==========================================

    def _create_input_row(self, text, default_val="", prefix=None, justify="left", label_width=80):
        """Gera uma linha horizontal contendo uma etiqueta (Label) e um campo de texto (Entry)."""
        f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        f.pack(pady=5, fill="x", padx=20)

        ctk.CTkLabel(f, text=text, width=label_width, anchor="e").pack(side="left")

        if prefix:
            ctk.CTkLabel(f, text=prefix, text_color=Colors.TEXT_MUTED).pack(side="left", padx=(10, 2))

        entry = ctk.CTkEntry(f, justify=justify)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10) if prefix else 10)

        if default_val:
            entry.insert(0, default_val)

        return entry

    def _create_action_buttons(self, confirm_text="OK", confirm_command=None):
        """Gera o rodapé padrão com opções de Cancelar e Confirmar."""
        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.pack(pady=20)

        ctk.CTkButton(
            btn_f, text="Cancelar", width=80, fg_color="transparent",
            border_width=1, text_color=Colors.TEXT_NORMAL, command=self._close_dialog
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_f, text=confirm_text, width=80, command=confirm_command
        ).pack(side="left", padx=5)