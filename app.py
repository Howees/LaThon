import shutil
import subprocess
import zipfile
import json
import os
from pathlib import Path
import queue
import re
import tkinter as tk
import tkinter.ttk as ttk

# --- UI Framework ---
import customtkinter as ctk
from tkinter import filedialog, messagebox
from customtkinter import CTkInputDialog

# --- Módulos da Aplicação ---
from compiler import find_latex_compiler, CompilerThread
from ui_widgets import CustomDialog, TableInputDialog, LayoutConfigDialog, EditorConfigDialog
from preview_handler import PreviewHandler, PYMUPDF_AVAILABLE
from find_replace import FindReplaceHandler
from file_manager import FileManager
from spell_checker import SpellCheckHandler
from autocomplete_handler import AutocompleteHandler

RECENTS_FILE = "recents.json"
LAYOUT_FILE = "layout_config.json"


class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, fg_color="transparent")
        self.app = app_instance

        self.center_container = ctk.CTkFrame(self, fg_color="transparent")
        self.center_container.place(relx=0.5, rely=0.5, anchor="center")
        self._show_main_menu()

    def _show_main_menu(self):
        for widget in self.center_container.winfo_children(): widget.destroy()

        # 1. LOGO
        logo_frame = ctk.CTkFrame(self.center_container, fg_color="transparent")
        logo_frame.pack(pady=(0, 20))
        ctk.CTkLabel(logo_frame, text="La", font=("Segoe UI", 60, "bold"), text_color="#2ea043").pack(side="left")
        ctk.CTkLabel(logo_frame, text="Thon", font=("Segoe UI", 60, "bold"), text_color="#41a5ee").pack(side="left")

        # 2. BOTÕES DE AÇÃO
        btn_new = ctk.CTkButton(self.center_container, text="✨  Criar Novo Projeto",
                                command=self._show_create_options,
                                width=300, height=45, font=("Segoe UI", 14, "bold"),
                                fg_color="#238636", hover_color="#2ea043", corner_radius=8)
        btn_new.pack(pady=8)

        btn_open = ctk.CTkButton(self.center_container, text="📂  Abrir Projeto Existente",
                                 command=self.app._open_project_flow,
                                 width=300, height=45, font=("Segoe UI", 14, "bold"),
                                 fg_color=("gray85", "gray20"), text_color=("black", "white"),
                                 border_width=2, border_color=("gray70", "gray50"),
                                 hover_color=("gray75", "gray25"), corner_radius=8)
        btn_open.pack(pady=8)

        # 3. ÁREA DE RECENTES COMPACTA
        recents = self.app._load_recents()
        if recents:
            # Separador visual discreto
            ctk.CTkFrame(self.center_container, height=1, width=150, fg_color=("gray70", "gray30")).pack(pady=(25, 10))

            ctk.CTkLabel(self.center_container, text="Recentes", text_color="gray50",
                         font=("Segoe UI", 11, "bold")).pack(pady=(0, 5))

            # Frame Simples (Não Scrollable) para ficar compacto
            recents_frame = ctk.CTkFrame(self.center_container, fg_color="transparent")
            recents_frame.pack()

            # Mostra apenas os 3 primeiros
            for path_str in recents[:3]:
                p = Path(path_str)
                if p.exists():
                    btn = ctk.CTkButton(recents_frame, text=f"📄 {p.name}", anchor="center",
                                        font=("Segoe UI", 12), height=28, width=200,
                                        fg_color="transparent",
                                        text_color=("gray30", "gray80"),
                                        hover_color=("gray90", "gray25"),
                                        command=lambda x=p: self.app.load_project_folder(x))
                    btn.pack(pady=1)

        # Rodapé Minimalista
        ctk.CTkLabel(self.center_container, text="v5.5", text_color="gray40",
                     font=("Segoe UI", 10)).pack(pady=(30, 0))

    def _show_create_options(self):
        for widget in self.center_container.winfo_children(): widget.destroy()

        ctk.CTkLabel(self.center_container, text="Novo Projeto", font=("Segoe UI", 24, "bold")).pack(pady=(0, 30))

        btn_blank = ctk.CTkButton(self.center_container, text="📄  Começar do Zero",
                                  command=lambda: self.app._finish_create_project("blank"),
                                  width=300, height=45, font=("Segoe UI", 14), corner_radius=8,
                                  fg_color=("#3B8ED0", "#1f538d"), hover_color=("#36719F", "#14375e"))
        btn_blank.pack(pady=10)

        btn_zip = ctk.CTkButton(self.center_container, text="📦  Importar de .zip",
                                command=lambda: self.app._finish_create_project("zip"),
                                width=300, height=45, font=("Segoe UI", 14), corner_radius=8,
                                fg_color=("gray80", "gray30"), text_color=("black", "white"),
                                hover_color=("gray70", "gray40"))
        btn_zip.pack(pady=10)

        ctk.CTkButton(self.center_container, text="← Voltar", command=self._show_main_menu,
                      width=100, height=30, fg_color="transparent", text_color="gray",
                      hover_color=("gray90", "gray20")).pack(pady=(30, 0))


