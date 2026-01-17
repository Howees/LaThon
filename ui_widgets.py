import tkinter as tk
import customtkinter as ctk


class CustomDialog(ctk.CTkToplevel):
    def __init__(self, title, text):
        super().__init__()
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("white", "#2b2b2b"))

        self.border_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=2,
                                         border_color=("gray70", "#454545"))
        self.border_frame.pack(fill="both", expand=True)

        w, h = 350, 180
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry(f"{w}x{h}+{int(x)}+{int(y)}")

        self.deiconify()
        self.grab_set()

        ctk.CTkLabel(self.border_frame, text=title, font=("Segoe UI", 14, "bold"), text_color=("black", "white")).pack(
            pady=(15, 5))
        ctk.CTkLabel(self.border_frame, text=text, wraplength=320, text_color=("gray20", "gray80")).pack(pady=5)

        self.button_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        self.button_frame.pack(pady=15)
        self.choice = None

    def add_button(self, text, command_value, fg_color=None):
        btn = ctk.CTkButton(
            self.button_frame, text=text,
            fg_color=fg_color if fg_color else ["#3a7ebf", "#1f538d"],
            command=lambda: self._set_choice_and_destroy(command_value)
        )
        btn.pack(side="left", padx=10)

    def _set_choice_and_destroy(self, choice):
        self.choice = choice
        self.destroy()

    def get_choice(self):
        self.master.wait_window(self)
        return self.choice


class FixedInputDialog(ctk.CTkToplevel):
    def __init__(self, title, text):
        super().__init__()
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("white", "#2b2b2b"))

        self.border_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=2,
                                         border_color=("gray70", "#454545"))
        self.border_frame.pack(fill="both", expand=True)

        w, h = 350, 180
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry(f"{w}x{h}+{int(x)}+{int(y)}")

        self.deiconify()
        self.grab_set()

        ctk.CTkLabel(self.border_frame, text=title, font=("Segoe UI", 14, "bold"), text_color=("black", "white")).pack(
            pady=(15, 5))
        ctk.CTkLabel(self.border_frame, text=text, text_color=("gray20", "gray80")).pack(pady=5)

        self.entry = ctk.CTkEntry(self.border_frame, width=250, fg_color=("gray95", "#343638"),
                                  text_color=("black", "white"))
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self._on_ok)
        self.entry.bind("<Escape>", self._on_cancel)
        self.entry.focus_set()

        btn_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      border_color=("gray60", "gray50"), text_color=("black", "white"), width=80,
                      command=self._on_cancel).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="OK", width=80, command=self._on_ok).pack(side="left", padx=5)
        self.user_input = None

    def _on_ok(self, event=None):
        self.user_input = self.entry.get()
        self.destroy()

    def _on_cancel(self, event=None):
        self.user_input = None
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self.user_input


