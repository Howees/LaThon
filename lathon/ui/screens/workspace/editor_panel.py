import tkinter as tk
import customtkinter as ctk
import re

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts
from lathon.ui.widgets.tooltip import ToolTip
from lathon.features.assistants.text_formatter import TextFormatter


class LaTeXEditor(ctk.CTkFrame):
    """
    Componente Visual: A área central de digitação do código LaTeX. Núcleo de edição de texto do LaThon.
    Gerencia as áreas de texto nativas, numeração de linhas acoplada (scroll proxy),
    sistema de marcadores (anotações de revisão do usuário) e o motor de Syntax Highlighting.
    """

    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app_instance

        # Linha 0: Toolbar de atalhos | Linha 1: Área Principal de Texto
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==========================================
        # 1. BARRA DE FERRAMENTAS DO EDITOR (TOOLBAR)
        # ==========================================
        self.toolbar = ctk.CTkFrame(self, height=38, fg_color=Colors.BG_PANEL, corner_radius=0)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")

        ctk.CTkFrame(self.toolbar, height=1, fg_color=Colors.BORDER).pack(side="bottom", fill="x")

        tools_container = ctk.CTkFrame(self.toolbar, fg_color="transparent", border_width=1, border_color=Colors.BORDER,
                                       corner_radius=6)
        tools_container.pack(side="top", fill="x", expand=True, padx=10, pady=5)

        btn_conf = {
            "width": 30, "height": 26, "fg_color": "transparent",
            "text_color": Colors.TEXT_NORMAL, "hover_color": Colors.BTN_HOVER
        }

        # Botões de Formatação Rápida
        self.btn_b = ctk.CTkButton(tools_container, text="B", font=Fonts.UI_BOLD,
                                   command=lambda: TextFormatter.apply_format(self, "bold"), **btn_conf)
        self.btn_b.pack(side="left", padx=(5, 2), pady=2)
        ToolTip(self.btn_b, "Negrito (Ctrl+B)")

        ctk.CTkFrame(tools_container, width=1, height=16, fg_color=Colors.BORDER).pack(side="left", padx=1)

        self.btn_i = ctk.CTkButton(tools_container, text="I", font=("Segoe UI", 12, "italic"),
                                   command=lambda: TextFormatter.apply_format(self, "italic"), **btn_conf)
        self.btn_i.pack(side="left", padx=2, pady=2)
        ToolTip(self.btn_i, "Itálico (Ctrl+I)")

        ctk.CTkFrame(tools_container, width=1, height=16, fg_color=Colors.BORDER).pack(side="left", padx=1)

        self.btn_u = ctk.CTkButton(tools_container, text="U", font=("Segoe UI", 12, "underline"),
                                   command=lambda: TextFormatter.apply_format(self, "underline"), **btn_conf)
        self.btn_u.pack(side="left", padx=2, pady=2)
        ToolTip(self.btn_u, "Sublinhado (Ctrl+U)")

        ctk.CTkFrame(tools_container, width=1, height=16, fg_color=Colors.BORDER).pack(side="left", padx=1)

        self.btn_comment = ctk.CTkButton(tools_container, text="%", font=Fonts.UI_BOLD,
                                         command=lambda: TextFormatter.toggle_comment(self), **btn_conf)
        self.btn_comment.pack(side="left", padx=2, pady=2)
        ToolTip(self.btn_comment, "Comentar (Ctrl+/)")

        # ==========================================
        # 2. ÁREA DE TEXTO E NUMERAÇÃO DE LINHAS
        # ==========================================

        # Textbox lateral passivo que exibe os números das linhas
        self.line_number_bar = ctk.CTkTextbox(self, width=45, font=Fonts.MONO, state="disabled",
                                              activate_scrollbars=False, fg_color=Colors.BG_SIDEBAR,
                                              text_color=Colors.TEXT_MUTED)
        self.line_number_bar.grid(row=1, column=0, sticky="nsw")
        self.line_number_bar._textbox.configure(spacing1=0, spacing2=0, spacing3=2)

        # Textbox principal de edição de código
        self.textbox = ctk.CTkTextbox(self, font=Fonts.MONO, wrap="word", undo=True, fg_color=Colors.BG_PANEL)
        self.textbox.grid(row=1, column=1, sticky="nsew")
        self.textbox._textbox.configure(spacing1=0, spacing2=0, spacing3=2, exportselection=False)
        self._textbox = self.textbox._textbox

        self.syntax_timer = None
        self.outline_timer = None
        self.spellcheck_timer = None

        # Gerenciamento de Anotações do Revisor (Markers)
        self.mark_comments = {}
        self.mark_counter = 0
        self.mark_tw = None

        # Hack de Scroll: Intercepta o scroll da janela principal para mover as linhas numéricas em sincronia
        self._original_scroll_cmd = self._textbox.cget("yscrollcommand")
        self._textbox.configure(yscrollcommand=self._on_scroll_proxy)

        # ==========================================
        # MAPEAMENTO DE EVENTOS E ATALHOS
        # ==========================================
        self.textbox.bind("<KeyRelease>", self._on_text_changed)
        self._textbox.bind("<Double-Button-1>", self._select_word_double_click)
        self.textbox.bind("<Control-z>", self.undo)
        self.textbox.bind("<Control-y>", self.redo)
        self.textbox.bind("<Control-Shift-Z>", self.redo)

        self.textbox.bind("<Control-t>", lambda e: self._override_shortcut(e, self.app._toggle_theme_shortcut))
        self.textbox.bind("<Control-b>",
                          lambda e: self._override_shortcut(e, lambda: TextFormatter.apply_format(self, "bold")))
        self.textbox.bind("<Control-i>",
                          lambda e: self._override_shortcut(e, lambda: TextFormatter.apply_format(self, "italic")))
        self.textbox.bind("<Control-u>",
                          lambda e: self._override_shortcut(e, lambda: TextFormatter.apply_format(self, "underline")))
        self.textbox.bind("<Control-e>", lambda e: self._override_shortcut(e, self.app._export_pdf_shortcut))
        self.textbox.bind("<Control-E>", lambda e: self._override_shortcut(e, self.app._export_zip_shortcut))
        self.textbox.bind("<Control-f>", lambda e: self._override_shortcut(e, self.app._find_shortcut))
        self.textbox.bind("<Control-s>", lambda e: self._override_shortcut(e, self.app._compile_shortcut))
        self.textbox.bind("<Control-slash>",
                          lambda e: self._override_shortcut(e, lambda: TextFormatter.toggle_comment(self)))

    def _override_shortcut(self, event, action):
        """Bloqueia a propagação de eventos padrão do Text widget e aciona métodos customizados."""
        action()
        return "break"

    # ==========================================
    # SISTEMA DE MARCAÇÕES (REVISOR)
    # ==========================================
    def add_marker(self, color, comment):
        """Cria uma tag colorida sobre o texto selecionado, armazenando um comentário do usuário."""
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
        """Renderiza uma Tooltip flutuante com o conteúdo da anotação ao passar o mouse."""
        comment = self.mark_comments.get(tag_name, "")
        if not comment: return

        if self.mark_tw: self._hide_mark_tooltip(None)

        x, y = self.winfo_rootx() + event.x + 15, self.winfo_rooty() + event.y + 15
        self.mark_tw = tk.Toplevel(self)
        self.mark_tw.wm_overrideredirect(True)
        self.mark_tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.mark_tw, text=comment, justify='left',
            background=Colors.MARKER_TOOLTIP_BG, foreground=Colors.MARKER_TOOLTIP_FG,
            relief='solid', borderwidth=1, font=Fonts.UI
        ).pack(ipadx=6, ipady=3)

    def _hide_mark_tooltip(self, event):
        if self.mark_tw:
            self.mark_tw.destroy()
            self.mark_tw = None

    def export_markers(self):
        """Gera um dicionário serializável das marcações para ser salvo no arquivo de configuração do projeto."""
        exported = []
        for tag_name, comment in self.mark_comments.items():
            ranges = self._textbox.tag_ranges(tag_name)
            if ranges:
                color = self._textbox.tag_cget(tag_name, "background")
                exported.append({
                    "tag": tag_name,
                    "start": str(ranges[0]),
                    "end": str(ranges[1]),
                    "color": color,
                    "comment": comment
                })
        return exported

    def import_markers(self, markers_list):
        """Lê os marcadores salvos e recria as tags de cor no editor ao abrir o documento."""
        self.mark_comments.clear()
        for tag in self._textbox.tag_names():
            if tag.startswith("user_mark_"):
                self._textbox.tag_delete(tag)

        max_counter = 0
        for m in markers_list:
            tag_name, start_idx, end_idx = m["tag"], m["start"], m["end"]
            color, comment = m["color"], m["comment"]

            try:
                num = int(tag_name.split("_")[-1])
                if num > max_counter: max_counter = num

                self.tag_configure(tag_name, background=color, foreground="black")
                self.tag_add(tag_name, start_idx, end_idx)
                self.mark_comments[tag_name] = comment
                self.tag_bind(tag_name, "<Enter>", lambda e, t=tag_name: self._show_mark_tooltip(e, t))
                self.tag_bind(tag_name, "<Leave>", self._hide_mark_tooltip)
            except Exception as e:
                pass
        self.mark_counter = max_counter

    # ==========================================
    # SISTEMA VISUAL (CORES E SYNTAX HIGHLIGHTING)
    # ==========================================
    def update_colors(self):
        """Aplica a paleta de cores (Claro/Escuro) às marcações visuais de sintaxe e busca do Textbox."""
        is_dark = ctk.get_appearance_mode() == "Dark"
        idx = 1 if is_dark else 0
        tb = self._textbox

        tb.tag_configure("command", foreground=Colors.SYNTAX_CMD[idx])
        tb.tag_configure("comment", foreground=Colors.SYNTAX_COMMENT[idx])
        tb.tag_configure("label", foreground=Colors.SYNTAX_LABEL[idx])
        tb.tag_configure("file_path", foreground=Colors.SYNTAX_FILE[idx])
        tb.tag_configure("misspell", foreground=Colors.SYNTAX_ERROR[idx], underline=True)
        tb.tag_configure("find_highlight_all", background=Colors.HIGHLIGHT_ALL[idx], foreground="black")
        tb.tag_configure("find_highlight_current", background=Colors.HIGHLIGHT_CURRENT[idx], foreground="black")

        # Fundo avermelhado de alerta para identificação de erros capturados pelo parser do terminal
        bg_error = "#5c1b1b" if is_dark else "#ffcccc"
        tb.tag_configure("error_line", background=bg_error)

        # Fundo amarelado para identificação visual de 'warnings' do LaTeX (como Estouro de Margem)
        bg_warning = "#5c4d1b" if is_dark else "#fff2cc"
        tb.tag_configure("warning_line", background=bg_warning)

    def highlight_error_line(self, line_num):
        self.tag_add("error_line", f"{line_num}.0", f"{line_num}.0 lineend")
        self.see(f"{line_num}.0")

    def highlight_warning_line(self, line_num):
        self.tag_add("warning_line", f"{line_num}.0", f"{line_num}.0 lineend")

    def clear_error_lines(self):
        """Limpa as marcações provisórias de erro geradas na última compilação."""
        self.tag_remove("error_line", "1.0", "end")
        self.tag_remove("warning_line", "1.0", "end")

    def apply_syntax_highlighting(self):
        """
        Gera as colorações de código mapeando o texto via Expressão Regular (Regex).
        Destaques: Comandos, Comentários, Labels e Caminhos de Arquivo.
        """
        for tag in ["command", "comment", "label", "file_path"]:
            self.tag_remove(tag, "1.0", "end")

        try:
            text_content = self.get("1.0", "end-1c")
        except:
            return

        # Comandos iniciados por contrabarra (ex: \textbf)
        for match in re.finditer(r'(\\[a-zA-Z]+)', text_content):
            self.tag_add("command", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        # Ambientes e referências vinculativas (ex: \ref{fig1})
        for match in re.finditer(r'\\(ref|cite|label|eqref|nameref|autoref)\s*\{(.*?)\}', text_content):
            self.tag_add("label", f"1.0 + {match.start(2)} chars", f"1.0 + {match.end(2)} chars")

        # Caminhos de inserção de arquivos ou recursos (ex: \includegraphics{caminho})
        for match in re.finditer(r'\\includegraphics(\[[^\]]*\])?\s*\{(.*?)\}', text_content):
            self.tag_add("file_path", f"1.0 + {match.start(2)} chars", f"1.0 + {match.end(2)} chars")

        # Comentários LaTeX: do '%' até o final da linha
        for match in re.finditer(r'(%.*?)$', text_content, re.MULTILINE):
            self.tag_add("comment", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    # ==========================================
    # UTILITÁRIOS E SINCRONIZAÇÃO DE COMPONENTES
    # ==========================================
    # Delegação direta dos métodos padrão de text widget para uso externo limpo
    def get(self, *args, **kwargs):
        return self.textbox.get(*args, **kwargs)

    def insert(self, *args, **kwargs):
        self.textbox.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.textbox.delete(*args, **kwargs)

    def see(self, *args, **kwargs):
        self.textbox.see(*args, **kwargs)

    def focus_set(self):
        self.textbox.focus_set()

    def index(self, *args, **kwargs):
        return self.textbox.index(*args, **kwargs)

    def compare(self, *args, **kwargs):
        return self._textbox.compare(*args, **kwargs)

    def bind(self, *args, **kwargs):
        self.textbox.bind(*args, **kwargs)

    def tag_add(self, *args, **kwargs):
        self._textbox.tag_add(*args, **kwargs)

    def tag_remove(self, *args, **kwargs):
        self._textbox.tag_remove(*args, **kwargs)

    def tag_ranges(self, *args, **kwargs):
        return self._textbox.tag_ranges(*args, **kwargs)

    def tag_names(self, *args, **kwargs):
        return self._textbox.tag_names(*args, **kwargs)

    def tag_configure(self, *args, **kwargs):
        self._textbox.tag_configure(*args, **kwargs)

    def tag_delete(self, *args, **kwargs):
        self._textbox.tag_delete(*args, **kwargs)

    def tag_bind(self, *args, **kwargs):
        self._textbox.tag_bind(*args, **kwargs)

    def mark_set(self, *args, **kwargs):
        self._textbox.mark_set(*args, **kwargs)

    def tag_cget(self, *args, **kwargs):
        return self._textbox.tag_cget(*args, **kwargs)

    def configure_font(self, font_tuple):
        self.textbox.configure(font=font_tuple)
        self.line_number_bar.configure(font=font_tuple)

    def undo(self, event=None):
        try:
            self._textbox.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def redo(self, event=None):
        try:
            self._textbox.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def clear_undo_history(self):
        try:
            self._textbox.edit_reset()
        except:
            pass

    def _on_scroll_proxy(self, *args):
        """Intercepta as roladas do editor e repassa proporcionalmente para a barra de números laterais."""
        if self._original_scroll_cmd:
            try:
                self.tk.call(self._original_scroll_cmd, *args)
            except tk.TclError:
                pass
        self.line_number_bar._textbox.yview_moveto(args[0])

    def update_line_numbers(self):
        """Recalcula o número total de quebras de linha ('\n') e redesenha a barra esquerda."""
        line_count = self.get("1.0", "end-1c").count("\n") + 1
        line_numbers_string = "\n".join(str(i) for i in range(1, line_count + 1))

        self.line_number_bar.configure(state="normal")
        self.line_number_bar.delete("1.0", "end")
        self.line_number_bar.insert("1.0", line_numbers_string)
        self.line_number_bar.configure(state="disabled")

        self.line_number_bar._textbox.yview_moveto(self._textbox.yview()[0])

    def _on_text_changed(self, event=None):
        """Gatilho principal ao digitar: Atualiza números, limpa erros e dispara timers de repintura visual."""
        self.update_line_numbers()

        # O evento virtual DEVE ser disparado no widget tk.Text interno do CustomTkinter
        self._textbox.event_generate("<<EditorTextChanged>>")

        if self.syntax_timer: self.after_cancel(self.syntax_timer)
        self.syntax_timer = self.after(800, self.apply_syntax_highlighting)

    def _select_word_double_click(self, event):
        """
        Sobrescreve a seleção nativa de palavra do Tkinter.
        Como o Tkinter para de selecionar palavras ao encontrar hífens ou contrabarras,
        usamos regex para garantir a seleção limpa e integral de comandos LaTeX.
        """
        try:
            cursor_index = self._textbox.index(f"@{event.x},{event.y}")
            text_content = self.get("1.0", "end-1c")
            flat_index = self._textbox.count("1.0", cursor_index, "chars")[0]
            match = None

            for m in re.finditer(r'(\w+)', text_content):
                if m.start() <= flat_index < m.end() or (
                        flat_index == m.end() and m.start() <= flat_index - 1 < m.end()):
                    match = m
                    break

            self.tag_remove("sel", "1.0", "end")

            if match:
                self.tag_add("sel", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
                return "break"
        except:
            pass
        return None