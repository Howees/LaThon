import tkinter as tk
from lathon.ui.design import Fonts


class ToolTip:
    """
    Gerencia a exibição de caixas de texto informativas (Tooltips)
    que flutuam acima de widgets específicos ao passar o mouse.
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None

        # Cria os gatilhos de interação do mouse
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        """Calcula a posição do mouse e renderiza a janela do Tooltip."""
        x, y, _, _ = self.widget.bbox("insert")

        # Desloca a caixa levemente para baixo e para a direita do cursor
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 30

        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)  # Remove as bordas do sistema operacional
        self.tw.wm_geometry(f"+{x}+{y}")

        # Design fixo e escuro inspirado em IDEs modernas
        tk.Label(
            self.tw,
            text=self.text,
            justify='left',
            background="#2b2b2b",
            foreground="white",
            relief='solid',
            borderwidth=1,
            font=Fonts.UI
        ).pack(ipadx=6, ipady=3)

    def leave(self, event=None):
        """Destrói a janela do Tooltip quando o mouse sai do widget."""
        if self.tw:
            self.tw.destroy()
            self.tw = None