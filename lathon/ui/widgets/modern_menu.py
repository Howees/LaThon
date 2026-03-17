import customtkinter as ctk

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors


class ModernMenu(ctk.CTkToplevel):
    def __init__(self, master, width=200):
        super().__init__(master)
        self.withdraw()
        self.overrideredirect(True)
        self.transient(master)

        # Puxa cores do Design System baseado no tema atual
        is_dark = ctk.get_appearance_mode() == "Dark"
        idx = 1 if is_dark else 0

        self.bg_color = Colors.BG_PANEL[idx]
        self.border_color = Colors.BORDER[idx]
        self.hover_color = Colors.BTN_HOVER[idx]
        self.text_color = Colors.TEXT_NORMAL[idx]

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