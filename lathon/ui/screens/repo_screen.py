import customtkinter as ctk
import tkinter as tk

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts, Icons, create_lathon_logo
from lathon.ui.widgets.icon_button import create_icon_button


class RepoPanel(ctk.CTkFrame):
    """
    Componente Visual: Tela global que lista os Repositórios do usuário.
    Gerencia a interface Raiz do Cofre (Workspace Central).
    Exibe todos os Repositórios (grupos de projetos) do usuário,
    permitindo criar novas pastas lógicas ou excluir repositórios existentes.
    """

    def __init__(self, parent, app, root_path, manager):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.manager = manager

        # ==========================================
        # BARRA DE FERRAMENTAS SUPERIOR (TOOLBAR)
        # ==========================================
        toolbar = ctk.CTkFrame(self, height=60, fg_color="transparent")
        toolbar.pack(fill="x", padx=40, pady=(40, 20))

        ctk.CTkLabel(toolbar, text="Meus Repositórios", font=Fonts.UI_MODAL_TITLE, text_color=Colors.TEXT_NORMAL).pack(
            side="left")

        actions_right = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_right.pack(side="right")

        # Adequação das cores do menu nativo com o tema selecionado no CustomTkinter
        idx = 1 if ctk.get_appearance_mode() == "Dark" else 0

        menu_import = tk.Menu(self, tearoff=0, bg=Colors.BG_MAIN[idx], fg=Colors.TEXT_NORMAL[idx],
                              activebackground=Colors.THON)
        menu_import.add_command(label=" Importar de ZIP", image=Icons.get_treeview_icon("zip.png"), compound="left",
                                command=lambda: manager.import_repo_zip(root_path))
        menu_import.add_command(label=" Importar de Pasta", image=Icons.get_treeview_icon("folder.png"),
                                compound="left",
                                command=lambda: manager.import_repository(root_path))

        btn_import = ctk.CTkButton(actions_right, text=" Importar Repositório",
                                   image=Icons.get_ctk_image("import.png", size=(16, 16)),
                                   command=lambda: self.app._popup_menu(menu_import, btn_import),
                                   fg_color="transparent",
                                   border_width=1, border_color=Colors.BORDER, text_color=Colors.TEXT_NORMAL,
                                   hover_color=Colors.BTN_HOVER)
        btn_import.pack(side="left", padx=(0, 10))

        ctk.CTkButton(actions_right, text=" Novo Repositório", image=Icons.get_ctk_image("new.png", size=(16, 16)),
                      command=lambda: manager.create_repository(root_path), fg_color=Colors.BTN_PRIMARY,
                      hover_color=Colors.BTN_PRIMARY_HOVER, font=Fonts.UI_BOLD, text_color=Colors.TEXT_NORMAL).pack(
            side="left")

        # ==========================================
        # RODAPÉ E IDENTIDADE VISUAL
        # ==========================================
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=(0, 20))
        logo_container = ctk.CTkFrame(footer, fg_color="transparent")
        logo_container.pack()
        create_lathon_logo(logo_container, font_size=14).pack(side="left")
        ctk.CTkLabel(logo_container, text=" v2.0", font=Fonts.UI_BOLD, text_color=Colors.TEXT_MUTED).pack(side="left",
                                                                                                          padx=(2, 0))

        # ==========================================
        # ÁREA DE LISTAGEM DE REPOSITÓRIOS (CARDS)
        # ==========================================
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        repositorios = [d for d in root_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

        if not repositorios:
            ctk.CTkLabel(scroll_frame, text="Seu cofre está vazio. Crie um novo Repositório para começar!",
                         text_color=Colors.TEXT_MUTED, font=Fonts.UI).pack(pady=40)
        else:
            for repo in repositorios:
                self._create_card(scroll_frame, repo)

    def _create_card(self, parent, repo_path):
        """Constrói o componente visual (Card) para representar um Repositório na lista."""
        card = ctk.CTkFrame(parent, fg_color=Colors.BG_PANEL, corner_radius=8, border_width=1,
                            border_color=Colors.BORDER)
        card.pack(fill="x", pady=5, padx=10)
        card.grid_columnconfigure(1, weight=1)

        # Indicador visual lateral (Fita Azul) que identifica a hierarquia de Repositório (Pasta Maior)
        ribbon = ctk.CTkFrame(card, width=4, fg_color=Colors.THON, corner_radius=4)
        ribbon.place(relx=0, rely=0.15, relheight=0.7, x=4)

        ctk.CTkLabel(card, text="", image=Icons.get_ctk_image("folder.png", size=(24, 24))).grid(row=0, column=0,
                                                                                                 padx=(15, 10), pady=15)
        ctk.CTkLabel(card, text=repo_path.name, font=Fonts.UI_TITLE, text_color=Colors.TEXT_NORMAL).grid(row=0,
                                                                                                         column=1,
                                                                                                         sticky="w")

        # Ações do Repositório
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=2, padx=15, sticky="e")
        create_icon_button(actions, "trash.png", "Excluir Repositório",
                           lambda: self.manager.delete_folder(repo_path, "Repositório"), is_danger=True)

        ctk.CTkFrame(actions, width=1, height=20, fg_color=Colors.BORDER).pack(side="left", padx=10)

        ctk.CTkButton(actions, text=" Entrar", image=Icons.get_ctk_image("open.png", size=(16, 16)),
                      command=lambda: self.manager.enter_repository(repo_path), width=90, height=32,
                      font=Fonts.UI_BOLD, fg_color=Colors.BG_MAIN, border_width=1, border_color=Colors.BORDER,
                      text_color=Colors.TEXT_NORMAL, hover_color=Colors.BTN_HOVER).pack(side="left")