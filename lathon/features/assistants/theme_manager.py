import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from lathon.ui.design import Colors


class ThemeManager:
    """Gerencia a alternância de Tema Claro/Escuro e as Cores Base do sistema."""

    @staticmethod
    def toggle_theme(app):
        # Descobre o novo tema e avisa o CustomTkinter
        new_theme = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)

        # Salva no arquivo de configuração
        app.config.update_appearance(mode=new_theme)

        is_dark = new_theme == "Dark"
        idx = 1 if is_dark else 0

        # ========================================================
        # 1. ATUALIZA COMPONENTES GLOBAIS/PERSISTENTES
        # (Estes existem desde o início e ficam escondidos, então DEVEM atualizar sempre!)
        # ========================================================

        # A) Fundo do frame principal
        if hasattr(app, 'main_frame'):
            app.main_frame.configure(fg_color=Colors.BG_MAIN[idx])

        # B) Árvore de Arquivos (Treeview é do Tkinter Clássico e precisa de estilo manual)
        if hasattr(app, 'file_panel'):
            app.file_panel.style_treeview()

        # C) Menus Superiores (tk.Menu Clássico não obedece ao CustomTkinter automaticamente)
        menu_bg = Colors.BG_MAIN[idx]
        menu_fg = Colors.TEXT_NORMAL[idx]

        for attr_name in dir(app):
            attr_value = getattr(app, attr_name, None)
            if isinstance(attr_value, tk.Menu):
                try:
                    attr_value.configure(bg=menu_bg, fg=menu_fg,
                                         activebackground=Colors.BTN_HOVER[idx],
                                         activeforeground=menu_fg)
                except:
                    pass

        # ========================================================
        # 2. ATUALIZA A TELA QUE O USUÁRIO ESTÁ VENDO AGORA
        # ========================================================
        if app.project_dir:
            # O usuário está dentro do Editor
            if hasattr(app, 'editor'):
                app.editor.update_colors()
                app.editor.apply_syntax_highlighting()

            if hasattr(app, 'chapter_highlighter') and app.chapter_highlighter.is_active:
                app.chapter_highlighter.update_colors()
                app.chapter_highlighter.apply()

            if hasattr(app, 'autocomplete_handler') and app.autocomplete_handler.suggestions_listbox:
                app.autocomplete_handler.suggestions_listbox.config(
                    bg=Colors.BG_PANEL[idx],
                    fg=Colors.TEXT_NORMAL[idx]
                )
        else:
            # O usuário está nas Telas de Repositório/Projetos
            # O CustomTkinter vai trocar a cor dos frames sozinho, mas nós mandamos
            # a tela se renderizar de novo para recriar os botões de menu (tk.Menu) com a cor certa.
            if hasattr(app, 'welcome_screen'):
                app.welcome_screen.configure(fg_color=Colors.BG_MAIN)
                app.welcome_screen._render()

    @staticmethod
    def set_color_theme(app, theme_name):
        """Muda a paleta base (black, green, blue), salva e avisa sobre o reinício."""

        # Salva no JSON
        app.config.update_appearance(color_theme=theme_name)

        # Avisa o usuário!
        messagebox.showinfo(
            "Tema Alterado",
            f"O tema de cores foi alterado para '{theme_name.capitalize()}'.\n\n"
            "Por favor, reinicie o LaThon para aplicar a nova paleta completamente."
        )