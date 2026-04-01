import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts

LIMITS = {
    'left': (15, 25),   # Arquivos: Mínimo 15%, Máximo 25%
    'center': (30, 60), # Editor: Mínimo 30%, Máximo 60%
    'pdf': (30, 60)     # PDF: Mínimo 30%, Máximo 60%
}

class LayoutConfigDialog(BaseModal):
    """
    Componente Modal: Sistema de Sliders Sincronizados para Layout.
    Permite o redimensionamento percentual dos três painéis principais (Sidebar, Editor e Preview).
    """

    def __init__(self, master_app):
        super().__init__(master_app, "Configuração de Tela", 450, 300)
        ctk.CTkLabel(self.border_frame, text="Configuração de Tela", font=Fonts.UI_TITLE).pack(pady=15)

        cfg = self.app.config.get_layout()
        self.left_val, self.center_val, self.pdf_val = cfg.get("left", 15), cfg.get("center", 50), cfg.get("pdf", 35)

        self.slider_left = self._create_row("Arquivos", self.left_val, 'left')
        self.slider_center = self._create_row("Editor", self.center_val, 'center')
        self.slider_pdf = self._create_row("PDF", self.pdf_val, 'pdf')

        self.lbl_total = ctk.CTkLabel(self.border_frame, text="", font=Fonts.UI_BOLD)
        self.lbl_total.pack(pady=10)

        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.pack(pady=10)
        ctk.CTkButton(btn_f, text="Cancelar", width=80, fg_color="transparent", border_width=1,
                      text_color=Colors.TEXT_NORMAL, command=self._close_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Salvar e Aplicar", width=140, command=self._apply).pack(side="left", padx=5)

        self._update_labels()

    def _create_row(self, name, val, source):
        """Cria e empacota uma linha contendo um Label e o respectivo Slider de proporção."""
        f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        f.pack(pady=10, fill="x", padx=20)

        lbl = ctk.CTkLabel(f, text=f"{name} ({val}%)", width=110, anchor="w")
        lbl.pack(side="left")

        # Busca os limites específicos para cada slider
        min_v, max_v = LIMITS.get(source)

        slider = ctk.CTkSlider(f, from_=min_v, to=max_v, command=lambda v: self._sync_sliders(source, v))
        slider.set(val)
        slider.pack(side="left", fill="x", expand=True)

        setattr(self, f"lbl_{source}", lbl)
        return slider

    def _sync_sliders(self, source, value):
        v = int(value)

        if source == 'left':
            # Trava Arquivos entre 15 e 25
            self.left_val = max(15, min(v, 25))
            rem = 100 - self.left_val
            # Ajusta Editor proporcionalmente
            self.center_val = int(rem * (self.center_val / max(1, self.center_val + self.pdf_val)))
            self.center_val = max(30, min(self.center_val, 60))
            # PDF assume o resto
            self.pdf_val = 100 - self.left_val - self.center_val

        elif source == 'center':
            self.center_val = max(30, min(v, 60))
            rem = 100 - self.center_val
            self.left_val = int(rem * (self.left_val / max(1, self.left_val + self.pdf_val)))
            # Aplica trava de 15 a 25 para Arquivos
            self.left_val = max(15, min(self.left_val, 25))
            self.pdf_val = 100 - self.center_val - self.left_val

        elif source == 'pdf':
            self.pdf_val = max(30, min(v, 60))
            rem = 100 - self.pdf_val
            self.left_val = int(rem * (self.left_val / max(1, self.left_val + self.center_val)))
            # Aplica trava de 15 a 25 para Arquivos
            self.left_val = max(15, min(self.left_val, 25))
            self.center_val = 100 - self.pdf_val - self.left_val

        # Sincronização visual
        self.slider_left.set(self.left_val)
        self.slider_center.set(self.center_val)
        self.slider_pdf.set(self.pdf_val)
        self._update_labels()

    def _update_labels(self):
        self.lbl_left.configure(text=f"Arquivos ({self.left_val}%)")
        self.lbl_center.configure(text=f"Editor ({self.center_val}%)")
        self.lbl_pdf.configure(text=f"PDF ({self.pdf_val}%)")
        self.lbl_total.configure(text="Total: 100% (Ajuste Automático)", text_color=Colors.LA)

    def _apply(self):
        """Delega a execução das proporções visuais à classe Controladora."""
        self.app.preferences_manager.apply_layout_weights(self.left_val, self.center_val, self.pdf_val)
        self._close_dialog()