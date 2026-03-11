import tkinter as tk
import customtkinter as ctk
import re
from pathlib import Path

SNIPPETS = {
    "figure": "\\begin{figure}[h]\n\t\\centering\n\t\\includegraphics[width=0.8\\textwidth]{}\n\t\\caption{Titulo}\n\t\\label{fig:}\n\\end{figure}",
    "table": "\\begin{table}[h]\n\t\\centering\n\t\\begin{tabular}{|c|c|}\n\t\t\\hline\n\t\tA & B \\\\\n\t\t\\hline\n\t\\end{tabular}\n\t\\caption{Titulo}\n\t\\label{tab:}\n\\end{table}",
    "itemize": "\\begin{itemize}\n\t\\item \n\\end{itemize}",
    "enumerate": "\\begin{enumerate}\n\t\\item \n\\end{enumerate}",
    "equation": "\\begin{equation}\n\t\n\t\\label{eq:}\n\\end{equation}",
    "align": "\\begin{align}\n\t &= \n\\end{align}",
    "frame": "\\begin{frame}\n\t\\frametitle{Titulo}\n\t\n\\end{frame}"
}

LATEX_COMMANDS = [
    "\\documentclass{}", "\\begin{}", "\\end{}", "\\usepackage{}", "\\section{}",
    "\\subsection{}", "\\subsubsection{}", "\\chapter{}", "\\label{}", "\\ref{}", "\\cite{}",
    "\\includegraphics{}", "\\maketitle", "\\tableofcontents", "\\textbf{}", "\\textit{}"
]

FILE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.pdf', '.tex')
BIB_EXTENSIONS = ('.bib',)


