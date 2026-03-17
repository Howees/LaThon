import queue
import re
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import zipfile
import subprocess

# --- Cérebro e Ferramentas Base ---
from lathon.core.config import ConfigManager
from lathon.core.compiler import find_latex_compiler, CompilerThread
from lathon.core.exporter import ProjectExporter

# --- Componentes Visuais (UI Panels & Widgets) ---
from lathon.ui.panels.welcome import WelcomeScreen
from lathon.ui.panels.editor import LaTeXEditor
from lathon.ui.panels.file import FilePanel
from lathon.ui.panels.preview import PreviewPanel
from lathon.ui.widgets.tooltip import ToolTip

# --- Funcionalidades Inserção e Preferências ---
from lathon.features.preferences.layout_config import LayoutConfigDialog
from lathon.features.preferences.font_config import FontConfigDialog
from lathon.features.preferences.spell_config import SpellConfigDialog
from lathon.features.insert.insert_manager import InsertManager

# --- Opções e Assistentes de Edição ---
from lathon.features.assistants.find_replace import FindReplaceHandler
from lathon.features.assistants.chapter_highlighter import ChapterHighlighter
from lathon.features.assistants.spell_checker import SpellCheckHandler
from lathon.features.assistants.autocomplete import AutocompleteHandler
from lathon.features.assistants.context_menu import ContextMenuManager
from lathon.features.assistants.text_formatter import TextFormatter
from lathon.features.assistants.options_manager import OptionsManager

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts, Icons, create_lathon_logo, resource_path