class MiniOverleaf(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LaThon LaTeX Editor")
        self.geometry("1200x800")

        self.latex_compiler = find_latex_compiler()
        self.queue = queue.Queue()
        self.project_dir = None
        self.active_file = None
        self.outline_update_timer = None
        self.syntax_highlight_timer = None
        self.download_notification_window = None
        self.spellcheck_timer = None
        self.highlight_chapters_active = False

        # --- CARREGA CONFIGURAÇÕES ---
        self.layout_pcts = {"files": 0.20, "pdf": 0.40}
        self.font_size = 12
        self.font_family = "Consolas"
        self._load_layout_config()

        # Inicializa como None para segurança
        self.preview_handler = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.welcome_screen = WelcomeScreen(self, self)
        self.welcome_screen.grid(row=0, column=0, sticky="nsew")

        self.scroll_conf = {
            "scrollbar_button_color": ("#bfbfbf", "#7a7a7a"),
            "scrollbar_button_hover_color": ("#a6a6a6", "#a0a0a0")
        }

        # --- TELA PRINCIPAL ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # BARRA SUPERIOR
        top_frame = ctk.CTkFrame(self.main_frame, height=35, corner_radius=0, fg_color=("gray90", "#1f1f1f"),
                                 border_width=0)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.grid_propagate(False)
        ctk.CTkFrame(top_frame, height=1, fg_color=("gray80", "#2b2b2b")).pack(side="bottom", fill="x")

        top_inner = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_inner.pack(fill="both", expand=True, padx=5)

        lbl_logo_la = ctk.CTkLabel(top_inner, text="La", font=("Segoe UI", 16, "bold"), text_color="#2ea043")
        lbl_logo_la.pack(side="left", padx=(5, 0))
        lbl_logo_thon = ctk.CTkLabel(top_inner, text="Thon", font=("Segoe UI", 16, "bold"), text_color="#41a5ee")
        lbl_logo_thon.pack(side="left", padx=(0, 15))

        menu_btn_conf = {"width": 80, "height": 26, "fg_color": "transparent", "text_color": ("gray10", "gray90"),
                         "hover_color": ("gray80", "gray30"), "font": ("Segoe UI", 12), "anchor": "center"}

        self.btn_file = ctk.CTkButton(top_inner, text="📄 Arquivo", command=self._show_file_menu, **menu_btn_conf)
        self.btn_file.pack(side="left", padx=1)
        self.menu_file = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#4158D0")
        self.menu_file.add_command(label="✨ Novo Projeto", command=self._create_project_flow)
        self.menu_file.add_command(label="📂 Abrir Projeto", command=self._open_project_flow)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="💾 Salvar (Ctrl+S)", command=self.compile_action)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="🧹 Limpar Temporários", command=self._clean_aux_files)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="❌ Fechar Projeto", command=self._close_project)

        self.btn_options = ctk.CTkButton(top_inner, text="🛠 Opções", command=self._show_options_menu, **menu_btn_conf)
        self.btn_options.pack(side="left", padx=1)
        self.menu_options = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#4158D0")
        self.menu_options.add_command(label="🔍 Localizar (Ctrl+F)", command=self._open_find_dialog)
        self.menu_options.add_separator()
        self.menu_options.add_command(label="▦ Inserir Tabela...", command=self._open_table_wizard)
        self.menu_options.add_separator()
        self.menu_options.add_checkbutton(label="👁️ Evidenciar Capítulos (Ctrl+M)",
                                          command=self._toggle_chapter_highlighting,
                                          variable=tk.BooleanVar(value=False))
        self.menu_options.add_separator()
        self.menu_options.add_command(label="🌗 Alternar Tema (Ctrl+T)", command=self._toggle_theme)

        self.btn_export = ctk.CTkButton(top_inner, text="📤 Exportar", command=self._show_export_menu, **menu_btn_conf)
        self.btn_export.pack(side="left", padx=1)
        self.menu_export = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#4158D0")
        self.menu_export.add_command(label="📄 PDF (Ctrl+E)", command=self.export_pdf)
        self.menu_export.add_command(label="📦 ZIP (Ctrl+Shift+E)", command=self._export_project_as_zip)

        self.btn_config = ctk.CTkButton(top_inner, text="⚙️ Config", command=self._show_config_menu, **menu_btn_conf)
        self.btn_config.pack(side="left", padx=1)
        self.menu_config = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#4158D0")
        self.menu_config.add_command(label="🖥️ Configurar Tela", command=self._open_layout_config)
        self.menu_config.add_command(label="📝 Configurar Editor", command=self._open_editor_config)
        self.menu_config.add_command(label="abc Configurar Corretor", command=self._open_spell_config)

        self.compile_button = ctk.CTkButton(top_inner, text="▶ Compile (Ctrl+S)", width=130, height=24,
                                            command=self.compile_action, fg_color="#238636", hover_color="#2ea043",
                                            font=("Segoe UI", 12, "bold"))
        self.compile_button.pack(side="right", padx=10)

        # =========================================================================
        # LAYOUT
        # =========================================================================

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#2b2b2b" if is_dark else "#e6e6e6"

        self.paned_main = tk.PanedWindow(self.main_frame, orient="horizontal", bd=0,
                                         sashwidth=0, sashpad=0, showhandle=False, bg=bg_color)
        self.paned_main.grid(row=1, column=0, sticky="nsew")

        self.paned_editor_pdf = tk.PanedWindow(self.paned_main, orient="horizontal", bd=0,
                                               sashwidth=0, sashpad=0, showhandle=False, bg=bg_color)

        # --- PAINEL ESQUERDO ---
        self.left_panel = ctk.CTkFrame(self.paned_main, fg_color=("gray95", "#252526"), corner_radius=0)
        self.left_panel.grid_rowconfigure(2, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.left_panel, show="tree headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_menu = tk.Menu(self, tearoff=0)

        outline_header = ctk.CTkFrame(self.left_panel, height=25, fg_color=("gray85", "#333333"), corner_radius=0)
        outline_header.grid(row=1, column=0, sticky="ew")
        ctk.CTkLabel(outline_header, text="ESTRUTURA", font=("Segoe UI", 11, "bold"), text_color="gray60").pack(
            side="left", padx=5)

        self.outline_frame = ctk.CTkScrollableFrame(self.left_panel, label_text="", fg_color="transparent",
                                                    **self.scroll_conf)
        self.outline_frame.grid(row=2, column=0, sticky="nsew")

        # --- PAINEL CENTRAL (EDITOR) ---
        self.center_frame = ctk.CTkFrame(self.paned_editor_pdf, fg_color=("white", "#1e1e1e"), corner_radius=0)
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(3, weight=0, minsize=100)
        self.center_frame.grid_columnconfigure(0, weight=1)

        self.editor_area_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.editor_area_frame.grid(row=0, column=0, sticky="nsew")
        self.editor_area_frame.grid_rowconfigure(0, weight=1)
        self.editor_area_frame.grid_columnconfigure(1, weight=1)

        initial_font = (self.font_family, self.font_size)

        self.line_number_bar = ctk.CTkTextbox(self.editor_area_frame, width=45, font=initial_font, state="disabled",
                                              activate_scrollbars=False, fg_color=("gray92", "#252526"),
                                              text_color="gray50")
        self.line_number_bar.grid(row=0, column=0, sticky="nsw")
        self.line_number_bar._textbox.configure(spacing1=0, spacing2=0, spacing3=2)

        self.editor = ctk.CTkTextbox(self.editor_area_frame, font=initial_font, wrap="word", undo=True,
                                     fg_color=("white", "#1a1a1a"))
        self.editor.grid(row=0, column=1, sticky="nsew")
        self.editor._textbox.configure(spacing1=0, spacing2=0, spacing3=2)

        self.image_viewer_container = ctk.CTkScrollableFrame(self.center_frame, label_text="", fg_color="transparent",
                                                             **self.scroll_conf)
        self.image_viewer_label = ctk.CTkLabel(self.image_viewer_container, text="")
        self.image_viewer_label.pack(expand=True, padx=5, pady=5)

        self.spell_menu = tk.Menu(self, tearoff=0)

        self._editor_original_scroll_command = self.editor._textbox.cget("yscrollcommand")
        self.editor._textbox.configure(yscrollcommand=self._on_editor_scroll_proxy)
        self._switch_center_view('editor')
        self.editor.bind("<KeyRelease>", self._on_text_changed)
        self.editor._textbox.bind("<Double-Button-1>", self._select_word_by_double_click)

        self.editor._textbox.tag_configure("command", foreground="#569cd6")
        self.editor._textbox.tag_configure("comment", foreground="#6a9955")
        self.editor._textbox.tag_configure("label", foreground="#ce9178")
        self.editor._textbox.tag_configure("file_path", foreground="#dcdcaa")
        self._update_highlight_colors()

        bg_find = ("#f0f0f0", "#252526")
        self.find_frame = ctk.CTkFrame(self.center_frame, fg_color=bg_find, corner_radius=0)
        self.find_frame.grid_columnconfigure(0, weight=1)

        entry_height, btn_height = 28, 28
        self.find_entry = ctk.CTkEntry(self.find_frame, placeholder_text="Localizar...", height=entry_height,
                                       border_width=1)
        self.find_entry.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="ew")
        self.find_next_button = ctk.CTkButton(self.find_frame, text="Próximo ⬇", width=90, height=btn_height,
                                              fg_color=("#3B8ED0", "#1f538d"), hover_color=("#36719F", "#14375e"))
        self.find_next_button.grid(row=0, column=1, columnspan=2, padx=5, pady=(10, 5), sticky="ew")
        self.find_close_button = ctk.CTkButton(self.find_frame, text="✕", width=30, height=btn_height,
                                               fg_color="transparent", text_color=("gray50", "gray70"),
                                               hover_color=("#ffcccc", "#4d0000"))
        self.find_close_button.grid(row=0, column=3, padx=(0, 5), pady=(10, 5))
        self.replace_entry = ctk.CTkEntry(self.find_frame, placeholder_text="Substituir por...", height=entry_height,
                                          border_width=1)
        self.replace_entry.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="ew")
        self.replace_button = ctk.CTkButton(self.find_frame, text="Substituir", width=90, height=btn_height,
                                            fg_color="transparent", border_width=1, border_color=("gray60", "gray50"),
                                            text_color=("black", "white"), hover_color=("gray90", "gray30"))
        self.replace_button.grid(row=1, column=1, padx=5, pady=(0, 10), sticky="ew")
        self.replace_all_button = ctk.CTkButton(self.find_frame, text="Tudo", width=90, height=btn_height,
                                                fg_color=("#3B8ED0", "#1f538d"), hover_color=("#36719F", "#14375e"))
        self.replace_all_button.grid(row=1, column=2, columnspan=2, padx=(0, 5), pady=(0, 10), sticky="ew")

        log_header = ctk.CTkFrame(self.center_frame, height=20, fg_color=("gray85", "#333333"), corner_radius=0)
        log_header.grid(row=2, column=0, sticky="ew")
        ctk.CTkLabel(log_header, text="TERMINAL / LOG", font=("Segoe UI", 10, "bold"), text_color="gray60").pack(
            side="left", padx=5)

        self.log = ctk.CTkTextbox(self.center_frame, font=("Consolas", 10), state="disabled",
                                  fg_color=("white", "#1e1e1e"))
        self.log.grid(row=3, column=0, sticky="nsew", pady=0)
        self.log.bind("<Button-1>", self._on_log_click)

        # --- C. PAINEL DIREITO (PDF) ---
        self.right_frame = ctk.CTkFrame(self.paned_editor_pdf, fg_color=("gray85", "#525659"), corner_radius=0)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.preview_frame = ctk.CTkScrollableFrame(self.right_frame, label_text="", fg_color="transparent",
                                                    **self.scroll_conf)
        self.preview_frame.grid(row=0, column=0, sticky="nsew")
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Abra um projeto para ver o preview.")
        self.preview_label.pack(anchor="n", fill="x", padx=0, pady=0)

        # --- APLICAÇÃO DAS TRAVAS (LIMITES) ---
        self.paned_main.add(self.left_panel)
        self.paned_main.add(self.paned_editor_pdf)
        self.paned_editor_pdf.add(self.center_frame)
        self.paned_editor_pdf.add(self.right_frame)

        # Aplicar layout inicial após a janela ser criada e renderizada
        self.after(500, self._apply_layout_settings)

        # --- Handlers ---
        self.preview_handler = PreviewHandler(self)
        self.file_manager = FileManager(self, self.tree, self.outline_frame, self.tree_menu)
        self.find_handler = FindReplaceHandler(self, self.editor, self.find_frame, self.find_entry, self.replace_entry)
        self.spell_checker = SpellCheckHandler(self, self.editor, self.spell_menu)
        self.autocomplete_handler = AutocompleteHandler(self, self.editor)

        # --- Bindings ---
        self.bind_all("<Control-s>", self._on_ctrl_s)
        self.bind_all("<Control-f>", self.find_handler.show_dialog)
        self.bind_all("<Control-m>", lambda e: self._toggle_chapter_highlighting())
        self.bind_all("<Control-e>", lambda e: self.export_pdf())
        self.bind_all("<Control-E>", lambda e: self._export_project_as_zip())
        self.bind_all("<Control-t>", lambda e: self._toggle_theme())
        self.bind_all("<Control-b>", lambda e: self._format_text("bold"))
        self.bind_all("<Control-i>", lambda e: self._format_text("italic"))

        self.editor.bind("<Control-z>", self._undo)
        self.editor.bind("<Control-y>", self._redo)
        self.editor.bind("<Control-Shift-Z>", self._redo)
        self.find_next_button.configure(command=self.find_handler.find_next)
        self.find_close_button.configure(command=self.find_handler.hide_dialog)
        self.replace_button.configure(command=self.find_handler.replace_one)
        self.replace_all_button.configure(command=self.find_handler.replace_all)
        self.find_entry.bind("<Return>", self.find_handler.find_next)
        self.find_entry.bind("<Escape>", self.find_handler.hide_dialog)
        self.replace_entry.bind("<Return>", self.find_handler.replace_one)
        self.replace_entry.bind("<Escape>", self.find_handler.hide_dialog)

        self.find_frame.grid_forget()
        self.process_queue()
        self._style_treeview()
        self._apply_editor_font()

        if not self.latex_compiler: messagebox.showerror("Aviso", "Compilador LaTeX não encontrado.")

    # --- LÓGICA DE CONFIGURAÇÃO DO LAYOUT ---
    def _load_layout_config(self):
        try:
            if Path(LAYOUT_FILE).exists():
                with open(LAYOUT_FILE, 'r') as f:
                    data = json.load(f)
                    self.layout_pcts = data.get("layout", self.layout_pcts)
                    self.font_size = data.get("font_size", 12)
                    self.font_family = data.get("font_family", "Consolas")
        except:
            pass

    def _save_layout_config(self):
        try:
            data = {
                "layout": self.layout_pcts,
                "font_size": self.font_size,
                "font_family": self.font_family
            }
            with open(LAYOUT_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass

    def _apply_layout_settings(self):
        total_width = self.winfo_width()
        if total_width <= 1: return

        files_px = int(total_width * self.layout_pcts["files"])
        try:
            self.paned_main.sash_place(0, files_px, 0)
        except:
            pass

        remaining_width = total_width - files_px
        pdf_px = int(total_width * self.layout_pcts["pdf"])
        sash2_pos = remaining_width - pdf_px
        try:
            self.paned_editor_pdf.sash_place(0, max(0, sash2_pos), 0)
        except:
            pass

    def _open_layout_config(self):
        d = LayoutConfigDialog(self.layout_pcts["files"], self.layout_pcts["pdf"])
        res = d.get_layout()
        if res:
            self.layout_pcts["files"] = res[0]
            self.layout_pcts["pdf"] = res[1]
            self._save_layout_config()
            self._apply_layout_settings()

    def _open_editor_config(self):
        d = EditorConfigDialog(self.font_size, self.font_family)
        res = d.get_settings()
        if res:
            new_size = res.get("font_size")
            new_family = res.get("font_family")
            if new_size != self.font_size or new_family != self.font_family:
                self.font_size = new_size
                self.font_family = new_family
                self._apply_editor_font()
                self._save_layout_config()

    def _open_spell_config(self):
        self.spell_checker.open_settings_window()

    def _apply_editor_font(self):
        font = (self.font_family, self.font_size)
        self.editor.configure(font=font)
        try:
            self.line_number_bar.configure(font=font)
        except:
            pass
        self._update_line_numbers()

    def _show_config_menu(self):
        self._popup_menu(self.menu_config, self.btn_config)

    def _load_recents(self):
        try:
            if Path(RECENTS_FILE).exists():
                with open(RECENTS_FILE, 'r') as f:
                    return json.load(f).get("recents", [])
        except:
            pass
        return []

    def _save_recents(self, new_path):
        current = self._load_recents()
        str_path = str(new_path)
        if str_path in current: current.remove(str_path)
        current.insert(0, str_path)
        current = current[:5]
        try:
            with open(RECENTS_FILE, 'w') as f:
                json.dump({"recents": current}, f)
        except:
            pass

    def _on_editor_scroll_proxy(self, *args):
        if self._editor_original_scroll_command:
            try:
                self.tk.call(self._editor_original_scroll_command, *args)
            except tk.TclError:
                pass
        self._sync_line_numbers_scroll(args[0])
        if hasattr(self, 'preview_handler') and self.preview_handler:
            self.preview_handler.sync_scroll_from_editor(args[0])

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
                end_idx = f"{line_num}.0 lineend"
                self.editor.tag_add("sel", f"{line_num}.0", end_idx)
        except:
            pass

    def _update_highlight_colors(self):
        current_theme = ctk.get_appearance_mode()
        if current_theme == "Light":
            c_part, c_chapter, c_section, c_subsection, c_subsubsection = "#DAE8FC", "#D5E8D4", "#E1D5E7", "#FFE6CC", "#FFF2CC"
        else:
            c_part, c_chapter, c_section, c_subsection, c_subsubsection = "#4a3b59", "#2d4a5e", "#2f5c5c", "#3e523e", "#5e5236"
        self.editor._textbox.tag_configure("h_part", background=c_part)
        self.editor._textbox.tag_configure("h_chapter", background=c_chapter)
        self.editor._textbox.tag_configure("h_section", background=c_section)
        self.editor._textbox.tag_configure("h_subsection", background=c_subsection)
        self.editor._textbox.tag_configure("h_subsubsection", background=c_subsubsection)

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_theme = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)
        self._style_treeview()
        self._update_highlight_colors()
        if hasattr(self.spell_checker, 'words_listbox'):
            bg = "#2b2b2b" if new_theme == "Dark" else "white"
            fg = "white" if new_theme == "Dark" else "black"
            try:
                self.spell_checker.words_listbox.config(bg=bg, fg=fg)
            except:
                pass
        bg = "#2b2b2b" if new_theme == "Dark" else "#e6e6e6"
        self.paned_main.configure(bg=bg)
        self.paned_editor_pdf.configure(bg=bg)

    def _open_spell_settings(self):
        self.spell_checker.open_settings_window()

    def _open_table_wizard(self):
        self._insert_table_template()

    def _clean_aux_files(self):
        if not self.project_dir: return
        count = 0
        for ext in [".aux", ".log", ".out", ".toc", ".bbl", ".blg", ".synctex.gz", ".fls", ".fdb_latexmk"]:
            for f in self.project_dir.rglob(f"*{ext}"):
                try:
                    f.unlink();
                    count += 1
                except:
                    pass
        self.log_line(f"Limpeza: {count} arquivos removidos.")

    def _open_table_wizard(self):
        d = TableInputDialog()
        res = d.get_dimensions()
        if res:
            r, c = res
            cols_str = "|" + "c|" * c
            latex = f"\\begin{{table}}[h]\n\t\\centering\n\t\\begin{{tabular}}{{{cols_str}}}\n\t\t\\hline\n"
            for _ in range(r):
                latex += "\t\t" + " & ".join([" "] * c) + " \\\\\n\t\t\\hline\n"
            latex += "\t\\end{tabular}\n\t\\caption{Legenda}\n\t\\label{tab:}\n\\end{table}"
            self.editor.insert("insert", latex)

    def _format_text(self, style):
        try:
            sel = self.editor.tag_ranges("sel")
            if not sel: return
            txt = self.editor.get(sel[0], sel[1])
            cmd = "\\textbf" if style == "bold" else "\\textit"
            self.editor.delete(sel[0], sel[1])
            self.editor.insert(sel[0], f"{cmd}{{{txt}}}")
        except:
            pass

    def _show_file_menu(self):
        self._popup_menu(self.menu_file, self.btn_file)

    def _show_options_menu(self):
        self._popup_menu(self.menu_options, self.btn_options)

    def _show_export_menu(self):
        self._popup_menu(self.menu_export, self.btn_export)

    def _popup_menu(self, menu, btn):
        try:
            x, y = btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _open_find_dialog(self):
        self.find_handler.show_dialog()

    def _create_project_flow(self):
        self._close_project()
        self.welcome_screen._show_create_options()

    def _finish_create_project(self, choice):
        project_folder = filedialog.askdirectory(title="Selecione pasta VAZIA")
        if not project_folder: return
        p = Path(project_folder)
        if any(p.iterdir()): messagebox.showerror("Erro", "A pasta deve estar vazia."); return

        if choice == "zip":
            zip_path = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")])
            if not zip_path: return
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(p)
                self.load_project_folder(p)
            except Exception as e:
                messagebox.showerror("Erro", f"{e}")
        elif choice == "blank":
            (p / "main.tex").write_text(
                "% LaThon Project\n\\documentclass{article}\n\\begin{document}\n\\section{Start}\nHello World!\n\\end{document}",
                encoding="utf-8")
            self.load_project_folder(p)

    def load_project_folder(self, folder_path):
        self.welcome_screen.grid_forget()
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        try:
            self.state('zoomed')
        except:
            self.attributes('-fullscreen', True)
        self.project_dir = folder_path
        self._save_recents(folder_path)
        self.file_manager.populate_tree()
        tex_files = list(self.project_dir.rglob("*.tex"))
        if not tex_files: messagebox.showerror("Erro", "Sem arquivos .tex."); return
        main_file = next((f for f in tex_files if f.name.lower() in ("main.tex", "root.tex")), tex_files[0])
        self._open_file(main_file)
        self.title(f"LaThon Editor - {self.project_dir.name}")
        self.compile_action()
        self.after(200, self._apply_layout_settings)

    def _close_project(self):
        if self.active_file: self._save_active_file()
        self.project_dir, self.active_file = None, None
        self.spell_checker.clear_state()
        self.file_manager.clear_tree_and_outline()
        self.find_handler.hide_dialog()
        self.editor.delete("1.0", "end")
        self.preview_label.destroy()
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Nenhum projeto aberto.")
        self.preview_label.pack(expand=True)
        self.preview_handler.pil_pdf_image = None
        self.highlight_chapters_active = False
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
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            self.active_file = file_path
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", text)
            self.log_line(f"Abriu: {self.active_file.name}")
            self.file_manager.update_file_outline()
            self._apply_syntax_highlighting()
            self._update_line_numbers()
            self.spell_checker.apply_spell_check()
            self.editor._textbox.edit_reset()
            self.editor.see("1.0")
        except Exception as e:
            messagebox.showerror("Erro ao Abrir", f"{e}")
            self.active_file = None

    def _set_auto_install_mode(self):
        if not self.latex_compiler: return
        try:
            compiler_path = Path(self.latex_compiler)
            miktex_config_path = compiler_path.parent / "miktex-config.exe"
            if miktex_config_path.exists():
                subprocess.run([str(miktex_config_path), 'set', '--user', 'AutoInstall=1'],
                               check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.log_line("Auto-instalação MiKTeX ativada.")
        except:
            pass

    def compile_action(self):
        if not self.project_dir: return
        if not self._save_active_file(): return
        self._set_auto_install_mode()
        tex_files = list(self.project_dir.rglob("*.tex"))
        main_file = next((f for f in tex_files if f.name.lower() in ("main.tex", "root.tex")), self.active_file)
        if not main_file or main_file.suffix.lower() != '.tex': messagebox.showerror("Erro",
                                                                                     "Arquivo principal não encontrado."); return
        self.log.configure(state="normal");
        self.log.delete('1.0', 'end');
        self.log.configure(state="disabled")
        self.log_line(f"Compilando: {main_file.name}")
        self.compile_button.configure(state="disabled", text="Compilando...", fg_color="gray")
        CompilerThread(self.project_dir, main_file.name, self.latex_compiler, self.queue).start()

    def on_compile_finished(self, success):
        if self.download_notification_window: self.download_notification_window.destroy(); self.download_notification_window = None
        self.compile_button.configure(state="normal", text="▶ Compile (Ctrl + S)", fg_color="#238636")
        if not self.project_dir: return
        main_file = next(
            (f for f in list(self.project_dir.rglob("*.tex")) if f.name.lower() in ("main.tex", "root.tex")),
            self.active_file)
        if not main_file: return
        pdf_path = self.project_dir / main_file.with_suffix(".pdf").name
        if success:
            self.log_line("\n--- SUCESSO ---")
            self.preview_handler.show_pdf_preview(pdf_path)
        else:
            self.log_line("\n--- FALHA ---")

    def export_pdf(self):
        if not self.project_dir: return
        main_file = next(
            (f for f in list(self.project_dir.rglob("*.tex")) if f.name.lower() in ("main.tex", "root.tex")),
            self.active_file)
        if not main_file: return
        pdf_path = self.project_dir / main_file.with_suffix(".pdf").name
        if not pdf_path.exists(): messagebox.showwarning("Aviso", "Compile o projeto primeiro."); return
        dest = filedialog.asksaveasfilename(title="Exportar PDF", initialfile=pdf_path.name, defaultextension=".pdf",
                                            filetypes=[("PDF", "*.pdf")])
        if dest:
            try:
                shutil.copy2(str(pdf_path), dest);
                messagebox.showinfo("Sucesso", "PDF Exportado.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def _export_project_as_zip(self):
        if not self.project_dir: return
        dest = filedialog.asksaveasfilename(title="Exportar ZIP", initialfile=f"{self.project_dir.name}.zip",
                                            defaultextension=".zip", filetypes=[("ZIP", "*.zip")])
        if dest:
            try:
                with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in self.project_dir.rglob('*'):
                        if f.resolve() == Path(dest).resolve(): continue
                        if f.suffix in {".aux", ".log", ".out", ".bbl",
                                        ".blg"} or f.name == "run_compiler.bat": continue
                        zf.write(f, f.relative_to(self.project_dir))
                messagebox.showinfo("Sucesso", "ZIP Exportado.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def log_line(self, text):
        try:
            self.log.configure(state="normal")
            self.log.insert("end", text + "\n")
            self.log.configure(state="disabled")
            self.log.see("end")
        except:
            pass

    def process_queue(self):
        try:
            msg = self.queue.get_nowait()
            if isinstance(msg, tuple):
                if msg[0] == "finished":
                    self.on_compile_finished(msg[1])
                elif msg[0] == "downloading_package" and not self.download_notification_window:
                    self.download_notification_window = ctk.CTkToplevel(self)
                    ctk.CTkLabel(self.download_notification_window, text="Baixando pacotes...").pack(padx=20, pady=20)
            else:
                self.log_line(str(msg))
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def _on_ctrl_s(self, event=None):
        self.compile_action()
        return "break"

    def _undo(self, event=None):
        try:
            self.editor._textbox.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def _redo(self, event=None):
        try:
            self.editor._textbox.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def _open_project_flow(self):
        file_path_str = filedialog.askopenfilename(filetypes=[("LaTeX", "*.tex")])
        if not file_path_str: return
        self.load_project_folder(Path(file_path_str).parent)

    def _style_treeview(self):
        style = ttk.Style(self)
        current = ctk.get_appearance_mode()
        if current == "Dark":
            bg = "#252526"
            fg = "white"
            sel_bg = "#37373d"
            heading_bg = "#333333"
            heading_fg = "gray"
        else:
            bg = "#f3f3f3"
            fg = "black"
            sel_bg = "#cce8ff"
            heading_bg = "#e1e1e1"
            heading_fg = "black"
        style.theme_use("clam")
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, borderwidth=0, rowheight=24,
                        font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", sel_bg)], foreground=[("selected", fg)])
        style.configure("Treeview.Heading", background=heading_bg, foreground=heading_fg, relief="flat")

        def tree_selection_fix(event):
            selected_item = self.tree.selection()
            for item in self.tree.get_children():
                def remove_tag(parent):
                    for child in self.tree.get_children(parent):
                        self.tree.item(child, tags=())
                        remove_tag(child)

                remove_tag(self.tree.get_children())
            if selected_item: self.tree.item(selected_item[0], tags=("selected",))

        self.tree.bind('<<TreeviewSelect>>', tree_selection_fix, add="+")
        self.tree.bind('<Button-1>', tree_selection_fix, add="+")

    def _select_word_by_double_click(self, event):
        try:
            cursor_index = self.editor._textbox.index(f"@{event.x},{event.y}")
            text_content = self.editor.get("1.0", "end-1c")
            flat_index = self.editor._textbox.count("1.0", cursor_index, "chars")[0]
            word_pattern = re.compile(r'(\w+)')
            match = None
            for m in word_pattern.finditer(text_content):
                if m.start() <= flat_index < m.end():
                    match = m
                    break
                elif flat_index == m.end():
                    if m.start() <= flat_index - 1 < m.end():
                        match = m
                        break
            self.editor._textbox.tag_remove("sel", "1.0", "end")
            if match:
                start_index_tk = self.editor._textbox.index(f"1.0 + {match.start()} chars")
                end_index_tk = self.editor._textbox.index(f"1.0 + {match.end()} chars")
                self.editor._textbox.tag_add("sel", start_index_tk, end_index_tk)
                return "break"
        except:
            pass
        return None

    def _sync_line_numbers_scroll(self, first_fraction):
        self.line_number_bar._textbox.yview_moveto(first_fraction)

    def _on_text_changed(self, event=None):
        self._update_line_numbers()
        self.editor.see("insert")
        self.editor.tag_remove("find_highlight", "1.0", "end")
        if self.outline_update_timer: self.after_cancel(self.outline_update_timer)
        self.outline_update_timer = self.after(1500, self.file_manager.update_file_outline)
        if self.syntax_highlight_timer: self.after_cancel(self.syntax_highlight_timer)
        self.syntax_highlight_timer = self.after(800, self._apply_syntax_highlighting)
        if self.spellcheck_timer: self.after_cancel(self.spellcheck_timer)
        self.spellcheck_timer = self.after(1000, self.spell_checker.apply_spell_check)

    def _switch_center_view(self, view_mode: str):
        if view_mode == 'image':
            self.editor_area_frame.grid_forget()
            self.image_viewer_container.grid(row=0, column=0, sticky="nsew")
        else:
            self.image_viewer_container.grid_forget()
            self.editor_area_frame.grid(row=0, column=0, sticky="nsew")

    def _show_main_editor(self):
        self.welcome_screen.grid_forget()
        self.main_frame.grid(row=0, column=0, sticky="nsew")

    def _update_line_numbers(self, event=None):
        line_count = self.editor.get("1.0", "end-1c").count("\n") + 1
        line_numbers_string = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_number_bar.configure(state="normal")
        self.line_number_bar.delete("1.0", "end")
        self.line_number_bar.insert("1.0", line_numbers_string)
        self.line_number_bar.configure(state="disabled")
        current_first_fraction = self.editor._textbox.yview()[0]
        self._sync_line_numbers_scroll(current_first_fraction)

    def _apply_syntax_highlighting(self):
        self.editor._textbox.tag_remove("command", "1.0", "end")
        self.editor._textbox.tag_remove("comment", "1.0", "end")
        self.editor._textbox.tag_remove("label", "1.0", "end")
        self.editor._textbox.tag_remove("file_path", "1.0", "end")
        try:
            text_content = self.editor.get("1.0", "end-1c")
        except:
            return
        command_pattern = re.compile(r'(\\[a-zA-Z]+)')
        for match in command_pattern.finditer(text_content):
            self.editor._textbox.tag_add("command", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
        label_pattern = re.compile(r'\\(ref|cite|label|eqref|nameref|autoref)\s*\{(.*?)\}')
        for match in label_pattern.finditer(text_content):
            self.editor._textbox.tag_add("label", f"1.0 + {match.start(2)} chars", f"1.0 + {match.end(2)} chars")
        file_path_pattern = re.compile(r'\\includegraphics(\[[^\]]*\])?\s*\{(.*?)\}')
        for match in file_path_pattern.finditer(text_content):
            self.editor._textbox.tag_add("file_path", f"1.0 + {match.start(2)} chars", f"1.0 + {match.end(2)} chars")
        comment_pattern = re.compile(r'(%.*?)$', re.MULTILINE)
        for match in comment_pattern.finditer(text_content):
            self.editor._textbox.tag_add("comment", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
        if self.highlight_chapters_active: self._apply_chapter_highlighting()

    def _toggle_chapter_highlighting(self):
        self.highlight_chapters_active = not self.highlight_chapters_active
        if self.highlight_chapters_active:
            self._apply_chapter_highlighting()
        else:
            self._remove_chapter_highlighting()

    def _apply_chapter_highlighting(self):
        self._remove_chapter_highlighting()
        try:
            text_content = self.editor.get("1.0", "end-1c")
        except:
            return
        pattern = re.compile(r'\\(part|chapter|section|subsection|subsubsection)(\*?)\s*\{', re.MULTILINE)
        for match in pattern.finditer(text_content):
            command = match.group(1)
            line_start_idx = f"1.0 + {match.start()} chars linestart"
            line_end_idx = f"1.0 + {match.start()} chars lineend"
            tag = "h_section"
            if command == "part":
                tag = "h_part"
            elif command == "chapter":
                tag = "h_chapter"
            elif command == "section":
                tag = "h_section"
            elif command == "subsection":
                tag = "h_subsection"
            elif command == "subsubsection":
                tag = "h_subsubsection"
            self.editor._textbox.tag_add(tag, line_start_idx, line_end_idx)

    def _remove_chapter_highlighting(self):
        self.editor._textbox.tag_remove("h_part", "1.0", "end")
        self.editor._textbox.tag_remove("h_chapter", "1.0", "end")
        self.editor._textbox.tag_remove("h_section", "1.0", "end")
        self.editor._textbox.tag_remove("h_subsection", "1.0", "end")
        self.editor._textbox.tag_remove("h_subsubsection", "1.0", "end")

    def on_closing(self):
        if self.project_dir:
            self._save_active_file()
        self.destroy()