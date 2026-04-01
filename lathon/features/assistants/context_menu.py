import customtkinter as ctk
from lathon.ui.widgets.modern_menu import ModernMenu
from lathon.ui.widgets.base_modal import BaseModal
from lathon.ui.design import Colors


class ContextMenuManager:
    """Intermediário que empacota as ações contextuais da UI."""

    def __init__(self, app, editor, spell_checker):
        self.app = app
        self.editor = editor
        self.spell_checker = spell_checker
        self.context_menu = ModernMenu(app, width=220)
        self.editor.bind("<Button-3>", self._on_right_click, add="+")

    def _on_right_click(self, event):
        self.context_menu.clear()
        index = self.editor.index(f"@{event.x},{event.y}")

        # Verifica se o clique ocorreu fora da área previamente selecionada pelo usuário
        # Se sim, anula a seleção antiga e foca na palavra exata sob o cursor.
        try:
            sel_start, sel_end = self.editor.tag_ranges("sel")
            if self.editor.compare(index, "<", sel_start) or self.editor.compare(index, ">=", sel_end):
                self.editor.tag_remove("sel", "1.0", "end")
                self._select_word_under_cursor(index)
        except ValueError:
            self._select_word_under_cursor(index)

        # Monta os comandos em camadas
        self._build_marker_options(index)
        self.spell_checker.build_context_options(self.context_menu, index)

        if len(self.context_menu.buttons) > 0:
            self.context_menu.popup(event.x_root, event.y_root)
        return "break"

    def _select_word_under_cursor(self, index):
        """Garante a seleção do alvo textual exato para ações dependentes de contexto."""
        word = self.editor.get(f"{index} wordstart", f"{index} wordend").strip()
        if word:
            self.editor.tag_add("sel", f"{index} wordstart", f"{index} wordend")

    def _build_marker_options(self, index):
        """Gera ações dinâmicas de Adição ou Remoção de Anotações."""
        tags_at_click = self.editor.tag_names(index)
        mark_tag = next((t for t in tags_at_click if t.startswith("user_mark_")), None)

        if mark_tag:
            self.context_menu.add_command("Remover Marcação", lambda t=mark_tag: self.editor.remove_marker(t),
                                          text_color=Colors.BTN_DANGER)
            self.context_menu.add_separator()
        else:
            try:
                if self.editor.tag_ranges("sel"):
                    self.context_menu.add_command("Marcar Texto...", lambda: self._prompt_mark())
                    self.context_menu.add_separator()
            except ValueError:
                pass

    def _prompt_mark(self):
        """Abre uma janela modal compacta que processa o cadastro de uma nova anotação colorida."""
        try:
            sel_start, sel_end = self.editor.tag_ranges("sel")
        except ValueError:
            return

        modal = BaseModal(self.app, "Marcação de Texto", 350, 220)

        ctk.CTkLabel(modal.border_frame, text="Adicione um comentário (ou deixe em branco):",
                     text_color=Colors.TEXT_NORMAL).pack(pady=(15, 5))
        entry = ctk.CTkEntry(modal.border_frame, width=280, fg_color=Colors.BG_MAIN, text_color=Colors.TEXT_NORMAL)
        entry.pack(pady=5)
        entry.focus_set()

        color_frame = ctk.CTkFrame(modal.border_frame, fg_color="transparent")
        color_frame.pack(pady=(10, 0))

        selected_color = ctk.StringVar(value=Colors.MARKER_YELLOW)

        # Renderiza botões em miniatura baseados na paleta do design system
        for hex_code, name in Colors.MARKER_PALETTE:
            rb = ctk.CTkRadioButton(color_frame, text="", variable=selected_color, value=hex_code, fg_color=hex_code,
                                    hover_color=hex_code, border_color=hex_code, width=20, border_width_checked=6)
            rb.pack(side="left", padx=10)

        def on_ok(event=None):
            modal.result = (selected_color.get(), entry.get())
            modal._close_dialog()

        def on_cancel(event=None):
            modal.result = None
            modal._close_dialog()

        entry.bind("<Return>", on_ok)
        entry.bind("<Escape>", on_cancel)
        modal._create_action_buttons("Marcar", on_ok)

        # O modal suspende o fluxo até o usuário interagir
        result = modal.get_data()

        if result:
            color, comment = result
            # Restaura a seleção do texto e aplica a cor na indexação
            self.editor.tag_add("sel", sel_start, sel_end)
            self.editor.add_marker(color, comment)