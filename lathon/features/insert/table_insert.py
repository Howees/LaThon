import os
from tkinter import filedialog, messagebox
from PIL import Image
import customtkinter as ctk
from lathon.ui.widgets.tooltip import ToolTip

from lathon.ui.widgets.base_modal import BaseModal
from lathon.ui.design import Colors, Fonts, resource_path, Icons


class BaseTableDialog(BaseModal):
    # MUDANÇA: Inseridos default_r e default_c no construtor
    def __init__(self, master_app, title, default_r, default_c, default_w, default_h, min_w, min_h, default_label="tab:"):
        super().__init__(master_app, title, 1050, 750)

        self.default_w = default_w
        self.default_h = default_h
        self.min_w = min_w
        self.min_h = min_h

        # Agora usa os valores repassados pelas classes filhas
        self.current_r = default_r
        self.current_c = default_c
        self.col_widths = [self.default_w] * 20
        self.row_heights = [self.default_h] * 30

        self.is_select_all = True
        self.selected_rows = set()
        self.selected_cols = set()

        self.col_indicators = []
        self.row_indicators = []
        self.entries = []

        self.header_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        self.header_frame.pack(side="top", fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(self.header_frame, text=title, font=Fonts.UI_TITLE).pack(side="left")

        self.controls_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.controls_frame.pack(side="right")

        self._build_extra_header()

        self.entry_rows, self.entry_h = self._build_counter_and_size(
            self.controls_frame, "Linhas:", self.current_r, self._change_rows, self._apply_r_direct, "Alt:",
            self._apply_h
        )
        ctk.CTkFrame(self.controls_frame, width=1, height=20, fg_color=Colors.BORDER).pack(side="left", padx=15)
        self.entry_cols, self.entry_w = self._build_counter_and_size(
            self.controls_frame, "Colunas:", self.current_c, self._change_cols, self._apply_c_direct, "Larg:",
            self._apply_w
        )

        # --- FAIXA DE FERRAMENTAS ---
        self.toolbar_frame = ctk.CTkFrame(self.border_frame, fg_color=Colors.BG_SIDEBAR, corner_radius=6)
        self.toolbar_frame.pack(side="top", fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(self.toolbar_frame, text="Alinhamento:", font=Fonts.UI_BOLD).pack(side="left", padx=(10, 5), pady=8)

        self.valign_combo = ctk.CTkOptionMenu(self.toolbar_frame, values=["Topo", "Meio", "Base"], width=90, fg_color=Colors.BG_MAIN, button_color=Colors.THON)
        self.valign_combo.set("Meio")
        self.valign_combo.pack(side="left", padx=(0, 5))

        self.halign_combo = ctk.CTkOptionMenu(self.toolbar_frame, values=["Esquerda", "Centro", "Direita"], width=90, fg_color=Colors.BG_MAIN, button_color=Colors.THON)
        self.halign_combo.set("Centro")
        self.halign_combo.pack(side="left")

        ctk.CTkFrame(self.toolbar_frame, width=1, height=20, fg_color=Colors.BORDER).pack(side="left", padx=15)

        # OS 11 ESTILOS VISUAIS
        estilos = [
            "Grade", "Grade Dupla", "Horizontais", "Horizontais Duplas",
            "Booktabs", "Booktabs Duplo", "Zebrada", "Zebrada + Grade",
            "Cabeçalho Destacado", "Zebrada + Cabeçalho", "Nenhuma"
        ]
        ctk.CTkLabel(self.toolbar_frame, text="Estilo Visual:", font=Fonts.UI_BOLD).pack(side="left", padx=(0, 5))
        self.border_combo = ctk.CTkOptionMenu(self.toolbar_frame, values=estilos, width=180, fg_color=Colors.BG_MAIN, button_color=Colors.THON)
        self.border_combo.set("Grade")
        self.border_combo.pack(side="left", padx=(0, 15))

        # --- RODAPÉ ---
        footer_container = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        footer_container.pack(side="bottom", fill="x", pady=(5, 20))

        leg_f = ctk.CTkFrame(footer_container, fg_color="transparent")
        leg_f.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(leg_f, text="Legenda:", width=80, anchor="e").pack(side="left")
        self.caption = ctk.CTkEntry(leg_f, justify="left")
        self.caption.pack(side="left", fill="x", expand=True, padx=10)

        lbl_f = ctk.CTkFrame(footer_container, fg_color="transparent")
        lbl_f.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(lbl_f, text="Label:", width=80, anchor="e").pack(side="left")
        ctk.CTkLabel(lbl_f, text=default_label, text_color=Colors.TEXT_MUTED).pack(side="left", padx=(10, 2))
        self.label = ctk.CTkEntry(lbl_f, justify="left")
        self.label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_f = ctk.CTkFrame(footer_container, fg_color="transparent")
        btn_f.pack(pady=10)
        ctk.CTkButton(btn_f, text="Cancelar", width=80, fg_color="transparent", border_width=1, text_color=Colors.TEXT_NORMAL, command=self._close_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Inserir Tabela", width=80, command=self._on_ok).pack(side="left", padx=5)

        self.grid_container = ctk.CTkFrame(self.border_frame, fg_color=Colors.BG_SIDEBAR, border_width=1, border_color=Colors.BORDER)
        self.grid_container.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 5))
        self.grid_container.bind("<Button-1>", self._deselect_all)

        self.update_idletasks()
        self._draw_grid()

    def _build_extra_header(self): pass
    def _create_cell(self, parent, r, c, w, h, initial_data): pass
    def _extract_cell_data(self, cell): pass
    def _on_ok(self): pass

    def _build_counter_and_size(self, parent, text, initial_val, callback_count, callback_direct, text_size, callback_size):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left")
        ctk.CTkLabel(f, text=text, font=Fonts.UI).pack(side="left", padx=(0, 5))
        btn_style = {"width": 24, "height": 24, "font": Fonts.UI_BOLD, "fg_color": Colors.BG_MAIN, "text_color": Colors.TEXT_NORMAL, "hover_color": Colors.BTN_HOVER, "border_width": 1, "border_color": Colors.BORDER}
        ctk.CTkButton(f, text="-", command=lambda: callback_count(-1), **btn_style).pack(side="left")
        count_entry = ctk.CTkEntry(f, width=35, height=24, font=Fonts.UI_BOLD, justify="center")
        count_entry.insert(0, str(initial_val))
        count_entry.pack(side="left", padx=2)
        count_entry.bind("<Return>", callback_direct)
        count_entry.bind("<FocusOut>", callback_direct)
        ctk.CTkButton(f, text="+", command=lambda: callback_count(1), **btn_style).pack(side="left")
        ctk.CTkLabel(f, text=text_size, font=Fonts.UI).pack(side="left", padx=(15, 5))
        size_entry = ctk.CTkEntry(f, width=45, height=24, font=Fonts.UI, justify="center")
        size_entry.pack(side="left")
        size_entry.bind("<Return>", callback_size)
        size_entry.bind("<FocusOut>", callback_size)
        return count_entry, size_entry

    def _apply_r_direct(self, event=None):
        try: val = int(self.entry_rows.get())
        except ValueError:
            self.entry_rows.delete(0, 'end'); self.entry_rows.insert(0, str(self.current_r)); return
        delta = val - self.current_r
        if delta != 0: self._change_rows(delta)

    def _apply_c_direct(self, event=None):
        try: val = int(self.entry_cols.get())
        except ValueError:
            self.entry_cols.delete(0, 'end'); self.entry_cols.insert(0, str(self.current_c)); return
        delta = val - self.current_c
        if delta != 0: self._change_cols(delta)

    def _update_size_entries(self):
        tgt_rows = list(self.selected_rows) if self.selected_rows else list(range(self.current_r))
        h_set = set(self.row_heights[r] for r in tgt_rows)
        tgt_cols = list(self.selected_cols) if self.selected_cols else list(range(self.current_c))
        w_set = set(self.col_widths[c] for c in tgt_cols)

        self.entry_h.configure(state="normal", fg_color=Colors.BG_MAIN, text_color=Colors.TEXT_NORMAL)
        self.entry_w.configure(state="normal", fg_color=Colors.BG_MAIN, text_color=Colors.TEXT_NORMAL)
        self.entry_h.delete(0, 'end')
        if len(h_set) == 1: self.entry_h.insert(0, str(list(h_set)[0]))
        elif len(h_set) > 1: self.entry_h.insert(0, "---")
        self.entry_w.delete(0, 'end')
        if len(w_set) == 1: self.entry_w.insert(0, str(list(w_set)[0]))
        elif len(w_set) > 1: self.entry_w.insert(0, "---")

        if self.is_select_all: pass
        elif self.selected_rows and not self.selected_cols:
            self.entry_w.configure(state="disabled", fg_color=Colors.BG_SIDEBAR, text_color=Colors.TEXT_MUTED)
        elif self.selected_cols and not self.selected_rows:
            self.entry_h.configure(state="disabled", fg_color=Colors.BG_SIDEBAR, text_color=Colors.TEXT_MUTED)

    def _apply_h(self, event=None):
        val_str = self.entry_h.get()
        if val_str == "---" or not val_str: return
        try: val = max(self.min_h, int(val_str))
        except ValueError: self._update_size_entries(); return
        tgt_rows = list(self.selected_rows) if self.selected_rows else list(range(self.current_r))
        max_h = self.grid_container.winfo_height() - 10
        current_other_h = sum(self.row_heights[r] for r in range(self.current_r) if r not in tgt_rows)
        avail = max_h - current_other_h - (self.current_r * 2) - 15
        if avail < len(tgt_rows) * self.min_h: self._update_size_entries(); return
        val = min(val, avail // len(tgt_rows))
        for r in tgt_rows: self.row_heights[r] = val
        self._draw_grid()

    def _apply_w(self, event=None):
        val_str = self.entry_w.get()
        if val_str == "---" or not val_str: return
        try: val = max(self.min_w, int(val_str))
        except ValueError: self._update_size_entries(); return
        tgt_cols = list(self.selected_cols) if self.selected_cols else list(range(self.current_c))
        max_w = self.grid_container.winfo_width() - 10
        current_other_w = sum(self.col_widths[c] for c in range(self.current_c) if c not in tgt_cols)
        avail = max_w - current_other_w - (self.current_c * 2) - 15
        if avail < len(tgt_cols) * self.min_w: self._update_size_entries(); return
        val = min(val, avail // len(tgt_cols))
        for c in tgt_cols: self.col_widths[c] = val
        self._draw_grid()

    def _select_all(self, event=None):
        self.is_select_all = not self.is_select_all
        if self.is_select_all:
            self.selected_rows.clear(); self.selected_cols.clear()
        self._refresh_indicators(); self._update_size_entries()

    def _deselect_all(self, event=None):
        self.is_select_all = True
        self.selected_rows.clear(); self.selected_cols.clear()
        self._refresh_indicators(); self._update_size_entries()

    def _toggle_col(self, c, multi=False):
        self.is_select_all = False
        if not multi: self.selected_cols.clear(); self.selected_rows.clear()
        if c in self.selected_cols: self.selected_cols.remove(c)
        else: self.selected_cols.add(c)
        if not self.selected_cols and not self.selected_rows: self.is_select_all = True
        self._refresh_indicators(); self._update_size_entries()

    def _toggle_row(self, r, multi=False):
        self.is_select_all = False
        if not multi: self.selected_rows.clear(); self.selected_cols.clear()
        if r in self.selected_rows: self.selected_rows.remove(r)
        else: self.selected_rows.add(r)
        if not self.selected_cols and not self.selected_rows: self.is_select_all = True
        self._refresh_indicators(); self._update_size_entries()

    def _refresh_indicators(self):
        if hasattr(self, 'corner_btn'):
            self.corner_btn.configure(fg_color=Colors.THON if self.is_select_all else Colors.TEXT_MUTED)
        for c, ind in enumerate(self.col_indicators):
            ind.configure(fg_color=Colors.THON if (c in self.selected_cols and not self.is_select_all) else Colors.BTN_HOVER)
        for r, ind in enumerate(self.row_indicators):
            ind.configure(fg_color=Colors.THON if (r in self.selected_rows and not self.is_select_all) else Colors.BTN_HOVER)

    def _change_rows(self, delta):
        if delta == 0: return
        max_h = self.grid_container.winfo_height() - 10
        if max_h < 100: max_h = 700
        target_r = self.current_r + delta
        if target_r < 1: target_r = 1
        if target_r > 30: target_r = 30

        if target_r > self.current_r:
            for i in range(self.current_r, target_r): self.row_heights[i] = self.default_h
            added_count = target_r - self.current_r
            current_total_h = sum(self.row_heights[:self.current_r]) + (self.current_r * 2) + 15
            avail = max_h - current_total_h
            if avail < added_count * (self.default_h + 2):
                allowed = int(max(0, avail // (self.default_h + 2)))
                target_r = self.current_r + allowed

        if target_r != self.current_r:
            self.current_r = target_r
            self.selected_rows = {r for r in self.selected_rows if r < self.current_r}
            self._draw_grid()

        self.entry_rows.delete(0, 'end'); self.entry_rows.insert(0, str(self.current_r))

    def _change_cols(self, delta):
        if delta == 0: return
        max_w = self.grid_container.winfo_width() - 10
        if max_w < 100: max_w = 1000
        target_c = self.current_c + delta
        if target_c < 1: target_c = 1
        if target_c > 20: target_c = 20

        if target_c > self.current_c:
            for i in range(self.current_c, target_c): self.col_widths[i] = self.default_w
            added_count = target_c - self.current_c
            current_total_w = sum(self.col_widths[:self.current_c]) + (self.current_c * 2) + 15
            avail = max_w - current_total_w
            if avail < added_count * (self.default_w + 2):
                allowed = int(max(0, avail // (self.default_w + 2)))
                target_c = self.current_c + allowed

        if target_c != self.current_c:
            self.current_c = target_c
            self.selected_cols = {c for c in self.selected_cols if c < self.current_c}
            self._draw_grid()

        self.entry_cols.delete(0, 'end'); self.entry_cols.insert(0, str(self.current_c))

    def _draw_grid(self):
        saved_data = []
        for r in range(len(self.entries)):
            saved_data.append([self._extract_cell_data(self.entries[r][c]) for c in range(len(self.entries[r]))])

        for widget in self.grid_container.winfo_children(): widget.destroy()

        self.grid_frame = ctk.CTkFrame(self.grid_container, fg_color=Colors.BORDER, corner_radius=0)
        self.grid_frame.place(x=5, y=5, anchor="nw")

        self.col_indicators = []
        self.row_indicators = []
        self.entries = []

        self.corner_btn = ctk.CTkButton(self.grid_frame, text="", width=12, height=12, corner_radius=2,
                                        fg_color=Colors.THON if self.is_select_all else Colors.TEXT_MUTED,
                                        hover_color=Colors.THON, command=self._select_all)
        self.corner_btn.grid(row=0, column=0, padx=2, pady=2)

        for c in range(self.current_c):
            ind = ctk.CTkFrame(self.grid_frame, height=8, width=self.col_widths[c], cursor="hand2", corner_radius=4)
            ind.grid(row=0, column=c + 1, pady=(0, 4), sticky="ew")
            ind.bind("<Button-1>", lambda e, col=c: self._toggle_col(col, multi=False))
            ind.bind("<Control-Button-1>", lambda e, col=c: self._toggle_col(col, multi=True))
            self.col_indicators.append(ind)

        for r in range(self.current_r):
            ind = ctk.CTkFrame(self.grid_frame, width=8, height=self.row_heights[r], cursor="hand2", corner_radius=4)
            ind.grid(row=r + 1, column=0, padx=(0, 4), sticky="ns")
            ind.bind("<Button-1>", lambda e, row=r: self._toggle_row(row, multi=False))
            ind.bind("<Control-Button-1>", lambda e, row=r: self._toggle_row(row, multi=True))
            self.row_indicators.append(ind)

            row_entries = []
            for c in range(self.current_c):
                w, h = self.col_widths[c], self.row_heights[r]
                init_data = saved_data[r][c] if (r < len(saved_data) and c < len(saved_data[r])) else None

                cell = self._create_cell(self.grid_frame, r, c, w, h, init_data)
                cell.grid(row=r + 1, column=c + 1, padx=1, pady=1, sticky="nsew")

                row_entries.append(cell)
            self.entries.append(row_entries)

        self._refresh_indicators()
        self._update_size_entries()

    def _move_focus(self, r, c, direction):
        nc = c + direction
        nr = r
        if nc >= self.current_c:
            nc = 0; nr += 1
        elif nc < 0:
            nc = self.current_c - 1; nr -= 1

        if 0 <= nr < self.current_r and 0 <= nc < self.current_c:
            try:
                cell = self.entries[nr][nc]
                if isinstance(cell, ctk.CTkTextbox): cell.focus_set()
                elif hasattr(cell, 'entry'): cell.entry.focus_set()
            except IndexError: pass


class TableInputDialog(BaseTableDialog):
    def __init__(self, master_app):
        # MUDANÇA: Tabela de texto normal agora é 4x8 com caixas de 60x30
        super().__init__(master_app, "Inserir Tabela Visual", default_r=4, default_c=8, default_w=60, default_h=30, min_w=20, min_h=20, default_label="tab:")

    def _create_cell(self, parent, r, c, w, h, initial_data):
        entry = ctk.CTkTextbox(parent, width=w, height=h, corner_radius=0, fg_color=Colors.BG_PANEL, text_color=Colors.TEXT_NORMAL, border_width=0, wrap="word", font=Fonts.UI)
        if initial_data: entry.insert("1.0", initial_data)

        def handle_key(action, event=None):
            if action == "next": self._move_focus(r, c, 1)
            elif action == "prev": self._move_focus(r, c, -1)
            return "break"

        entry.bind("<Tab>", lambda e=None: handle_key("next", e))
        entry.bind("<Shift-Tab>", lambda e=None: handle_key("prev", e))

        return entry

    def _extract_cell_data(self, cell):
        return cell.get("1.0", "end-1c")

    def _on_ok(self):
        matrix_data = [[self._extract_cell_data(cell).strip() for cell in r_entries] for r_entries in self.entries]
        active_widths = self.col_widths[:self.current_c]

        self.result = (
            matrix_data, active_widths, self.caption.get(), f"tab:{self.label.get().strip()}",
            self.valign_combo.get(), self.halign_combo.get(), self.border_combo.get()
        )
        self._close_dialog()


class ImageTableInputDialog(BaseTableDialog):
    def __init__(self, master_app):
        # MUDANÇA: Tabela de figuras agora é 2x2 com caixas bem maiores (180x150)
        super().__init__(master_app, "Tabela de Figuras", default_r=2, default_c=2, default_w=180, default_h=150, min_w=20, min_h=20, default_label="tab:fig_")

    def _create_cell(self, parent, r, c, w, h, initial_data):
        cell_frame = ctk.CTkFrame(parent, width=w, height=h, corner_radius=0, fg_color=Colors.BG_PANEL, border_width=0)
        cell_frame.pack_propagate(False)

        cell_frame.mode = "text"
        cell_frame.file_path = ""
        cell_frame.full_path = ""
        cell_frame.target_w = w
        cell_frame.target_h = h

        entry = ctk.CTkTextbox(cell_frame, fg_color="transparent", border_width=0, corner_radius=0, text_color=Colors.TEXT_NORMAL, font=Fonts.UI, wrap="word")

        btn_add = ctk.CTkButton(cell_frame, text="", corner_radius=4, fg_color="transparent", hover_color=Colors.BTN_HOVER)
        img_display = ctk.CTkLabel(cell_frame, text="", text_color=Colors.TEXT_NORMAL)
        img_tooltip = ToolTip(img_display, "")
        btn_trash = ctk.CTkButton(cell_frame, text="", corner_radius=4, fg_color="transparent", hover_color=Colors.BTN_DANGER_HOVER)

        def handle_key(action, event=None):
            if action == "next": self._move_focus(r, c, 1)
            elif action == "prev": self._move_focus(r, c, -1)
            return "break"

        def update_ui():
            if not cell_frame.winfo_exists(): return
            entry.pack_forget(); btn_add.place_forget(); img_display.pack_forget(); btn_trash.place_forget()

            cur_w = cell_frame.winfo_width() if cell_frame.winfo_width() > 1 else cell_frame.target_w
            cur_h = cell_frame.winfo_height() if cell_frame.winfo_height() > 1 else cell_frame.target_h
            is_micro = cur_w <= 70 or cur_h <= 40
            is_small = cur_w <= 100 or cur_h <= 70

            btn_sz = 16 if is_micro else (20 if is_small else 24)
            icn_sz = (10, 10) if is_micro else ((12, 12) if is_small else (14, 14))

            try:
                pil_add = Image.open(resource_path("icones/image.png")).convert("RGBA")
                pil_trash = Image.open(resource_path("icones/trash.png")).convert("RGBA")
                icn_add = ctk.CTkImage(light_image=pil_add, dark_image=pil_add, size=icn_sz)
                icn_trash = ctk.CTkImage(light_image=pil_trash, dark_image=pil_trash, size=icn_sz)
            except Exception:
                icn_add = icn_trash = None

            btn_add.configure(width=btn_sz, height=btn_sz, image=icn_add)
            btn_trash.configure(width=btn_sz, height=btn_sz, image=icn_trash)

            if cell_frame.mode == "text":
                entry.pack(fill="both", expand=True, padx=2, pady=2)
                img_tooltip.text = ""
                if not entry.get("1.0", "end-1c").strip(): btn_add.place(relx=0.98, rely=0.05, anchor="ne")
            else:
                img_display.pack(fill="both", expand=True)
                btn_trash.place(relx=0.98, rely=0.05, anchor="ne")
                img_tooltip.text = f"Imagem: {os.path.basename(cell_frame.full_path)}"
                try:
                    big_sz = (24, 24) if is_micro else ((32, 32) if is_small else (48, 48))
                    # Pegamos a versão GIGANTE da imagem direto do nosso cache inteligente
                    big_icon = Icons.get_ctk_image("image.png", size=big_sz)
                    img_display.configure(text="", image=big_icon, compound="center")
                except Exception:
                    img_display.configure(text="IMG", image=None, compound="center")

        def select_image():
            if not cell_frame.winfo_exists(): return
            proj_dir = str(self.app.project_dir.resolve())
            path = filedialog.askopenfilename(title="Selecione a Imagem", initialdir=proj_dir, filetypes=[("Imagens e PDFs", "*.png *.jpg *.jpeg *.pdf")])
            if not cell_frame.winfo_exists() or not path: return
            try:
                rel_path = os.path.relpath(path, proj_dir)
                if rel_path.startswith("..") or os.path.isabs(rel_path):
                    messagebox.showerror("Aviso", "A imagem deve estar na pasta do projeto.")
                    return
                cell_frame.file_path = rel_path.replace("\\", "/")
                cell_frame.full_path = path
                cell_frame.mode = "image"
                update_ui()
            except ValueError:
                messagebox.showerror("Erro", "O arquivo deve estar na unidade de disco do projeto.")

        def clear_image():
            if not cell_frame.winfo_exists(): return
            cell_frame.file_path = cell_frame.full_path = ""
            cell_frame.mode = "text"
            update_ui()

        entry.bind("<FocusIn>", lambda e: btn_add.place_forget())
        entry.bind("<FocusOut>", lambda e: btn_add.place(relx=0.98, rely=0.05, anchor="ne") if not entry.get("1.0", "end-1c").strip() else None)
        entry.bind("<Tab>", lambda e=None: handle_key("next", e))
        entry.bind("<Shift-Tab>", lambda e=None: handle_key("prev", e))

        btn_add.configure(command=select_image)
        btn_trash.configure(command=clear_image)

        if initial_data:
            if initial_data["type"] == "text":
                cell_frame.mode = "text"
                entry.insert("1.0", initial_data["value"])
            else:
                cell_frame.file_path = initial_data["value"]
                cell_frame.full_path = initial_data.get("full_path", "")
                cell_frame.mode = "image"

        update_ui()

        def get_data():
            if cell_frame.mode == "text": return {"type": "text", "value": entry.get("1.0", "end-1c").strip()}
            return {"type": "image", "value": cell_frame.file_path, "full_path": cell_frame.full_path}

        cell_frame.get_data = get_data
        cell_frame.entry = entry

        return cell_frame

    def _extract_cell_data(self, cell):
        return cell.get_data()

    def _on_ok(self):
        matrix_data = [[self._extract_cell_data(cell) for cell in r_entries] for r_entries in self.entries]
        active_widths = self.col_widths[:self.current_c]

        self.result = (
            matrix_data, active_widths, self.caption.get(), f"tab:fig_{self.label.get().strip()}",
            self.valign_combo.get(), self.halign_combo.get(), self.border_combo.get()
        )
        self._close_dialog()