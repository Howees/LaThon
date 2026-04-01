

from lathon.features.preferences.layout_config import LayoutConfigDialog
from lathon.features.preferences.font_config import FontConfigDialog
from lathon.features.preferences.spell_config import SpellConfigDialog


class PreferencesManager:
    """
    Gerenciador central de configurações e aplicação de layout
    Intermedia as requisições das modais de configuração e aplica as mudanças globais
    na janela principal (main_window), garantindo o isolamento de responsabilidades.
    """

    def __init__(self, app):
        self.app = app

    # ==========================================
    # ROTAS DE ABERTURA DE MODAIS
    # ==========================================
    def open_spell_config(self):
        SpellConfigDialog(self.app, self.app.spell_checker)

    def open_font_config(self):
        FontConfigDialog(self.app)

    def open_layout_config(self):
        LayoutConfigDialog(self.app)

    # ==========================================
    # LÓGICA DE APLICAÇÃO VISUAL
    # ==========================================
    def apply_layout_weights(self, left_pct, center_pct, pdf_pct):
        """
        Ajusta a proporção das colunas da janela principal via Tkinter Grid Weights
        e salva os novos valores no arquivo JSON. Dispara recompilação para ajustar PDF se necessário.
        """
        self.app.main_frame.grid_columnconfigure(0, weight=left_pct, uniform="colunas")
        self.app.main_frame.grid_columnconfigure(1, weight=center_pct, uniform="colunas")
        self.app.main_frame.grid_columnconfigure(2, weight=pdf_pct, uniform="colunas")
        self.app.config.update_layout(left=left_pct, center=center_pct, pdf=pdf_pct)

        if self.app.project_dir:
            self.app.compile_action()

    def apply_font_config(self, family, size):
        """Aplica os novos parâmetros tipográficos no Text Editor nativo e salva as preferências."""
        self.app.editor.configure_font((family, size))
        self.app.config.update_layout(font_family=family, font_size=size)