import os
from pathlib import Path
import customtkinter as ctk

from lathon.core.workspace import WorkspaceManager
from lathon.ui.design import Colors, Fonts, Icons, create_lathon_logo
from lathon.ui.screens.repo_screen import RepoPanel
from lathon.ui.screens.project_screen import ProjectPanel


class WelcomeScreen(ctk.CTkFrame):
    """Atua como ROTEADOR e tela de SETUP inicial."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=Colors.BG_MAIN)
        self.app = app
        self.manager = WorkspaceManager(app, self)
        self._render()

    def _render(self):
        for widget in self.winfo_children():
            widget.destroy()

        root_path = self.app.config.get_root_path()
        if not root_path or not os.path.exists(root_path):
            self._render_setup_panel()
            return

        last_ws = self.app.config.get_last_workspace()
        if last_ws and os.path.exists(last_ws):
            if Path(root_path) in Path(last_ws).parents or Path(root_path) == Path(last_ws).parent:
                ProjectPanel(self, self.app, Path(last_ws), self.manager).pack(fill="both", expand=True)
                return

        RepoPanel(self, self.app, Path(root_path), self.manager).pack(fill="both", expand=True)

    def _render_setup_panel(self):
        """Renderiza a tela de configuração inicial direto na WelcomeScreen."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.place(relx=0.5, rely=0.4, anchor="center")

        create_lathon_logo(container, font_size=40).pack(pady=(0, 10))

        ctk.CTkLabel(container, text="Bem-vindo ao LaThon!", font=Fonts.UI_MODAL_TITLE,
                     text_color=Colors.TEXT_NORMAL).pack(pady=(0, 5))

        ctk.CTkLabel(container,
                     text="Para começarmos, escolha onde você deseja salvar todos os seus Repositórios e Projetos.",
                     font=Fonts.UI, text_color=Colors.TEXT_MUTED).pack(pady=(0, 30))

        ctk.CTkButton(container, text=" Escolher Pasta Principal", image=Icons.get_ctk_image("folder.png"),
                      command=self.manager.set_root_directory, font=Fonts.UI_TITLE, height=50,
                      fg_color=Colors.BTN_PRIMARY,
                      hover_color=Colors.BTN_PRIMARY_HOVER).pack()