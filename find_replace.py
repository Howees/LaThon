import re
import tkinter as tk
import customtkinter as ctk


class FindReplaceHandler:
    """
    Gerencia toda a lógica e estado da funcionalidade
    Localizar/Substituir.
    """

    def __init__(self, app: 'MiniOverleaf', editor: ctk.CTkTextbox, find_frame: ctk.CTkFrame,
                 find_entry: ctk.CTkEntry, replace_entry: ctk.CTkEntry):
        self.app = app
        self.editor = editor
        self.find_frame = find_frame
        self.find_entry = find_entry
        self.replace_entry = replace_entry
        self.last_find_pos = "1.0"

        # Configura as tags de destaque (Amarelo/Laranja)
        self.editor._textbox.tag_configure("find_highlight", background="#ffcc00", foreground="black")

    def show_dialog(self, event=None):
        """
        Mostra a barra de Localizar/Substituir.
        USANDO .place() PARA NÃO DEFORMAR O LAYOUT (Floating Overlay)
        """
        # Posiciona no canto superior direito do editor, flutuando sobre o texto
        # relx=0.98: Canto direito com pequena margem
        # rely=0.01: Topo com pequena margem
        # anchor="ne": Âncora no Norte-Leste (Canto superior direito da barra)
        self.find_frame.place(relx=0.98, rely=0.01, anchor="ne")

        self.find_frame.lift()  # Garante que fique na frente de tudo
        self.find_entry.focus_set()
        self.find_entry.select_range(0, 'end')
        self.last_find_pos = "1.0"
        return "break"

    def hide_dialog(self, event=None):
        """Esconde a barra."""
        self.editor.tag_remove("find_highlight", "1.0", "end")
        self.find_frame.place_forget()  # Remove do lugar sem destruir
        self.editor.focus_set()
        return "break"

    def find_next(self, event=None):
        """Encontra a próxima ocorrência."""
        self.editor.tag_remove("find_highlight", "1.0", "end")
        query = self.find_entry.get()
        if not query:
            return "break"

        # Busca a partir da última posição
        start_pos = self.editor._textbox.search(query, self.last_find_pos, stopindex="end", nocase=True)

        if start_pos:
            end_pos = f"{start_pos} + {len(query)} chars"
            self.editor.tag_add("find_highlight", start_pos, end_pos)
            self.editor.see(start_pos)
            self.last_find_pos = end_pos
        else:
            # Se não achar, tenta do início (Loop)
            self.last_find_pos = "1.0"
            start_pos = self.editor._textbox.search(query, self.last_find_pos, stopindex="end", nocase=True)
            if start_pos:
                end_pos = f"{start_pos} + {len(query)} chars"
                self.editor.tag_add("find_highlight", start_pos, end_pos)
                self.editor.see(start_pos)
                self.last_find_pos = end_pos
            else:
                self.app.log_line(f"Busca encerrada: '{query}' não encontrado.")

        return "break"

    def replace_one(self, event=None):
        """Substitui a seleção atual."""
        query = self.find_entry.get()
        replace_text = self.replace_entry.get()
        ranges = self.editor.tag_ranges("find_highlight")

        if ranges:
            start_pos, end_pos = ranges
            self.editor.delete(start_pos, end_pos)
            self.editor.insert(start_pos, replace_text)
            self.last_find_pos = f"{start_pos} + {len(replace_text)} chars"
            self.find_next()
        else:
            self.find_next()
        return "break"

    def replace_all(self, event=None):
        """Substitui tudo de uma vez com suporte a Undo único."""
        query = self.find_entry.get()
        replace_text = self.replace_entry.get()

        if not query: return "break"

        self.editor.tag_remove("find_highlight", "1.0", "end")
        count = 0
        start_pos = "1.0"

        self.editor._textbox.edit_separator()  # Inicia bloco de Undo
        original_cursor = self.editor.index("insert")

        while True:
            pos = self.editor._textbox.search(query, start_pos, stopindex="end", nocase=True, forwards=True)
            if not pos: break

            count += 1
            end_pos = f"{pos}+{len(query)}c"
            self.editor.delete(pos, end_pos)
            self.editor.insert(pos, replace_text)
            start_pos = f"{pos}+{len(replace_text)}c"

        self.editor._textbox.edit_separator()  # Finaliza bloco de Undo

        if count > 0:
            self.app.log_line(f"Substituídos {count} itens.")
            self.app._update_line_numbers()
            self.app._apply_syntax_highlighting()
            try:
                self.editor.mark_set("insert", original_cursor)
            except:
                pass
        else:
            self.app.log_line(f"Nada encontrado para '{query}'.")

        return "break"