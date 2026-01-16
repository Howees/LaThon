import os
import shutil
import re
from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

# Importa o FixedInputDialog e o ModernMenu
from ui_widgets import CustomDialog, ModernMenu, FixedInputDialog

IGNORED_EXTENSIONS = {
    ".aux", ".log", ".out", ".toc", ".lof", ".lot", ".bbl", ".blg",
    ".bak", ".nav", ".snm", ".vrb", ".gz", ".synctex.gz", ".fls",
    ".fdb_latexmk", ".xml", ".run.xml",
    ".msc", ".glo", ".idx", ".ist", ".ilg", ".dvi", ".bcf", ".spl"
}
IGNORED_NAMES = {"__pycache__", "run_compiler.bat"}


class FileManager:
    def __init__(self, app: 'MiniOverleaf', tree_widget: ttk.Treeview,
                 outline_frame: ctk.CTkScrollableFrame, tree_menu: tk.Menu):
        self.app = app
        self.tree = tree_widget
        self.outline_frame = outline_frame

        self.context_menu = ModernMenu(app, width=180)
        self.tree.path_map = {}
        self.rename_entry = None
        self.rename_item_id = None

        self.root_icon = None
        self.folder_icon = None
        self.folder_empty_icon = None
        self.tex_icon = None
        self.bib_icon = None
        self.image_icon = None
        self.file_icon = None
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
            icon_path = Path(data['file'])
            icon_attr = f"{name}_icon"
            try:
                pil_img = None
                if icon_path.exists():
                    pil_img = Image.open(icon_path).resize(size, Image.Resampling.LANCZOS)
                else:
                    pil_img = Image.new('RGB', size, color=data['color'])
                if pil_img:
                    photo_img = ImageTk.PhotoImage(pil_img)
                    setattr(self, icon_attr, photo_img)
                    self.image_references.append(photo_img)
                else:
                    setattr(self, icon_attr, None)
            except:
                setattr(self, icon_attr, None)

    def populate_tree(self):
        self._cancel_inline_rename()
        for i in self.tree.get_children(): self.tree.delete(i)

        if not self.app.project_dir: return
        self.tree.path_map = {}

        def _walk_dir(parent_id, path):
            filtered = []
            try:
                for p in path.iterdir():
                    is_ignored = p.name in IGNORED_NAMES or p.name.startswith('.')
                    is_ignored_ext = p.is_file() and p.suffix.lower() in IGNORED_EXTENSIONS
                    if is_ignored or is_ignored_ext: continue

                    # Filtro PDF inteligente
                    if p.is_file() and p.suffix.lower() == ".pdf":
                        if p.parent.resolve() == self.app.project_dir.resolve(): continue

                    filtered.append(p)
                items = sorted(filtered, key=lambda p: (p.is_file(), p.name.lower()))
            except:
                return

            for p in items:
                icon = self.file_icon
                is_folder = p.is_dir()
                if is_folder:
                    has_children = any(x for x in p.iterdir() if x.name not in IGNORED_NAMES)
                    icon = self.folder_icon if has_children else self.folder_empty_icon
                elif p.is_file():
                    ext = p.suffix.lower()
                    if ext in [".tex", ".txt"]:
                        icon = self.tex_icon
                    elif ext == ".bib":
                        icon = self.bib_icon
                    elif ext in [".png", ".jpg", ".jpeg", ".pdf"]:
                        icon = self.image_icon

                dot_value = "⋮" if is_folder else ""
                oid = self.tree.insert(parent_id, "end", text=p.name, open=False,
                                       image=icon if icon else '', values=(dot_value,))
                self.tree.path_map[oid] = p
                if is_folder: _walk_dir(oid, p)

        root_oid = self.tree.insert("", "end", text=self.app.project_dir.name, open=True,
                                    image=self.root_icon if self.root_icon else '', values=("⋮",))
        self.tree.path_map[root_oid] = self.app.project_dir
        _walk_dir(root_oid, self.app.project_dir)

    def clear_tree_and_outline(self):
        self._cancel_inline_rename()
        for i in self.tree.get_children(): self.tree.delete(i)
        for w in self.outline_frame.winfo_children(): w.destroy()
        self.tree.path_map = {}

    def on_tree_select(self, event):
        if not self.tree.selection(): return
        selected_id = self.tree.selection()[0]
        file_path = self.tree.path_map.get(selected_id)

        if file_path == self.app.project_dir:
            self.tree.selection_remove(selected_id)
            return

        if not file_path or not file_path.is_file(): return

        text_ext = [".tex", ".txt", ".bib"]
        img_ext = [".png", ".jpg", ".jpeg", ".pdf"]
        if file_path.suffix.lower() in text_ext:
            self.app._open_file(file_path)
        elif file_path.suffix.lower() in img_ext:
            if file_path.suffix == ".pdf":
                self.app.preview_handler.show_pdf_in_editor_panel(file_path)
            else:
                self.app.preview_handler.show_image_in_editor_panel(file_path)

    def on_left_click(self, event):
        self._cancel_inline_rename()
        region = self.tree.identify_region(event.x, event.y)
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item_id: return

        if column == "#1":
            values = self.tree.item(item_id, "values")
            if values and values[0] == "⋮":
                self.tree.selection_set(item_id)
                self.open_options_menu(event, item_id)
                return "break"

        sel = self.tree.selection()
        if sel and sel[0] == item_id and (region == "tree" or column == "#0"):
            path = self.tree.path_map.get(item_id)
            if path == self.app.project_dir: return
            self.app.after(400, lambda: self._check_inline_rename_trigger(item_id))

    def _check_inline_rename_trigger(self, item_id):
        sel = self.tree.selection()
        if sel and sel[0] == item_id:
            self.start_inline_rename(item_id)

    def open_options_menu(self, event, item_id):
        path = self.tree.path_map.get(item_id)
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
        path = self.tree.path_map.get(item_id)
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
        new_name = self.rename_entry.get().strip()
        old_path = self.tree.path_map.get(self.rename_item_id)
        self.rename_entry.destroy()
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
        if self.rename_entry:
            self.rename_entry.destroy()
            self.rename_entry = None
        self.rename_item_id = None

    # --- Funções de Ação Padrão (AGORA USANDO O DIÁLOGO FIXO) ---
    def create_new_file(self, parent):
        # Aqui está a mudança: FixedInputDialog
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
        # Aqui está a mudança: FixedInputDialog
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
        p = self.tree.path_map.get(iid)
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
        pat = re.compile(r'^\\(part|chapter|section|subsection|subsubsection)\*?\s*\{(.*?)\}', re.MULTILINE | re.DOTALL)
        for m in pat.finditer(content):
            cmd, title = m.groups()
            title = " ".join(title.strip().split())
            line = content.count('\n', 0, m.start()) + 1
            indent = 0
            if cmd in ["subsection", "chapter"]:
                indent = 15
            elif cmd == "subsubsection":
                indent = 30
            disp = title if len(title) <= 24 else title[:21] + "..."
            btn = ctk.CTkButton(self.outline_frame, text=disp, anchor="w", fg_color="transparent",
                                text_color=("gray10", "gray90"), hover_color=("gray80", "gray25"),
                                command=lambda l=line: self.on_outline_click(l))
            btn.pack(anchor="w", padx=(indent, 0), pady=1, fill="x")

    def on_outline_click(self, l):
        self.app._switch_center_view('editor')
        self.app.editor.see(f"{l}.0")
        self.app.editor._textbox.focus_set()
        self.app.editor._textbox.mark_set("insert", f"{l}.0")