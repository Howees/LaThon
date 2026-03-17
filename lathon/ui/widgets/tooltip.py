import tkinter as tk

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts


class ToolTip:
    """Classe responsável por mostrar as caixinhas de dica ao passar o mouse por cima dos botões."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 30
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")

        # Tooltip sempre com um fundo escuro legível, estilo VSCode
        tk.Label(self.tw, text=self.text, justify='left', background="#2b2b2b", foreground="white",
                 relief='solid', borderwidth=1, font=Fonts.UI).pack(ipadx=6, ipady=3)

    def leave(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None