class AutocompleteHandler:
    def __init__(self, app, editor):
        self.is_active = True
        self.app = app
        self.editor = editor
        self.autocomplete_window = None
        self.suggestions_listbox = None
        self.start_index = None
        self.suggestion_type = None

        self.editor.bind("<KeyRelease>", self._on_key_release, add="+")
        self.editor.bind("<Return>", self._select_suggestion, add="+")
        self.editor.bind("<Tab>", self._select_suggestion, add="+")
        self.editor.bind("<Up>", self._move_selection, add="+")
        self.editor.bind("<Down>", self._move_selection, add="+")
        self.editor.bind("<Escape>", self._hide_suggestions, add="+")

        # --- NOVAS BLINDAGENS DE UX ---
        # 1. Clicou no editor (em qualquer lugar)? Some na hora!
        self.editor.bind("<Button-1>", self._hide_suggestions, add="+")
        # 2. Saiu do editor (Alt+Tab, clicou na árvore, clicou fora)? Some na hora!
        self.editor.bind("<FocusOut>", self._on_focus_out, add="+")

    def _on_focus_out(self, event=None):
        # Um pequeno delay (50ms) garante que o Tkinter saiba exatamente para onde o mouse foi
        self.app.after(50, self._check_focus_and_hide)

    def _check_focus_and_hide(self):
        current_focus = self.app.focus_get()
        # Se o foco atual NÃO for a própria listinha de sugestões, mate a janela!
        if current_focus != self.suggestions_listbox:
            self._hide_suggestions()

    def _get_project_data(self):
        if not self.app.project_dir: return [], [], [], []
        labels, files, cite_labels, bib_files = [], [], [], []
        for p in self.app.project_dir.rglob('*'):
            if p.is_file():
                if p.suffix in ('.aux', '.log', '.out'): continue
                if p.suffix.lower() in FILE_EXTENSIONS: files.append(p.relative_to(self.app.project_dir).as_posix())
                if p.suffix.lower() in BIB_EXTENSIONS: bib_files.append(p.stem)
                if p.suffix.lower() == '.tex':
                    try:
                        content = p.read_text(encoding="utf-8", errors="ignore")
                        labels.extend(re.findall(r'\\label\s*\{(.*?)\}', content))
                    except:
                        pass

        for bib in bib_files:
            try:
                path = self.app.project_dir / f"{bib}.bib"
                if path.exists():
                    c = path.read_text(encoding="utf-8", errors="ignore")
                    cite_labels.extend(re.findall(r'@[a-zA-Z]+\s*\{\s*([^,\s]+)', c))
            except:
                pass

        return sorted(list(set(labels))), sorted(files), sorted(list(set(cite_labels))), sorted(bib_files)

    def _on_key_release(self, event):
        if not self.is_active: return
        # Retirei as setas 'Left' e 'Right' da lista de ignorados.
        # Se o usuário andar para o lado, o balão some!
        if event.keysym in ('Return', 'Tab', 'Escape', 'Up', 'Down'): return

        text_content = self.editor.get("1.0", "insert")
        cursor_pos = len(text_content)
        word_start = cursor_pos

        while word_start > 0 and (
                text_content[word_start - 1].isalnum() or text_content[word_start - 1] in "\\_{}:/.-"):
            word_start -= 1

        current_word = text_content[word_start:cursor_pos]
        suggestions = []
        self.suggestion_type = None
        self.start_index = f"1.0 + {word_start} chars"

        last_brace = text_content.rfind('{', 0, cursor_pos)
        last_newline = text_content.rfind('\n', 0, cursor_pos)

        if last_brace > last_newline and last_brace >= word_start - 1:
            prefix = text_content[:last_brace].strip()
            cmd_match = re.search(r'\\(\w+)(\[[^\]]*\])?$', prefix)
            if cmd_match:
                cmd = cmd_match.group(1)
                content_inside = text_content[last_brace + 1:cursor_pos]
                self.start_index = f"1.0 + {last_brace + 1} chars"
                labels, files, cites, bibs = self._get_project_data()

                if cmd in ['ref', 'eqref']:
                    suggestions = [x for x in labels if x.startswith(content_inside)]
                elif cmd in ['includegraphics', 'input']:
                    suggestions = [x for x in files if x.startswith(content_inside)]
                elif cmd == 'cite':
                    suggestions = [x for x in cites if x.startswith(content_inside)]
                elif cmd == 'bibliography':
                    suggestions = [x for x in bibs if x.startswith(content_inside)]
                self.suggestion_type = 'context'

        elif not self.suggestion_type and current_word and current_word in [k[:len(current_word)] for k in
                                                                            SNIPPETS.keys()]:
            suggestions = [k for k in SNIPPETS.keys() if k.startswith(current_word)]
            self.suggestion_type = 'snippet'

        elif not self.suggestion_type and current_word.startswith('\\'):
            suggestions = [cmd for cmd in LATEX_COMMANDS if cmd.startswith(current_word)]
            self.suggestion_type = 'command'

        if suggestions:
            self._show_suggestions_popup(suggestions)
        else:
            self._hide_suggestions()

    def _show_suggestions_popup(self, suggestions):
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_col = "#2b2b2b" if is_dark else "#f0f0f0"
        fg_col = "white" if is_dark else "black"
        sel_col = "#007acc" if is_dark else "#005a9e"

        if not self.autocomplete_window:
            self.autocomplete_window = tk.Toplevel(self.app)
            self.autocomplete_window.wm_overrideredirect(True)
            self.autocomplete_window.transient(self.app)

            self.suggestions_listbox = tk.Listbox(self.autocomplete_window, height=5, font=("Consolas", 11),
                                                  bg=bg_col, fg=fg_col, selectbackground=sel_col, highlightthickness=0)
            self.suggestions_listbox.pack(fill="both", expand=True)

            # Clicar na própria listinha executa a sugestão
            self.suggestions_listbox.bind("<Button-1>", self._select_suggestion)
        else:
            self.suggestions_listbox.config(bg=bg_col, fg=fg_col, selectbackground=sel_col)

        self.suggestions_listbox.delete(0, tk.END)
        for s in suggestions: self.suggestions_listbox.insert(tk.END, s)
        self.suggestions_listbox.selection_set(0)

        try:
            bbox = self.editor._textbox.bbox("insert")
            if bbox:
                x = self.editor._textbox.winfo_rootx() + bbox[0]
                y = self.editor._textbox.winfo_rooty() + bbox[1] + bbox[3] + 5
                self.autocomplete_window.geometry(f"+{x}+{y}")
                self.autocomplete_window.deiconify()
        except:
            self._hide_suggestions()

    def _hide_suggestions(self, event=None):
        if self.autocomplete_window:
            self.autocomplete_window.withdraw()

    def _select_suggestion(self, event=None):
        if not self.autocomplete_window or self.autocomplete_window.state() == "withdrawn": return
        sel = self.suggestions_listbox.curselection()
        if not sel: return
        text = self.suggestions_listbox.get(sel[0])

        self.editor.delete(self.start_index, "insert")

        if self.suggestion_type == 'snippet':
            self.editor.insert(self.start_index, SNIPPETS[text])
        else:
            self.editor.insert(self.start_index, text)
            if "{}" in text: self.editor.mark_set("insert", "insert -1 chars")

        self._hide_suggestions()
        return "break"

    def _move_selection(self, event):
        if not self.autocomplete_window or self.autocomplete_window.state() == "withdrawn": return
        cur = self.suggestions_listbox.curselection()
        if not cur: return
        idx = cur[0]

        if event.keysym == "Down":
            idx = min(idx + 1, self.suggestions_listbox.size() - 1)
        else:
            idx = max(idx - 1, 0)

        self.suggestions_listbox.selection_clear(0, tk.END)
        self.suggestions_listbox.selection_set(idx)
        self.suggestions_listbox.see(idx)
        return "break"