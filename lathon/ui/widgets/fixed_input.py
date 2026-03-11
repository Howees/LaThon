import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal

class FixedInputDialog(BaseModal):
    def __init__(self, title, text, master_app=None):
        super().__init__(master_app, title, 350, 180)

        ctk.CTkLabel(self.border_frame, text=text, text_color=("gray20", "gray80")).pack(pady=(20, 5))
        self.entry = ctk.CTkEntry(self.border_frame, width=250, fg_color=("gray95", "#343638"), text_color=("black", "white"))
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self._on_ok)
        self.entry.bind("<Escape>", self._on_cancel)
        self.entry.focus_set()

        btn_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1, text_color=("black", "white"), width=80, command=self._on_cancel).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="OK", width=80, command=self._on_ok).pack(side="left", padx=5)

    def _on_ok(self, event=None):
        self.result = self.entry.get()
        self._close_dialog()

    def _on_cancel(self, event=None):
        self.result = None
        self._close_dialog()

    def get_input(self):
        return self.get_data()