import customtkinter as ctk
from lathon.ui.design import Colors, Fonts, Icons
from lathon.ui.widgets.icon_button import create_icon_button

class RepoPanel(ctk.CTkFrame):
    def __init__(self, parent, app, root_path, manager):
        super().__init__(parent, fg_color="transparent")
        self.manager = manager

        toolbar = ctk.CTkFrame(self, height=60, fg_color="transparent")
        toolbar.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(toolbar, text="Meus Repositórios", font=Fonts.UI_MODAL_TITLE, text_color=Colors.TEXT_NORMAL).pack(side="left")

        actions_right = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_right.pack(side="right")
        ctk.CTkButton(actions_right, text=" Importar Repositório", image=Icons.get_ctk_image("import.png", size=(16, 16)),
                      command=lambda: manager.import_repository(root_path), fg_color="transparent", border_width=1,
                      border_color=Colors.BORDER, text_color=Colors.TEXT_NORMAL, hover_color=Colors.BTN_HOVER).pack(side="left", padx=(0, 10))
        ctk.CTkButton(actions_right, text=" Novo Repositório", image=Icons.get_ctk_image("new.png", size=(16, 16)),
                      command=lambda: manager.create_repository(root_path), fg_color=Colors.BTN_PRIMARY,
                      hover_color=Colors.BTN_PRIMARY_HOVER, font=Fonts.UI_BOLD, text_color=Colors.TEXT_NORMAL).pack(side="left")

        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        repositorios = [d for d in root_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if not repositorios:
            ctk.CTkLabel(scroll_frame, text="Seu cofre está vazio. Crie um novo Repositório para começar!",
                         text_color=Colors.TEXT_MUTED, font=Fonts.UI).pack(pady=40)
        else:
            for repo in repositorios: self._create_card(scroll_frame, repo)

    def _create_card(self, parent, repo_path):
        card = ctk.CTkFrame(parent, fg_color=Colors.BG_PANEL, corner_radius=8, border_width=1, border_color=Colors.BORDER)
        card.pack(fill="x", pady=5, padx=10)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="", image=Icons.get_ctk_image("folder.png", size=(24, 24))).grid(row=0, column=0, padx=(15, 10), pady=15)
        ctk.CTkLabel(card, text=repo_path.name, font=Fonts.UI_TITLE, text_color=Colors.TEXT_NORMAL).grid(row=0, column=1, sticky="w")

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=2, padx=15, sticky="e")
        create_icon_button(actions, "trash.png", "Excluir Repositório", lambda: self.manager.delete_folder(repo_path, "Repositório"), is_danger=True)
        ctk.CTkFrame(actions, width=1, height=20, fg_color=Colors.BORDER).pack(side="left", padx=10)
        ctk.CTkButton(actions, text=" Entrar", image=Icons.get_ctk_image("open.png", size=(16, 16)),
                      command=lambda: self.manager.enter_repository(repo_path), width=90, height=32, font=Fonts.UI_BOLD,
                      fg_color=Colors.BG_MAIN, border_width=1, border_color=Colors.BORDER, text_color=Colors.TEXT_NORMAL, hover_color=Colors.BTN_HOVER).pack(side="left")