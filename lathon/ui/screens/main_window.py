import queue
import re
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import subprocess

# --- Cérebro e Ferramentas Base ---
from lathon.core.config import ConfigManager
from lathon.core.compiler import find_latex_compiler, CompilerThread
from lathon.core.exporter import ProjectExporter

# --- Componentes Visuais (UI Panels & Widgets) ---
from lathon.ui.screens.welcome_screen import WelcomeScreen
from lathon.ui.screens.workspace.editor_panel import LaTeXEditor
from lathon.ui.screens.workspace.file_panel import FilePanel
from lathon.ui.screens.workspace.preview_panel import PreviewPanel
from lathon.features.assistants.terminal_logs import TerminalPanel
from lathon.ui.widgets.icon_button import create_icon_button

# --- Funcionalidades Inserção e Preferências ---
from lathon.features.preferences.preferences_manager import PreferencesManager
from lathon.features.insert.insert_manager import InsertManager

# --- Opções e Assistentes de Edição ---
from lathon.features.assistants.find_replace import FindReplaceHandler
from lathon.features.assistants.chapter_highlighter import ChapterHighlighter
from lathon.features.assistants.spell_checker import SpellCheckHandler
from lathon.features.assistants.autocomplete import AutocompleteHandler
from lathon.features.assistants.context_menu import ContextMenuManager
from lathon.features.assistants.options_manager import OptionsManager

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts, Icons, create_lathon_logo


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
        self.active_compiler_thread = None  # Thread do compilador para poder ser morta
        self.download_notification_window = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.welcome_screen = WelcomeScreen(self, self)
        self.welcome_screen.grid(row=0, column=0, sticky="nsew")

        self.scroll_conf = {"scrollbar_button_color": Colors.SCROLL_BTN,
                            "scrollbar_button_hover_color": Colors.SCROLL_HOVER}

        # Contrata o gerente PRIMEIRO!
        self.preferences_manager = PreferencesManager(self)

        # Agora sim manda construir a interface
        self._build_ui()
        self._bind_events()

        # E depois da interface pronta, aplica a fonte no editor
        layout_cfg = self.config.get_layout()
        self.preferences_manager.apply_font_config(layout_cfg.get("font_family"), layout_cfg.get("font_size"))
        self.editor.update_colors()

        if not self.latex_compiler: messagebox.showerror("Aviso", "Compilador LaTeX não encontrado.")

        # Inicia a fila de mensagens
        self.after(100, self.process_queue)

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

        # Configuração base dos botões de menu
        menu_btn_conf = {"height": 26, "width": 30, "fg_color": "transparent",
                         "text_color": Colors.BTN_TRANSPARENT_TEXT,
                         "hover_color": Colors.BTN_HOVER, "font": Fonts.UI}
        menu_bg = Colors.BG_MAIN[1]

        # BOTÃO VOLTAR
        self.btn_back = ctk.CTkButton(top_inner, text=" Voltar", image=Icons.get_ctk_image("back.png", size=(18, 18)),
                                      command=self._close_project, **menu_btn_conf)
        self.btn_back.pack(side="left", padx=(10, 5))

        # DIVISÓRIA VERTICAL ELEGANTE
        ctk.CTkFrame(top_inner, width=1, height=20, fg_color=Colors.BORDER).pack(side="left", padx=(5, 10))

        # Inserir
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

        # Opções (RESTAUROU O SEU ORIGINAL COM CTRL+M)
        self.btn_options = ctk.CTkButton(top_inner, text=" Opções", image=Icons.get_ctk_image("options.png"),
                                         command=lambda: self._popup_menu(self.menu_options, self.btn_options),
                                         **menu_btn_conf)
        self.btn_options.pack(side="left", padx=2)
        self.menu_options = tk.Menu(self, tearoff=0, bg=menu_bg, fg="white", activebackground=Colors.THON)

        # Variáveis do Menu
        self.var_chap = tk.BooleanVar(value=False)
        self.var_auto = tk.BooleanVar(value=True)
        self.var_spell = tk.BooleanVar(value=True)
        self.var_warnings = tk.BooleanVar(value=True)  # <- NOVA VARIÁVEL AQUI

        self.menu_options.add_command(label=" Localizar (Ctrl+F)", image=Icons.get_treeview_icon("search.png"),
                                      compound="left", command=lambda: self.options_manager.show_find_dialog())
        self.menu_options.add_command(label=" Ver Lista de Marcações...", image=Icons.get_treeview_icon("list.png"),
                                      compound="left", command=lambda: self.options_manager.open_markers_list())
        self.menu_options.add_separator()

        self.menu_options.add_checkbutton(label="Evidenciar Capítulos (Ctrl+M)", variable=self.var_chap,
                                          selectcolor=Colors.THON,
                                          command=lambda: self.options_manager.set_chapter_highlight(
                                              self.var_chap.get()))
        self.menu_options.add_checkbutton(label="Autocompletar LaTeX", variable=self.var_auto, selectcolor=Colors.THON,
                                          command=lambda: self.options_manager.set_autocomplete(self.var_auto.get()))
        self.menu_options.add_checkbutton(label="Corretor Ortográfico", variable=self.var_spell,
                                          selectcolor=Colors.THON,
                                          command=lambda: self.options_manager.set_spellcheck(self.var_spell.get()))

        # === ADICIONE O NOVO BOTÃO AQUI ===
        self.menu_options.add_checkbutton(label="Mostrar Avisos (Warnings)", variable=self.var_warnings,
                                          selectcolor=Colors.THON,
                                          command=lambda: self.options_manager.set_warnings(self.var_warnings.get()))

        self.menu_options.add_separator()
        self.menu_options.add_command(label=" Alternar Tema (Ctrl+T)", image=Icons.get_treeview_icon("theme.png"),
                                      compound="left", command=lambda: self.options_manager.toggle_theme())

        # Exportar
        self.btn_export = ctk.CTkButton(top_inner, text=" Exportar", image=Icons.get_ctk_image("export.png"),
                                        command=lambda: self._popup_menu(self.menu_export, self.btn_export),
                                        **menu_btn_conf)
        self.btn_export.pack(side="left", padx=2)
        self.menu_export = tk.Menu(self, tearoff=0, bg=menu_bg, fg="white", activebackground=Colors.THON)
        self.menu_export.add_command(label=" PDF (Ctrl+E)", image=Icons.get_treeview_icon("pdf.png"), compound="left",
                                     command=lambda: ProjectExporter.export_pdf(self.project_dir, self.active_file))
        self.menu_export.add_command(label=" ZIP (Ctrl+Shift+E)", image=Icons.get_treeview_icon("zip.png"),
                                     compound="left", command=lambda: ProjectExporter.export_zip(self.project_dir))

        # Config (RESTAUROU O SEU MENU DEDICADO DE CONFIG)
        self.btn_config = ctk.CTkButton(top_inner, text=" Config", image=Icons.get_ctk_image("config.png"),
                                        command=lambda: self._popup_menu(self.menu_config, self.btn_config),
                                        **menu_btn_conf)
        self.btn_config.pack(side="left", padx=2)
        self.menu_config = tk.Menu(self, tearoff=0, bg=menu_bg, fg="white", activebackground=Colors.THON)
        self.menu_config.add_command(label=" Corretor Ortográfico...", image=Icons.get_treeview_icon("spell.png"),
                                     compound="left", command=lambda: self.preferences_manager.open_spell_config())
        self.menu_config.add_separator()
        self.menu_config.add_command(label=" Fonte do Editor...", image=Icons.get_treeview_icon("font.png"),
                                     compound="left", command=lambda: self.preferences_manager.open_font_config())
        self.menu_config.add_separator()
        self.menu_config.add_command(label=" Configuração de Tela...", image=Icons.get_treeview_icon("layout.png"),
                                     compound="left", command=lambda: self.preferences_manager.open_layout_config())

        # Compile e Info
        self.compile_button = ctk.CTkButton(top_inner, text=" Compile (Ctrl+S)",
                                            image=Icons.get_ctk_image("compile.png"), height=24,
                                            command=self.compile_action, fg_color=Colors.BTN_PRIMARY,
                                            hover_color=Colors.BTN_PRIMARY_HOVER, font=Fonts.UI_BOLD)
        self.compile_button.pack(side="right", padx=10)

        self.info_button = create_icon_button(top_inner, "info.png", "Informações do LaThon", self._show_about_dialog, side="right", padx=(0, 5))

        # ==========================================
        # 2. CONSTRUÇÃO DOS COMPONENTES (PAINÉIS)
        # ==========================================
        layout_cfg = self.config.get_layout()
        self.preferences_manager.apply_layout_weights(layout_cfg["left"], layout_cfg["center"], layout_cfg["pdf"])

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

        self.image_viewer_container = ctk.CTkScrollableFrame(self.center_frame, label_text="", fg_color="transparent",
                                                             **self.scroll_conf)
        self.image_viewer_label = ctk.CTkLabel(self.image_viewer_container, text="")
        self.image_viewer_label.pack(expand=True, padx=5, pady=5)

        self.find_frame = ctk.CTkFrame(self.center_frame, fg_color=Colors.BG_MAIN, corner_radius=6, border_width=1,
                                       border_color=Colors.BORDER)

        # === NOVO TERMINAL INTELIGENTE ===
        self.terminal_panel = TerminalPanel(self.center_frame, self)
        self.terminal_panel.grid(row=2, column=0, rowspan=2, sticky="nsew", pady=0)

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

    # --- Funções Básicas e Atalhos ---
    def _show_about_dialog(self):
        about_text = (
            "Lathon LaTeX Editor\nVersão 1.2\nCompilador Latex MiKTeX Portable\nDesenvolvido por: Murilo Campos\n\nEm caso de bugs ou sujestões, entre em contato...\nFique a vontade e aproveite o Lathon!!!")
        messagebox.showinfo("Sobre o Lathon", about_text)

    def _compile_shortcut(self, event=None):
        self.compile_action()

    def _export_pdf_shortcut(self, event=None):
        ProjectExporter.export_pdf(self.project_dir, self.active_file)

    def _export_zip_shortcut(self, event=None):
        ProjectExporter.export_zip(self.project_dir)

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
        self.bind_all("<Control-f>", lambda e: self._handle_shortcut(self._find_shortcut))
        self.bind_all("<Control-m>", lambda e: self._handle_shortcut(self._toggle_chapter_shortcut))
        self.bind_all("<Control-t>", lambda e: self._handle_shortcut(self._toggle_theme_shortcut))
        self.editor.bind("<KeyRelease>", self._schedule_outline_update, add="+")
        self._outline_timer = None

    def _handle_shortcut(self, func):
        func()
        return "break"

    def _schedule_outline_update(self, event=None):
        if getattr(self, '_outline_timer', None):
            self.after_cancel(self._outline_timer)
        self._outline_timer = self.after(1000, self.file_panel.update_file_outline)

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
        self.terminal_panel.log_line(text)

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

    # --- Gerenciamento de Projetos e Arquivos ---
    def load_project_folder(self, folder_path):
        self.welcome_screen.grid_forget()
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        try:
            self.state('zoomed')
        except:
            self.attributes('-fullscreen', True)
        self.project_dir = folder_path

        self.file_panel.populate_tree()
        tex_files = list(self.project_dir.rglob("*.tex"))
        if tex_files:
            main_file = next((f for f in tex_files if f.name.lower() in ("main.tex", "root.tex")), tex_files[0])
            self._open_file(main_file)

        self.title(f"LaThon Editor - {self.project_dir.name}")
        self.compile_action()

    def _close_project(self):
        """Limpa o projeto atual, MATA o compilador e volta ao Dashboard"""

        # 1. Mata a compilação ativa e limpa a fila do zumbi
        if self.active_compiler_thread and self.active_compiler_thread.is_alive():
            self.active_compiler_thread.cancel()
            self.active_compiler_thread = None

        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except:
                pass

        # 2. Salva e limpa a UI
        self._save_active_file()
        self.project_dir, self.active_file = None, None
        self.spell_checker.clear_state()
        self.file_panel.clear_tree_and_outline()
        self.find_handler.hide_dialog()
        self.editor.delete("1.0", "end")
        self.preview_panel.clear_image()
        self.chapter_highlighter.is_active = False

        # 3. Restaura janela
        self.title("LaThon LaTeX Editor")
        try:
            self.state('normal')
        except:
            self.attributes('-fullscreen', False)
        self.geometry("1200x800")

        # 4. Troca para a Tela Inicial (Welcome/Dashboard)
        self.main_frame.grid_forget()
        self.welcome_screen.grid(row=0, column=0, sticky="nsew")
        self.welcome_screen._render()

    def _save_active_file(self):
        if self.active_file and self.active_file.exists():
            try:
                self.active_file.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
                self.config.save_file_markers(str(self.active_file.resolve()), self.editor.export_markers())
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
            saved_markers = self.config.get_file_markers(str(self.active_file.resolve()))
            self.editor.import_markers(saved_markers)
            self.editor.see("1.0")
        except Exception as e:
            messagebox.showerror("Erro ao Abrir", f"{e}")
            self.active_file = None

    def _clean_aux_files(self):
        """Limpa arquivos temporários do LaTeX silenciosamente a cada compilação."""
        if not self.project_dir: return
        for ext in [".aux", ".log", ".out", ".toc", ".bbl", ".blg", ".synctex.gz", ".fls", ".fdb_latexmk"]:
            for f in self.project_dir.rglob(f"*{ext}"):
                try: f.unlink()
                except: pass

    # --- Compilação e Threads ---
    def compile_action(self):
        if not self.project_dir or not self._save_active_file(): return
        self._clean_aux_files()
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

        self.terminal_panel.clear()
        self.log_line(f"Compilando: {main_file.name}")
        self.compile_button.configure(state="disabled", text=" Compilando...", fg_color="gray")

        # Mata compilação anterior se estiver rodando
        if getattr(self, "active_compiler_thread", None) and self.active_compiler_thread.is_alive():
            self.active_compiler_thread.cancel()

        # Inicia a nova
        self.active_compiler_thread = CompilerThread(self.project_dir, main_file.name, self.latex_compiler, self.queue)
        self.active_compiler_thread.start()

    def process_queue(self):
        try:
            # Puxa tudo que tiver na fila para não engasgar a interface
            while True:
                msg = self.queue.get_nowait()
                if isinstance(msg, tuple):
                    if msg[0] == "finished":
                        if self.download_notification_window: self.download_notification_window.destroy(); self.download_notification_window = None
                        self.compile_button.configure(state="normal", text=" Compile (Ctrl+S)",
                                                      fg_color=Colors.BTN_PRIMARY)
                        if self.project_dir:
                            main_file = next((f for f in list(self.project_dir.rglob("*.tex")) if
                                              f.name.lower() in ("main.tex", "root.tex")), self.active_file)
                            if main_file:
                                pdf = self.project_dir / main_file.with_suffix(".pdf").name
                                log_file = self.project_dir / main_file.with_suffix(".log").name

                                # 1. Roda o caçador de bugs SEMPRE (lendo o arquivo .log)
                                has_errors = self.terminal_panel.analyze_latex_log(log_file)

                                if msg[1]:
                                    # Gerou PDF, mas teve erro de sintaxe no meio?
                                    if has_errors:
                                        self.terminal_panel.log_line(
                                            "\n--- COMPILADO COM ERROS (Verifique as linhas vermelhas) ---", "error")
                                    else:
                                        self.terminal_panel.log_line("\n--- SUCESSO ---", "success")
                                    self.preview_panel.show_pdf_preview(pdf)
                                else:
                                    # Falhou criticamente (nem gerou PDF)
                                    self.terminal_panel.log_line("\n--- FALHA CRÍTICA NA COMPILAÇÃO ---", "error")

                    elif msg[0] == "downloading_package" and not self.download_notification_window:
                        self.download_notification_window = ctk.CTkToplevel(self)
                        ctk.CTkLabel(self.download_notification_window, text="Baixando pacotes...").pack(padx=20,
                                                                                                         pady=20)
                else:
                    self.log_line(str(msg))
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def on_closing(self):
        if self.project_dir: self._save_active_file()
        if self.active_compiler_thread and self.active_compiler_thread.is_alive():
            self.active_compiler_thread.cancel()
        self.destroy()