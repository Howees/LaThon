import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts

class MarkersListDialog(BaseModal):
    """Janela que lista todas as marcações e anotações feitas no documento atual."""

    def __init__(self, app):
        super().__init__(app, "Lista de Marcações", 500, 400)

        ctk.CTkLabel(self.border_frame, text="Anotações no Documento", font=Fonts.UI_TITLE).pack(anchor="w", padx=20, pady=(20, 5))

        self.scroll = ctk.CTkScrollableFrame(self.border_frame, fg_color=Colors.BG_MAIN)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=5)

        self._populate_markers()
        self._create_action_buttons("Fechar", self._close_dialog)

    def _populate_markers(self):
        editor = self.app.editor
        comments = editor.mark_comments

        if not comments:
            ctk.CTkLabel(self.scroll, text="Nenhuma marcação no documento atual.", text_color=Colors.TEXT_MUTED, font=Fonts.UI).pack(pady=20)
            return

        for tag, comment in comments.items():
            try:
                idx = editor.index(f"{tag}.first")
                line = idx.split(".")[0]
                word = editor.get(f"{tag}.first", f"{tag}.last")
            except:
                continue

            f = ctk.CTkFrame(self.scroll, fg_color="transparent")
            f.pack(fill="x", pady=2, padx=5)

            color = editor.tag_cget(tag, "background")
            ctk.CTkFrame(f, width=12, height=12, fg_color=color, corner_radius=6).pack(side="left", padx=(0, 10))

            text_disp = f"Linha {line} | '{word}' -> {comment if comment else '(Sem comentário)'}"
            ctk.CTkLabel(f, text=text_disp, anchor="w", justify="left", font=Fonts.UI).pack(side="left", fill="x", expand=True)

            ctk.CTkButton(f, text="Ir", width=40, height=24, font=Fonts.UI, fg_color=Colors.BTN_PRIMARY, hover_color=Colors.BTN_PRIMARY_HOVER,
                          command=lambda t=idx: self._goto_line(t)).pack(side="right")

    def _goto_line(self, index):
        self.app.editor.see(index)
        self.app.editor.mark_set("insert", index)
        self._close_dialog()