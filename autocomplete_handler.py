import tkinter as tk
import customtkinter as ctk
import re
from pathlib import Path

# --- SNIPPETS (CODIGOS PRONTOS) ---
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
    def __init__(self, app: 'MiniOverleaf', editor: ctk.CTkTextbox):
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

        # Leitura basica de bib (pode ser melhorado)
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
        if event.keysym in ('Return', 'Tab', 'Escape', 'Up', 'Down', 'Left', 'Right'): return

        text_content = self.editor.get("1.0", "insert")
        cursor_pos = len(text_content)

        # Detecta palavra atual
        word_start = cursor_pos
        while word_start > 0 and (text_content[word_start - 1].isalnum() or text_content[word_start - 1] in "\\_{}:"):
            word_start -= 1

        current_word = text_content[word_start:cursor_pos]

        suggestions = []
        self.suggestion_type = None
        self.start_index = f"1.0 + {word_start} chars"

        # 1. Snippets (Sem barra)
        if current_word and current_word in [k[:len(current_word)] for k in SNIPPETS.keys()]:
            suggestions = [k for k in SNIPPETS.keys() if k.startswith(current_word)]
            self.suggestion_type = 'snippet'

        # 2. Comandos
        elif current_word.startswith('\\'):
            suggestions = [cmd for cmd in LATEX_COMMANDS if cmd.startswith(current_word)]
            self.suggestion_type = 'command'

        # 3. Contexto (Dentro de chaves)
        else:
            last_brace = text_content.rfind('{', 0, cursor_pos)
            if last_brace > -1 and last_brace >= word_start - 1:
                # Estamos dentro de chaves, verifique o comando anterior
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

        if suggestions:
            self._show_suggestions_popup(suggestions)
        else:
            self._hide_suggestions()

    def _show_suggestions_popup(self, suggestions):
        if not self.autocomplete_window:
            self.autocomplete_window = tk.Toplevel(self.app)
            self.autocomplete_window.wm_overrideredirect(True)
            self.autocomplete_window.attributes("-topmost", True)
            self.suggestions_listbox = tk.Listbox(self.autocomplete_window, height=5, font=("Consolas", 11),
                                                  bg="#2b2b2b", fg="white", selectbackground="#007acc",
                                                  highlightthickness=0)
            self.suggestions_listbox.pack(fill="both", expand=True)
            self.suggestions_listbox.bind("<Button-1>", self._select_suggestion)

        self.suggestions_listbox.delete(0, tk.END)
        for s in suggestions: self.suggestions_listbox.insert(tk.END, s)
        self.suggestions_listbox.selection_set(0)

        try:
            bbox = self.editor._textbox.bbox("insert")
            if bbox:
                x = self.app.winfo_rootx() + bbox[0]
                y = self.app.winfo_rooty() + bbox[1] + bbox[3] + 5
                self.autocomplete_window.geometry(f"+{x}+{y}")
                self.autocomplete_window.deiconify()
        except:
            self._hide_suggestions()

    def _hide_suggestions(self, event=None):
        if self.autocomplete_window: self.autocomplete_window.withdraw()

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
            if "{}" in text:
                # Move cursor para dentro das chaves
                self.editor.mark_set("insert", f"insert -1 chars")

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