class TableInputDialog(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("white", "#2b2b2b"))

        border = ctk.CTkFrame(self, fg_color="transparent", border_width=2, border_color=("gray70", "#454545"))
        border.pack(fill="both", expand=True)

        w, h = 300, 220
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
        self.deiconify()
        self.grab_set()

        ctk.CTkLabel(border, text="Inserir Tabela", font=("Segoe UI", 14, "bold"), text_color=("black", "white")).pack(
            pady=15)

        f1 = ctk.CTkFrame(border, fg_color="transparent")
        f1.pack(pady=5)
        ctk.CTkLabel(f1, text="Linhas:", width=60, anchor="e", text_color=("gray20", "gray80")).pack(side="left")
        self.rows = ctk.CTkEntry(f1, width=60, justify="center")
        self.rows.pack(side="left", padx=10)
        self.rows.insert(0, "3")

        f2 = ctk.CTkFrame(border, fg_color="transparent")
        f2.pack(pady=5)
        ctk.CTkLabel(f2, text="Colunas:", width=60, anchor="e", text_color=("gray20", "gray80")).pack(side="left")
        self.cols = ctk.CTkEntry(f2, width=60, justify="center")
        self.cols.pack(side="left", padx=10)
        self.cols.insert(0, "3")

        btn_f = ctk.CTkFrame(border, fg_color="transparent")
        btn_f.pack(pady=20)
        ctk.CTkButton(btn_f, text="Cancelar", width=80, fg_color="transparent", border_width=1,
                      text_color=("black", "white"), command=self.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Inserir", width=80, command=self._on_ok).pack(side="left", padx=5)

        self.result = None

    def _on_ok(self):
        try:
            r = int(self.rows.get())
            c = int(self.cols.get())
            self.result = (r, c)
            self.destroy()
        except:
            pass

    def get_dimensions(self):
        self.master.wait_window(self)
        return self.result


class ModernMenu(ctk.CTkToplevel):
    def __init__(self, master, width=200):
        super().__init__(master)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.bg_color = ("white", "#2b2b2b")
        self.border_color = ("gray70", "#454545")
        self.hover_color = ("gray90", "#3a3d41")
        self.text_color = ("black", "#cccccc")
        self.frame = ctk.CTkFrame(self, width=width, corner_radius=6, fg_color=self.bg_color, border_width=1,
                                  border_color=self.border_color)
        self.frame.pack(fill="both", expand=True)
        self.buttons = []
        self.bind("<FocusOut>", lambda e: self.withdraw())

    def add_command(self, label, command, text_color=None, hover_color=None):
        t_col = text_color if text_color else self.text_color
        h_col = hover_color if hover_color else self.hover_color
        btn = ctk.CTkButton(self.frame, text=label, anchor="w", fg_color="transparent", text_color=t_col,
                            hover_color=h_col, height=30, corner_radius=4,
                            command=lambda: self._execute_and_close(command))
        btn.pack(fill="x", padx=4, pady=2)
        self.buttons.append(btn)

    def add_separator(self):
        sep = ctk.CTkFrame(self.frame, height=1, fg_color=self.border_color)
        sep.pack(fill="x", padx=0, pady=2)
        self.buttons.append(sep)

    def _execute_and_close(self, command):
        self.withdraw()
        if command: command()

    def popup(self, x, y):
        self.deiconify()
        self.geometry(f"+{x}+{y}")
        self.focus_set()

    def clear(self):
        for btn in self.buttons: btn.destroy()
        self.buttons = []


class LayoutConfigDialog(ctk.CTkToplevel):
    """Janela para configurar proporções da tela visualmente."""

    def __init__(self, current_file_pct=0.2, current_pdf_pct=0.4):
        super().__init__()
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("white", "#2b2b2b"))

        self.border = ctk.CTkFrame(self, fg_color="transparent", border_width=2, border_color=("gray70", "#454545"))
        self.border.pack(fill="both", expand=True)

        w, h = 600, 350
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        ctk.CTkLabel(self.border, text="Configurar Tela", font=("Segoe UI", 16, "bold"),
                     text_color=("black", "white")).pack(pady=10)
        ctk.CTkLabel(self.border, text="Arraste as divisórias verticais para ajustar.",
                     font=("Segoe UI", 12), text_color="gray").pack(pady=(0, 5))
        ctk.CTkLabel(self.border, text="(Limites: Pasta > 15%, Editor > 30%, PDF > 40%)",
                     font=("Segoe UI", 10), text_color="gray60").pack(pady=(0, 20))

        self.canvas_width = 500
        self.canvas_height = 100
        self.canvas = tk.Canvas(self.border, width=self.canvas_width, height=self.canvas_height,
                                bg="#202020", highlightthickness=0)
        self.canvas.pack(pady=10)

        self.result = None
        self.file_pct = current_file_pct
        self.pdf_pct = current_pdf_pct

        self.min_file_px = 0.15 * self.canvas_width
        self.min_editor_px = 0.30 * self.canvas_width
        self.min_pdf_px = 0.40 * self.canvas_width

        self.line1_x = self.file_pct * self.canvas_width
        self.line2_x = self.canvas_width - (self.pdf_pct * self.canvas_width)

        self.rect_files = self.canvas.create_rectangle(0, 0, self.line1_x, self.canvas_height,
                                                       fill="#2196F3", outline="")
        self.rect_editor = self.canvas.create_rectangle(self.line1_x, 0, self.line2_x, self.canvas_height,
                                                        fill="#333333", outline="")
        self.rect_pdf = self.canvas.create_rectangle(self.line2_x, 0, self.canvas_width, self.canvas_height,
                                                     fill="#F44336", outline="")

        self.txt_files = self.canvas.create_text(self.line1_x / 2, self.canvas_height / 2, text="Pasta", fill="white",
                                                 font=("Segoe UI", 10, "bold"))
        self.txt_editor = self.canvas.create_text((self.line1_x + self.line2_x) / 2, self.canvas_height / 2,
                                                  text="Editor", fill="white", font=("Segoe UI", 10, "bold"))
        self.txt_pdf = self.canvas.create_text((self.line2_x + self.canvas_width) / 2, self.canvas_height / 2,
                                               text="PDF", fill="white", font=("Segoe UI", 10, "bold"))

        self.sep1_visual = self.canvas.create_line(self.line1_x, 0, self.line1_x, self.canvas_height, fill="white",
                                                   width=2)
        self.sep2_visual = self.canvas.create_line(self.line2_x, 0, self.line2_x, self.canvas_height, fill="white",
                                                   width=2)

        self.sep1_hitbox = self.canvas.create_rectangle(self.line1_x - 10, 0, self.line1_x + 10, self.canvas_height,
                                                        fill="", outline="", tags="sep1_drag")
        self.sep2_hitbox = self.canvas.create_rectangle(self.line2_x - 10, 0, self.line2_x + 10, self.canvas_height,
                                                        fill="", outline="", tags="sep2_drag")

        self.canvas.tag_bind("sep1_drag", "<Enter>", lambda e: self.canvas.config(cursor="sb_h_double_arrow"))
        self.canvas.tag_bind("sep1_drag", "<Leave>", lambda e: self.canvas.config(cursor="arrow"))
        self.canvas.tag_bind("sep2_drag", "<Enter>", lambda e: self.canvas.config(cursor="sb_h_double_arrow"))
        self.canvas.tag_bind("sep2_drag", "<Leave>", lambda e: self.canvas.config(cursor="arrow"))

        info_frame = ctk.CTkFrame(self.border, fg_color="transparent")
        info_frame.pack(fill="x", padx=50, pady=10)
        self.lbl_files = ctk.CTkLabel(info_frame, text=f"Pasta: {int(self.file_pct * 100)}%", text_color="#2196F3",
                                      font=("Segoe UI", 12, "bold"))
        self.lbl_files.pack(side="left", expand=True)
        self.lbl_editor = ctk.CTkLabel(info_frame, text=f"Editor: {int((1 - self.file_pct - self.pdf_pct) * 100)}%",
                                       text_color="gray", font=("Segoe UI", 12, "bold"))
        self.lbl_editor.pack(side="left", expand=True)
        self.lbl_pdf = ctk.CTkLabel(info_frame, text=f"PDF: {int(self.pdf_pct * 100)}%", text_color="#F44336",
                                    font=("Segoe UI", 12, "bold"))
        self.lbl_pdf.pack(side="left", expand=True)

        self.canvas.tag_bind("sep1_drag", "<Button-1>", self._start_drag)
        self.canvas.tag_bind("sep1_drag", "<B1-Motion>", self._drag_sep1)
        self.canvas.tag_bind("sep2_drag", "<Button-1>", self._start_drag)
        self.canvas.tag_bind("sep2_drag", "<B1-Motion>", self._drag_sep2)

        btn_f = ctk.CTkFrame(self.border, fg_color="transparent")
        btn_f.pack(side="bottom", pady=20)
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="transparent", border_width=1, text_color=("black", "white"),
                      command=self._on_cancel).pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="Aplicar", command=self._on_apply, fg_color="#238636", hover_color="#2ea043").pack(
            side="left", padx=10)

        self.deiconify()
        self.grab_set()

    def _start_drag(self, event):
        self.last_x = event.x

    def _drag_sep1(self, event):
        x = event.x
        coords_sep2 = self.canvas.coords(self.sep2_visual)
        current_sep2_x = coords_sep2[0]

        limit_min = self.min_file_px
        limit_max = current_sep2_x - self.min_editor_px

        if x < limit_min: x = limit_min
        if x > limit_max: x = limit_max

        self.canvas.coords(self.sep1_visual, x, 0, x, self.canvas_height)
        self.canvas.coords(self.sep1_hitbox, x - 10, 0, x + 10, self.canvas_height)
        self._update_visuals(x, current_sep2_x)

    def _drag_sep2(self, event):
        x = event.x
        coords_sep1 = self.canvas.coords(self.sep1_visual)
        current_sep1_x = coords_sep1[0]

        limit_max = self.canvas_width - self.min_pdf_px
        limit_min = current_sep1_x + self.min_editor_px

        if x < limit_min: x = limit_min
        if x > limit_max: x = limit_max

        self.canvas.coords(self.sep2_visual, x, 0, x, self.canvas_height)
        self.canvas.coords(self.sep2_hitbox, x - 10, 0, x + 10, self.canvas_height)
        self._update_visuals(current_sep1_x, x)

    def _update_visuals(self, x1, x2):
        self.canvas.coords(self.rect_files, 0, 0, x1, self.canvas_height)
        self.canvas.coords(self.rect_editor, x1, 0, x2, self.canvas_height)
        self.canvas.coords(self.rect_pdf, x2, 0, self.canvas_width, self.canvas_height)

        self.canvas.coords(self.txt_files, x1 / 2, self.canvas_height / 2)
        self.canvas.coords(self.txt_editor, (x1 + x2) / 2, self.canvas_height / 2)
        self.canvas.coords(self.txt_pdf, (x2 + self.canvas_width) / 2, self.canvas_height / 2)

        p_files = x1 / self.canvas_width
        p_pdf = (self.canvas_width - x2) / self.canvas_width
        p_editor = 1.0 - p_files - p_pdf

        self.lbl_files.configure(text=f"Pasta: {int(p_files * 100)}%")
        self.lbl_editor.configure(text=f"Editor: {int(p_editor * 100)}%")
        self.lbl_pdf.configure(text=f"PDF: {int(p_pdf * 100)}%")

    def _on_apply(self):
        x1 = self.canvas.coords(self.sep1_visual)[0]
        x2 = self.canvas.coords(self.sep2_visual)[0]
        self.result = (x1 / self.canvas_width, (self.canvas_width - x2) / self.canvas_width)
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

    def get_layout(self):
        self.master.wait_window(self)
        return self.result


