import tkinter as tk
import customtkinter as ctk


class CustomDialog(ctk.CTkToplevel):
    """Diálogo genérico com botões."""

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
    """Janela de input simples."""

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


# --- NOVO: JANELA PARA TABELA ---
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
    """Menu flutuante customizado."""

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