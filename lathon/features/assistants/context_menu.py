from lathon.ui.widgets.modern_menu import ModernMenu
from lathon.features.assistants.marker_dialog import MarkerDialog

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors

class ContextMenuManager:
    """Gerencia a exibição do menu de botão direito, delegando as ações para os respectivos módulos."""
    def __init__(self, app, editor, spell_checker):
        self.app = app
        self.editor = editor
        self.spell_checker = spell_checker
        self.context_menu = ModernMenu(app, width=220)
        self.editor.bind("<Button-3>", self._on_right_click, add="+")

    def _on_right_click(self, event):
        self.context_menu.clear()
        index = self.editor.index(f"@{event.x},{event.y}")

        try:
            sel_start, sel_end = self.editor.tag_ranges("sel")
            if self.editor.compare(index, "<", sel_start) or self.editor.compare(index, ">=", sel_end):
                self.editor.tag_remove("sel", "1.0", "end")
                self._select_word_under_cursor(index)
        except ValueError:
            self._select_word_under_cursor(index)

        self._build_marker_options(index)
        self.spell_checker.build_context_options(self.context_menu, index)

        if len(self.context_menu.buttons) > 0:
            self.context_menu.popup(event.x_root, event.y_root)
        return "break"

    def _select_word_under_cursor(self, index):
        word = self.editor.get(f"{index} wordstart", f"{index} wordend").strip()
        if word:
            self.editor.tag_add("sel", f"{index} wordstart", f"{index} wordend")

    def _build_marker_options(self, index):
        tags_at_click = self.editor.tag_names(index)
        mark_tag = next((t for t in tags_at_click if t.startswith("user_mark_")), None)

        if mark_tag:
            self.context_menu.add_command("Remover Marcação", lambda t=mark_tag: self.editor.remove_marker(t), text_color=Colors.BTN_DANGER)
            self.context_menu.add_separator()
        else:
            try:
                if self.editor.tag_ranges("sel"):
                    self.context_menu.add_command("Marcar Texto...", lambda: self._prompt_mark())
                    self.context_menu.add_separator()
            except ValueError: pass

    def _prompt_mark(self):
        try: sel_start, sel_end = self.editor.tag_ranges("sel")
        except ValueError: return

        d = MarkerDialog(self.app)
        result = d.get_data()

        if result:
            color, comment = result
            self.editor.tag_add("sel", sel_start, sel_end)
            self.editor.add_marker(color, comment)