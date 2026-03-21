import tkinter as tk
import customtkinter as ctk
import datetime
from lathon.ui.design import Colors, Fonts, Icons
from lathon.ui.widgets.icon_button import create_icon_button
from lathon.core.exporter import ProjectExporter

class ProjectPanel(ctk.CTkFrame):
    def __init__(self, parent, app, ws_path, manager):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.manager = manager

        toolbar = ctk.CTkFrame(self, height=60, fg_color="transparent")
        toolbar.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(toolbar, text=f"Repositório: {ws_path.name}", font=Fonts.UI_MODAL_TITLE, text_color=Colors.TEXT_NORMAL).pack(side="left")

        actions_right = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_right.pack(side="right")
        ctk.CTkButton(actions_right, text=" Voltar aos Repositórios", image=Icons.get_ctk_image("back.png", size=(16, 16)), command=manager.force_workspace_selector, fg_color="transparent", border_width=1, border_color=Colors.BORDER, text_color=Colors.TEXT_NORMAL, hover_color=Colors.BTN_HOVER).pack(side="right", padx=(10, 0))

        menu_import = tk.Menu(self, tearoff=0, bg=Colors.BG_MAIN[1], fg="white", activebackground=Colors.THON)
        menu_import.add_command(label=" Importar de ZIP", image=Icons.get_treeview_icon("zip.png"), compound="left", command=lambda: manager.import_zip(ws_path))
        menu_import.add_command(label=" Importar de Pasta", image=Icons.get_treeview_icon("folder.png"), compound="left", command=lambda: manager.import_folder(ws_path))

        btn_import = ctk.CTkButton(actions_right, text=" Importar Projeto", image=Icons.get_ctk_image("import.png", size=(16, 16)), command=lambda: self.app._popup_menu(menu_import, btn_import), fg_color="transparent", border_width=1, border_color=Colors.BORDER, text_color=Colors.TEXT_NORMAL, hover_color=Colors.BTN_HOVER)
        btn_import.pack(side="right", padx=(10, 0))
        ctk.CTkButton(actions_right, text=" Novo Projeto", image=Icons.get_ctk_image("new.png", size=(16, 16)), command=lambda: manager.create_new_project(ws_path), fg_color=Colors.BTN_PRIMARY, hover_color=Colors.BTN_PRIMARY_HOVER, font=Fonts.UI_BOLD, text_color=Colors.TEXT_NORMAL).pack(side="right")

        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        projetos = [d for d in ws_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if not projetos:
            ctk.CTkLabel(scroll_frame, text="Nenhum projeto encontrado neste repositório. Crie ou importe um para começar!", text_color=Colors.TEXT_MUTED, font=Fonts.UI).pack(pady=40)
        else:
            projetos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            for proj in projetos: self._create_card(scroll_frame, proj)

    def _create_card(self, parent, project_path):
        card = ctk.CTkFrame(parent, fg_color=Colors.BG_PANEL, corner_radius=8, border_width=1, border_color=Colors.BORDER)
        card.pack(fill="x", pady=5, padx=10)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="", image=Icons.get_ctk_image("folder.png", size=(24, 24))).grid(row=0, column=0, rowspan=2, padx=(15, 10), pady=15)
        ctk.CTkLabel(card, text=project_path.name, font=Fonts.UI_TITLE, text_color=Colors.TEXT_NORMAL).grid(row=0, column=1, sticky="sw", pady=(12, 0))

        mod_time = datetime.datetime.fromtimestamp(project_path.stat().st_mtime).strftime("%d/%m/%Y às %H:%M")
        ctk.CTkLabel(card, text=f"Modificado em: {mod_time}", font=("Segoe UI", 11), text_color=Colors.TEXT_MUTED).grid(row=1, column=1, sticky="nw", pady=(0, 12))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, padx=15, sticky="e")

        create_icon_button(actions, "duplicate.png", "Duplicar Projeto", lambda: self.manager.duplicate_project(project_path))
        create_icon_button(actions, "rename.png", "Renomear", lambda: self.manager.rename_project(project_path))
        create_icon_button(actions, "pdf.png", "Exportar PDF", lambda: ProjectExporter.export_pdf(project_path, None))
        create_icon_button(actions, "zip.png", "Exportar ZIP", lambda: ProjectExporter.export_zip(project_path))
        create_icon_button(actions, "trash.png", "Excluir Projeto", lambda: self.manager.delete_folder(project_path, "Projeto"), is_danger=True)

        ctk.CTkFrame(actions, width=1, height=20, fg_color=Colors.BORDER).pack(side="left", padx=10)
        ctk.CTkButton(actions, text=" Abrir Projeto", image=Icons.get_ctk_image("open.png", size=(16, 16)), command=lambda: self.app.load_project_folder(project_path), width=90, height=32, font=Fonts.UI_BOLD, fg_color=Colors.BG_MAIN, border_width=1, border_color=Colors.BORDER, text_color=Colors.TEXT_NORMAL, hover_color=Colors.BTN_HOVER).pack(side="left")