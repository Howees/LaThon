import os
import shutil
import re
from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

from lathon.ui.widgets.modern_menu import ModernMenu
from lathon.ui.widgets.fixed_input import FixedInputDialog

import sys


def resource_path(relative_path):
    """ Encontra o caminho dos arquivos dentro do EXE ou em modo Dev """
    try:
        # O PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    # Forçamos a conversão para str para eliminar o aviso do editor
    return str(os.path.join(base_path, relative_path))

IGNORED_EXTENSIONS = {".aux", ".log", ".out", ".toc", ".lof", ".lot", ".bbl", ".blg", ".bak", ".nav", ".snm", ".vrb",
                      ".gz", ".synctex.gz", ".fls", ".fdb_latexmk", ".xml", ".run.xml", ".msc", ".glo", ".idx", ".ist",
                      ".ilg", ".dvi", ".bcf", ".spl"}
IGNORED_NAMES = {"__pycache__", "run_compiler.bat"}


class FilePanel(ctk.CTkFrame):
    """Componente Visual: O Painel Esquerdo que gerencia os arquivos do projeto."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=("gray95", "#252526"), corner_radius=0, **kwargs)
        self.app = app

        # --- CONSTRUÇÃO DA INTERFACE ---
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, show="tree headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        outline_header = ctk.CTkFrame(self, height=25, fg_color=("gray85", "#333333"), corner_radius=0)
        outline_header.grid(row=1, column=0, sticky="ew")
        ctk.CTkLabel(outline_header, text="ESTRUTURA", font=("Segoe UI", 11, "bold"),
                     text_color=("gray30", "gray60")).pack(side="left", padx=5)

        scroll_conf = {"scrollbar_button_color": ("#bfbfbf", "#7a7a7a"),
                       "scrollbar_button_hover_color": ("#a6a6a6", "#a0a0a0")}
        self.outline_frame = ctk.CTkScrollableFrame(self, label_text="", fg_color="transparent", **scroll_conf)
        self.outline_frame.grid(row=2, column=0, sticky="nsew")

        # --- LÓGICA E ESTADO ---
        self.tree_menu = tk.Menu(self, tearoff=0)
        self.context_menu = ModernMenu(app, width=180)
        self.path_map = {}
        self.rename_entry = None
        self.rename_item_id = None
        self.image_references = []
        self._load_icons()

        self.tree.configure(columns=("options",), displaycolumns=("options",))
        self.tree.column("#0", width=220, anchor="w")
        self.tree.heading("#0", text="Arquivos", anchor="w")
        self.tree.column("options", width=30, minwidth=30, stretch=False, anchor="center")
        self.tree.heading("options", text="")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Delete>", self.on_delete_key)
        self.tree.bind("<Button-1>", self.on_left_click, add="+")

        self.bind("<Configure>", self._on_panel_resize)
        self._resize_timer = None
        self._last_panel_width = 0

    def _on_panel_resize(self, event):
        if abs(self._last_panel_width - event.width) > 5:
            self._last_panel_width = event.width
            if self._resize_timer: self.app.after_cancel(self._resize_timer)
            self._resize_timer = self.app.after(150, self.update_file_outline)

    def _load_icons(self):
        self.image_references = []
        ICON_MAP = {
            'root': {'file': 'icones/project_root.png', 'color': '#008CBA'},
            'folder': {'file': 'icones/folder.png', 'color': '#FFD700'},
            'folder_empty': {'file': 'icones/folder_empty.png', 'color': '#E0E0E0'},
            'tex': {'file': 'icones/tex.png', 'color': '#E65100'},
            'bib': {'file': 'icones/bib.png', 'color': '#1E88E5'},
            'image': {'file': 'icones/image.png', 'color': '#4CAF50'},
            'file': {'file': 'icones/file.png', 'color': '#9E9E9E'}
        }
        size = (18, 18)
        for name, data in ICON_MAP.items():
            icon_path = Path(resource_path(data['file']))
            icon_attr = f"{name}_icon"
            try:
                pil_img = Image.open(icon_path).resize(size,
                                                       Image.Resampling.LANCZOS) if icon_path.exists() else Image.new(
                    'RGB', size, color=data['color'])
                photo_img = ImageTk.PhotoImage(pil_img)
                setattr(self, icon_attr, photo_img)
                self.image_references.append(photo_img)
            except:
                setattr(self, icon_attr, None)

    def populate_tree(self):
        self._cancel_inline_rename()
        for i in self.tree.get_children(): self.tree.delete(i)
        if not self.app.project_dir: return
        self.path_map = {}

        def _walk_dir(parent_id, path):
            filtered = []
            try:
                for p in path.iterdir():
                    if p.name in IGNORED_NAMES or p.name.startswith('.') or (
                            p.is_file() and p.suffix.lower() in IGNORED_EXTENSIONS): continue
                    if p.is_file() and p.suffix.lower() == ".pdf" and p.parent.resolve() == self.app.project_dir.resolve(): continue
                    filtered.append(p)
                items = sorted(filtered, key=lambda p: (p.is_file(), p.name.lower()))
            except:
                return

            for p in items:
                icon = self.file_icon
                is_folder = p.is_dir()
                if is_folder:
                    icon = self.folder_icon if any(
                        x for x in p.iterdir() if x.name not in IGNORED_NAMES) else self.folder_empty_icon
                elif p.is_file():
                    ext = p.suffix.lower()
                    if ext in [".tex", ".txt"]:
                        icon = self.tex_icon
                    elif ext == ".bib":
                        icon = self.bib_icon
                    elif ext in [".png", ".jpg", ".jpeg", ".pdf"]:
                        icon = self.image_icon

                oid = self.tree.insert(parent_id, "end", text=p.name, open=False, image=icon if icon else '',
                                       values=("⋮" if is_folder else "",))
                self.path_map[oid] = p
                if is_folder: _walk_dir(oid, p)

        root_oid = self.tree.insert("", "end", text=self.app.project_dir.name, open=True,
                                    image=self.root_icon if self.root_icon else '', values=("⋮",))
        self.path_map[root_oid] = self.app.project_dir
        _walk_dir(root_oid, self.app.project_dir)

    def clear_tree_and_outline(self):
        self._cancel_inline_rename()
        for i in self.tree.get_children(): self.tree.delete(i)
        for w in self.outline_frame.winfo_children(): w.destroy()
        self.path_map = {}

    def on_tree_select(self, event):
        if not self.tree.selection(): return
        selected_id = self.tree.selection()[0]
        file_path = self.path_map.get(selected_id)

        if file_path == self.app.project_dir: self.tree.selection_remove(selected_id); return
        if not file_path or not file_path.is_file(): return

        ext = file_path.suffix.lower()
        if ext in [".tex", ".txt", ".bib"]:
            self.app._open_file(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".pdf"]:
            if ext == ".pdf":
                self.app.preview_panel.show_pdf_in_editor_panel(file_path)
            else:
                self.app.preview_panel.show_image_in_editor_panel(file_path)

    def on_left_click(self, event):
        self._cancel_inline_rename()
        region, item_id, column = self.tree.identify_region(event.x, event.y), self.tree.identify_row(
            event.y), self.tree.identify_column(event.x)
        if not item_id: return

        if column == "#1":
            values = self.tree.item(item_id, "values")
            if values and values[0] == "⋮":
                self.tree.selection_set(item_id)
                self.open_options_menu(event, item_id)
                return "break"

        sel = self.tree.selection()
        if sel and sel[0] == item_id and (region == "tree" or column == "#0"):
            if self.path_map.get(item_id) == self.app.project_dir: return
            self.app.after(400, lambda: self._check_inline_rename_trigger(item_id))

    def _check_inline_rename_trigger(self, item_id):
        sel = self.tree.selection()
        if sel and sel[0] == item_id: self.start_inline_rename(item_id)

    def open_options_menu(self, event, item_id):
        path = self.path_map.get(item_id)
        if not path: return
        self.context_menu.clear()

        if path.is_dir():
            self.context_menu.add_command("📄 Novo Arquivo", lambda: self.create_new_file(path))
            self.context_menu.add_command("📁 Nova Pasta", lambda: self.create_new_folder(path))
            self.context_menu.add_command("📥 Importar...", lambda: self.add_file_to_project(path))
            self.context_menu.add_separator()
            if path != self.app.project_dir:
                self.context_menu.add_command("✏ Renomear", lambda: self.start_inline_rename(item_id))
                self.context_menu.add_command("❌ Excluir", lambda: self.delete_item(item_id, path),
                                              text_color="#ff5555", hover_color="#502020")

        self.context_menu.popup(event.x_root, event.y_root)

    def start_inline_rename(self, item_id):
        if self.rename_entry: self._cancel_inline_rename()
        self.rename_item_id = item_id
        path = self.path_map.get(item_id)
        if not path: return
        try:
            x, y, w, h = self.tree.bbox(item_id, column="#0")
        except:
            return
        if h == 0: return

        self.rename_entry = ctk.CTkEntry(self.tree, height=h, width=w, font=("Segoe UI", 13))
        self.rename_entry.place(x=x, y=y)
        self.rename_entry.insert(0, path.name)
        self.rename_entry.select_range(0, 'end')
        self.rename_entry.focus_set()
        self.rename_entry.bind("<Return>", self._finish_inline_rename)
        self.rename_entry.bind("<Escape>", lambda e: self._cancel_inline_rename())
        self.rename_entry.bind("<FocusOut>", lambda e: self._finish_inline_rename(e))

    def _finish_inline_rename(self, event=None):
        if not self.rename_entry: return
        new_name, old_path = self.rename_entry.get().strip(), self.path_map.get(self.rename_item_id)
        self.rename_entry.destroy();
        self.rename_entry = None

        if not new_name or not old_path or new_name == old_path.name: return
        new_path = old_path.parent / new_name
        if new_path.exists(): messagebox.showerror("Erro", "Nome já existe."); return

        try:
            os.rename(old_path, new_path)
            self.app.log_line(f"Renomeado: {old_path.name} -> {new_name}")
            self.populate_tree()
            if self.app.active_file == old_path: self.app.active_file = new_path
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _cancel_inline_rename(self):
        if self.rename_entry: self.rename_entry.destroy(); self.rename_entry = None
        self.rename_item_id = None

    def create_new_file(self, parent):
        d = FixedInputDialog(text="Nome do arquivo:", title="Novo Arquivo")
        n = d.get_input()
        if not n: return
        p = parent / n
        if p.exists(): messagebox.showerror("Erro", "Já existe."); return
        try:
            p.touch(); self.populate_tree()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def create_new_folder(self, parent):
        d = FixedInputDialog(text="Nome da pasta:", title="Nova Pasta")
        n = d.get_input()
        if not n: return
        p = parent / n
        if p.exists(): messagebox.showerror("Erro", "Já existe."); return
        try:
            p.mkdir(); self.populate_tree()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_delete_key(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        iid = sel[0]
        p = self.path_map.get(iid)
        if p and p != self.app.project_dir: self.delete_item(iid, p)
        return "break"

    def delete_item(self, iid, p):
        if not messagebox.askyesno("Excluir", f"Apagar '{p.name}'?"): return
        try:
            if p.is_file():
                if self.app.active_file == p: self.app.active_file = None; self.app.editor.delete("1.0", "end")
                os.remove(p)
            else:
                shutil.rmtree(p)
            self.populate_tree()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def add_file_to_project(self, target):
        files = filedialog.askopenfilenames()
        if not files: return
        for f in files:
            try:
                shutil.copy2(f, target)
            except:
                pass
        self.populate_tree()

    def update_file_outline(self):
        for w in self.outline_frame.winfo_children(): w.destroy()
        if not self.app.active_file: return
        try:
            content = self.app.editor.get("1.0", "end-1c")
        except:
            return

        self.outline_frame.update_idletasks()
        panel_width = self.outline_frame.winfo_width()
        if panel_width <= 10: panel_width = 200

        pat = re.compile(r'^\\(part|chapter|section|subsection|subsubsection)\*?\s*\{(.*?)\}', re.MULTILINE | re.DOTALL)
        for m in pat.finditer(content):
            cmd, title = m.groups()
            title = " ".join(title.strip().split())
            line = content.count('\n', 0, m.start()) + 1
            indent = 15 if cmd in ["subsection", "chapter"] else (30 if cmd == "subsubsection" else 0)

            max_chars = max(10, int((panel_width - indent - 40) / 6.5))
            disp = title[:max_chars - 3] + "..." if len(title) > max_chars else title

            btn = ctk.CTkButton(self.outline_frame, text=disp, anchor="w", fg_color="transparent",
                                text_color=("gray10", "gray90"), hover_color=("gray80", "gray25"),
                                command=lambda l=line: self.on_outline_click(l))
            btn.pack(anchor="w", padx=(indent, 0), pady=1, fill="x")

    def on_outline_click(self, l):
        self.app._switch_center_view('editor')
        self.app.editor.see(f"{l}.0")
        self.app.editor.focus_set()
        self.app.editor.mark_set("insert", f"{l}.0")

    def style_treeview(self):
        style = ttk.Style(self)
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg, fg, sel_bg, h_bg, h_fg = ("#252526", "white", "#37373d", "#333333", "gray") if is_dark else (
        "#f3f3f3", "black", "#cce8ff", "#e1e1e1", "black")
        style.theme_use("clam")
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, borderwidth=0, rowheight=24,
                        font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", sel_bg)], foreground=[("selected", fg)])
        style.configure("Treeview.Heading", background=h_bg, foreground=h_fg, relief="flat")