class MiniOverleaf(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LaThon LaTeX Editor")

        Icons.set_window_icon(self)

        self.geometry("1200x800")

        self.config = ConfigManager()
        self.latex_compiler = find_latex_compiler()
        self.queue = queue.Queue()
        self.project_dir = None
        self.active_file = None
        self.download_notification_window = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.welcome_screen = WelcomeScreen(self, self)
        self.welcome_screen.grid(row=0, column=0, sticky="nsew")

        self.scroll_conf = {"scrollbar_button_color": Colors.SCROLL_BTN, "scrollbar_button_hover_color": Colors.SCROLL_HOVER}

        self._build_ui()
        self._bind_events()

        layout_cfg = self.config.get_layout()
        self.apply_font_config(layout_cfg.get("font_family"), layout_cfg.get("font_size"))
        self.editor.update_colors()

        if not self.latex_compiler: messagebox.showerror("Aviso", "Compilador LaTeX não encontrado.")
        self.process_queue()

    def _build_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=Colors.BG_MAIN, corner_radius=0)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # ==========================================
        # 1. BARRA SUPERIOR E MENUS
        # ==========================================
        top_frame = ctk.CTkFrame(self.main_frame, height=35, corner_radius=0, fg_color=Colors.BG_TOPBAR, border_width=0)
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        top_frame.grid_propagate(False)
        ctk.CTkFrame(top_frame, height=1, fg_color=Colors.BORDER).pack(side="bottom", fill="x")

        top_inner = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_inner.pack(fill="both", expand=True, padx=5)

        create_lathon_logo(top_inner, font_size=16).pack(side="left", padx=5, pady=4)

        menu_btn_conf = {"height": 26, "fg_color": "transparent", "text_color": Colors.BTN_TRANSPARENT_TEXT,
                         "hover_color": Colors.BTN_HOVER, "font": Fonts.UI}
        menu_bg = Colors.BG_MAIN[1]

        self.btn_file = ctk.CTkButton(top_inner, text=" Arquivo", image=Icons.get_ctk_image("folder.png"),
                                      command=lambda: self._popup_menu(self.menu_file, self.btn_file), **menu_btn_conf)
        self.btn_file.pack(side="left", padx=2)
        self.menu_file = tk.Menu(self, tearoff=0, bg=menu_bg, fg="white", activebackground=Colors.THON)
        self.menu_file.add_command(label=" Novo Projeto", image=Icons.get_treeview_icon("new.png"), compound="left",
                                   command=self._create_project_flow)
        self.menu_file.add_command(label=" Abrir Projeto", image=Icons.get_treeview_icon("open.png"), compound="left",
                                   command=self._open_project_flow)
        self.menu_file.add_separator()
        self.menu_file.add_command(label=" Salvar (Ctrl+S)", image=Icons.get_treeview_icon("save.png"), compound="left",
                                   command=self.compile_action)
        self.menu_file.add_separator()
        self.menu_file.add_command(label=" Limpar Temporários", image=Icons.get_treeview_icon("clean.png"),
                                   compound="left", command=self._clean_aux_files)
        self.menu_file.add_separator()
        self.menu_file.add_command(label=" Fechar Projeto", image=Icons.get_treeview_icon("close.png"), compound="left",
                                   command=self._close_project)

        self.btn_insert = ctk.CTkButton(top_inner, text=" Inserir", image=Icons.get_ctk_image("insert.png"),
                                        command=lambda: self._popup_menu(self.menu_insert, self.btn_insert),
                                        **menu_btn_conf)
        self.btn_insert.pack(side="left", padx=2)
        self.menu_insert = tk.Menu(self, tearoff=0, bg=menu_bg, fg="white", activebackground=Colors.THON)
        self.menu_insert.add_command(label=" Tabela Básica...", image=Icons.get_treeview_icon("table.png"),
                                     compound="left", command=lambda: self.insert_manager.open_table_wizard())
        self.menu_insert.add_command(label=" Figura Simples...", image=Icons.get_treeview_icon("figure.png"),
                                     compound="left", command=lambda: self.insert_manager.open_figure_wizard())
        self.menu_insert.add_command(label=" Tabela de Figuras...", image=Icons.get_treeview_icon("table_fig.png"),
                                     compound="left", command=lambda: self.insert_manager.open_image_table_wizard())
        self.menu_insert.add_separator()
        self.menu_insert.add_command(label=" Fórmula Matemática...", image=Icons.get_treeview_icon("math.png"),
                                     compound="left", command=lambda: self.insert_manager.open_formula_wizard())

        self.btn_options = ctk.CTkButton(top_inner, text=" Opções", image=Icons.get_ctk_image("options.png"),
                                         command=lambda: self._popup_menu(self.menu_options, self.btn_options),
                                         **menu_btn_conf)
        self.btn_options.pack(side="left", padx=2)
        self.menu_options = tk.Menu(self, tearoff=0, bg=menu_bg, fg="white", activebackground=Colors.THON)

        self.var_chap = tk.BooleanVar(value=False)
        self.var_auto = tk.BooleanVar(value=True)
        self.var_spell = tk.BooleanVar(value=True)

        self.menu_options.add_command(label=" Localizar (Ctrl+F)", image=Icons.get_treeview_icon("search.png"),
                                      compound="left", command=lambda: self.options_manager.show_find_dialog())
        self.menu_options.add_command(label=" Ver Lista de Marcações...", image=Icons.get_treeview_icon("list.png"),
                                      compound="left", command=lambda: self.options_manager.open_markers_list())
        self.menu_options.add_separator()

        # Checkbuttons mantidos sem ícone customizado para não quebrar o "V" de seleção nativo
        self.menu_options.add_checkbutton(label="Evidenciar Capítulos (Ctrl+M)", variable=self.var_chap, selectcolor=Colors.THON,
                                          command=lambda: self.options_manager.set_chapter_highlight(self.var_chap.get()))
        self.menu_options.add_checkbutton(label="Autocompletar LaTeX", variable=self.var_auto, selectcolor=Colors.THON,
                                          command=lambda: self.options_manager.set_autocomplete(self.var_auto.get()))
        self.menu_options.add_checkbutton(label="Corretor Ortográfico", variable=self.var_spell, selectcolor=Colors.THON,
                                          command=lambda: self.options_manager.set_spellcheck(self.var_spell.get()))

        self.menu_options.add_separator()
        self.menu_options.add_command(label=" Alternar Tema (Ctrl+T)", image=Icons.get_treeview_icon("theme.png"),
                                      compound="left", command=lambda: self.options_manager.toggle_theme())

        self.btn_export = ctk.CTkButton(top_inner, text=" Exportar", image=Icons.get_ctk_image("export.png"),
                                        command=lambda: self._popup_menu(self.menu_export, self.btn_export),
                                        **menu_btn_conf)
        self.btn_export.pack(side="left", padx=2)
        self.menu_export = tk.Menu(self, tearoff=0, bg=menu_bg, fg="white", activebackground=Colors.THON)
        self.menu_export.add_command(label=" PDF (Ctrl+E)", image=Icons.get_treeview_icon("pdf.png"), compound="left",
                                     command=lambda: ProjectExporter.export_pdf(self.project_dir, self.active_file))
        self.menu_export.add_command(label=" ZIP (Ctrl+Shift+E)", image=Icons.get_treeview_icon("zip.png"),
                                     compound="left", command=lambda: ProjectExporter.export_zip(self.project_dir))

        self.btn_config = ctk.CTkButton(top_inner, text=" Config", image=Icons.get_ctk_image("config.png"),
                                        command=lambda: self._popup_menu(self.menu_config, self.btn_config),
                                        **menu_btn_conf)
        self.btn_config.pack(side="left", padx=2)
        self.menu_config = tk.Menu(self, tearoff=0, bg=menu_bg, fg="white", activebackground=Colors.THON)
        self.menu_config.add_command(label=" Corretor Ortográfico...", image=Icons.get_treeview_icon("spell.png"),
                                     compound="left", command=lambda: SpellConfigDialog(self, self.spell_checker))
        self.menu_config.add_separator()
        self.menu_config.add_command(label=" Fonte do Editor...", image=Icons.get_treeview_icon("font.png"),
                                     compound="left", command=lambda: FontConfigDialog(self))
        self.menu_config.add_separator()
        self.menu_config.add_command(label=" Configuração de Tela...", image=Icons.get_treeview_icon("layout.png"),
                                     compound="left", command=lambda: LayoutConfigDialog(self))

        format_frame = ctk.CTkFrame(top_inner, fg_color="transparent", border_width=1, border_color=Colors.BORDER, corner_radius=6)
        format_frame.pack(side="left", padx=15, pady=4)
        format_conf = {"width": 30, "height": 24, "fg_color": "transparent", "text_color": Colors.BTN_TRANSPARENT_TEXT, "hover_color": Colors.BTN_HOVER}

        self.btn_b = ctk.CTkButton(format_frame, text="B", font=Fonts.UI_BOLD, command=self._format_bold_shortcut, **format_conf)
        self.btn_b.pack(side="left", padx=2, pady=2)
        ToolTip(self.btn_b, "Negrito (Ctrl+B)")
        ctk.CTkFrame(format_frame, width=1, height=18, fg_color=Colors.BORDER).pack(side="left", padx=2)

        self.btn_i = ctk.CTkButton(format_frame, text="I", font=("Segoe UI", 12, "italic"), command=self._format_italic_shortcut, **format_conf)
        self.btn_i.pack(side="left", padx=2, pady=2)
        ToolTip(self.btn_i, "Itálico (Ctrl+I)")
        ctk.CTkFrame(format_frame, width=1, height=18, fg_color=Colors.BORDER).pack(side="left", padx=2)

        self.btn_u = ctk.CTkButton(format_frame, text="U", font=("Segoe UI", 12, "underline"), command=self._format_underline_shortcut, **format_conf)
        self.btn_u.pack(side="left", padx=2, pady=2)
        ToolTip(self.btn_u, "Sublinhado (Ctrl+U)")

        self.compile_button = ctk.CTkButton(top_inner, text=" Compile (Ctrl+S)", image=Icons.get_ctk_image("compile.png"), height=24,
                                            command=self.compile_action, fg_color=Colors.BTN_PRIMARY, hover_color=Colors.BTN_PRIMARY_HOVER, font=Fonts.UI_BOLD)
        self.compile_button.pack(side="right", padx=10)

        self.info_button = ctk.CTkButton(top_inner, text="", image=Icons.get_ctk_image("info.png"), width=26, height=24, fg_color="transparent", border_width=0,
                                         hover_color=Colors.BTN_HOVER, command=self._show_about_dialog)
        self.info_button.pack(side="right", padx=(0, 5))
        ToolTip(self.info_button, "Informações do LaThon")

        # ==========================================
        # 2. CONSTRUÇÃO DOS COMPONENTES (PAINÉIS)
        # ==========================================
        layout_cfg = self.config.get_layout()
        self.apply_layout_weights(layout_cfg["left"], layout_cfg["center"], layout_cfg["pdf"])

        self.file_panel = FilePanel(self.main_frame, self)
        self.file_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 2))
        self.file_panel.style_treeview()

        self.center_frame = ctk.CTkFrame(self.main_frame, fg_color=Colors.BG_PANEL, corner_radius=0)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 2))
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(3, weight=0, minsize=100)

        self.editor_area_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.editor_area_frame.grid(row=0, column=0, sticky="nsew")
        self.editor_area_frame.grid_rowconfigure(0, weight=1)
        self.editor_area_frame.grid_columnconfigure(0, weight=1)

        self.editor = LaTeXEditor(self.editor_area_frame, self)
        self.editor.grid(row=0, column=0, sticky="nsew")

        self.image_viewer_container = ctk.CTkScrollableFrame(self.center_frame, label_text="", fg_color="transparent", **self.scroll_conf)
        self.image_viewer_label = ctk.CTkLabel(self.image_viewer_container, text="")
        self.image_viewer_label.pack(expand=True, padx=5, pady=5)

        self.find_frame = ctk.CTkFrame(self.center_frame, fg_color=Colors.BG_MAIN, corner_radius=6, border_width=1, border_color=Colors.BORDER)

        log_header = ctk.CTkFrame(self.center_frame, height=20, fg_color=Colors.BG_SIDEBAR, corner_radius=0)
        log_header.grid(row=2, column=0, sticky="ew")
        ctk.CTkLabel(log_header, text="TERMINAL / LOG", font=Fonts.LOG_BOLD, text_color=Colors.TEXT_MUTED).pack(side="left", padx=5)
        self.log = ctk.CTkTextbox(self.center_frame, font=Fonts.LOG, state="disabled", fg_color=Colors.BG_PANEL)
        self.log.grid(row=3, column=0, sticky="nsew", pady=0)
        self.log.bind("<Button-1>", self._on_log_click)

        self.preview_panel = PreviewPanel(self.main_frame, self)
        self.preview_panel.grid(row=1, column=2, sticky="nsew")

        self._switch_center_view('editor')

        # ==========================================
        # 3. LIGANDO OS MOTORES (ASSISTENTES E FEATURES)
        # ==========================================
        self.chapter_highlighter = ChapterHighlighter(self.editor)
        self.insert_manager = InsertManager(self, self.editor)
        self.options_manager = OptionsManager(self)
        self.find_handler = FindReplaceHandler(self, self.editor, self.find_frame)
        self.autocomplete_handler = AutocompleteHandler(self, self.editor)
        self.spell_checker = SpellCheckHandler(self, self.editor)
        self.context_menu_manager = ContextMenuManager(self, self.editor, self.spell_checker)

    def _show_about_dialog(self):
        about_text = ("Lathon LaTeX Editor\nVersão 1.2\nCompilador Latex MiKTeX Portable\nDesenvolvido por: Murilo Campos\n\nEm caso de bugs ou sujestões, entre em contato...\nFique a vontade e aproveite o Lathon!!!")
        messagebox.showinfo("Sobre o Lathon", about_text)

    def _compile_shortcut(self, event=None):
        self.compile_action()

    def _export_pdf_shortcut(self, event=None):
        ProjectExporter.export_pdf(self.project_dir, self.active_file)

    def _export_zip_shortcut(self, event=None):
        ProjectExporter.export_zip(self.project_dir)

    def _format_bold_shortcut(self, event=None):
        TextFormatter.apply_format(self.editor, "bold")

    def _format_italic_shortcut(self, event=None):
        TextFormatter.apply_format(self.editor, "italic")

    def _format_underline_shortcut(self, event=None):
        TextFormatter.apply_format(self.editor, "underline")

    def _find_shortcut(self, event=None):
        self.options_manager.show_find_dialog()

    def _toggle_chapter_shortcut(self, event=None):
        new_val = not self.var_chap.get()
        self.var_chap.set(new_val)
        self.options_manager.set_chapter_highlight(new_val)

    def _toggle_theme_shortcut(self, event=None):
        self.options_manager.toggle_theme()

    def _bind_events(self):
        self.bind_all("<Control-s>", lambda e: self._handle_shortcut(self._compile_shortcut))
        self.bind_all("<Control-e>", lambda e: self._handle_shortcut(self._export_pdf_shortcut))
        self.bind_all("<Control-E>", lambda e: self._handle_shortcut(self._export_zip_shortcut))
        self.bind_all("<Control-b>", lambda e: self._handle_shortcut(self._format_bold_shortcut))
        self.bind_all("<Control-i>", lambda e: self._handle_shortcut(self._format_italic_shortcut))
        self.bind_all("<Control-u>", lambda e: self._handle_shortcut(self._format_underline_shortcut))
        self.bind_all("<Control-f>", lambda e: self._handle_shortcut(self._find_shortcut))
        self.bind_all("<Control-m>", lambda e: self._handle_shortcut(self._toggle_chapter_shortcut))
        self.bind_all("<Control-t>", lambda e: self._handle_shortcut(self._toggle_theme_shortcut))
        self.editor.bind("<KeyRelease>", self._schedule_outline_update, add="+")
        self._outline_timer = None

    def _handle_shortcut(self, func):
        func()
        return "break"

    def _schedule_outline_update(self, event=None):
        """Atualiza o painel de Estrutura 1 segundo após o usuário parar de digitar."""
        if getattr(self, '_outline_timer', None):
            self.after_cancel(self._outline_timer)
        self._outline_timer = self.after(1000, self.file_panel.update_file_outline)

    def apply_layout_weights(self, left_pct, center_pct, pdf_pct):
        self.main_frame.grid_columnconfigure(0, weight=left_pct, uniform="colunas")
        self.main_frame.grid_columnconfigure(1, weight=center_pct, uniform="colunas")
        self.main_frame.grid_columnconfigure(2, weight=pdf_pct, uniform="colunas")

        self.config.update_layout(left=left_pct, center=center_pct, pdf=pdf_pct)
        if self.project_dir: self.compile_action()

    def apply_font_config(self, family, size):
        self.editor.configure_font((family, size))
        self.config.update_layout(font_family=family, font_size=size)

    def _popup_menu(self, menu, btn):
        menu.tk_popup(btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())
        menu.grab_release()

    def _switch_center_view(self, view_mode: str):
        if view_mode == 'image':
            self.editor_area_frame.grid_forget()
            self.image_viewer_container.grid(row=0, column=0, sticky="nsew")
        else:
            self.image_viewer_container.grid_forget()
            self.editor_area_frame.grid(row=0, column=0, sticky="nsew")

    def log_line(self, text):
        try:
            self.log.configure(state="normal")
            self.log.insert("end", text + "\n")
            self.log.configure(state="disabled")
            self.log.see("end")
        except:
            pass

    def _on_log_click(self, event):
        try:
            idx = self.log.index(f"@{event.x},{event.y}")
            line_text = self.log.get(f"{idx} linestart", f"{idx} lineend")
            match = re.search(r'l\.(\d+)', line_text)
            if match:
                line_num = match.group(1)
                self._switch_center_view('editor')
                self.editor.see(f"{line_num}.0")
                self.editor._textbox.mark_set("insert", f"{line_num}.0")
                self.editor.focus_set()
                self.editor.tag_add("sel", f"{line_num}.0", f"{line_num}.0 lineend")
        except:
            pass

    def _create_project_flow(self):
        self._close_project()
        self.welcome_screen._show_create_options()

    def _finish_create_project(self, choice):
        if choice == "zip":
            zip_path = filedialog.askopenfilename(title="1. Selecione o arquivo .ZIP", filetypes=[("ZIP", "*.zip")])
            if not zip_path: return
            p = Path(filedialog.askdirectory(title="2. Selecione uma pasta VAZIA para extrair o projeto"))
            if not p or any(p.iterdir()): messagebox.showerror("Erro", "A pasta deve estar vazia."); return
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(p)
                self.load_project_folder(p)
            except Exception as e:
                messagebox.showerror("Erro", f"{e}")
        elif choice == "blank":
            p = Path(filedialog.askdirectory(title="Selecione ou crie uma pasta VAZIA para o novo projeto"))
            if not p or any(p.iterdir()): messagebox.showerror("Erro", "A pasta deve estar vazia."); return
            (p / "main.tex").write_text(
                "% LaThon Project\n\\documentclass{article}\n\\begin{document}\n\\section{Start}\nHello World!\n\\end{document}",
                encoding="utf-8")
            self.load_project_folder(p)

    def _open_project_flow(self):
        fp = filedialog.askopenfilename(filetypes=[("LaTeX", "*.tex")])
        if fp: self.load_project_folder(Path(fp).parent)

    def load_project_folder(self, folder_path):
        self.welcome_screen.grid_forget()
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        try:
            self.state('zoomed')
        except:
            self.attributes('-fullscreen', True)
        self.project_dir = folder_path
        self.config.add_recent(folder_path)
        self.file_panel.populate_tree()
        tex_files = list(self.project_dir.rglob("*.tex"))
        if tex_files:
            main_file = next((f for f in tex_files if f.name.lower() in ("main.tex", "root.tex")), tex_files[0])
            self._open_file(main_file)
        self.title(f"LaThon Editor - {self.project_dir.name}")
        self.compile_action()

    def _close_project(self):
        self._save_active_file()
        self.project_dir, self.active_file = None, None
        self.spell_checker.clear_state()
        self.file_panel.clear_tree_and_outline()
        self.find_handler.hide_dialog()
        self.editor.delete("1.0", "end")

        self.preview_panel.clear_image()

        self.chapter_highlighter.is_active = False
        self.title("LaThon LaTeX Editor")
        try:
            self.state('normal')
        except:
            self.attributes('-fullscreen', False)
        self.geometry("1200x800")
        self.main_frame.grid_forget()
        self.welcome_screen.grid(row=0, column=0, sticky="nsew")
        self.welcome_screen._show_main_menu()

    def _save_active_file(self):
        if self.active_file and self.active_file.exists():
            try:
                self.active_file.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
                return True
            except Exception as e:
                messagebox.showerror("Erro", f"{e}")
                return False
        return True

    def _open_file(self, file_path: Path):
        self._switch_center_view('editor')
        if self.active_file == file_path: return
        if not self._save_active_file(): return
        try:
            self.active_file = file_path
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", file_path.read_text(encoding="utf-8", errors="ignore"))

            self.editor.clear_undo_history()

            self.log_line(f"Abriu: {self.active_file.name}")
            self.file_panel.update_file_outline()
            self.editor.apply_syntax_highlighting()
            self.editor.update_line_numbers()
            self.spell_checker.apply_spell_check()
            self.editor.see("1.0")
        except Exception as e:
            messagebox.showerror("Erro ao Abrir", f"{e}")
            self.active_file = None

    def _clean_aux_files(self):
        if not self.project_dir: return
        count = 0
        for ext in [".aux", ".log", ".out", ".toc", ".bbl", ".blg", ".synctex.gz", ".fls", ".fdb_latexmk"]:
            for f in self.project_dir.rglob(f"*{ext}"):
                try:
                    f.unlink(); count += 1
                except:
                    pass
        self.log_line(f"Limpeza: {count} arquivos removidos.")

    def compile_action(self):
        if not self.project_dir or not self._save_active_file(): return
        tex_files = list(self.project_dir.rglob("*.tex"))
        main_file = next((f for f in tex_files if f.name.lower() in ("main.tex", "root.tex")), self.active_file)
        if not main_file: return

        if self.latex_compiler:
            try:
                subprocess.run(
                    [str(Path(self.latex_compiler).parent / "miktex-config.exe"), 'set', '--user', 'AutoInstall=1'],
                    creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass

        self.log.configure(state="normal");
        self.log.delete('1.0', 'end');
        self.log.configure(state="disabled")
        self.log_line(f"Compilando: {main_file.name}")
        self.compile_button.configure(state="disabled", text=" Compilando...", fg_color="gray")
        CompilerThread(self.project_dir, main_file.name, self.latex_compiler, self.queue).start()

    def process_queue(self):
        try:
            msg = self.queue.get_nowait()
            if isinstance(msg, tuple):
                if msg[0] == "finished":
                    if self.download_notification_window: self.download_notification_window.destroy(); self.download_notification_window = None
                    self.compile_button.configure(state="normal", text=" Compile (Ctrl+S)", fg_color=Colors.BTN_PRIMARY)
                    if self.project_dir:
                        main_file = next((f for f in list(self.project_dir.rglob("*.tex")) if
                                          f.name.lower() in ("main.tex", "root.tex")), self.active_file)
                        pdf = self.project_dir / main_file.with_suffix(".pdf").name
                        if msg[1]:
                            self.log_line("\n--- SUCESSO ---")
                            self.preview_panel.show_pdf_preview(pdf)
                        else:
                            self.log_line("\n--- FALHA ---")
                elif msg[0] == "downloading_package" and not self.download_notification_window:
                    self.download_notification_window = ctk.CTkToplevel(self)
                    ctk.CTkLabel(self.download_notification_window, text="Baixando pacotes...").pack(padx=20, pady=20)
            else:
                self.log_line(str(msg))
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def on_closing(self):
        if self.project_dir: self._save_active_file()
        self.destroy()