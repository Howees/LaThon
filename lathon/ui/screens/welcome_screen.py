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
        """Renderiza a tela de configuração inicial (Setup Wizard) centralizada."""

        # OBS: Removemos os comandos self.app.geometry() e self.app.state() daqui.
        # Agora ela respeita a posição X e Y calculada pelo main_window!

        container = ctk.CTkFrame(self, fg_color="transparent")
        # MÁGICA DO ALINHAMENTO INTERNO
        container.place(relx=0.5, rely=0.5, anchor="center")

        # --- LOGO E BOAS-VINDAS ---
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(pady=(0, 15))

        big_logo = Icons.get_ctk_image("lathon.ico", size=(80, 80))
        if big_logo:
            ctk.CTkLabel(header, text="", image=big_logo).pack(pady=(0, 10))

        welcome_f = ctk.CTkFrame(header, fg_color="transparent")
        welcome_f.pack()
        ctk.CTkLabel(welcome_f, text="Bem-vindo ao ", font=Fonts.UI_MODAL_TITLE, text_color=Colors.TEXT_NORMAL).pack(
            side="left")
        create_lathon_logo(welcome_f, font_size=24).pack(side="left")

        ctk.CTkLabel(header, text="Vamos preparar o seu ambiente de trabalho.", font=Fonts.UI,
                     text_color=Colors.TEXT_MUTED).pack(pady=(5, 0))

        # --- PASSO 1: TEMA ---
        theme_frame = ctk.CTkFrame(container, fg_color="transparent")
        theme_frame.pack(pady=(10, 20), fill="x")

        ctk.CTkLabel(theme_frame, text="1. Escolha sua interface:", font=Fonts.UI_BOLD, text_color=Colors.TEXT_NORMAL,
                     anchor="w").pack(fill="x", pady=(0, 10))

        def on_theme_change(choice):
            theme_map = {"Classic (Preto)": "black", "La (Verde)": "green", "Thon (Azul)": "blue"}
            sys_theme = theme_map[choice]
            self.app.config.update_appearance(color_theme=sys_theme)
            c_data = Colors.THEME_BTNS[sys_theme]
            seg_btn.configure(selected_color=c_data["color"], selected_hover_color=c_data["hover"])

        current_theme = self.app.config.get_appearance().get("color_theme", "black")
        rev_map = {"black": "Classic (Preto)", "green": "La (Verde)", "blue": "Thon (Azul)"}
        initial_choice = rev_map.get(current_theme, "Classic (Preto)")
        init_c_data = Colors.THEME_BTNS[current_theme]

        seg_btn = ctk.CTkSegmentedButton(theme_frame, values=["Classic (Preto)", "La (Verde)", "Thon (Azul)"],
                                         command=on_theme_change,
                                         selected_color=init_c_data["color"],
                                         selected_hover_color=init_c_data["hover"])
        seg_btn.set(initial_choice)
        seg_btn.pack(fill="x")

        # --- PASSO 2: PASTA PRINCIPAL ---
        folder_frame = ctk.CTkFrame(container, fg_color="transparent")
        folder_frame.pack(pady=(0, 0), fill="x")

        ctk.CTkLabel(folder_frame, text="2. Defina o seu cofre de projetos:", font=Fonts.UI_BOLD,
                     text_color=Colors.TEXT_NORMAL, anchor="w").pack(fill="x", pady=(0, 10))

        ctk.CTkButton(folder_frame, text=" Escolher Pasta e Começar", image=Icons.get_ctk_image("folder.png"),
                      command=self.manager.set_root_directory, font=Fonts.UI_TITLE, height=45,
                      fg_color=Colors.BTN_PRIMARY, hover_color=Colors.BTN_PRIMARY_HOVER).pack(fill="x")