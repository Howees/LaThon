import customtkinter as ctk


class BaseModal(ctk.CTkToplevel):
    def __init__(self, master_app, title, width, height):
        super().__init__(master_app)
        self.app = master_app
        self.title(title)
        self.withdraw()
        if master_app: self.transient(master_app)
        self.configure(fg_color=("white", "#2b2b2b"))

        self.border_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.border_frame.pack(fill="both", expand=True)

        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+{int((ws / 2) - (width / 2))}+{int((hs / 2) - (height / 2))}")

        self.deiconify()
        self.grab_set()
        self.result = None

    def _close_dialog(self):
        self.grab_release()
        self.destroy()
        if self.app: self.app.focus_force()

    def get_data(self):
        self.master.wait_window(self)
        return self.result

    # ==========================================
    # FERRAMENTAS UNIVERSAIS PARA AS TELAS FILHAS
    # ==========================================
    def _create_input_row(self, text, default_val="", prefix=None, justify="left", label_width=80):
        """Cria e retorna uma linha padronizada com um texto (Label) e uma caixa de digitação (Entry)"""
        f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        f.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(f, text=text, width=label_width, anchor="e").pack(side="left")

        if prefix:
            ctk.CTkLabel(f, text=prefix, text_color="gray50").pack(side="left", padx=(10, 2))

        entry = ctk.CTkEntry(f, justify=justify)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10) if prefix else 10)

        if default_val:
            entry.insert(0, default_val)

        return entry

    def _create_action_buttons(self, confirm_text="OK", confirm_command=None):
        """Cria os botões padrão de Cancelar e Confirmar no rodapé da janela"""
        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.pack(pady=20)
        ctk.CTkButton(btn_f, text="Cancelar", width=80, fg_color="transparent", border_width=1,
                      text_color=("black", "white"), command=self._close_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text=confirm_text, width=80, command=confirm_command).pack(side="left", padx=5)