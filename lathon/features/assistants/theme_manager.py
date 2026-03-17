import customtkinter as ctk
from lathon.ui.design import Colors


class ThemeManager:
    """Gerencia a alternância de Tema Claro/Escuro por todo o sistema."""

    @staticmethod
    def toggle_theme(app):
        # 1. Descobre o novo tema e avisa o CustomTkinter
        new_theme = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)

        is_dark = new_theme == "Dark"
        idx = 1 if is_dark else 0

        # 2. Atualiza os painéis principais
        app.file_panel.style_treeview()
        app.main_frame.configure(fg_color=Colors.BG_MAIN[idx])

        # 3. Força a atualização dos Menus do Topo (Eles não atualizam sozinhos!)
        menu_bg = Colors.BG_MAIN[idx]
        menu_fg = Colors.TEXT_NORMAL[idx]
        for menu in [app.menu_file, app.menu_insert, app.menu_options, app.menu_export, app.menu_config]:
            menu.configure(bg=menu_bg, fg=menu_fg)

        # 4. Atualiza a base do editor e FORÇA a sintaxe a repintar na hora
        app.editor.update_colors()
        app.editor.apply_syntax_highlighting()

        # 5. Atualiza a cor dos capítulos (se estiver ativo)
        if hasattr(app, 'chapter_highlighter') and app.chapter_highlighter.is_active:
            app.chapter_highlighter.update_colors()
            app.chapter_highlighter.apply()

        # 6. Atualiza a janela flutuante do Autocompletar
        if hasattr(app, 'autocomplete_handler') and app.autocomplete_handler.suggestions_listbox:
            app.autocomplete_handler.suggestions_listbox.config(
                bg=Colors.BG_PANEL[idx],
                fg=Colors.TEXT_NORMAL[idx]
            )