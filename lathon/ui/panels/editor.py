import tkinter as tk
import customtkinter as ctk
import re

class LaTeXEditor(ctk.CTkFrame):
    """Componente Visual: A área central de digitação do código LaTeX."""

    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app_instance

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.line_number_bar = ctk.CTkTextbox(self, width=45, font=("Consolas", 12), state="disabled", activate_scrollbars=False, fg_color=("gray92", "#252526"), text_color="gray50")
        self.line_number_bar.grid(row=0, column=0, sticky="nsw")
        self.line_number_bar._textbox.configure(spacing1=0, spacing2=0, spacing3=2)

        self.textbox = ctk.CTkTextbox(self, font=("Consolas", 12), wrap="word", undo=True, fg_color=("white", "#1a1a1a"))
        self.textbox.grid(row=0, column=1, sticky="nsew")
        self.textbox._textbox.configure(spacing1=0, spacing2=0, spacing3=2, exportselection=False)
        self._textbox = self.textbox._textbox

        self.syntax_timer = None
        self.outline_timer = None
        self.spellcheck_timer = None

        # --- VARIÁVEIS DO MARCA-TEXTO ---
        self.mark_comments = {}
        self.mark_counter = 0
        self.mark_tw = None

        self._original_scroll_cmd = self._textbox.cget("yscrollcommand")
        self._textbox.configure(yscrollcommand=self._on_scroll_proxy)

        self.textbox.bind("<KeyRelease>", self._on_text_changed)
        self._textbox.bind("<Double-Button-1>", self._select_word_double_click)
        self.textbox.bind("<Control-z>", self.undo)
        self.textbox.bind("<Control-y>", self.redo)
        self.textbox.bind("<Control-Shift-Z>", self.redo)

    # ==========================================
    # LÓGICA DO MARCA-TEXTO (Highlighter)
    # ==========================================
    def add_marker(self, color, comment):
        try:
            sel_start, sel_end = self.tag_ranges("sel")
        except ValueError:
            return

        self.mark_counter += 1
        tag_name = f"user_mark_{self.mark_counter}"

        self.tag_configure(tag_name, background=color, foreground="black")
        self.tag_add(tag_name, sel_start, sel_end)
        self.tag_remove("sel", "1.0", "end")

        self.mark_comments[tag_name] = comment
        self.tag_bind(tag_name, "<Enter>", lambda e, t=tag_name: self._show_mark_tooltip(e, t))
        self.tag_bind(tag_name, "<Leave>", self._hide_mark_tooltip)

    def remove_marker(self, tag_name):
        self.tag_delete(tag_name)
        if tag_name in self.mark_comments:
            del self.mark_comments[tag_name]
        self._hide_mark_tooltip(None)

    def _show_mark_tooltip(self, event, tag_name):
        comment = self.mark_comments.get(tag_name, "")
        if not comment: return
        if self.mark_tw: self._hide_mark_tooltip(None)

        x, y = self.winfo_rootx() + event.x + 15, self.winfo_rooty() + event.y + 15
        self.mark_tw = tk.Toplevel(self)
        self.mark_tw.wm_overrideredirect(True)
        self.mark_tw.wm_geometry(f"+{x}+{y}")
        tk.Label(self.mark_tw, text=comment, justify='left', background="#ffffe0", foreground="black", relief='solid', borderwidth=1, font=("Segoe UI", 10)).pack(ipadx=6, ipady=3)

    def _hide_mark_tooltip(self, event):
        if self.mark_tw:
            self.mark_tw.destroy()
            self.mark_tw = None

    # ==========================================
    # SINTAXE E CORES BASE (Apenas LaTeX nativo)
    # ==========================================
    def update_colors(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        tb = self._textbox

        tb.tag_configure("command", foreground="#569cd6" if is_dark else "#0000ff")
        tb.tag_configure("comment", foreground="#6a9955" if is_dark else "#008000")
        tb.tag_configure("label", foreground="#ce9178" if is_dark else "#a31515")
        tb.tag_configure("file_path", foreground="#dcdcaa" if is_dark else "#795e26")

        tb.tag_configure("misspell", foreground="#ff6b6b" if is_dark else "#d32f2f", underline=True)
        tb.tag_configure("find_highlight_all", background="#5c5c42" if is_dark else "#f2f2a4", foreground="black")
        tb.tag_configure("find_highlight_current", background="#ffaa00" if is_dark else "#ffcc00", foreground="black")

    def apply_syntax_highlighting(self):
        for tag in ["command", "comment", "label", "file_path"]:
            self.tag_remove(tag, "1.0", "end")

        try:
            text_content = self.get("1.0", "end-1c")
        except:
            return

        for match in re.finditer(r'(\\[a-zA-Z]+)', text_content):
            self.tag_add("command", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
        for match in re.finditer(r'\\(ref|cite|label|eqref|nameref|autoref)\s*\{(.*?)\}', text_content):
            self.tag_add("label", f"1.0 + {match.start(2)} chars", f"1.0 + {match.end(2)} chars")
        for match in re.finditer(r'\\includegraphics(\[[^\]]*\])?\s*\{(.*?)\}', text_content):
            self.tag_add("file_path", f"1.0 + {match.start(2)} chars", f"1.0 + {match.end(2)} chars")
        for match in re.finditer(r'(%.*?)$', text_content, re.MULTILINE):
            self.tag_add("comment", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    # ==========================================
    # MÉTODOS DE COMPATIBILIDADE E EVENTOS
    # ==========================================
    def get(self, *args, **kwargs): return self.textbox.get(*args, **kwargs)
    def insert(self, *args, **kwargs): self.textbox.insert(*args, **kwargs)
    def delete(self, *args, **kwargs): self.textbox.delete(*args, **kwargs)
    def see(self, *args, **kwargs): self.textbox.see(*args, **kwargs)
    def focus_set(self): self.textbox.focus_set()
    def index(self, *args, **kwargs): return self.textbox.index(*args, **kwargs)
    def compare(self, *args, **kwargs): return self._textbox.compare(*args, **kwargs)
    def bind(self, *args, **kwargs): self.textbox.bind(*args, **kwargs)
    def tag_add(self, *args, **kwargs): self._textbox.tag_add(*args, **kwargs)
    def tag_remove(self, *args, **kwargs): self._textbox.tag_remove(*args, **kwargs)
    def tag_ranges(self, *args, **kwargs): return self._textbox.tag_ranges(*args, **kwargs)
    def tag_names(self, *args, **kwargs): return self._textbox.tag_names(*args, **kwargs)
    def tag_configure(self, *args, **kwargs): self._textbox.tag_configure(*args, **kwargs)
    def tag_delete(self, *args, **kwargs): self._textbox.tag_delete(*args, **kwargs)
    def tag_bind(self, *args, **kwargs): self._textbox.tag_bind(*args, **kwargs)
    def mark_set(self, *args, **kwargs): self._textbox.mark_set(*args, **kwargs)
    def tag_cget(self, *args, **kwargs): return self._textbox.tag_cget(*args, **kwargs)

    def configure_font(self, font_tuple):
        self.textbox.configure(font=font_tuple)
        self.line_number_bar.configure(font=font_tuple)

    def undo(self, event=None):
        try: self._textbox.edit_undo()
        except tk.TclError: pass
        return "break"

    def redo(self, event=None):
        try: self._textbox.edit_redo()
        except tk.TclError: pass
        return "break"

    def _on_scroll_proxy(self, *args):
        if self._original_scroll_cmd:
            try: self.tk.call(self._original_scroll_cmd, *args)
            except tk.TclError: pass
        self.line_number_bar._textbox.yview_moveto(args[0])

    def update_line_numbers(self):
        line_count = self.get("1.0", "end-1c").count("\n") + 1
        line_numbers_string = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_number_bar.configure(state="normal")
        self.line_number_bar.delete("1.0", "end")
        self.line_number_bar.insert("1.0", line_numbers_string)
        self.line_number_bar.configure(state="disabled")
        self.line_number_bar._textbox.yview_moveto(self._textbox.yview()[0])

    def _on_text_changed(self, event=None):
        self.update_line_numbers()
        self.event_generate("<<EditorTextChanged>>")
        if self.syntax_timer: self.after_cancel(self.syntax_timer)
        self.syntax_timer = self.after(800, self.apply_syntax_highlighting)

    def _select_word_double_click(self, event):
        try:
            cursor_index = self._textbox.index(f"@{event.x},{event.y}")
            text_content = self.get("1.0", "end-1c")
            flat_index = self._textbox.count("1.0", cursor_index, "chars")[0]

            match = None
            for m in re.finditer(r'(\w+)', text_content):
                if m.start() <= flat_index < m.end() or (flat_index == m.end() and m.start() <= flat_index - 1 < m.end()):
                    match = m; break

            self.tag_remove("sel", "1.0", "end")
            if match:
                self.tag_add("sel", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
                return "break"
        except: pass
        return None