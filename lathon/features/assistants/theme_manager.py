import customtkinter as ctk


class ThemeManager:
    """Gerencia a alternância de Tema Claro/Escuro por todo o sistema."""

    @staticmethod
    def toggle_theme(app):
        new_theme = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)

        app.file_panel.style_treeview()
        app.main_frame.configure(fg_color="#2b2b2b" if new_theme == "Dark" else "#e6e6e6")

        # Atualiza a base do editor
        app.editor.update_colors()

        # Atualiza a cor dos capítulos (se estiver ativo)
        if hasattr(app, 'chapter_highlighter'):
            app.chapter_highlighter.update_colors()

        is_dark = new_theme == "Dark"
        if hasattr(app, 'autocomplete_handler') and app.autocomplete_handler.suggestions_listbox:
            app.autocomplete_handler.suggestions_listbox.config(bg="#2b2b2b" if is_dark else "#f0f0f0",
                                                                fg="white" if is_dark else "black")