from lathon.features.assistants.theme_manager import ThemeManager
from lathon.features.assistants.markers_list_dialog import MarkersListDialog

class OptionsManager:
    """
    Gerencia as ações diretas do Menu 'Opções'.
    É a ponte entre o main_window.py e os módulos da pasta assistants.
    """
    def __init__(self, app):
        self.app = app

    # --- GERENCIAMENTO DO TEMA ---
    def toggle_theme(self):
        ThemeManager.toggle_theme(self.app)

    # --- GERENCIAMENTO DE BUSCA (FIND/REPLACE) ---
    def show_find_dialog(self):
        # Acessa o find_handler que está instanciado no app
        if hasattr(self.app, 'find_handler'):
            self.app.find_handler.show_dialog()

    # --- GERENCIAMENTO DA LISTA DE MARCAÇÕES ---
    def open_markers_list(self):
        MarkersListDialog(self.app)

    # --- ATIVAÇÃO/DESATIVAÇÃO DOS ASSISTENTES (TOGGLES) ---
    def set_chapter_highlight(self, active):
        if not hasattr(self.app, 'chapter_highlighter'): return
        self.app.chapter_highlighter.is_active = active
        if active:
            self.app.chapter_highlighter.update_colors()
            self.app.chapter_highlighter.apply()
        else:
            self.app.chapter_highlighter.remove()

    def set_autocomplete(self, active):
        if not hasattr(self.app, 'autocomplete_handler'): return
        self.app.autocomplete_handler.is_active = active

    def set_spellcheck(self, active):
        if not hasattr(self.app, 'spell_checker'): return
        self.app.spell_checker.is_active = active
        if active:
            self.app.spell_checker.apply_spell_check()
        else:
            self.app.spell_checker.clear_state()