from lathon.features.preferences.layout_config import LayoutConfigDialog
from lathon.features.preferences.font_config import FontConfigDialog
from lathon.features.preferences.spell_config import SpellConfigDialog

class PreferencesManager:
    """Gerencia as configurações do sistema e aplica as mudanças na UI, aliviando o main_window.py."""

    def __init__(self, app):
        self.app = app

    # --- ABERTURA DAS TELAS ---
    def open_spell_config(self):
        SpellConfigDialog(self.app, self.app.spell_checker)

    def open_font_config(self):
        FontConfigDialog(self.app)

    def open_layout_config(self):
        LayoutConfigDialog(self.app)

    # --- LÓGICA DE APLICAÇÃO (Removida do main_window.py) ---
    def apply_layout_weights(self, left_pct, center_pct, pdf_pct):
        """Aplica as larguras dos painéis e salva na configuração."""
        self.app.main_frame.grid_columnconfigure(0, weight=left_pct, uniform="colunas")
        self.app.main_frame.grid_columnconfigure(1, weight=center_pct, uniform="colunas")
        self.app.main_frame.grid_columnconfigure(2, weight=pdf_pct, uniform="colunas")
        self.app.config.update_layout(left=left_pct, center=center_pct, pdf=pdf_pct)
        if self.app.project_dir:
            self.app.compile_action()

    def apply_font_config(self, family, size):
        """Atualiza a fonte do editor e do terminal, e salva na configuração."""
        self.app.editor.configure_font((family, size))
        self.app.config.update_layout(font_family=family, font_size=size)