class EditorConfigDialog(ctk.CTkToplevel):
    def __init__(self, current_font_size, current_font_family):
        super().__init__()
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("white", "#2b2b2b"))

        self.border = ctk.CTkFrame(self, fg_color="transparent", border_width=2, border_color=("gray70", "#454545"))
        self.border.pack(fill="both", expand=True)

        w, h = 400, 320
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.deiconify()
        self.grab_set()

        ctk.CTkLabel(self.border, text="Configurar Editor", font=("Segoe UI", 16, "bold"),
                     text_color=("black", "white")).pack(pady=15)

        ctk.CTkLabel(self.border, text="Tipo de Fonte:", text_color="gray", anchor="w").pack(fill="x", padx=30,
                                                                                             pady=(10, 0))
        self.font_family_var = ctk.StringVar(value=current_font_family)
        fonts = ["Consolas", "Courier New", "Arial", "Verdana", "Times New Roman", "Segoe UI"]
        self.font_combo = ctk.CTkComboBox(self.border, values=fonts, variable=self.font_family_var)
        self.font_combo.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(self.border, text="Tamanho:", text_color="gray", anchor="w").pack(fill="x", padx=30, pady=(15, 0))
        self.font_slider = ctk.CTkSlider(self.border, from_=10, to=26, number_of_steps=16, command=self._update_lbl)
        self.font_slider.set(current_font_size)
        self.font_slider.pack(fill="x", padx=30, pady=5)
        self.lbl_font_size = ctk.CTkLabel(self.border, text=f"{int(current_font_size)} px")
        self.lbl_font_size.pack()

        btn_f = ctk.CTkFrame(self.border, fg_color="transparent")
        btn_f.pack(side="bottom", pady=20)
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="transparent", border_width=1, text_color=("black", "white"),
                      command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="Salvar", command=self._on_save, fg_color="#238636", hover_color="#2ea043").pack(
            side="left", padx=10)

        self.result = None

    def _update_lbl(self, val):
        self.lbl_font_size.configure(text=f"{int(val)} px")

    def _on_save(self):
        self.result = {
            "font_size": int(self.font_slider.get()),
            "font_family": self.font_family_var.get()
        }
        self.destroy()

    def get_settings(self):
        self.master.wait_window(self)
        return self.result