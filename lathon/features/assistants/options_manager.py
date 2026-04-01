from lathon.features.assistants.theme_manager import ThemeManager
from lathon.ui.widgets.base_modal import BaseModal
from lathon.ui.design import Colors, Fonts
import customtkinter as ctk


class OptionsManager:
    """Controlador que vincula componentes de UI aos módulos em background."""

    def __init__(self, app):
        self.app = app
        self.show_warnings = True

    def toggle_theme(self):
        ThemeManager.toggle_theme(self.app)

    def set_color_theme(self, theme_name):
        ThemeManager.set_color_theme(self.app, theme_name)

    def show_find_dialog(self):
        if hasattr(self.app, 'find_handler'):
            self.app.find_handler.show_dialog()

    def open_markers_list(self):
        """Modal de Tabela (Dashboard) listando todos os comentários vinculados ao texto."""
        modal = BaseModal(self.app, "Lista de Marcações", 500, 400)
        ctk.CTkLabel(modal.border_frame, text="Anotações no Documento", font=Fonts.UI_TITLE).pack(anchor="w", padx=20,
                                                                                                  pady=(20, 5))

        scroll = ctk.CTkScrollableFrame(modal.border_frame, fg_color=Colors.BG_MAIN)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        comments = self.app.editor.mark_comments

        if not comments:
            ctk.CTkLabel(scroll, text="Nenhuma marcação no documento atual.", text_color=Colors.TEXT_MUTED,
                         font=Fonts.UI).pack(pady=20)
        else:
            for tag, comment in comments.items():
                try:
                    idx = self.app.editor.index(f"{tag}.first")
                    line = idx.split(".")[0]
                    word = self.app.editor.get(f"{tag}.first", f"{tag}.last")
                except:
                    continue

                f = ctk.CTkFrame(scroll, fg_color="transparent")
                f.pack(fill="x", pady=2, padx=5)

                color = self.app.editor.tag_cget(tag, "background")
                ctk.CTkFrame(f, width=12, height=12, fg_color=color, corner_radius=6).pack(side="left", padx=(0, 10))

                text_disp = f"Linha {line} | '{word}' -> {comment if comment else '(Sem comentário)'}"
                ctk.CTkLabel(f, text=text_disp, anchor="w", justify="left", font=Fonts.UI).pack(side="left", fill="x",
                                                                                                expand=True)

                def goto_line(t=idx):
                    """Transporta o cursor para o trecho exato da anotação, mesmo em textos imensos."""
                    self.app.editor.see(t)
                    self.app.editor.mark_set("insert", t)
                    modal._close_dialog()

                ctk.CTkButton(f, text="Ir", width=40, height=24, font=Fonts.UI, fg_color=Colors.BTN_PRIMARY,
                              hover_color=Colors.BTN_PRIMARY_HOVER, command=goto_line).pack(side="right")

        modal._create_action_buttons("Fechar", modal._close_dialog)
        modal.get_data()

        # ==========================================

    # COMANDOS DE ATIVAÇÃO GERAL (TOGGLES)
    # ==========================================
    def set_chapter_highlight(self, active):
        if not hasattr(self.app, 'chapter_highlighter'): return
        self.app.chapter_highlighter.is_active = active
        if active:
            self.app.chapter_highlighter.update_colors()
            self.app.chapter_highlighter.apply()
        else:
            self.app.chapter_highlighter.remove()

    def set_autocomplete(self, active):
        if not hasattr(self.app, 'autocomplete_handler'): return
        self.app.autocomplete_handler.is_active = active

    def set_spellcheck(self, active):
        if not hasattr(self.app, 'spell_checker'): return
        self.app.spell_checker.is_active = active
        if active:
            self.app.spell_checker.apply_spell_check()
        else:
            self.app.spell_checker.clear_state()

    def set_warnings(self, active):
        """Determina se o Terminal irá omitir 'Overfull hbox' e 'Warnings' padrão do compilador."""
        self.show_warnings = active
        if hasattr(self.app, 'terminal_panel'):
            if not active:
                self.app.terminal_panel.log_line(">> Avisos (Warnings) desativados.", "warning")
            else:
                self.app.terminal_panel.log_line(">> Avisos (Warnings) ativados.", "success")