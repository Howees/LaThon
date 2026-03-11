import tkinter as tk
import customtkinter as ctk


class FindReplaceHandler:
    def __init__(self, app, editor, find_frame):
        self.app = app
        self.editor = editor
        self.find_frame = find_frame
        self.matches = []
        self.current_match_idx = -1
        self.replace_popup = None

        # --- A NOVA INTERFACE MODERNA (Estilo VS Code / Imagem do Usuário) ---
        self.find_entry = ctk.CTkEntry(self.find_frame, placeholder_text="Localizar...", width=150, height=28,
                                       border_width=0, fg_color="transparent")
        self.find_entry.pack(side="left", padx=(10, 5), pady=4)

        self.find_counter = ctk.CTkLabel(self.find_frame, text="0/0", text_color="gray50", width=40)
        self.find_counter.pack(side="left", padx=5)

        self.btn_prev = ctk.CTkButton(self.find_frame, text="↑", width=28, height=28, fg_color="transparent",
                                      hover_color=("gray80", "#3a3d41"), text_color=("black", "white"),
                                      command=self.prev_match)
        self.btn_prev.pack(side="left", padx=1)

        self.btn_next = ctk.CTkButton(self.find_frame, text="↓", width=28, height=28, fg_color="transparent",
                                      hover_color=("gray80", "#3a3d41"), text_color=("black", "white"),
                                      command=self.next_match)
        self.btn_next.pack(side="left", padx=1)

        self.btn_more = ctk.CTkButton(self.find_frame, text="⋮", width=28, height=28, fg_color="transparent",
                                      hover_color=("gray80", "#3a3d41"), text_color=("black", "white"),
                                      command=self.show_replace_popup)
        self.btn_more.pack(side="left", padx=1)

        self.btn_close = ctk.CTkButton(self.find_frame, text="✕", width=28, height=28, fg_color="transparent",
                                       hover_color="#ffcccc", text_color=("black", "white"), command=self.hide_dialog)
        self.btn_close.pack(side="left", padx=(1, 5))

        # Eventos para o usuário digitar e pesquisar ao vivo
        self.find_entry.bind("<KeyRelease>", self.update_matches)
        self.find_entry.bind("<Return>", lambda e: self.next_match())
        self.find_entry.bind("<Escape>", lambda e: self.hide_dialog())

        # Ouve o editor!
        self.editor.bind("<<EditorTextChanged>>", self._on_editor_changed, add="+")

    def _on_editor_changed(self, event=None):
        if self.find_frame.winfo_ismapped():
            self.update_matches()

    def show_dialog(self, event=None):
        # A mágica do painel flutuante
        self.find_frame.place(relx=0.98, rely=0.02, anchor="ne")
        self.find_frame.lift()
        self.find_entry.focus_set()
        self.find_entry.select_range(0, 'end')
        self.update_matches()
        return "break"

    def hide_dialog(self, event=None):
        self.editor.tag_remove("find_highlight_all", "1.0", "end")
        self.editor.tag_remove("find_highlight_current", "1.0", "end")
        self.find_frame.place_forget()
        self._close_replace_popup()

        # Devolve o foco para o editor imediatamente!
        self.app.focus_force()
        self.editor.focus_set()
        return "break"

    def update_matches(self, event=None):
        query = self.find_entry.get()
        self.editor.tag_remove("find_highlight_all", "1.0", "end")
        self.editor.tag_remove("find_highlight_current", "1.0", "end")
        self.matches = []
        self.current_match_idx = -1

        if not query:
            self.find_counter.configure(text="0/0")
            return

        start_pos = "1.0"
        while True:
            pos = self.editor._textbox.search(query, start_pos, stopindex="end", nocase=True)
            if not pos: break
            end_pos = f"{pos} + {len(query)} chars"
            self.matches.append((pos, end_pos))
            self.editor.tag_add("find_highlight_all", pos, end_pos)
            start_pos = end_pos

        if self.matches:
            self.current_match_idx = 0
            self._highlight_current()
        else:
            self.find_counter.configure(text="0/0")

    def _highlight_current(self):
        self.editor.tag_remove("find_highlight_current", "1.0", "end")
        if not self.matches or self.current_match_idx < 0 or self.current_match_idx >= len(self.matches): return

        pos, end_pos = self.matches[self.current_match_idx]
        self.editor.tag_add("find_highlight_current", pos, end_pos)
        self.editor.see(pos)
        self.find_counter.configure(text=f"{self.current_match_idx + 1}/{len(self.matches)}")

    def next_match(self):
        if not self.matches: return
        self.current_match_idx = (self.current_match_idx + 1) % len(self.matches)
        self._highlight_current()

    def prev_match(self):
        if not self.matches: return
        self.current_match_idx = (self.current_match_idx - 1) % len(self.matches)
        self._highlight_current()

    def show_replace_popup(self):
        if self.replace_popup and self.replace_popup.winfo_exists():
            self._close_replace_popup()
            return

        self.replace_popup = ctk.CTkToplevel(self.app)
        self.replace_popup.overrideredirect(True)
        self.replace_popup.transient(self.app)
        self.replace_popup.configure(fg_color=("white", "#2b2b2b"))

        border = ctk.CTkFrame(self.replace_popup, border_width=1, border_color=("gray70", "#454545"))
        border.pack(fill="both", expand=True)

        self.replace_entry = ctk.CTkEntry(border, placeholder_text="Substituir por...", width=150, height=28)
        self.replace_entry.pack(side="left", padx=5, pady=5)
        self.replace_entry.bind("<Return>", lambda e: self.replace_all())

        # Se mudar de ideia e apertar Esc, esconde e devolve o clique
        self.replace_entry.bind("<Escape>", lambda e: self._close_replace_popup())

        btn_rep_all = ctk.CTkButton(border, text="Substituir Tudo", width=100, height=28, command=self.replace_all)
        btn_rep_all.pack(side="left", padx=(0, 5), pady=5)

        # Posiciona logo abaixo do botão de menu
        x = self.btn_more.winfo_rootx() - 100
        y = self.btn_more.winfo_rooty() + self.btn_more.winfo_height() + 2
        self.replace_popup.geometry(f"+{x}+{y}")
        self.replace_entry.focus_set()

    def replace_all(self):
        if not hasattr(self, 'replace_entry'): return
        replace_text = self.replace_entry.get()
        query = self.find_entry.get()
        if not query or not self.matches: return

        # Substitui de trás para frente para não estragar os índices do Tkinter!
        self.editor._textbox.edit_separator()
        for pos, end_pos in reversed(self.matches):
            self.editor.delete(pos, end_pos)
            self.editor.insert(pos, replace_text)
        self.editor._textbox.edit_separator()

        self.app.log_line(f"Substituídos {len(self.matches)} itens.")

        self._close_replace_popup()
        self.update_matches()

    def _close_replace_popup(self):
        """Função utilitária para matar o popup e devolver o controle para a janela principal"""
        if self.replace_popup:
            self.replace_popup.destroy()
            self.replace_popup = None

        # Puxa o mouse ativamente de volta
        self.app.focus_force()
        self.find_entry.focus_set()